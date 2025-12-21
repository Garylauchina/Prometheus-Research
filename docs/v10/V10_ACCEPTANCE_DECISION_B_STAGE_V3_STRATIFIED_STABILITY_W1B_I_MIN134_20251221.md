# V10 B阶段 v3 分层稳定性审计（赢家人群分箱）— W1b + I_min_134（A vs B2）— 2025-12-21

目的：验证“生存窗口（W1b）下的赢家/存活机制”是否在赢家人群内部对不同“行为强度层”保持稳定（而非单点偶然）。

本审计严格只读 Quant 结果目录，只写 Research 文档与中间统计（已清理）。

---

## 0) 输入证据（可复核）

- A：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W1b_start0_len4380__20251221_115821`
- B2：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W1b_start0_len4380__20251221_121143`

协议参考：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`

---

## 1) 赢家定义（锚定口径，退化处理已生效）

由于 W1b 中 `q90_A=0` 会退化，因此按协议使用：

- anchor：`q95_A`（value≈+0.65%）

- winner（roi_lifetime ≥ anchor）样本量：
  - A：586
  - B2：397

---

## 2) 分层方法

在赢家人群内，按三分位对以下维度分箱：

- `total_trades`
- `win_rate`
- `last_signal`

每箱要求 `nA>=30` 且 `nB2>=30` 才纳入结论。

---

## 3) 结果摘要（W1b：三维分层均稳定）

### 3.1 total_trades 分箱（全部有效、同向性=1.0）

- bin0：A=214, B2=111，同向性=1.0
- bin1：A=145, B2=179，同向性=1.0
- bin2：A=227, B2=107，同向性=1.0

### 3.2 win_rate 分箱（全部有效、同向性=1.0）

- bin0：A=226, B2=99，同向性=1.0
- bin1：A=164, B2=160，同向性=1.0
- bin2：A=196, B2=138，同向性=1.0

### 3.3 last_signal 分箱（全部有效、同向性=1.0）

- bin0：A=190, B2=135，同向性=1.0
- bin1：A=196, B2=128，同向性=1.0
- bin2：A=200, B2=134，同向性=1.0

含义：  
W1b 的赢家机制在三个维度的强度分层里都稳定同向，这为“可重复机制”提供了比 v2 更硬的证据。

---

## 4) 本轮 v3 结论（W1b）

在 W1b 的赢家人群上：

- 三种行为强度分层全部稳定同向（同向性=1.0）
- 每个分箱的样本量均充分，结论可靠度高于 W2 的某些退化分箱情形

这说明：W1b 的关键差异通道不是“靠某个角落的赢家撑起来”，而是对赢家人群内多个强度层都成立。


