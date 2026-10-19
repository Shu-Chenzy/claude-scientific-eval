# Multi-Model Scientific Evaluation v1.0 — experimental and translational cancer biology

Shu Chen, Postdoctoral Scholar, UCSF

Six expert-curated tasks spanning the scientific decision loop, answered by three frontier models under identical conditions, scored blind by a domain expert against a predefined rubric and failure taxonomy.

The question behind it: *when a model's output could decide what a lab spends the next several weeks doing, how much should we trust it — and does a more capable model actually make fewer experimentally consequential mistakes?*

This is deliberately a pilot: six high-information tasks spanning the decision loop, rather than broad benchmark coverage.

## Design

| Task | Capability | What it tests |
|---|---|---|
| [T1](review/T1.md) | Evidence grounding | Separating direct evidence from inference and speculation; detecting statements that exceed the data |
| [T2](review/T2.md) | Mechanistic and causal reasoning | Correlation versus causation; generating genuinely distinct competing mechanisms |
| [T3](review/T3.md) | Target prioritization | Choosing what to test first under fixed time and resources |
| [T4](review/T4.md) | Experimental design, controls, falsifiability | A minimal causal experiment, the controls that make it interpretable, and a rescue arm |
| [T5](review/T5.md) | Closed-loop decision-making | Hypothesis → evidence → experiment → stop rules → feedback |
| [T6](review/T6.md) | Quantitative assay design | Measuring a low-abundance cell-surface GPCR well enough to compare two conditions |

T1–T5 each bundle several related questions, so one answer exercises a whole step of the loop rather than a fragment. T6 is the one task with a largely settled right answer, which makes it the best test of whether a model knows a field's practical methods rather than its vocabulary.

**Controlled comparison.** Every model receives the identical prompt, the identical input packet, the identical output schema, and `effort: high`, each in a fresh context with no history. Model, version, effort, token counts and the model that actually served the request are recorded with every response.

**Refusals are recorded, not routed around.** Server-side refusal fallbacks are disabled in the primary arm. With fallbacks on, a declined prompt is answered by a different model inside the same call, which silently contaminates a model comparison. Here a refusal is recorded as a refusal, so refusal rate is itself a comparable metric, and a separate clearly-labelled fallback arm supplies an answer to score where a model declined.

**Blind scoring.** Responses are presented as Model A, B and C, and the labels are **shuffled independently on every task**, so an inference about identity on one task cannot be carried to the next. The mapping was kept out of this repository until scoring was complete; it is now in
`results/blinding_key.csv`.

## Scoring

Six dimensions, 1–5, with written anchors ([`scoring/rubric.md`](scoring/rubric.md)): biological correctness, evidence grounding, causal reasoning, experimental feasibility, falsifiability, uncertainty calibration. Each task additionally carries `expected_elements` — concrete, checkable points a strong answer should contain — which serve as the per-task anchors.

Every response is then marked 0 or 1 against all 15 codes of the failure taxonomy ([`scoring/failure_taxonomy.md`](scoring/failure_taxonomy.md)), from hallucinated evidence through missing controls to clinically unrealistic recommendations. Marking all 15 on every response, rather than only noting the ones that fire, is what makes failure rates comparable between models.

6 tasks × 3 models × 6 dimensions = **108 scored points**, plus 270 failure-code judgements.

Novelty is recorded but never summed. Answer length is recorded and reported next to the scores but not scored.

## Data

