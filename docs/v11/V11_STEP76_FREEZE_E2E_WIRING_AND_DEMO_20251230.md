# V11 Step 76 — Execution Freeze E2E Wiring & Minimal Demo (Quant) — SSOT — 2025-12-30

目的：确保 Step74 的 execution_frozen 不仅是“模块+单测”，而是 **E2E 强制生效**：任何写操作（place/cancel/replace）在进入 BrokerTrader/Connector 之前都必须经过 freeze pre-check；一旦冻结，后续写操作必须被拒绝并写实落盘。

本文件只允许追加（additive-only）。

前置：
- Step74：execution freeze contract（reason_code / evidence / manifest）
- Step74 Quant 已实现 ExecutionFreezeManager
- Step75：CI gate 锁定 freeze 语义不回退

---

## 1) 强制接入点（冻结）

execution_freeze pre-check 必须位于 **所有写路径的最外层**（冻结）：
- BrokerTrader 的 `place_order` / `cancel_order` / `replace_order`（或等价接口）
- 任何 connector 的 write API 之前

硬规则：
- **不得**允许某个调用方绕过该 pre-check（不得存在“直接调用 connector.place_order”路径）。

---

## 2) pre-check 行为（冻结）

每次写操作前必须调用：
- `freeze_manager.check_order_write_allowed(...)`

当 frozen=true：
- 立即拒绝写操作（抛出明确异常或返回明确的 L1 分类，但不得继续向交易所发请求）
- 写实记录（至少）：
  - `errors.jsonl`（如 Step74 已定义）
  - `decision_trace.jsonl`（若本 tick 有 intent）：应写实 `blocked_by_execution_freeze=true` 或等价字段

当 enabled=false：
- 写实为 disabled（manifest/status），但不得静默（防误判）。

---

## 3) 最小 E2E 演示用例（冻结）

提供一个可复现的演示/测试（建议新脚本）：
- `tools/test_step76_freeze_e2e.py`

流程（冻结）：
1) 创建一个最小 runner/broker_trader 实例（可用 stub connector）
2) 触发冻结（例如调用 freeze trigger：`p2_overdue` 或 `account_restricted`，写入证据）
3) 尝试执行一次写操作（place/cancel/replace 任一）
4) 断言写操作被拒绝，且未产生任何“下游 connector write call”证据
5) 断言：
   - `errors.jsonl` 有冻结记录
   - `reconciliation_freeze_events.jsonl` 有冻结事件
   - manifest `execution_freeze.frozen=true` 写实

验收要点（硬）：
- **E2E 证明“冻结后不会再触达交易所写入口”**（哪怕是 stub connector，也要能断言“write 未被调用”）。

---

## 4) CI（建议，非冻结）

若 Step76 引入新测试脚本，建议把它纳入 CI（可作为后续 Step77）。

---

## 5) Research 侧交付物

- 本 SSOT 文档
- Quant 落地后补 `...IMPLEMENTED_IN_QUANT...` 记录（commit SHA + 测试输出片段）


