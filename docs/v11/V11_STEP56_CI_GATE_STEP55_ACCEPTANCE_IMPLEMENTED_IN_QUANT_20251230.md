# V11 Step 56 — CI Gate for Step55 Acceptance — Implemented in Quant — 2025-12-30

目的：记录 Step56 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step56 CI gate run Step54 integration test`
- **Commit (short)**: `36cc203`
- **Commit (full)**: `36cc2030847264ba95db229c7b32bcd5682f184d`

修改的 workflow（Quant）：
- `.github/workflows/v11_evidence_gate.yml`

新增/修改要点（事实）：
- 新增 job：`verify_step54_integration`（Step56 Gate）
- 串行依赖：`needs: verify_step26_evidence`（先 Step26，再 Step54）
- 执行命令：`python3 tools/test_step54_integration.py`
- 失败语义：exit 非 0 → workflow FAIL（阻断 PR/push gate）

---

## 2) 前置条件提供方案（写实）

采用方案 A（fixtures，最稳）：
- `tests/fixtures/step51_C_off_minimal/`
- `tests/fixtures/step51_C_on_minimal/`

每个 fixture 最小文件集合（事实）：
- `run_manifest.json`
- `decision_trace.jsonl`（Step51 的 agent_detail 记录）
- `ablation_summary.json`
- `SHA256SUMS.txt`
- `README.md`

选择方案 A 的理由（事实取向）：
- CI 稳定、无需动态生成 runs
- 结果可复现，不依赖 runner 运行时行为

---

## 3) 测试脚本的 CI 优先策略（事实）

Quant 修改了：
- `tools/test_step54_integration.py`

行为（写实）：
- CI 优先读取 `tests/fixtures/step51_C_off_*` 与 `tests/fixtures/step51_C_on_*`
- 本地后备读取 `runs_step51/*C_off*` 与 `runs_step51/*C_on*`
- 前置条件不满足必须 FAIL（禁止 skip-and-pass）

---

## 4) CI 失败语义（冻结口径落地）

Step56 gate 失败语义（事实）：
- `tools/test_step54_integration.py` exit 非 0 → workflow FAIL → 阻断合并

覆盖的关键断言（由 test 输出体现）：
- 能基于 C_off/C_on runs 生成 Step53 compare
- `ablation_compare.json` 通过 Step53 verifier
- evidence packaging 递归包含 `step53_compare/ablation_compare.json`（FILELIST/SHA256SUMS 覆盖）


