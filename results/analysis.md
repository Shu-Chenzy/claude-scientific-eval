# Results

Six tasks, three models, 18 responses, scored blind against the rubric in `scoring/rubric.md`.
Labels were revealed only after every score and failure code was fixed.

Scores: `scoring/blind_scores.csv`. Label mapping: `results/blinding_key.csv`.

## Overall

| Model | Mean core score | Mean words | Mean stated confidence | Failure flags | Refusals (primary arm) |
|---|---|---|---|---|---|
| Haiku 5.5 | 4.14 | 1,822 | 44% | 7 | 0 / 6 |
| Sonnet 5.5 | **4.47** | 1,772 | 53% | 6 | 0 / 6 |
| Opus 5.5 | 4.39 | 2,873 | 62% | 5 | **4 / 6** |

Scores span 3 to 5 with a standard deviation of 0.34 across responses, so the rubric separated the
three models rather than saturating. Sonnet 5.5 scored highest. The gap to Opus 5.5 is 0.08 points
on six tasks, which is well inside what a single scorer can resolve, so the honest reading is that
Sonnet and Opus are indistinguishable here and both are ahead of Haiku.

![overall](figures/01_overall_model_performance.png)

The Opus 5.5 row is not clean. Four of its six answers came from the fallback model after refusals
(below), so that row mixes two models. Its two genuine answers averaged 4.58 and the four fallback
answers 4.29, but with n = 2 that difference means nothing. It is a caveat, not a finding.

## Length does not buy quality

Spearman correlation between answer length and score is 0.03. Opus 5.5 wrote 62% more words than
Sonnet 5.5 and scored slightly lower. The longest answer in the set (3,854 words) and one of the
shortest (1,343 words) differ by 0.67 points in the direction that favours the short one on
feasibility.

For someone deciding what to do at the bench, this matters more than the overall ranking: a longer
answer is a longer read, not a better plan.

## Confidence tracks quality

Spearman correlation between stated confidence and expert score is 0.50 (n = 18). The models are
not merely hedging uniformly; when they said they were less sure, they were in fact weaker.

Confidence also separates the models in a way the scores do not. Haiku averaged 44%, Sonnet 53%,
Opus 62%. Since their scores are within 0.33 of each other, the most confident model is not the
most accurate one, and the least confident is not the worst by the margin its confidence suggests.

## By capability

![capability](figures/02_by_capability.png)

| Capability | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| Evidence grounding | 4.67 | 4.67 | 4.67 |
| Experimental design, controls, falsifiability | 4.00 | 4.67 | 4.67 |
| Mechanistic and causal reasoning | 4.17 | 4.50 | 4.50 |
| Quantitative assay design | 3.83 | 4.50 | 4.50 |
| Closed-loop decision-making | 4.50 | 4.50 | 3.83 |
| Target prioritization | 3.67 | 4.00 | 4.17 |

Two results stand out.

**Target prioritization is the weakest capability for every model** (3.67 to 4.17), and it is the
only task where all three lost points on the same thing. Evidence grounding is the strongest and is
identical across all three, which says the task is no longer discriminating and should be made
harder in the next version.

**Haiku 5.5 beat Opus 5.5 on closed-loop decision-making** (4.50 against 3.83). The cheapest model
produced the better-gated plan on the task that most resembles a real programme decision. Whatever
the larger model is buying, it is not judgement about when to stop.

## Failure modes

![failures](figures/03_failure_modes.png)

Eighteen flags across 18 responses; 12 of 18 responses carry at least one. Six of the fifteen codes
fired. The distribution is the most useful part of the result:

| Code | Haiku | Sonnet | Opus | Where |
|---|---|---|---|---|
| F11 poor prioritization | 2 | 2 | 2 | T3 and T5, **all three models in both** |
| F07 incorrect experimental logic | 2 | 1 | 1 | T4 (all three), T6 (Haiku) |
| F13 unnecessary experimentation | 1 | 1 | 1 | T4, T5 |
| F05 missing critical control | 1 | 1 | 0 | T4 |
| F02 unsupported mechanism | 1 | 0 | 1 | T2, T6 |
| F06 infeasible experiment | 0 | 1 | 0 | T3 |

