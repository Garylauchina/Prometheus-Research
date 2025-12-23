# V10 Contract: Startup Preflight + Bootstrap (Capital & Agent Count) — 2025-12-23

## Purpose / 目的

**English (primary)**: Define a hard, auditable contract for **execution-world startup** (`okx_demo_api` / `okx_live`):

- always start from a **clean slate** (no open orders / no positions)
- bootstrap system capital from **exchange balance after flatten**
- (optional but recommended) derive initial Agent count from capital in a deterministic, auditable way

**中文（辅助）**：本合同把“启动时如何对齐交易所真实状态”变成硬规则：先撤单/平仓保持空仓，再用清理后的余额作为启动资金；并可选地规定“按资金计算初始 Agent 数量”的口径，避免系统自说自话。

---

## Scope / 适用范围（强制）

- Applies to: `okx_demo_api`, `okx_live`
- Not required for: `offline`, `okx_demo_sim` (must write `null + reason` if fields are missing)

---

## Startup Preflight (Clean slate) / 启动前置清理（强制）

### Step order (must be fixed) / 固定顺序（不可变）

1) **Connect check**
2) **Snapshot BEFORE** (orders/positions/balance)
3) **Cancel all open orders**
4) **Flatten all positions** (reduceOnly / close semantics; must not open new positions)
5) **Snapshot AFTER** (orders/positions/balance)
6) **Bootstrap** (use `balance_after` as the only allowed source)

### Success conditions (hard gate) / 成功条件（硬门槛）

- `open_orders_after_count == 0`
- `positions_after_count == 0`
- `balance_after` exists and is non-negative

### Failure behavior / 失败行为（强制）

If any hard gate fails:

- set `run_manifest.preflight_status = "failed"`
- set `run_manifest.status = "aborted"` (preferred) or `interrupted`
- write `startup_preflight.json` with failure reasons and partial results
- produce an IEB (see C2.0 runbook) and exit **without entering the main loop**

Rationale: entering the main loop with “dirty” exchange state pollutes all later evidence.

---

## Bootstrap Capital / 启动资金（强制）

### Allowed source / 唯一允许来源

- `bootstrap_capital_value = balance_after` (from preflight AFTER snapshot)

### Exchange is the source of truth / 交易所余额为真值（核心审计规则）

**Hard audit invariant (execution world)**:

\[
exchange\_balance\_{equity} \;\approx\; allocated\_capital + system\_reserve \;=\; current\_total
\]

Where:

- `exchange_balance_equity` is the chosen exchange “account equity” field (see `bootstrap_capital_field` mapping below)
- `allocated_capital` is the sum allocated to Agents (fixed by rule at bootstrap)
- `system_reserve` is the system wallet (residual)
- `current_total = allocated_capital + system_reserve`

**If mismatch occurs** (beyond a small tolerance):

- the system must **reconcile to the exchange value** (exchange wins)
- the reconciliation action must be recorded as an auditable event (see “Capital reconciliation record”)

Recommended handling (does not rewrite individual Agent ledgers):

- keep `allocated_capital` unchanged (audit stability)
- set `system_reserve = exchange_balance_equity - allocated_capital`
- if `system_reserve < 0`, treat as **internal collapse** (reserve exhausted) and stop/mark severity accordingly (do not hide insolvency)

Rationale: without this, the “system wallet” becomes a fictional number and all ROI/collapse claims become unauditable.

### Allocation semantics (hard rule) / 启动资金拆分语义（硬规则）

Given `bootstrap_capital_value` (in `bootstrap_capital_currency`, typically `USDT`):

- `allocated_capital_target = bootstrap_capital_value * allocation_ratio` (default `allocation_ratio=0.8`)
- `system_reserve_base = bootstrap_capital_value - allocated_capital_target` (default 20%)

If `bootstrap_agent_count_enabled=true` and `capital_per_agent` is fixed (default `1000 USDT`):

- `num_agents = floor(allocated_capital_target / capital_per_agent)`  ✅ (floor is mandatory for consistency)
- `allocated_capital_actual = num_agents * capital_per_agent`
- `system_reserve = system_reserve_base + (allocated_capital_target - allocated_capital_actual)`  
  (i.e., the remainder/rounding dust must be carried into system reserve to keep accounting closed)

