# V11 Step 77 — CI Gate: Step76 Freeze E2E Acceptance (Quant) — SSOT — 2025-12-30

目的：将 Step76（freeze E2E wiring demo/test）升级为 **CI 必跑且不可回退** 的验收项，锁定关键断言：
- 当 execution_frozen=true 时，任何写操作不得触达 connector（“物理不可达”的运行时证明）
- place/cancel/replace 三条写路径均覆盖

本文件只允许追加（additive-only）。

前置：
- Step74/75：freeze 语义与 CI gate 已存在
- Step76 Quant 已实现：`tools/test_step76_freeze_e2e.py`

---

## 1) CI 必跑项（冻结）

Quant CI 必须新增一个 job 或 step（建议添加到 `.github/workflows/v11_evidence_gate.yml` 的 `verify_step54_integration` job 尾部）：

```text
python3 tools/test_step76_freeze_e2e.py
```

预期：
- exit 0 → PASS
- exit 非 0 → FAIL（阻断合并）

---

## 2) 失败语义（冻结）

- 任一断言失败 → CI FAIL（阻断合并）
- 不允许在 CI 中跳过（不得用条件判断把该测试静默跳过）

---

## 3) 最小断言（硬）

CI 必须至少证明（由 `tools/test_step76_freeze_e2e.py` 覆盖）：
- 冻结前：写操作可达 connector（证明测试有效，不是“永远不调用”假阳性）
- 冻结后：place/cancel/replace 均被拒绝，且 **connector 未被调用**
- manifest section（execution_freeze）结构可生成并写实

---

## 4) 生产写路径“不可绕过”要求（声明，冻结）

除 CI demo/test 外，生产 BrokerTrader 的写路径必须满足：
- freeze pre-check 位于写入口最外层
- 不存在绕过 pre-check 直接调用 connector 的路径

说明：
- 本 Step 仅冻结“CI 断言必须存在且必跑”；生产写路径的静态结构性检查可作为后续 Step78 单独落地。

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 合入后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + workflow 修改位置 + CI 输出片段）


