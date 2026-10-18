# Multi-Model Scientific Evaluation v1.0 — experimental and translational cancer biology

Shu Chen, Postdoctoral Scholar, UCSF

Six expert-curated tasks spanning the scientific decision loop, answered by three frontier models under identical conditions, scored blind by a domain expert against a predefined rubric and failure taxonomy.

The question behind it: *when a model's output could decide what a lab spends the next several weeks doing, how much should we trust it — and does a more capable model actually make fewer experimentally consequential mistakes?*

This is deliberately a pilot: six high-information tasks spanning the decision loop, rather than broad benchmark coverage.

## Design

| Task | Capability | What it tests |
|---|---|---|
| [T1](review_blind/T1.md) | Evidence grounding | Separating direct evidence from inference and speculation; detecting statements that exceed the data |
| [T2](review_blind/T2.md) | Mechanistic and causal reasoning | Correlation versus causation; generating genuinely distinct competing mechanisms |
| [T3](review_blind/T3.md) | Target prioritization | Choosing what to test first under fixed time and resources |
| [T4](review_blind/T4.md) | Experimental design, controls, falsifiability | A minimal causal experiment, the controls that make it interpretable, and a rescue arm |
| [T5](review_blind/T5.md) | Closed-loop decision-making | Hypothesis → evidence → experiment → stop rules → feedback |
| [T6](review_blind/T6.md) | Quantitative assay design | Measuring a low-abundance cell-surface GPCR well enough to compare two conditions |

T1–T5 each bundle several related questions, so one answer exercises a whole step of the loop rather than a fragment. T6 is the one task with a largely settled right answer, which makes it the best test of whether a model knows a field's practical methods rather than its vocabulary.

**Controlled comparison.** Every model receives the identical prompt, the identical input packet, the identical output schema, and `effort: high`, each in a fresh context with no history. Model, version, effort, token counts and the model that actually served the request are recorded with every response.

**Refusals are recorded, not routed around.** Server-side refusal fallbacks are disabled in the primary arm. With fallbacks on, a declined prompt is answered by a different model inside the same call, which silently contaminates a model comparison. Here a refusal is recorded as a refusal, so refusal rate is itself a comparable metric, and a separate clearly-labelled fallback arm supplies an answer to score where a model declined.

**Blind scoring.** Responses are presented as Model A, B and C, and the labels are **shuffled independently on every task**, so an inference about identity on one task cannot be carried to the next. The mapping stays out of this repository until scoring is complete.

## Scoring

Six dimensions, 1–5, with written anchors ([`scoring/rubric.md`](scoring/rubric.md)): biological correctness, evidence grounding, causal reasoning, experimental feasibility, falsifiability, uncertainty calibration. Each task additionally carries `expected_elements` — concrete, checkable points a strong answer should contain — which serve as the per-task anchors.

Every response is then marked 0 or 1 against all 15 codes of the failure taxonomy ([`scoring/failure_taxonomy.md`](scoring/failure_taxonomy.md)), from hallucinated evidence through missing controls to clinically unrealistic recommendations. Marking all 15 on every response, rather than only noting the ones that fire, is what makes failure rates comparable between models.

6 tasks × 3 models × 6 dimensions = **108 scored points**, plus 270 failure-code judgements.

Novelty is recorded but never summed. Answer length is recorded and reported next to the scores but not scored.

## Data

All tasks share one input packet: [`inputs/public/prostate_public_packet.md`](inputs/public/prostate_public_packet.md), built from my public prostate cancer analysis ([prostate-ai-hypothesis-evaluation](https://github.com/Shu-Chenzy/prostate-ai-hypothesis-evaluation)) using GEO GSE35988 and SU2C/PCF 2019 data.

The packet contains **expression statistics only** — no perturbation, drug, organoid or animal data. Several prompts deliberately ask about things it does not contain. A strong answer says what is missing; a weak one invents it.

Unpublished work is **not** in this repository.

## First result: refusals

This came out of the run itself, before any scoring, and it is the reason the fallback arm exists.

| Model | Tasks | Refused | Rate |
|---|---|---|---|
| Haiku 5.5 | 6 | 0 | 0% |
| Sonnet 5.5 | 6 | 0 | 0% |
| **Opus 5.5** | 6 | **4** | **67%** |

Opus 5.5 declined T3, T4, T5 and T6 — target prioritization, experimental design, the go/no-go
decision, and the assay-design task — all with `stop_details.category = "bio"`. It answered T1 and
T2. The split is clean: it answered the two tasks that ask what the provided data support, and
declined the four that ask what experiment to run next. Haiku 5.5 and Sonnet 5.5 answered all six.

Each refused prompt was sent again twice under identical conditions. **All three attempts refused
every time**, so this is deterministic for these prompts rather than sampling noise.
Details: [`results/refusal_summary.md`](results/refusal_summary.md).

This is only visible because the primary arm runs with fallbacks disabled. With fallbacks on, the
API answers the prompt using a different model inside the same call, and a comparison that did not
record `served_by` would silently attribute those answers to Opus 5.5.

## Status

| Step | State |
|---|---|
| Tasks defined, anchors written | done |
| Responses generated, 3 models × 6 tasks | done |
| Refusals characterised and repeat-tested | done |
| Responses blinded, scoring sheet built | done |
| **Expert scoring** | **in progress** |
| Unblinding, analysis, figures | pending scoring |

**No quality scores are published yet.** The comparison in `results/` will be generated from the
expert's completed sheet. Nothing here should be cited as a model-quality comparison until then;
the refusal rates above are measured, not scored.

## Reproduce

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python scripts/build_packet.py ../prostate-ai-hypothesis-evaluation   # rebuild the input packet
python scripts/build_tasks_v1.py                                      # write the six tasks
python scripts/run_models.py                                          # 3 models x 6 tasks, fresh context each
python scripts/extract_citations.py --model claude-opus-5-5           # references to verify
python scripts/retry_refusals.py --attempts 2                          # are refusals reproducible?
python scripts/run_models.py --models claude-opus-5-5 --fallback       # labelled fallback arm
python scripts/summarize_refusals.py                                   # refusal tables
python scripts/blind_and_build_sheet.py                               # blind + scoring sheet + review pages
# expert fills in scoring/blind_scores.xlsx, then:
python scripts/analyze_blind.py --publish-key
```

## Repository layout

```
├── tasks/                  the six tasks, with prompts and scoring anchors
├── inputs/public/          the shared input packet
├── outputs/<model>/        raw responses, one directory per model
├── review_blind/           per-task pages: prompt, anchors, three blinded responses
├── scoring/                rubric, failure taxonomy, blind scoring sheet
├── results/                tables and figures (after scoring)
└── scripts/
```

## Contact

Shu Chen · shu.chen@ucsf.edu · [LinkedIn](https://www.linkedin.com/in/shu-chen-170111323/) · [Google Scholar](https://scholar.google.com/citations?hl=en&user=WkITc2YAAAAJ)
