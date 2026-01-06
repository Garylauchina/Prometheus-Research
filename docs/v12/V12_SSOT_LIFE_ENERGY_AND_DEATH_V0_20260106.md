# V12 SSOT — Life: Energy + Death v0 (Death is NOT reward) — 2026-01-06

Goal: freeze the minimal, auditable Life contract for V12.4 (death-only baseline), with a hard red-line:

> **Death verdict must never be smuggled into reward shaping.**

Additive-only.

---

## 0) Core principle (frozen)

- **Death verdict is a constraint, not an objective.**
- We treat **energy** as an internal survival budget (a contract-defined coordinate), not as exchange equity.

---

## 1) Terms (frozen)

- **energy**: internal survival budget; a state variable owned by Life.
- **death_verdict**: the binary verdict whether the agent remains alive.
- **reward shaping**: any implicit/explicit mechanism that makes death/survival depend on success/profit/fitness ranking, thus turning death into an optimization signal.

---

## 2) Hard red-lines (frozen, no negotiation)

### R1) Death verdict MUST be energy-only

`death_verdict` MUST be computed from **energy only**:

- `death_verdict = (energy_after_tick <= 0)`

Hard ban:
- Death verdict MUST NOT read any “success” signals:
  - profit, ROI, Δequity, win-rate
  - ranking, fitness score, selection pressure metrics
  - “good/bad decision” labels

### R2) No direct equity/profit → energy injection (V12.4)

In V12.4 (death-only baseline), we explicitly ban:

- `profit / ROI / Δequity / Δbalance (exchange_truth)` → `energy`

Rationale: this is the most common way to accidentally turn survival into reward shaping.

### R3) Energy updates must be rule-based, auditable, and ablationable

Any energy update rule MUST:

- be **predefined** by SSOT (no silent adaptive tuning)
- be **auditable** (reason_codes + parameters recorded in evidence)
- be **ablationable** (on/off switch; comparable runs on the same replay dataset)

If any of these are missing => NOT_READY.

### R4) Prefer cost-type rules; forbid outcome-type rules (early mainline)

Allowed (cost-type / resource-type) energy deltas (examples):
- tick survival cost
- interaction impedance cost (latency / reject / rate-limit buckets), when measurability is satisfied
- attempt cost (placing an order attempt), if/when uplink is enabled

Forbidden (outcome-type / success-type) energy deltas:
- profit-based bonus
- “good trade” bonus
- “alpha score” bonus

---

## 3) Baseline v0 (death-only) contract (frozen)

This is the ugly baseline life mechanism.

- `truth_profile`: `replay_truth`
- `energy_init`: constant `E0` for all agents (v0)
- `delta_per_tick`: constant `-1` for all agents (v0)
- `death rule`: `energy_after_tick <= 0` => dead
- **Reproduction**: disabled (explicitly deferred)

Note:
- “Mass simultaneous death” is an allowed and informative baseline outcome.

---

## 4) Evidence requirements (v0)

Life v0 must produce minimal auditable evidence (exact filenames are implementation-defined, but semantics must be equivalent):

- Per-run summary (required):
  - `agent_count`
  - `energy_init_E0`
  - `delta_per_tick`
  - `steps_target`
  - `steps_actual`
  - `extinction_tick` (or null if not extinct)
  - `verdict` + `reason_codes`

- Per-tick summary (recommended, strict JSONL):
  - `tick_id`
  - `alive_count`
  - `dead_count_cum`
  - `extinct` (bool)

Hard rule: all `.jsonl` evidence must be strict JSONL (no comments).

---

## 5) NOT_MEASURABLE / FAIL semantics (frozen)

- **FAIL**:
  - missing required evidence
  - non-strict JSONL
  - death_verdict reads forbidden “success” signals

- **NOT_MEASURABLE**:
  - evidence is valid but a higher-level measurement (e.g. impedance-based energy costs) is disabled or not measurable
  - (baseline v0 itself should usually be PASS if evidence is complete)

---

## 6) Cross-links (frozen entries)

- V12 index (EN): `docs/v12/V12_RESEARCH_INDEX.md`
- V12 index (CN): `docs/v12/V12_RESEARCH_INDEX_CN.md`
- Replay dataset v0: `docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`


