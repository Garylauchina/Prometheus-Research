# V11 Step 59 — Compare Bundle (fact-only) — Implemented in Quant — 2025-12-30

目的：记录 Step59 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP59_COMPARE_BUNDLE_CONTRACT_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step59 generate compare_bundle.json (fact-only)`
- **Commit (short)**: `524b322`
- **Commit (full)**: `524b32223462abbb6fe4dd6d8c4012dc974de425`

新增脚本（Quant）：
- `tools/generate_step59_compare_bundle.py`
- `tools/verify_step59_compare_bundle.py`

---

## 2) 行为与口径（事实）

生成器：
- 输入：一个 compare 目录（包含 `ablation_compare.json`）
- 输出：`compare_bundle.json`（写入同目录或 `--output-dir`）
- 原则：只做摘录/汇总（fact-only），不新增指标、不写解释
- `comparability.passed=false` 仍生成 bundle（写实 reason，NOT_MEASURABLE 风格）

验证器：
- 校验 `compare_bundle.json` schema 完整性
- 校验 evidence refs 的存在性与基本格式（file/sha256_16/purpose）

Exit codes（事实）：
- `generate_step59_compare_bundle.py`：PASS=0；FAIL=2
- `verify_step59_compare_bundle.py`：PASS=0；FAIL=1

---

## 3) evidence_refs（事实）

bundle 至少回指 3 个文件：
- 源 `ablation_compare.json`
- left `ablation_summary.json`
- right `ablation_summary.json`

每条 refs 至少包含：
- `file`
- `sha256_16`
- `purpose`

---

## 4) 示例复核入口（写实）

示例输出（来自 Step53 compare 目录）：
- `runs_step53/compare_20251229_184438/compare_bundle.json`

校验（示例）：

```text
python3 tools/generate_step59_compare_bundle.py runs_step53/compare_20251229_184438
python3 tools/verify_step59_compare_bundle.py runs_step53/compare_20251229_184438/compare_bundle.json
```


