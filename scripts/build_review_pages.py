"""Build unblinded per-task review pages after scoring is complete."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORE = [
    "biological_correctness",
    "evidence_grounding",
    "causal_reasoning",
    "experimental_feasibility",
    "falsifiability",
    "uncertainty_calibration",
]
FCODES = [f"F{i:02d}" for i in range(1, 16)]
SHORT = {
    "claude-haiku-5-5": "Haiku 5.5",
    "claude-sonnet-5-5": "Sonnet 5.5",
    "claude-opus-5-5": "Opus 5.5",
    "claude-opus-5": "Opus 5 fallback",
}


def main():
    scores = pd.read_csv(ROOT / "scoring" / "blind_scores.csv")
    key = pd.read_csv(ROOT / "results" / "blinding_key.csv")
    df = scores.merge(
        key[["task_id", "label", "model", "arm", "served_by"]],
        left_on=["task_id", "response"],
        right_on=["task_id", "label"],
    )
    df["requested_short"] = df.model.map(SHORT)
    df["served_short"] = df.served_by.map(SHORT).fillna(df.served_by)
    df["is_fallback"] = df.arm != df.model
    df["display"] = df.apply(
        lambda r: f"{r.served_short} (fallback after {r.requested_short} refusal)" if r.is_fallback else r.requested_short,
        axis=1,
    )
    df["mean_core"] = df[CORE].mean(axis=1).round(2)

    out = ROOT / "review"
    out.mkdir(exist_ok=True)
    index_rows = []

    for p in sorted((ROOT / "tasks").glob("T*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        tid = t["task_id"]
        rows = df[df.task_id == tid].copy()

        page = [
            f"# {tid} — {t['title']}",
            f"**Capability:** {t['capability']}",
            "## Prompt",
            "```\n" + t["prompt"] + "\n```",
            f"Input: [`prostate_public_packet.md`](../{t['input_files'][0]})",
            "## Scoring anchors",
            "\n".join(f"- {e}" for e in t["expected_elements"]),
            "## Scores",
            "| Response | " + " | ".join(c.replace("_", " ") for c in CORE) + " | mean | flags |",
            "|---|" + "---|" * (len(CORE) + 2),
        ]

        for r in rows.sort_values(["is_fallback", "requested_short"]).itertuples():
            flags = [c for c in FCODES if getattr(r, c) == 1]
            page.append(
                f"| {r.display} | "
                + " | ".join(str(int(getattr(r, c))) for c in CORE)
                + f" | **{r.mean_core}** | {', '.join(flags) or '—'} |"
            )

        page.append("### Reviewer notes")
        for r in rows.sort_values(["is_fallback", "requested_short"]).itertuples():
            page.append(f"**{r.display}** — {r.notes}")

        for r in rows.sort_values(["is_fallback", "requested_short"]).itertuples():
            rec = json.loads((ROOT / "outputs" / r.arm / f"{tid}.json").read_text(encoding="utf-8"))
            page += [
                f"## {r.display} — mean {r.mean_core}, stated confidence {r.confidence}%, {r.words} words",
                rec["output"],
            ]

        page.append("---\n\n[← all tasks](index.md) · [results](../results/analysis.md) · [rubric](../scoring/rubric.md)")
        (out / f"{tid}.md").write_text("\n\n".join(page) + "\n", encoding="utf-8")

        vals = {}
        for requested in ["Haiku 5.5", "Sonnet 5.5", "Opus 5.5"]:
            sub = rows[rows.requested_short == requested]
            if sub.empty:
                vals[requested] = "—"
            else:
                r = sub.iloc[0]
                score = f"{r.mean_core:.2f}"
                vals[requested] = score + ("*" if r.is_fallback else "")
        index_rows.append(
            {
                "Task": f"[{tid}]({tid}.md)",
                "Capability": t["capability"],
                "Haiku 5.5": vals["Haiku 5.5"],
                "Sonnet 5.5": vals["Sonnet 5.5"],
                "Opus 5.5 request": vals["Opus 5.5"],
                "Flags": int(rows[FCODES].sum().sum()),
            }
        )

    index = [
        "# Six-task review",
        "Each page contains the task, scoring anchors, unblinded responses, scores, and reviewer notes. Scoring itself was performed blind; `review_blind/` preserves that version.",
        pd.DataFrame(index_rows).to_markdown(index=False),
        "*For T3–T6, the Opus 5.5 request was refused. The starred score is from the separate Opus 5 fallback arm and is not an Opus 5.5 measurement.*",
        "[Full results](../results/analysis.md) · [per-response scores](../scoring/blind_scores.csv)",
    ]
    (out / "index.md").write_text("\n\n".join(index) + "\n", encoding="utf-8")
    print(f"wrote {len(index_rows)} review pages")


if __name__ == "__main__":
    main()
