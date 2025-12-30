# V11 Step 86 — Backfill View Verifier + Backfill Integrity (evidence_refs_backfill.jsonl) — SSOT — 2025-12-30

目的：把 Step85 的 append-only backfill 机制升级为 **强制验真视图**：verifier 在校验 freeze evidence 时必须自动应用 `evidence_refs_backfill.jsonl`（backfill view），并对 backfill 文件本身执行完整性/一致性规则，形成闭环的可审计、防篡改体系。

本文件只允许追加（additive-only）。

前置：
- Step 46：Evidence Gate Bundle Freeze（evidence_refs 结构 + dereference）
- Step 82/83/84：dereference + sha256 alignment + range validation
- Step 85：runtime autogen + append-only backfill（`evidence_refs_backfill.jsonl`）

---

## 1) Backfill View 的定义（冻结）

Backfill view = 原始证据文件（append-only） + backfill 补丁文件（append-only）共同定义的“审计视图”。

原则（冻结）：
- 不允许重写原始 jsonl 证据文件
- 任何 `sha256_16` 回填必须通过 `evidence_refs_backfill.jsonl` 记录
- verifier 必须以 backfill view 作为校验输入，而不是以“原始文件未回填状态”校验

---

## 2) Backfill 记录格式（冻结，最小）

`evidence_refs_backfill.jsonl` 每条记录最小字段（冻结）：
- `ts_utc`
- `run_id`
- `target_file`（相对 run_dir，例如 `order_attempts.jsonl`）
- `target_line`（1-based，指目标记录所在行）
- `ref_index`（int，指目标记录的 evidence_refs 数组索引）
- `sha256_16`（回填值）

可选字段（但建议）：
- `audit_scope_id`
- `reason_code`（例如 `backfill_sha256_16_from_ref_index`）

---

## 3) Backfill Integrity Rules（新增 verifier 规则）

### 3.1 基础一致性（冻结）
对每条 backfill 记录：
- `target_file` 必须存在且位于 evidence package 内
- `target_line` 必须在目标文件行数范围内
- `ref_index` 必须是非负整数
- `sha256_16` 必须是长度为 16 的十六进制字符串（小写/大写接受由实现冻结）

### 3.2 Index 对齐（冻结）
当 Evidence Gate enabled 时：
- `sha256_16` 必须等于 `evidence_ref_index.json` 中 `target_file` 的 `sha256_16`
  - 不匹配 → FAIL（防止 backfill 注入错误 hash）

### 3.3 单调性/幂等（冻结）
对同一个 `(target_file, target_line, ref_index)`：
- 不允许出现两个不同 `sha256_16`
- 允许重复写入相同 `sha256_16`（幂等），但 verifier 可对重复计数发出 warning（不影响 PASS）

---

## 4) Backfill View 应用规则（Verifier 必须实现）

Verifier 在检查 `evidence_refs` 时必须：
1) 读取目标记录（jsonl 的 target_line）
2) 取出该记录的 `evidence_refs[ref_index]`
3) 若该 ref 缺少 `sha256_16`，则使用 backfill 记录回填到“内存视图”
4) 若该 ref 已有 `sha256_16`，则必须与 backfill（若存在）一致，否则 FAIL

完成 backfill view 后，再执行：
- Step82：dereference + 语义校验
- Step83：sha256 对齐（ref.sha256_16 与 index）
- Step84：range 解引用 + 同质性

---

## 5) Fixture（PASS/FAIL 必须具备）

### 5.1 PASS fixture（必须）
- 原始证据文件里的 evidence_refs 不包含 sha256_16（或部分不包含）
- backfill 文件提供对应 sha256_16
- verifier 应用 backfill view 后 PASS

### 5.2 FAIL fixture（必须）
至少一种 FAIL：
- backfill 的 sha256_16 与 evidence_ref_index 不一致
- 或同一个 (file,line,ref_index) 出现两个不同 sha256_16
- 或 backfill 指向越界行/不存在文件

---

## 6) 最小验收（硬）

必须证明：
- PASS：backfill view 生效（原始缺 sha256_16 但最终 PASS）
- FAIL：backfill 注入错误值被 fail-closed 捕获（exit 1）


