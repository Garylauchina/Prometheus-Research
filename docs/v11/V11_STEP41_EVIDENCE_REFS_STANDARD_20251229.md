# V11 Step 41 — Evidence Refs Standard (Machine-Traceable Audit Chain) — 2025-12-29

目的：把审计链的“回指证据”从文本描述升级为 **机器可追踪的引用协议**，实现：
- auditor_report/ discrepancy / error → 一键定位到对应证据文件行范围
- 引用可被 hash 覆盖（防篡改/防盲区）

背景：
我们已经建立了 paging_traces + paging_coverage + scope_id/query_chain_id + audit_scopes[]。  
现在缺的是统一的 **evidence_refs 协议**，否则复核仍需人工 grep。

---

## 1) evidence_refs 统一结构（冻结）

所有需要回指证据的记录（auditor_report / auditor_discrepancies / errors）统一使用：

`evidence_refs`: list[object]

每个 ref（最小字段集）：
- `file`: string（run_dir 相对路径，例如 `paging_traces.jsonl`）
- `line_start`: int|null（1-based；未知可为 null）
- `line_end`: int|null（1-based；若只引用 1 行则等于 line_start）
- `sha256_16`: string|null（文件 sha256 前 16 hex；若缺 hash 覆盖则必须为 null 并触发 FAIL/NOT_MEASURABLE）
- `audit_scope_id`: string|null（若该 ref 属于某次审计 scope，必须填）

硬规则：
- 若 `line_start` 非空，则 `line_end` 必须非空且 `line_start <= line_end`
- `file` 必须存在于 `FILELIST.ls.txt` 与 `SHA256SUMS.txt`（否则证据盲区）
- 若本 run 启用了 evidence packaging gate：`sha256_16` 必须可从 `SHA256SUMS.txt` 复算得到（否则 FAIL）

---

## 2) 必须携带 evidence_refs 的产物（冻结）

当 ExchangeAuditor 运行时：
- `auditor_report.json`：每个检查项（orphan / fills join / bills join / paging closure）都应附 `evidence_refs`
- `auditor_discrepancies.jsonl`：每条 discrepancy 必须附 `evidence_refs`（至少 1 个）
- `errors.jsonl`：与审计/证据链相关的错误（paging proof missing / verifier fail / mismatch）必须附 `evidence_refs`

---

## 3) verifier/gates 最小校验（fail-closed）

当检测到上述文件存在且包含 evidence_refs：
- 校验 `file` 存在
- 校验 `file` 在 FILELIST/SHA256 覆盖范围内
- 若有 line_range，则校验行号合法
- 校验 `sha256_16` 与 SHA256SUMS 一致（若 gate 已启用）

不满足 → FAIL（exit 1），用于 CI 与 run-end gate。


