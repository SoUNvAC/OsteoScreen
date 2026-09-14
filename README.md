# Transportability of routine laboratory–based osteoporosis prediction from the USA to China and South Korea

**Reproducibility archive, v1.2.4 (2026-09-13)**

> Version history: v1.2.4 updates the author order (Faxin Wang moved to last non-corresponding author; equal-contribution marker removed; no other change). v1.2.3 rewords the registration statement ("analysis-documentation and code archive"; no content change). v1.2.2 adds model_specs/M2_specification.json (M1–M4 structural symmetry; serialized from a verified deterministic re-execution, 7/7 frozen checksums exact; no frozen result changed). v1.2.1 applies the second release-candidate round (per-case arrays no longer persisted by the pipeline and .gitignore guards added; withdrawn survey-weight audit gated default-off in the audit script; submission-status wording corrected; license metadata aligned across LICENSE/CITATION.cff/Zenodo instructions; docs/historical/README.md now lists all known SAP↔final discrepancies including M4; small wording cleanups). v1.2.0 was a re-issue of the frozen v1.1.1 content under the release number requested by the authors (no content change). v1.1.1 cleared six release-candidate findings (LICENSE file added as dual MIT/CC BY 4.0; dated SAP v2 archived verbatim in docs/historical/; imputation wording narrowed to the actual IterativeImputer implementation; M4 freeze-timing statement corrected; Part-4 inline calibration slope aligned to the unpenalised GLM estimator; superseded China-women 8-variable JSON removed). v1.1.0 documented the removal of the survey-weight sensitivity from the final manuscript (archived computation retained — see Section 11); v1.0.0 was the initial packaging. No frozen result changed in any version.

This repository is the code/model/aggregate-results archive accompanying the
manuscript:

> Wu Z, Zhang H, Du L, Yu J, Wang F, Gao F. *Transportability of routine
> laboratory–based osteoporosis prediction from the USA to China and South
> Korea: a three-cohort study of external validation and recalibration.*
> Manuscript prepared for submission to The Lancet Regional Health – Western Pacific.

The study was **not registered**; this analysis-documentation and code
archive is publicly deposited with a timestamped DOI (Zenodo) before journal submission.

---

## 1. Study overview

Frozen logistic-regression models were trained on NHANES 2005–2018
(USA; adults aged 40 years or older) and externally validated, without any
refitting, in:

* a hospital cohort in Harbin, China (n = 190; January–March 2024; 54
  osteoporosis events), and
* KNHANES 2009–2011 (South Korea; women n = 4,053 with 1,868 events; men
  n = 3,154 with 436 events, all-sex extension).

The study quantifies which aspects of performance transport (discrimination vs
absolute predicted probability), characterises calibration drift on three explicit tiers, and
benchmarks the frozen logistic regression against 11 algorithms and 13
domain-adaptation variants (exploratory).

## 2. Repository purpose

Faithful encapsulation of the completed and frozen research: model
specifications, analysis code, aggregate results, final figures, and the
documentation needed to reproduce every manuscript number. **Nothing in this
archive redefines the study**: no new analyses, models, subgroups, or
exploratory cuts were added at packaging time, and no frozen number was
altered. Where archived artifacts use superseded terminology or estimators,
the artifact is kept verbatim and the discrepancy is documented (see
`docs/provenance_notes.md`).

## 3. Folder structure

```
README.md                       this file
LICENSE                         MIT (code); see Section 15
.gitignore                      privacy guards: blocks restricted cohort inputs and per-case regenerated files
CITATION.cff                    citation metadata (DOI back-filled at release)
RELEASE_MANIFEST.md             full file inventory with SHA-256 checksums
EXCLUDED_FILES_LOG.md           materials deliberately not published, with reasons
REPRODUCIBILITY_AUDIT.md        packaging dry-run audit (syntax/paths/values)
ZENODO_RELEASE_CHECKLIST.md     step-by-step Zenodo/GitHub release checklist
environment/
  requirements.txt              pinned Python dependencies
  software_versions.txt         version evidence and to-be-verified flags
model_specs/
  M1_specification.json         15-predictor all-sex model (frozen)
  M2_specification.json         15-predictor women model (serialized from verified deterministic re-execution; see Section 15)
  M3_specification.json         8-predictor women model (frozen)
  M4_specification.json         9-predictor all-sex model (frozen)
  M3_model_frozen.pkl           serialised frozen M3 (scikit-learn Pipeline)
  M4_model_frozen.pkl           serialised frozen M4
analysis/
  main_analysis_pipeline.py     merged frozen pipeline (4 parts, see header)
  korea_tier1b_class_prior_correction.py
  calibration_audit_slopes_bootstrap.py
  algorithm_benchmark_reconstructed.py   (reconstructed; see provenance)
results/                        aggregate JSON results + figure source data (npz)
figures/                        final Figure 1–5 and eFigure S1–S5 (PNG + PDF)
docs/                           data dictionary, implementation notes,
                                provenance notes, cohort notes, checklists
docs/historical/                dated internal protocol (SAP v2, verbatim)
                                + terminology provenance note
data/
  nhanes_analytic_main_v4.csv   analysis-ready NHANES extract (see Section 4)
```

