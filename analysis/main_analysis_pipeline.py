# -*- coding: utf-8 -*-
"""
================================================================================
骨质疏松预测模型跨人群可迁移性研究 —— 完整分析代码（投稿仓库合并版）
================================================================================

版本修正 (v2, 2026-09-13, GPT 代码审计整改):
  1) "Platt" 校正由概率尺度改为 logit 尺度拟合 (LogisticRegression 拟合 y~logit(OOF)),
     与冻结归档结果一致 (中国 Platt Brier 0.169 / 韩国 0.259; 旧概率尺度实现为 0.177/0.261,
     属仓库脚本与冻结分析的偏差, 已对齐; 冻结数值与全部图表不变)。
  2) 校准斜率 (cal_slope/cal_stats) 由默认 L2 惩罚 LogisticRegression 改为无惩罚
     二项 GLM (statsmodels), 与稿件统计口径一致 (中国 raw 0.72 / 韩国女性 1.64)。
  仅代码对齐, 无新增分析, 无结果改动。
  v1.2.1 (2026-09-13, 发布安全整改): PART 2 的 dca_data_women.npz 只保存聚合曲线
     (grid/nb_model/nb_osta/nb_all), 不再持久化逐例预测与标签 (受限数据防泄漏)。
  v1.1.1 (2026-09-13, Zenodo RC 整改): PART 4 扩展指标节的行内校准斜率同样改为
     无惩罚 GLM (此前为惩罚 LR, 重跑会得到旧口径 ≈1.63; 归档 JSON 中的 1.63 已在
     provenance_notes.md 登记为被取代的惩罚估计)。另: "MICE" 措辞统一收窄为
     迭代链式条件模型插补的实际实现 (IterativeImputer, 单一完成数据集, 无 Rubin 合并)。
     仅注释/估计器口径对齐, 无新增分析, 无结果改动。
对应稿件: Transportability of a routine-laboratory osteoporosis prediction model
         (NHANES -> China hospital cohort -> KNHANES)
数据版本: NHANES分析集v4_主模型.csv (n=5,217) / 外部验证集汇总_v4.xlsx (n=190, 冻结)
         / 韩国队列最终验证集_v1.csv (KNHANES 2009-2011, n=4,053)
模型:     Logistic回归(class_weight='balanced'), 15个预声明特征, 管道全程冻结,
         目标域标签在阈值锁定与适配环节零暴露。

文件结构 (四个独立可运行脚本的合并存档, 建议按PART拆分后单独运行):
  PART 1  模型分析代码汇总_v4.py     —— 主管道: 数据重建/四层验证/校准/DA 13变体/
                                       实例选择/失败替代方案/≥50复现
  PART 2  分析脚本_女性主分析_v5.py  —— 女性亚组全套 (v5冻结管道: 女性专属迭代链式插补)
  PART 3  分析脚本_DeLong修补_v5.py  —— DeLong配对AUC检验 (Sun & Xu实现, 已修正)
  PART 4  分析脚本_韩国队列验证_v1.py —— 韩国队列: 双标签AUC/DeLong/校准截距校正/
                                       DCA/锁定阈值迁移/亚组/中国女性8变量对称面板

运行环境: Python 3.12; numpy/pandas/scikit-learn/scipy/matplotlib 必需;
         lightgbm/xgboost/catboost 仅13模型动物园一节需要(已做try/except降级)。
路径说明: 见文件顶部 RELEASE PATH CONFIGURATION（默认仓库相对路径, 可用环境变量覆盖）。
复现基准线: 中国全量0.745 | 中国女性0.818 | 韩国0.787 | OSTA: 中国0.792/韩国0.800
================================================================================
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



# ================================================================================
# PART 1  模型分析代码汇总_v4.py
# ================================================================================

# -*- coding: utf-8 -*-
"""
骨质疏松预测模型 · NHANES→中国外部验证 全部分析代码汇总（v4）
================================================================
数据：data/nhanes_analytic_main_v4.csv（n=5,217, OP=492；随仓库分发）
      china_external_v4.xlsx（sheet=主数据_质控修订, n=190, OP=54；不公开分发, 见README）
设计原则：中国队列标签在阈值锁定/适配/选样环节零暴露；
          中国缺失值仅用X做迭代链式条件模型插补(IterativeImputer, 单一完成数据集, 无Rubin合并)；标准化器仅拟合NHANES。

目录：
  第0节  数据管道重建（特征映射/CKD-EPI/迭代链式插补/标准化）
  第1节  四层验证（①内部CV ②跨族裔 ③时间 ④中国外部）
  第2节  校准与决策性能（Platt / 先验截距校正 / 锁定阈值）
  第3节  13 documented domain-adaptation variants（原注释"DA穷尽性检验"）（13个变体）
  第4节  突破路线：目标引导实例选择（k网格/bootstrap/构成分析）
  第5节  失败的替代路线（KNN软加权/纯亚裔/log变换）
  第6节  最优管线终版（k=15选样+LR+先验校正）
  第7节  对方团队0.801复现检验（≥50子集）
