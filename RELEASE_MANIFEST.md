# RELEASE MANIFEST — osteoporosis_transportability_zenodo_v1.2.4

Generated 2026-09-13 (v1.2.4: author-order update; v1.2.3 fixed registration-statement wording; v1.2.2 added the M2 specification JSON; v1.2.1 cleared the second release-candidate round; v1.2.0 re-issued v1.1.1; v1.1.1 cleared six release-candidate findings). 62 files. SHA-256 checksums below.
Verbatim frozen artifacts keep their archived bytes; renamed files map to
their internal-archive originals as follows (all other files are new
release documents).

## Name mapping (release path ← internal original)

* `analysis/algorithm_benchmark_reconstructed.py` ← `模型动物园_重建核验版_v1.py (paths + docstring wording aligned; no computation change)`
* `analysis/calibration_audit_slopes_bootstrap.py` ← `校准口径修正_无惩罚slope与bootstrapCI_脚本_v2.py (paths released-configured; no computation change)`
* `analysis/korea_tier1b_class_prior_correction.py` ← `韩国M3_Tier1b_类先验校正_脚本_v2.py (paths released-configured; no computation change)`
* `analysis/main_analysis_pipeline.py` ← `骨质疏松模型_完整分析代码_投稿仓库版_v2.py (paths released-configured; no computation change)`
* `data/nhanes_analytic_main_v4.csv` ← `NHANES分析集v4_主模型.csv (public-use NHANES extract, verbatim)`
* `docs/korea_cohort_revision_notes.md` ← `韩国队列最终验证集_v2_修订说明.md (verbatim)`
* `model_specs/M1_specification.json` ← `模型规范附录_M1.json (frozen, verbatim)`
* `model_specs/M3_model_frozen.pkl` ← `简约8变量模型_knhanes待用.pkl (frozen, verbatim)`
* `model_specs/M3_specification.json` ← `模型规范附录_M3_v2.json (frozen, verbatim)`
* `model_specs/M4_model_frozen.pkl` ← `全性别9变量模型_M4_knhanes待用.pkl (frozen, verbatim)`
* `model_specs/M4_specification.json` ← `模型规范附录_M4.json (frozen, verbatim)`
* `results/algorithm_benchmark_bootstrap_results.json` ← `模型动物园bootstrap结果_v1.json (frozen, verbatim)`
* `results/algorithm_benchmark_verification.json` ← `模型动物园重建核验_v2.json (verbatim)`
* `results/calibration_audit_results.json` ← `校准口径修正_无惩罚slope与bootstrapCI_结果_v2.json (frozen, verbatim)`
* `results/extension_analyses_results.json` ← `分析扩展包_GPT总指令_结果_v1.json (aggregate results; filename neutralised, content verbatim)`
* `results/korea_m4_allsex_extension_results.json` ← `韩国全性别扩展_M4结果_v1.json (frozen, verbatim)`
* `results/korea_tier1b_correction_results.json` ← `韩国M3_Tier1b_类先验校正_结果_v2.json (frozen, verbatim)`
* `results/korea_validation_results.json` ← `韩国队列验证结果_v1.json (frozen, verbatim)`
* `results/revision_round3_analyses_results.json` ← `GPT第三轮评审整改_v3.json (aggregate results; filename neutralised, content verbatim)`
* `results/women_main_analysis_results.json` ← `女性主分析结果_v5.json (frozen, verbatim)`
* `results/figure_source/dca_tier23_osta_recalc_v2.npz` ← `dca_tier23_osta_重算_v2.npz (verbatim)`

