"""Write the five pilot tasks (tasks/T1.json ... T5.json).

    python scripts/build_tasks_v1.py

Each task bundles several related questions so that one answer exercises a whole step of the
scientific decision loop. `expected_elements` are checkable against the input packet
and are the scoring anchors; they are never sent to the model.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = "inputs/public/prostate_public_packet.md"

SCHEMA = """
Structure your answer under these headings:
1. Main conclusion / recommendation
2. Evidence (Direct evidence; Indirect evidence)
3. Reasoning
4. Assumptions
5. Alternative explanations
6. Proposed experiment / next step
7. Key controls
8. What would falsify the hypothesis?
9. Uncertainty / limitations
10. Confidence: a single number from 0 to 100%
""".strip()

TASKS = [
{
 "task_id": "T1",
 "capability": "Evidence grounding",
 "title": "Separate evidence, inference and speculation",
 "covers": ["evidence classification", "unsupported-claim detection"],
 "prompt": """Using only the provided material, identify the three strongest conclusions it supports.

For each conclusion, state separately:
- what is directly demonstrated by the data shown,
- what is interpretation added on top of the data,
- what remains uncertain.

Then list every statement in the material that goes beyond the evidence shown, and for each one state the minimum additional evidence that would be needed to support it.

Do not introduce results, mechanisms or literature that are not in the provided material. If you use outside knowledge anywhere, label it explicitly as outside knowledge.""",
 "expected_elements": [
   "Notes that the pre-specified gene SSTR1 does not meet the material's own replication threshold (tier 2; site-adjusted p = 0.077; FDR 0.334).",
   "Flags that the claim 'TRPM8 and DPP4 are androgen-regulated' is asserted in the material without any supporting data.",
   "Flags the lymph-node/bone site-concentration claim as having no per-site numbers, sample sizes or interaction test behind it.",
   "Flags that the referenced bench result is not included, so any claim of consistency with it cannot be assessed.",
   "Distinguishes the computed results (differential expression, composition correlations, enrichment, replication statistics) from the interpretation placed on them.",
   "Notes that the composition correlation was computed only within localized tumours, so it cannot establish cell of origin.",
 ],
 "common_failures": ["F01", "F02", "F03", "F08"],
},
{
 "task_id": "T2",
 "capability": "Mechanistic and causal reasoning",
 "title": "Competing mechanisms and the limits of causal inference",
 "covers": ["causal versus correlational evidence", "competing mechanisms"],
 "prompt": """The material reports that a candidate gene is expressed at lower levels in treatment-resistant disease.

1. Identify which analysis in the material comes closest to supporting causality rather than correlation. State what causal link it supports, which alternative explanations its design excludes, and which remain open.
2. Propose three mechanistically distinct explanations for the lower expression. For each, give the observation it predicts, an experiment that could falsify it, and the specific result that would argue against it.
3. State which of the three the material best supports, and how confident that judgement can be.

