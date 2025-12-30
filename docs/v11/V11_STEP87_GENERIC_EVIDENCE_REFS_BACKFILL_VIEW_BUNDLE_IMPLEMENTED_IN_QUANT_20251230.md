# V11 Step 87 — Generic EvidenceRefs Backfill View Bundle — Implemented in Quant — 2025-12-30

本文件是 Step87 在 **Prometheus-Quant** 的落地记录（不可变记录）。  
SSOT（规格）：`docs/v11/V11_STEP87_GENERIC_EVIDENCE_REFS_BACKFILL_VIEW_BUNDLE_20251230.md`

---

## 1) Quant Commit Anchor

（per user report）
- Quant commit (short): `b4f407c`
  - message: Step87 generic evidence refs bundle (audit artifacts coverage, CI gate)

---

## 2) Covered Audit Artifacts (Quant)

（per user report）本次 Step87 将通用证据链机制推广覆盖到审计关键证据文件，包括：
- `paging_traces.jsonl`
- `auditor_report.json`
- `auditor_discrepancies.jsonl`（或 `discrepancies.jsonl`，以 Quant 实际路径为准）

并复用/继承 Step81-86 机制：
- backfill view（Step86）
- sha256_16 ↔ evidence_ref_index（Step83）
- dereference（Step82）
- range 同质性（Step84）

---

## 3) Key Rules (Quant)

（per user report）Step87 新增/强化的核心同质性规则（paging_traces range）：
- range 内必须满足：
  - `run_id` 一致
  - `scope_id` 一致
  - `query_chain_id` 一致
  - `endpoint_family` 一致

并在 CI 中 fail-closed（CRITICAL SECURITY ISSUE）。


