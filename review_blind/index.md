# Blind review: six tasks, three models

Each page holds one task, its prompt, the scoring anchors, and the three responses labelled A, B and C. **Labels are shuffled independently on every task**, so you cannot carry an inference about identity from one task to the next.

Score in [`scoring/blind_scores.xlsx`](../scoring/blind_scores.xlsx) using [the rubric](../scoring/rubric.md) and [the failure taxonomy](../scoring/failure_taxonomy.md).

| Task        | Capability                                       | Title                                                       | Words A/B/C        | Confidence A/B/C   |
|:------------|:-------------------------------------------------|:------------------------------------------------------------|:-------------------|:-------------------|
| [T1](T1.md) | Evidence grounding                               | Separate evidence, inference and speculation                | 1760 / 2155 / 2497 | 72 / 60 / 70       |
| [T2](T2.md) | Mechanistic and causal reasoning                 | Competing mechanisms and the limits of causal inference     | 1523 / 1697 / 2610 | 35 / 30 / 30       |
| [T3](T3.md) | Target prioritization                            | Prioritize candidates under uncertainty and resource limits | 3632 / 1605 / 1542 | 70 / 28 / 55       |
| [T4](T4.md) | Experimental design, controls and falsifiability | Minimum causal experiment with controls and a rescue arm    | 1503 / 1862 / 1343 | 66 / 72 / 40       |
| [T5](T5.md) | Closed-loop scientific decision-making           | Hypothesis to experiment to feedback                        | 2782 / 1618 / 1727 | 65 / 75 / 40       |
| [T6](T6.md) | Quantitative assay design                        | Quantify a low-abundance cell-surface GPCR                  | 2576 / 3854 / 2510 | 58 / 72 / 62       |
