# V11 Step 85 — Runtime EvidenceRefs Auto-Generation + sha256_16 Backfill — SSOT — 2025-12-30

目的：把 Step82/83/84 的 EvidenceRefs 验证从“demo/fixture/手工拼装”提升为 **真实运行产物自动满足**：运行时自动生成 `evidence_refs`（含行号/范围），并在 run-end gate 基于 `evidence_ref_index.json` 回填 `sha256_16`，实现可审计且可验真的引用闭环。

本文件只允许追加（additive-only）。

前置：
- Step 43：`evidence_ref_index.json`
- Step 46：Evidence Gate Bundle Freeze（EvidenceRefs hardening + dereference）
- Step 82/83/84：freeze evidence refs dereference + sha256 alignment + range validation

---

## 1) 关键约束（冻结）

- **运行时写入阶段**不能可靠知道最终 `sha256_16`（因为文件还会继续 append）。
- 因此 Step85 采用两阶段：
  1) **运行时生成 line_range**（file/line_start/line_end）
  2) **run-end gate 回填 sha256_16**（从 `evidence_ref_index.json` 读取）

fail-closed（冻结）：
- Evidence gate enabled 时，如果回填后仍存在缺失/不一致，run-end gate 必须失败（exit 2/FAIL），并写入 errors。

---

## 2) Runtime 侧：EvidenceRef 占位生成（Phase 1）

运行时写入任意 `.jsonl` 记录时，写入工具必须返回（或可查询）该次 append 的 **行号范围**：
- `file`（相对 run_dir）
- `line_start`
- `line_end`

规则（冻结）：
- 单条写入：`line_start == line_end`
- 批量写入（若支持）：`line_end >= line_start`，且范围连续

写入工具推荐形态（示例）：
- `append_jsonl(path, record) -> (line_no: int)`
- `append_jsonl_many(path, records) -> (line_start: int, line_end: int)`

生成的 `evidence_refs`（Phase 1）允许 **暂不包含** `sha256_16`，但必须包含：
- `file`
- `line_start`
- `line_end`
- `audit_scope_id`（若启用；否则可省略）

---

## 3) Run-end gate：sha256_16 回填（Phase 2）

run-end gate 已生成 `evidence_ref_index.json` 后，执行回填：

对所有 evidence 文件中出现的 `evidence_refs`：
- 读取 `evidence_ref_index.json`，建立 `rel_path -> sha256_16` 映射
- 对每个 evidence_ref：
  - 若缺少 `sha256_16`：回填
  - 若存在 `sha256_16`：必须匹配 index，否则 FAIL

重要：回填是 **就地写回** 对应 json/jsonl 记录（append-only 约束下的处理方式必须被冻结）：
- 推荐策略 A（append-only）：写入一个补丁文件（例如 `evidence_refs_backfill.jsonl`）记录“哪个文件的哪一行 evidence_ref 被回填为何值”，并在 verifier 中把“补丁应用视图”作为审计视图。
- 推荐策略 B（允许重写）：若允许对某些派生/summary 文件重写，则必须明确哪些文件允许重写，哪些文件 append-only。

Step85 选择必须在 Quant 落地时冻结其策略并记录在 manifest/gate 输出中。

---

## 4) Verifier 新规则（Step85）

当 evidence gate enabled 时：
- 若某些 `evidence_refs.sha256_16` 缺失 → FAIL
- 若 `sha256_16` 与 index 不一致 → FAIL
- 继续保留 Step82/84 的 dereference + range 语义校验

---

## 5) 最小验收（硬）

必须证明：
- 真实运行（非 demo 脚本）生成的冻结 trigger/reject 记录具备 evidence_refs（至少 file+line_range）
- run-end gate 回填后，evidence_refs 的 sha256_16 完整且与 index 一致
- 构造一个缺失或不一致场景，run-end gate fail-closed


