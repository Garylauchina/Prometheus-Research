# Trial-10 — BTC Evidence Re-indexing by Consensus Epochs (world_u boundaries) — Archived Artifacts (v0, 2026-01-09)

Purpose (descriptive audit only):
- Re-index existing evidence-chain statistics by Trial-9 consensus epoch boundaries.
- Produce per-epoch descriptive stats and between-epoch effect sizes.
- No prediction. No mechanism changes.

Inputs (frozen):
- boundaries: `[644, 3837, 5812, 6339, 6676]`
- run_dirs: `run_dirs.txt` (3 seeds, full only)

Tool:
- `tools/v12/reindex_btc_evidence_by_consensus_epochs_v0.py`

Outputs:
- `per_run_epoch_metrics.json` (world_u + gate + fail-closed per epoch per run)
- `between_epoch_effects.json` (all epoch pairs, per-seed effects)
- `between_epoch_effects_top50.json` (compact ranking for audit)
- `aggregate_verdict.json` (do-or-die verdict)
- `stdout_aggregate.json` (stdout mirror)

