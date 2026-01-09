# V12 SSOT — World Pressure as Boundary Signal (Changepoint Detector on world_u) v0 — 2026-01-09

Additive-only. This SSOT defines a **measurement-only** tool framing for world pressure:

> Under the current `world_u` semantics, “pressure” is treated as a **boundary / regime signal**, not a continuous monotone gauge.

Status: **CANDIDATE** (must pass a do-or-die calibration trial; otherwise the tool exits).

---

## §0 Positioning / intent (frozen)

Goal:
- Detect **change points** (regime boundaries) in `world_u` within a single world, with strict auditability.

Non-goals:
- Not a continuous gauge.
- Not a behavioral optimizer.
- Not a reward signal.

Hard bans:
- No reward / PnL.
- No rollout / planning / search.
- No “best behavior” discussion.
- No cross-dataset comparisons inside this tool claim.

---

## §1 Frozen observable

Per tick t:
- `u_t = interaction_impedance.metrics.world_u`

We detect a set of boundaries (changepoints):
- `CP = {t_1, t_2, ...}` where each `t_k` is an index in [0, N).

Interpretation:
- Boundaries are not “good/bad”; they are **world regime switches** under the current proxy.

---

## §2 Evidence contract (v0; frozen)

Required per run_dir:
- `interaction_impedance.jsonl` (strict JSONL, 1 record per tick)

Required fields per record:
- `ts_utc` (string, non-empty)
- `metrics.world_u` (number)

Fail-closed:
- missing file / invalid JSONL / missing required fields ⇒ FAIL
- `N < 1000` ⇒ FAIL (insufficient evidence)

Join:
- This tool uses only `interaction_impedance.jsonl` (no join to other files).

---

## §3 Changepoint algorithm contract (v0; frozen)

We use **greedy binary segmentation** with SSE cost and a penalty term (auditable, stdlib-only).

Definitions:
- For a segment [i, j) with values u_i..u_{j-1}:
  - `SSE(i,j) = Σ(u^2) - (Σu)^2 / (j-i)`
- A split at k yields:
  - `gain = SSE(i,j) - (SSE(i,k) + SSE(k,j) + beta)`

Constraints:
- `min_segment_len = 200`
- `max_changepoints = 10`
- penalty `beta` is frozen per trial (see pre-reg).

Stop criterion:
- If best gain ≤ 0 ⇒ stop splitting that segment.

---

## §4 Falsification / stop rule (v0; frozen)

This candidate tool is rejected if the do-or-die calibration trial fails under its frozen thresholds.

Stop rule:
- If rejected ⇒ tool exits; no patching inside the same claim.


---

## §5 Operational status (append-only)

As of 2026-01-09:
- Trial-8 BTC do-or-die changepoint verdict: **PASS**.
- Therefore `world_u` is accepted as a **boundary/regime signal** (not a continuous gauge) under this evidence contract.

References:
- Trial-8 pre-reg: `docs/v12/pre_reg/V12_WORLD_PRESSURE_BOUNDARY_TRIAL8_BTC_DO_OR_DIE_CHANGEPOINT_V0_20260109.md`
- Trial-8 artifacts: `docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/README.md`
