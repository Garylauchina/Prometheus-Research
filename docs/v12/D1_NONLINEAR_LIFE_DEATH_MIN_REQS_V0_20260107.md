# D1 — Nonlinear life/death adjudication: minimal necessary conditions (killable) v0 — 2026-01-07

Additive-only. This document defines **minimum necessary conditions** for starting D1.
It does not justify them; it defines what must be true, and how to falsify / stop.

---

## §0 Hard red lines (non-negotiable)

- **No explicit reward / ROI / profit / utility optimization** may enter death/energy updates.
- **Energy is an internal survival budget**; death is `energy <= 0`.
- **Energy updates are allowed only from**:
  - `action_cost`
  - `impedance_cost`
- **Strict evidence**:
  - strict JSON / JSONL (one valid JSON object per line; no comments)
  - fail-closed on missing evidence (stop)

---

## §1 What “nonlinear adjudication” means (minimal)

We require at least one **nonlinear mapping** from a time-coupled observable to a survival-impacting cost term:

- `cost_t = f(z_t)` where:
  - `z_t` is a time-coupled observable (depends on ordered history, not only marginals)
  - `f` is nonlinear (not affine / not piecewise-affine with fixed slope everywhere)

Allowed examples of nonlinearity (illustrative, not prescriptive):
- threshold + saturation
- sigmoid / tanh
- convex penalty after a breakpoint
- hysteresis with two thresholds (enter/exit)

Forbidden:
- any mapping that directly encodes “success” proxies (PnL, ROI, Sharpe, realized profit, equity)

---

## §2 Minimal necessary conditions (D1 entry gate)

### C1) Observable must be time-coupled and auditable

- `z_t` must be computable from **evidence-logged world input** and/or **evidence-logged interaction events**.
- `z_t` must be joinable to a run via run_id and tick index (or event_id).

Fail world (kill condition):
- if `z_t` cannot be recomputed from evidence (observer cannot reproduce), D1 is `NOT_MEANINGFUL`.

### C2) Nonlinearity must be explicit, bounded, and versioned

- `f` must be explicitly specified in a SSOT-style contract (with version id).
- `f` output must be bounded to prevent hidden “infinite punish/reward” tricks:
  - `cost_t ∈ [0, cost_max]` (frozen)

Fail world:
- if `f` is not fully specified or not bounded, stop (`FAIL (contract_drift)`).

### C3) Negative controls must exist and be run-able (fail-closed)

At minimum:
- **Time order break control** (shuffle or time reversal) must be defined for the D1 observable.
- A run must record the control kind unambiguously (e.g., `world_transform.kind`).

Fail world:
- if we cannot construct a valid negative control without changing other semantics, stop (D1 blocked).

### C4) Attribution isolation: no hidden coupling to “success”

We must be able to prove by inspection of evidence schema that:
- energy deltas do not contain any “profit-like” inputs
- no account equity or realized PnL flows into `cost_t`

Fail world:
- if any profit-like signal enters energy, D1 is invalid (hard stop).

---

## §3 Killable hypotheses (D1 targets; minimal set)

### H-D1-1 (existence): nonlinear + time-coupled mapping can produce separable survival distributions without reward

- **Claim**: there exists at least one `f(z_t)` satisfying §2, such that survival distributions diverge measurably under a pre-registered metric.
- **Kill condition**: under a frozen D1 protocol and across two independent world inputs (both W0=PASS), all tested `f` (pre-registered family) fail to produce measurable separation beyond a pre-registered threshold.

### H-D1-2 (nonlinearity necessity candidate): linear adjudication cannot do it in unstructured worlds

- **Claim**: for a formal “unstructured world class” (pre-registered), any linear / quasi-linear mapping fails to produce stable separation.
- **Kill condition**: find one linear mapping that produces stable separation under the same protocol.

Notes:
- This is a **candidate** hypothesis; do not treat it as concluded from D0.

---

## §4 Stop conditions (“never try again under same axioms”)

We stop D1 attempts under this axiom set if any occurs:

- **S1**: red line violation (any profit/ROI/utility enters energy) ⇒ stop permanently for this branch.
- **S2**: protocol unreliability repeats (evidence missing / non-strict JSONL / controls invalid) ⇒ stop until infrastructure fixed.
- **S3**: after N independent campaigns (pre-registered; N must be written before running), H-D1-1 fails with `NOT_MEASURABLE` or `FAIL` in all campaigns ⇒ stop and redesign axioms/observable.

---

## §5 Required evidence (minimum schema)

Per run:
- `run_manifest.json` with:
  - `d1.enabled=true`
  - `d1.observable_name`
  - `d1.f_version`
  - `d1.control_kind`
- `life_tick_summary.jsonl` (or equivalent) including:
  - tick index
  - energy_before / delta_energy / energy_after
  - cost components (`action_cost`, `impedance_cost`) and their sources
  - `z_t` (or reference allowing recomputation)

Strict JSONL required.


