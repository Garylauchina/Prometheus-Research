# V11 Step 72 — Agent Metabolism Observability — Implemented in Quant — 2025-12-30

目的：记录 Step72 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_20251230.md`
- `docs/v11/V11_STEP72_1_AGENT_METABOLISM_CANDIDATES_AND_FILTER_20251230.md`
- `docs/v11/V11_STEP72_2_AGENT_METABOLISM_PREIMPLEMENTATION_CHECKLIST_AND_LIFESPAN_VIEWS_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step72 agent metabolism observability (fact-only, non-genetic)`
- **Commit (short)**: `3881893`
- **Commit (full)**: `3881893a4dfa918f3604f1f5da09c670bcfdaa56`

修改文件（Quant）：
- `tools/generate_agent_metabolism_summary.py`
- `prometheus/v11/ops/run_v11_service.py`

---

## 2) 产物与集成（事实）

新增产物（事实）：
- `research_bundle/agent_metabolism_summary.json`

集成点（事实）：
- run-end 阶段生成 summary，并自动纳入：
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`
  - `evidence_ref_index.json`
- 被 Step67 `research_bundle/entry.json` 索引（artifact kind：`agent_metabolism_summary_json`，包含 `sha256_16`/`byte_size`）。
- `run_manifest.json` 写实记录 `agent_metabolism` 状态。

---

## 3) 可测性（事实）

- `M_intent`: **MEASURABLE**（来源：`decision_trace.jsonl`）
- `M_resource_cpu_time`: **NOT_MEASURABLE**（reason: `instrumentation_not_implemented`）
- `M_resource_api`: **NOT_MEASURABLE**（reason: `paging_traces_not_found`；world-level/agent-level 均为 null）

写实规则（事实）：
- 不可测字段以 `null + measurement_status=NOT_MEASURABLE + reason_codes[]` 表达；
- 不用 0 伪装 unknown。


