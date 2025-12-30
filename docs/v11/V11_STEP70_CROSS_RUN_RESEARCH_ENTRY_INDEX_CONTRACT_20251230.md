# V11 Step 70 — Cross-Run Research Entrypoint Index (Fact-Only) — SSOT — 2025-12-30

目的：为 runs_root（多 run 目录）生成一个 **跨 run 的研究入口索引**，统一聚合每个 run 的 `research_bundle/entry.json`，用于批量检索/归档/研究消费。

原则：
- fact-only：仅聚合事实入口，不输出解释性结论。
- 混扫防护：必须显式记录 scan_root，并避免把不同来源的 entry 混到同一个 index（可检测）。
- 可复核：index 必须提供 `sha256_16` 与必要的 evidence_refs，支持与 `evidence_ref_index.json` 交叉校验。
- additive-only：本文件只允许追加。

前置：
- Step67：`research_bundle/entry.json`（单 run 入口）
- Step68/69：entrypoint 校验 + CI 防回退（保证单 run 入口稳定）
- Step61：compare_bundle_index（可作为实现参考，但 index 对象不同）

---

## 1) 输出文件与命名（冻结）

跨 run 聚合输出（文件名冻结）：
- `research_entry_index.json`

输出位置（实现可选，但必须写实记录）：
- 推荐：`<runs_root>/research_entry_index.json`
- 或：`<runs_root>/research_bundle_index/research_entry_index.json`

---

## 2) scan_root 规则（冻结）

工具必须以一个显式 `scan_root` 运行：
- `scan_root`：一个目录（runs_root），其下包含多个 run_dir（每个 run_dir 可有 `run_manifest.json`、`research_bundle/entry.json` 等）

硬规则：
- index 内必须记录 `scan_root`（字符串，建议绝对路径或相对调用点的固定表示）。
- index 生成必须是 **只读扫描**（不得修改 run_dir 内任何文件）。

---

## 3) research_entry_index.json Schema（冻结）

最小 schema（字段冻结；可 additive 扩展）：

```json
{
  "contract_version": "V11_STEP70_RESEARCH_ENTRY_INDEX_20251230.1",
  "ts_utc": "YYYY-MM-DDTHH:MM:SS.ssssssZ",
  "scan_root": "string",
  "entry_count": 1,
  "entries": [
    {
      "run_dir_rel": "runs_step54_test/test_integration_run",
      "entry_rel_path": "runs_step54_test/test_integration_run/research_bundle/entry.json",
      "entry_sha256_16": "16hex",
      "run_id": "string",
      "entry_contract_version": "V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_20251230.1",
      "artifact_count": 2,
      "evidence_refs": []
    }
  ]
}
```

字段约束（冻结）：
- `contract_version`：必须精确匹配上述字符串。
- `entry_count == len(entries)`。
- `entry_rel_path` 必须指向一个存在的文件。
- `entry_contract_version` 必须等于 Step67 contract_version。
- `entry_sha256_16`：
  - 必须等于该 `entry.json` 文件本身的 sha256 前 16 个 hex 字符；
  - 且必须与该 run_dir 的 `evidence_ref_index.json` 中对应 `rel_path="research_bundle/entry.json"` 的 `sha256_16` 一致（若可读取到）。
- `run_id/artifact_count`：必须从 entry.json 中读取并写实填充。
- `evidence_refs`：允许为空数组；若提供必须符合 Step41-46 的结构（可选增强）。

`run_dir_rel` 语义（冻结）：
- `run_dir_rel` 是相对于 `scan_root` 的路径（用于稳定定位，不依赖绝对路径）。

实现细节（允许，非冻结）：
- verifier 若要读取 `entry_rel_path` 指向的文件，必须以 `scan_root` 作为基准拼接实际路径（例如 `join(scan_root, entry_rel_path)`）；否则在 CI 中可能出现 “file not found” 导致该项校验 NOT_MEASURABLE。

---

## 4) 混扫防护（硬规则）

index 生成必须避免混扫污染：
- 如果 `entries[]` 中出现重复的 `entry_sha256_16` 但 `run_dir_rel` 不同，必须记录为 WARNING（允许重复但要显式统计）。
- 如果扫描到的 entry.json 的 `bundle_dir != "research_bundle"` 或 contract_version 不匹配，必须视为无效 entry（默认跳过并计入 invalid_count；若开启严格模式则 FAIL）。

（可选实现）支持 `--strict`：
- strict 模式下：发现无效 entry → exit 2。

---

## 5) 失败语义（冻结）

默认（非 strict）：
- 生成成功 → exit 0
- scan_root 不存在/不可读 → exit 2
- entries 为空（entry_count=0）→ exit 2（防空跑，作为研究入口必须有内容）

strict 模式（若实现）：
- 任一无效 entry → exit 2

---

## 6) Research 侧交付物

- 本 SSOT 文档
- 工具实现建议在 Quant（`tools/index_research_entries.py` + `tools/verify_step70_research_entry_index.py`）或研究侧独立工具；落地后补 `...IMPLEMENTED_IN_QUANT...` 记录。


