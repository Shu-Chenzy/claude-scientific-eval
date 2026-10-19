# Failure taxonomy

Each response is marked **0 or 1 against every one of the 15 codes**: 0 if the failure does not
appear, 1 if it does. A response can score 0 everywhere, or fire several codes. Labels describe
*what went wrong*; the rubric scores describe *how much it matters*.

Counting all 15 codes on every response, rather than only noting the ones that fire, is what makes
failure rates comparable between models.

| Code | Label | Use when | Example |
|---|---|---|---|
| F01 | Hallucinated evidence | A number, result, citation or dataset is stated as fact but is not in the input and is not real or verifiable. | Cites "Smith et al. 2019" for a finding that does not exist. |
| F02 | Unsupported mechanism | A mechanism is asserted as established when the input only shows association. | "Gene X drives resistance through AKT" when only expression data were given. |
| F03 | Correlation interpreted as causation | Co-occurrence treated as cause. | Lower expression in resistant tumors -> "loss causes resistance." |
| F04 | Missing alternative explanation | A plausible competing explanation the input invites is not considered. | Ignores reverse causation, cell composition, or proliferation effects. |
| F05 | Missing critical control | An experiment lacks the control needed to interpret it. | Knockout without rescue; drug without on-target confirmation. |
| F06 | Infeasible experiment | Cannot be done as described with realistic resources. | Genome-wide in vivo screen with 3 PDOs in 4 weeks. |
| F07 | Incorrect experimental logic | The experiment would not answer the stated question. | Overexpression in a line that already expresses high levels. |
| F08 | Overconfident conclusion | Certainty exceeds the evidence. | 90% confidence on a single-cell-line result. |
| F09 | Failure to identify contradiction | Contradictory results in the input are not noticed, or are averaged away. | Reports "consistent with mechanism" when one assay disagrees. |
| F10 | Known idea presented as novel | Established knowledge framed as a new hypothesis. | Proposes AR amplification as a new resistance mechanism. |
| F11 | Poor target prioritization | Ranking ignores a decisive property in the input. | Ranks a stromal or essential housekeeping gene first. |
| F12 | Ignored negative evidence | Data against the hypothesis are present but not used. | Ignores the null result in the second model. |
| F13 | Excessive / unnecessary experimentation | Proposes many experiments where a few decide the question. | 12 experiments when 2 would discriminate. |
| F14 | Clinically unrealistic recommendation | Recommendation ignores trial, regulatory or patient reality. | Phase 3 trial from one PDX result. |
| F15 | Correct conclusion for incorrect reason | Right answer, wrong justification. | Ranks the right target first because of fold change alone. |

## Tips for consistent labeling

- **F01 vs F02:** F01 is invented *evidence*; F02 is an over-claimed *interpretation* of real evidence.
- **F03 vs F08:** if the response explicitly says "causes", use F03; if it hedges but still gives high confidence, use F08.
- **F04 vs F09:** F09 is only for contradictions that are *in the provided input*. Missing an outside possibility is F04.
- **F05 vs F07:** a missing control is F05; a design that answers a different question is F07.
- Each task lists expected elements in its `tasks/T*.json` file. If a response misses one, there is usually a label that applies.
