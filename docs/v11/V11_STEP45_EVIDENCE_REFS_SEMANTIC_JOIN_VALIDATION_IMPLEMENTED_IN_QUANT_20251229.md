# V11 Step 45 — Semantic-Join Validation Implemented in Quant — 2025-12-29

目的：记录 Step 45（evidence_refs 语义 join 校验：scope_id/query_chain_id/endpoint_family + audit_scope 元数据一致性）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点与最小验收（含投机负例）。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit（短）：`ef272c6`
- Quant commit（完整）：`ef272c6c72cbbe101389780225c86e839e79b980`
- message：`v11: Step45 enforce semantic-join validation for evidence_refs (scope/query_chain/endpoint_family)`

---

## 2) 落地摘要（用户验收事实）

核心验证器：
- `tools/verify_step26_evidence.py`：新增 Step 45 语义 join 校验逻辑（在 Step 44 dereference 基础上）

PASS fixture 更新：
- `tests/fixtures/step26_min_run_dir/`：调整 `auditor_report.json` 的 `evidence_refs` 只引用单一 endpoint 的单一行范围；并同步更新 `SHA256SUMS.txt` 与 `evidence_ref_index.json`

新增投机负例 fixtures（都必须 FAIL）：
- `tests/fixtures/step45_fail_mixed_query_chain/`：mixed `query_chain_id`（含 `README_STEP45_FAIL_A.md`）
- `tests/fixtures/step45_fail_mixed_endpoint/`：mixed `endpoint_family`（同时也触发 mixed `query_chain_id`，fail-fast 于 query_chain）（含 `README_STEP45_FAIL_B.md`）

CI 结果：
- PASS fixture：通过
- FAIL fixtures：按预期 FAIL（fail-fast）


