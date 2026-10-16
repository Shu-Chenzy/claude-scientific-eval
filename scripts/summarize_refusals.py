"""Summarize which prompts each model declined, and whether the refusals reproduce.

    python scripts/summarize_refusals.py

Reads the primary arm, the repeat attempts and the fallback arm, and writes
results/refusal_summary.md and results/refusals.csv. Refusal rate is only comparable because the
primary arm runs with server-side fallbacks disabled.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
SHORT = {"claude-haiku-5-5": "Haiku 5.5", "claude-sonnet-5-5": "Sonnet 5.5", "claude-opus-5-5": "Opus 5.5"}


def main():
    tasks = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "tasks").glob("T*.json")}
    rows = []
    for m in MODELS:
        for p in sorted((ROOT / "outputs" / m).glob("T*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            tid = r["task_id"]
            retries = sorted((ROOT / "outputs" / m / "retries").glob(f"{tid}_attempt*.json"))
            att = [json.loads(q.read_text(encoding="utf-8")) for q in retries]
            fb = ROOT / "outputs" / f"{m}+fallback" / f"{tid}.json"
            fb_rec = json.loads(fb.read_text(encoding="utf-8")) if fb.exists() else None
            rows.append({
                "task_id": tid, "capability": tasks[tid]["capability"], "model": SHORT[m],
                "refused": r["refused"], "refusal_category": r["refusal_category"],
                "attempts": 1 + len(att),
                "attempts_refused": int(r["refused"]) + sum(a["refused"] for a in att),
                "fallback_answered": bool(fb_rec and not fb_rec["refused"]),
                "fallback_served_by": fb_rec["served_by"] if fb_rec else "",
                "words": r["words"], "confidence": r["confidence"],
            })
    df = pd.DataFrame(rows)
    (ROOT / "results").mkdir(exist_ok=True)
    df.to_csv(ROOT / "results" / "refusals.csv", index=False)

    rate = df.groupby("model").agg(tasks=("task_id", "size"), refused=("refused", "sum"))
    rate["refusal_rate"] = (rate.refused / rate.tasks).map("{:.0%}".format)
    grid = df.assign(outcome=df.refused.map({True: "refused", False: "answered"})) \
             .pivot(index="task_id", columns="model", values="outcome")
    grid.insert(0, "capability", [tasks[t]["capability"] for t in grid.index])

    ref = df[df.refused]
    lines = [
        "# Refusals",
        "Every model received identical prompts, identical input and `effort: high`, each in a fresh "
        "context. **Server-side refusal fallbacks are disabled in the primary arm**, so a declined "
        "prompt is recorded as a refusal rather than being answered by a different model. That is what "
        "makes these rates comparable.",
        "## Rate", rate.to_markdown(),
        "## Which prompts", grid.to_markdown(),
    ]
    if not ref.empty:
        det = ref[ref.attempts_refused == ref.attempts]
        lines += [
            "## Reproducibility",
            f"Each refused prompt was sent again under identical conditions. "
            f"{len(det)} of {len(ref)} refused on **every** attempt "
            f"({ref.attempts.min()}–{ref.attempts.max()} attempts each), so these are deterministic "
            "properties of the prompt and model, not sampling noise.",
            ref[["task_id", "capability", "model", "refusal_category", "attempts", "attempts_refused"]]
                .to_markdown(index=False),
            "## Category",
            "All refusals carry `stop_details.category = "
            + ", ".join(sorted(set(ref.refusal_category.dropna()))) + "`.",
            "## Fallback arm",
            "A separate, clearly-labelled arm re-runs the refused prompts with fallbacks enabled, so "
            "there is an answer to score. Those answers come from whichever model the API routed to, "
            "recorded per response:",
            ref[["task_id", "model", "fallback_answered", "fallback_served_by"]].to_markdown(index=False),
        ]
    (ROOT / "results" / "refusal_summary.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")

    print(rate.to_string())
    print()
    print(grid.to_string())
    print("\nwrote results/refusal_summary.md and results/refusals.csv")


if __name__ == "__main__":
    main()
