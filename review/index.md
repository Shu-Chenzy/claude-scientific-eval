# Six-task review

Each page contains the task, scoring anchors, unblinded responses, scores, and reviewer notes. Scoring itself was performed blind; `review_blind/` preserves that version.

| Task        | Capability                                       |   Haiku 5.5 |   Sonnet 5.5 | Opus 5.5 request   |   Flags |
|:------------|:-------------------------------------------------|------------:|-------------:|:-------------------|--------:|
| [T1](T1.md) | Evidence grounding                               |        4.67 |         4.67 | 4.67               |       0 |
| [T2](T2.md) | Mechanistic and causal reasoning                 |        4.17 |         4.5  | 4.50               |       1 |
| [T3](T3.md) | Target prioritization                            |        3.67 |         4    | 4.17*              |       4 |
| [T4](T4.md) | Experimental design, controls and falsifiability |        4    |         4.67 | 4.67*              |       6 |
| [T5](T5.md) | Closed-loop scientific decision-making           |        4.5  |         4.5  | 3.83*              |       5 |
| [T6](T6.md) | Quantitative assay design                        |        3.83 |         4.5  | 4.50*              |       2 |

*For T3–T6, the Opus 5.5 request was refused. The starred score is from the separate Opus 5 fallback arm and is not an Opus 5.5 measurement.*

[Full results](../results/analysis.md) · [per-response scores](../scoring/blind_scores.csv)
