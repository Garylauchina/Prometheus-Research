# Trial-8 — World Pressure as Boundary Signal — BTC Do-or-Die (Changepoint) — Result Summary (2026-01-09)

World proxy:
- `u_t = interaction_impedance.metrics.world_u`

Detector (frozen):
- greedy binary segmentation (SSE + beta)
- `min_segment_len=200`, `max_changepoints=10`, `beta=0.5`

Acceptance (frozen):
- per-run: `cp_count>=1`, `R2>=0.05`, median adjacent-mean jump >= 0.05*std(u)
- cross-seed: first K changepoints align (normalized position std <= 0.05)

Verdict:
- **PASS** (3/3 runs pass per-run checks; cross-seed alignment check passes)

Example (seed 71001):
- changepoints: `[644, 3837, 5812, 6339, 6676]`
- R2 ≈ 0.0527

Interpretation (within Trial-8 scope):
- Under current `world_u` semantics, it is **measurable** as a boundary/regime signal in BTC single-world evidence.