All tasks share one input packet: [`inputs/public/prostate_public_packet.md`](inputs/public/prostate_public_packet.md), built from my public prostate cancer analysis ([prostate-ai-hypothesis-evaluation](https://github.com/Shu-Chenzy/prostate-ai-hypothesis-evaluation)) using GEO GSE35988 and SU2C/PCF 2019 data.

The packet contains **expression statistics only** — no perturbation, drug, organoid or animal data. Several prompts deliberately ask about things it does not contain. A strong answer says what is missing; a weak one invents it.

Unpublished work is **not** in this repository.

**[→ All six tasks: prompt, the three responses, scores and notes](review/index.md)**

## Results

Full write-up with figures: **[`results/analysis.md`](results/analysis.md)**. Per-response scores:
[`scoring/blind_scores.csv`](scoring/blind_scores.csv).

| Model | Mean core score | Mean words | Mean confidence | Failure flags | Refusals |
|---|---|---|---|---|---|
| Haiku 5.5 | 4.14 | 1,822 | 44% | 7 | 0 / 6 |
| Sonnet 5.5 | **4.47** | 1,772 | 53% | 6 | 0 / 6 |
| Opus 5.5 | 4.39 | 2,873 | 62% | 5 | **4 / 6** |

![overall](results/figures/01_overall_model_performance.png)

Scores ran from 3 to 5 (sd 0.34), so the rubric separated the models instead of saturating. Sonnet
5.5 came out on top, but its 0.08-point lead over Opus 5.5 is inside what one scorer can resolve on
six tasks: Sonnet and Opus are indistinguishable here, and both are ahead of Haiku.

**The failures belong to the tasks, not the models.** Eighteen failure flags were assigned across
18 responses. The two commonest fired on every model:

- **Poor prioritization (F11)** hit all three models on both T3 and T5. Each one led with a
  candidate that had failed the replication threshold in the provided data instead of the signal
  that replicated. This is the error that costs bench time.
- **Incorrect experimental logic (F07)** hit all three on T4, where each treated a failed rescue as
  decisive evidence against on-target causality. A failed rescue is usually ambiguous, and reading
  it as a clean negative would retire a real target.

Choosing a more capable model would not have prevented any of these.

**Length bought nothing.** Correlation between answer length and score was 0.03. Opus 5.5 wrote 62%
more words than Sonnet 5.5 and scored marginally lower.

**Confidence was informative.** Correlation between stated confidence and expert score was 0.50, so
the models were weaker where they said they were less sure. They differ in baseline though: Haiku
averaged 44% confidence, Opus 62%, for scores 0.25 apart.

**Target prioritization was the weakest capability for all three** (3.67–4.17), and evidence
grounding the strongest and identical across all three (4.67), which means that task no longer
discriminates and needs to be made harder.

**Haiku 5.5 beat Opus 5.5 on closed-loop decision-making** (4.50 against 3.83), the task closest to
a real programme decision.

### Refusals

With fallbacks disabled, Opus 5.5 declined four of six prompts, all under
`stop_details.category = "bio"`. Haiku 5.5 and Sonnet 5.5 answered all six. Every refused prompt was
re-sent twice under identical conditions and refused each time, so this is deterministic rather than
sampling noise.

| | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|
| Haiku 5.5 | answered | answered | answered | answered | answered | answered |
| Sonnet 5.5 | answered | answered | answered | answered | answered | answered |
| Opus 5.5 | answered | answered | refused | refused | refused | refused |

Opus 5.5 answered the two tasks that ask what the data support and declined the four that ask what
experiment to run next. Those four are standard published oncology methodology, and they are the
questions a lab actually needs answered. A separate labelled fallback arm supplied answers for them
so the comparison could proceed; those four rows therefore mix two models, which is noted wherever
Opus 5.5 is reported. Details: [`results/refusal_summary.md`](results/refusal_summary.md).

### How I would use these models at the bench

All three were reliable at reading evidence: nothing was fabricated, and the single literature
citation in the set checks out. The weakness was deciding what to do with the evidence — which
candidate deserves four weeks, and when a negative result is real — and that weakness did not
improve with model size. On this evidence I would use a model to organise evidence, enumerate
alternatives and draft controls, and keep prioritization and the reading of negative results with
the experimentalist.

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
python scripts/build_review_pages.py                                  # unblinded per-task pages
```

## Repository layout

```
├── tasks/                  the six tasks, with prompts and scoring anchors
├── inputs/public/          the shared input packet
├── outputs/<model>/        raw responses, one directory per model
├── review_blind/           what was scored: prompt, anchors, three blinded responses
├── review/                 same pages unblinded, with scores and notes
├── scoring/                rubric, failure taxonomy, completed scores
├── results/                scores unblinded: tables, figures, refusal record
└── scripts/
```

## Contact

Shu Chen · shu.chen@ucsf.edu · [LinkedIn](https://www.linkedin.com/in/shu-chen-170111323/) · [Google Scholar](https://scholar.google.com/citations?hl=en&user=WkITc2YAAAAJ)