**The failures are a property of the task, not of the model.** F11 fired on all three models in both
T3 and T5. F07 fired on all three in T4. No code fired on one model alone more than twice. Picking a
more capable model would not have avoided any of these six responses.

The two systematic errors, in the reviewer's words:

1. **Prioritizing a weakly supported candidate over the reproducible signal.** In T3 and T5 every
   model led with a gene that failed the replication threshold in the provided data, rather than
   with the signal that replicated. One response elevated a candidate that both failed replication
   and reversed sign between cohorts. Another chose a target that depends on reagents the stated
   four-week resource set does not guarantee. This is the error with a direct cost: it is the one
   that sends a lab after the wrong gene.

2. **Treating a failed rescue as decisive.** In T4 all three models read "the rescue construct did
   not restore the phenotype" as evidence against on-target causality. A failed rescue is usually
   weak or technically ambiguous: the construct may be non-functional, mislocalised, the wrong
   isoform, or expressed at the wrong level. Reading it as a clean negative would retire a real
   target.

Two further observations from scoring, outside the codes: several designs were judged on
theoretical feasibility while overlooking practical difficulty, with low knock-in efficiency making
a tag-based receptor readout impractical in two cases; and the scoring picked out one response
whose candidate choice followed the data rather than the framing of the prompt, which is the
behaviour worth wanting.

## Refusals

With server-side fallbacks disabled, Opus 5.5 declined four of six prompts, all with
`stop_details.category = "bio"`. Haiku 5.5 and Sonnet 5.5 answered all six. Each refused prompt was
re-sent twice under identical conditions and refused every time, so the behaviour is deterministic
for these prompts rather than sampling variation.

| | T1 | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|---|
| Haiku 5.5 | answered | answered | answered | answered | answered | answered |
| Sonnet 5.5 | answered | answered | answered | answered | answered | answered |
| Opus 5.5 | answered | answered | refused | refused | refused | refused |

The split is clean. Opus 5.5 answered the two tasks that ask what the provided data support, and
declined the four that ask what experiment to run next: target prioritization, experimental design,
the go/no-go decision, and assay design. Those are the questions an experimental lab actually needs
answered, and they are standard published oncology methodology.

This is only visible because fallbacks were off. With them on, the API answers using a different
model inside the same call; a comparison that did not record `served_by` would attribute those four
answers to Opus 5.5. Details and the repeat-attempt record: `results/refusal_summary.md`.

## What this says about using these models at the bench

The models are reliable at reading evidence. All three scored 4.67 on evidence grounding, nothing
was fabricated, and the one literature citation in the set checks out. Where they are weak is
deciding what to do with the evidence: which candidate to spend four weeks on, and when a negative
result is real. Both weak points are failures of judgement under constraint, and both were
model-independent.

So the division of labour that the data support is: use the model to organise evidence, enumerate
alternatives and draft controls, and keep the prioritization decision and the interpretation of
negatives with the experimentalist. That is not a general claim about model capability. It is what
these six tasks showed on this packet.

## Limitations

- One scorer, no second reviewer, so inter-rater reliability is unmeasured.
- Six tasks and 18 responses. Differences below roughly 0.3 points are not resolvable.
- One shared input packet correlates difficulty across tasks.
- Four of six Opus 5.5 answers came from the fallback model, so that row is not a clean measurement
  of one model.
- One run per task. No sampling variation was measured for the answers, only for the refusals.
- Effort was fixed at `high` for all three models, but effort levels are calibrated per model, so
  this equalises the instruction rather than the compute.
- Evidence grounding no longer discriminates and should be made harder before it is reused.
