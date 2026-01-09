# V12 SSOT — World Pressure via Gate Transfer Function (Suppression) v0 — Candidate Contract — 2026-01-09

Additive-only. This SSOT defines a **measurement-only** candidate tool to produce a **continuous** world-pressure readout using the already-audited gate outputs.

Status: **CANDIDATE** (must pass a do-or-die calibration trial; otherwise the tool exits).

---

## §0 Positioning / intent (frozen)

Goal:
- Produce a continuous pressure gauge by measuring **how the world/gate compresses proposed actions**.

We measure **a transfer function**, not reachability:
- Proposed intensity → post-gate intensity
- The compression amount is the readout.

Hard bans:
- No reward / PnL.
- No rollout / planning / search.
- No “improve behavior”; measurement only.
- No new knobs in Quant runner for this tool (posthoc only).

---

## §1 Frozen object of study

Per tick \(t\), we study:
- proposed intensity: `interaction_intensity`
- realized intensity after gate: `post_gate_intensity`

Define the per-tick suppression scalar:

\[
\mathrm{suppression}(t) = 
\begin{cases}
0 & \text{if } \mathrm{interaction\_intensity}(t)=0 \\\\
1 - \frac{\mathrm{post\_gate\_intensity}(t)}{\mathrm{interaction\_intensity}(t)} & \text{otherwise}
\end{cases}
\]

Range requirement (fail-closed):
- suppression(t) must be within [0,1] up to small numeric tolerance.

---

## §2 World pressure proxy (v0; frozen)

World pressure proxy per tick:
- `u_t = interaction_impedance.metrics.world_u`

---

## §3 Evidence contract / join rule (v0; frozen)

Required files per run_dir:
- `decision_trace.jsonl` (1 record per tick)
- `interaction_impedance.jsonl` (1 record per tick; may not include tick_index)

Join rule (fail-closed):
- Strict implicit ordering join **with line-by-line `ts_utc` equality** between the two files.
- Record-count mismatch or any `ts_utc` mismatch ⇒ FAIL.

---

## §4 Falsification / stop rule (v0; frozen)

This candidate tool is rejected if the do-or-die calibration trial fails under frozen thresholds.

Stop rule:
- If rejected ⇒ tool exits; no patching inside the same claim.


---

## §5 Operational status (append-only)

As of 2026-01-09:
- Trial-7 BTC do-or-die calibration verdict: **FAIL**.
- Therefore this candidate tool is **REJECTED** for “continuous world-pressure gauge” under the frozen v0 definition.

References:
- Trial-7 pre-reg: `docs/v12/pre_reg/V12_WORLD_PRESSURE_GATE_TRANSFER_TRIAL7_BTC_DO_OR_DIE_CALIBRATION_V0_20260109.md`
- Trial-7 artifacts: `docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/README.md`
