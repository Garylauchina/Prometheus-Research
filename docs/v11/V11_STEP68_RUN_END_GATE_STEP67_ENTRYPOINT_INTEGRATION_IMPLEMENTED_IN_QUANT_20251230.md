# V11 Step 68 — Run-End Gate: Step67 Entrypoint Integration — Implemented in Quant — 2025-12-30

目的：记录 Step68 在 **Prometheus-Quant** 的落地实现与验收结果，作为 Research 仓库的可复核锚点（implementation record）。

对应 SSOT：
- `docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_20251230.md`

---

## 1) Quant 实现锚点

- **Commit message**: `v11: Step68 run-end gate Step67 entrypoint integration`
- **Commit (short)**: `150da05`
- **Commit (full)**: `150da050fd8b2f073dd88d8e0148c42d1b022bcf`

修改文件（Quant）：
- `prometheus/v11/ops/run_v11_service.py`
- `tools/test_step68_entrypoint.py`

---

## 2) 产物与校验（事实）

生成文件（事实）：
- `research_bundle/entry.json`

校验要点（事实）：
- artifact 文件存在
- artifact 必须被 `evidence_ref_index.json` 覆盖
- `sha256_16` 与 `byte_size` 必须与 `evidence_ref_index.json` 一致
- 失败 → 写入 `errors.jsonl` 且 exit 2（fail-closed）

---

## 3) Manifest 记录（事实 / additive-only）

`run_manifest.json` 增加对象：
- `research_bundle_entrypoint`（enabled/entry_rel_path/contract_version/artifact_count/status）

说明（事实）：
- Quant 实现中 `status` 词表相对 SSOT 有扩展（例如 `pending_validation`）；但 `pass|fail|skipped` 语义保持一致。


