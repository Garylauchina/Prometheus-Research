# V12 — Survival Space (E+M) Experiment Execution Checklist v0 — 2026-01-08

Additive-only. This is an execution/acceptance checklist (no narrative).
This checklist operationalizes the SSOT contract:
- `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md`

---

## §0 Run manifest: goals / non-goals (required)

`run_manifest.json` MUST include an explicit declaration (strings are frozen keywords; additive-only):

- `experiment_goal`:
  - `verify_survival_space_shapes_actionability`
- `non_goals` (array, MUST include all):
  - `no_rollout`
  - `no_planning`
  - `no_reward`
  - `no_learning`
  - `no_parameter_adaptation`

---

## §1 Minimal viable closed-loop pipeline (must run end-to-end)

Required chain (must be replayable):

- E (`market_snapshot.jsonl`) + M (`interaction_impedance.jsonl`)
  → `survival_space.jsonl`
  → action gate (hard constraint)
  → agent (script/random only; no learning)
  → `order_attempts.jsonl`
  → impedance aggregation (`interaction_impedance.jsonl`)

### §1.1 New output required: `survival_space.jsonl` (strict JSONL)

Per tick MUST include join keys:
- `ts_utc`
- `snapshot_id` (references `market_snapshot.jsonl.snapshot_id`)
- `account_id_hash`

And Survival Space fields (see SSOT §1.2):
- `L_liq`, `L_imp`, `L=min(..)` + masks + reason_codes

Hard rule:
- `L` is used only as a **gate boundary** (never as score/utility).

### §1.2 Gate must be hard constraint

Gate evidence MUST write explicit fields in `decision_trace.jsonl` or `order_attempts.jsonl`:
- `action_allowed` (bool)
- `gate_reason_codes` (array[string])
- `intensity_cap` (optional; enum/int with frozen range)

Forbidden:
- any “soft penalty / scoring / ranking”.

---

## §2 Ablations (first-class; mandatory)

`run_manifest.json` MUST include:

```json
{
  "ablation": {
    "survival_space": {
      "enabled": true,
      "mode": "full | no_m | no_e | null"
    }
  }
}
```

Semantics (must match SSOT §5.2):
- `full`
- `no_m`: `L_imp=null`, `L_imp_mask=0`, `L_imp_reason_codes=["ablation:M_off"]`, and `L=L_liq`
- `no_e`: symmetric, and `L=L_imp`
- `null`: all `L_*_mask=0`, gate should be effectively “always allowed” (control for linear timer / fake loop)

Fail-closed:
- if ablation enabled but any required file/field missing ⇒ `NOT_MEASURABLE` or `FAIL` (per verifier rules).

---

## §3 Minimal agent (must be non-learning)

Agent must be “unarguably dumb”:
- `interaction_intensity ∈ {0,1,2,3}` (or frozen equivalent)
- default policy: scripted or random
- when gate triggers: forced downshift or forbidden

Forbidden:
- any learning, optimization, or parameter adaptation based on `L` history.

---

## §4 Evidence join must work (core acceptance)

One-shot join requirements:
- `decision_trace.market_snapshot_id` → `market_snapshot.snapshot_id`
- `decision_trace` → `survival_space` (same tick, same `snapshot_id`, same `account_id_hash`)
- `order_attempts` → `decision_trace` (via `decision_ref` or stable join key such as `clOrdId`)
- `interaction_impedance.evidence_refs` can point back to `order_attempts` / `okx_api_calls`

---

## §5 Engineering acceptance: 4 structural signals (not KPI)

After each ablation group (`full/no_m/no_e/null`), produce `report.json` containing at least:

1) Gate trigger rate
   - `null` should be near 0 (gate rarely/never blocks)
2) Exhaustion attribution diversity
   - `first_exhaust_dim` should not be always the same in `full`
3) Action–dissipation coupling
   - in `full`, action intensity should correlate with `dL_imp/dt`
   - in `no_m`, this should disappear or weaken materially
4) Nonlinear collapse behavior
   - near `L→0`, action set should shrink in stages (hard blocks), not uniform slow-down

If 2–3 signals are present ⇒ mechanism exists in this regime.
If none ⇒ record as “blocked path” (append-only; no post-hoc rescue).

---

## §6 Frozen parameters (avoid debate)

- `seeds`: 100–300
- `steps`: 10k–50k
  - start with 10k for iteration; expand to 50k only after signals appear
- `run_kind`: `modeling_tool` (per isolation rules)
- each run MUST print: rerun command, runs_root, run_id

---

## §7 Code review checklist: three hard bans

- Ban 1: do NOT feed `L` into an agent “strategy selector” as soft optimization (only gate)
- Ban 2: do NOT EMA/smooth `L` (it changes dissipation into “recharge”)
- Ban 3: do NOT runtime-adapt thresholds/collapse params (that is KPI tuning)

