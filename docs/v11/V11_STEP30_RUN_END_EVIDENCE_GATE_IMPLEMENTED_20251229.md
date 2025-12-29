# V11 Step 30 — Run-End Evidence Packaging + Gate (Implemented in Quant) — 2025-12-29

目的：记录 **V11 Step 28（run-end evidence packaging + gate）** 已在实现仓库（Prometheus-Quant）落地为 **强制执行（fail-closed）**，并冻结其“对外可审计口径”。

适用范围：
- execution_world runner 的 run-end（正常结束/STOP/冻结均必须执行）
- 针对 Step 26（DecisionEngine inputs: E + MFStats + Comfort）的最小可复核 gate

SSOT 关联：
- Step 27（最小复核清单）：`docs/v10/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
- Step 28（run-end gate 规格）：`docs/v10/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`
- Step 29（CI gate）：`docs/v10/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`

---

## 1) 落地锚点（实现仓库）

实现仓库（Prometheus-Quant）已完成并推送：
- Quant commit：`2d1de8a`  
- message：`v11: enforce run-end evidence packaging + step26 gate (fail-closed, exit2 on fail)`
- 变更文件：`prometheus/v11/ops/run_v11_service.py`

> 注：Research 仓库不复刻 Quant 代码；此处仅冻结“实现已完成”的审计锚点与行为口径。

---

## 2) 冻结的 run-end 行为（对外口径）

### 2.1 顺序硬约束（必须）

1) 生成/更新 `FILELIST.ls.txt`
2) 生成/更新 `SHA256SUMS.txt`
3) 运行 Step 26 verifier（Quant 自包含版）

禁止：
- 先跑 verifier 再生成 `FILELIST/SHA256SUMS`（会导致 verifier 覆盖范围不完整）

### 2.2 退出码冻结（关键）

- verifier exit `0` → runner exit `0`（PASS）
- verifier exit `1` → runner exit `2`（FAIL：证据不可复核）
- verifier exit `2` → runner exit `2`（ERROR：输入不可读/格式错误）

语义：`exit 2` 表示“证据不可复核”，不得被误当作“正常结束”。

### 2.3 manifest 写实（additive-only）

`run_manifest.json` 必须追加记录：
- `evidence_package`（filelist/sha256sums 路径与 file_count）
- `evidence_gate`（gate_name/version/triggered/verdict/exit_code/time_range/fail_reasons 等）
- `status`：至少区分 `completed_with_evidence_gate_pass` 与 `evidence_gate_failed`（或语义等价字段）

### 2.4 errors.jsonl（append-only）

gate `FAIL/ERROR` 时必须追加写入一条：
- `error_type="evidence_gate_failed"`
- `gate_name/verdict/verifier_exit_code/fail_reasons`

---

## 3) 这一步防的是什么

- 防“证据缺口但误判 run 成功”（fail-open）
- 防“忘记打包 hash/index 导致事后不可验”
- 防“结构退化（contract/mask/evidence_refs 漂移）后还能继续长跑污染结论”


