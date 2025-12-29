# V11 Step 58 — Fixtures Contract Verifier + CI Integration — Implemented in Quant — 2025-12-30

目的：记录 Step58 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP58_FIXTURES_CONTRACT_VERIFIER_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step58 add fixtures contract verifier + CI gate integration`
- **Commit (short)**: `bf6dc5a`
- **Commit (full)**: `bf6dc5ac519277019318e831a5909060b0dc565a`

新增脚本（Quant）：
- `tools/verify_step57_fixtures_contract.py`

修改 workflow（Quant）：
- `.github/workflows/v11_evidence_gate.yml`
  - 在 `verify_step54_integration` job 中，新增 Step57 fixtures verifier 步骤，并在 Step54 integration test 之前执行

---

## 2) Verifier 断言集（事实）

脚本：`python3 tools/verify_step57_fixtures_contract.py`

最小检查项（按 Step57/Step58 SSOT）：
- fixtures 目录存在：
  - `tests/fixtures/step51_C_off_minimal/`
  - `tests/fixtures/step51_C_on_minimal/`
- 每个 fixtures 目录包含 5 个必需文件：
  - `run_manifest.json`
  - `decision_trace.jsonl`
  - `ablation_summary.json`
  - `SHA256SUMS.txt`
  - `README.md`
- `run_manifest.json` 最小字段存在性（含 `ablation_experiment` 控制变量）
- `ablation_summary.json` 最小字段存在性
- C_off vs C_on 控制变量一致性（除 `variant` 外一致；feature_contract_version 与 evidence_gate_bundle 一致；variant 必须不同）
- `SHA256SUMS.txt` 覆盖最小集合（至少包含 run_manifest/decision_trace/ablation_summary）

Exit codes（事实）：
- PASS → 0
- FAIL → 1（fail-closed，用于 CI gate）

---

## 3) CI 集成语义（事实）

workflow 中执行顺序（写实）：
- Step26 gate（verify_step26_evidence）PASS 后
- Step56 gate（verify_step54_integration）中：
  1) 先跑 Step57 fixtures verifier
  2) 再跑 Step54 integration test

任一步骤非 0 → workflow FAIL（阻断合并）。

---

## 4) 已修复的 fixtures 缺陷（写实）

在落地过程中发现并修复：
- `SHA256SUMS.txt` 缺少 `ablation_summary.json` 的 hash 条目（C_off/C_on 两个 fixtures 均补齐）

---

## 5) 证据入口（供复核）

Quant 侧关键路径：
- Verifier：`tools/verify_step57_fixtures_contract.py`
- CI workflow：`.github/workflows/v11_evidence_gate.yml`


