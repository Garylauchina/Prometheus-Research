# V11 Step 35 — paging_traces Required in Gates (Implemented in Quant) — 2025-12-29

目的：记录 Step 35（把 `paging_traces.jsonl` 纳入 verifier / run-end gate / CI gate 的硬要求）已在实现仓库（Prometheus-Quant）落地，并冻结其“对外可审计口径”。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v10/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`3366070`
- message：`v11: enforce paging_traces presence in evidence gates (P3/P4 closure proof)`

主要改动（实现仓库摘要）：
- `tools/verify_step26_evidence.py`：
  - 新增 `verify_paging_traces` 检查（P3/P4 closure proof 必备）
- fixture：`tests/fixtures/step26_min_run_dir/`
  - 新增：`paging_traces.jsonl`、`auditor_report.json`、`auditor_discrepancies.jsonl`
  - 更新：`FILELIST.ls.txt` / `SHA256SUMS.txt` 覆盖新增文件

---

## 2) 冻结的关键口径（与 Step 35 Spec 一致）

- 当 run 启用/声称 P3/P4（fills/bills）可测时：
  - 缺少 `paging_traces.jsonl` → gate 不得通过（fail-closed）
  - `paging_traces.jsonl` 必须纳入 `FILELIST/SHA256SUMS`（避免证据盲区）


