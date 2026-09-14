# Script and artifact provenance

This archive distinguishes **original frozen execution scripts**,
**reconstructed scripts verified against frozen outputs**, and **audit
scripts added at the final consistency-audit stage**. No script is presented
as something it is not.

## analysis/main_analysis_pipeline.py

Merged archive of the four frozen execution scripts (Parts 1–4, named in the
file header), with two code-audit corrections that align the code to the
already-frozen results (no result changed):

1. **Tier 1a "Platt" scale.** The standalone original scripts fitted the
   recalibration on the probability scale. Reverse verification against the
   frozen archived Brier scores (0.169 / 0.259) and the archived eFigure S4
   decision-curve data (max abs deviation 0.0 / 0.00025) established that the
   frozen analysis itself was logit-scale. The released script implements
   `y ~ logit(p_oof)`. Manuscript frozen results and figures were unchanged.
2. **Calibration slopes.** The standalone originals used penalised
   LogisticRegression for calibration slopes; the released script uses the
   manuscript's estimator — unpenalised binomial GLM (statsmodels) — yielding
   the reported values (China 0.72, Korea 1.64). In v1.1.1 the Part 4 inline
   intercept-shift slope (the last remaining penalised call) was aligned to
   the same GLM estimator and functionally re-verified on the frozen Korea M3
   predictions (recomputed slope 1.6361, rounds to 1.64). No result changed.

The standalone originals are therefore superseded and are not distributed
(see `EXCLUDED_FILES_LOG.md`).

## analysis/algorithm_benchmark_reconstructed.py

**Reconstructed from archived analysis records** — the original benchmark
script was lost in-session before being saved. This reconstruction was
verified member-by-member against the frozen archived bootstrap results
(11 algorithms, B = 2,000, seed 42): per-model ΔAUC errors ≤ 0.007 for all
members, all CIs highly overlapping, no sign flips, no conclusion change
(verification detail: `results/algorithm_benchmark_verification.json`).
It is labeled "reconstructed / verified against frozen archived outputs" and
must not be cited as the original frozen execution script.

## analysis/korea_tier1b_class_prior_correction.py

Deterministic transformation of frozen M3 predictions (no refitting, no
tuning), added at the final consistency-audit stage. Output verified bit-for-
bit against the frozen computation: MCE −0.2294, Brier 0.2550.

## analysis/calibration_audit_slopes_bootstrap.py

Consistency-audit script (unpenalised slopes, scale-fork evidence, bootstrap
CIs, survey-weight sensitivity, China-women symmetry panel). Asserts the
frozen checksums before computing anything. Zero new analyses. In v1.2.4 the
withdrawn survey-weight sensitivity was gated behind
`RUN_WITHDRAWN_SURVEY_AUDIT = False` (default off): it is a withdrawn
historical audit retained only to reproduce the archived JSON byte-for-byte
when explicitly enabled; it must not be used for inference.

## Frozen result JSONs — archived verbatim, with these documented notes

* `results/korea_validation_results.json`: the field
  `calibration_slope_calibrated: 1.63` was computed with the superseded
  penalised-LR estimator. The final reported value is the unpenalised GLM
  slope **1.64** (see `results/calibration_audit_results.json`). The frozen
  file is archived verbatim; the manuscript reports 1.64.
* `results/women_main_analysis_results.json`: the sub-entry
  `女性校准.Platt` (Brier 0.177, slope 1.52) reflects the superseded
  probability-scale Platt implementation. Final logit-scale Tier 1a values
  are in the calibration-audit JSON and the manuscript. Archived verbatim.
* `model_specs/M1_specification.json` and `M4_specification.json`: the JSON
  key `probability_recovery` is retained verbatim from the frozen archive;
  it denotes the **analytic class-prior correction** (formula unchanged:
  `p = expit(logit(p_balanced) − log(w1/w0))`). Final terminology is
  "correction / approximate correction"; no claim of mathematically exact
  recovery of natural-prior probabilities is made.
* `results/algorithm_benchmark_bootstrap_results.json` ("_meta") and
  `results/algorithm_benchmark_verification.json`: shorthand verdict labels
  in these frozen artifacts (e.g. "显著更差") predate the final manuscript
  wording; the manuscript reports these comparisons as "the unadjusted 95%
  CI excluded zero in the harmful direction (exploratory, unadjusted)".
  Archived verbatim.
* `results/calibration_audit_results.json` (`survey_weight_sensitivity`
  section) and `results/women_main_analysis_results.json`
  (`调查加权模型` entry): archived audit-stage survey-weight computations
  (WTMEC2YR). Removed from the final manuscript because the fasting-glucose
  predictor belongs to the NHANES fasting subsample, whose prescribed CDC
  weight (WTSAF2YR) is absent from the frozen extract. Archived verbatim for
  transparency; not manuscript results.
* (Removed in v1.1.1) `results/china_women_8var_results.json`: a
  calibration-intermediate archive whose slope/intercept values were
  penalised-logistic-regression estimates (e.g. 1.17 for the symmetry panel),
  superseded by the final unpenalised GLM value (1.26). Unlike the two
  verbatim-archived items above it had never been registered here, so it was
  withdrawn from the package rather than archived; the final China-women
  calibration numbers live only in `results/calibration_audit_results.json`.
  Removal logged in `EXCLUDED_FILES_LOG.md`.
* `results/extension_analyses_results.json` and
  `results/revision_round3_analyses_results.json`: aggregate outputs of the
  prespecified extension/revision analyses; file names were neutralised at
  packaging (original internal names recorded in `RELEASE_MANIFEST.md`).

## Not archived (and consequences)

* **M2 standalone specification JSON** was never written during the frozen
  sessions. In v1.2.2, `model_specs/M2_specification.json` was added for
  M1–M4 structural symmetry: serialized from a deterministic re-execution of
  the frozen Part 2 training code (distributed NHANES extract only) and
  verified against seven frozen archived checksums, all exact (women
  n = 2,653 / 380; CV AUC 0.784, AUPRC 0.365; ethnicity AUCs 0.836 / 0.752 /
  0.715 / 0.747; temporal AUC 0.768). It is labeled accordingly in its
  `_provenance` field and is not an archived frozen file.
* **M4 all-sex extension script** was executed in-session and not saved to
  disk. M4 is fully specified by `model_specs/M4_specification.json` +
  `M4_model_frozen.pkl` (deterministic predictions from frozen coefficients),
  and its frozen outputs are in
  `results/korea_m4_allsex_extension_results.json`. Logged as MISSING.
* The statistical analysis plan (SAP v2) is archived verbatim at
  `docs/historical/statistical_analysis_plan_v2_dated_2026-09-11.md` (added
  in v1.1.1) with a companion `docs/historical/README.md` covering two
  wording artefacts: the historical term "概率恢复 / probability recovery"
  (final manuscript term: analytic class-prior correction; formula and
  frozen values unchanged) and the historical phrase "回顾性注册 /
  retrospectively registered" (the study was never submitted to any
  registry; the manuscript correctly reports "Not registered", and the
  study must not be cited as registered). The two reporting/technical notes
  remain withheld pending author decision (`EXCLUDED_FILES_LOG.md`, HOLD
  section).
