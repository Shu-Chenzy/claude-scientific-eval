# Public prostate cancer analysis (packet v0.1)

Source: prostate-ai-hypothesis-evaluation (public GEO GSE35988 and SU2C/PCF 2019 data). All values below come from that analysis. No unpublished experimental data are included.

## Question

1. Which genes change as prostate cancer becomes castration-resistant, and which of those changes come from the tumor cells rather than from how the samples were collected?
2. Which of them hold up in an independent cohort that compares ARSI-exposed with ARSI-naive metastatic tumors? Does SSTR1?

## Data

| Cohort | Role | Samples | Access |
|---|---|---|---|
| GSE35988 (Grasso et al., *Nature* 2012) | discovery | 49 localized (prostatectomy), 27 metastatic CRPC (rapid autopsy), 12 benign; Agilent arrays | NCBI GEO |
| SU2C/PCF 2019 (Abida et al., *PNAS* 2019) | replication | 257 mCRPC patients (136 ARSI-exposed, 121 ARSI-naive); RNA-seq | cBioPortal API |
| UniProt | annotation | subcellular location and protein class for tested genes | REST API |

Raw data are not committed; the notebook downloads and caches them. Details in data/README.md.

## Analysis

All in notebooks/prostate_cancer_analysis.ipynb, about 5 minutes end to end. Thresholds are set in the first code cell, before any gene list is inspected.

1. **Differential expression**, CRPC vs localized: Welch's t-test on log2 ratios, Benjamini-Hochberg FDR. Hit = FDR < 0.05 and |log2FC| > 1.
2. **Composition and handling check.** Localized tumors are surgical specimens that contain benign stroma and immune cells; CRPC samples are metastases taken at autopsy. I score each sample for smooth-muscle stroma, immune cells, mast cells and immediate-early stress genes (FOS, EGR1 and others, induced by surgical ischemia). A hit is flagged if it correlates with any score (Spearman rho ≥ 0.5) across localized tumors.
3. **Pathways** (MSigDB Hallmark via Enrichr) on the hits that survive step 2.
4. **Replication in SU2C**: top 300 surviving hits plus SSTR1 (pre-specified), model `expression ~ ARSI exposure + biopsy site`, one biopsy per patient. AR is the positive control.
5. **UniProt annotation**: cell-surface location and protein class (GPCR, kinase, enzyme, etc.).
6. **Candidate table**: rule-based tiers, written to results/candidate_targets.csv.

## Findings

- **Most top hits are not tumor biology.** 1,282 of 5,746 hits (34% of downregulated, 3% of upregulated) track stroma, immune, mast-cell or handling signals, including 20 of the top 25. Ranking candidates by p-value alone would have sent me to the bench with PAGE4, ACTG2 and mast-cell genes.
- **After filtering, the biology is coherent.** Retained upregulated hits are enriched for E2F targets and G2-M checkpoint; downregulated hits for Androgen Response. AR, EZH2 and AURKA rise in CRPC as expected.
- **Six candidates replicate in ARSI-exposed tumors** (FDR < 0.10): DPP4, ST6GALNAC1, TRPM8, SNTG2, TSPAN11, AGBL2, all lower after ARSI exposure. TRPM8 and DPP4 are androgen-regulated, so the most reproducible signal is loss of AR output under ARSI pressure. The AR positive control behaves as expected (higher after ARSI, p = 3e-5).
- **SSTR1 is consistent with my bench result but not conclusive on public data alone.** Lower in CRPC (log2FC -1.18, FDR 0.047), not driven by composition (rho 0.01). Lower in ARSI-exposed mCRPC (unadjusted p = 0.013; site-adjusted beta -0.34, p = 0.077), with the effect concentrated in lymph node and bone biopsies. SSTR1 correlates with AR activity (rho 0.19, p = 0.002), consistent with it sitting downstream of AR signaling.

## Limitations

- Association, not causation; that is what the bench experiments are for.
- CRPC vs localized mixes castration, metastasis, chemotherapy and autopsy vs surgical collection. The composition flag removes the obvious artifacts, not all of them. Marker-based scores are not a full deconvolution.
- Welch's t-test is simple and transparent; limma would be the formal choice and could move borderline genes such as SSTR1.
- In SU2C, ARSI exposure is not the same as ARSI resistance, and low-expressed genes have limited power in FPKM data.
- mRNA is not protein. For SSTR1, the quantity that matters for a ligand-based therapy is surface receptor protein.
- The evaluation is small (35 questions, one run of one model), and 3 answers came from the fallback model. It is meant to find failure modes, not to produce a benchmark score.

