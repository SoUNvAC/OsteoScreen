# -*- coding: utf-8 -*-
"""
================================================================================
校准口径修正审计脚本 v2（2026-09-13，GPT 代码审计整改轮；v2 收尾轮更新）
  v1.2.1 变更：survey-weight 敏感性设为默认关闭的 withdrawn historical audit
  （RUN_WITHDRAWN_SURVEY_AUDIT=False；仅复现归档 JSON 时打开）。其余零改动。
  v2 变更：survey-weight 敏感性增加 mean=1 规范化口径（GPT P1-条件性裁定：
  sklearn sample_weight 与 class_weight 相乘且默认 L2 正则化，权重整体尺度影响
  相对正则化强度）。其余零改动。v1 已由本版取代。
================================================================================
目的：全部为冻结结果的口径修正与审计核验，零新增分析。
  1) 无惩罚校准斜率（statsmodels 二项 GLM，y ~ logit(p)）：
     中国 M1 raw 与韩国女性 M3 raw；Tier1a 源端逻辑再校准后的斜率（同口径）；
     截距位移后斜率不变性的数值验证。
  2) Tier1a "Platt" 尺度分叉核验：logit 尺度（冻结归档口径）vs 概率尺度
     （仓库脚本旧实现）——冻结值 0.169/0.259 对应 logit 尺度。
  3) 两个主外部队列核心校准指标的 2,000 次 bootstrap 95%CI
     （seed 42，百分位法；Tier3 按重采样患病率重锚定；Tier2 在固定文献锚点
     0.192（中国）/0.37（韩国）下对重采样预测重解位移）。
  4) NHANES 调查加权（WTMEC2YR）源域重拟合敏感性：中国外部 AUC 变化。
  5) 中国女性 8 变量对称面板（M3→中国女性 n=116）logit 尺度校准截距/斜率
     的无惩罚重算（Supplement eAppendix 11 口径对齐）。

输入（冻结文件）：
  NHANES分析集v4_主模型.csv（n=5,217）/ 外部验证集汇总_v4.xlsx（n=190，排除标记==0）
  / 韩国队列最终验证集_v1.csv（KNHANES 女性 50–80，n=4,053）
  / 模型规范附录_M1.json / 模型规范附录_M3_v2.json
冻结校验（本脚本复现值 == 冻结归档值）：
  中国 M1：AUC 0.7448，MCE +0.3133，Brier 0.2908
  韩国 M3：AUC 0.7874，MCE +0.1339，Brier 0.2124
  M1 OOF AUC 0.8032；M3 女性 OOF AUC 0.7778
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
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import expit
from scipy.optimize import brentq
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

OUT_JSON = os.path.join(OUT_DIR, 'calibration_audit_results.json')


def slogit(p):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def slope_unpen(y, p):
    """无惩罚校准斜率：statsmodels 二项 GLM，y ~ logit(p)。"""
    return float(sm.GLM(y, sm.add_constant(slogit(p)),
                        family=sm.families.Binomial()).fit().params[1])


def main():
    # ---------- 冻结管线重建 ----------
    spec1 = json.load(open(os.path.join(SPEC_DIR, 'M1_specification.json'), encoding='utf-8'))
    spec3 = json.load(open(os.path.join(SPEC_DIR, 'M3_specification.json'), encoding='utf-8'))
    nh = pd.read_csv(NH_CSV)
    cn = pd.read_excel(CN_XLSX, sheet_name='主数据_质控修订')
    cn = cn[cn['排除标记'] == 0].reset_index(drop=True)
    kr = pd.read_csv(KR_CSV)
    lab = [c for c in cn.columns if '研究终点' in str(c)][0]

    f15 = spec1['features']
    vmap_nh = {'age': '年龄', 'sex': '性别', 'bmi': 'bmi', 'wbc': '白细胞计数',
               'neu': '中性粒细胞百分比', 'lym': '淋巴细胞百分比', 'hb': '血红蛋白',
               'alp': '碱性磷酸酶', 'ast': '谷草转氨酶', 'alb': '血清白蛋白',
               'ua': '血尿酸', 'tc': '血清总胆固醇', 'fbg': '空腹血糖', 'egfr': 'eGFR'}
    Xnh = pd.DataFrame({k: nh[v].values for k, v in vmap_nh.items()})
    Xnh['nlr'] = nh['中性粒细胞百分比'] / nh['淋巴细胞百分比']
    Xnh = Xnh[f15].fillna(pd.Series(spec1['impute_constants_NHANES_median'])[f15])
    y_nh = nh['研究终点'].values.astype(int)

    vmap_cn = {'age': '年龄', 'sex': '性别', 'bmi': 'bmi',
               'wbc': '白细胞计数（WBC）×10⁹/L（保留 1 位小数）',
               'neu': '中性粒细胞百分比（Neu%）', 'lym': '淋巴细胞百分比（Lym%）',
               'hb': '血红蛋白（Hb）g/L（保留 0 位小数）', 'alp': '碱性磷酸酶（ALP）U/L',
               'ast': '谷草转氨酶（AST）U/L（保留 0 位小数）',
               'alb': '血清白蛋白（ALB）g/L（保留 1 位小数）', 'ua': '血尿酸（UA）umol/L',
               'tc': '血清总胆固醇（TC）mmol/L（保留 2 位小数）',
               'fbg': '空腹血糖（FBG）mmol/L（保留 2 位小数）'}
    Xc15 = pd.DataFrame({k: cn[v].values for k, v in vmap_cn.items()})
    Xc15['nlr'] = cn['中性粒细胞百分比（Neu%）'] / cn['淋巴细胞百分比（Lym%）']
    crm = cn['血清肌酐（Cr）umol/L'] / 88.4
    female = (cn['性别'] == 2).values
    k_ = np.where(female, 0.7, 0.9)
    a_ = np.where(female, -0.241, -0.302)
    Xc15['egfr'] = (142 * np.minimum(crm / k_, 1) ** a_ * np.maximum(crm / k_, 1) ** (-1.200)
                    * 0.9938 ** cn['年龄'] * np.where(female, 1.012, 1.0))
    Xc15 = Xc15[f15]
    y_cn = cn[lab].values.astype(int)
    Xc15i = pd.DataFrame(IterativeImputer(max_iter=15, random_state=42).fit_transform(Xc15),
                         columns=f15)

    mu1, sd1 = pd.Series(spec1['scaler_mean'])[f15], pd.Series(spec1['scaler_scale'])[f15]
    b1v = pd.Series(spec1['coefficients'])[f15]
    p_cn_raw = expit(((Xc15i - mu1) / sd1).values @ b1v.values + spec1['intercept'])

    f8 = spec3['features']
    kmap = {'hb': 'hb_gL', 'tc': 'tc_mmol', 'fbg': 'fbg_mmol'}
    Xk = pd.DataFrame({f: (kr[kmap[f]] if f in kmap else kr[f]) for f in f8})
    y_kr = kr['op_nhanes'].values.astype(int)
    mu3, sd3 = pd.Series(spec3['scaler_mean'])[f8], pd.Series(spec3['scaler_scale'])[f8]
    b3v = pd.Series(spec3['coefficients'])[f8]
    p_kr_raw = expit(((Xk - mu3) / sd3).values @ b3v.values + spec3['intercept'])

    # OOF（5 折，balanced，max_iter=2000）——Tier1a 源端再校准的拟合输入
    skf = StratifiedKFold(5, shuffle=True, random_state=42)
    oof1 = np.zeros(len(y_nh))
    for tr, te in skf.split(Xnh, y_nh):
        sc = StandardScaler().fit(Xnh.iloc[tr])
        m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(
            sc.transform(Xnh.iloc[tr]), y_nh[tr])
        oof1[te] = m.predict_proba(sc.transform(Xnh.iloc[te]))[:, 1]
    wom = nh[nh['性别'] == 2].reset_index(drop=True)
    Xw = pd.DataFrame({'age': wom['年龄'], 'bmi': wom['bmi'], 'wbc': wom['白细胞计数'],
                       'hb': wom['血红蛋白'], 'ast': wom['谷草转氨酶'],
                       'tc': wom['血清总胆固醇'], 'fbg': wom['空腹血糖'],
                       'egfr': wom['eGFR']})[f8]
    Xw = Xw.fillna(pd.Series(spec3['impute_constants_NHANES_women_median'])[f8])
    y_w = wom['研究终点'].values.astype(int)
    oof3 = np.zeros(len(y_w))
    for tr, te in skf.split(Xw, y_w):
        sc = StandardScaler().fit(Xw.iloc[tr])
        m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(
            sc.transform(Xw.iloc[tr]), y_w[tr])
        oof3[te] = m.predict_proba(sc.transform(Xw.iloc[te]))[:, 1]

    R = {'frozen_checksums': {
        'china_M1': {'AUC': round(roc_auc_score(y_cn, p_cn_raw), 4),
                     'MCE': round(float(p_cn_raw.mean() - y_cn.mean()), 4),
                     'Brier': round(brier_score_loss(y_cn, p_cn_raw), 4)},
        'korea_M3': {'AUC': round(roc_auc_score(y_kr, p_kr_raw), 4),
                     'MCE': round(float(p_kr_raw.mean() - y_kr.mean()), 4),
                     'Brier': round(brier_score_loss(y_kr, p_kr_raw), 4)},
        'M1_OOF_AUC': round(roc_auc_score(y_nh, oof1), 4),
        'M3_women_OOF_AUC': round(roc_auc_score(y_w, oof3), 4)}}

    # ---------- 1) 无惩罚校准斜率 ----------
    # Tier1a：logit 尺度（冻结归档口径）与概率尺度（仓库脚本旧实现）两种拟合
    pl_l_cn = LogisticRegression().fit(slogit(oof1).reshape(-1, 1), y_nh)
    pB_cn = pl_l_cn.predict_proba(slogit(p_cn_raw).reshape(-1, 1))[:, 1]
    pl_p_cn = LogisticRegression().fit(oof1.reshape(-1, 1), y_nh)
    pP_cn = pl_p_cn.predict_proba(p_cn_raw.reshape(-1, 1))[:, 1]
    pl_l_kr = LogisticRegression().fit(slogit(oof3).reshape(-1, 1), y_w)
    pB_kr = pl_l_kr.predict_proba(slogit(p_kr_raw).reshape(-1, 1))[:, 1]
    pl_p_kr = LogisticRegression().fit(oof3.reshape(-1, 1), y_w)
    pP_kr = pl_p_kr.predict_proba(p_kr_raw.reshape(-1, 1))[:, 1]

    R['slopes_unpenalised_GLM'] = {
        'china_raw': round(slope_unpen(y_cn, p_cn_raw), 4),
        'korea_raw': round(slope_unpen(y_kr, p_kr_raw), 4),
        'china_Tier1a_logitscale': round(slope_unpen(y_cn, pB_cn), 4),
        'korea_Tier1a_logitscale': round(slope_unpen(y_kr, pB_kr), 4),
        'china_Tier1a_probscale': round(slope_unpen(y_cn, pP_cn), 4),
        'korea_Tier1a_probscale': round(slope_unpen(y_kr, pP_kr), 4),
        'china_Tier1a_logitscale_penalised_reference': round(float(
            LogisticRegression().fit(slogit(pB_cn).reshape(-1, 1), y_cn).coef_[0][0]), 4),
        'korea_Tier1a_logitscale_penalised_reference': round(float(
            LogisticRegression().fit(slogit(pB_kr).reshape(-1, 1), y_kr).coef_[0][0]), 4)}

    # 截距位移后斜率不变性（数学性质的数值验证）
    invar = {}
    for nm, y, p in [('china', y_cn, p_cn_raw), ('korea', y_kr, p_kr_raw)]:
        b = brentq(lambda d: expit(slogit(p) + d).mean() - y.mean(), -10, 10)
        invar[nm] = {'shift': round(b, 4),
                     'slope_after_shift': round(slope_unpen(y, expit(slogit(p) + b)), 6),
                     'slope_raw': round(slope_unpen(y, p), 6)}
    R['intercept_shift_slope_invariance'] = invar

    # ---------- 2) Tier1a 尺度分叉核验 ----------
    R['Tier1a_scale_fork'] = {
        'china_brier_logitscale': round(brier_score_loss(y_cn, pB_cn), 6),
        'china_brier_probscale': round(brier_score_loss(y_cn, pP_cn), 6),
        'korea_brier_logitscale': round(brier_score_loss(y_kr, pB_kr), 6),
        'korea_brier_probscale': round(brier_score_loss(y_kr, pP_kr), 6),
        'frozen_archived': {'china': 0.169, 'korea': 0.259},
        'conclusion': ('冻结归档值 0.169/0.259 与 logit 尺度实现一致（另经归档 eFigure S4 '
                       'DCA 曲线逐点核对，最大差 0.0/0.00025）；仓库脚本旧概率尺度实现 '
                       '(0.177/0.261) 已在 _v2 修正为 logit 尺度。')}

    # ---------- 3) bootstrap 95%CI ----------
    def boot_cal(y, p, anchor, B=2000, seed=42):
        rng = np.random.default_rng(seed)
        n = len(y)
        out = {k: [] for k in ['MCE', 'slope', 'Brier_raw', 'Brier_T2', 'Brier_T3',
                               'improve_T2', 'improve_T3']}
        for _ in range(B):
            idx = rng.integers(0, n, n)
            yb, pb = y[idx], p[idx]
            if yb.sum() in (0, len(yb)):
                continue
            lp = slogit(pb)
            br = brier_score_loss(yb, pb)
            b3 = brentq(lambda d: expit(lp + d).mean() - yb.mean(), -10, 10)
            b2 = brentq(lambda d: expit(lp + d).mean() - anchor, -10, 10)
            br3 = brier_score_loss(yb, expit(lp + b3))
            br2 = brier_score_loss(yb, expit(lp + b2))
            out['MCE'].append(pb.mean() - yb.mean())
            out['slope'].append(slope_unpen(yb, pb))
            out['Brier_raw'].append(br)
            out['Brier_T2'].append(br2)
            out['Brier_T3'].append(br3)
            out['improve_T2'].append(br - br2)
            out['improve_T3'].append(br - br3)
        return {k: [round(float(np.percentile(v, 2.5)), 4),
                    round(float(np.percentile(v, 97.5)), 4)] for k, v in out.items()}

    R['bootstrap_95CI_2000_seed42'] = {
        'china_M1': boot_cal(y_cn, p_cn_raw, 0.192),
        'korea_women_M3': boot_cal(y_kr, p_kr_raw, 0.37),
        'note': ('Tier3 按各重采样患病率重锚定；Tier2 在固定文献锚点（中国 0.192／韩国 0.37）'
                 '下对重采样预测重解位移；百分位法 2.5/97.5。')}

    # --------------------------------------------------------------------------------
    # WITHDRAWN HISTORICAL AUDIT — default OFF (v1.2.1)
    # Section 4 below (WTMEC2YR survey-weight sensitivity) was WITHDRAWN from the final
    # manuscript: the fasting-glucose predictor belongs to the NHANES fasting subsample,
    # whose prescribed CDC weight (WTSAF2YR) is absent from the frozen extract, so this
    # computation must not be used for inference. The archived record is retained in
    # results/calibration_audit_results.json for provenance only. Set this flag to True
    # solely to reproduce that archived JSON byte-for-byte; a normal reproduction of the
    # final manuscript leaves it False.
    RUN_WITHDRAWN_SURVEY_AUDIT = False
    if RUN_WITHDRAWN_SURVEY_AUDIT:
        # ---------- 4) 调查加权敏感性（WITHDRAWN historical audit，默认关闭） ----------
        def survey_refit(Xtr, ytr, wts, Xte, yte):
            sw = compute_sample_weight('balanced', ytr) * wts
            sc = StandardScaler().fit(Xtr)
            m = LogisticRegression(max_iter=2000).fit(sc.transform(Xtr), ytr, sample_weight=sw)
            return float(roc_auc_score(yte, m.predict_proba(sc.transform(Xte))[:, 1]))

        w_nh = nh['WTMEC2YR'].values
        m2f = (nh['性别'] == 2).values
        a1 = survey_refit(Xnh, y_nh, w_nh, Xc15i, y_cn)
        a2 = survey_refit(Xnh[m2f], y_nh[m2f], w_nh[m2f], Xc15i[female], y_cn[female])
        # mean=1 规范化口径（GPT P1-条件性）：sklearn sample_weight 与类权重相乘，
        # 默认 L2 正则化下权重整体尺度影响相对正则化强度
        a1n = survey_refit(Xnh, y_nh, w_nh / w_nh.mean(), Xc15i, y_cn)
        w2 = w_nh[m2f]
        a2n = survey_refit(Xnh[m2f], y_nh[m2f], w2 / w2.mean(), Xc15i[female], y_cn[female])
        R['survey_weight_sensitivity'] = {
            'M1_china_AUC': round(a1, 4), 'M1_delta_vs_0.7448': round(a1 - 0.7448, 4),
            'M2_china_women_AUC': round(a2, 4), 'M2_delta_vs_0.818': round(a2 - 0.818, 4),
            'M1_china_AUC_mean1_normalised': round(a1n, 4),
            'M2_china_women_AUC_mean1_normalised': round(a2n, 4),
            'note': ('WTMEC2YR × balanced 类权重。规范化（mean=1）与未规范化结果相差 ≤0.001'
                     '（0.7523 vs 0.7522；0.8242 vs 0.8232）；落文采用规范化口径：'
                     'M1 0.745→0.752、M2 0.818→0.824，变化 ≤0.008。')}

    # ---------- 5) 中国女性 8 变量对称面板（无惩罚口径重算） ----------
    cw = cn[cn['性别'] == 2]
    y_cw = cw[lab].values.astype(int)
    crw = cw['血清肌酐（Cr）umol/L'] / 88.4
    egfr_w = 142 * np.minimum(crw / 0.7, 1) ** (-0.241) * np.maximum(crw / 0.7, 1) ** (-1.200) \
        * 0.9938 ** cw['年龄'] * 1.012
    Xcw = pd.DataFrame({'age': cw['年龄'].values, 'bmi': cw['bmi'].values,
                        'wbc': cw['白细胞计数（WBC）×10⁹/L（保留 1 位小数）'].values,
                        'hb': cw['血红蛋白（Hb）g/L（保留 0 位小数）'].values,
                        'ast': cw['谷草转氨酶（AST）U/L（保留 0 位小数）'].values,
                        'tc': cw['血清总胆固醇（TC）mmol/L（保留 2 位小数）'].values,
                        'fbg': cw['空腹血糖（FBG）mmol/L（保留 2 位小数）'].values,
                        'egfr': egfr_w})[f8].fillna(Xc15i[f8].median())
    eta_cw = ((Xcw - mu3) / sd3).values @ b3v.values + spec3['intercept']
    g_pre = sm.GLM(y_cw, sm.add_constant(eta_cw), family=sm.families.Binomial()).fit()
    b_cw = brentq(lambda d: expit(eta_cw + d).mean() - y_cw.mean(), -10, 10)
    g_post = sm.GLM(y_cw, sm.add_constant(eta_cw + b_cw), family=sm.families.Binomial()).fit()
    R['china_women_8var_symmetry_unpenalised'] = {
        'n': int(len(cw)), 'AUC': round(roc_auc_score(y_cw, expit(eta_cw)), 4),
        'Brier_raw': round(brier_score_loss(y_cw, expit(eta_cw)), 4),
        'intercept_shift_b': round(b_cw, 4),
        'calib_intercept_pre': round(float(g_pre.params[0]), 4),
        'calib_intercept_post': round(float(g_post.params[0]), 4),
        'calib_slope': round(float(g_pre.params[1]), 4),
        'note': '替代旧惩罚 LR 口径（−1.42→0.10，斜率 1.17）；无惩罚 GLM 为 −1.48→0.15，斜率 1.26。'}

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    print(json.dumps(R, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
