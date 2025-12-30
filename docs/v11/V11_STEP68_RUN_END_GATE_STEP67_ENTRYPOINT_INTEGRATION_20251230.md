# V11 Step 68 — Run-End Gate: Step67 Entrypoint Integration (Quant) — SSOT — 2025-12-30

目的：把 Step67 的 `research_bundle/entry.json` 从“规范”升级为 **run-end gate 可验证产物**：生成→校验→纳入 evidence package→写实 manifest。启用时 fail-closed，防止入口漂移或断链。

本文件只允许追加（additive-only）。

前置：
- Step65：`research_bundle/` 输出（fact-only）
- Step67：`research_bundle/entry.json` contract
- Step28/46：evidence packaging + evidence gate bundle（`FILELIST/SHA256SUMS/evidence_ref_index`）

---

## 1) Gate 开关（冻结）

Quant runner/run-end gate 新增开关（名称冻结）：
- `--enable-step68-entrypoint`（默认建议 true；若默认 false 必须写实记录）

说明：
- Step68 控制“是否把 entrypoint 作为 gate 产物并校验、失败则 fail-closed”。
- Step67 仍定义 entry 的 schema；Step68 定义 runner/gate 行为与失败语义。

---

## 2) 执行顺序（冻结）

当 `--enable-step68-entrypoint` 生效时，run-end gate 阶段顺序必须固定为：

1) 生成 research_bundle（Step65 已有；若未启用或未生成，必须写实）
2) 生成 `research_bundle/entry.json`（Step67）
3) 生成 evidence package：`FILELIST.ls.txt` / `SHA256SUMS.txt` / `evidence_ref_index.json`
4) 校验 entry.json（至少做 Step67 的一致性校验；可复用 verifier 或内置校验）
5) 写实更新 `run_manifest.json`
6) 运行既有 evidence gate bundle（若存在）

关键约束（冻结）：
- entry.json 必须在 evidence packaging 之后校验（因为要与 `evidence_ref_index.json` 对齐）。
- entry.json 必须在 run-end gate 完成前写盘（append-only 证据链的一部分）。

---

## 3) 最小校验集（硬）

当 enabled=true：
- `research_bundle/entry.json` 文件存在
- `contract_version` 精确匹配 Step67
- `bundle_dir == "research_bundle"`
- `evidence_package.evidence_ref_index_rel_path == "evidence_ref_index.json"`（相对 run_dir）
- `artifacts[]` 中每个 `rel_path` 必须存在文件
- `artifacts[].sha256_16/byte_size` 必须与 `evidence_ref_index.json` 中对应 `rel_path` 的值一致
- `research_bundle_entrypoint` manifest 对象存在且写实（见下一节）

---

## 4) Manifest 记录（additive-only，冻结）

在 `run_manifest.json` 必须写入：
- `research_bundle_entrypoint.enabled`（bool）
- `research_bundle_entrypoint.entry_rel_path`（默认 `research_bundle/entry.json`）
- `research_bundle_entrypoint.contract_version`（Step67 contract version）
- `research_bundle_entrypoint.artifact_count`（int）
- `research_bundle_entrypoint.status`（`pass|fail|skipped`）

---

## 5) 失败语义（冻结）

当 `enabled=true`：
- 任何 Step68 最小校验失败 → **FAIL（exit 2, fail-closed）**
- 必须写入 `errors.jsonl`（reason_code 至少包含 `step68_entrypoint_failed`）
- manifest 必须写实 `status="fail"`

当 `enabled=false`：
- entry.json 可不生成，manifest `status="skipped"`；不得伪造 entry.json。

---

## 6) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + gate 输出片段 + 样例 entry.json）


