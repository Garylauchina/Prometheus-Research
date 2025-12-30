# V11 Step 79 — Freeze Precheck Dominance Guard (BrokerTrader) — SSOT — 2025-12-30

目的：在 Step78（文件级 non-bypass）之上，进一步保证 **BrokerTrader 内部也不能绕过 freeze gate**：任何 connector 写调用必须被 “freeze pre-check” 语句在控制流上支配（dominance）。

本文件只允许追加（additive-only）。

前置：
- Step74/75/76/77：运行时 freeze + 测试与 CI gate
- Step78：结构性 non-bypass（禁止生产代码旁路直接调用 connector 写方法）

背景事实（来自 Quant 当前实现）：
- 生产写入口文件：`prometheus/v11/ops/broker_trader.py`
- 类：`BrokerTrader`
- 主要写入口函数：`submit_intent()`（该函数内部调用 `okx_connector.place_order(...)`）

---

## 1) 必须成立的安全语义（冻结）

在 `execution_frozen=true` 后：
- **任何**订单写操作（place/cancel/replace）必须在到达 connector 之前被阻断。
- 该阻断必须发生在 **BrokerTrader 写入口**，且必须有 append-only 证据（errors / freeze events / manifest anchors）。

Step79 的目标不是替代运行时机制，而是防止未来重构导致：
- 删除/移动 freeze pre-check
- 将写调用包进 helper 导致 review 漏洞
- 在 BrokerTrader 内新增第二个“未 pre-check 的写路径”

---

## 2) 冻结前置检查（Pre-check）定义

Quant 必须冻结一个 **唯一的 pre-check 调用点**（函数名冻结，且在文档/代码中可审计），例如：
- `freeze_manager.check_order_write_allowed(...)`
  - 或等价的单一入口（以 Quant 实际命名为准）

Step79 不规定其参数细节，但要求：
- 该调用 **在控制流上支配**（dominates）任何 connector 写调用
- 若 pre-check 抛错/返回不允许，则不得继续触达 connector

### 2.1 冻结命名（Quant 已确认）

冻结 pre-check 的唯一函数名与位置如下（用于静态门禁的唯一匹配目标）：
- 文件：`prometheus/v11/core/execution_freeze.py`
- 类：`ExecutionFreezeManager`
- 函数：`check_order_write_allowed(self, operation: str = "order_write") -> bool`

说明：
- BrokerTrader 写入口在触达 connector 写方法前，必须调用：
  - `if not self.freeze_manager.check_order_write_allowed("place_order"): ...`

---

## 3) 静态门禁规则（Dominance）

新增/扩展一个静态门禁工具（建议直接扩展 Step78 的 `tools/freeze_gate_guard.py`）以覆盖：

### 3.1 规则 R1（函数级唯一写入口）

在生产代码中：
- connector 写方法只允许出现在 allowlist 文件内（Step78 继续生效）
- 且在 allowlist 文件内，写方法只允许出现在以下函数集合（冻结）：
  - `BrokerTrader.submit_intent`
  - （如存在）`BrokerTrader.execute_lifecycle_flatten` / `BrokerTrader.cancel_*` 等明确列出的写入口

### 3.2 规则 R2（pre-check dominance）

对每一个 `Call` 节点，如果它是：
- `self.okx_connector.place_order(...)` / `...cancel_order(...)` / `...replace_order(...)`

则要求在同一函数体内：
- 在到达该 `Call` 的所有路径上，必须先执行冻结 pre-check（dominance）

最小可执行近似（AST 可实现的保守规则）：
- 在该 connector 写调用之前的“顺序语句”中必须出现一次 pre-check 调用
- 且 connector 写调用不得出现在 pre-check 之前的任何分支中

注：该近似可以保守（宁可误报也不漏报）。任何误报只能通过显式重构（例如把写调用收敛到单一 block）解决，不允许通过放宽规则“跳过”。

---

## 4) CI 集成与失败语义（冻结）

Step79 检查必须在 CI 中无条件执行，不可跳过：
- exit code：`0=PASS`, `1=FAIL`, `2=ERROR`
- `FAIL/ERROR` 都必须阻断合并
- 失败信息必须标注为 `CRITICAL SECURITY ISSUE`

---

## 5) 最小验收（硬）

必须证明以下 2 点：
- PASS：主分支结构满足 R1/R2
- FAIL：故意把 `place_order` 移到 pre-check 之前 / 删除 pre-check 后，静态门禁能在 CI 中失败并输出定位

---

## 6) Quant 落地记录要求

Quant 落地后必须新增一份不可变记录：
- `docs/v11/V11_STEP79_FREEZE_PRECHECK_DOMINANCE_GUARD_IMPLEMENTED_IN_QUANT_20251230.md`
  - commit SHA
  - allowlist 函数集合（冻结）
  - CI PASS 片段
  - 失败示例（可用 unit test 或自检脚本输出证明）


