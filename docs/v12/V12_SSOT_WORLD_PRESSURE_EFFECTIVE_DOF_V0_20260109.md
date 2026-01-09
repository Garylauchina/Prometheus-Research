# V12 SSOT — World Pressure via Effective Degrees of Freedom (EDoF) v0 — Candidate Contract — 2026-01-09

Additive-only. This SSOT defines a **measurement-only** candidate tool to produce a **continuous** world-pressure readout.

Status: **CANDIDATE** (must pass a do-or-die calibration trial; otherwise the tool exits).

---

## §0 Positioning / intent (frozen)

Goal:
- Measure how the world **continuously** compresses the agent’s effective action freedom, without introducing reward, optimization, or “better behavior”.

Why this exists:
- Local Reachability (feasible_ratio) behaves like a regime/boundary detector (strong quantile separation but weak continuous ordering).
- We need a more continuous geometric readout: **effective degrees of freedom** and its **collapse rate**.

Hard bans (inherits V12 red lines):
- No reward / PnL / ROI input.
- No rollout / planning / search.
- No “how to survive” narratives or decision guidance.
- No I-dimension expansion inside this tool.

---

## §1 Frozen object of study

We study a time series of **action attempt vectors** \(a_t \in \mathbb{R}^d\) (one vector per tick).

The tool measures:
- \( \mathrm{EDoF}(t) \): effective degrees of freedom of \(\{a_{t-W+1},...,a_t\}\) in a rolling window of size \(W\).
- \( \mathrm{EDoF\text{-}CR}(t) = -\Delta \mathrm{EDoF}(t) \): collapse rate (positive means “degrees of freedom are collapsing”).

EDoF is a geometric / correlation-structure readout, not a performance metric.

---

## §2 Minimal action vector definition (v0; frozen)

We define the per-tick attempt vector \(a_t\) from **decision_trace evidence** (Quant run output):

Let:
- `x1 = interaction_intensity` (proposed interaction intensity)
- `x2 = post_gate_intensity` (post-gate intensity)
- `x3 = 1 if action_allowed else 0`

Then:
- \(a_t = [x1, x2, x3]\) with \(d=3\).

Notes (frozen):
- We intentionally use a minimal, audit-friendly embedding.
- We do not use any reward, market return, or latent state.

---

## §3 EDoF definition (v0; frozen)

Given a window of vectors \(A = \{a_i\}_{i=1..W}\), compute the **correlation matrix** \(R \in \mathbb{R}^{d \times d}\) after per-dimension z-score normalization within the window.

Let \(\{\lambda_k\}_{k=1..d}\) be eigenvalues of \(R\) (non-negative, sum \(\approx d\)).

Define participation-ratio effective dimension:

\[
\mathrm{EDoF} = \frac{(\sum_k \lambda_k)^2}{\sum_k \lambda_k^2}
\]

Range: \([1, d]\).

EDoF collapse rate:
- \(\Delta \mathrm{EDoF}(t) = \mathrm{EDoF}(t) - \mathrm{EDoF}(t-1)\)
- \(\mathrm{EDoF\text{-}CR}(t) = -\Delta \mathrm{EDoF}(t)\)

We do not force monotonicity; we only measure it.

---

## §4 World pressure proxy (v0; frozen)

World pressure proxy per tick:
- `u_t = interaction_impedance.metrics.world_u`

---

## §5 Evidence contract (v0; frozen)

Required files per run_dir:
- `decision_trace.jsonl` (1 record per tick)
- `interaction_impedance.jsonl` (1 record per tick; may not include tick_index)

Join key rule (fail-closed):
- Prefer explicit `tick_index` present in both files (1:1 join).
- If `interaction_impedance.jsonl` lacks `tick_index`, **strict implicit ordering join** is allowed only if:
  - record counts match
  - `ts_utc` matches line-by-line between the two files
  - and the tool records this join semantic in its report

---

## §6 Falsification / stop rule (v0; frozen)

This candidate tool is **rejected** if the do-or-die calibration trial fails under its frozen thresholds.

Stop rule:
- If rejected ⇒ tool exits; no patching inside the same claim.


---

## §7 Operational status (append-only)

As of 2026-01-09:
- Trial-6 BTC do-or-die calibration verdict: **FAIL**.
- Therefore this candidate tool is **REJECTED** for “continuous world-pressure gauge” under the frozen v0 action embedding.

References:
- Trial-6 pre-reg: `docs/v12/pre_reg/V12_WORLD_PRESSURE_EDOF_TRIAL6_BTC_DO_OR_DIE_CALIBRATION_V0_20260109.md`
- Trial-6 artifacts: `docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/README.md`
