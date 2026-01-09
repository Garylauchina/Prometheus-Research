# Trial-9 — BTC Epoch Annotation (from world_u changepoints) — Result Summary (2026-01-09)

Input boundary signal:
- Trial-8 changepoints on `u_t = interaction_impedance.metrics.world_u`

Construction (frozen by pre-reg):
- Per-run epochs from each run’s ordered changepoints.
- Consensus epochs from the first K changepoints (K = min cp_count across runs), using median normalized position.

Verdict:
- **PASS**

Consensus (K=5, N=10000):
- boundaries: `[644, 3837, 5812, 6339, 6676]`

Artifacts:
- `epoch_candidates.json`
- `per_run_epoch_stats.json`
- `consensus_epoch_stats_by_run.json`

Meaning (annotation-only):
- These boundaries are accepted as **epoch candidates** for audit / labeling purposes.
- They do not change any mechanism or evaluation semantics.

