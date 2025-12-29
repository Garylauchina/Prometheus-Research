# V11 Step 44 — Evidence Refs Dereference Validation (Semantic Self-Consistency) — 2025-12-29

目的：在 Step 41-43（file/hash/line 覆盖）基础上，补上“语义自洽”的最后一段：  
让 verifier 在 gate-on 时能 **按 evidence_refs 解引用到具体 JSON 行**，并校验 run_id / audit_scope_id 等关键 join 锚点一致，防止“形式正确但指向无关行”的投机。

前置 SSOT：
- Step 41：`docs/v10/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`
- Step 42：`docs/v10/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`
- Step 43：`docs/v10/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`

---

## 1) verifier 行为（冻结，gate-on 时）

当 gate-on（同 Step 42）且存在 `evidence_ref_index.json`（Step 43）时：
- verifier 必须对审计链关键产物中的 `evidence_refs[]` 做 **dereference 校验**

覆盖文件（最小）：
- `auditor_report.json`
- `auditor_discrepancies.jsonl`
- 审计/证据链相关的 `errors.jsonl`

---

## 2) 解引用规则（jsonl）

对每个 ref，若 `ref.file` 以 `.jsonl` 结尾：
- 读取 `line_start..line_end` 的每一行（小范围读取；禁止扫描全文件）
- 每行必须是合法 JSON（parse 必须成功）

对每个被引用 JSON 对象（若字段存在则强制一致）：
- `run_id` 必须 == 当前 run 的 `run_id`
- 若 `ref.audit_scope_id` 非空：
  - 被引用对象的 `audit_scope_id` 必须存在且 == `ref.audit_scope_id`

可选增强（如果实现侧已有这些字段）：
- 若被引用对象含 `evidence_file` / `evidence_line`：
  - `evidence_file` 必须与 `ref.file` 一致
  - `evidence_line` 必须落在 `[line_start, line_end]` 内或与某行一致（实现侧可选择“等于某行号”的严格模式）

任何不满足 → **FAIL（exit 1，fail-closed）**

---

## 3) 解引用规则（json）

若 `ref.file` 以 `.json` 结尾：
- 允许 `line_start/line_end` 为 null（整文件语义）
- 不强制做行级解引用
- 但仍必须满足 Step 42/43 的 hash/index 覆盖规则

---

## 4) 最小验收（CI fixture）

fixture 必须新增一个“投机负例”（必须 FAIL）：
- 保持 `file`/`sha256_16`/`line_range` 都合法（不触发 Step 42/43 的形式校验）
- 但让被引用行的 JSON 内容在语义上不一致，例如：
  - `run_id` 不匹配
  - 或 `audit_scope_id` 不匹配/缺失（ref.audit_scope_id 非空时）

verifier 必须在 Step 44 的 dereference 校验中抓到并 FAIL。


