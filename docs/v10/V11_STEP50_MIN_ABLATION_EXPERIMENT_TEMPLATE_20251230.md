# V11 Step 50 — Minimal Ablation Experiment Template (C_off vs C_on) — 2025-12-30

目的：把 `C_off` vs `C_on` 的对照实验从“口头约定”升级为 **可复制、可复核、机器可读** 的实验模板，避免：
- 运行参数漂移（seed/ticks/agents/truth_profile 不一致）
- 口径漂移（feature_contract/bundle_version 不一致）
- 证据不可复核（manifest 缺少实验配置）

前置：
- Step 46：Evidence Gate Bundle（必须记录 bundle_name/bundle_version/steps_included）
- Step 48：I/C probes 注入
- Step 49：`c_feature_mode`（C_off/C_on）

---

## 1) 实验模板（冻结字段集合）

定义 `ablation_experiment`（写入 `run_manifest.json`）为 machine-readable：

必含字段（最小）：
- `experiment_name`: string（例如 `C_ablation_prev_net_intent`）
- `variant`: `"C_off"` | `"C_on"`（与 c_feature_mode 一致）
- `seed`: int
- `tick_count`: int
- `agent_count`: int
- `truth_profile`: string（SSOT 词表：degraded_truth/full_truth_pnl）
- `mode`: string（stub/okx_demo_api/okx_live_api）
- `feature_contract_version`: string
- `evidence_gate_bundle_name`: string
- `evidence_gate_bundle_version`: string
- `evidence_gate_bundle_steps_included`: list[int]

建议字段（强烈建议，但允许缺省）：
- `inst_id`: string
- `tick_seconds`: int
- `notes`: string

硬规则：
- 对照实验中，除 `variant` 外，其他必含字段必须一致（否则“不是同一次对照实验”）
- `variant` 必须与 `c_feature_mode` 一致

---

## 2) 最小验收（Quant 落地必须达成）

必须提供一个脚本/CI 断言：
- 生成两份 run_manifest（或同一 run 里两次 run 目录）
  - A：`variant="C_off"`
  - B：`variant="C_on"`
- 断言：
  - A/B 的 `seed/tick_count/agent_count/truth_profile/mode/feature_contract_version/bundle_*` 完全一致
  - 只有 `variant` 不同（且与 c_feature_mode 一致）

失败语义：
- 任一字段不一致 → FAIL（用于 CI / run-end gate 前置校验）


