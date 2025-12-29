# V11 Step 42 — Evidence Refs Hardening Implemented in Quant — 2025-12-29

目的：记录 Step 42（gate-on 时 evidence_refs 的 hash/行号强约束）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点与 hard 口径。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`461baa5`
- message：`v11: Step42 harden evidence_refs (hash+line mandatory when gate-on)`

实现摘要（以用户验收为准）：
- gate-on 时强制 `evidence_refs[].sha256_16` 非空且可从 `SHA256SUMS.txt` 复算匹配（fail-closed）
- 对 `.jsonl` 引用强制 `line_start/line_end` 非空并校验范围合法（fail-closed）
- 强制 FILELIST 覆盖（ref.file 必须在 `FILELIST.ls.txt`）
- 强制 `audit_scope_id` join 纪律（审计域内引用必须可 join 到 `run_manifest.audit_scopes[]`）

---

## 2) 冻结的 hard 口径（与 Step 42 Spec 一致）

- gate-on 不是“有就用”，而是“启用即强制”：缺 hash/缺行号（jsonl）→ FAIL
- `.json` 可允许 line_range 为 null，但 gate-on 时 hash 必须存在且可复算匹配
- 任何引用不得指向 FILELIST/SHA256 覆盖之外的文件（避免证据盲区）


