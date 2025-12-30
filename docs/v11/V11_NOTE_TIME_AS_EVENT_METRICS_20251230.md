# V11 Note — Time as Event Metrics (De-fence) — 2025-12-30

目的：记录一个研究方向（非实现指令）：在 execution_world 的演化观察中，把“时间刻度（tick/分钟）”视为人造坐标系，逐步转向更自然、更可审计的尺度：**变化次数 / 状态转移成本 / 不可逆事件计数**。

本文件只允许追加（additive-only）。

---

## 1) 核心观点（写实）

- “tick 数/分钟数”在系统层面常常是人为参数（调度、限频、机器负载都会改变它的意义），可能导致隐性围栏：同样的“活了 100 tick”，在不同系统负载下不可比。
- 更自然的尺度应来自 **事件与变化**：
  - **变化次数**：状态发生了多少次改变（例如 open/close/hold 的转移次数；订单状态转移次数）。
  - **状态转移成本**：一次转移消耗的资源（fee、延迟、API calls、CPU time 等），但必须写实可测。
  - **不可逆事件计数**：一旦发生就无法撤销或强约束系统行为的事件（例如强平、穿仓、冻结、fail-closed STOP、审判死亡等）。

该观点的目标是 **去围栏（de-fence）**：让观察尺度更贴近 execution_world 的物理约束，而不是人造时间刻度。

---

## 2) 与当前主线的关系（不冲突）

- 该 note 不要求修改基因/probe/DecisionEngine，不改变现有死亡/繁殖制度。
- 该 note 更像“观测坐标系”的重构方向，可与 Step72（代谢观测）、寿命三视角（L_time/L_exec/L_budget）并存。

---

## 3) 候选事件类型（草案，非冻结）

### 3.1 可逆/可恢复事件（示例）
- decision intent：HOLD→OPEN / HOLD→CLOSE / OPEN→HOLD 等
- order lifecycle：P0→P1 ack→P2 terminal

### 3.2 不可逆事件（示例）
- 强平（exchange liquidation）发生
- 穿仓（system_reserve absorbed negative delta）发生
- 运行 fail-closed 退出（ProbeGating STOP、evidence gate FAIL）
- execution_frozen=true（实时冻结）触发
- 审判死亡（lifecycle death）落盘

---

## 4) 后续讨论的关键问题（待定）

- 哪些事件必须由“真值证据链”支撑（否则必须 NOT_MEASURABLE）？
- 状态转移成本如何定义为纯事实（避免解释性指标）？
- 在跨 run 聚合时，如何避免不同 truth_profile/不同系统负载带来的不可比？