| path | bytes | sha256 |
|---|---|---|
| .gitignore | 933 | a8b979fa2256f2d2f5b7b15b49335cf120b22ff11a6657c390e6a105e4b46f1f |
| CITATION.cff | 1862 | 5926b859ababc1b832a0f8a7b1fac25fa1398b61fd19a72a2874169b34c85fef |
| EXCLUDED_FILES_LOG.md | 6249 | c210b9c698379ae4b04f4eb0f58a50bbeafb7ffdc6953d0232b1769e1c513257 |
| LICENSE | 2250 | 6c9c2b7b00c519ef897d82bd4e68ed70d684670ab803766ea79330a57af46af0 |
| README.md | 21730 | 5c0054cdf8a93d489a450123992eb9c6a05aaf3b892205d17c9eea0477db0845 |
| RELEASE_MANIFEST.md | (self) | (self-referential; regenerated each version) |
| REPRODUCIBILITY_AUDIT.md | 7693 | 271806fd4e87239bb75f279c1e5a5ae24c77f97d285d9be5d02f8b0ea73c2ccb |
| ZENODO_RELEASE_CHECKLIST.md | 5209 | defd57565845ea568dbc8c3547979739e96692426d2a499b94b2201c43549d25 |
| analysis/algorithm_benchmark_reconstructed.py | 11501 | fe9f53776796eb97c55d4f9059c3aa4ee29edef1f6e76b68fe7c10179d52d7e7 |
| analysis/calibration_audit_slopes_bootstrap.py | 18585 | 7f711c03d4f9e9db1fbca740a0e5485f4014e831c30ba251535ec4c1263eecd7 |
| analysis/korea_tier1b_class_prior_correction.py | 2090 | 42bfab7fd85f9b61be3ed5cfaf6ba2ca7e91a067b6e00c1163be9156edee2851 |
| analysis/main_analysis_pipeline.py | 60440 | 14d669426edc5c1ca237a7cef0397c70f0753027dadb4980ac5ef99d4d44baee |
| data/nhanes_analytic_main_v4.csv | 1686706 | 97724eb3b4b7c8390ef054ce53a687a0263f4560ec3a979577790dfce0f444e9 |
| docs/data_dictionary.md | 3750 | 6ef55bdfeead9ac84dd927279a71ae8867a610d6c3474793cdf148c6f6ed6a8b |
| docs/historical/README.md | 2351 | e9cb6390ca59310e0f730a27bba56a3ececc0a829e45d6a8fa43d5a0c6e7a0ba |
| docs/historical/statistical_analysis_plan_v2_dated_2026-09-11.md | 13666 | 454507f6f2420b505451063b73b415b04905dfb6c1c8f81c1d6791d08d304ebc |
| docs/korea_cohort_revision_notes.md | 1880 | 196122878a3c82c7ed3ab203b2692a0bcf9f4ddefa0feb795683e876f1ff4ee0 |
| docs/model_implementation_notes.md | 4099 | e19f40a9885dfab7cfcc46122bce6393cfceec355dcb6f8b1af67cf0b0538707 |
| docs/provenance_notes.md | 7516 | 325819b1cce48d2824e3fe9c4e34af6faac56f04f7061dd796dbfb68d916d4b5 |
| environment/requirements.txt | 398 | 80d6351741d59841780b24ac40c1b440dad4aad49cdfc6394c2fcc4d80d84fe0 |
| environment/software_versions.txt | 1818 | b70684240250b8bb57cd5c39d27c80f43074301573c00197b50dc56c678c6746 |
| figures/Figure1_study_design.pdf | 30654 | 17080722a6af86cb3d0d4304fb8ccca744aaf7216a21baab80bd8a54cd1bcadd |
| figures/Figure1_study_design.png | 482579 | d4fa3cb9b08e4596d83d195daea4af7428985cb48c2ee469b289c38f9ae090c6 |
| figures/Figure2_discrimination_transport.pdf | 29326 | 59a62fd93fc95112be07aa287a88cbb68ac63a437bb0939dae15b2e63faee7e7 |
| figures/Figure2_discrimination_transport.png | 335233 | 0483712f409c2d032df5313e7881028cb347d7dd19068b4c17a0e32e06dd0be0 |
| figures/Figure3_calibration_tiers.pdf | 34750 | 7eaf6d2cf9d6b5bee664786cc2354ab55d1897c33052da98cf686dc57a41bb65 |
| figures/Figure3_calibration_tiers.png | 425153 | 89d7cc2dd63f5e2860c7ca90f7a487119ea92bf6916b9889bcb916c675f49814 |
| figures/Figure4_casemix_distributions.pdf | 23595 | 9765454876a74bb5bfd29df99a30a001fac57fd583948a142d133ce687c284f1 |
| figures/Figure4_casemix_distributions.png | 125650 | 1a5f1bc77227e24d98b271b9743cdc2455e1dfd36535acfae38eb9eddc81a5b3 |
| figures/Figure5_decision_curves.pdf | 27965 | 8a833d863fc45568ad8d43ccb0cc1971cca3a86152ab4c78b0fb4e859b721f09 |
| figures/Figure5_decision_curves.png | 340467 | 0ffe3060eb6ce6b9d5b3a57533c459ffc0387698dad7f51f62b2b62f3eb53c0c |
| figures/eFigureS1_casemix_distributions_full.pdf | 42009 | 593e9e4b4d4393aaea024286f8a09a49f236d897850e52fee8f08ac6237cbd34 |
| figures/eFigureS1_casemix_distributions_full.png | 281849 | 26649ee749afde7d2627271b9b3af862689e45783af77f0417b492d08a53c05c |
| figures/eFigureS2_domain_adaptation_variants.pdf | 29992 | 5b608b20c77cdcca6d7f871243044662f35f965c3cdb0dbf5d0634afb417b7a8 |
| figures/eFigureS2_domain_adaptation_variants.png | 363590 | 546f0cc720c78b2f246038fb75505a5a4da604dc8fcfe23413ac602d352f5b74 |
| figures/eFigureS3_information_dose.pdf | 28871 | 6256a592b2a8c8492b16184f859d4c75bcd240633b87e1b60f94087115d4d62a |
| figures/eFigureS3_information_dose.png | 277462 | 90f009b092eee2578a80cbe6a9ad4080a147efd901013224492dc163bc22b52d |
| figures/eFigureS4_dca_raw_platt_tiers.pdf | 29778 | 79dc002cbd812d74aaca3583f04a6572131831d2ae326fe02b50ac5a0c92f0c4 |
| figures/eFigureS4_dca_raw_platt_tiers.png | 394072 | 3157fca63ca19fac1440835acbf16178091dec33acb59bd1da87f899745f85a8 |
| figures/eFigureS5_smd_vs_coefficient.pdf | 30677 | 6e8f3ee0b3176eb10ba492126303ba54f12ed5c67c3d5aad35fa25d150528208 |
| figures/eFigureS5_smd_vs_coefficient.png | 161966 | b6c768ee575ede1ff80fd0f8b743aeebffe43e2a839152de770addfae6dd4a3c |
| model_specs/M1_specification.json | 1426 | 189b8da6b0693ea47fc89554ad59aa22017270c3483d47c57b597da3b07eed80 |
| model_specs/M2_specification.json | 2462 | 627414a43435dc04cc8512faeac29f136aee7c4bd4a540f4716537ea1436f5bb |
| model_specs/M3_model_frozen.pkl | 1425 | b481baa418f8d55102e66e9f2fabe24b8913f5e31091bdcf9ed3917537001ea5 |
| model_specs/M3_specification.json | 1539 | 93d33b2931e8c172e3151016a837ecbe195216f49c50c43a09c6141c51ab4a0f |
| model_specs/M4_model_frozen.pkl | 1360 | cfb108f9eedea8974c8b2721dc19e21a4f967dad8b36e678e4e972e704cc034f |
| model_specs/M4_specification.json | 1509 | 7229b1f65d80825b45bc0fc9dbde7a8bcd15474176459218867890ac25121873 |
| results/algorithm_benchmark_bootstrap_results.json | 1730 | 2de342cb36d9b07ea2a4757d2357e65888018cba01f6657d261c4f90d4062d8a |
| results/algorithm_benchmark_verification.json | 4284 | 235a689cfee995935ff007d9844472b0caa4ec3555ba1bf82c52045821d3ef13 |
| results/calibration_audit_results.json | 3355 | 6ad0161aca7355c0cfc52a0d1b1a5068a44d77ca8170559702964eb1d576c80f |
| results/extension_analyses_results.json | 3649 | 945a9ed269b61b1c7d7e2383fa6c9de608d3ea0a0be9fc2e3016e521d01297ed |
| results/figure_source/dca_data_china_full.npz | 2792 | 6d66c1b43fb68ad0bc56c04b67ae02df582ae17352c0e2be5da41d424530846c |
| results/figure_source/dca_data_china_women_8var.npz | 3264 | 5e09f26dcf0c339a545917ff1de6fdb978bfb10b431f3b36d94f911dd0b3d105 |
| results/figure_source/dca_data_korea.npz | 4464 | dc3c077b5c3c1e040cd2bac8761d5aa7b8761e50ecc30a4ab7e8e6558577d12e |
| results/figure_source/dca_efigureS4_raw_platt_curves.npz | 4618 | 59f121c01ff22fd4b2fffd915dd82a8db4d7ccca8ca805899a48e44cc5333ccb |
| results/figure_source/dca_figure5_curves.npz | 7686 | 061ff1377d61776f56cf61d160dcedd85ce6db8e3b2e57172f53832054a6e1f7 |
| results/figure_source/dca_tier23_osta_recalc_v2.npz | 9762 | f81aac1eb5f346476f93e4329266fa379eb2cc6441dce23def75afaa7e4a1cf0 |
| results/korea_m4_allsex_extension_results.json | 2155 | 2fe1003bba75212e20b2efd88afa0d1274440ea2091ca167432d9d6093b4facf |
| results/korea_tier1b_correction_results.json | 1742 | c11812eb94efc3b58aee36eed23ddb93d0dfd0a2793cea64dacdef5bafb54613 |
| results/korea_validation_results.json | 2009 | 49696b83e17ab911812f04794fff003ee161d414a2fbbeb666a3fa6bc5a1cf5e |
| results/revision_round3_analyses_results.json | 2448 | 034f2d72e592768b5f4709125c416e7b92860771ffb667ed606f3083fbd96ed4 |
| results/women_main_analysis_results.json | 2711 | ce4268ca3b131fe17e7f6ad49416e7d079d8df51d7d151a350fba58c7bc21adf |
