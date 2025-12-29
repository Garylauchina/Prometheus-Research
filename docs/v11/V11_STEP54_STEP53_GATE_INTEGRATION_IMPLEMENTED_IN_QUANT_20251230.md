# V11 Step 54 — Integrate Step53 into Evidence Gates — Implemented in Quant — 2025-12-30

目的：记录 Step 54 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step54 integrate Step53 compare into run-end/CI gates`
- **Commit (short)**: `dac806c`
- **Commit (full)**: `dac806c2c3cf86fb570b2fb6a86feb936a85a304`

变更文件（Quant）：
- Modified: `prometheus/v11/ops/run_v11_service.py`
- Added: `tools/test_step54_integration.py`

---

## 2) 开关与 manifest 写实（事实）

新增 CLI 参数（Quant runner）：
- `--enable-step53-compare`
- `--compare-left-run-dir <path>`
- `--compare-right-run-dir <path>`
- `--compare-output-dir <path>`（可选）

`run_manifest.json`（additive-only）新增字段：
- `step53_compare.enabled`
- `step53_compare.left_run_dir`
- `step53_compare.right_run_dir`
- `step53_compare.output_path`
- `step53_compare.generation_status`（`pending|generated|skipped|failed`）
- `step53_compare.reason`

---

## 3) run-end gate 集成（事实）

当 `--enable-step53-compare` 启用且输入 run_dir 存在：
- compare 产物输出到 **当前 run_dir 内**：`run_dir/step53_compare/ablation_compare.json`
- compare 产物被纳入证据包打包范围：
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`
  - `evidence_ref_index.json`（gate-on 时）

Exit code 口径（对齐 Step53）：
- **PASS**：`comparability.passed==true` → exit 0
- **WARNING**：`comparability.passed==false` → exit 0（必须打印 WARNING + reason，不阻塞）
- **FAIL**：工具/证据失败（缺文件/解析失败/schema 缺失/hash 失败等）→ exit 2

未启用或输入缺失：
- `generation_status="skipped"`，`reason` 写实（例如 `flag_disabled` / `missing_run_dirs`）

---

## 4) CI / 最小验收（事实）

新增测试脚本：
- `tools/test_step54_integration.py`

测试覆盖点（最小）：
- 基于 Step51 的两次 run_dir（C_off/C_on）生成 compare
- `ablation_compare.json` 存在
- 运行 `verify_step53_ablation_compare.py` 返回 PASS
- `FILELIST.ls.txt` / `SHA256SUMS.txt` 能包含 `step53_compare/ablation_compare.json`（证明子目录文件被纳入证据包）

---

## 5) 关键设计决策（写实）

- compare 产物放入 `run_dir/step53_compare/`（而非外部 `runs_step53/`）：
  - 使 compare 成为 run 的证据包一部分，自动进入 `FILELIST/SHA256SUMS/evidence_ref_index`
  - 与 run 生命周期绑定（run 删除时 compare 一起删除）

- 证据包打包采用递归包含子目录（允许 `step53_compare/` 被纳入）：
  - 使 run_dir 内的证据文件不因目录层级而漏打包


