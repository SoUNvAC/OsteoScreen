# Data dictionary and variable mapping

This document maps the model variables onto the three cohorts' source
columns. All model variables are SI units: haemoglobin g/L; total
cholesterol and fasting glucose mmol/L; creatinine µmol/L (China) or mg/dL
(NHANES/KNHANES source files); eGFR mL/min/1.73 m².

## Model variables (M1: all 15; M3: the 8 marked •; M4: M3 + sex)

| Variable | Definition | Source |
|---|---|---|
| age • | age, years | direct |
| sex | 1 = male, 2 = female (NHANES coding) | direct |
| bmi • | kg/m² | direct |
| wbc • | white-cell count, ×10⁹/L | direct |
| neu | neutrophil percentage | direct |
| lym | lymphocyte percentage | direct |
| nlr | neu / lym (derived) | derived |
| hb • | haemoglobin, g/L | direct |
| alp | alkaline phosphatase, U/L | direct |
| ast • | aspartate aminotransferase, U/L | direct |
| alb | albumin, g/L | direct |
| ua | uric acid, µmol/L | direct |
| tc • | total cholesterol, mmol/L | unit-harmonised |
| fbg • | fasting glucose, mmol/L | unit-harmonised |
| egfr • | CKD-EPI 2021 (race-free), from creatinine; female κ = 0.7, α = −0.241, ×1.012 | derived |

## Cohort column mapping

| Model variable | NHANES extract (`data/nhanes_analytic_main_v4.csv`) | China (`china_external_v4.xlsx`, sheet 主数据_质控修订 — not distributed) | KNHANES rebuild (from KDCA raw; not distributed) |
|---|---|---|---|
| age | 年龄 | 年龄 | age |
| sex | 性别 | 性别 | sex |
| bmi | bmi | bmi | bmi |
| wbc | 白细胞计数 | 白细胞计数（WBC）×10⁹/L（保留 1 位小数） | wbc |
| neu | 中性粒细胞百分比 | 中性粒细胞百分比（Neu%） | — |
| lym | 淋巴细胞百分比 | 淋巴细胞百分比（Lym%） | — |
| hb | 血红蛋白 | 血红蛋白（Hb）g/L（保留 0 位小数） | hb_gL (SI) / hb_gdL |
| alp | 碱性磷酸酶 | 碱性磷酸酶（ALP）U/L | — |
| ast | 谷草转氨酶 | 谷草转氨酶（AST）U/L（保留 0 位小数） | ast |
| alb | 血清白蛋白 | 血清白蛋白（ALB）g/L（保留 1 位小数） | — |
| ua | 血尿酸 | 血尿酸（UA）umol/L | — |
| tc | 血清总胆固醇 | 血清总胆固醇（TC）mmol/L | tc_mmol (SI) / tc_mgdl |
| fbg | 空腹血糖 | 空腹血糖（FBG）mmol/L | fbg_mmol (SI) / fbg_mgdl |
| creatinine | 血清肌酐 | 血清肌酐（Cr）umol/L | crea_mgdl |
| outcome | 研究终点 | 研究终点（≥50岁任一部位T≤-2.5；<50岁任一部位Z≤-2.0） | op_nhanes (primary) / op_asia (sensitivity) |

## Outcome labels

* **Primary (all cohorts):** osteoporosis by DXA T-score ≤ −2.5 at femoral
  neck or lumbar spine L1–L4, referenced to a uniform young white female
  reference (femoral neck NHANES III: mean 0.858, SD 0.120; lumbar L1–L4 US
  young-adult female: mean 1.047, SD 0.11). Chinese cohort additionally used
  Z ≤ −2.0 for participants younger than 50 years.
* **Sensitivity (Korea):** sex-matched Asian references (`op_asia`).
* Known rounding note: the female Korean labels used lumbar SD 0.111 while
  the male M4 session used 0.110 (both roundings of the published 0.11);
  this affects at most 13/3,154 borderline male classifications; frozen
  results were computed in their respective sessions and not re-run
  (`docs/korea_cohort_revision_notes.md`).

## China file columns used by the pipeline

`排除标记 == 0` selects the analysed sample (n = 190); the outcome column is
matched by the substring `研究终点`; creatinine is divided by 88.4 to reach
mg/dL before CKD-EPI 2021; NLR = Neu% / Lym%. Chinese-cohort missing
predictors were imputed by iterative multivariable imputation using chained
conditional models (IterativeImputer; single completed dataset; no Rubin
pooling) on predictors only (no labels).
