# D1 SSOT — Active interoception + bidirectional interaction adjudication v0 — 2026-01-07

Additive-only. This SSOT freezes the **D1 base** and the **D1 stop rules**.
It is a contract for execution and verification (no narrative).

---

## §0 Scope (frozen)

D1 base theme:
- **Active interoception**: death-proximity is a decision input (derived from survival ledger only).
- **Bidirectional interaction adjudication**: decisions change interaction intensity; interaction intensity changes cost exposure; cost exposure changes survival energy; survival energy changes interoception.

Hard boundary:
- Rewards (including reproduction reward) **must not usurp death adjudication** (directly). Allowed only to bias action choice (indirect).

---

## §1 Frozen preconditions (must hold)

### §1.1 W0 measurability gate (mandatory)

All D1 runs MUST use world inputs where W0 verdict = `PASS`.
Tool (Research):
- `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`

If W0 != PASS => D1 campaign is `NOT_MEASURABLE`.

### §1.2 Evidence discipline (mandatory)

- Strict JSON / JSONL only (one JSON object per line; no comments).
- Fail-closed: missing required evidence file => `FAIL (evidence_missing)`.

---

## §2 D1 base: ledgers + interoception (frozen)

### §2.1 Two ledgers (hard separation)

**Survival ledger** (authoritative for death):
- Energy update ONLY from:
  - `action_cost`
  - `impedance_cost`
- Death verdict:
  - `death = (energy_after <= 0)`

**Reward ledger** (non-authoritative for death):
- Reward MAY bias action selection/policy.
- Reward MUST NOT directly:
  - increase energy
  - modify death threshold / energy cap
  - modify action/impedance cost tables/functions

### §2.2 Interoception signal (D1.0: single value)

D1.0 uses a single interoception value derived from survival energy:
- Option (recommended): `energy_level_discrete ∈ {LOW, MED, HIGH}` (Avida-style)
  - computed from `energy_ratio = clamp(energy / energy_cap, 0, 1)` and frozen thresholds

No trend/burn-rate in D1.0.

### §2.3 Interoception weight (fixed; Option A)

- `w_death ∈ [0,1]` is a per-agent constant (genome/identity field).
- It may affect action selection only (indirect effect on energy trajectory).
- It must be logged in evidence for each agent.

---

## §3 Bidirectional interaction adjudication (frozen)

### §3.1 Decision output is constrained to “interaction intensity”

D1.0 decision output MUST include:
- `interaction_intensity` (bounded integer or float; frozen range)
- `action_class` (finite enum; frozen set)

No price prediction requirement in D1.0.

### §3.2 Action cost must be auditable and action-dependent

Survival ledger must show:
- `action_cost = cost_table[action_class] + cost_intensity[interaction_intensity]`
- Tables are frozen by version id.

### §3.3 Impedance cost must be auditable and world-coupled

Impedance is sourced from logged world/interaction events (e.g., measurability gaps, API friction events).
The exact impedance observable (`z_t`) must be pre-registered per campaign.

---

## §4 D1 falsification criteria (F1/F2/F3) + “3 strikes” stop rule

We run independent D1 campaigns (world-input independence; see D0 SSOT §2.1).
If the same failure (F1/F2/F3) triggers in **3 independent campaigns**, stop D1 under this base and redesign.

### F1) Protocol / evidence failure (fail-closed)

Trigger if any required evidence is missing, non-strict, or cannot be joined/recomputed:
- `FAIL (protocol_unreliable)`

### F2) Interoception does not affect interaction (closed-loop missing)

Trigger if, under the pre-registered test, varying `w_death` does NOT produce measurable differences in `interaction_intensity` / `action_class` distributions (same world input, same seed protocol):
- `FAIL (interoception_not_expressed_in_behavior)`

### F3) Interaction does not affect survival-cost exposure (world cannot penetrate)

Trigger if, under the pre-registered test, varying interaction (via policy or forced schedule) does NOT change the time series of `action_cost` and/or `impedance_cost` in a measurable way:
- `FAIL (interaction_not_coupled_to_cost_exposure)`

Notes:
- These are preconditions to any “higher-level” claims about survival distribution shapes.

---

## §5 Minimal “three knives” to reuse (mandatory for D1)

These are the minimal, mechanism-agnostic checks that must remain available:

1) **W0 gate** (measurability prerequisite)
2) **Time-order break negative control**: `shuffle` or `time_reversal` must be definable and runnable with explicit evidence field `world_transform.kind`
3) **Cross-world pseudo-independence check**: at least one cross-market/cross-window check under frozen knobs (to prevent single-world overfitting)

The exact implementation per campaign must be pre-registered, but the existence of these controls is non-negotiable.

---

## §6 Required evidence files (minimum)

Per run_dir:
- `run_manifest.json`
  - includes: base versions, dataset_dir, w0_report_ref, control_kind, cost_table_version
- `decision_trace.jsonl`
  - per tick: world_obs_ref, energy_before, interoception_value, w_death, chosen action_class, interaction_intensity, rng_state_ref
- `life_tick_summary.jsonl`
  - per tick: energy_before, action_cost, impedance_cost, energy_after, death_flag, evidence_refs for impedance inputs
- `errors.jsonl` (must exist, can be empty)


