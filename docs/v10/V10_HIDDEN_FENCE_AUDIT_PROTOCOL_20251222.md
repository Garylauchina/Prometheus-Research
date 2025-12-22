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


