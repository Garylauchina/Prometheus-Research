# V11 Step 46 — Evidence Gate Bundle Freeze (SSOT Contract + Fixtures + Exit Codes) — 2025-12-29

目的：把 Step 41–45 的 evidence_refs 证据链门禁收口成一个**可版本化的 bundle**，形成不可漂移的“最终闸门”，避免后续增量改动导致：
- verifier 口径漂移（今天能过、明天过不了）
- fixture 被悄悄改语义（回归测试失真）
- exit code 语义不一致（CI / run-end gate 行为不可控）

前置 SSOT：
- Step 41–45（evidence_refs 标准/强约束/index/dereference/semantic-join）

---

## 1) Bundle Contract（冻结）

Bundle 名称（建议）：
- `V11_EVIDENCE_GATE_BUNDLE_20251229`

Bundle 版本号（必须写入产物）：
- `bundle_version`: `2025-12-29.1`

verifier 在 PASS/FAIL 输出中必须打印并写入（machine-readable）：
- `bundle_name`
- `bundle_version`
- `bundle_steps_included`: `[41,42,43,44,45]`

run-end gate / run_manifest 必须记录：
- `evidence_gate.bundle_name`
- `evidence_gate.bundle_version`
- `evidence_gate.verifier_commit_sha`（Quant 提交锚点）

---

## 2) 必需产物清单（冻结）

当 gate-on 时（存在 FILELIST/SHA256 且 evidence_gate 执行）：

必须存在并被 SHA256 覆盖：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`（Step 43）

审计链关键产物（若该 run 执行了审计模块）：
- `auditor_report.json`
- `auditor_discrepancies.jsonl`
- `paging_traces.jsonl`

基础 join 锚点产物：
- `run_manifest.json`
- `errors.jsonl`（允许为空文件，但若存在 audit 相关 error 必须有 evidence_refs）

---

## 3) Exit Code 语义（冻结）

verifier：
- PASS → exit `0`
- FAIL（任何 bundle 规则不满足）→ exit `1`

run-end evidence gate（runner 退出前的 packaging+verify）：
- PASS → exit `0`
- FAIL → exit `2`（保持既有约定；若实现侧已有固定值，以实现侧为准，但必须在文档里冻结并一致）

注：verifier 的 exit code 与 run-end gate 的 exit code 可以不同，但必须在 manifest 与文档里明确记录。

---

## 4) Fixture 套件冻结（CI 不可绕过）

必须保留的 fixtures（冻结语义、禁止删除、禁止改“预期”）：

### 4.1 PASS fixture（必须长期存在）
- `tests/fixtures/step26_min_run_dir/` → 预期 PASS

### 4.2 FAIL fixtures（投机负例，必须长期存在）
- Step 44：run_id mismatch → 预期 FAIL
- Step 45：mixed query_chain_id → 预期 FAIL
- Step 45：mixed endpoint_family（可 fail-fast 于 query_chain，但仍必须保持“该负例代表 endpoint 混用”）→ 预期 FAIL

规则：
- 任何对上述 fixture 的修改必须是“additive-only”（例如补 README 说明/补字段但不改变 FAIL 原因）
- 新增更多 fixtures 允许，但不得替代上述最小套件

---

## 5) 最小验收（Quant 落地必须达成）

- verifier 输出包含 bundle_name/bundle_version/steps_included
- run_manifest.evidence_gate 记录 bundle_name/bundle_version/verifier_commit_sha
- CI 同时跑 PASS + 三个 FAIL fixtures，且结果固定不变


