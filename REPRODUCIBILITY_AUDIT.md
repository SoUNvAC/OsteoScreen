# REPRODUCIBILITY AUDIT — packaging dry run

Archive: `osteoporosis_transportability_zenodo_v1.2.4` — audit date 2026-09-13.
Scope: packaging/reproducibility checks only. **No scientific analysis was
added, removed, re-run for content, or altered.** Two scripts were executed
solely to verify that the path-cleaned release copies still reproduce the
frozen archived outputs (verification runs against frozen values, not new
analysis).

## 1. Static checks

| Check | Result |
|---|---|
| All 4 analysis scripts compile (`py_compile`) | PASS |
| Absolute paths (`/mnt`, `/Users`, `/home`, Windows drive letters) anywhere in package | PASS — none |
| All 12 JSON files parse (UTF-8; `china_women_8var_results.json` withdrawn in v1.1.1) | PASS |
| All 6 figure-source NPZ files parse; arrays are curve grids only (max length 80; no patient-level arrays) | PASS |
| `CITATION.cff` parses as YAML 1.2 (cff-version 1.2.4) | PASS |
| Banned legacy phrases (`analytic recovery`, `substantial prior-probability shift component`) | PASS — absent |
| Bracketed placeholders (`[DOI 待补]`, `[GitHub 链接待补]`, etc.) | PASS — absent |
| `requirements.txt` versions match `software_versions.txt` evidence | PASS |
| `LICENSE` present at package root (dual MIT code / CC BY 4.0 figures, docs, aggregate results) | PASS (added in v1.1.1) |
| `.gitignore` blocks restricted cohort inputs and per-case regenerated files | PASS (added in v1.2.1) |

## 2. Live verification runs (frozen-value checks)

Restricted input files were temporarily placed in `data/`, the scripts were
run, and the restricted files were then deleted (they are NOT part of this
archive):

| Script | Frozen expectation | Observed | Result |
|---|---|---|---|
| `analysis/korea_tier1b_class_prior_correction.py` | MCE −0.2294, Brier 0.2550 | MCE −0.2294, Brier 0.2550 | PASS (exact) |
| `analysis/calibration_audit_slopes_bootstrap.py` | full JSON identical to archived `results/calibration_audit_results.json`; internal frozen checksums (China AUC 0.7448 / MCE +0.3133 / Brier 0.2908; Korea 0.7874 / +0.1339 / 0.2124; OOF 0.8032 / 0.7778) | rerun JSON byte-for-byte equal to archived JSON; all internal checksum assertions passed | PASS (exact; v1.2.4 note: byte-identity requires the default-off flag `RUN_WITHDRAWN_SURVEY_AUDIT=True`, since the survey-weight block is now gated as a withdrawn historical audit) |

`analysis/main_analysis_pipeline.py` and
`analysis/algorithm_benchmark_reconstructed.py` were **not** executed at
packaging time (multi-hour runtime; benchmark additionally needs xgboost /
catboost, absent from the final packaging environment). In v1.1.1 the
pipeline's Part 4 intercept-shift slope was aligned from penalised
LogisticRegression to the unpenalised binomial GLM and **functionally
re-verified** on the frozen Korea M3 predictions (recomputed slope 1.6361,
rounds to the frozen 1.64); no frozen result changed. Both compiled
cleanly; their frozen outputs are archived in `results/`. The benchmark
script is a reconstruction verified against frozen outputs (see
`docs/provenance_notes.md`).

## 3. Value consistency — released aggregates vs manuscript frozen values

