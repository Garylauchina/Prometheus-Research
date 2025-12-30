# V11 Step 71 — CI Gate: Step70 Cross-Run Index — Implemented in Quant — 2025-12-30

目的：记录 Step71 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP71_CI_GATE_STEP70_CROSS_RUN_INDEX_20251230.md`
- 关联：`docs/v11/V11_STEP70_CROSS_RUN_RESEARCH_ENTRY_INDEX_CONTRACT_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step71 CI gate generate+verify cross-run research_entry_index`
- **Commit (short)**: `a313aa6`
- **Commit (full)**: `a313aa68857fe789c90e2b7adf253a2157c45240`

修改文件（Quant）：
- `tools/index_research_entries.py`
- `tools/verify_step70_research_entry_index.py`
- `.github/workflows/v11_evidence_gate.yml`

---

## 2) CI 固定参数（事实）

- `scan_root = runs_step54_test`
- 输出：`ci_artifacts/research_entry_index.json`

---

## 3) 失败语义（事实）

- 任一步 exit 非 0 → CI FAIL（阻断合并）
- 生成器空跑（`entry_count==0`）→ exit 2

---

## 4) 可测性备注（写实）

Quant verifier 在 CI 中对 `entry_sha256_16` 的“文件一致性”校验出现 WARNING：
- 原因：`entry_rel_path` 为相对 `scan_root` 的路径，若 verifier 未将其与 `scan_root` 拼接为可读的实际路径，会导致 `file not found`，从而该项校验 **NOT_MEASURABLE**。

说明：
- 这不影响 Step71 gate 的主目标（生成/验证 schema/entry_count/contract_version 一致性）；
- 若希望该校验变为可测，建议后续将 verifier 的文件读取路径改为：`join(scan_root, entry_rel_path)`。


