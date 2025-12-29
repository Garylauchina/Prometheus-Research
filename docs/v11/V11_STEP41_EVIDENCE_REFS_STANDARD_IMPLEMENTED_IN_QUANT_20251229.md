# V11 Step 41 — evidence_refs Standard Implemented in Quant — 2025-12-29

目的：记录 Step 41（审计链 `evidence_refs` 统一协议 + verifier hash/line 覆盖校验）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点与 hard 口径。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`f8fe427`
- message：`v11: standardize evidence_refs across audit artifacts and verify hash/line coverage`

实现内容（用户验收摘要）：
- 统一 `evidence_refs` 协议：`file + line_range + sha256_16 + audit_scope_id`
- `auditor_report.json` 添加 `evidence_refs[]`（回指 paging_traces 与 discrepancies）
- `auditor_discrepancies.jsonl` 每条记录预留 `evidence_refs[]`
- verifier 校验：
  - 文件存在性
  - FILELIST 覆盖
  - sha256_16 匹配
  - 行号合法性
  - 违规 → FAIL（exit 1，fail-closed）
- CI fixture 更新并通过

---

## 2) 冻结的 hard 口径（与 Step 41 Spec 一致）

- `evidence_refs` 必须可回查且被 `SHA256SUMS.txt` 覆盖（避免证据盲区）
- 引用的 `line_start/line_end` 必须合法（1-based，start≤end）
- 引用必须携带 `audit_scope_id`（用于跨文件 join）


