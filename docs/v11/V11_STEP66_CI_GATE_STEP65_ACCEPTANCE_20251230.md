# V11 Step 66 — CI Gate: Step65 Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step65（research_bundle 研究消费入口目录）从“可用功能”升级为 **CI 必跑且不可回退** 的验收项，防止未来改动破坏目录布局、manifest 写实、evidence packaging 覆盖。

本文件只允许追加（additive-only）。

前置：
- Step65 SSOT：`docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_20251230.md`
- Step65 Quant 已实现：`tools/test_step65_research_bundle.py`

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml`）：

```text
python3 tools/test_step65_research_bundle.py
```

预期：
- exit 0 → PASS
- 非 0 → FAIL（阻断合并）

---

## 2) 失败语义（冻结）

- 任何断言失败 → CI FAIL
- 不允许在 CI 中跳过（不得用条件判断把该测试静默跳过）

---

## 3) 最小断言（硬）

CI 必须至少证明（由 `tools/test_step65_research_bundle.py` 覆盖）：
- `run_dir/research_bundle/` 存在
- 至少收集到 Step53/59 的 fact-only 产物副本（按当前实现：`ablation_compare.json`、`compare_bundle.json`）
- `run_manifest.json` 中 `research_bundle{...}` 字段写实，且未生成产物为 `null`（不伪造空文件）
- evidence packaging 覆盖 `research_bundle/`（`FILELIST.ls.txt` / `SHA256SUMS.txt` / `evidence_ref_index.json`）

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


