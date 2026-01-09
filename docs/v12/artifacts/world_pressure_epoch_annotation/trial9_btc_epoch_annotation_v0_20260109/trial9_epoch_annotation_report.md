# Trial-9 — BTC Epoch Annotation (from world_u changepoints) — Result Summary (2026-01-09)

**Demoted (SSOT rule)**: these epoch candidates are **annotation-only**; **prohibited** as downstream controls/conditioners per Trial-10 FAIL.  
Reference: `docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md` (§6) and Trial-10 report `docs/v12/artifacts/world_pressure_evidence_reindex/trial10_btc_reindex_by_epoch_v0_20260109/trial10_btc_evidence_reindex_report.md`.

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

