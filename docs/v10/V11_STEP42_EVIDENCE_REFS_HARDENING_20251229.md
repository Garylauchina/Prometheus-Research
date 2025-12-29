# V11 Step 42 — Evidence Refs Hardening (Hash/Line Mandatory) — 2025-12-29

目的：在 Step 41（evidence_refs 协议）基础上，把“可追踪”升级为**不可投机**：
- 只要 run 启用了 evidence packaging gate（产出 `FILELIST.ls.txt` + `SHA256SUMS.txt`），则所有审计链引用必须被 hash 覆盖
- 对 `*.jsonl` 引用必须给出行号范围（line_start/line_end），保证“一键定位”可机器复核

SSOT 依赖：
- Step 41 Spec：`docs/v10/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`

---

## 1) 强约束规则（冻结）

### 1.1 Hash 强制（gate-on 时）

前置条件（gate-on 的判定）：
- run_dir 内存在 `SHA256SUMS.txt`
- 且 `run_manifest.evidence_gate.status` 明确为启用/执行过（实现侧具体字段由 Quant 维持，但 verifier 必须能判定 gate-on）

规则：
- 任何出现在以下文件中的 `evidence_refs[]`，其每个 ref 的 `sha256_16` **必须非空**
  - `auditor_report.json`
  - `auditor_discrepancies.jsonl`
  - 审计/证据链相关的 `errors.jsonl`（例如 verifier fail / paging proof missing / mismatch）
- verifier 必须能从 `SHA256SUMS.txt` 复算 `file` 的 sha256，并比对前 16 hex == `sha256_16`
- 不满足 → **FAIL（exit 1，fail-closed）**

### 1.2 Line Range 强制（jsonl）

对 `file` 以 `.jsonl` 结尾的 ref：
- `line_start` 与 `line_end` **必须非空**
- 且 `1 <= line_start <= line_end`
- verifier 必须校验行号不超过文件实际行数（至少校验 `line_start` 合法；建议校验 `line_end` 合法）
- 不满足 → **FAIL**

对 `.json` 的 ref：
- `line_start/line_end` 允许为 null（语义通常为“整文件引用”）
- 但在 gate-on 时 `sha256_16` 仍必须存在且可复算匹配

### 1.3 FILELIST 覆盖强制

任何 ref 的 `file`：
- 必须存在
- 必须在 `FILELIST.ls.txt` 中出现
- 不满足 → **FAIL**

### 1.4 audit_scope_id 强制（审计域内）

若该 evidence ref 属于某个审计 scope（auditor_* 产物 / paging_traces / discrepancies 相关）：
- `audit_scope_id` 必须非空
- 且必须与 `run_manifest.audit_scopes[]` 中某一项一致（join key）
- 不满足 → **FAIL**

---

## 2) 工程实现建议（Quant 侧约束，不是 Research 代码）

为避免各模块手写导致不一致，建议在 Quant 提供统一构造器：

`make_evidence_ref(file, line_start, line_end, audit_scope_id, sha256sums_path) -> dict`

要求：
- 统一处理 `sha256_16` 计算（读取 `SHA256SUMS.txt` 或直接 hash 文件，再裁剪 16）
- 统一处理 `.jsonl` 行号非空校验
- 统一处理相对路径规范（run_dir 相对路径）

---

## 3) 验收口径（最小）

- gate-on 的 fixture：必须覆盖 auditor_report / discrepancies / paging_traces 的至少一个引用
- verifier 必须能：
  - 找到 file
  - 在 FILELIST 找到 file
  - 从 SHA256SUMS 复算匹配 sha256_16
  - 校验 jsonl 行号范围合法
- 任一不满足 → FAIL（CI fail / run-end gate fail）


