# V12 SSOT — Survival Space (E + M) v1.0 — Minimal Contract — 2026-01-08

Additive-only. This document defines the minimal, auditable, ablationable contract for **Survival Space** in V12.
It is a contract for execution and verification (no narrative).

---

## §0 Positioning / design intent (frozen)

- Survival Space is a **measurement mechanism**, not a strategy, reward, or goal.
- Survival Space describes:
  - under the current world input and interaction reality, how much **actionability** remains.
- Survival Space does **not**:
  - predict the future
  - do rollout / planning / search
  - compare outcome “good vs bad”
- Death/extinction is only a **readout** after Survival Space is exhausted, not a shaping signal.

Scope of v1.0 (frozen):
- Uses **E (Exogenous market info)** and **M (Interaction impedance)** only.
- Does **not** introduce I (Position) as a primary dimension in v1.0.

Hard boundary (inherits V12 Life red-line):
- Reward / profit / ROI MUST NOT directly enter survival energy or death adjudication.  
  (Survival Space is observational; it must not become reward shaping.)

---

## §1 Canonical output (frozen)

### §1.1 Evidence file

- `survival_space.jsonl` (strict JSONL, append-only; one JSON object per line)

One line corresponds to one decision tick (or one `market_snapshot` alignment point).

### §1.2 Required fields (v1.0 frozen)

```json
{
  "ts_utc": "ISO8601",
  "snapshot_id": "string",
  "account_id_hash": "string",

  "L_liq": "number|null",
  "L_liq_mask": "0|1",
  "L_liq_reason_codes": ["string"],

  "L_imp": "number|null",
  "L_imp_mask": "0|1",
  "L_imp_reason_codes": ["string"],

  "L": "number|null",
  "L_mask": "0|1",
  "L_reason_codes": ["string"]
}
```

Constraints (frozen):
- All `L_*` must be in \([0,1]\) when measurable.
- `mask=0` ⇒ value MUST be `null`.
- Forbidden: using `0` to fake “not measurable”.

---

## §2 Input truths (frozen)

### §2.1 E — Market exogenous truth

- Source: `market_snapshot.jsonl`
- SSOT: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`

E is used only as a **world constraint source** (no prediction, no reward semantics).

### §2.2 M — Interaction impedance truth (account-local)

- Source: `interaction_impedance.jsonl`
- SSOT:
  - `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md` (§1.1.1)
  - `docs/v12/V12_SSOT_BASE_DIMENSIONS_EIM_V0_20260104.md` (§3)

M is an **account-local observation**, not a knob; the agent must not directly optimize it as an explicit objective.

---

## §3 Dimension definitions (frozen)

### §3.1 Liquidity Liberty — `L_liq` (from E)

Semantics (frozen wording):
- Under current *exogenous* market structure, the remaining space for executing a “minimal viable action” without irreversible friction.

Design constraints (frozen):
- Monotonic: market becomes “harder” ⇒ `L_liq` decreases.
- Nonlinear collapse: in some market states, `L_liq` may rapidly approach 0.
- Must not depend on profit / PnL / strategy outcome.
- Must depend only on auditable E fields.

NOT_MEASURABLE entry reasons (frozen vocabulary; additive-only):
- `not_measurable:market_snapshot_missing`
- `not_measurable:market_fields_insufficient`

### §3.2 Interaction Liberty — `L_imp` (from M)

Semantics (frozen wording):
- Under current account/connection conditions, the remaining space for actions to be **accepted** by the world (not rejected / rate-limited / swallowed by errors).

Input fields (v1.0 frozen entry; names align to impedance v0 schema):
- `order_attempts_count`
- `reject_count`
- `rate_limited_count`
- `http_error_count`
- `avg_ack_latency_ms` (if measurable)

Design constraints (frozen):
- Monotonic:
  - reject / rate-limit / error / latency ↑ ⇒ `L_imp` ↓
- Collapse:
  - `rate_limited_count > 0` OR sustained rejects ⇒ `L_imp` must significantly decrease (implementation must pre-register thresholds).
- Attributable:
  - `L_imp_reason_codes` must indicate major contributors (top factors).

NOT_MEASURABLE (inherits SSOT vocabulary; references frozen sources):
- `not_measurable:impedance_no_attempts`
- `not_measurable:impedance_missing_api_calls`
- `not_measurable:impedance_truth_missing`

---

## §4 Aggregation rule (frozen)

### §4.1 Total Survival Space — `L`

Primary rule (frozen):

\[
L = \min(L\_{liq}, L\_{imp})
\]

Rationale (frozen, non-narrative):
- shortest board dominates (“气” / liberty bottleneck)
- forces attribution: which dimension exhausted first
- avoids weighted-sum degenerating into a linear timer

### §4.2 Mask propagation (frozen)

- If either `L_liq_mask=0` OR `L_imp_mask=0`:
  - `L_mask=0`
  - `L=null`
  - `L_reason_codes` MUST include the source dimension reason(s).

---

## §5 Ablation discipline (frozen)

### §5.1 Run manifest switches (required; frozen)

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

### §5.2 Ablation semantics (frozen)

- `full`:
  - `L = min(L_liq, L_imp)`
- `no_m`:
  - `L_imp_mask=0`
  - `L = L_liq`
  - reason: `ablation:M_off`
- `no_e`:
  - `L_liq_mask=0`
  - `L = L_imp`
  - reason: `ablation:E_off`
- `null`:
  - all `L_*_mask=0`
  - reason: `ablation:survival_space_null`

Fail-closed (frozen):
- if `ablation.survival_space.enabled=true` but required fields are missing ⇒ `FAIL` or `NOT_MEASURABLE` (per verifier; missing evidence must not silently pass).

---

## §6 Verifier rules (frozen entry)

A run is **FAIL** if any holds:
- `survival_space.jsonl` missing OR not strict JSONL
- mask discipline violated (null/0 mixing, mask-value mismatch)
- ablation mode inconsistent with emitted fields

A run is **NOT_MEASURABLE** if any holds:
- input truths (E or M) are `NOT_MEASURABLE` under their SSOT/verifier
- ablation explicitly disables a dimension and marks it correctly

---

## §7 Explicit non-goals (frozen)

Survival Space v1.0 does **not** do:
- reward / utility / value estimation
- rollout / planning / search
- reproduction / copying / genome expansion
- I (Position) dominated modeling (deferred to v1.1+)

---

## §8 Upgrade path (non-frozen notes; additive-only)

- v1.1: introduce I (Position Liberty) as a third dimension (still via `min`)
- v2: allow structural dependencies between dimensions (still must not introduce reward→death)

---

Frozen sentence (recommended for README; non-narrative):

> Survival Space does not tell the agent what is good. It only tells the system what is still possible.

