# V11 Step 48 — I/C Probes Injection Implemented in Quant — 2025-12-30

目的：记录 Step 48（I 维度来自 Ledger triad 注入 + C_prev_net_intent(t-1)）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点（含 SHA）与最小验收事实。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP48_I_C_PROBES_INJECTION_SSOT_20251230.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`504757d`
- Quant commit（完整）：`504757d9be4b1ce4b4e07f70ebeb5a38c8763665`
- message：`v11: Step48 inject I/C probes (ledger triad I + C_prev_net_intent)`

---

## 2) 落地摘要（用户验收事实）

变更文件：
- `prometheus/v11/core/features_contract.py`
  - contract version：`V11_FEATURE_PROBE_CONTRACT_20251230.1`
  - feature dimension：13
  - 新增 I probes：
    - `I_position_exposure_ratio`（index 6）
    - `I_pos_side_sign`（index 7）
  - 新增 C probe：
    - `C_prev_net_intent`（index 11）
  - 新增 `compute_c_prev_net_intent()`（从 decision_trace(t-1) 聚合）

新增验收脚本：
- `tools/verify_step48_i_c_probes.py`
  - 验证：contract info、I null 纪律（quality 驱动 mask）、C tick=1 null、C tick>=2 来自 t-1

关键硬约束（实现侧）：
- I 注入：禁止读取 agent-local `has_position/position_direction`；quality!=ok → I probes mask=0（不伪造 0）
- C 注入：只来自 tick=t-1 聚合；tick=1 → null + `reason_code="no_prev_tick"`（不伪造 0）


