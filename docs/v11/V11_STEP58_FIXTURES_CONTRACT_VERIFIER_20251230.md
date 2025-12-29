# V11 Step 58 — Fixtures Contract Verifier + CI Integration (Quant) — SSOT — 2025-12-30

目的：把 Step57（Step51 minimal fixtures contract）从“文档约束”升级为**机器可执行的 verifier**，并纳入 Quant CI（Step56 gate 链路），使 fixtures 漂移立刻可见并阻断合并。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并同步更新 verifier 与 fixtures。

前置：
- Step 56：`docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_20251230.md`
- Step 57：`docs/v11/V11_STEP57_STEP51_MIN_FIXTURES_CONTRACT_20251230.md`

---

## 1) Quant 交付物（冻结）

### 1.1 新增 verifier 脚本（推荐）

Quant 新增：
- `tools/verify_step57_fixtures_contract.py`

（可选方案：扩展 `tools/test_step54_integration.py` 也可以，但推荐独立 verifier，减少耦合。）

### 1.2 CI 集成（硬）

Quant 的 CI workflow（`v11_evidence_gate.yml`）必须在 Step56 gate 前（或同 job 内先）运行：

```text
python3 tools/verify_step57_fixtures_contract.py
```

非 0 退出 → CI FAIL（阻断合并）。

---

## 2) Verifier 断言集（冻结，最小）

Verifier 必须检查以下内容（最小集合）：

### 2.1 fixtures 发现与路径（硬）

必须存在两个 fixtures 目录：
- `tests/fixtures/step51_C_off_minimal/`
- `tests/fixtures/step51_C_on_minimal/`

### 2.2 文件存在性（硬）

每个 fixtures 目录内必须包含：
- `run_manifest.json`
- `decision_trace.jsonl`
- `ablation_summary.json`
- `SHA256SUMS.txt`
- `README.md`

### 2.3 manifest 最小字段（硬）

`run_manifest.json` 中必须存在：
- `run_id`
- `ablation_experiment` 且至少包含：
  - `experiment_name`
  - `variant`
  - `seed`
  - `tick_count`
  - `agent_count`
  - `truth_profile`
  - `mode`
  - `feature_contract_version`
  - `evidence_gate_bundle`（或等价三件套字段）

### 2.4 summary 最小字段（硬）

`ablation_summary.json` 必须存在并至少包含：
- `run_id`
- `ablation_experiment`
- `feature_contract_version`
- `evidence_gate_bundle`（或等价信息）
- `tick_range`
- `decision_intent_counts_total`
- `c_probe_stats`
- `evidence_refs`

### 2.5 控制变量一致性（硬）

C_off vs C_on 两份 fixtures 必须满足：
- 除 `variant` 外，`ablation_experiment` 的控制变量字段完全一致（Step50 口径）
- `feature_contract_version` 一致
- `evidence_gate_bundle` 三件套一致

允许差异：
- `variant`

### 2.6 SHA256SUMS 覆盖（硬）

`SHA256SUMS.txt` 必须至少包含以下文件的条目：
- `run_manifest.json`
- `decision_trace.jsonl`
- `ablation_summary.json`

---

## 3) Exit codes（冻结）

- PASS → exit 0
- FAIL → exit 1

（说明：此 verifier 是 CI gate，用于阻断回归；无需 NOT_MEASURABLE 语义。）

---

## 4) 产出与日志（建议）

建议 verifier 输出：
- PASS/FAIL 总结
- 失败时打印缺失的文件/字段名与 fixtures 路径

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后，新增一份 `...IMPLEMENTED_IN_QUANT...` 记录文档（包含 commit SHA + verifier 路径 + CI workflow 路径）


