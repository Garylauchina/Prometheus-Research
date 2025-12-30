# V11 Step 67 — Research Bundle Entrypoint Contract (Fact-Only) — SSOT — 2025-12-30

目的：为 Step65 的 `research_bundle/` 提供 **单入口文件**，让研究侧程序只读一个 JSON 即可发现、校验、定位全部 fact-only 研究产物，并能与 evidence package 交叉复核。

原则：
- additive-only：新增入口文件与记录字段，不改变既有产物语义。
- fact-only：入口只做“索引与引用”，不得写解释性结论。
- 可复核：入口必须能用 `SHA256SUMS.txt` / `evidence_ref_index.json` 验证文件身份。

前置：
- Step65：`research_bundle/` 目录与 `run_manifest.research_bundle`
- Step43：`evidence_ref_index.json`（包含 `rel_path` / `sha256_16` / `line_count` / `byte_size`）

---

## 1) 文件路径（冻结）

每个 run_dir 内必须生成：
- `research_bundle/entry.json`

---

## 2) entry.json Schema（冻结）

最小 schema（字段冻结；可 additive 扩展）：

```json
{
  "contract_version": "V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_20251230.1",
  "run_id": "string",
  "ts_utc": "YYYY-MM-DDTHH:MM:SS.ssssssZ",
  "bundle_dir": "research_bundle",
  "artifacts": [
    {
      "kind": "compare_bundle_json",
      "rel_path": "research_bundle/compare_bundle.json",
      "sha256_16": "16hex",
      "byte_size": 1234,
      "evidence_refs": []
    }
  ],
  "evidence_package": {
    "filelist_rel_path": "FILELIST.ls.txt",
    "sha256sums_rel_path": "SHA256SUMS.txt",
    "evidence_ref_index_rel_path": "evidence_ref_index.json"
  }
}
```

约束（冻结）：
- `contract_version`：必须精确匹配上述字符串。
- `bundle_dir`：必须为 `"research_bundle"`。
- `artifacts[]`：只列出 **实际存在** 且被纳入 evidence package 的文件；不得列出不存在的条目。
- `sha256_16`：必须与 `evidence_ref_index.json` 中对应 `rel_path` 的 `sha256_16` 一致。
- `byte_size`：必须与 `evidence_ref_index.json` 中对应 `rel_path` 的 `byte_size` 一致。
- `evidence_refs`：允许为空数组；若提供，必须符合 Step41-46 的 evidence_refs 结构与 dereference 规则。

`kind` 词表（冻结，最小集合）：
- `ablation_compare_json`（Step53）
- `compare_bundle_json`（Step59）
- `compare_bundle_index_json`（Step61/63，可选）

---

## 3) Evidence packaging 覆盖（冻结）

`research_bundle/entry.json` 必须被纳入：
- `FILELIST.ls.txt`
- `SHA256SUMS.txt`
- `evidence_ref_index.json`

且 `entry.json.artifacts[*].sha256_16/byte_size` 必须可由 `evidence_ref_index.json` 复核。

---

## 4) Manifest 记录（additive-only，冻结）

在 `run_manifest.json` 增加字段（字段冻结）：

```json
{
  "research_bundle_entrypoint": {
    "enabled": true,
    "entry_rel_path": "research_bundle/entry.json",
    "contract_version": "V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_20251230.1",
    "artifact_count": 2,
    "status": "pass"
  }
}
```

`status` 词表（冻结）：
- `pass`
- `fail`
- `skipped`

规则：
- 若生成失败且启用 gate（由实现决定是否默认启用），必须写实记录 `status="fail"` 并遵循 fail-closed 约束（见下一节）。

---

## 5) 失败语义（冻结，建议）

当 Step67 在 run-end gate 中启用时（推荐默认启用）：
- entry.json 写入失败 / schema 不完整 / 与 evidence_ref_index 不一致 → **FAIL（exit 2）**

当未启用时：
- 允许 `status="skipped"`，但不得伪造 entry.json。

---

## 6) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + 样例 entry.json + gate/CI 输出片段）


