# V11 Step 43 — Evidence Ref Index (Hash + LineCount Index for Verifier) — 2025-12-29

目的：把 Step 42 引入的“hash/行号强校验”的**复算成本**从 verifier 挪到 run-end gate，避免 verifier 反复读取大文件计算行数/哈希导致慢、且重复逻辑容易漂移。

前置 SSOT：
- Step 41：`docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`
- Step 42：`docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`

---

## 1) 新增产物（冻结）

在 run_dir 内新增：
- `evidence_ref_index.json`

该文件为“本次 run 的证据索引”，用于 verifier 快速校验引用的合法性与覆盖范围。

### 1.1 Schema（最小冻结字段）

顶层字段：
- `run_id`: string
- `generated_at_utc`: string（ISO 8601）
- `index_version`: string（例如 `2025-12-29.1`）
- `entries`: list[object]

每个 entry（最小字段集）：
- `rel_path`: string（run_dir 相对路径，例如 `paging_traces.jsonl`）
- `sha256_16`: string（sha256 前 16 hex，必须与 `SHA256SUMS.txt` 一致）
- `byte_size`: int（文件字节数）
- `line_count`: int|null
  - 若 `rel_path` 以 `.jsonl` 结尾：必须为非空 int
  - 其他文件类型：可为 null

---

## 2) 生成时机与 hard 规则（冻结）

### 2.1 生成时机

在 run-end evidence packaging gate 中：
- 已生成 `FILELIST.ls.txt` 与 `SHA256SUMS.txt` 之后
- 生成 `evidence_ref_index.json`

### 2.2 覆盖规则

`entries[]` 至少覆盖：
- `FILELIST.ls.txt` 中列出的所有证据文件（建议全覆盖）
- 其中对 `.jsonl` 必须填 `line_count`

不满足 → gate **FAIL（exit 2 或实现既定错误码）**

---

## 3) verifier 行为（冻结）

当 gate-on（见 Step 42）时，verifier 必须优先使用 `evidence_ref_index.json`：
- `evidence_refs[].file` 必须能在 `entries.rel_path` 中找到
- `evidence_refs[].sha256_16` 必须与 entry 的 `sha256_16` 相等
- 若 `file` 是 `.jsonl`：
  - `line_start/line_end` 必须非空（Step 42）
  - 且 `line_end <= entry.line_count`

若缺少 `evidence_ref_index.json` 或 index 不一致：
- 视为证据链不可复核 → **FAIL（exit 1，fail-closed）**

允许的实现优化：
- verifier 不再逐文件读取计算行数/哈希（以 index 为准）
- 仍可做“抽查式复算”（可选，非必需；但若做必须 fail-closed）

---

## 4) 最小验收（fixture）

CI fixture 必须包含：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`
- 至少一个 `.jsonl` 证据文件（例如 `paging_traces.jsonl`）以及引用它的 `evidence_refs`（带合法 line_range + sha256_16）

verifier 必须能通过 index 完成所有校验。


