# V11 Step 71 — CI Gate: Step70 Cross-Run Research Entry Index (Quant) — SSOT — 2025-12-30

目的：将 Step70（跨 run `research_entry_index.json`）升级为 **CI 必跑且不可回退** 的验收项，防止跨 run 聚合入口长期不跑而腐化/漂移。

本文件只允许追加（additive-only）。

前置：
- Step70 SSOT：`docs/v11/V11_STEP70_CROSS_RUN_RESEARCH_ENTRY_INDEX_CONTRACT_20251230.md`
- CI 中已有可用 runs_root：`runs_step54_test`（由 Step54 integration test 生成）

---

## 1) CI scan_root（冻结）

CI 固定使用：
- `scan_root = runs_step54_test`

理由（事实）：
- 该目录在 CI 中稳定生成，包含至少 1 个 run_dir，且 run_dir 内已具备 `research_bundle/entry.json`（Step68）与 evidence package 三件套。

---

## 2) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml` 的 `verify_step54_integration` job 尾部）：

1) 生成跨 run index：

```text
python3 tools/index_research_entries.py runs_step54_test --output ci_artifacts/research_entry_index.json
```

2) 校验跨 run index：

```text
python3 tools/verify_step70_research_entry_index.py ci_artifacts/research_entry_index.json
```

预期：
- 两步均 exit 0 → PASS
- 任一步非 0 → CI FAIL（阻断合并）

---

## 3) 失败语义（冻结）

硬规则：
- scan_root 不存在/不可读 → FAIL（exit 2）
- `entry_count == 0`（空跑）→ FAIL（exit 2）
- schema 不完整/不匹配 Step70 → FAIL（exit 2）

并且：
- 不允许在 CI 中跳过（不得用条件判断把该步骤静默跳过）

---

## 4) 最小断言（硬）

CI 必须至少证明：
- `research_entry_index.json` 生成成功且 schema 满足 Step70
- `entry_count >= 1`
- 至少 1 个 entry 能读取到并解析 run_id / artifact_count

（可选增强）若 verifier 支持读取 run_dir 的 `evidence_ref_index.json`：
- 校验 `entry_sha256_16` 与 `research_bundle/entry.json` 的 sha256_16 一致

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


