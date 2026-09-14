# EXCLUDED FILES LOG

(v1.1.1 update: the dated SAP v2 is no longer withheld — it is archived
verbatim in `docs/historical/` with a terminology provenance note. The
superseded China-women 8-variable results JSON was withdrawn from the
package — see §B.)

Materials deliberately **not** published in this archive, with reasons.
No content of these files is reproduced here. Nothing excluded here is
needed to reproduce any published aggregate result (rebuild routes are
documented in `README.md` and `docs/`).

## A. Restricted data (must never be public)

| File | Reason |
|---|---|
| `外部验证集汇总_v3_质控修订.xlsx`, `外部验证集汇总_v4.xlsx` (and all earlier uploads) | Chinese patient-level data (n = 190): ethics/privacy restrictions; may be shared only on reasonable request per the manuscript's data-sharing statement |
| `韩国队列最终验证集_v1.csv`, `韩国队列最终验证集_男女全量_v1*.csv`, `韩国队列最终验证集_男女全量_v2.csv` | per-case KNHANES analytic extracts; KDCA redistribution permission not confirmed |
| `韩国M3_Tier1b_类先验校正_预测_v2.csv` (and v1) | per-case KNHANES prediction file |
| `dca_data_women.npz` | contains per-patient predictions and labels for 116 Chinese women (`p_raw/p_prior/p_platt/p_osta/y_cn/osta`, n = 116). v1.2.1: the released pipeline no longer persists these arrays (aggregate curve grids only) and `.gitignore` blocks any legacy-named regeneration, closing the accidental-recommit trap |
| `KNHANES_DXA提取.csv`, `KNHANES化验提取_v2.csv` (uploads) | per-case KNHANES raw extractions |

## B. Superseded artifacts (replaced; single-caliber archive)

| File | Superseded by | Reason |
|---|---|---|
| `骨质疏松模型_完整分析代码_投稿仓库版.py` (v1) | `analysis/main_analysis_pipeline.py` | probability-scale Platt deviation |
| `模型分析代码汇总_v4.py`, `分析脚本_女性主分析_v5.py`, `分析脚本_DeLong修补_v5.py`, `分析脚本_韩国队列验证_v1.py` | merged release script | standalone originals containing the superseded probability-scale Platt / penalised-slope implementations |
| `校准口径修正_无惩罚slope与bootstrapCI_脚本_v1.py` / `_结果_v1.json` | `_v2` (released) | v1 marked superseded at v2 issuance |
| `韩国M3_Tier1b_类先验恢复_脚本_v1.py` / `_结果_v1.json` / `_预测_v1.csv` | `_v2` correction trio | "recovery" terminology; v1 marked superseded |
| `模型规范附录_M3.json` | `M3_specification.json` (= `_M3_v2.json`) | v2 adds frozen class weights and imputation constants |
| `模型动物园重跑_v1.py`, `模型动物园重建核验_v1.json` | `analysis/algorithm_benchmark_reconstructed.py`, `algorithm_benchmark_verification.json` (= v2) | earlier reconstruction; v1 JSON additionally has a non-UTF-8 encoding defect |
| `NHANES主模型_分析就绪_剔除编码5.csv`, `NHANES全量_分析就绪_剔除编码5.csv`, `NHANES分析集v4_全量.csv` | `data/nhanes_analytic_main_v4.csv` | pre-v4 cleaning snapshots / unreferenced by released scripts |
| `模型动物园_重建核验版` intermediate runs | released benchmark script | consolidation |
| `中国女性8变量验证结果_v1.json` (was `results/china_women_8var_results.json` in v1.0.0–v1.1.0) | `results/calibration_audit_results.json` (`china_women_8var_symmetry_unpenalised`) | archived penalised-LR slopes (1.17) superseded by the final unpenalised GLM value (1.26); removed from the public package at RC review so no undisclosed legacy values remain |

## C. Internal process materials (not for public archive)

| File | Reason |
|---|---|
| `GPT评审回应审计结果_v1.json` | internal review-response audit; contains superseded calibers (slope 0.70; "恢复" terminology) |
| `研究工作流与结果总汇总_v5…v43.md` (all ledger versions) | internal work ledger / process history |
| `全稿一致性审计报告_v1/v2.md`, `全稿自查修改报告_中文版_v1.md` | internal audit logs |
| `白皮书_v5/v6`, `总体研究策略_v4.md`, `数据集投稿可行性评估报告.md`, `论文升级总指令*.md`, pasted review-round texts | internal planning/draft documents |
| `GitHub_Zenodo时间戳傻瓜流程.md`, `OSF注册傻瓜流程指南.md` | internal how-to notes (OSF guide deprecated) |
| All manuscript drafts except the final pair; all Chinese-mirror drafts; submission ZIPs v1–v3; ChangeLogs; 投稿首页三件套 versions | manuscript/submission history — the public archive is a code+data deposit, not a draft repository |
| `图1_…图14…png`, `图13s_…png` (Chinese-named working figures), `数据清洗策略流程图_v4.png`, `图10_研究流程与标签暴露三色图.png` | working/draft figures superseded by `figures/Figure1–5` + `eFigureS1–S5` |
| `模型选择对照表_13模型.xlsx`, `数据评估QC备份_20260907.json` | internal selection/QC working files |
| `__pycache__/`, `.DS_Store`-class OS/IDE artifacts | cache/system files |

## D. HOLD — withheld pending author confirmation

| File | Reason / required author decision |
|---|---|
| `PROBAST-AI自评估_终稿_v4.md` | contains "自然先验恢复" wording; reporting checklist, author to harmonise or waive |
| `技术核验包_CITL定义与OSTA-DCA_v1.md` | table carries superseded slope values (0.70 / 1.63) and "解析权重恢复" wording; definitional content is now covered by `docs/model_implementation_notes.md` with final values |
| `TRIPOD-AI清单_终稿对照_v4.md` | quotes manuscript pre-release placeholders ([DOI 待补] / [GitHub 链接待补]); can be added after DOI backfill |
| `英文初稿_LRHWP_v31.md`, `补充材料_Supplement_v12.md` | final manuscript files — authors to decide whether the submitted manuscript PDF/markdown joins the Zenodo deposit after acceptance/DOI minting (journal policy) |
| ~~LICENSE choice~~ **RESOLVED (v1.1.1)** | dual license implemented: code MIT / figures·docs·specs·aggregate results CC BY 4.0 (`LICENSE`, README §17) |

## E. Never present anywhere in the pipeline

No API keys, tokens, credentials, IDE configs, `__MACOSX`, `.DS_Store`,
`Thumbs.db`, absolute local paths, or user-directory paths exist in this
package (verified by scan, see `REPRODUCIBILITY_AUDIT.md`).