This rule ensures:

- fixed per-agent start capital (auditable)
- deterministic agent count (auditable)
- closed-form capital triplet at bootstrap (no hidden drift)

### Required manifest fields / 必须落盘字段

- `bootstrap_capital_source` = `"exchange_balance_after_flatten"` (or `"preflight_balance"`, but must be stable)
- `bootstrap_capital_currency` (e.g. `USDT`)
- `bootstrap_capital_field` (which exchange field is used; must be explicit and mapped via alignment evidence)
- `bootstrap_capital_value` (number)
- `allocation_ratio` (default `0.8`)

---

## Bootstrap Agent Count / 初始 Agent 数量（推荐）

### Principle / 原则

Agent count must be derived from capital **deterministically** and recorded to avoid “magic numbers”.

### Recommended rule / 推荐规则

Let:

- `total_capital = bootstrap_capital_value`
- `allocatable = total_capital * allocation_ratio`
- `capital_per_agent` = a fixed, auditable scalar (config)

Then:

- `num_agents = floor(allocatable / capital_per_agent)`  ✅ (floor is mandatory)
- clamp: `num_agents = min(max(num_agents, min_agents), max_agents)`

### Required fields if enabled / 启用时必须落盘

- `bootstrap_agent_count_enabled` (bool)
- `allocation_ratio`
- `capital_per_agent`
- `min_agents`, `max_agents`
- `num_agents` (final)
- `agent_count_rule` (string identifier, e.g. `"floor(allocatable/capital_per_agent) with clamp"`)

### Balance field mapping note (OKX REST vs CCXT) / 余额字段对齐说明

The bootstrap balance field MUST be declared and mapped:

- If using **OKX REST evidence**: explicitly record which OKX field is used (e.g., equity-like vs available).
- If using **CCXT**: `fetch_balance()` typically returns:
  - `total` / `free` / `used` (per currency), plus raw `info`.

**Audit requirement**: `bootstrap_capital_field` must be one of a fixed set (project-defined), and the chosen mapping must be referenced by an alignment evidence bundle (report + raw samples).

Recommended default for “account balance” in audit sense:

- Prefer **equity-like** fields (`total` in CCXT; `eq/totalEq`-like in OKX REST), not `free/availBal`.

---

## Capital reconciliation record / 资金对账记录（强制，execution world）

Each run must write a lightweight reconciliation log (JSONL) at a fixed cadence (recommended: per tick or per lifecycle review):

- `capital_reconciliation_events.jsonl`

Each record must include (redacted-safe):

- `ts_utc`, `tick`
- `exchange_balance_equity` (value + field name + currency)
- `allocated_capital`, `system_reserve`, `current_total`
- `delta = exchange_balance_equity - current_total_before_reconcile`
- `reconciled` (bool), `tolerance`
- `action_taken`: `"set_reserve_to_match_exchange"` | `"collapse_reserve_negative"` | `"skipped"`
- `error_events_window_summary` (counts by type, optional)


If disabled, must write:

- `bootstrap_agent_count_enabled=false`
- `num_agents` still must be recorded, with `num_agents_source="fixed_config"`

---

## Required artifact: startup_preflight.json / 必须产物

In `RUN_DIR/startup_preflight.json` (redacted):

- `start_time`, `end_time`, `duration_ms`
- `mode`, `inst_id`, `symbol_in_use`
- `before`: `open_orders_count`, `positions_count`, `balance` (value+ccy+field)
- `after`:  `open_orders_count`, `positions_count`, `balance` (value+ccy+field)
- `actions[]`: cancel/close actions (IDs hashed/truncated)
- `preflight_status`: `"success"|"partial"|"failed"`
- `preflight_errors[]`

---

## References / 参考

- Incident evidence bundle standard: `docs/v10/V10_INCIDENT_RUNBOOK_C2_0_20251222.md`
- VPS development guide / artifact contract: `docs/v10/V10_VPS_DEVELOPMENT_GUIDE.md`
- Acceptance criteria (Gate 4 execution-world requirements): `docs/v10/V10_ACCEPTANCE_CRITERIA.md`


