# Historical documents — provenance note

This folder preserves dated internal planning documents **verbatim**, for
transparency. They are point-in-time records; where their wording differs
from the final manuscript, the manuscript governs. Known instances in
`statistical_analysis_plan_v2_dated_2026-09-11.md`:

1. **"概率恢复 / probability recovery"** — the plan's term for what the final
   manuscript calls the **analytic class-prior correction**
   (`logit(p_corrected) = logit(p_balanced) − log(w1/w0)`). The formula and
   all frozen numbers are unchanged; only the terminology was narrowed
   ("correction / approximate correction"; no claim of mathematically exact
   recovery of natural-prior probabilities, because the models are
   L2-regularised — China M1 audit agreement ±0.005).

2. **"回顾性注册 (retrospectively registered)"** — the plan's internal
   wording for depositing a frozen dated document. The study is reported in
   the manuscript as **"Not registered"**, with the protocol and code
   publicly archived with a timestamped DOI before submission. The SAP was
   never submitted to any registry; this archive deposit is the only form of
   public timestamping. Do not cite the study as registered.

3. **KNHANES missing-data handling** — the plan mentions median imputation
   for KNHANES; the final analysis used complete-case KNHANES data (no
   imputation in the external cohorts). The manuscript governs.

4. **Frozen NHANES median-imputer deployment sensitivity** — planned in the
   SAP; later deleted because no verifiable frozen result existed. It is not
   part of the final analysis set.

5. **NNS (number needed to screen)** — mentioned in the plan; removed from
   the final manuscript. Residual NNS strings inside frozen archived JSONs
   are historical artifacts, not manuscript results.

6. **M4 is not in SAP v2.** M4 was not prespecified in SAP v2; it was added
   after the Chinese sex-heterogeneity finding and prospectively specified
   and frozen before any access to KNHANES male data. The manuscript states
   this explicitly; do not describe M4 as "prespecified in the SAP".

The plan also cites superseded spec filenames (`模型规范附录_M1.json` /
`_M3.json`); the released equivalents are `model_specs/M1_specification.json`
and `model_specs/M3_specification.json`.