## 4. Cohorts and data-access boundaries

| Cohort | Content | In this archive? |
|---|---|---|
| NHANES 2005–2018 (USA) | analysis-ready extract, n = 5,217, 492 events | **Yes** — `data/nhanes_analytic_main_v4.csv`; derivative of de-identified CDC/NCHS public-use data |
| Chinese hospital cohort | patient-level data, n = 190 | **No** — ethics/privacy restrictions; not in any public repository. Aggregate results and full analysis code are public; patient-level data may be obtainable from the corresponding author on reasonable request, subject to ethics approval |
| KNHANES 2009–2011 (Korea) | analytic extracts / per-case predictions | **No** — KDCA redistribution terms for derived per-case extracts were not confirmed at release. Raw KNHANES data must be obtained by the user from the Korea Disease Control and Prevention Agency (KDCA); `docs/korea_cohort_revision_notes.md` and the code headers document the required variables, unit conventions, and label definitions so the analytic extract can be rebuilt from lawfully obtained data |

"Publicly available" source data does **not** imply a right to redistribute
derived per-case extracts; this archive therefore distributes code, model
specifications, aggregate results, and rebuild instructions only, for KNHANES.

All scripts default to repository-relative paths
(`data/nhanes_analytic_main_v4.csv`, `data/china_external_v4.xlsx`,
`data/korea_knhanes_women_v1.csv`) and can be pointed elsewhere with the
`OPTRANS_DATA_DIR` / `OPTRANS_OUT_DIR` environment variables. Files that are
not distributed are clearly marked in each script header.

## 5. Exact model identities (M1–M4)

All four models are **scikit-learn logistic regression, L2 penalty (C = 1.0),
lbfgs solver, max 2,000 iterations, tolerance 10⁻⁴, balanced class weights,
fitted on standardised predictors** (scaler fitted on NHANES only). M1–M3
were frozen before their respective external outcome evaluations; M4 was
specified after the Chinese sex-heterogeneity finding and frozen before any
access to KNHANES male data.

| Model | Predictors | Training set | Spec file |
|---|---|---|---|
| M1 | 15 (age, sex, BMI, WBC, neutrophil %, lymphocyte %, NLR, haemoglobin, ALP, AST, albumin, uric acid, total cholesterol, fasting glucose, eGFR) | NHANES all-sex, n = 5,217 (492 events) | `model_specs/M1_specification.json` |
| M2 | same 15, retrained on women | NHANES women, n = 2,653 (380 events) | `model_specs/M2_specification.json` (added in v1.2.2 — serialized from a verified deterministic re-execution of the frozen Part 2 pipeline; see Section 15) |
| M3 | 8 (age, BMI, WBC, haemoglobin, AST, total cholesterol, fasting glucose, eGFR) | NHANES women, n = 2,653 (380 events) | `model_specs/M3_specification.json` + `M3_model_frozen.pkl` |
| M4 | M3's 8 + sex | NHANES all-sex, n = 5,217 (492 events); frozen before any contact with KNHANES male data | `model_specs/M4_specification.json` + `M4_model_frozen.pkl` |

Each specification JSON contains: feature list, intercept, coefficients,
scaler mean/scale, NHANES median imputation constants, balanced class weights,
and the class-prior correction formula. Units are SI
(haemoglobin g/L, cholesterol and fasting glucose mmol/L); eGFR is CKD-EPI
2021 (race-free), computed from creatinine.