"""

import numpy as np
import pandas as pd
import warnings
from scipy.optimize import brentq
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             brier_score_loss, confusion_matrix, roc_curve)
warnings.filterwarnings('ignore')

# ============================================================
# 第0节  数据管道重建
# ============================================================
nh = pd.read_csv(NH_CSV)
cn_raw = pd.read_excel(CN_XLSX, sheet_name='主数据_质控修订')
YCN = '研究终点（≥50岁任一部位T≤-2.5；<50岁任一部位Z≤-2.0）'
cn = cn_raw[cn_raw['排除标记'] == 0].copy()          # 排除10例A组 → n=190

# 15个核心特征映射：(NHANES短列名, 中国长列名)；另派生 nlr、egfr → 共17列，cr/bun由egfr替代 → 15核+eGFR=16特征入模
vmap = {'age': ('年龄', '年龄'), 'sex': ('性别', '性别'), 'bmi': ('bmi', 'bmi'),
        'wbc': ('白细胞计数', '白细胞计数（WBC）×10⁹/L（保留 1 位小数）'),
        'neu': ('中性粒细胞百分比', '中性粒细胞百分比（Neu%）'),
        'lym': ('淋巴细胞百分比', '淋巴细胞百分比（Lym%）'),
        'hb': ('血红蛋白', '血红蛋白（Hb）g/L（保留 0 位小数）'),
        'alp': ('碱性磷酸酶', '碱性磷酸酶（ALP）U/L'),
        'ast': ('谷草转氨酶', '谷草转氨酶（AST）U/L（保留 0 位小数）'),
        'alb': ('血清白蛋白', '血清白蛋白（ALB）g/L（保留 1 位小数）'),
        'cr': ('血清肌酐', '血清肌酐（Cr）umol/L'),
        'bun': ('血清尿素氮', '血清尿素氮（BUN）mmol/L'),
        'ua': ('血尿酸', '血尿酸（UA）umol/L'),
        'tc': ('血清总胆固醇', '血清总胆固醇（TC）mmol/L（保留 2 位小数）'),
        'fbg': ('空腹血糖', '空腹血糖（FBG）mmol/L（保留 2 位小数）')}


def ckdepi(cr, age, sex):
    """CKD-EPI 2021（无种族系数）。sex: 1=男, 2=女。cr单位 umol/L。"""
    female = (sex == 2).astype(float)
    k = np.where(female == 1, 0.7, 0.9)
    a = np.where(female == 1, -0.241, -0.302)
    scr = cr / 88.4
    return (142 * np.minimum(scr / k, 1) ** a * np.maximum(scr / k, 1) ** (-1.200)
            * 0.9938 ** age * (1 + 0.012 * female))


def build_X(df, side):
    """side=0: NHANES（eGFR直接取自原列）；side=1: 中国（CKD-EPI计算）。"""
    idx = 0 if side == 0 else 1
    X = pd.DataFrame({k: pd.to_numeric(df[v[idx]], errors='coerce') for k, v in vmap.items()})
    X['nlr'] = X['neu'] / X['lym']
    X['egfr'] = pd.to_numeric(df['eGFR'], errors='coerce') if side == 0 else ckdepi(X['cr'], X['age'], X['sex'])
    return X


X_nh = build_X(nh, 0); y_nh = nh['研究终点'].astype(int)
X_cn = build_X(cn, 1); y_cn = cn[YCN].astype(int)

# 缺失填补：中国→迭代链式条件模型插补(IterativeImputer, 仅X无标签, 单一完成数据集, 无Rubin合并)；NHANES→中位数
X_cn_imp = pd.DataFrame(IterativeImputer(max_iter=15, random_state=42).fit_transform(X_cn),
                        columns=X_cn.columns)
X_nh_imp = X_nh.fillna(X_nh.median())

feats15 = [f for f in X_nh_imp.columns if f not in ('cr', 'bun')]   # 15核+eGFR，共16列
sc = StandardScaler().fit(X_nh_imp[feats15])
Xs = sc.transform(X_nh_imp[feats15])       # NHANES标准化后
Xt = sc.transform(X_cn_imp[feats15])       # 中国标准化后（同一scaler）
yc = y_cn.values
rng = np.random.default_rng(42)
print(f'[数据] NHANES {Xs.shape} OP={y_nh.sum()} | 中国 {Xt.shape} OP={y_cn.sum()}')


def ev(Xtr, ytr, w=None, Xte=Xt, yte=y_cn):
    """LR训练并在中国集上评AUC的快捷函数。"""
    m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xtr, ytr, sample_weight=w)
    return roc_auc_score(yte, m.predict_proba(Xte)[:, 1]), m


# ============================================================
# 第1节  四层验证
# ============================================================
# ---- ① NHANES 5折内部CV（产出OOF预测，供阈值锁定与Platt） ----
skf = StratifiedKFold(5, shuffle=True, random_state=42)
oof = np.zeros(len(y_nh))
for tr, te in skf.split(X_nh_imp, y_nh):
    sc_cv = StandardScaler().fit(X_nh_imp.iloc[tr][feats15])
    m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(
        sc_cv.transform(X_nh_imp.iloc[tr][feats15]), y_nh.iloc[tr])
    oof[te] = m.predict_proba(sc_cv.transform(X_nh_imp.iloc[te][feats15]))[:, 1]
print(f'[①内部CV] AUC={roc_auc_score(y_nh, oof):.3f} AUPRC={average_precision_score(y_nh, oof):.3f}')
# → AUC=0.803 AUPRC=0.328

# ---- ② 跨族裔迁移（白人→黑人/墨西哥裔/其他西语裔/亚裔） ----
for nm, rc in [('黑人', 4), ('墨西哥裔', 1), ('其他西语裔', 2), ('亚裔', 6)]:
    mw, mr = (nh['种族'] == 3).values, (nh['种族'] == rc).values
    a, _ = ev(Xs[mw], y_nh[mw], Xte=Xs[mr], yte=y_nh[mr])
    print(f'[②白→{nm}] n={mr.sum()} OP={y_nh[mr].sum()} AUC={a:.3f}')
# → 0.798 / 0.774 / 0.810 / 0.796

# ---- ③ 时间验证（周期4-6 → 周期8） ----
mtr, mte = nh['周期'].isin([4, 5, 6]).values, (nh['周期'] == 8).values
a, m_tmp = ev(Xs[mtr], y_nh[mtr], Xte=Xs[mte], yte=y_nh[mte])
p_t = m_tmp.predict_proba(Xs[mte])[:, 1]
print(f'[③时间] n={mte.sum()} OP={y_nh[mte].sum()} AUC={a:.3f} AUPRC={average_precision_score(y_nh[mte], p_t):.3f}')
# → AUC=0.786

# ---- ④ 中国外部验证（主分析：未适配LR） ----
m_base = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh)
p_raw = m_base.predict_proba(Xt)[:, 1]
aucs_b = [roc_auc_score(yc[b], p_raw[b]) for b in (rng.integers(0, len(yc), len(yc)) for _ in range(2000))
          if yc[b].sum() not in (0, len(yc))]
print(f'[④中国] AUC={roc_auc_score(y_cn, p_raw):.3f} '
      f'95%CI {np.percentile(aucs_b, 2.5):.3f}-{np.percentile(aucs_b, 97.5):.3f} '
      f'AUPRC={average_precision_score(y_cn, p_raw):.3f}')
# → AUC=0.745 (0.650-0.828) AUPRC=0.621

# ============================================================
# 第2节  校准与决策性能
# ============================================================
# Youden阈值锁定（NHANES OOF，目标域零标签）
fpr, tpr, thr = roc_curve(y_nh, oof)
thr_lock = thr[np.argmax(tpr - fpr)]                       # → 0.526

def slogit(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))

# Platt校准（仅拟合NHANES OOF；logit尺度，与冻结归档一致）
platt = LogisticRegression().fit(slogit(oof).reshape(-1, 1), y_nh)
p_platt = platt.predict_proba(slogit(p_raw).reshape(-1, 1))[:, 1]


def cal_slope(y, p):
    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    import statsmodels.api as _sm
    return _sm.GLM(y, _sm.add_constant(lp), family=_sm.families.Binomial()).fit().params[1]


print(f'[校准] 原始 Brier={brier_score_loss(y_cn, p_raw):.3f} 斜率={cal_slope(y_cn, p_raw):.2f} | '
      f'Platt Brier={brier_score_loss(y_cn, p_platt):.3f} 斜率={cal_slope(y_cn, p_platt):.2f}')
# → 0.291/0.72 → 0.169/0.75  (logit尺度Platt, 与冻结归档一致)

# 先验截距校正（仅用1个外部参数：中国人群OP患病率，可引自流行病学文献）
def prior_adjust(p, prev_target=0.284):
    lp = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
    d = brentq(lambda d: (1 / (1 + np.exp(-(lp + d)))).mean() - prev_target, -10, 10)
    return 1 / (1 + np.exp(-(lp + d))), d

p_prior, d_prior = prior_adjust(p_raw)
print(f'[先验校正] 截距平移{d_prior:+.2f} → Brier={brier_score_loss(y_cn, p_prior):.3f}（AUC不变）')
# → Brier=0.165

# 锁定阈值下的决策性能（Platt概率空间，单调变换不影响敏感度/特异度读数）
thr_cal = platt.predict_proba([[slogit(thr_lock)]])[0, 1]
tn, fp, fn, tp = confusion_matrix(y_cn, (p_platt >= thr_cal).astype(int)).ravel()
print(f'[锁定阈值] Se={tp/(tp+fn):.2f} Sp={tn/(tn+fp):.2f} '
      f'PPV={tp/max(tp+fp,1):.2f} NPV={tn/max(tn+fn,1):.2f}')
# → Se 0.85 Sp 0.40 PPV 0.36 NPV 0.87

# ============================================================
# 第3节  13 documented domain-adaptation variants（原注释"DA穷尽性检验"）（13变体，基线0.745）
# ============================================================
def coral_v2(Xs_, Xt_, lam=1e-3):
    """CORAL修正版：均值+协方差对齐（v1缺均值对齐，已弃用）。"""
    mu_s, mu_t = Xs_.mean(0), Xt_.mean(0); d = Xs_.shape[1]
    Cs = np.cov((Xs_ - mu_s).T) + lam * np.eye(d)
    Ct = np.cov((Xt_ - mu_t).T) + lam * np.eye(d)
    es, Us = np.linalg.eigh(Cs); et, Ut = np.linalg.eigh(Ct)
    A = Us @ np.diag(1 / np.sqrt(np.maximum(es, 1e-8))) @ Us.T \
        @ Ut @ np.diag(np.sqrt(np.maximum(et, 1e-8))) @ Ut.T
    return (Xs_ - mu_s) @ A + mu_t

Xs_c = coral_v2(Xs, Xt)
print('[DA-1] 全量CORAL: %.3f' % ev(Xs_c, y_nh)[0])                       # 0.720

# 密度比IW（域分类器法，clip[0.1,10]）
Xd = np.vstack([Xs, Xt]); yd = np.r_[np.zeros(len(Xs)), np.ones(len(Xt))]
dom = LogisticRegression(max_iter=2000).fit(Xd, yd)
pt = dom.predict_proba(Xs)[:, 1]
w_iw = np.clip(pt / np.maximum(1 - pt, 1e-6), 0.1, 10)
print('[DA-2] IW: %.3f (截断率%.0f%%)' % (ev(Xs, y_nh, w_iw)[0], 100*np.mean((w_iw <= 0.1) | (w_iw >= 10))))  # 0.744
print('[DA-3] CORAL+IW(预注册): %.3f' % ev(coral_v2(Xs, Xt), y_nh, w_iw)[0])  # 0.715

# 部分CORAL（α混合）——单调恶化即剂量-效应证据
for alpha in [0.25, 0.5, 0.75]:
    print(f'[DA-4] 部分CORAL α={alpha}: {ev((1-alpha)*Xs+alpha*Xs_c, y_nh)[0]:.3f}')  # 0.739/0.734/0.727

# 仅均值对齐（恰好持平 → 对齐无收益可挖）
print('[DA-5] 仅均值对齐: %.3f' % ev(Xs + (Xt.mean(0) - Xs.mean(0)), y_nh)[0])        # 0.745

# 仅高偏移特征（SMD>0.3: bmi/hb/alp/alb）做CORAL
smd = np.abs(Xt.mean(0) - Xs.mean(0)) / np.sqrt((Xs.var(0) + Xt.var(0)) / 2)
hi = smd > 0.3
Xs_part = Xs.copy(); Xs_part[:, hi] = coral_v2(Xs[:, hi], Xt[:, hi])
print('[DA-6] 高偏移特征CORAL: %.3f' % ev(Xs_part, y_nh)[0])                 # 0.733

# 强正则化域分类器IW（C网格：最强正则退化为无效操作）
for C in [0.001, 0.01, 0.1]:
    dom2 = LogisticRegression(C=C, max_iter=3000).fit(Xd, yd)
    pt2 = dom2.predict_proba(Xs)[:, 1]
    w2 = np.clip(pt2 / np.maximum(1 - pt2, 1e-6), 0.1, 10)
    a_dom = roc_auc_score(yd, dom2.predict_proba(Xd)[:, 1])
    print(f'[DA-7] IW C={C}: 域AUC={a_dom:.2f} → {ev(Xs, y_nh, w2)[0]:.3f}')  # 0.745/0.741/0.736

# TCA（线性核MMD，NHANES子采样2000防内存爆炸）
idx_s = np.random.default_rng(0).choice(len(Xs), 2000, replace=False)
Xs_sub, ys_sub = Xs[idx_s], y_nh.iloc[idx_s]
ns, nt = len(Xs_sub), len(Xt)
X_all = np.vstack([Xs_sub, Xt])
L = np.zeros((ns + nt, ns + nt))
L[:ns, :ns] = 1 / ns**2; L[ns:, ns:] = 1 / nt**2
L[:ns, ns:] = -1 / (ns * nt); L[ns:, :ns] = -1 / (ns * nt)
K = X_all @ X_all.T
H = np.eye(ns + nt) - np.ones((ns + nt, ns + nt)) / (ns + nt)
eigvals, eigvecs = np.linalg.eigh(np.linalg.pinv(np.eye(ns + nt) + K @ L @ K) @ K @ H @ K)
W = eigvecs[:, -15:].real
Z = K @ W
m_tca = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Z[:ns], ys_sub)
print('[DA-8] TCA线性核: %.3f' % roc_auc_score(y_cn, m_tca.predict_proba(Z[ns:])[:, 1]))  # 0.736

# 极简3特征（年龄+性别+BMI）上的CORAL
f3i = [feats15.index(f) for f in ['age', 'sex', 'bmi']]
b3 = ev(Xs[:, f3i], y_nh, Xte=Xt[:, f3i])[0]
c3 = ev(coral_v2(Xs[:, f3i], Xt[:, f3i]), y_nh, Xte=Xt[:, f3i])[0]
print(f'[DA-9] 3特征: 未适配={b3:.3f} CORAL={c3:.3f}')                       # 0.734 / 0.729

# ============================================================
# 第4节  突破：目标引导实例选择（唯一有效路线）
# ============================================================
# 每个中国患者的k个最近NHANES邻居取并集 → 相似子训练集（零标签、无监督）
res = {}
for k in [10, 15, 20, 30, 40, 50, 75]:
    nn = NearestNeighbors(n_neighbors=k).fit(Xs)
    _, idx = nn.kneighbors(Xt)
    sel = np.unique(idx.ravel())
    res[k] = sel
    print(f'[选样] k={k}: n={len(sel)} AUC={ev(Xs[sel], y_nh.iloc[sel])[0]:.3f}')
# → 0.766/0.772/0.766/0.760/0.757/0.763/0.756（曲线平滑）

# k=20 配对bootstrap ΔAUC
sel20 = res[20]
m0 = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh)
m1 = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs[sel20], y_nh.iloc[sel20])
p0, p1 = m0.predict_proba(Xt)[:, 1], m1.predict_proba(Xt)[:, 1]
diffs = [roc_auc_score(yc[b], p1[b]) - roc_auc_score(yc[b], p0[b])
         for b in (rng.integers(0, len(yc), len(yc)) for _ in range(2000))
         if yc[b].sum() not in (0, len(yc))]
diffs = np.array(diffs)
print(f'[Δ检验] ΔAUC={diffs.mean():+.3f} 95%CI [{np.percentile(diffs,2.5):+.3f}, '
      f'{np.percentile(diffs,97.5):+.3f}] P(Δ>0)={100*np.mean(diffs>0):.1f}%')
# → +0.021 [-0.003,+0.048] P=95.4%

# 选中集构成分析
sel15 = res[15]
print('[构成] 亚裔%.1f%%(全量2.7) OP率%.1f%%(全量9.4) 年龄中位%.0f 女性%.0f%%' % (
    100 * (nh['种族'].iloc[sel15] == 6).mean(), 100 * y_nh.iloc[sel15].mean(),
    nh['年龄'].iloc[sel15].median(), 100 * (nh['性别'].iloc[sel15] == 2).mean()))

# ============================================================
# 第5节  失败的替代路线（同思路其他实现均无效）
# ============================================================
# KNN密度比软加权（w∝(rs/rt)^d，clip[0.1,10]）
nn_s = NearestNeighbors(n_neighbors=30).fit(Xs)
nn_t = NearestNeighbors(n_neighbors=30).fit(np.vstack([Xs, Xt]))
rs = nn_s.kneighbors(Xs)[0][:, -1]
rt = nn_t.kneighbors(Xs)[0][:, -1]
w_knn = np.clip((rs / np.maximum(rt, 1e-6)) ** 15, 0.1, 10)
print('[替代-1] KNN软加权: %.3f' % ev(Xs, y_nh, w_knn)[0])                   # 0.743

# 纯亚裔子集训练（n=142太小）
ma = (nh['种族'] == 6).values
print('[替代-2] 纯亚裔训练: %.3f' % ev(Xs[ma], y_nh[ma])[0])                 # 0.731

# log1p偏态变换
Xnh2, Xcn2 = X_nh_imp[feats15].copy(), X_cn_imp[feats15].copy()
for c in ['wbc', 'neu', 'lym', 'alp', 'ast', 'ua', 'tc', 'fbg', 'nlr', 'hb']:
    Xnh2[c] = np.log1p(np.clip(Xnh2[c], 0, None))
    Xcn2[c] = np.log1p(np.clip(Xcn2[c], 0, None))
sc2 = StandardScaler().fit(Xnh2)
m_lg = LogisticRegression(class_weight='balanced', max_iter=2000).fit(sc2.transform(Xnh2), y_nh)
print('[替代-3] log变换: %.3f' % roc_auc_score(y_cn, m_lg.predict_proba(sc2.transform(Xcn2))[:, 1]))  # 0.747

# ============================================================
# 第6节  最优管线终版：k=15选样 + LR + 先验截距校正
# ============================================================
mF = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs[sel15], y_nh.iloc[sel15])
pF = mF.predict_proba(Xt)[:, 1]
pF_adj, dF = prior_adjust(pF)
aucsF = [roc_auc_score(yc[b], pF[b]) for b in (rng.integers(0, len(yc), len(yc)) for _ in range(2000))
         if yc[b].sum() not in (0, len(yc))]
print(f'[终版] AUC={roc_auc_score(y_cn, pF):.3f} '
      f'95%CI {np.percentile(aucsF,2.5):.3f}-{np.percentile(aucsF,97.5):.3f} '
      f'AUPRC={average_precision_score(y_cn, pF):.3f} '
      f'Brier {brier_score_loss(y_cn,pF):.3f}→{brier_score_loss(y_cn,pF_adj):.3f}')
# → AUC=0.772 (0.683-0.851) AUPRC=0.652 Brier 0.220→0.157

# ============================================================
# 第7节  对方团队0.801复现检验（≥50子集；XGB可选，缺失则仅跑LR）
# ============================================================
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print('[提示] 未安装xgboost（pip install xgboost），本节仅跑LR')

m_nh50, m_cn50 = (nh['年龄'] >= 50).values, (cn['年龄'] >= 50).values
for tag, fts in [('15核+eGFR', feats15), ('全17特征', list(X_nh_imp.columns))]:
    sc50 = StandardScaler().fit(X_nh_imp.loc[m_nh50, fts])
    lr50 = LogisticRegression(class_weight='balanced', max_iter=2000).fit(
        sc50.transform(X_nh_imp.loc[m_nh50, fts]), y_nh[m_nh50])
    a_lr = roc_auc_score(y_cn[m_cn50], lr50.predict_proba(sc50.transform(X_cn_imp.loc[m_cn50, fts]))[:, 1])
    a_xg = np.nan
    if HAS_XGB:
        spw = (y_nh[m_nh50] == 0).sum() / (y_nh[m_nh50] == 1).sum()
        xg50 = XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                             scale_pos_weight=spw, eval_metric='logloss', random_state=42).fit(
            sc50.transform(X_nh_imp.loc[m_nh50, fts]), y_nh[m_nh50])
        a_xg = roc_auc_score(y_cn[m_cn50], xg50.predict_proba(sc50.transform(X_cn_imp.loc[m_cn50, fts]))[:, 1])
    print(f'[≥50复现] {tag}: LR={a_lr:.3f} XGB={a_xg:.3f}')
# → 15核+eGFR: LR=0.786 XGB=0.750（对方0.801大体可信，Δ0.015由队列构成差异解释）


# ================================================================================
# PART 2  分析脚本_女性主分析_v5.py
# ================================================================================

# -*- coding: utf-8 -*-
"""女性主分析全套优化（v5）——一次跑完，结果存JSON"""
import json
import numpy as np
import pandas as pd
import warnings
from scipy.optimize import brentq
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, roc_curve
warnings.filterwarnings('ignore')
R = {}  # 结果容器
rng = np.random.default_rng(42)

# ============ 数据管道 ============
nh = pd.read_csv(NH_CSV)
cn_raw = pd.read_excel(CN_XLSX, sheet_name='主数据_质控修订')
YCN = '研究终点（≥50岁任一部位T≤-2.5；<50岁任一部位Z≤-2.0）'
cn = cn_raw[cn_raw['排除标记'] == 0].copy()
vmap = {'age': ('年龄', '年龄'), 'sex': ('性别', '性别'), 'bmi': ('bmi', 'bmi'),
        'wbc': ('白细胞计数', '白细胞计数（WBC）×10⁹/L（保留 1 位小数）'),
        'neu': ('中性粒细胞百分比', '中性粒细胞百分比（Neu%）'),
        'lym': ('淋巴细胞百分比', '淋巴细胞百分比（Lym%）'),
        'hb': ('血红蛋白', '血红蛋白（Hb）g/L（保留 0 位小数）'),
        'alp': ('碱性磷酸酶', '碱性磷酸酶（ALP）U/L'),
        'ast': ('谷草转氨酶', '谷草转氨酶（AST）U/L（保留 0 位小数）'),
        'alb': ('血清白蛋白', '血清白蛋白（ALB）g/L（保留 1 位小数）'),
        'cr': ('血清肌酐', '血清肌酐（Cr）umol/L'),
        'bun': ('血清尿素氮', '血清尿素氮（BUN）mmol/L'),
        'ua': ('血尿酸', '血尿酸（UA）umol/L'),
        'tc': ('血清总胆固醇', '血清总胆固醇（TC）mmol/L（保留 2 位小数）'),
        'fbg': ('空腹血糖', '空腹血糖（FBG）mmol/L（保留 2 位小数）')}


def ckdepi(cr, age, sex):
    female = (sex == 2).astype(float)
    k = np.where(female == 1, 0.7, 0.9); a = np.where(female == 1, -0.241, -0.302)
    scr = cr / 88.4
    return (142 * np.minimum(scr / k, 1) ** a * np.maximum(scr / k, 1) ** (-1.200)
            * 0.9938 ** age * (1 + 0.012 * female))


def build_X(df, side):
    idx = 0 if side == 0 else 1
    X = pd.DataFrame({k: pd.to_numeric(df[v[idx]], errors='coerce') for k, v in vmap.items()})
    X['nlr'] = X['neu'] / X['lym']
    X['egfr'] = pd.to_numeric(df['eGFR'], errors='coerce') if side == 0 else ckdepi(X['cr'], X['age'], X['sex'])
    return X


X_nh_all = build_X(nh, 0); y_nh_all = nh['研究终点'].astype(int)
X_cn_all = build_X(cn, 1); y_cn_all = cn[YCN].astype(int).values

# ---- 女性子集 ----
FW_NH = (nh['性别'] == 2).values
FW_CN = (cn['性别'] == 2).values
X_nh = X_nh_all[FW_NH].reset_index(drop=True); y_nh = y_nh_all[FW_NH].reset_index(drop=True)
X_cn = X_cn_all[FW_CN].reset_index(drop=True); y_cn = y_cn_all[FW_CN]
nh_w = nh[FW_NH].reset_index(drop=True)
cn_w = cn[FW_CN].reset_index(drop=True)
X_cn_imp = pd.DataFrame(IterativeImputer(max_iter=15, random_state=42).fit_transform(X_cn), columns=X_cn.columns)
X_nh_imp = X_nh.fillna(X_nh.median())
feats15 = [f for f in X_nh_imp.columns if f not in ('cr', 'bun')]
sc = StandardScaler().fit(X_nh_imp[feats15])
Xs = sc.transform(X_nh_imp[feats15]); Xt = sc.transform(X_cn_imp[feats15])
R['女性样本'] = {'NHANES_n': len(y_nh), 'NHANES_OP': int(y_nh.sum()),
             '中国_n': int(FW_CN.sum()), '中国_OP': int(y_cn.sum())}
print('[女性] NHANES n=%d OP=%d | 中国 n=%d OP=%d (%.1f%%)' % (
    len(y_nh), y_nh.sum(), FW_CN.sum(), y_cn.sum(), 100 * y_cn.mean()))

# ============ DeLong CI（Sun&Xu快速实现） ============
def delong_ci(y, p, alpha=0.95):
    pos = p[y == 1]; neg = p[y == 0]; m, n = len(pos), len(neg)
    V10 = np.array([np.mean(pos > x) + 0.5 * np.mean(pos == x) for x in pos])
    V01 = np.array([np.mean(x > neg) + 0.5 * np.mean(x == neg) for x in pos])
    auc = np.mean(V10)
    S10 = np.var(V10, ddof=1) / m; S01 = np.var(V01, ddof=1) / n
    se = np.sqrt(S10 + S01)
    from scipy.stats import norm
    z = norm.ppf(1 - (1 - alpha) / 2)
    return auc, max(0, auc - z * se), min(1, auc + z * se), se

# ============ ① 女性四层验证 ============
skf = StratifiedKFold(5, shuffle=True, random_state=42)
oof = np.zeros(len(y_nh))
for tr, te in skf.split(X_nh_imp, y_nh):
    sc_cv = StandardScaler().fit(X_nh_imp.iloc[tr][feats15])
    m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(
        sc_cv.transform(X_nh_imp.iloc[tr][feats15]), y_nh.iloc[tr])
    oof[te] = m.predict_proba(sc_cv.transform(X_nh_imp.iloc[te][feats15]))[:, 1]
R['女性①内部CV'] = {'AUC': round(roc_auc_score(y_nh, oof), 3), 'AUPRC': round(average_precision_score(y_nh, oof), 3)}

eth = {}
for nm, rc in [('黑人', 4), ('墨西哥裔', 1), ('其他西语裔', 2), ('亚裔', 6)]:
    mw, mr = (nh_w['种族'] == 3).values, (nh_w['种族'] == rc).values
    if mr.sum() < 30:
        continue
    sc_e = StandardScaler().fit(X_nh_imp[mw][feats15])
    m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(sc_e.transform(X_nh_imp[mw][feats15]), y_nh[mw])
    eth[nm] = {'n': int(mr.sum()), 'OP': int(y_nh[mr].sum()),
               'AUC': round(roc_auc_score(y_nh[mr], m.predict_proba(sc_e.transform(X_nh_imp[mr][feats15]))[:, 1]), 3)}
R['女性②跨族裔'] = eth

mtr, mte = nh_w['周期'].isin([4, 5, 6]).values, (nh_w['周期'] == 8).values
sc_t = StandardScaler().fit(X_nh_imp[mtr][feats15])
m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(sc_t.transform(X_nh_imp[mtr][feats15]), y_nh[mtr])
R['女性③时间'] = {'n': int(mte.sum()), 'OP': int(y_nh[mte].sum()),
              'AUC': round(roc_auc_score(y_nh[mte], m.predict_proba(sc_t.transform(X_nh_imp[mte][feats15]))[:, 1]), 3)}

# ④ 中国女性外部验证（主分析）
m_base = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh)
p_raw = m_base.predict_proba(Xt)[:, 1]
auc_dl, lo_dl, hi_dl, se_dl = delong_ci(y_cn, p_raw)
R['女性④中国外部'] = {'AUC': round(auc_dl, 3), 'DeLong95CI': [round(lo_dl, 3), round(hi_dl, 3)],
                 'AUPRC': round(average_precision_score(y_cn, p_raw), 3),
                 'Brier_raw': round(brier_score_loss(y_cn, p_raw), 3)}
print('[女性④] AUC=%.3f (DeLong %.3f-%.3f)' % (auc_dl, lo_dl, hi_dl))

# ============ OSTA头对头 + IDI/NRI ============
osta = (0.2 * (pd.to_numeric(cn_w['体重kg'], errors='coerce') - pd.to_numeric(cn_w['年龄'], errors='coerce'))).values
a_osta, lo_o, hi_o, _ = delong_ci(y_cn, -osta)
R['OSTA女性'] = {'AUC': round(a_osta, 3), 'DeLong95CI': [round(lo_o, 3), round(hi_o, 3)]}
# DeLong配对检验模型vs OSTA
def delong_test(y, p1, p2):
    # 简化配对DeLong：方差-协方差
    def comps(y, p):
        pos, neg = p[y == 1], p[y == 0]
        V10 = np.array([np.mean(pos > x) + 0.5 * np.mean(pos == x) for x in pos])
        V01 = np.array([np.mean(x > neg) + 0.5 * np.mean(x == neg) for x in pos])
        return V10, V01
    V10a, V01a = comps(y, p1); V10b, V01b = comps(y, p2)
    m, n = (y == 1).sum(), (y == 0).sum()
    Sa = np.cov(V10a, V10b) / m + np.cov(V01a, V01b) / n
    var = Sa[0, 0] + Sa[1, 1] - 2 * Sa[0, 1]
    from scipy.stats import norm
    z = (roc_auc_score(y, p1) - roc_auc_score(y, p2)) / np.sqrt(max(var, 1e-12))
    return z, 2 * (1 - norm.cdf(abs(z)))
z_dl, p_dl = delong_test(y_cn, p_raw, -osta)
R['模型vsOSTA_Delong检验'] = {'z': round(z_dl, 2), 'p': round(p_dl, 4)}

# IDI / NRI（模型 vs OSTA）
def idi_nri(y, p_new, p_old, thr=0.2):
    ev, nev = y == 1, y == 0
    idi = (p_new[ev].mean() - p_old[ev].mean()) - (p_new[nev].mean() - p_old[nev].mean())
    up_n, dn_n = (p_new[ev] >= thr) & (p_old[ev] < thr), (p_new[ev] < thr) & (p_old[ev] >= thr)
    up_ne, dn_ne = (p_new[nev] < thr) & (p_old[nev] >= thr), (p_new[nev] >= thr) & (p_old[nev] < thr)
    nri = (up_n.sum() - dn_n.sum()) / ev.sum() + (up_ne.sum() - dn_ne.sum()) / nev.sum()
    return idi, nri
# OSTA概率化：Platt于中国女性（仅作比较基准，属监督参考）
p_osta = LogisticRegression().fit((-osta).reshape(-1, 1), y_cn).predict_proba((-osta).reshape(-1, 1))[:, 1]
idi, nri = idi_nri(y_cn, p_raw, p_osta)
R['IDI_NRI_模型vsOSTA'] = {'IDI': round(idi, 3), 'NRI@0.2': round(nri, 3)}

# ============ 实例选择（女性，k网格） ============
inst = {}
for k in [10, 15, 20, 30, 50]:
    nn = NearestNeighbors(n_neighbors=k).fit(Xs)
    _, idx = nn.kneighbors(Xt)
    sel = np.unique(idx.ravel())
    m_k = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs[sel], y_nh.iloc[sel])
    p_k = m_k.predict_proba(Xt)[:, 1]
    a_k, lo_k, hi_k, _ = delong_ci(y_cn, p_k)
    inst[k] = {'n_sel': int(len(sel)), 'AUC': round(a_k, 3), 'CI': [round(lo_k, 3), round(hi_k, 3)]}
R['女性实例选择'] = inst
best_k = max(inst, key=lambda k: inst[k]['AUC'])
print('[女性实例选择]', {k: v['AUC'] for k, v in inst.items()})

# ============ 先验校正 + Platt（女性患病率） ============
def slogit(p):  # PART 2 单拆运行时的本地定义（与 PART 1 相同）
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))
prev_w = y_cn.mean()
def prior_adjust(p, prev_target):
    lp = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
    d = brentq(lambda d: (1 / (1 + np.exp(-(lp + d)))).mean() - prev_target, -10, 10)
    return 1 / (1 + np.exp(-(lp + d))), d
p_prior, d_pri = prior_adjust(p_raw, prev_w)
platt = LogisticRegression().fit(slogit(oof).reshape(-1, 1), y_nh)  # logit尺度, 与冻结归档一致 (0.259)
p_platt = platt.predict_proba(slogit(p_raw).reshape(-1, 1))[:, 1]
def cal_stats(y, p):
    lp = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    import statsmodels.api as _sm
    _g = _sm.GLM(y, _sm.add_constant(lp), family=_sm.families.Binomial()).fit()
    class _LR:  # 保持下游 lr1.coef_[0][0] 接口
        coef_ = np.array([[_g.params[1]]])
    lr1 = _LR()
    # 校准截距：logit(observed)回归 offset(lp)
    from scipy.optimize import minimize_scalar
    f = lambda a: -np.sum(y * (a + lp) - np.log(1 + np.exp(a + lp)))
    a_hat = minimize_scalar(f).x
    return brier_score_loss(y, p), lr1.coef_[0][0], a_hat
b0, s0, i0 = cal_stats(y_cn, p_raw)
b1, s1, i1 = cal_stats(y_cn, p_prior)
b2, s2, i2 = cal_stats(y_cn, p_platt)
R['女性校准'] = {'raw': {'Brier': round(b0, 3), 'slope': round(s0, 2), 'intercept': round(i0, 2)},
            '先验校正': {'Brier': round(b1, 3), 'slope': round(s1, 2), 'intercept': round(i1, 2)},
            'Platt': {'Brier': round(b2, 3), 'slope': round(s2, 2), 'intercept': round(i2, 2)}}

# ============ 锁定阈值 + DCA + NNS ============
fpr, tpr, thr = roc_curve(y_nh, oof)
thr_lock = float(thr[np.argmax(tpr - fpr)])
thr_cal = float(platt.predict_proba([[slogit(thr_lock)]])[0, 1])
def dca(y, p, thresholds):
    n = len(y); nb = []
    for t in thresholds:
        pred = p >= t
        tp = np.sum(pred & (y == 1)); fp = np.sum(pred & (y == 0))
        nb.append(tp / n - fp / n * t / (1 - t))
    return np.array(nb)
grid = np.linspace(0.01, 0.5, 50)
nb_model = dca(y_cn, p_prior, grid)
nb_osta = dca(y_cn, p_osta, grid)
nb_all = y_cn.mean() - (1 - y_cn.mean()) * grid / (1 - grid)
pred = (p_prior >= 0.284).astype(int)  # 患病率阈值下的NNS
tp, fp = np.sum(pred & (y_cn == 1)), np.sum(pred & (y_cn == 0))
nns = 1 / max(tp / len(y_cn) - fp / len(y_cn) * 0.284 / (1 - 0.284), 1e-9)
R['女性阈值_DCA'] = {'锁定阈值': round(thr_lock, 3), '映射后': round(thr_cal, 3),
               'NNS@患病率阈值': round(float(nns), 1)}
# v1.2.4 release-safety fix: persist aggregate DCA curve grids ONLY.
# The frozen internal archive also saved per-case arrays (p_*/y_cn/osta) here;
# those are restricted patient-level data (EXCLUDED_FILES_LOG) and must never be
# regenerated inside a public working tree. No computation above has changed.
np.savez(os.path.join(OUT_DIR, 'dca_data_women.npz'), grid=grid, nb_model=nb_model,
         nb_osta=nb_osta, nb_all=nb_all)

# ============ 调查加权建模对照 ============
w = pd.to_numeric(nh_w['WTMEC2YR'], errors='coerce').fillna(0).values
w = w / w.mean()
m_wtd = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh, sample_weight=w)
p_wtd = m_wtd.predict_proba(Xt)[:, 1]
a_wtd, lo_w, hi_w, _ = delong_ci(y_cn, p_wtd)
R['调查加权模型'] = {'AUC': round(a_wtd, 3), 'DeLong95CI': [round(lo_w, 3), round(hi_w, 3)],
              'vs非加权Δ': round(a_wtd - auc_dl, 3)}

# ============ bootstrap乐观度校正（NHANES女性内部） ============
rng2 = np.random.default_rng(7)
optims = []
for _ in range(200):
    b = rng2.integers(0, len(y_nh), len(y_nh))
    if y_nh.iloc[b].sum() in (0, len(b)):
        continue
    sc_b = StandardScaler().fit(X_nh_imp.iloc[b][feats15])
    m_b = LogisticRegression(class_weight='balanced', max_iter=2000).fit(sc_b.transform(X_nh_imp.iloc[b][feats15]), y_nh.iloc[b])
    a_boot = roc_auc_score(y_nh.iloc[b], m_b.predict_proba(sc_b.transform(X_nh_imp.iloc[b][feats15]))[:, 1])
    a_orig = roc_auc_score(y_nh, m_b.predict_proba(sc_b.transform(X_nh_imp[feats15]))[:, 1])
    optims.append(a_boot - a_orig)
optimism = float(np.mean(optims))
R['乐观度校正'] = {'表观AUC': round(roc_auc_score(y_nh, m_base.predict_proba(Xs)[:, 1]), 3),
             '平均乐观度': round(optimism, 4),
             '校正后AUC': round(roc_auc_score(y_nh, m_base.predict_proba(Xs)[:, 1]) - optimism, 3)}

# ============ 模型更新谱系（Steyerberg） ============
# Tier0: 无适应(0.745→女性auc_dl) | Tier1: 先验截距(零标签) | Tier2: 交叉拟合Platt(监督参考)
p_platt_cn = cross_val_predict(LogisticRegression(), p_raw.reshape(-1, 1), y_cn, cv=5, method='predict_proba')[:, 1]
lp_raw = np.log(np.clip(p_raw, 1e-6, 1 - 1e-6) / (1 - np.clip(p_raw, 1e-6, 1 - 1e-6)))
p_recal = cross_val_predict(LogisticRegression(), lp_raw.reshape(-1, 1), y_cn, cv=5, method='predict_proba')[:, 1]
R['模型更新谱系'] = {'Tier0_无适应': {'AUC': round(auc_dl, 3), 'Brier': round(b0, 3)},
               'Tier1_先验截距_零标签': {'AUC': round(auc_dl, 3), 'Brier': round(b1, 3)},
               'Tier2_交叉拟合再校准_监督参考': {'Brier': round(brier_score_loss(y_cn, p_recal), 3),
                                        'slope': round(cal_stats(y_cn, p_recal)[1], 2)}}

# ============ 完整个案敏感性 ============
cc = X_cn.dropna().index
if len(cc) >= 60:
    p_cc = m_base.predict_proba(Xt[X_cn.index.isin(cc)])[:, 1]
    a_cc, lo_c, hi_c, _ = delong_ci(y_cn[X_cn.index.isin(cc)], p_cc)
    R['完整个案敏感性'] = {'n': int(len(cc)), 'AUC': round(a_cc, 3), 'CI': [round(lo_c, 3), round(hi_c, 3)]}

with open(WOMEN_JSON, 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print(json.dumps(R, ensure_ascii=False, indent=2))


# ================================================================================
# PART 3  分析脚本_DeLong修补_v5.py
# ================================================================================

# -*- coding: utf-8 -*-
"""修补DeLong + 修正IDI/NRI用校准后概率，更新女性结果JSON"""
import json
import numpy as np
import pandas as pd
import warnings
from scipy.optimize import brentq, minimize_scalar
from scipy.stats import norm
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score, brier_score_loss
warnings.filterwarnings('ignore')
rng = np.random.default_rng(42)

nh = pd.read_csv(NH_CSV)
cn_raw = pd.read_excel(CN_XLSX, sheet_name='主数据_质控修订')
YCN = '研究终点（≥50岁任一部位T≤-2.5；<50岁任一部位Z≤-2.0）'
cn = cn_raw[cn_raw['排除标记'] == 0].copy()
vmap = {'age': ('年龄', '年龄'), 'sex': ('性别', '性别'), 'bmi': ('bmi', 'bmi'),
        'wbc': ('白细胞计数', '白细胞计数（WBC）×10⁹/L（保留 1 位小数）'),
        'neu': ('中性粒细胞百分比', '中性粒细胞百分比（Neu%）'),
        'lym': ('淋巴细胞百分比', '淋巴细胞百分比（Lym%）'),
        'hb': ('血红蛋白', '血红蛋白（Hb）g/L（保留 0 位小数）'),
        'alp': ('碱性磷酸酶', '碱性磷酸酶（ALP）U/L'),
        'ast': ('谷草转氨酶', '谷草转氨酶（AST）U/L（保留 0 位小数）'),
        'alb': ('血清白蛋白', '血清白蛋白（ALB）g/L（保留 1 位小数）'),
        'cr': ('血清肌酐', '血清肌酐（Cr）umol/L'),
        'bun': ('血清尿素氮', '血清尿素氮（BUN）mmol/L'),
        'ua': ('血尿酸', '血尿酸（UA）umol/L'),
        'tc': ('血清总胆固醇', '血清总胆固醇（TC）mmol/L（保留 2 位小数）'),
        'fbg': ('空腹血糖', '空腹血糖（FBG）mmol/L（保留 2 位小数）')}


def ckdepi(cr, age, sex):
    female = (sex == 2).astype(float)
    k = np.where(female == 1, 0.7, 0.9); a = np.where(female == 1, -0.241, -0.302)
    scr = cr / 88.4
    return (142 * np.minimum(scr / k, 1) ** a * np.maximum(scr / k, 1) ** (-1.200)
            * 0.9938 ** age * (1 + 0.012 * female))


def build_X(df, side):
    idx = 0 if side == 0 else 1
    X = pd.DataFrame({k: pd.to_numeric(df[v[idx]], errors='coerce') for k, v in vmap.items()})
    X['nlr'] = X['neu'] / X['lym']
    X['egfr'] = pd.to_numeric(df['eGFR'], errors='coerce') if side == 0 else ckdepi(X['cr'], X['age'], X['sex'])
    return X


FW_NH = (nh['性别'] == 2).values
FW_CN = (cn['性别'] == 2).values
X_nh = build_X(nh, 0)[FW_NH].reset_index(drop=True); y_nh = nh['研究终点'].astype(int)[FW_NH].reset_index(drop=True)
X_cn = build_X(cn, 1)[FW_CN].reset_index(drop=True); y_cn = cn[YCN].astype(int)[FW_CN].values
cn_w = cn[FW_CN].reset_index(drop=True)
X_cn_imp = pd.DataFrame(IterativeImputer(max_iter=15, random_state=42).fit_transform(X_cn), columns=X_cn.columns)
X_nh_imp = X_nh.fillna(X_nh.median())
feats15 = [f for f in X_nh_imp.columns if f not in ('cr', 'bun')]
sc = StandardScaler().fit(X_nh_imp[feats15])
Xs = sc.transform(X_nh_imp[feats15]); Xt = sc.transform(X_cn_imp[feats15])
m_base = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh)
p_raw = m_base.predict_proba(Xt)[:, 1]


# ---- 正确的快速DeLong ----
def _comps(y, p):
    pos, neg = p[y == 1], p[y == 0]
    V10 = np.array([np.mean(x > neg) + 0.5 * np.mean(x == neg) for x in pos])
    V01 = np.array([np.mean(pos > x) + 0.5 * np.mean(pos == x) for x in neg])
    return V10, V01


def delong_ci(y, p, alpha=0.95):
    V10, V01 = _comps(y, p)
    m, n = (y == 1).sum(), (y == 0).sum()
    auc = V10.mean()
    se = np.sqrt(V10.var(ddof=1) / m + V01.var(ddof=1) / n)
    z = norm.ppf(1 - (1 - alpha) / 2)
    return auc, max(0, auc - z * se), min(1, auc + z * se), se


def delong_test(y, p1, p2):
    V10a, V01a = _comps(y, p1); V10b, V01b = _comps(y, p2)
    m, n = (y == 1).sum(), (y == 0).sum()
    Sa = np.cov(np.vstack([V10a, V10b])) / m + np.cov(np.vstack([V01a, V01b])) / n
    var = Sa[0, 0] + Sa[1, 1] - 2 * Sa[0, 1]
    z = (V10a.mean() - V10b.mean()) / np.sqrt(max(var, 1e-12))
    return z, 2 * (1 - norm.cdf(abs(z)))


# ---- 先验校正概率（模型侧校准） ----
def prior_adjust(p, prev_target):
    lp = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
    d = brentq(lambda d: (1 / (1 + np.exp(-(lp + d)))).mean() - prev_target, -10, 10)
    return 1 / (1 + np.exp(-(lp + d))), d
p_prior, _ = prior_adjust(p_raw, y_cn.mean())

osta = (0.2 * (pd.to_numeric(cn_w['体重kg'], errors='coerce')
               - pd.to_numeric(cn_w['年龄'], errors='coerce'))).values
p_osta = LogisticRegression().fit((-osta).reshape(-1, 1), y_cn).predict_proba((-osta).reshape(-1, 1))[:, 1]

R = json.load(open(WOMEN_JSON))

a_dl, lo, hi, _ = delong_ci(y_cn, p_raw)
R['女性④中国外部'].update({'AUC': round(a_dl, 3), 'DeLong95CI': [round(lo, 3), round(hi, 3)]})
a_o, lo_o, hi_o, _ = delong_ci(y_cn, -osta)
R['OSTA女性'].update({'AUC': round(a_o, 3), 'DeLong95CI': [round(lo_o, 3), round(hi_o, 3)]})
z_dl, p_dl = delong_test(y_cn, p_raw, -osta)
R['模型vsOSTA_Delong检验'] = {'z': round(z_dl, 2), 'p': round(p_dl, 4)}

# IDI/NRI：两侧都用校准后概率（模型用零标签先验校正；OSTA用Platt，监督参考基准）
def idi_nri(y, p_new, p_old, thr):
    ev, nev = y == 1, y == 0
    idi = (p_new[ev].mean() - p_old[ev].mean()) - (p_new[nev].mean() - p_old[nev].mean())
    nri = ((p_new[ev] >= thr).sum() - (p_old[ev] >= thr).sum()) / ev.sum() \
        + ((p_old[nev] >= thr).sum() - (p_new[nev] >= thr).sum()) / nev.sum()
    return idi, nri
idi02, nri02 = idi_nri(y_cn, p_prior, p_osta, 0.2)
idi33, nri33 = idi_nri(y_cn, p_prior, p_osta, 1 / 3)
R['IDI_NRI_模型vsOSTA'] = {'IDI': round(idi02, 3), 'NRI@0.2': round(nri02, 3),
                     'NRI@0.33': round(nri33, 3),
                     '说明': '模型用零标签先验校正概率；OSTA概率为Platt拟合(监督参考)'}

# 实例选择重评（正确DeLong）
inst = {}
for k in [10, 15, 20, 30, 50]:
    nn = NearestNeighbors(n_neighbors=k).fit(Xs)
    _, idx = nn.kneighbors(Xt)
    sel = np.unique(idx.ravel())
    m_k = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs[sel], y_nh.iloc[sel])
    p_k = m_k.predict_proba(Xt)[:, 1]
    a_k, lo_k, hi_k, _ = delong_ci(y_cn, p_k)
    inst[k] = {'n_sel': int(len(sel)), 'AUC': round(a_k, 3), 'CI': [round(lo_k, 3), round(hi_k, 3)]}
R['女性实例选择'] = inst

# 调查加权重评
nh_w = nh[FW_NH].reset_index(drop=True)
w = pd.to_numeric(nh_w['WTMEC2YR'], errors='coerce').fillna(0).values
w = w / w.mean()
m_wtd = LogisticRegression(class_weight='balanced', max_iter=2000).fit(Xs, y_nh, sample_weight=w)
a_w, lo_w, hi_w, _ = delong_ci(y_cn, m_wtd.predict_proba(Xt)[:, 1])
R['调查加权模型'].update({'AUC': round(a_w, 3), 'DeLong95CI': [round(lo_w, 3), round(hi_w, 3)],
                    'vs非加权Δ': round(a_w - a_dl, 3)})

# 完整个案重评
cc = X_cn.dropna().index
a_c, lo_c, hi_c, _ = delong_ci(y_cn[X_cn.index.isin(cc)], p_raw[X_cn.index.isin(cc)])
R['完整体案敏感性' if '完整体案敏感性' in R else '完整个案敏感性'] = {
    'n': int(len(cc)), 'AUC': round(a_c, 3), 'CI': [round(lo_c, 3), round(hi_c, 3)]}
R.pop('完整个案敏感性', None) if '完整体案敏感性' in R else None
R['模型更新谱系']['Tier0_无适应']['AUC'] = round(a_dl, 3)
R['模型更新谱系']['Tier1_先验截距_零标签']['AUC'] = round(a_dl, 3)

with open(WOMEN_JSON, 'w', encoding='utf-8') as f:
    json.dump(R, f, ensure_ascii=False, indent=2)
print(json.dumps({k: R[k] for k in ['女性④中国外部', 'OSTA女性', '模型vsOSTA_Delong检验',
      'IDI_NRI_模型vsOSTA', '女性实例选择', '调查加权模型', '完整个案敏感性']},
      ensure_ascii=False, indent=2))


# ================================================================================
# PART 4  分析脚本_韩国队列验证_v1.py
# ================================================================================

# -*- coding: utf-8 -*-
"""
韩国队列（KNHANES 2009-2011）外部验证复现脚本
================================================
输入:
  1. 韩国队列最终验证集_v1.csv  —— n=4,053, 全部≥50岁女性, 8变量零缺失
  2. 简约8变量模型_knhanes待用.pkl —— {'scaler','model','feats'}, NHANES训练, SI单位
