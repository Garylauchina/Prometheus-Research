# V12 Pre-reg — Local Reachability — Trial-2 (Impedance probe; M-measurable) v0 — 2026-01-09

Status: **PRE-REGISTERED**

This document is **append-only** after pre-registration. Completion anchors must be appended.

Cross-links:
- SSOT: `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Trial-1 (Volatility proxy; E-only): `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_VOLATILITY_PROXY_V0_20260109.md`
- Trial-1 Seed Sweep: `docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL1_SEED_SWEEP_V0_20260109.md`

---

## 0. Purpose (frozen)

Trial-1 volatility proxy (E-only) was **trivial across seeds** under the same dataset, therefore rejected as a useful variability lens.

Trial-2 introduces a **measurement-only impedance probe** to ensure M is **measurable per tick**, and uses M as the reachability compression source.

Hard boundaries (frozen):
- no rollout / planning / search
- no “better/worse agent” judgments
- no reward / PnL / ROI involvement
- death remains ex-post only (disabled in this trial)
- the probe MUST NOT change survival adjudication or any reward ledger

---

## 1. Frozen inputs

Operate on a Quant run_dir that contains (required):

- `run_manifest.json`
- `decision_trace.jsonl`
- `interaction_impedance.jsonl` (must be measurable per tick; see §2)

No new world data is introduced.

---

## 2. Frozen measurability requirement (M-probe)

To avoid the “no attempts ⇒ impedance NOT_MEASURABLE” deadlock, the runner MUST provide:

- `probe_attempts_per_tick = 1` (frozen)

Definition (frozen):
- A **probe attempt** is a logged interaction attempt used only to measure impedance.
- Probe attempts are recorded into evidence (e.g., `order_attempts.jsonl`), and are included in `interaction_impedance.metrics.order_attempts_count`.
- Probe attempts MUST NOT:
  - place real orders
  - change survival energy
  - create reward
  - alter gate logic (the gate still gates agent actions only)

Acceptance (frozen):
- For all ticks `t`, `interaction_impedance.metrics.order_attempts_count >= 1`
- Therefore `interaction_impedance.verdict == PASS` per tick.

If this cannot be satisfied, Trial-2 is **NOT_READY** (stop; no patching within this claim).

---

## 3. Frozen neighborhood definition \(A(s)\)

We keep the same neighborhood size:

- `N = 9`

Trial-2 does **not** require using agent intensity to define candidates; only neighborhood width is measured.

---

## 4. Frozen M-only compression proxy (no thresholds)

At each tick, read `interaction_impedance.metrics`:

- `attempts = order_attempts_count`
- `rejects = reject_count`
- `rate_limited = rate_limited_count`
- `http_err = http_error_count`
- `lat_ms = avg_ack_latency_ms` (may be null)

Define rates (frozen):

- `rej_rate = rejects / max(1, attempts)`
- `rl_rate  = rate_limited / max(1, attempts)`
- `http_rate = http_err / max(1, attempts)`
- `lat_norm = clamp(lat_ms / latency_hi_ms, 0..1)` with `latency_hi_ms = 200.0` (frozen)
  - if `lat_ms` is null ⇒ `lat_norm = 0.0`

Frozen mapping (monotone compression):

- `L_m = exp(-(a*rej_rate + b*rl_rate + c*http_rate + d*lat_norm))`
- coefficients (frozen):
  - `a=2.0, b=3.0, c=2.0, d=1.0`

No threshold-based decision is used here; this is a lens definition.

---

## 5. Frozen reachability set size

- `candidate_count = N`
- `feasible_count = floor(N * L_m)`
- `feasible_ratio = feasible_count / N`

---

## 6. Frozen outputs

Write:

- `<RUN_DIR>/local_reachability.jsonl` (strict JSONL, append-only)

Required SSOT v0 schema must be satisfied.

Reason codes (allowed, deterministic):
- `reachability_proxy:impedance_exp`
- `reachability_proxy:coeffs:a2_b3_c2_d1`
- `reachability_proxy:latency_hi_ms=200`
- `reachability_proxy:probe_attempts_per_tick=1`

Graph optional fields: disabled (nulls).
Death label: disabled (nulls).

---

## 7. Falsification criteria (Trial-2)

Reject Trial-2 as a useful measurement lens if any triggers:

- **Probe drift**: probe attempts are found to affect survival or rewards (hard failure).
- **Triviality across seeds**: per-run mean feasible_ratio is identical across seeds for the same dataset (no usable variability).
- **Epoch sensitivity failure**: reachability compression changes radically under different epoch chunking without world contract change.

Stop rule (hard):
- If triggered ⇒ stop (no patching within this claim).

---

## 8. Completion anchors (append-only)

### 8.1 Run anchors

- quant_run_dir:
- probe_config:
- command:
- local_reachability_jsonl:

### 8.2 Verification / summary

- verifier_verdict:
- summary_json_path:
- notes:

