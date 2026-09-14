# Model implementation notes

These notes collect the implementation details needed to reproduce the
manuscript outputs, in one place. They describe the frozen analysis; nothing
here modifies it.

## Fitting settings (M1–M4)

scikit-learn `LogisticRegression`: L2 penalty, C = 1.0, lbfgs solver,
max_iter = 2,000, tol = 10⁻⁴, `class_weight='balanced'`, fitted on
standardised predictors (scaler fitted on NHANES only). Internal
out-of-fold predictions: 5-fold StratifiedKFold (shuffle, seed 42), same
settings.

## Balanced class weights

sklearn's `balanced` rule: w_j = n / (2 · n_j).

* M1/M4 (n = 5,217; 492 events): w1 = 5.3018, w0 = 0.5521
* M3 (women, n = 2,653; 380 events): w1 = 3.4908, w0 = 0.5836

Raw balanced outputs are prior-shifted by design and are reported explicitly
as Tier 0. The analytic class-prior correction
`logit(p_c) = logit(p_b) − log(w1/w0)` approximates the natural-prior
probability scale; because the models are L2-regularised we do not claim
exact equivalence to an unweighted refit (China M1 audit: agreement with a
direct natural-weight fit to within ±0.005).

## Calibration slope definition

Unpenalised binomial GLM of outcome on logit(predicted probability)
(statsmodels). Intercept-only updating (Tiers 2–3) leaves this slope
unchanged by construction — numerically verified in
`results/calibration_audit_results.json`
(`intercept_shift_slope_invariance`).

## Tier 1a scale verification

Frozen Tier 1a Brier scores (China 0.169 / Korea 0.259) correspond to the
**logit-scale** Platt implementation; an earlier probability-scale
reconstruction (0.177 / 0.261) was a repository-script deviation, since
corrected. Evidence chain in `results/calibration_audit_results.json`
(`Tier1a_scale_fork`) and `docs/provenance_notes.md`.

## Tier 2/3 intercept shifts (frozen)

* China (M1): Tier 2 shift b = −2.419 (anchor 19.2%); Tier 3 b = −1.771
  (cohort prevalence 28.4%).
* Korea women (M3): Tier 2 shift b = −1.024 (anchor 37%; frozen archive
  value — re-solving at exactly 0.37 yields −1.039 with Brier 0.2028 vs the
  archived 0.202; the frozen archive value is used everywhere for exact
  consistency); Tier 3 b = −0.613 (cohort prevalence 46.1%).

## Operating thresholds

Locked on NHANES out-of-fold predictions (Youden index) before any
target-outcome access. M4 source-locked threshold: 0.1043 (recorded in
`model_specs/M4_specification.json`). Threshold translation after
cohort-derived intercept updating is treated as label-assisted and reported
as such.

## Decision-curve analysis

Threshold-probability grid 0.01–0.50 (referral for DXA). OSTA scores are
mapped to probabilities by univariate logistic calibration fitted within each
target cohort — a label-assisted comparator, reported as such. Curve source
data (grids and net benefits, no patient-level records) are in
`results/figure_source/`.

## Survey-weight sensitivity (archived; not reported in the final manuscript)

A WTMEC2YR × balanced-class-weight L2-regularised refit (weights normalised
to mean 1) was computed at the audit stage and is archived in
`results/calibration_audit_results.json` (0.7523 / 0.8242, mean-1
normalised). Because the fasting-glucose predictor derives from the NHANES
fasting subsample — for which CDC prescribes the WTSAF2YR weight, absent
from the frozen extract — the authors removed this sensitivity from the
manuscript rather than report it with the MEC weight. Archived for
transparency.

## Bootstrap conventions

2,000 replicates, seed 42, percentile method. Tier 3 CIs are re-anchored to
each resample's prevalence; Tier 2 CIs re-solve the shift at the fixed
literature anchors (0.192 / 0.37). Paired bootstrap for AUC differences, with
the selection step nested inside the loop for instance selection.

## Multiplicity

No adjustment for multiplicity; all 95% CIs are unadjusted; p values and
interval exclusions of zero are interpreted descriptively, not as
confirmatory hypothesis tests. The algorithm benchmark represents the tested
fixed implementations only — not an exhaustive hyperparameter optimisation.