| Quantity | Archived | Manuscript | Result |
|---|---|---|---|
| China raw calibration slope | 0.7154 | 0.72 | PASS |
| Korea raw calibration slope | 1.6361 | 1.64 | PASS |
| Tier 1a logit-scale slopes | 0.7494 / 1.7454 | 0.75 / 1.75 | PASS |
| Tier 1a Brier, logit scale | 0.169477 / 0.259236 | 0.169 / 0.259 | PASS |
| Tier 1b Korea | Brier 0.255, MCE −0.2294, slope 1.64 | 0.255 / −0.229 / 1.64 | PASS |
| Tier 2 / Tier 3 Korea Brier | 0.2022 / 0.1929 | 0.202 / 0.193 | PASS |
| Survey-weight AUC (mean-1 normalised) | 0.7523 / 0.8242 | **removed from final manuscript** (WTSAF2YR absent from frozen extract; authors' decision 2026-09-13) — archived for transparency | PASS (archive internal consistency) |
| Korea M3 AUC in archive | 0.787 | 0.787 | PASS |
| China women M2 AUC in archive | 0.818 (frozen); survey-weight audit 0.824 withdrawn | manuscript 0.818; withdrawn survey-weight audit 0.824 retained only for provenance | PASS |
| Benchmark members | 11 + `_meta` | 11 algorithms | PASS |

## 4. Legacy-caliber scan (whole package)

Located legacy material and disposition:

| Location | Content | Disposition |
|---|---|---|
| `results/korea_validation_results.json` → `calibration_slope_calibrated: 1.63` | superseded penalised-LR estimator | kept verbatim (frozen archive); documented in `docs/provenance_notes.md`; final value 1.64 in calibration-audit JSON |
| `results/women_main_analysis_results.json` → `女性校准.Platt` (Brier 0.177, slope 1.52) | superseded probability-scale Platt | kept verbatim; documented; final logit-scale values in calibration-audit JSON |
| `model_specs/M1/M4_specification.json` key `probability_recovery` | pre-harmonisation key name, formula correct | kept verbatim; documented as analytic class-prior correction |
| benchmark JSON `_meta` / verification JSON shorthand labels ("显著更差") | pre-final wording | kept verbatim; final manuscript wording documented in `docs/provenance_notes.md` |
| `analysis/algorithm_benchmark_reconstructed.py` docstring | same shorthand | **aligned** to final wording (comment only, no computation change); one archived dict key kept for bit-consistency with the archived verification JSON |
| `main_analysis_pipeline.py` Part 2 `dca_data_women.npz` per-case arrays | release-safety trap: script could regenerate restricted per-case file into the working tree | **code fixed in v1.2.1** (aggregate curve grids only; no computation change) + `.gitignore` guard |
| `results/china_women_8var_results.json` penalised slopes (e.g. 1.17 symmetry panel) | superseded penalised-LR estimates, never registered in provenance notes | **withdrawn from package in v1.1.1**; final unpenalised values (1.26) in `results/calibration_audit_results.json`; logged in `EXCLUDED_FILES_LOG.md` |
| SAP v2 | pre-harmonisation terminology ("概率恢复"; "回顾性注册") | **archived verbatim in v1.1.1** at `docs/historical/` with companion README stating the final terminology and that the study is NOT registered |
| PROBAST-AI self-assessment v4, CITL/OSTA-DCA technical notes, TRIPOD-AI checklist | pre-harmonisation terminology / pre-release placeholders | **withheld from package** — see `EXCLUDED_FILES_LOG.md` (HOLD) |

No undisclosed legacy values remain in released scripts or documentation.

## 5. MISSING items (not fabricatable; for authors)

1. (Resolved in v1.2.2) **M2 standalone specification JSON** — now distributed
   as `model_specs/M2_specification.json`, serialized from a verified
   deterministic re-execution of the frozen Part 2 pipeline (7/7 frozen
   checksums exact); labeled non-archival in its `_provenance` field.
2. **M4 all-sex extension script** — executed in-session, not saved; M4 is
   fully specified by `model_specs/M4_specification.json` +
   `M4_model_frozen.pkl`, and frozen outputs are archived.
3. **GitHub repository URL and Zenodo DOI** — do not exist yet; deliberately
   absent from all files (no fake placeholders). Back-fill per
   `ZENODO_RELEASE_CHECKLIST.md`.
4. **lightgbm frozen-run version** — not recorded in archived metadata;
   flagged 待核 in `environment/software_versions.txt`.

## 6. CONFLICT register

No unresolved scientific conflicts. The legacy-caliber items in Section 4 are
all identified, sourced, and dispositioned as superseded artifacts with the
frozen files kept verbatim; none alters any frozen result. Per the packaging
rule ("if any CONFLICT exists, do not claim the package is final-frozen"):
**no open CONFLICT remains in this register.**
