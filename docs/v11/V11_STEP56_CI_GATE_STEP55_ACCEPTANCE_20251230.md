# V11 Step 56 — CI Gate for Step55 Acceptance (Quant) — SSOT — 2025-12-30

目的：把 Step55（Step54 验收协议）从“建议执行”升级为 **CI 必跑门禁**，防止未来回归把 Step53/54 的证据闭环弄断。

本文件只允许追加（additive-only）；破坏性变更必须提升 major 并重跑最小 PROBE。

前置：
- Step 54：`docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`
- Step 55：`docs/v11/V11_STEP55_STEP54_ACCEPTANCE_PROTOCOL_20251230.md`

---

## 1) CI 必跑项（冻结）

Quant 的 CI 必须包含一个 job（或 step）执行：

```text
python3 tools/test_step54_integration.py
```

预期：
- exit code = 0（PASS）

说明（写实）：
- 该测试依赖 Step51 两次 run_dir（C_off/C_on）可用；CI 需确保 fixture 或生成路径满足该前置条件。
- 不允许“静默跳过”：缺前置条件必须明确 FAIL（使回归可见）。

---

## 2) 失败语义（冻结）

CI gate 的最小失败语义：
- `tools/test_step54_integration.py` 非 0 → CI FAIL（阻断合并）

---

## 3) 交付物（冻结）

Quant 侧：
- CI workflow 更新（把 Step55 验收作为必跑）
- 如使用 fixture：明确 fixture 路径与生成方式（写入 workflow 或 README/注释）

Research 侧：
- 本 SSOT 文档
- 合入后补充一份 `...IMPLEMENTED_IN_QUANT...` 记录（包含 workflow 文件路径 + commit SHA）


