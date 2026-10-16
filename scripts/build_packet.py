"""Build inputs/public/prostate_public_packet.md from the published prostate-ai-hypothesis-evaluation repo.

    python scripts/build_packet.py "path/to/prostate-ai-hypothesis-evaluation"

Uses only the analysis sections of that README and its result tables (public GEO / SU2C data).
The earlier LLM-evaluation sections are excluded so they cannot prime the model.
"""

import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEEP = ["Question", "Data", "Analysis", "Findings", "Limitations"]


def readme_sections(text):
    parts = re.split(r"^## ", text, flags=re.M)
    out = {}
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out[head.strip()] = body.strip()
    return out


def clean(body):
    lines = []
    for line in body.splitlines():
        if line.startswith("!["):  # figures
            continue
        if "Claude" in line or "LLM" in line or "language model" in line:  # drop earlier eval content
            continue
        lines.append(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line))  # strip links
    return "\n".join(lines).strip()


def md_table(df):
    cols = list(df.columns)
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        rows.append("| " + " | ".join(f"{v:.3g}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(rows)


def main():
    src = Path(sys.argv[1])
    sec = readme_sections((src / "README.md").read_text(encoding="utf-8"))
    cand = pd.read_csv(src / "results" / "candidate_targets.csv")
    deg = pd.read_csv(src / "results" / "deg_crpc_vs_localized.csv")
    up = pd.read_csv(src / "results" / "hallmark_up_in_CRPC.csv").sort_values("Adjusted P-value").head(5)
    down = pd.read_csv(src / "results" / "hallmark_down_in_CRPC.csv").sort_values("Adjusted P-value").head(5)

    cols = ["gene", "tier", "direction_in_CRPC", "log2FC_GSE35988", "FDR_GSE35988", "su2c_beta_ARSI", "su2c_p",
            "su2c_FDR", "su2c_median_log2FPKM", "composition_rho", "protein_class", "cell_surface"]
    tier1 = cand[cand.tier == 1]
    tier2 = cand[(cand.tier == 2) & ~cand.prespecified].sort_values("su2c_p").head(6)
    pre = cand[cand.prespecified]
    shortlist = pd.concat([tier1, tier2, pre])[cols]

    flagged = (deg[deg.composition_flag & (deg.FDR < 0.05) & (deg.log2FC.abs() > 1)]
               .sort_values("p").head(8)[["gene", "log2FC", "FDR", "composition_rho", "composition_driver"]])

    parts = [
        "# Public prostate cancer analysis (packet v0.1)",
        "Source: prostate-ai-hypothesis-evaluation (public GEO GSE35988 and SU2C/PCF 2019 data). "
        "All values below come from that analysis. No unpublished experimental data are included.",
    ]
    for k in KEEP:
        if k in sec:
            parts.append(f"## {k}\n\n{clean(sec[k])}")
    parts += [
        "## Candidate table (tier 1 = replicated in SU2C; tier 2 = not replicated; SSTR1 pre-specified)\n\n"
        "log2FC and FDR: CRPC vs localized in GSE35988. su2c_beta_ARSI: ARSI-exposed minus ARSI-naive, site-adjusted. "
        "composition_rho: max Spearman rho with stroma/immune/mast-cell/early-response scores.\n\n" + md_table(shortlist),
        "## Top composition-flagged hits (excluded from the candidate table)\n\n" + md_table(flagged),
        "## Hallmark pathways, retained hits\n\nUp in CRPC:\n\n" + md_table(up[["Term", "Overlap", "Adjusted P-value"]])
        + "\n\nDown in CRPC:\n\n" + md_table(down[["Term", "Overlap", "Adjusted P-value"]]),
    ]
    out = ROOT / "inputs" / "public" / "prostate_public_packet.md"
    out.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {out.name}: {len(out.read_text(encoding='utf-8'))} characters, {len(shortlist)} candidates")


if __name__ == "__main__":
    main()
