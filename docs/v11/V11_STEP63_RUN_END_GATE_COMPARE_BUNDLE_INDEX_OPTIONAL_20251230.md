# V11 Step 63 — Run-End Evidence Gate Optional: Compare Bundle Index — SSOT — 2025-12-30

目的：将 Step61 的 `compare_bundle_index.json` 从“仅 CI 入口（Step62）”扩展为 **run-end evidence gate 的可选产物**，用于本地/离线研究归档的一致性与可追溯检索。

原则：
- additive-only：新增可选产物与记录字段，不改变既有语义。
- fail-closed：当显式启用 Step63 gate 时，生成/验证/打包任一失败必须导致 run-end gate FAIL（exit 2）。
- 不引入解释：index 与 verifier 只做 fact-only 聚合与一致性校验。

前置：
- Step 61：`compare_bundle_index.json` contract + verifier 已存在
- Step 62：CI gate 已覆盖生成/验证（用于防止入口腐化）

---

## 1) Runner / Run-End Gate 行为（冻结）

新增一个可选开关（Quant runner 或 run-end gate CLI）：
- `--enable-step63-index`

启用时，在 run-end gate 阶段追加以下步骤（顺序冻结）：

1) **Generate compare_bundle_index.json**
- scan_root：使用本 run 的 evidence package root（建议为 run_dir 或其 `runs_root` 父目录下的可控子树），必须在 manifest 中写实记录。
- 输出：`compare_bundle_index.json`（建议放在 run_dir 顶层，便于检索；路径冻结于 manifest）

2) **Verify compare_bundle_index.json**
- 运行 Step61 verifier：
  - `python3 tools/verify_step61_compare_bundle_index.py <path>`

3) **Evidence packaging**
- 必须被纳入：
  - `FILELIST.ls.txt`
  - `SHA256SUMS.txt`
  - `evidence_ref_index.json`
- 若 gate bundle（Step46）开启，则 index 内的 `evidence_refs` 必须可被 verifier 依据 index 进行 dereference 校验（沿用 Step61/Step46 规则）。

4) **Manifest 记录（additive-only）**
在 `run_manifest.json` 增加一个对象（字段冻结）：

```json
{
  "step63_compare_bundle_index": {
    "enabled": true,
    "scan_root": "runs_root_or_run_dir",
    "output_file": "compare_bundle_index.json",
    "generate_exit_code": 0,
    "verify_exit_code": 0,
    "bundle_count": 1,
    "status": "pass"
  }
}
```

`status` 词表（冻结）：
- `pass`
- `fail`
- `skipped`（enabled=false 时）

---

## 2) 失败语义（冻结）

当 `enabled=true`：
- generate 失败（非 0 / 文件不存在）→ **FAIL（exit 2）**
- verify 失败（非 0）→ **FAIL（exit 2）**
- `bundle_count < 1` → **FAIL（exit 2）**（防空跑）

当 `enabled=false`：
- 不生成、不验证，`status="skipped"`，不得影响现有 gate 行为。

---

## 3) scan_root 约束（冻结）

必须满足：
- 可复现：scan_root 必须是 run 内可追溯且稳定的目录（写入 manifest）
- 不跨 run 混扫：默认只扫当前 run 的产物树；如需跨 run 聚合，必须显式传参并记录（本 Step63 baseline 不要求）

---

## 4) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + runner/gate 修改位置 + 样例 manifest 片段）