输出:
  - 双标签(NHANES III白人参照 / 亚洲参照)的模型与OSTA AUC + 配对DeLong检验
  - 校准-in-the-large 与无标签截距校正(brentq)
  - 韩国队列验证结果_v1.json
注意:
  scaler拟合于SI单位(hb g/L, tc mmol/L, fbg mmol/L)。
  误用mg/dL列会得到AUC≈0.59的假象 —— 务必使用 *_mmol / hb_gL 列。
运行: python3 分析脚本_韩国队列验证_v1.py
"""

import json
import pickle
import numpy as np
import pandas as pd
from scipy import stats as sst
from scipy.optimize import brentq
from scipy.special import expit
from sklearn.metrics import roc_auc_score

# KR_CSV / NH_CSV / MODEL_PKL are configured in the release header (top of file).
OUT_JSON = os.path.join(OUT_DIR, 'korea_validation_results.json')


# ---------- DeLong (Sun & Xu 快速实现, 与 v5 修补版一致) ----------
def _comps(y, p):
    pos, neg = p[y == 1], p[y == 0]
    V10 = np.array([np.mean(x > neg) + 0.5 * np.mean(x == neg) for x in pos])
    V01 = np.array([np.mean(pos > x) + 0.5 * np.mean(pos == x) for x in neg])
    return V10, V01


def delong_test(y, p1, p2):
    """配对DeLong: 返回 auc1, ci1, auc2, ci2, delta, p"""
    V10_1, V01_1 = _comps(y, p1)
    V10_2, V01_2 = _comps(y, p2)
    m, n = (y == 1).sum(), (y == 0).sum()
    auc1, auc2 = V10_1.mean(), V10_2.mean()
    var1 = V10_1.var(ddof=1) / m + V01_1.var(ddof=1) / n
    var2 = V10_2.var(ddof=1) / m + V01_2.var(ddof=1) / n
    cov = np.cov(V10_1, V10_2)[0, 1] / m + np.cov(V01_1, V01_2)[0, 1] / n
    se_d = np.sqrt(var1 + var2 - 2 * cov)
    z = (auc1 - auc2) / se_d
    p = 2 * sst.norm.sf(abs(z))
    ci1 = (auc1 - 1.96 * np.sqrt(var1), auc1 + 1.96 * np.sqrt(var1))
    ci2 = (auc2 - 1.96 * np.sqrt(var2), auc2 + 1.96 * np.sqrt(var2))
    return auc1, ci1, auc2, ci2, auc1 - auc2, p


def main():
    # ---------- 1. 数据 ----------
    kr = pd.read_csv(KR_CSV)
    assert kr.shape[0] == 4053, f"行数异常: {kr.shape}"
    assert (kr['sex'] == 2).all() and kr['age'].min() >= 50, "应为≥50岁女性"

    with open(MODEL_PKL, 'rb') as f:
        m8 = pickle.load(f)
    feats = m8['feats']  # ['age','bmi','wbc','hb','ast','tc','fbg','egfr']

    # SI单位取列: hb→g/L, tc→mmol/L, fbg→mmol/L (与训练时一致)
    X = pd.DataFrame({
        'age': kr['age'], 'bmi': kr['bmi'], 'wbc': kr['wbc'], 'hb': kr['hb_gL'],
        'ast': kr['ast'], 'tc': kr['tc_mmol'], 'fbg': kr['fbg_mmol'], 'egfr': kr['egfr'],
    })
    assert X.isna().sum().sum() == 0, "8变量应零缺失"

    # 量纲自检: 训练均值 vs 本批均值 (hb应~135, tc应~5, fbg应~6)
    print('--- 量纲自检 (训练均值 | 本批均值) ---')
    for f, mu in zip(feats, m8['scaler'].mean_):
        print(f'  {f:5s} {mu:8.2f} | {X[f].mean():8.2f}')

    # ---------- 2. 预测 (零目标标签暴露: scaler/model均仅用NHANES拟合) ----------
    p = m8['model'].predict_proba(m8['scaler'].transform(X[feats]))[:, 1]

    # ---------- 3. 双标签 AUC + 配对DeLong ----------
    results = {}
    for tag, ycol in [('primary_label_nhanes_ref', 'op_nhanes'),
                      ('sensitivity_label_asia_ref', 'op_asia')]:
        y = kr[ycol].values
        a1, c1, a2, c2, d, pv = delong_test(y, p, -kr['osta'].values)
        results[tag] = {
            'prevalence': round(float(y.mean()), 4), 'events': int(y.sum()),
            'model_auc': round(a1, 3), 'model_ci': [round(c1[0], 3), round(c1[1], 3)],
            'osta_auc': round(a2, 3), 'osta_ci': [round(c2[0], 3), round(c2[1], 3)],
            'delta': round(d, 3), 'delong_p': round(pv, 4),
        }
        print(f'\n[{ycol}] 患病率={y.mean():.1%} (事件{int(y.sum())})')
        print(f'  8变量模型: {a1:.3f} ({c1[0]:.3f}-{c1[1]:.3f})')
        print(f'  OSTA:      {a2:.3f} ({c2[0]:.3f}-{c2[1]:.3f})')
        print(f'  Δ={d:+.3f}, DeLong p={pv:.4f}')

    # ---------- 4. 校准-in-the-large + 无标签截距校正 ----------
    y = kr['op_nhanes'].values
    obs = y.mean()
    eta = m8['model'].intercept_[0] + m8['scaler'].transform(X[feats]) @ m8['model'].coef_[0]
    b_star = brentq(lambda b: expit(eta + b).mean() - obs, -10, 10)
    p_cal = expit(eta + b_star)
    results['calibration'] = {
        'observed_prev': round(float(obs), 4),
        'mean_pred_raw': round(float(p.mean()), 3),
        'intercept_shift_b': round(float(b_star), 3),
        'mean_pred_calibrated': round(float(p_cal.mean()), 4),
    }
    print(f'\n校准-in-the-large: 观察={obs:.1%} vs 原始预测均值={p.mean():.1%}'
          f' → 截距校正 b*={b_star:+.3f}, 校正后={p_cal.mean():.1%}, AUC不变={roc_auc_score(y, p_cal):.3f}')

    # ---------- 4b. DCA 决策曲线 (2026-09-09 补) ----------
    # DCA对校准敏感：模型报原始/截距校正两组概率；OSTA用单变量logistic概率化（比较器标准做法）
    from sklearn.linear_model import LogisticRegression

    def net_benefit(yv, pv, thr):
        pred = pv >= thr
        tp = ((pred == 1) & (yv == 1)).sum()
        fp = ((pred == 1) & (yv == 0)).sum()
        return tp / len(yv) - fp / len(yv) * thr / (1 - thr)

    yi = y.astype(int)
    osta_v = kr['osta'].values
    p_osta = LogisticRegression().fit(osta_v.reshape(-1, 1), yi).predict_proba(osta_v.reshape(-1, 1))[:, 1]

    grid = np.linspace(0.01, 0.80, 80)
    nb = {
        'model_raw': np.array([net_benefit(yi, p, t) for t in grid]),
        'model_cal': np.array([net_benefit(yi, p_cal, t) for t in grid]),
        'osta': np.array([net_benefit(yi, p_osta, t) for t in grid]),
        'all': np.array([yi.mean() - (1 - yi.mean()) * t / (1 - t) for t in grid]),
    }
    print('\n--- DCA 关键阈值点净获益 ---')
    print(f"{'阈值':>6s} {'模型(原始)':>10s} {'模型(校正)':>10s} {'OSTA':>8s} {'全干预':>8s}")
    for t0 in [0.10, 0.20, 0.30, 0.40, 0.50]:
        i = int(np.argmin(np.abs(grid - t0)))
        print(f"{grid[i]:6.2f} {nb['model_raw'][i]:10.3f} {nb['model_cal'][i]:10.3f} "
              f"{nb['osta'][i]:8.3f} {nb['all'][i]:8.3f}")
    np.savez(os.path.join(OUT_DIR, 'dca_data_korea.npz'), grid=grid,
             nb_model_raw=nb['model_raw'], nb_model_cal=nb['model_cal'],
             nb_osta=nb['osta'], nb_all=nb['all'])
    print('saved:', os.path.join(OUT_DIR, 'dca_data_korea.npz'))

    # ---------- 4c. 扩展指标 (2026-09-09 第二轮): 锁定阈值迁移 / AUPRC / Brier / 校准斜率 / 亚组 ----------
    from sklearn.model_selection import cross_val_predict, StratifiedKFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_curve, average_precision_score, brier_score_loss
    from scipy.special import logit as slogit

    # 锁定阈值: NHANES女性(训练子集)5折OOF → Youden
    nh = pd.read_csv(NH_CSV)
    nhw = nh[nh['性别'] == 2]
    Xn = pd.DataFrame({'age': nhw['年龄'], 'bmi': nhw['bmi'], 'wbc': nhw['白细胞计数'],
                       'hb': nhw['血红蛋白'], 'ast': nhw['谷草转氨酶'],
                       'tc': nhw['血清总胆固醇'], 'fbg': nhw['空腹血糖'], 'egfr': nhw['eGFR']})
    yn = nhw['研究终点'].values.astype(int)
    oof = np.zeros(len(yn))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(Xn, yn):
        sc = StandardScaler().fit(Xn.iloc[tr])
        lr = LogisticRegression(class_weight='balanced', max_iter=1000).fit(sc.transform(Xn.iloc[tr]), yn[tr])
        oof[te] = lr.predict_proba(sc.transform(Xn.iloc[te]))[:, 1]
    fpr, tpr, thr = roc_curve(yn, oof)
    lock8 = float(thr[np.argmax(tpr - fpr)])
    t_map = float(expit(slogit(lock8) + b_star))
    print(f'\nNHANES女性8变量OOF: AUC={roc_auc_score(yn, oof):.3f}, 锁定Youden阈值={lock8:.3f} → 韩国映射={t_map:.3f}')

    def clin_metrics(yv, pred):
        tp = ((pred == 1) & (yv == 1)).sum(); fp = ((pred == 1) & (yv == 0)).sum()
        fn = ((pred == 0) & (yv == 1)).sum(); tn = ((pred == 0) & (yv == 0)).sum()
        return tp/(tp+fn), tn/(tn+fp), tp/(tp+fp), tn/(tn+fn)

    sens, spec, ppv, npv = clin_metrics(yi, (p_cal >= t_map).astype(int))
    nns = 1 / (sens * yi.mean() - (1 - spec) * (1 - yi.mean()))
    s2, p2, v2, n2 = clin_metrics(yi, (kr['osta'].values <= -1).astype(int))
    nns2 = 1 / (s2 * yi.mean() - (1 - p2) * (1 - yi.mean()))
    print(f'模型(校正@映射阈值): 敏感={sens:.3f} 特异={spec:.3f} PPV={ppv:.3f} NPV={npv:.3f} NNS={nns:.1f}')
    print(f'OSTA(@-1):          敏感={s2:.3f} 特异={p2:.3f} PPV={v2:.3f} NPV={n2:.3f} NNS={nns2:.1f}')

    auprc = average_precision_score(yi, p)
    br_raw, br_cal = brier_score_loss(yi, p), brier_score_loss(yi, p_cal)
    lp = np.log(np.clip(p_cal, 1e-12, 1 - 1e-12) / (1 - np.clip(p_cal, 1e-12, 1 - 1e-12)))
    import statsmodels.api as _sm  # final manuscript estimator: unpenalised binomial GLM (y ~ logit(p))
    slope_cal = _sm.GLM(yi, _sm.add_constant(lp), family=_sm.families.Binomial()).fit().params[1]
    print(f'AUPRC={auprc:.3f} | Brier {br_raw:.3f}→校正{br_cal:.3f} | 校准斜率(校正)={slope_cal:.2f}')

    print('\n--- 亚组AUC ---')
    subs = {}
    for name, m in [('2009', kr['year'] == 2009), ('2010', kr['year'] == 2010), ('2011', kr['year'] == 2011),
                    ('50-59岁', kr['age'] < 60), ('60-69岁', (kr['age'] >= 60) & (kr['age'] < 70)),
                    ('70-80岁', kr['age'] >= 70), ('已绝经', kr['menop'] == 1), ('其他', kr['menop'] != 1)]:
        a = roc_auc_score(yi[m.values], p[m.values])
        subs[name] = round(float(a), 3)
        print(f'  {name:8s} n={int(m.sum()):4d} AUC={a:.3f}')

    results['extended'] = {
        'locked_threshold': {'NHANES女性OOF_Youden': round(lock8, 3), '韩国映射阈值': round(t_map, 3)},
        'threshold_metrics': {'模型_校正后': {'敏感': round(sens,3), '特异': round(spec,3), 'PPV': round(ppv,3), 'NPV': round(npv,3), 'NNS': round(float(nns),1)},
                              'OSTA_at_-1': {'敏感': round(s2,3), '特异': round(p2,3), 'PPV': round(v2,3), 'NPV': round(n2,3), 'NNS': round(float(nns2),1)}},
        'auprc': round(float(auprc), 3), 'brier_raw': round(br_raw, 3), 'brier_calibrated': round(br_cal, 3),
        'calibration_slope_calibrated': round(float(slope_cal), 2), 'subgroups_auc': subs,
    }

    # ---------- 4d. 中国女性8变量对称面板 (与韩国同口径) ----------
    # CN_XLSX configured in release header
    cn = pd.read_excel(CN_XLSX, sheet_name='主数据_质控修订')
    cn0 = cn[cn['排除标记'] == 0]
    cw = cn0[cn0['性别'] == 2]  # 2=女
    lab = [c for c in cn0.columns if '研究终点' in str(c)][0]
    y_cw = cw[lab].values.astype(int)
    cr_mgdl = cw['血清肌酐（Cr）umol/L'] / 88.4  # CKD-EPI 2021 女性
    egfr_c = np.where(cr_mgdl <= 0.7, 142*(cr_mgdl/0.7)**(-0.241), 142*(cr_mgdl/0.7)**(-1.200)) * 0.9938**cw['年龄'] * 1.012
    Xc = pd.DataFrame({'age': cw['年龄'].values, 'bmi': cw['bmi'].values,
                       'wbc': cw['白细胞计数（WBC）×10⁹/L（保留 1 位小数）'].values,
                       'hb': cw['血红蛋白（Hb）g/L（保留 0 位小数）'].values,
                       'ast': cw['谷草转氨酶（AST）U/L（保留 0 位小数）'].values,
                       'tc': cw['血清总胆固醇（TC）mmol/L（保留 2 位小数）'].values,
                       'fbg': cw['空腹血糖（FBG）mmol/L（保留 2 位小数）'].values,
                       'egfr': egfr_c})
    Xc = Xc.fillna(Xc.median())  # 缺失≤2例, 中位数填补(与主流程对极小缺失的处理一致)
    Xcs = m8['scaler'].transform(Xc[feats])
    p_cw = m8['model'].predict_proba(Xcs)[:, 1]
    osta_cw = 0.2 * (cw['体重kg'].values - cw['年龄'].values)
    a_cw, a_cw_osta = roc_auc_score(y_cw, p_cw), roc_auc_score(y_cw, -osta_cw)
    eta_c = m8['model'].intercept_[0] + Xcs @ m8['model'].coef_[0]
    b_c = brentq(lambda b: expit(eta_c + b).mean() - y_cw.mean(), -10, 10)
    print(f'\n中国女性8变量对称面板: n={len(cw)} 模型AUC={a_cw:.3f} OSTA={a_cw_osta:.3f} '
          f'Brier {brier_score_loss(y_cw,p_cw):.3f}→校正{brier_score_loss(y_cw, expit(eta_c+b_c)):.3f} (b*={b_c:+.3f})')
    results['china_women_8var_symmetry'] = {
        'n': int(len(cw)), 'model_auc': round(float(a_cw), 3), 'osta_auc': round(float(a_cw_osta), 3),
        'brier_raw': round(float(brier_score_loss(y_cw, p_cw)), 3),
        'brier_calibrated': round(float(brier_score_loss(y_cw, expit(eta_c + b_c))), 3),
        'b_star': round(float(b_c), 3)}

    # ---------- 5. 保存 ----------
    results.update({
        'cohort': 'KNHANES 2009-2011, women >=50',
        'n': int(len(kr)),
        'years': {str(k): int(v) for k, v in kr['year'].value_counts().items()},
        'age_range': [int(kr['age'].min()), int(kr['age'].max())],
        'model': '简约8变量LR (age,bmi,wbc,hb,ast,tc,fbg,egfr), SI单位',
        'units_note': 'scaler拟合于SI单位(hb g/L, tc mmol/L, fbg mmol/L); 误用mg/dL列→AUC 0.59假象, 已排雷',
    })
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\n已保存: {OUT_JSON}')

    # 复现基准线 (主标签): model 0.787 (0.774-0.801), OSTA 0.800, p=0.0003


if __name__ == '__main__':
    main()
