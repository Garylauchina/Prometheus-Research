# V11 Step 65 — Research Bundle Output Contract — Implemented in Quant — 2025-12-30

目的：记录 Step65 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step65 research_bundle output contract (fact-only)`
- **Commit (short)**: `8dab067`
- **Commit (full)**: `8dab06790b013b43516d5bb57803f45e6780981a`

修改文件（Quant）：
- `prometheus/v11/ops/run_v11_service.py`
- `tools/test_step65_research_bundle.py`

---

## 2) 目录布局与行为（事实）

在每个 run_dir 中新增：
- `research_bundle/`（研究侧统一消费入口）

收集方式（事实）：
- 将既有 fact-only 产物复制为副本进入 `research_bundle/`
- 原始产物目录保留不变（双份存储）

样例（事实）：
- `research_bundle/ablation_compare.json`（Step53 产物副本）
- `research_bundle/compare_bundle.json`（Step59 产物副本）
- `research_bundle/compare_bundle_index.json`：未生成则为 null（本次样例为 null）

---

## 3) Manifest 记录（事实 / additive-only）

新增对象（字段冻结）：
- `research_bundle.enabled`（本次实现默认为 true）
- `research_bundle.bundle_dir = "research_bundle"`
- `research_bundle.artifacts.*`（未生成则 `null`，不得伪造空文件）

---

## 4) Evidence packaging（事实）

`research_bundle/` 内文件会被自动纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`


