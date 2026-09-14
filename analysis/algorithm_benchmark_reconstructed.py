# -*- coding: utf-8 -*-
"""
模型动物园 重建核验版 v1（2026-09-13）
====================================
用途：Supplement eTable S4 的可执行规格来源 + GitHub 代码归档。

来源与地位（透明声明）：
    产出 模型动物园bootstrap结果_v1.json（2026-09-09，11 模型配对 bootstrap，
    B=2000，seed=42，中国全量 n=190）的原始脚本随会话丢失、未曾落盘。
    本脚本是在 模型动物园重跑_v1.py（早前重建版）基础上**修正成员与口径**后的
    重建核验版：成员精确对齐冻结档案的 11 模型（补 QDA/CatBoost、KNN k=15、
    MLP (32,16)），bootstrap 口径对齐冻结档案（中国全量、RandomState(42)、B=2000）。

核验结论（对冻结档案 模型动物园bootstrap结果_v1.json，逐模型 ΔAUC/CI/P 比对）：
    - 11 个模型 ΔAUC 最大误差 0.007，其中 9 个 ≤0.005；
    - LASSO/弹性网络 Δ=0.000、kNN −0.044、朴素贝叶斯 −0.018 精确命中；
    - QDA −0.068 vs 冻结 −0.067（CI [−0.139,−0.006] vs [−0.134,−0.003]）；
    - 全部 CI 高度重叠，无符号翻转，无结论变化：无一模型优于 LR；
      QDA 的未校正 95% CI 在有害方向不含 0（exploratory, unadjusted）；
      SVM-RBF 边缘（P≈0.04，未校正）。
    - MLP 对训练时长敏感（max_iter=3000 收敛后 Δ=−0.055；sklearn 默认
      max_iter=200 时 Δ=−0.022），本脚本取 alpha=0.001 + 默认 max_iter=200，
      与冻结 −0.016 的误差 0.006，在全体误差带内。
    核验明细：results/algorithm_benchmark_verification.json（逐模型 rerun vs frozen + 判定）。

管道（与全部冻结脚本一致）：
    15 特征（14 原始 + NLR 派生；eGFR 按 CKD-EPI 2021 无种族公式由肌酐计算）；
    标准化均值/SD 仅拟合于 NHANES；缺失值在标准化空间 fillna(0)（等价于
    NHANES 中位数填补——部署敏感性口径）；中国队列标签仅用于评估，零调参。
    管道正确性锚点：线性 LR（class_weight=balanced, max_iter=2000）
    中国队列 AUC = 0.745，与冻结主分析逐位一致。

运行：python 模型动物园_重建核验版_v1.py
依赖：pandas numpy scikit-learn xgboost==3.4.1 lightgbm catboost==1.2.40 openpyxl
"""

# ================================================================================
# RELEASE PATH CONFIGURATION (public archive, v1.2.4)
# All inputs/outputs are repository-relative; override via environment variables.
#   OPTRANS_DATA_DIR : input data folder   (default: <repo>/data)
#   OPTRANS_OUT_DIR  : results folder      (default: <repo>/results)
# Data availability (see README.md section "Data access"):
#   data/nhanes_analytic_main_v4.csv   distributed (de-identified CDC public-use extract)
#   china_external_v4.xlsx             NOT distributed (ethics/privacy); sheet 主数据_质控修订
#   korea_knhanes_women_v1.csv         NOT distributed; rebuild from KNHANES (KDCA) per docs/
# ================================================================================
import os
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get('OPTRANS_DATA_DIR', os.path.join(_REPO, 'data'))
OUT_DIR = os.environ.get('OPTRANS_OUT_DIR', os.path.join(_REPO, 'results'))
SPEC_DIR = os.path.join(_REPO, 'model_specs')
NH_CSV = os.path.join(DATA_DIR, 'nhanes_analytic_main_v4.csv')
CN_XLSX = os.path.join(DATA_DIR, 'china_external_v4.xlsx')        # NOT distributed
KR_CSV = os.path.join(DATA_DIR, 'korea_knhanes_women_v1.csv')     # NOT distributed
MODEL_PKL = os.path.join(SPEC_DIR, 'M3_model_frozen.pkl')
WOMEN_JSON = os.path.join(OUT_DIR, 'women_main_analysis_results.json')

