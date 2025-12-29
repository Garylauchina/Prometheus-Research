# V11 Step 49 — C Ablation Switch Implemented in Quant — 2025-12-30

目的：记录 Step 49（`C_off` vs `C_on` 消融开关 + 证据化写入 contract/manifest）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点（含 SHA）与最小验收事实。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP49_C_ABLATION_SWITCH_20251230.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`bc4c90b`
- Quant commit（完整）：`bc4c90b9b185a23286db67ebd6dc2e15a02e4a0d`
- message：`v11: Step49 add C ablation switch (C_off/C_on) and record in manifest`

---

## 2) 落地摘要（用户验收事实）

修改文件：
- `prometheus/v11/core/features_contract.py`
  - contract version：`V11_FEATURE_PROBE_CONTRACT_20251230.2`
  - 新增 `CFeatureMode = Literal["C_off", "C_on"]`
  - `encode_features(..., c_feature_mode=...)`：
    - `C_off`：强制 `C_prev_net_intent` mask=0，value=0.0，reason_code=`c_feature_off`（维度保持不变）
    - `C_on`：遵循 Step 48 规则
  - `get_contract_info(c_feature_mode=...)`：证据化输出 `c_off_policy/c_on_policy/c_probe_definition`

新增验收脚本：
- `tools/verify_step49_c_ablation.py`：验证 Contract Info、C_on、C_off、维度保持

关键硬约束（实现侧）：
- 固定维度不变（C_off/C_on 均为 13 维，C probe index 不变）
- C_off 只通过 mask 关闭信息作用（不删维度）


