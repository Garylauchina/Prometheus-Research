# V11 Step 49 — C Ablation Switch (C_off vs C_on) — 2025-12-30

目的：把 C 维度（`C_prev_net_intent`）明确为**可控实验变量**，并保证任何实验结论可复核：
- 同一代码基线，仅切换一个开关：`C_off` vs `C_on`
- 开关状态必须写入 `run_manifest.json` + feature/probe contract info（机器可读）

前置：
- Step 48 Spec：`docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_20251230.md`
- Step 48 Quant 落地：`docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`

---

## 1) 开关定义（冻结）

新增配置项（建议命名）：
- `c_feature_mode`: `"C_off"` | `"C_on"`

语义：
- `C_on`：按 Step48 规则计算 `C_prev_net_intent`（tick=1 null；tick>=2 来自 t-1 聚合）
- `C_off`：强制关闭 C 维度的“信息作用”
  - 推荐方式：保持维度不变，但对 `C_prev_net_intent` **强制 mask=0**（值可为 0/None 但必须 mask=0 且 reason_code="c_feature_off"）
  - 禁止方式：删维度/改向量长度（破坏固定维度 contract）

---

## 2) 证据化要求（冻结）

当 run 产生 `run_manifest.json` 时，必须记录：
- `feature_contract_version`
- `c_feature_mode`（C_off/C_on）

当 feature/probe contract 输出 contract info 时，必须包含：
- `c_feature_mode`（或 `c_ablation_mode`）
- `c_probe_definition`：说明 `C_prev_net_intent` 的来源与 tick=1 缺省
- `c_off_policy`：mask=0 + reason_code

---

## 3) 最小验收（Quant 落地必须达成）

必须提供一个脚本或 CI fixture 验证：

### 3.1 C_on 验收
- tick=1：`C_prev_net_intent` mask=0，reason_code="no_prev_tick"
- tick=2：`C_prev_net_intent` 来自 tick=1 的聚合，mask=1

### 3.2 C_off 验收
- tick>=1：`C_prev_net_intent` 一律 mask=0，reason_code="c_feature_off"
- 且 `run_manifest.json` 与 contract info 中明确记录 `c_feature_mode="C_off"`

---

## 4) 破坏性变更边界（提醒）

- C_off/C_on 只能改变 mask/值来源，不得改变 probe 维度与顺序。
- 若未来要引入更多 C probes（比如 entropy/open_ratio/close_ratio），必须走新的 contract version，并明确为 additive-only 或 major bump。


