"""Blind the responses, build the blind scoring sheet, and write the side-by-side review pages.

    python scripts/blind_and_build_sheet.py

The label mapping is randomised INDEPENDENTLY FOR EACH TASK, so Model A on T1 is not Model A on T2.
That stops the reviewer from inferring identity on one task and carrying it to the rest.

Writes:
  private/blinding_key.csv          the mapping (gitignored; do not read while scoring)
  scoring/blind_scores.xlsx/.csv    one row per response, blank scores
  review_blind/T*.md                the three responses for each task, side by side
  review_blind/index.md
"""

import itertools
import json
import random
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
LABELS = ["A", "B", "C"]
SEED = 20261015
CORE = ["biological_correctness", "evidence_grounding", "causal_reasoning",
        "experimental_feasibility", "falsifiability", "uncertainty_calibration"]
FCODES = [f"F{i:02d}" for i in range(1, 16)]


def main():
    tasks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "tasks").glob("T*.json"))]
    rng = random.Random(SEED)
    # Balanced assignment rather than an independent shuffle per task: with 3 models there are 6
    # label permutations, so over 6 tasks each model sits under each label exactly twice. A plain
    # shuffle can leave one model under the same label on most tasks, which leaks its identity.
    perms = list(itertools.permutations(MODELS))
    rng.shuffle(perms)
    orders = [perms[i % len(perms)] for i in range(len(tasks))]

    key, rows, pages, refusals = [], [], [], []
    for task_index, t in enumerate(tasks):
        tid = t["task_id"]
        # One scoreable response per model. Where a model refused, the clearly-labelled
        # fallback-enabled arm supplies the answer in its place; the refusal is recorded separately.
        recs = {}
        for m in MODELS:
            p = ROOT / "outputs" / m / f"{tid}.json"
            if not p.exists():
                continue
            r = json.loads(p.read_text(encoding="utf-8"))
            if r["refused"]:
                refusals.append({"task_id": tid, "model": m, "refusal_category": r["refusal_category"]})
                fb = ROOT / "outputs" / f"{m}+fallback" / f"{tid}.json"
                if not fb.exists():
                    continue
                r = json.loads(fb.read_text(encoding="utf-8"))
                r["arm"] = f"{m}+fallback"
            else:
                r["arm"] = m
            recs[m] = r
        if len(recs) < len(MODELS):
            print(f"{tid}: only {len(recs)} of {len(MODELS)} scoreable responses, skipping")
            continue

        mapping = dict(zip(LABELS, orders[task_index]))

        body = [f"# {tid} — {t['title']}",
                f"**Capability tested: {t['capability']}**",
                "Three models answered the identical prompt below in separate, fresh contexts. "
                "They are labelled A, B and C. **The labels are shuffled independently for this task**, "
                "so Model A here is not necessarily Model A on any other task.",
                "## Prompt", "```\n" + t["prompt"] + "\n```",
                f"Input material: [`prostate_public_packet.md`](../{t['input_files'][0]})",
                "## Expected elements (scoring anchors)",
                "Tick which of these each response contains. They are checkable against the material; "
                "they are not a complete definition of a good answer.",
                "\n".join(f"- {e}" for e in t["expected_elements"]),
                f"**Failure codes most likely to apply here:** {', '.join(t['common_failures'])}"]

        for lab in LABELS:
            m = mapping[lab]
            r = recs[m]
            key.append({"task_id": tid, "label": lab, "model": m, "arm": r["arm"],
                        "served_by": r["served_by"], "words": r["words"], "confidence": r["confidence"]})
            rows.append({
                "task_id": tid, "capability": t["capability"], "response": lab,
                "words": r["words"], "confidence": r["confidence"],
                **{c: "" for c in CORE}, **{f: 0 for f in FCODES},
                "novelty": "", "notes": "",
            })
            body += [f"## Response {lab}",
                     f"*{r['words']} words · stated confidence {r['confidence']}%*",
                     r["output"]]

        body.append(f"---\n\n[← all tasks](index.md) · [rubric](../scoring/rubric.md) · "
                    f"[failure taxonomy](../scoring/failure_taxonomy.md)")
        (ROOT / "review_blind").mkdir(exist_ok=True)
        (ROOT / "review_blind" / f"{tid}.md").write_text("\n\n".join(body) + "\n", encoding="utf-8")
        pages.append({"Task": f"[{tid}]({tid}.md)", "Capability": t["capability"], "Title": t["title"],
                      "Words A/B/C": " / ".join(str(recs[mapping[l]]["words"]) for l in LABELS),
                      "Confidence A/B/C": " / ".join(str(recs[mapping[l]]["confidence"]) for l in LABELS)})

    (ROOT / "private").mkdir(exist_ok=True)
    pd.DataFrame(key).to_csv(ROOT / "private" / "blinding_key.csv", index=False)
    # The refusal record is not blinded: it is a property of the model, not an answer to score.
    pd.DataFrame(refusals).to_csv(ROOT / "results" / "refusals.csv", index=False)

    df = pd.DataFrame(rows)
    cols = (["task_id", "capability", "response", "words", "confidence"]
            + CORE + FCODES + ["novelty", "notes"])
    df = df[cols]
    df.to_csv(ROOT / "scoring" / "blind_scores.csv", index=False)

    wb = Workbook()
    ws = wb.active
    ws.title = "scores"
    ws.append(cols)
    for _, r in df.iterrows():
        ws.append(list(r.values))
    n = len(df) + 1
    dv_score = DataValidation(type="whole", operator="between", formula1="1", formula2="5",
                              showErrorMessage=True, error="Score must be 1-5")
    dv_flag = DataValidation(type="whole", operator="between", formula1="0", formula2="1",
                             showErrorMessage=True, error="0 or 1")
    dv_nov = DataValidation(type="list", formula1='"Low,Medium,High,Cannot determine"')
    for dv in (dv_score, dv_flag, dv_nov):
        ws.add_data_validation(dv)
    for c in CORE:
        col = ws.cell(row=1, column=cols.index(c) + 1).column_letter
        dv_score.add(f"{col}2:{col}{n}")
    for f in FCODES:
        col = ws.cell(row=1, column=cols.index(f) + 1).column_letter
        dv_flag.add(f"{col}2:{col}{n}")
    col = ws.cell(row=1, column=cols.index("novelty") + 1).column_letter
    dv_nov.add(f"{col}2:{col}{n}")
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "D2"
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions[ws.cell(row=1, column=cols.index("notes") + 1).column_letter].width = 60

    ref = wb.create_sheet("failure_codes")
    for line in (ROOT / "scoring" / "failure_taxonomy.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("| F"):
            ref.append([x.strip() for x in line.strip("|").split("|")][:3])
    wb.save(ROOT / "scoring" / "blind_scores.xlsx")

    index = ["# Blind review: six tasks, three models",
             "Each page holds one task, its prompt, the scoring anchors, and the three responses labelled "
             "A, B and C. **Labels are shuffled independently on every task**, so you cannot carry an "
             "inference about identity from one task to the next.",
             "Score in [`scoring/blind_scores.xlsx`](../scoring/blind_scores.xlsx) using "
             "[the rubric](../scoring/rubric.md) and [the failure taxonomy](../scoring/failure_taxonomy.md).",
             pd.DataFrame(pages).to_markdown(index=False)]
    (ROOT / "review_blind" / "index.md").write_text("\n\n".join(index) + "\n", encoding="utf-8")

    print(f"blinded {len(df)} responses across {len(pages)} tasks")
    print("key -> private/blinding_key.csv (gitignored; do not open while scoring)")


if __name__ == "__main__":
    main()
