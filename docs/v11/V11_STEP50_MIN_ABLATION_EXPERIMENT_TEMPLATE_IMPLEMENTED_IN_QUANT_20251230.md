# V11 Step 50 — Minimal Ablation Experiment Template Implemented in Quant — 2025-12-30

目的：记录 Step 50（C_off vs C_on 最小对照实验模板：`run_manifest.ablation_experiment`）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点（含 SHA）与最小验收事实。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP50_MIN_ABLATION_EXPERIMENT_TEMPLATE_20251230.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`d2555b8`
- Quant commit（完整）：`d2555b8db94b09c40a30e008c4e628b5cc766dd6`
- message：`v11: Step50 record ablation_experiment template in run_manifest (C_off vs C_on)`

---

## 2) 落地摘要（用户验收事实）

修改文件：
- `prometheus/v11/ops/run_v11_service.py`
  - 新增 CLI 参数：`--c-feature-mode` / `--seed` / `--agent-count` / `--truth-profile`
  - `run_manifest.json` 写入 `ablation_experiment`（必含 11 字段 + 可选字段）
  - 记录 evidence gate bundle 信息（Step 46）

新增验收脚本：
- `tools/verify_step50_ablation_template.py`
  - 验证：ablation_experiment 存在性、variant==c_feature_mode、一致性（除 variant 外字段完全一致）、bundle 记录