**M2 specification.** No standalone M2 spec JSON was archived during the
frozen sessions. M2 is exactly reproducible by running Part 2 of
`analysis/main_analysis_pipeline.py` (the frozen women pipeline); its frozen
aggregate outputs are in `results/women_main_analysis_results.json`. This is
logged in `REPRODUCIBILITY_AUDIT.md`.

## 6. Software environment

Python 3.12 with numpy / pandas / scipy / scikit-learn / statsmodels /
matplotlib / openpyxl (pinned in `environment/requirements.txt`; evidence and
flags in `environment/software_versions.txt`). lightgbm / xgboost / catboost
are needed only by the algorithm-benchmark script, which degrades gracefully
if they are absent.

## 7. How to reproduce each major output

After placing the obtainable input files in `data/` (Section 4):

| Manuscript output | Script / part | Frozen aggregate result file |
|---|---|---|
| Table 2 / Fig 2 — China M1 discrimination, calibration, tiers 0–3 | `main_analysis_pipeline.py` Part 1 | `results/calibration_audit_results.json` |
| China women M2 full panel (AUC 0.818, tiers) | Part 2 | `results/women_main_analysis_results.json` |
| DeLong paired AUC tests (model vs OSTA) | Part 3 | `results/women_main_analysis_results.json`, `results/korea_validation_results.json` |
| Korea M3 validation (AUC 0.787, calibration, DCA, locked thresholds, subgroups, China-women 8-variable symmetry panel) | Part 4 | `results/korea_validation_results.json`; symmetry-panel final calibration values: `results/calibration_audit_results.json` |
| Korea M4 all-sex extension (men AUC 0.728) | deterministic from `model_specs/M4_specification.json` (no separate script was archived — see provenance) | `results/korea_m4_allsex_extension_results.json` |
| Korea Tier 1b analytic class-prior correction (Brier 0.255, MCE −0.229) | `korea_tier1b_class_prior_correction.py` | `results/korea_tier1b_correction_results.json` |
| Unpenalised calibration slopes, 2,000-rep bootstrap 95% CIs, Tier 1a scale verification | `calibration_audit_slopes_bootstrap.py` (also contains an archived survey-weight computation not reported in the final manuscript — see Section 11) | `results/calibration_audit_results.json` |
| eTable S4 — 11-algorithm benchmark | `algorithm_benchmark_reconstructed.py` (reconstructed; verified against frozen outputs) | `results/algorithm_benchmark_bootstrap_results.json`, `results/algorithm_benchmark_verification.json` |
| eFigures — case-mix, domain adaptation, information dose, DCA tiers, mechanism scatter | Part 1 sections 3–7 / extension analyses | `results/extension_analyses_results.json`, `results/revision_round3_analyses_results.json`, `results/figure_source/*.npz` |

Figures in `figures/` are the final published PNG (300 dpi) + vector PDF pair;
their underlying curve data (non-patient-level) are in
`results/figure_source/`.

Expected frozen checksums are listed in Section 13.

## 8. Calibration tier definitions

| Tier | Name | Target-outcome information used | Definition |
|---|---|---|---|
| 0 | Raw baseline | none | uncorrected balanced-class-weight outputs (audit baseline, not expected to estimate natural-prevalence risk) |
| 1a | Platt scaling | none (source only) | logistic recalibration fitted on the **logits** of NHANES out-of-fold predicted probabilities (scikit-learn LogisticRegression, L2 penalty, C = 1.0) |
| 1b | Analytic class-prior correction | none (source only) | deterministic logit shift, Section 10 |
| 2 | Literature-anchored intercept updating | aggregate external prevalence only (no cohort outcome labels) | intercept shifted so mean predicted risk equals the literature anchor: 19.2% (China, first national survey, adults ≥ 50 y) / 37% (Korean women ≥ 50 y, approximating the KNHANES 2008–2011 estimate of 38.0%) |
| 3 | Cohort-informed intercept updating | cohort aggregate prevalence (**label-assisted**, reported as such) | intercept shifted to the study cohort's observed prevalence |

Tier 1a and Tier 1b are **alternatives, not a sequence**. Intercept-only
updating (Tiers 2–3) leaves the calibration slope unchanged by construction.

## 9. Tier 1a — exact implementation