## Candidate table (tier 1 = replicated in SU2C; tier 2 = not replicated; SSTR1 pre-specified)

log2FC and FDR: CRPC vs localized in GSE35988. su2c_beta_ARSI: ARSI-exposed minus ARSI-naive, site-adjusted. composition_rho: max Spearman rho with stroma/immune/mast-cell/early-response scores.

| gene | tier | direction_in_CRPC | log2FC_GSE35988 | FDR_GSE35988 | su2c_beta_ARSI | su2c_p | su2c_FDR | su2c_median_log2FPKM | composition_rho | protein_class | cell_surface |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DPP4 | 1 | down | -4.78 | 8.77e-18 | -1.01 | 1.06e-05 | 0.00261 | 2.33 | 0.165 | membrane receptor | True |
| ST6GALNAC1 | 1 | down | -4.18 | 2.43e-11 | -0.738 | 2.42e-05 | 0.00298 | 0.598 | 0.208 | enzyme | False |
| TRPM8 | 1 | down | -5.19 | 4.18e-09 | -1.15 | 5.03e-05 | 0.00413 | 1.63 | -0.16 | ion channel | True |
| SNTG2 | 1 | down | -2.76 | 3.71e-11 | -0.184 | 0.000509 | 0.0313 | 0.0946 | 0.0423 | other | False |
| TSPAN11 | 1 | down | -2.71 | 4.28e-12 | -0.366 | 0.000933 | 0.0459 | 0.424 | 0.416 | other | False |
| AGBL2 | 1 | down | -2.73 | 1.33e-09 | -0.136 | 0.00243 | 0.0996 | 0.188 | 0.267 | enzyme | False |
| CHP2 | 2 | down | -3.67 | 3.54e-17 | -0.114 | 0.00392 | 0.138 | 0 | 0.291 | other | False |
| HS3ST3A1 | 2 | down | -2 | 1.97e-10 | -0.136 | 0.00625 | 0.14 | 0.211 | 0.434 | enzyme | False |
| CCPG1 | 2 | down | -3 | 2.27e-08 | 0.254 | 0.00629 | 0.14 | 3.48 | 0.424 | other | False |
| AQP11 | 2 | down | -3.13 | 3.65e-15 | -0.226 | 0.00648 | 0.14 | 1.5 | 0.0663 | other | True |
| SLC35A3 | 2 | down | -2.65 | 4.15e-10 | 0.228 | 0.00667 | 0.14 | 2.28 | 0.279 | other | False |
| TONSL | 2 | up | 2.16 | 2e-10 | -0.329 | 0.00684 | 0.14 | 2.77 | 0.0535 | other | False |
| SSTR1 | 2 | down | -1.18 | 0.0468 | -0.343 | 0.0766 | 0.334 | 1.25 | 0.0146 | GPCR | True |

## Top composition-flagged hits (excluded from the candidate table)

| gene | log2FC | FDR | composition_rho | composition_driver |
|---|---|---|---|---|
| PAGE4 | -6.84 | 2.1e-35 | 0.625 | stroma |
| FCER1A | -4.46 | 1.05e-32 | 0.584 | mast_cell |
| SRD5A2 | -5 | 5.23e-27 | 0.596 | stroma |
| MS4A2 | -4.36 | 5.35e-27 | 0.889 | mast_cell |
| PCP4 | -4.81 | 9.34e-27 | 0.823 | stroma |
| ACTG2 | -4.35 | 1.36e-25 | 0.848 | stroma |
| ASB5 | -6.22 | 1.6e-25 | 0.689 | stroma |
| C18orf34 | -3.88 | 1.68e-25 | 0.567 | stroma |

## Hallmark pathways, retained hits

Up in CRPC:

| Term | Overlap | Adjusted P-value |
|---|---|---|
| E2F Targets | 71/200 | 3.38e-20 |
| G2-M Checkpoint | 65/200 | 1.73e-16 |
| Mitotic Spindle | 46/199 | 1.71e-06 |
| Glycolysis | 35/200 | 0.0149 |
| mTORC1 Signaling | 29/200 | 0.36 |

Down in CRPC:

| Term | Overlap | Adjusted P-value |
|---|---|---|
| Androgen Response | 41/100 | 1.08e-11 |
| Protein Secretion | 32/96 | 9.53e-07 |
| Fatty Acid Metabolism | 36/158 | 0.00144 |
| Bile Acid Metabolism | 28/112 | 0.00144 |
| Pperoxisome | 22/104 | 0.0572 |
