# V11 Step 57 — Step51 Minimal Fixtures Contract (for CI) — SSOT — 2025-12-30

目的：冻结 Quant CI 中用于 Step56 gate 的 Step51 最小 fixtures 口径，避免 fixture 随实现细节漂移，导致 CI gate “看似通过但不可复核/不可比”。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并同步更新 CI fixtures 与验收。

前置：
- Step 51：`docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_20251230.md`
- Step 53：`docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`
- Step 54：`docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`
- Step 56：`docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_20251230.md`

---

## 1) 适用范围（冻结）

本 contract 仅约束 **CI fixtures**（用于 Step56 gate），不约束生产 run_dir。

目标 fixtures：
- `tests/fixtures/step51_C_off_minimal/`
- `tests/fixtures/step51_C_on_minimal/`

---

## 2) 目录结构（冻结，最小）

每个 fixture 目录必须包含以下文件（最小集合）：

- `run_manifest.json`
- `decision_trace.jsonl`
- `ablation_summary.json`
- `SHA256SUMS.txt`
- `README.md`

禁止：
- 额外塞入大量无关文件作为“凑数”（例如完整 run_dir 全量复制），除非另立 SSOT 并说明必要性。

---

## 3) 字段最小要求（硬）

### 3.1 run_manifest.json（最小）

必须包含（用于可比性检查的控制变量法）：
- `run_id`
- `ablation_experiment` object，且至少包含：
  - `experiment_name`
  - `variant`（C_off / C_on）
  - `seed`
  - `tick_count`
  - `agent_count`
  - `truth_profile`
  - `mode`
  - `feature_contract_version`
  - `evidence_gate_bundle`（或等价三件套字段：bundle_name/bundle_version/steps_included）

### 3.2 decision_trace.jsonl（最小）

必须能支持 Step53/54 对 C_probe 的统计输入（t-1 intent 统计）：
- 需要包含 agent 级别 intent 记录（open/close/hold）
- 行数必须满足 fixture 声称的 tick_count × agent_count（或明确写实缺口原因并由脚本显式处理）

### 3.3 ablation_summary.json（最小）

必须符合 Step51 SSOT 的 schema 最小要求，并能被 Step53 compare 读取：
- `run_id`
- `ablation_experiment`（与 manifest 控制变量一致）
- `feature_contract_version`
- `evidence_gate_bundle`（或等价信息）
- `tick_range`
- `decision_intent_counts_total`
- `c_probe_stats`
- `evidence_refs`（至少回指 manifest 与 decision_trace 的可复核锚点）

### 3.4 SHA256SUMS.txt（最小）

必须至少覆盖：
- `run_manifest.json`
- `decision_trace.jsonl`
- `ablation_summary.json`

### 3.5 README.md（最小）

必须写实说明：
- 该 fixture 的用途：Step56 CI gate 输入（C_off/C_on）
- 该 fixture 的来源方式（如何从真实 run_dir 抽取最小集合）
- 该 fixture 的关键控制变量（seed/ticks/agents/truth_profile/mode）

---

## 4) 可比性与差异规则（硬）

两个 fixtures（C_off vs C_on）必须满足：
- 除 `variant` 外，`ablation_experiment` 控制变量字段完全一致
- `feature_contract_version` 一致
- `evidence_gate_bundle` 三件套一致

允许的差异：
- `variant`
- C_probe 的 mask 行为（C_off mask=0；C_on mask=1 的行数>0）

---

## 5) 最小验收（CI gate 必须可机械复核）

Quant CI 的 Step56 gate 应至少验证：
- fixtures 可被 `tools/test_step54_integration.py` 定位
- Step53 compare 能从两份 fixture 生成 `ablation_compare.json`
- Step53 verifier PASS
- evidence packaging 递归包含 `step53_compare/ablation_compare.json`

---

## 6) 变更纪律（冻结）

对 fixtures 的任何变更必须：
- 同步更新本 contract（additive-only 或 bump）
- 在 Quant 侧提交中写明原因（防“悄悄换样本”）
- 若涉及字段/语义变化，必须重跑并更新 Step56 gate 的验收输出说明


