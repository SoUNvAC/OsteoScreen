# 韩国 M3 Tier 1b: analytic class-prior correction（终审 P1-1 批准的确定性补充，2026-09-13；v2 口径统一 2026-09-13）
# v2 变更：文件名与注释统一为 "correction"（approximating the natural-prior probability scale）；
#          结果 JSON 的 slope 改报无惩罚 GLM 口径 1.64（= raw 1.64，logit 位移按构造不变）。
#          计算与预测输出零改动，与 v1 逐位一致。
# 输入：冻结 M3 规范（模型规范附录_M3_v2.json）+ 韩国女性验证集（韩国队列最终验证集_v1.csv）
# 变换：p_natural = expit(logit(p_balanced) − log(w1/w0))，w1=3.4908, w0=0.5836（冻结类权重）
# 不训练模型、不调参、不改数据集；仅对冻结预测做确定性 logit 平移。
import json, os, numpy as np, pandas as pd
from scipy.special import expit, logit
from sklearn.metrics import brier_score_loss
# Release path configuration (v1.2.4): repository-relative, env-overridable
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get('OPTRANS_DATA_DIR', os.path.join(_REPO, 'data'))
SPEC_DIR = os.path.join(_REPO, 'model_specs')
KR_CSV = os.path.join(DATA_DIR, 'korea_knhanes_women_v1.csv')  # NOT distributed; rebuild from KNHANES (KDCA) per docs/
m3 = json.load(open(os.path.join(SPEC_DIR, 'M3_specification.json'), encoding='utf-8'))
kr = pd.read_csv(KR_CSV)
feats8=m3['features']
beta=np.array([m3['coefficients'][f] for f in feats8])
mu=np.array([m3['scaler_mean'][f] for f in feats8]); sd=np.array([m3['scaler_scale'][f] for f in feats8])
Xk=pd.DataFrame({'age':kr['age'],'bmi':kr['bmi'],'wbc':kr['wbc'],'hb':kr['hb_gL'],
                 'ast':kr['ast'],'tc':kr['tc_mmol'],'fbg':kr['fbg_mmol'],'egfr':kr['egfr']})
y=kr['op_nhanes'].astype(int).values
L=(Xk[feats8].values-mu)/sd @ beta + m3['intercept']
p_raw=expit(L)
w1,w0=m3['class_weight']['w1'],m3['class_weight']['w0']
p_cor=expit(logit(np.clip(p_raw,1e-12,1-1e-12))-np.log(w1/w0))
print('MCE %+.4f | Brier %.4f'%(p_cor.mean()-y.mean(), brier_score_loss(y,p_cor)))
# 输出：MCE -0.2294 | Brier 0.2550