Treat the authors' preferred explanation as one hypothesis among several, not as the default.""",
 "expected_elements": [
   "States that no analysis in the material establishes causality; all are observational.",
   "Identifies the independent-cohort treatment-exposure comparison as the closest to causal, and says why (exposure precedes measurement; disease stage and sample type held roughly constant; site adjusted; positive control behaves as expected).",
   "Names confounding by indication / treatment history, clonal selection, and lineage shift as alternatives the design does not exclude.",
   "Gives three mechanisms that are genuinely distinct rather than restatements, separable by kinetics, reversibility or cell-level distribution.",
   "Notes that exposure is not the same as resistance, so 'decreases after resistance develops' is an inference the data do not directly support.",
   "Notes that the reported correlation with pathway activity is weak (rho 0.19, about 4% of variance).",
 ],
 "common_failures": ["F02", "F03", "F04", "F09"],
},
{
 "task_id": "T3",
 "capability": "Target prioritization",
 "title": "Prioritize candidates under uncertainty and resource limits",
 "covers": ["ranking under constraints", "missing-data identification", "objective sensitivity"],
 "prompt": """From the candidates in the provided material, choose the two you would test first with four weeks of experimental time and the following resources: CRISPR knockout and CRISPRi, live-cell imaging, drug treatment, and a small number of patient-derived organoid models.

For your two choices give: the reasoning, the major risk, and the first experiment.

Then state:
- what information the material does not contain that you would need, and which single missing data point would most change your decision;
- how your ranking would change if the objective were instead (a) largest biological effect, or (b) fastest experimental validation;
- which candidates you are deprioritizing and why.

Be explicit about what you are assuming where the material is silent.""",
 "expected_elements": [
   "Uses the decisive columns in the table: independent replication, effect size, expression level in the replication cohort, composition correlation, and annotated protein class or surface location.",
   "Notes that every replicated candidate is lower in the resistant state, so inhibition is the wrong therapeutic logic and the perturbation direction must be re-expression rather than knockout.",
   "Deprioritizes candidates whose expression is near the detection floor, and the ones that reverse direction between the two cohorts.",
   "Flags the columns the question presumes but the material lacks (dependency scores, druggability, normal-tissue expression) instead of inventing them.",
   "Names a concrete single missing data point, most defensibly protein-level measurement in the relevant tissue, and says why it would move the ranking.",
   "Gives a different ranking under the different objectives rather than repeating one list.",
 ],
 "common_failures": ["F11", "F15", "F08", "F12"],
},
{
 "task_id": "T4",
 "capability": "Experimental design, controls and falsifiability",
 "title": "Minimum causal experiment with controls and a rescue arm",
 "covers": ["minimal causal design", "control selection", "rescue logic", "proliferation confound"],
 "prompt": """Design the minimum experiment that would determine whether loss of a candidate gene causally contributes to treatment resistance.

Include:
- the intervention and the model system,
- the readout and the primary endpoint,
- the controls needed to separate a target-specific effect from nonspecific toxicity, from a proliferation artifact, and from a transduction or editing artifact,
- a rescue strategy and what it would and would not establish,
- the expected result if the hypothesis is true,
- an explicit result that would falsify it,
- scale: replicates, duration, and anything that makes this infeasible as described.

Keep the design minimal. Do not include experiments that would not change the conclusion.""",
 "expected_elements": [
   "Frames the causal quantity as a genotype-by-treatment interaction, not a single-arm viability difference.",
   "Identifies the proliferation confound explicitly: a perturbation that slows growth will reduce an endpoint viability signal regardless of any drug-specific effect, so within-genotype normalization or growth-rate-corrected metrics are required.",
   "Includes two or more independent targeting reagents and a perturbation-resistant rescue construct.",
   "Distinguishes vector, selection and cutting controls from non-targeting controls.",
   "States that successful rescue is strong evidence while failed rescue is weak evidence, and that partial rescue is ambiguous.",
   "Includes a positive control establishing that the assay can detect a real effect, so a negative result is interpretable.",
   "States replicates and duration, and notes the expression level required for the perturbation to be readable at all.",
   "Notes that the candidate is lower in the resistant state, so knockout in an already-low background may be uninformative.",
 ],
 "common_failures": ["F05", "F06", "F07", "F13"],
},
{
 "task_id": "T5",
 "capability": "Closed-loop scientific decision-making",
 "title": "Hypothesis to experiment to feedback",
 "covers": ["hypothesis selection", "decision gates", "go/no-go", "feedback"],
 "prompt": """Using the provided material, produce a single prioritized hypothesis that is worth spending wet-lab resources on, and the plan around it.

Give:
1. the hypothesis, and why this one rather than the alternatives you considered;
2. the evidence supporting it, and the evidence against it;
3. one falsifiable prediction;
4. the minimal validation plan, with the decision gate at each step and the result that would stop the programme;
5. a go / no-go / need-more-data recommendation, naming the strongest evidence, the biggest uncertainty, and the experiment with the highest decision value;
6. what should be fed back into the next round of analysis, whichever way the experiment goes.

Mark every claim as evidence, inference or speculation. Do not propose experiments that would not change the decision.""",
 "expected_elements": [
   "Selects a hypothesis built on the most reproducible signal in the material rather than the most interesting one, and says why the alternatives were rejected.",
   "States the evidence against its own hypothesis, not only the evidence for it.",
   "Returns need-more-data or no-go rather than go, given that the material contains expression data only.",
   "Names the experiment with the highest decision value and what each outcome would mean.",
   "Includes an explicit stop rule at one or more gates.",
   "Lists experiments deliberately excluded because they would not change the decision.",
   "Keeps the evidence / inference / speculation labelling consistent through the answer.",
   "Notes that the therapeutic logic is constrained by the direction of the change.",
 ],
 "common_failures": ["F08", "F13", "F14", "F10"],
},
{
 "task_id": "T6",
 "capability": "Quantitative assay design",
 "title": "Quantify a low-abundance cell-surface GPCR",
 "covers": ["assay selection", "specificity controls", "detection limits"],
 "prompt": """The material's central limitation is that it measures mRNA, and states that for a ligand-based therapy the quantity that matters is cell-surface receptor protein. The candidate is a G-protein-coupled receptor whose transcript level in the metastatic cohort is low.

Design the measurement that resolves this gap. You must produce a number that can be compared between treated and untreated samples, not a presence/absence call.

Address:
1. Which assay you would use, and why that one rather than the alternatives you considered. Name the alternatives and the reason each was rejected.
2. What quantity the assay actually reports, and whether that is receptors per cell, a relative signal, or something else.
3. How you establish that the signal is the intended receptor and not background or a related family member.
4. How you distinguish receptor at the cell surface from receptor in intracellular compartments.
5. The detection limit problem: what the assay's sensitivity has to be for this target, and what you do if the receptor is near or below it.
6. How the approach changes between cultured cells, patient-derived models, and archival patient tissue.
7. The replicate structure and the normalization that make two conditions comparable.

State clearly which parts of your answer are standard practice and which are your judgement.""",
 "expected_elements": [
   "Names radioligand binding (saturation binding giving Bmax and Kd) as the method that yields receptors per cell, and treats it as the quantitative reference rather than a western blot.",
   "Identifies antibody specificity as the central risk: commercial GPCR antibodies are frequently non-specific, so any antibody-based readout requires a knockout or knockdown control, not an isotype control alone.",
   "Separates surface from total receptor explicitly: non-permeabilized flow cytometry, surface biotinylation, or binding with a non-cell-permeant ligand, rather than whole-cell lysate.",
   "Addresses subtype cross-reactivity within the receptor family, for example by competition with a subtype-selective ligand or by testing a receptor-null line.",
   "Proposes an epitope or tag knock-in at the endogenous locus, or targeted mass spectrometry with heavy-labelled peptide standards, as the route when antibodies fail.",
   "Confronts the low-abundance problem directly: states a sensitivity requirement, and gives a fallback when the target is near the detection limit rather than assuming the assay will work.",
   "Treats archival tissue differently from live cells, noting that binding assays need intact membranes and that quantitative IHC requires membrane-specific scoring and calibration.",
   "Specifies normalization (per cell number, per total membrane protein, or per surface-marker reference) and a replicate structure that makes two conditions comparable.",
 ],
 "common_failures": ["F06", "F07", "F05", "F08"],
},
]


def main():
    (ROOT / "tasks").mkdir(exist_ok=True)
    for t in TASKS:
        t = dict(t)
        t["prompt"] = t["prompt"].strip() + "\n\n" + SCHEMA
        t["prompt_version"] = "v1.0"
        t["input_version"] = "prostate_public_packet v0.1"
        t["input_files"] = [PACKET]
        t["visibility"] = "public"
        (ROOT / "tasks" / f"{t['task_id']}.json").write_text(
            json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(TASKS)} tasks")
    for t in TASKS:
        print(f"  {t['task_id']}  {t['capability']:<42} {len(t['expected_elements'])} anchors")


if __name__ == "__main__":
    main()
