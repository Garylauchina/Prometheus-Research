# V10 Gene Table Audit (execution_world + Ledger truth) / 基因表全量审计

Date: 2025-12-26  
Scope: `Prometheus-Quant` (code truth) + Gate4 execution_world constraints  
Goal: **enumerate everything** the Agent + Core depends on (genome + features + truth), and mark what is *truth-driven* vs *simulated/default* so we do not miss items during the v2 rewrite.

---

## 0) Sources of truth (code)

- **Genome schema**: `prometheus/v10/core/genome.py`
- **Feature vector contract**: `prometheus/v10/core/features.py` (`features_to_vector`, fixed ordering)
- **Decision input wiring**: `prometheus/v10/core/decision_engine.py` (calls `FeatureCalculator.features_to_vector`)
- **execution_world semantics**: `prometheus/v10/core/agent.py` (intent-only; positions must remain empty)
- **Ledger truth**: `prometheus/v10/ops/ledger/ledger_module.py` (writes `ledger_ticks.jsonl`, exports `ledger_*` fields)
- **Service wiring**: `prometheus/v10/ops/run_v10_service.py` (calls Ledger each tick)

---

## 1) Genome table (what evolves)

### 1.1 `GenomeV10` dimensions = 342 (frozen in code today)

From `GenomeV10.to_array()`:

- **[0:170)**: `network_out_weights` (OUT_MARKET network, 170 dims)
- **[170:340)**: `network_in_weights` (IN_MARKET network, 170 dims)
- **[340]**: `entry_threshold`
- **[341]**: `exit_threshold`

**Implication**: any change to feature vector length/order is a **breaking change** (the networks’ input_dim changes → weight layouts are incompatible → must isolate a new pool).

---

## 2) Feature table (what the genome reads)

### 2.1 Current fixed vector ordering (v1, as implemented)

From `FeatureCalculator.features_to_vector()`:

- **E (12 or 15 dims)**: `E1..E12` (+ optional `E13..E15`)
- **I (3 or 4 dims)**: `I1_has_position`, `I2_position_direction`, `I3_state_machine_state` (+ optional `I4_last_signal`)
- **M (12 dims)**: `M1..M12`
- **C (5 dims)**: `C1..C5`

Test evidence pins indices (required E only):
- `vector[12] == I1_has_position`
- `vector[13] == I2_position_direction`
- `vector[14] == I3_state_machine_state`

### 2.2 Truth audit (execution_world)

In execution_world:
- `Agent.positions == []` invariant holds (intent-only) → **agent-local has_position/direction are not truth**.
- Ledger can query exchange positions, but demo positions may be unreliable → must use `positions_truth_quality`.

Therefore, the **current I-table is not judgeable** for execution_world unless it is injected from Ledger truth (or explicitly labeled unknown).

---

## 3) Ledger truth table (what the system can know)

### 3.1 `ledger_ticks.jsonl` evidence schema (current code)

Ledger records (per tick) include:
- capital: `bootstrap_equity`, `exchange_equity`, `capital_health_ratio`
- positions: `positions_truth_quality`, `has_position`, `pos_side`, `pos_size`, `mgn_mode`
- execution: `execution_orders_sent_this_tick`, `...acked...failed...`

### 3.2 Exported features (current code)

`LedgerModule.export_features()` currently exports:
- `ledger_capital_health_ratio`
- `ledger_has_position`
- `ledger_pos_size`
- `ledger_positions_truth_quality`
- `ledger_execution_orders_sent_this_tick`

---

## 4) M/C dimensions: contamination risks (must be audited in v2)

Even if we fix I-dimension, current `features.py` still contains multiple **simulation-style defaults**:

- **M** uses `agent_state['capital']` and `agent_state['position']` and a `recent_trades` window.  
  In execution_world, those must be derived from **exchange evidence** (fills/order_status/positions reconstruction) or explicitly marked degraded.

- **C** uses `agents_list` fields like `has_position`, `pnl_pct`, `roi`, `last_signal`.  
  In execution_world, `pnl_pct/roi/has_position` must be truth-driven or labeled unknown; otherwise C becomes a “pseudo-I” contamination channel.

These are not “bugs”; they are **contract mismatches** that make ablation and attribution non-judgeable.

---

## 5) V2 rewrite acceptance checklist (what must be true after rewrite)

### 5.1 Core truth-driven I inputs (minimal)

For execution_world (Gate4):
- **`capital_health_ratio`** (truth, from Ledger)
- **`position_exposure_ratio`** (truth, from Ledger; 0.0 = flat)
- **`positions_truth_quality`** (truth-quality gate; if not ok → exposure must be null/unknown)

> Note: whether we keep a boolean `has_position` is a *readability/legacy* choice, not a required decision feature. If kept, it must be derived from exposure (`exposure > ε`) and must not fabricate certainty under degraded truth.

### 5.2 Breaking-change discipline

- Any change to feature vector length/order → **new pool namespace** + explicit contract versions in manifest.

---

## 6) Immediate gaps found (actionable)

1) `FeatureCalculator.calculate_i_features()` is still v1 (`has_position/direction/state`).  
2) `SystemManager.calculate_agent_features()` feeds I from `agent.get_state()` (agent-local), which is not truth in execution_world.  
3) Ledger exports truth fields but the injection path into core features is not yet a frozen contract (needs explicit mapping + masking rules).

---

## 7) Deliverable for the next step

For the v2 rewrite, we will produce:
- a frozen **Feature Contract** (names + order + missing rules)
- a frozen **Genome Schema v2** (weight layout matches feature vector)
- a frozen **Ledger → Feature injection contract** (masking, truth_quality semantics)