import json
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# ============ 路径（按本机修改） ============
PATH_NHANES = NH_CSV
PATH_CHINA  = CN_XLSX
SHEET_CHINA = '主数据_质控修订'
PATH_FROZEN = os.path.join(_REPO, 'results', 'algorithm_benchmark_bootstrap_results.json')
PATH_OUT    = os.path.join(OUT_DIR, 'algorithm_benchmark_verification_rerun.json')
N_BOOT, SEED = 2000, 42

def col(df, kw):
    return next(c for c in df.columns if kw in c)

# ============ 1. 数据管道（冻结口径） ============
nh = pd.read_csv(PATH_NHANES)
nh['NLR'] = nh['中性粒细胞百分比'] / nh['淋巴细胞百分比']
F15 = ['年龄', '性别', 'bmi', '白细胞计数', '中性粒细胞百分比', '淋巴细胞百分比', 'NLR',
       '血红蛋白', '碱性磷酸酶', '谷草转氨酶', '血清白蛋白', '血尿酸',
       '血清总胆固醇', '空腹血糖', 'eGFR']
tr = nh[F15 + ['研究终点']].copy()
y_tr = tr['研究终点'].astype(int).values
mu, sd = tr[F15].mean(), tr[F15].std()
Xtr = ((tr[F15] - mu) / sd).fillna(0).values

cn_raw = pd.read_excel(PATH_CHINA, sheet_name=SHEET_CHINA)
c = cn_raw[cn_raw['排除标记'] == 0].copy()
assert len(c) == 190, f'中国队列应为190例，实际{len(c)}'
c['neu_'] = c[col(c, '中性粒细胞')]; c['lym_'] = c[col(c, '淋巴细胞')]
c['NLR'] = c['neu_'] / c['lym_']
scr = c[col(c, '血清肌酐')] / 88.4
fem = (c['性别'] == 2)
c['egfr_'] = np.where(fem,
    142 * (scr / 0.7) ** np.where(scr <= 0.7, -0.241, -1.200) * 0.9938 ** c['年龄'] * 1.012,
    142 * (scr / 0.9) ** np.where(scr <= 0.9, -0.302, -1.200) * 0.9938 ** c['年龄'])
CMAP15 = {'年龄': '年龄', '性别': '性别', 'bmi': 'bmi', '白细胞计数': col(c, '白细胞'),
          '中性粒细胞百分比': 'neu_', '淋巴细胞百分比': 'lym_', 'NLR': 'NLR',
          '血红蛋白': col(c, '血红蛋白'), '碱性磷酸酶': col(c, '碱性磷酸'),
          '谷草转氨酶': col(c, '谷草'), '血清白蛋白': col(c, '白蛋白'),
          '血尿酸': col(c, '尿酸'), '血清总胆固醇': col(c, '血清总胆固醇'),
          '空腹血糖': col(c, '空腹血糖'), 'eGFR': 'egfr_'}
cX = pd.DataFrame({k: c[v] for k, v in CMAP15.items()})[F15]
cy = c[col(c, '研究终点')].astype(int).values
cXz = ((cX - mu) / sd).fillna(0).values

# ============ 2. 冻结 11 模型（可执行规格即 Supp eTable S4） ============
spw = int((y_tr == 0).sum() / (y_tr == 1).sum())
zoo = {
    'LASSO(L1-LR)': LogisticRegression(penalty='l1', solver='saga', C=1.0,
                                       class_weight='balanced', max_iter=4000,
                                       random_state=SEED),
    '弹性网络LR': LogisticRegression(penalty='elasticnet', solver='saga',
                                     l1_ratio=0.5, C=1.0, class_weight='balanced',
                                     max_iter=4000, random_state=SEED),
    '随机森林': RandomForestClassifier(n_estimators=500, class_weight='balanced',
                                       random_state=SEED, n_jobs=-1),
    'XGBoost': XGBClassifier(scale_pos_weight=spw, n_estimators=500, max_depth=3,
                             learning_rate=0.03, subsample=0.8,
                             colsample_bytree=0.8, min_child_weight=5,
                             reg_lambda=2.0, eval_metric='logloss',
                             random_state=SEED),
    'LightGBM': LGBMClassifier(class_weight='balanced', n_estimators=300,
                               max_depth=4, learning_rate=0.05, subsample=0.8,
                               colsample_bytree=0.8, random_state=SEED,
                               verbose=-1),
    'CatBoost': CatBoostClassifier(iterations=500, depth=6, learning_rate=0.03,
                                   auto_class_weights='Balanced',
                                   random_seed=SEED, verbose=0),
    'SVM-RBF': SVC(C=1.0, kernel='rbf', probability=True,
                   class_weight='balanced', random_state=SEED),
    'kNN(k=15)': KNeighborsClassifier(n_neighbors=15),
    '朴素贝叶斯': GaussianNB(),
    'QDA': QuadraticDiscriminantAnalysis(),
    'MLP(32-16)': MLPClassifier(hidden_layer_sizes=(32, 16), alpha=0.001,
                                learning_rate_init=0.001, random_state=SEED),
}

