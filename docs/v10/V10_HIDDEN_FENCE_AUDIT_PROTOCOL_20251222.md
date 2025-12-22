# V10 Protocol: Hidden Fence Audit (Fence Inventory + Gating Telemetry) / 隐含围栏审计协议 — 2025-12-22

## Purpose / 目的

**English (primary)**: Prevent “hidden fences” (implicit human constraints) from silently shaping behavior and causing abnormal convergence.  
This protocol forces every hard gate / fallback / clip / default to be **listed** and **measured** (trigger rate), without injecting thresholds into the decision path.

**中文（辅助）**：防止“隐含围栏”把系统悄悄剪成一个主观策略系统。要求所有硬阈值/硬分支/默认回退/强制裁剪都必须：  
**列清单 + 统计触发率 + 缺字段必须标注 reason**。

---

## Definitions / 定义

- **Ecological fences**: allowed constraints that belong to environment/lifecycle/audit/physical exchange rules (death/repro/collapse/reboot, liquidation, margin rules).
- **Man-made fences (hidden fences)**: constraints that directly or indirectly gate trading behavior (enter/add/exit/size), often disguised as defaults/fallbacks/safety checks.
- **Gating telemetry**: counters that answer: “How often did this gate trigger?” and “How often did it block an action?”

---

## Principle 4 Audit: “Evolution obeys natural selection” / 原则4审计：演化必须遵从自然选择

### Operational definition / 可操作定义

**English (primary)**: A system “obeys natural selection” if the dominant selection pressure comes from **world rules** (capital conservation, liquidation, fees/slippage, margin, time, resource limits, quarterly review, collapse/reboot), not from arbitrary designer gates that pre-filter actions.  

**中文（辅助）**：当系统的淘汰与繁殖主要由“世界规则/物理规则”驱动，而不是被某些拍脑袋阈值先挡在门外时，我们才说它遵从自然选择。

### Hard rule / 硬规则（Fail-fast）

- If a fence **changes the action space** in a way that resembles strategy design (e.g., “only trade when signal strong enough”, “no entry unless abs(signal)>x”, “block add/exit by handcrafted thresholds”), it is a **strategy fence** → treat as **man_made** and must not live inside the decision path.
- “Safety” is not a free pass. If a safety check gates trading behavior (enter/exit/size) and is not an exchange rule, it is still **man_made** and must be surfaced + measured + falsifiable.

### What this audit must answer / 审计必须回答的问题

- **Q4.1**: Are there any fences that prevent Agents from acting for reasons unrelated to exchange physics or lifecycle rules?
- **Q4.2**: Do fences create a “default world” (silent fallback values) that collapses exploration into a narrow behavior attractor?
- **Q4.3**: Are observed population outcomes (mass non-trading, abnormal convergence) explained by market pressure, or by frequent gate blocking?

### Falsifiability requirement / 可否证要求（必须可做对照）

For every `man_made` fence that touches trading behavior (`what_it_gates` includes enter/exit/size/order send):

- It must have an explicit **disable/ablation path** (ops/runner only; not a runtime monkey patch of core).
- It must have a documented **A/B check**:
  - Baseline: fence enabled (current world)
  - Counterfactual: fence disabled (same commit/config/seed/window)
  - Compare at least: `system_roi`, `extinction_rate`, and the fence’s own `block_rate`

**Interpretation rule (minimal)**:

- If disabling a man-made fence causes a large increase in trading activity and changes outcomes, then previous outcomes were partly “designer-shaped” → must be explicitly reported as such (not allowed to claim “pure natural selection”).

---

## 1) Fence Inventory / 围栏清单（必须维护）

Create and maintain a list of all fences, including those in **ops layer**.

For each fence:

- `id`: e.g. `FENCE_I_POSITIONS_EMPTY_FALLBACK`
- `layer`: `core` | `ops` | `runner` | `analysis`
- `type`: threshold | fallback | clip | hard branch | missing-field default
- `category`: ecological | man_made
- `location`: file + function + short snippet reference
- `what_it_gates`: enter | exit | size | order send | liquidation | reporting | other
- `default_behavior`: what happens when triggered
- `risk`: what bias it introduces (e.g., “freezes trading”, “forces always-flat”, “suppresses exploration”)
- `required_telemetry`: which counters must be recorded

> Rule: If it gates trading behavior, it must be treated as **man-made** unless it is a hard exchange rule.

---

## 2) Gating Telemetry / 触发率遥测（必须落盘）

### Minimal telemetry schema (per run)

Write a JSON artifact (suggested): `gating_telemetry.json`

Minimum content:

- `run_id`, `mode`, `created_at`
- `counters`: dict keyed by `fence_id`, each with:
  - `trigger_count`
  - `block_count` (how many actions were prevented)
  - `note` (optional)

### Acceptance rule / 验收规则

- Any fence with **high trigger rate** must be surfaced:
  - Example heuristic: `trigger_count / steps > 0.2` or `block_count / attempts > 0.2`
- High trigger rate is not automatically “bad”, but it must be:
  - explained (ecological vs man-made),
  - and if man-made: moved out of decision path or made evolvable/ablated.

### Principle 4 tie-in / 与原则4的绑定口径

- If `man_made` fences have high `block_count`, then the dominant selection pressure is likely “designer gatekeeping”, not market pressure.
- Therefore, any run used to claim “natural selection behavior” must include:
  - the `gating_telemetry.json` artifact,
  - and a short statement on whether selection pressure appears ecological vs man-made (based on block rates).

---

## 3) Missing fields must be honest / 缺字段必须诚实

When external data is missing/unreliable (positions/fills/orderbook/etc.):

- Never silently replace with “reasonable defaults”.
- Must use `null + reason` and record which fallback was used.

This avoids “default worlds” that trap Agents into abnormal convergence.

---

## 4) Where to implement (C-stage) / C阶段落地点（不进决策路径）

Implementation should stay in **ops layer** (audit shell), not core:

- Record fence inventory in docs (this file).
- Emit `gating_telemetry.json` per run and reference it from `run_manifest.json`.

---

## 5) Minimal initial fence list (seed examples) / 初始示例（种子）

> These are examples; the real list must be generated from the repo.

- `FENCE_I_POSITIONS_EMPTY_FALLBACK` (ops, fallback, man_made)
- `FENCE_M_NO_FILLS_SKIP_RECONSTRUCTION` (ops, hard branch, man_made)
- `FENCE_RATE_LIMITER_BLOCK_ORDER` (ops, hard branch, ecological/physical)
- `FENCE_LIVE_AUTH_GUARD` (ops, hard branch, ecological/safety)


