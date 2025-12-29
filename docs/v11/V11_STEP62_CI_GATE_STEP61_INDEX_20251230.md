# V11 Step 62 — CI Gate for Step61 Index (Quant) — SSOT — 2025-12-30

目的：把 Step61 的 `compare_bundle_index.json` 从“可选离线工具”升级为 **CI 必跑产物**：在 CI 中基于 fixtures-root 生成 index 并验证 PASS，防止 index 入口长期不跑而漂移/腐化。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 57：CI fixtures（Step51 minimal）
- Step 58：fixtures verifier 已纳入 CI
- Step 61：index/verify 脚本已实现

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 step/job（建议挂在现有 `v11_evidence_gate.yml` 的 Step56 job 后续步骤中）：

1) 生成 index（基于 fixtures-root 扫描）

```text
python3 tools/index_compare_bundles.py <scan_root> --output ci_artifacts/compare_bundle_index.json
```

2) 验证 index

```text
python3 tools/verify_step61_compare_bundle_index.py ci_artifacts/compare_bundle_index.json
```

预期：
- 两条命令均 exit 0

说明（写实）：
- scan_root 推荐两种等价来源（任一即可，CI 需固定选择）：
  - `tests/fixtures`（静态 fixtures-root）
  - `runs_step54_test`（由 Step54 integration test 在 CI 中生成的测试 run_dir root，包含派生的 compare_bundle.json）
- `ci_artifacts/` 可为临时目录；若 CI 不保存 artifact，也至少要在日志中打印 index 路径与 bundle_count。

---

## 2) 失败语义（冻结）

任一命令非 0 → CI FAIL（阻断合并）。

---

## 3) 最小断言（硬）

CI 必须至少证明：
- index 生成成功（文件存在）
- `verify_step61_compare_bundle_index.py` PASS
- `bundle_count >= 1`（确保不是空跑；若 fixtures 规模变化，需同步更新本条硬规则并解释原因）

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 文件路径 + CI 输出片段）


