# V11 Step 69 — CI Gate: Step68 Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step68（run-end gate 校验 `research_bundle/entry.json`）升级为 **CI 必跑且不可回退** 的验收项，锁定 Step67+68 的 schema/校验/fail-closed 语义，防止入口链路被未来改动破坏。

本文件只允许追加（additive-only）。

前置：
- Step67 SSOT：`docs/v11/V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_CONTRACT_20251230.md`
- Step68 SSOT：`docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_20251230.md`
- Step68 Quant 已实现：`tools/test_step68_entrypoint.py`

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml`）：

```text
python3 tools/test_step68_entrypoint.py
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

CI 必须至少证明（由 `tools/test_step68_entrypoint.py` 覆盖）：
- `research_bundle/entry.json` 存在
- entry.json 的 `contract_version`、`bundle_dir`、`evidence_package` 字段满足 Step67
- entry.json 的 `artifacts[]` 中每个条目：
  - 文件存在
  - `sha256_16` 与 `byte_size` 与 `evidence_ref_index.json` 一致
- fail-closed 行为：enabled=true 且校验失败 → exit 2，并写入 `errors.jsonl`（reason_code=step68_entrypoint_failed）
- manifest 写实：`run_manifest.research_bundle_entrypoint{...}` 存在且与 entry.json 一致

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