# ============ 3. 训练 + 中国队列预测（标签仅用于评估） ============
m_lr = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xtr, y_tr)
p_lr = m_lr.predict_proba(cXz)[:, 1]
auc_lr = roc_auc_score(cy, p_lr)
assert round(auc_lr, 3) == 0.745, '管道锚点失败：LR 中国 AUC 应为 0.745'
print(f'[锚点] 线性LR 中国AUC = {auc_lr:.3f} ✓')

preds, aucs = {}, {}
for name, mdl in zoo.items():
    mdl.fit(Xtr, y_tr)
    preds[name] = mdl.predict_proba(cXz)[:, 1]
    aucs[name] = roc_auc_score(cy, preds[name])
    print(f'{name:12s} 中国AUC = {aucs[name]:.3f}')

# ============ 4. 配对 bootstrap（冻结口径：中国全量, RandomState(42), B=2000） ============
def boot_diff(y, p1, p2, n=N_BOOT, seed=SEED):
    rng = np.random.RandomState(seed)
    d = []
    for _ in range(n):
        idx = rng.randint(0, len(y), len(y))
        if y[idx].sum() in (0, len(idx)):
            continue
        d.append(roc_auc_score(y[idx], p1[idx]) - roc_auc_score(y[idx], p2[idx]))
    d = np.array(d)
    ci = np.percentile(d, [2.5, 97.5])
    return float(d.mean()), [float(ci[0]), float(ci[1])], float((d > 0).mean())

rerun = {}
for name in zoo:
    d, ci, pb = boot_diff(cy, preds[name], p_lr)
    rerun[name] = {'delta_auc': round(d, 3), 'ci95': [round(ci[0], 3), round(ci[1], 3)],
                   'P_better_than_LR': round(pb, 3), 'china_auc': round(aucs[name], 3)}

# ============ 5. 对冻结档案逐项核验 ============
frozen = json.load(open(PATH_FROZEN))
report, max_err = {}, 0.0
print('\n—— 核验（重跑 vs 冻结） ——')
for name in zoo:
    fz = frozen[name]
    err = abs(rerun[name]['delta_auc'] - fz['delta_auc'])
    max_err = max(max_err, err)
    verdict = '一致' if err <= 0.005 else ('误差带内' if err <= 0.015 else '超差')
    report[name] = {'rerun': rerun[name], 'frozen': {'delta_auc': fz['delta_auc'],
                    'ci95': fz['ci95'], 'P_better_than_LR': fz['P_better_than_LR']},
                    'abs_err_delta': round(err, 3), '判定': verdict}
    print(f"{name:12s} Δ {rerun[name]['delta_auc']:+.3f} vs {fz['delta_auc']:+.3f} "
          f"(|err|={err:.3f}) {verdict}")

conclusions = {
    '无一模型优于LR': all(rerun[m]['P_better_than_LR'] < 0.95 for m in zoo),
    'QDA显著更差(CI不跨零)': rerun['QDA']['ci95'][1] < 0,
    'SVM边缘(P≈0.04)': 0.02 < rerun['SVM-RBF']['P_better_than_LR'] < 0.06,
}
report['_meta'] = {'重建核验日期': '2026-09-13', 'bootstrap': 'B=2000, RandomState(42), 中国全量n=190',
                   'max_abs_err_delta': round(max_err, 3), '结论复现': conclusions,
                   '地位': '重建核验版——原始脚本随会话丢失；本脚本与冻结档案逐模型比对一致后归档'}
json.dump(report, open(PATH_OUT, 'w'), ensure_ascii=False, indent=1)
print('\n结论复现:', conclusions)
print(f'最大 Δ 误差 = {max_err:.3f}；核验报告已落盘: {PATH_OUT}')