"Platt scaling" in this study denotes **logit-scale** logistic recalibration:
`LogisticRegression(C=1.0)` (scikit-learn default L2 penalty) fitted as
`y ~ logit(p_oof)` on NHANES out-of-fold predictions, then applied to target
predictions as `p_cal = sigmoid(a + b · logit(p_raw))`.

Frozen Tier 1a Brier scores: **China ≈ 0.169, Korea ≈ 0.259**.

Provenance disclosure (also in `docs/provenance_notes.md`): an earlier
reconstructed repository script mistakenly fitted the recalibration on the
probability scale (yielding ≈ 0.177 / 0.261). Reverse verification against
the frozen Brier scores and the archived eFigure S4 decision-curve data
(max abs deviation 0.0 / 0.00025) confirmed the frozen analysis was
logit-scale. The released scripts implement the logit-scale version;
**manuscript frozen results and figures were never changed**.

## 10. Tier 1b — exact analytic correction formula

For frozen balanced-weight predictions:

```
logit(p_corrected) = logit(p_balanced) − log(w1 / w0)
```

with frozen class weights w1 / w0 = 5.3018 / 0.5521 (M1, M4) and
3.4908 / 0.5836 (M3), where sklearn's `balanced` rule gives
w_j = n / (2 · n_j).

Properties, stated precisely:

* this is an **analytic class-prior correction** (approximating the
  natural-prior probability scale);
* **no model is refitted**; AUC is unchanged (strictly monotone transform);
* because the main models carry L2 regularisation, we do **not** claim the
  correction is mathematically exactly equivalent to refitting an unweighted
  model; in the China M1 audit the corrected probabilities matched directly
  fitted natural-weight outputs to within **±0.005**;
* frozen Korea Tier 1b result: **Brier 0.255, MCE −0.229**
  (`analysis/korea_tier1b_class_prior_correction.py`).

## 11. Notes on balanced class weights, survey weights, imputation, and label-assisted steps

* **Balanced class weights.** All development used `class_weight='balanced'`.
  Raw outputs are therefore prior-shifted by design; this is characterised
  explicitly (Tier 0) rather than concealed, and every primary evaluation is
  on natural-prevalence external cohorts.
* **Survey-weight sensitivity — archived but not reported.** A
  survey-weighted source refit (WTMEC2YR × balanced class weights,
  mean-1-normalised) was computed at the audit stage and is archived in
  `results/calibration_audit_results.json`. It was **removed from the final
  manuscript** because the frozen NHANES extract contains only WTMEC2YR,
  whereas the fasting-glucose predictor comes from the fasting subsample
  (provenance check: its missingness pattern matches the fasting-only
  variables triglycerides/LDL at 99.9%/99.0% per-participant agreement),
  for which CDC prescribes the WTSAF2YR weight — not present in the frozen
  extract. Retained here for transparency; not a manuscript result. KNHANES
  sampling weights were unavailable in the analytic extract; Korean estimates
  represent the analytic sample.
* **Transductive Chinese imputation.** Chinese missing predictors were
  imputed by iterative multivariable imputation using chained conditional
  models (IterativeImputer, max_iter = 15, random_state = 42; single
  completed dataset; no Rubin pooling), using predictors only — no outcome
  labels; the scaler was fitted on NHANES
  only; operating thresholds were locked on NHANES out-of-fold predictions
  before any target-outcome access.
* **Label-assisted steps (all reported as such).** Tier 3 intercept updating
  uses cohort aggregate prevalence; OSTA decision-curve display maps OSTA
  scores to probabilities by univariate logistic calibration fitted within
  each target cohort (a label-assisted comparator); operating points
  translated after cohort-derived intercept updating are treated as
  label-assisted.
* **Calibration slope definition.** Unpenalised binomial GLM of the outcome
  on the logit of the predicted probability (statsmodels). Frozen primary
  values: China raw 0.72; Korean women raw 1.64; Tier 1a (logit-scale)
  0.75 / 1.75.
* **Multiplicity.** No adjustment for multiplicity was made; all 95% CIs are
  unadjusted and interval exclusions of zero are interpreted descriptively.

## 12. Primary / secondary / exploratory analyses

* **Primary:** frozen-model external validations — M1 → China; M3 → KNHANES
  women.
* **Secondary (prespecified in SAP v2):** OSTA comparisons; age and sex
  strata; three-tier recalibration; operating points; decision-curve
  analysis.
