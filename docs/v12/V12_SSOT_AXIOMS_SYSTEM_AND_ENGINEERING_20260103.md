# V12 SSOT — Axioms (System-level vs Engineering-level) — 2026-01-03

目的（冻结）：
- 保存 V12 的“指导性公理”（system-level），**不改变当前版本节奏**，不直接作为单次提交的验收项。
- 同时明确“工程级公理”（engineering-level）是为**净化观测/归因环境**服务，确保系统级公理能被稳定观测与复现。

本文件 additive-only。

---

## 1) System-level axioms（系统级公理，指导性，不直接作为工具验收项）

### Axiom 0（原文，冻结）

> 公理 0：所有个体都受到统一的 birth–death / 资源约束裁决。

含义（解释性补充，冻结入口）：
- “统一裁决”是选择压力的来源；任何绕过/分叉裁决口径的实现都会把演化退化成特权系统。
- 该裁决必须对所有个体一致地作用于：生存、死亡、资源消耗/补给（例如 Δenergy / Δbalance events）。

### Axiom 1（原文，冻结）

> 公理 1：生命意义 = 个体在该裁决下对自身存在方式的内在坐标系。

含义（解释性补充，冻结入口）：
- 行为可被视作“内在坐标系”的投影；低级体投影更扁平，高级体投影更高维、更情境化。
- 在当前版本（V12.x early）我们**不否定复杂性**，而是将其冻结为“最扁平可测版本”，以验证测量系统的普适性。

---

## 2) Engineering-level axioms（工程级公理，执行约束，用于净化可观测环境）

工程级公理不是“植入策略”，而是为了让 system-level axioms 可被证据系统稳定观测（可 join、可复跑、可比对）。

### E-Axiom A：Attribution-first（可归因优先）

- 任意新自由度/新旋钮进入系统前，必须回答：结果能否被 join 到真值证据链（event_id + evidence_ref + join keys）？
- 不可归因 ⇒ 不可观测 ⇒ “自由度失去价值”。

### E-Axiom B：Shared-state freeze（共享状态先冻结）

- 在“多 Agent 共享账户/共享执行通道”的阶段，账户级共享状态默认 `system_fact` 冻结（例如 `posMode/mgnMode`）。
- 若允许表达，只能走 `agent_proposable`：Agent 仅“提议”，由 Broker/ProxyTrader gate-control 执行，并必须有 write+read truth 闭环证据。

### E-Axiom C：Freedom budget（自由度按证据成本分层开放）

- 先开放证据成本低、后果直接的空间（典型：order 参数、可消融候选维度）。
- 再开放证据成本中等但能闭环的空间（典型：`leverage_target` 走 pretrade + positions truth）。
- 最后才开放会改变系统动力学结构的共享状态（典型：`posMode/mgnMode`），通常需要隔离/强路由/更重账簿。

---

## 3) Applicability（适用场景对照，冻结入口）

### 3.1 System-level axioms：适用范围

- 适用于：生命系统（birth–death）、资源裁决、能量接口（Δ events）、演化观测目标（聚类/维度坍缩）。
- 不直接约束：具体交易策略、具体订单参数取值（这些属于下游投影与碰撞空间）。

### 3.2 Engineering-level axioms：适用范围

- 适用于：证据链设计、Broker/ProxyTrader gate、run_dir 证据落盘、verifier/manifest 一致性、对齐表（alignment table）的控制分类。
- 不改变：system-level axioms 的含义（工程约束不得“偷偷改裁决”）。

---

## 4) Concrete mapping (V12.4, frozen entry)

当前落地口径（只增不改）：
- `posMode`：`system_fact`（必须先读真值确认并冻结）
- `mgnMode`：`system_fact`（必须先读真值确认并冻结）
- `posSide`：`agent_expressible`（order 参数，但受 `posMode(system_fact)` 约束）
- `leverage_target`：`agent_proposable`（必须 `set-leverage` + `positions truth` 闭环，fail-closed）


