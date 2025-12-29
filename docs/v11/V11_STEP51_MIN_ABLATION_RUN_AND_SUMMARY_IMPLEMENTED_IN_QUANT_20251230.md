# V11 Step 51 — Minimal Ablation Run + Summary Implemented in Quant — 2025-12-30

目的：记录 Step 51（最小对照实验跑通 + 生成 `ablation_summary.json`）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点（含 SHA）与验收事实（含两次 run 产物）。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_20251230.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`34a1b91`
- Quant commit（完整）：`34a1b91791febb0c65cdabb8a779e759defe31b5`
- message：`v11: Step51 generate ablation_summary.json for C_off/C_on runs`

---

## 2) 落地摘要（用户验收事实）

修改/新增：
- `prometheus/v11/ops/run_v11_service.py`：新增 `generate_ablation_summary()`，生成 `ablation_summary.json`（事实统计 + evidence_refs）
- `tools/run_step51_minimal_ablation.py`：最小对照实验运行脚本（生成 manifest/trace/SHA256/summary）
- `tools/verify_step51_ablation_summary.py`：验收脚本（6 项校验：存在性/必填字段/可比性/C stats/evidence_refs/bundle 规则）
- `runs_step51/`：两次对照实验完整输出（C_off/C_on）

对照 run（事实）：
- C_off：`runs_step51/step51_C_off_20251229_172513/`
- C_on：`runs_step51/step51_C_on_20251229_172518/`

关键断言（事实）：
- C_off：`c_prev_net_intent_mask_1_count == 0`
- C_on：`c_prev_net_intent_mask_1_count == 4950`（tick=2..100, 50 agents/tick）
- 两份 summary 的 `ablation_experiment` 除 `variant` 外完全一致（Step 50）
- summary 的 `evidence_refs` 回指 `run_manifest.json` 与 `decision_trace.jsonl`，并满足 Step 46 bundle 复核要求