* **Secondary (added after SAP v2):** the all-sex Korean extension (M4) was
  not prespecified in SAP v2; it was added after the Chinese
  sex-heterogeneity finding and prospectively specified and frozen before
  any access to KNHANES male data (see `docs/historical/README.md`).
* **Exploratory (labelled as such throughout):** the 11-algorithm benchmark
  (fixed tested implementations — not an exhaustive hyperparameter search);
  13 domain-adaptation variants; instance selection; case-mix
  score-distribution analysis; information-dose simulation; year-by-year
  intercept transport; adaptation-mechanism scatter; under-50 boundary probe;
  incremental-value extension.

## 13. Expected outputs / frozen checksums

Running the released scripts on the proper inputs must reproduce:

| Quantity | Frozen value |
|---|---|
| China M1 — AUC / MCE / Brier | 0.7448 / +0.3133 / 0.2908 |
| Korea M3 (women) — AUC / MCE / Brier | 0.7874 / +0.1339 / 0.2124 |
| M1 NHANES out-of-fold AUC | 0.8032 |
| M3 NHANES women out-of-fold AUC | 0.7778 |
| China women M2 — AUC | 0.818 |
| Tier 1a Brier — China / Korea | 0.169 / 0.259 |
| Tier 1b Korea — Brier / MCE | 0.255 / −0.229 |
| Tier 2 Brier — China / Korea | 0.172 / 0.202 |
| Tier 3 Brier — China / Korea | 0.165 / 0.193 |
| Calibration slopes (unpenalised GLM) — China raw / Korea raw / Tier 1a | 0.72 / 1.64 / 0.75, 1.75 |

`analysis/calibration_audit_slopes_bootstrap.py` asserts these checksums
before computing any derived quantity.

## 14. Data-sharing restrictions

* Chinese patient-level data: not public (ethics/privacy); aggregate results
  and all code are public; patient-level data may be available from the
  corresponding author on reasonable request subject to ethics approval —
  this archive makes no broader promise than the manuscript's data-sharing
  statement.
* KNHANES: obtain from KDCA; this archive distributes no per-case KNHANES
  extract or prediction file; rebuild instructions are in
  `docs/korea_cohort_revision_notes.md` and the script headers.
* NHANES: public-use CDC/NCHS data; the analysis-ready extract is included
  for convenience and provenance.

## 15. Script provenance

See `docs/provenance_notes.md` for the full per-script account. Summary:
`main_analysis_pipeline.py` merges the four frozen execution scripts with two
code-audit corrections (logit-scale Platt; unpenalised GLM slopes) that align
code to the already-frozen results; `algorithm_benchmark_reconstructed.py` is
a **reconstruction** (the original benchmark script was lost before being
saved), verified member-by-member against the frozen archived outputs;
`korea_tier1b_class_prior_correction.py` and
`calibration_audit_slopes_bootstrap.py` are deterministic audit/consistency
scripts added at the final consistency-audit stage (no refitting, no tuning).
No released script is presented as something it is not.

`model_specs/M2_specification.json` (added in v1.2.2) was **not** an archived
frozen file: no standalone M2 spec JSON was ever written during the frozen
sessions. It was serialized from a deterministic re-execution of the frozen
Part 2 women-pipeline training code on the distributed NHANES extract (no
restricted data involved) and verified against seven frozen archived
checksums, all exact (women n = 2,653 / 380 events; 5-fold CV AUC 0.784,
AUPRC 0.365; ethnicity AUCs 0.836 / 0.752 / 0.715 / 0.747; temporal AUC
0.768).

## 16. Citation

Cite the manuscript (see `CITATION.cff`). After the Zenodo DOI is minted it
will be back-filled here and in `CITATION.cff`.

## 17. Contact and license

Corresponding author: Feng Gao, gaofeng19761222@163.com — Department of
Orthopaedics (Ward 1), Second Hospital of Harbin Medical University, Harbin,
China.

Dual license (`LICENSE`): **code under MIT**; **figures, documentation,
model specifications, and aggregate results under CC BY 4.0** (with citation
of the manuscript; see `CITATION.cff`). `CITATION.cff` deliberately declares
no single license (CFF 1.2 multi-license arrays are interpreted as OR, not as
file-scoped boundaries); the Zenodo deposit should declare both MIT and
CC BY 4.0 with this boundary stated in the description (see
`ZENODO_RELEASE_CHECKLIST.md`).
