# V11 Step 29 — CI Evidence Gate (Step26) — 2025-12-29

目的：把 **Step 26（DecisionEngine inputs: E + MFStats + Comfort）** 的“可复核性”做成 **CI 层的 fail-closed gate**，防止后续 runner 改动造成证据链静默退化。

适用范围：
- Prometheus-Quant（实现仓库）CI（push / PR 到 `main` 与 `v11/**`）
- gate 只验证 **结构与引用闭合**，不验证真实市场数据与策略效果。

---

## 1) Gate 组成（Quant 侧必须自包含）

### 1.1 Fixture（最小、自包含、引用闭合）

路径（示例）：`tests/fixtures/step26_min_run_dir/`

最小内容（必须）：
- `run_manifest.json`（包含 `feature_contract`：`contract_version/dimension/probe_order/probe_categories`）
- `e_probes.jsonl`（至少 1 行）
- `mf_stats_ticks.jsonl`（至少 1 行）
- `comfort_ticks.jsonl`（至少 1 行）
- `decision_trace.jsonl`（至少 1 行，且 `evidence_refs` 回指上述三份 jsonl 的行号）
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `README.md`（说明 fixture 仅用于结构验证）

硬规则：
- fixture 必须小（禁止把 `test_runs/**` 等大体量运行产物混入仓库）。

### 1.2 Verifier（stdlib-only，exit code 冻结）

路径（示例）：`tools/verify_step26_evidence.py`

要求：
- 仅 Python stdlib（不可跨仓 import，不依赖 Research 仓库路径）
- exit code 冻结：`0=PASS / 1=FAIL / 2=ERROR`

### 1.3 CI Workflow（fail-closed）

路径（示例）：`.github/workflows/v11_evidence_gate.yml`

触发（示例）：
- push：`main`、`v11/**`
- pull_request：`main`、`v11/**`

命令（示例）：
- `python3 tools/verify_step26_evidence.py --run-dir tests/fixtures/step26_min_run_dir`

FAIL 策略：
- 任何退出码 ≠ 0 → workflow FAILED → 阻断合并

---

## 2) SSOT 关联（Research 侧）

Step 26 最小复核清单（逻辑口径）：
- `docs/v10/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`

run-end evidence packaging gate（运行时 gate）：
- `docs/v10/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`

本 Step 29（CI gate）与 Step 28（run-end gate）关系：
- Step 28：运行时保证“该次 run 的证据包可复核”（fail-closed）
- Step 29：开发过程保证“未来代码改动不会破坏可复核性”（fail-closed）


