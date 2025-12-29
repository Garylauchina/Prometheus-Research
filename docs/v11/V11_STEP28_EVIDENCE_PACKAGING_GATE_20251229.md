# V11 Step 28 — Evidence Packaging + Gate (run-end, fail-closed) — 2025-12-29

目的：把“证据包打包 + 最小复核 Gate”做成 execution_world 的 **run-end 硬环**：  
先生成 `FILELIST/SHA256SUMS`，再运行 verifier；若 FAIL，则该 run 的“Step26 可复核声明”无效（必须明确写实为 FAIL）。

适用范围：
- Prometheus-Quant（实现仓库）`execution_world` runner 的 run-end 流程（同一个 run_dir）。
- 本 Step 28 针对 Step 26：DecisionEngine 输入（E + MFStats + Comfort）的可复核性。

---

## 1) 运行时流程（冻结）

在 runner 退出前（无论正常结束/STOP/冻结），按顺序执行：

1) **RunArtifacts：生成证据包索引**
   - 写入/更新 `FILELIST.ls.txt`
   - 写入/更新 `SHA256SUMS.txt`

2) **Evidence Gate：运行 Step26 verifier（fail-closed）**
   - 输入：`--run-dir <RUN_DIR>`
   - 输出：stdout/stderr（可收集到日志），并把结果写入 `run_manifest.json`

3) **退出码冻结**
   - verifier `0` → gate PASS（runner 仍可 exit 0）
   - verifier `1` → gate FAIL（runner 必须 exit 2）
   - verifier `2` → gate ERROR（runner 必须 exit 2）

说明：
- `exit 2` 的目的：让 CI/批量回放/外部监控能稳定识别“证据不可复核”，而不是误当作正常结束。

---

## 2) gate 触发条件（最小、不可绕过）

满足任一条件就必须触发 Step26 gate：
- `run_manifest.feature_contract.dimension >= 10` 且 `probe_order` 包含 `MF_stats` 与 `comfort`（语义等价判断）
- 或 runner 明确声明 `feature_contract_version == V11_FEATURE_PROBE_CONTRACT_20251228.1`（或后续 additive 扩展版本）

禁止：
- 通过 CLI flag/环境变量“跳过 gate”（fail-open）  
  若确需临时关闭，只允许 **在 run_manifest 写实声明**（`gate_disabled=true + reason_code + who/where`），并且该 run 的 Step26 结论自动降级为 NOT_MEASURABLE（不得当 PASS 宣称）。

---

## 3) run_manifest.json 必须写入的 gate 结果字段（建议最小字段集）

在 `run_manifest.json` 追加（additive-only）：

- `evidence_gate`（object）
  - `gate_name`: `"step26_min_review"`
  - `gate_version`: `"2025-12-29.1"`（本文件版本）
  - `verifier_entry`: `"tools/verify_step26_evidence.py"`
  - `verdict`: `"PASS" | "FAIL" | "ERROR"`
  - `verifier_exit_code`: `0|1|2`
  - `ts_utc_start` / `ts_utc_end`
  - `fail_reasons[]`（若 FAIL/ERROR，写入摘要）

硬规则：
- gate FAIL/ERROR 时，必须同步写入 `errors.jsonl`（append-only），并在 manifest 中写 `status="evidence_gate_failed"`（或语义等价字段）。

---

## 4) verifier 的 SSOT

Step 26 的最小复核清单与参考实现（stdlib-only）在 Prometheus-Research（SSOT）：
- `docs/v11/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
- `tools/verify_step26_evidence.py`

实现仓库（Prometheus-Quant）必须：
- 复制同等逻辑到自身闭包可达位置（或实现等价 verifier），并保持 exit code 语义一致；
- 不得依赖跨仓库运行时 import（避免运行环境耦合与不可复现）。


