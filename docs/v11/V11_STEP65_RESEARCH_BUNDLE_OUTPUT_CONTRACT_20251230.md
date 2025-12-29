# V11 Step 65 — Research Bundle Output Contract (Run-End) — SSOT — 2025-12-30

目的：冻结一个 **研究侧消费入口** 的目录布局与命名规则，把 Step53/59/61 的派生产物组织为可检索、可归档、可复核的“research_bundle”，避免散落在 run_dir 顶层造成长期漂移与混扫污染。

原则：
- additive-only：新增目录与引用字段，不改变既有产物语义。
- fact-only：research_bundle 只收集事实文件与引用，不包含解释性文本。
- 单 run 与多 run 聚合必须物理分离（避免 mixed scan_root）。

前置（已有产物）：
- Step53：`ablation_compare.json`
- Step59：`compare_bundle.json`
- Step61：`compare_bundle_index.json`
- Step28/46：evidence package（`FILELIST.ls.txt` / `SHA256SUMS.txt` / `evidence_ref_index.json`）

---

## 1) research_bundle 目录布局（冻结）

在每个 run_dir 内新增目录：
- `research_bundle/`

该目录内允许出现的文件（最小集合，冻结）：
- `research_bundle/compare_bundle.json`（Step59）
- `research_bundle/ablation_compare.json`（Step53）
- `research_bundle/compare_bundle_index.json`（Step61/Step63，可选）
- `research_bundle/README.txt`（可选，**仅允许写“文件列表 + 生成时间 + 版本号”**，不得写解释性结论）

说明：
- 上述 3 个 json 文件均为 **fact-only** 研究消费入口。
- `compare_bundle_index.json` 在 Step63 enabled=true 时才会生成；CI 的 Step62 产物不强制写入 run_dir。

---

## 2) 单 run vs 多 run 聚合（冻结）

### 2.1 单 run（run_dir 内）

单 run 只允许生成/包含：
- 该 run 自身产出的 `compare_bundle.json`（及其上游 refs）
- 该 run 自身的 `compare_bundle_index.json`（scan_root 必须是该 run 的可控子树；写入 manifest）

禁止：
- 在 run_dir 内生成“跨 run 聚合”的 index（容易混扫、不可控）

### 2.2 多 run 聚合（runs_root 外部工具）

跨 run 聚合必须通过外部工具在一个显式 runs_root 上执行：
- `tools/index_compare_bundles.py <runs_root> --output <out_path>`

输出路径建议（非强制）：
- `<runs_root>/compare_bundle_index.json` 或 `<runs_root>/research_bundle_index/compare_bundle_index.json`

关键：跨 run 聚合产物必须与单 run 产物 **物理隔离**（不同目录），并在产物内记录 `scan_root`。

---

## 3) Evidence packaging 要求（冻结）

当这些文件在 run_dir 中存在时（路径可变，但语义固定），必须被纳入 evidence package：
- `research_bundle/compare_bundle.json`
- `research_bundle/ablation_compare.json`
- `research_bundle/compare_bundle_index.json`（若生成）

必须覆盖：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`

---

## 4) Manifest 记录（additive-only，冻结）

在 `run_manifest.json` 增加对象（字段冻结）：

```json
{
  "research_bundle": {
    "enabled": true,
    "bundle_dir": "research_bundle",
    "artifacts": {
      "compare_bundle_json": "research_bundle/compare_bundle.json",
      "ablation_compare_json": "research_bundle/ablation_compare.json",
      "compare_bundle_index_json": "research_bundle/compare_bundle_index.json"
    }
  }
}
```

规则：
- 若某产物未生成，则对应值为 `null`（不得伪造空文件）。
- `enabled=false` 时允许整个对象缺失或 `status=skipped`（实现可选，但需写实一致）。

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + 样例目录树 + manifest 片段）


