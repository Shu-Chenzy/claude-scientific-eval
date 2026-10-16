# Scoring rubric

Six dimensions, 1–5, applied to every response. Each task also has `expected_elements` in its
`tasks/T*.json` file: concrete, checkable points a strong answer should contain. Those are the
anchors; the scores below say how much a hit or a miss matters.

**Scoring is blind.** Responses are labelled Model A, B and C. The mapping to real model names is
not in this repository until scoring is finished.

## Procedure

1. Read the task prompt and the input packet.
2. Read the task's `expected_elements` and tick which ones the response contains.
3. Read the response. Score dimensions 1–5 **without looking at the stated confidence**.
4. Then read the confidence line and score **Uncertainty calibration**.
5. Mark each of the 15 failure codes 0 or 1 (`scoring/failure_taxonomy.md`).
6. Write one sentence in `notes` explaining the lowest score you gave.

Score each dimension independently: an answer can be biologically correct (5) and badly calibrated (2).
Score a response against the task's expected elements rather than against the other two responses —
but if a direct comparison is what decided a score, say so in `notes`.

## 1. Biological correctness

| Score | Anchor |
|---|---|
| 5 | Fully correct; no material biological error. |
| 4 | Essentially correct; a minor omission or error that would not change the decision. |
| 3 | Mixed; a meaningful error, but the answer is still partially useful. |
| 2 | A major biological error that affects the interpretation. |
| 1 | Fundamentally incorrect, or potentially misleading. |

Check: gene and protein function, pathway direction, drug mechanism and selectivity, assay physics,
model-system facts.

## 2. Evidence grounding

| Score | Anchor |
|---|---|
| 5 | Every claim traceable to the material, or explicitly labelled as outside knowledge. |
| 4 | Labelling mostly right; one claim slightly overstated or one value misread. |
| 3 | Outside knowledge mixed in unlabelled, but nothing invented. |
| 2 | Overstates what the data show, or quotes numbers not in the material. |
| 1 | Invents results, data or citations. |

Check every number against the packet, and every citation against the extracted list.

## 3. Causal and scientific reasoning

| Score | Anchor |
|---|---|
| 5 | Distinguishes correlation, necessity and sufficiency; raises confounds and alternatives unprompted. |
| 4 | Sound; misses one secondary alternative. |
| 3 | Main logic sound but misses an important confound. |
| 2 | A logical gap that undermines the conclusion. |
| 1 | The conclusion does not follow. |

## 4. Experimental feasibility

| Score | Anchor |
|---|---|
| 5 | Executable as written: model, reagents, readout, replicates, duration and scale all stated. |
| 4 | Executable, but scale or duration is missing. |
| 3 | Right idea, substantially under-specified, or one impractical element. |
| 2 | A major practical problem: wrong model, unrealistic timeline, or a reagent that does not exist. |
| 1 | Not executable. |

A design that is correct but uncosted is a 4, not a 5. Uncosted designs are the most common weakness, so apply this anchor strictly.

## 5. Falsifiability

| Score | Anchor |
|---|---|
| 5 | Explicit predictions plus a stated result that would reject the hypothesis, with a threshold where one is possible. |
| 4 | Clear predictions; the rejection criterion is implicit. |
| 3 | Predictions vague ("may affect", "could be involved"). |
| 2 | Mostly unfalsifiable framing. |
| 1 | No testable prediction. |

## 6. Uncertainty calibration

| Score | Anchor |
|---|---|
| 5 | Stated confidence fits the evidence; flags the uncertainties you would flag. |
| 4 | Slightly off in one direction. |
| 3 | Noticeably over- or under-confident, or hedges everything uniformly. |
| 2 | High confidence on a weak or wrong answer. |
| 1 | Confident and wrong on the key point. |

Score this last. A wrong answer at 30% confidence can earn a 4; a correct answer at 95% confidence
on thin evidence may earn a 3.

## Not scored

**Novelty**: recorded as Low / Medium / High / Cannot determine, never summed. "The model did not
cite prior work" is not evidence of novelty.

**Answer length** is recorded automatically and reported next to the scores, because a 2,500-word
answer to a question a paragraph would settle has a real cost. It is not scored.
