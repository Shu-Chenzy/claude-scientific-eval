"""Build review/ : per-task pages with model identities, scores and the full responses.

    python scripts/build_review_pages.py

Run only after scoring is complete and the key has been published. review_blind/ is kept as the
record of what was actually scored; review/ is the readable version.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORE = ["biological_correctness", "evidence_grounding", "causal_reasoning",
        "experimental_feasibility", "falsifiability", "uncertainty_calibration"]
FCODES = [f"F{i:02d}" for i in range(1, 16)]
SHORT = {"claude-haiku-5-5": "Haiku 5.5", "claude-sonnet-5-5": "Sonnet 5.5", "claude-opus-5-5": "Opus 5.5"}


def main():
    scores = pd.read_csv(ROOT / "scoring" / "blind_scores.csv")
    key = pd.read_csv(ROOT / "results" / "blinding_key.csv")
    df = scores.merge(key[["task_id", "label", "model", "arm", "served_by"]],
                      left_on=["task_id", "response"], right_on=["task_id", "label"])
    df["short"] = df.model.map(SHORT)
    df["mean_core"] = df[CORE].mean(axis=1).round(2)

    out = ROOT / "review"
    out.mkdir(exist_ok=True)
    index_rows = []

    for p in sorted((ROOT / "tasks").glob("T*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        tid = t["task_id"]
        rows = df[df.task_id == tid].sort_values("mean_core", ascending=False)

        page = [f"# {tid} — {t['title']}",
                f"**Capability: {t['capability']}**",
                "## Prompt", "```\n" + t["prompt"] + "\n```",
                f"Input: [`prostate_public_packet.md`](../{t['input_files'][0]})",
                "## Scoring anchors", "\n".join(f"- {e}" for e in t["expected_elements"]),
                "## Scores",
                "| Model | " + " | ".join(c.replace("_", " ") for c in CORE) + " | mean | flags |",
                "|---|" + "---|" * (len(CORE) + 2)]
        for r in rows.itertuples():
            flags = [c for c in FCODES if getattr(r, c) == 1]
            page.append(f"| {r.short} | " + " | ".join(str(int(getattr(r, c))) for c in CORE)
                        + f" | **{r.mean_core}** | {', '.join(flags) or '—'} |")

        page.append("### Reviewer notes")
        for r in rows.itertuples():
            page.append(f"**{r.short}** — {r.notes}")

        for r in rows.itertuples():
            rec = json.loads((ROOT / "outputs" / r.arm / f"{tid}.json").read_text(encoding="utf-8"))
            note = (f"  \n*Served by `{r.served_by}` after `{r.model}` declined this prompt; "
                    f"scored as the fallback arm.*" if r.arm != r.model else "")
            page += [f"## {r.short} — mean {r.mean_core}, stated confidence {r.confidence}%, "
                     f"{r.words} words{note}", rec["output"]]

        page.append("---\n\n[← all tasks](index.md) · [results](../results/analysis.md) · "
                    "[rubric](../scoring/rubric.md)")
        (out / f"{tid}.md").write_text("\n\n".join(page) + "\n", encoding="utf-8")

        best = rows.iloc[0]
        index_rows.append({"Task": f"[{tid}]({tid}.md)", "Capability": t["capability"],
                           "Haiku 5.5": rows.loc[rows.short == "Haiku 5.5", "mean_core"].iat[0],
                           "Sonnet 5.5": rows.loc[rows.short == "Sonnet 5.5", "mean_core"].iat[0],
                           "Opus 5.5": rows.loc[rows.short == "Opus 5.5", "mean_core"].iat[0],
                           "Flags": int(rows[FCODES].sum().sum())})

    index = ["# All six tasks, scored",
             "Each page holds the prompt, the scoring anchors, the three responses with the model "
             "named, and the scores with reviewer notes. Scoring was done blind; "
             "[`review_blind/`](../review_blind/index.md) is the version that was scored.",
             pd.DataFrame(index_rows).to_markdown(index=False),
             "Mean of the six core dimensions, 1–5. Opus 5.5 rows for T3–T6 are fallback-arm answers "
             "(it declined those prompts), so they are not clean measurements of that model.",
             "[Full results and figures](../results/analysis.md) · "
             "[per-response scores](../scoring/blind_scores.csv)"]
    (out / "index.md").write_text("\n\n".join(index) + "\n", encoding="utf-8")
    print(f"wrote review/index.md and {len(index_rows)} task pages")


if __name__ == "__main__":
    main()
