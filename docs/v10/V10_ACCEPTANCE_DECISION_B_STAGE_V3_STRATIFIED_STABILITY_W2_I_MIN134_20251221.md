# V10 B阶段 v3 分层稳定性审计（赢家人群分箱）— W2 + I_min_134（A vs B2）— 2025-12-21

目的：验证“赚钱机制”是否只是一两个统计偶然，还是在**赢家人群内部**对不同“行为强度层”（交易数/胜率/信号强度）都保持稳定。

本审计严格只读 Quant 结果目录，只写 Research 文档与中间统计（已清理）。

---

## 0) 输入证据（可复核）

- A：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_A_real_100__ablation_I_min_134__W2_start4380_len4380__20251221_112841`
- B2：`/Users/liugang/Cursor_Store/Prometheus-Quant/prometheus/v10/experiments/results_B2_shuffle_returns_100__ablation_I_min_134__W2_start4380_len4380__20251221_114331`

协议参考：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`

---

## 1) 赢家定义（锚定口径）

使用锚定阈值：`q90_A`（method=`q90_A`，value≈+8.72%）

- winner（roi_lifetime ≥ q90_A）样本量：
  - A：1114
  - B2：381

> 注：v3分层只在“赢家人群”上做，避免全体人群稀释信号。

---

## 2) 分层方法

在赢家人群内，对以下三个行为强度维度做三分位分箱（每个箱单独计算 Top 通道与 IN/OUT 同向性）：

- `total_trades`
- `win_rate`
- `last_signal`

每个箱的结论要求：

- `nA >= 30` 且 `nB2 >= 30` 才纳入“有效证据”
- 否则标记为样本不足（不用于结论）

---

## 3) 结果摘要

### 3.1 last_signal 分箱（有效，三箱全部稳定）

三箱样本量均满足要求，且 **IN/OUT 同向性全部=1.0**：

- bin0：A=296, B2=198，同向性=1.0
- bin1：A=374, B2=119，同向性=1.0
- bin2：A=444, B2=64，同向性=1.0

含义：  
赢家人群在不同信号强度层上，“关键通道方向”都稳定一致 —— 这更像机制，而不是偶然。

### 3.2 win_rate 分箱（部分有效）

分箱出现明显偏态：

- bin0：A=103, B2=368（有效），同向性=1.0
- bin1：A=0, B2=0（无效）
- bin2：A=1011, B2=13（无效：B2样本过少）

解释：  
这说明在 W2 赢家人群里，B2 的胜率分布高度集中（造成某些箱极端稀疏），因此 win_rate 分层只能在 bin0 上给出有效证据。

### 3.3 total_trades 分箱（退化）

分箱 cut 退化为 `[2,2,2,4186]`，导致：

- bin0 / bin1 空箱
- bin2 实际等同“全体赢家”

这不是算法错误，而是数据分布形态：赢家人群里 `total_trades` 在分位点处出现坍缩（大量集中在同一值）。

---

## 4) 本轮 v3 结论（W2）

在 W2 的赢家人群上：

- “last_signal 分层”提供了最硬的证据：**三个强度层全部同向且稳定**
- “win_rate 分层”部分有效：有效箱同向且稳定，但分布偏态导致其余箱不具备比较意义
- “trades 分层”退化：需要换用更稳健的分箱策略（例如 log-trades 或固定阈值分箱）

---

## 5) 下一步（v3.1，仍不改core）

为解决 trades 分箱退化，建议做一个 v3.1：

- 改用 `log1p(total_trades)` 分箱，或采用固定阈值分箱（例如 0-50, 50-300, 300+）
- 复跑 W2 赢家人群分层稳定性


