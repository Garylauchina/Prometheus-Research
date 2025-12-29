# V11 Step 43 — evidence_ref_index Implemented in Quant — 2025-12-29

目的：记录 Step 43（新增 `evidence_ref_index.json`，把 hash/行号复算成本从 verifier 挪到 run-end gate）已在实现仓库（Prometheus-Quant）落地，并冻结实现锚点与 hard 口径。

SSOT 规格：
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`

---

## 1) 实现锚点（Quant）

Prometheus-Quant 已完成并推送：
- Quant commit：`64c5867`
- message：`v11: Step43 add evidence_ref_index for fast hash/line validation`

---

## 2) 落地口径（应与 Step 43 Spec 一致）

- run-end gate 生成 `evidence_ref_index.json`（在 `FILELIST.ls.txt` 与 `SHA256SUMS.txt` 之后）
- index entries 提供：
  - `rel_path`
  - `sha256_16`
  - `byte_size`
  - `line_count`（对 `.jsonl` 必填）
- verifier gate-on 时：
  - 必须存在 `evidence_ref_index.json`
  - `evidence_refs` 的 `file/sha256_16` 必须能在 index 中匹配
  - `.jsonl` 的 `line_end` 必须 `<= line_count`
  - 不满足 → fail-closed


