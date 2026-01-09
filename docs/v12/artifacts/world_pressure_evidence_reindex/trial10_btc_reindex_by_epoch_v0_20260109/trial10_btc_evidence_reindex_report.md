# Trial-10 — BTC Evidence Re-indexing by Consensus Epochs (world_u boundaries) — Result Summary (2026-01-09)

Consensus epoch boundaries (frozen, N=10000):
- `[644, 3837, 5812, 6339, 6676]`

What we computed (descriptive only):
- Within each epoch:
  - world_u distribution
  - gate statistics: attempted_rate, block_rate, downshift_rate, suppression distribution
  - fail-closed event density from errors.jsonl
- Between epochs:
  - effect sizes only (Cohen’s d for world_u/suppression; absolute differences for rates)

Do-or-die thresholds (frozen by pre-reg):
- Need >=2 distinguishable epoch pairs covering >=3 epochs, where:
  - min_seed |d_world_u| >= 0.30 AND
  - (min_seed |Δblock| >= 0.05 OR min_seed |Δdownshift| >= 0.05 OR min_seed |d_suppression| >= 0.30)

Verdict:
- **FAIL** (distinguishable_pairs=0)

High-signal audit note:
- world_u differences across epochs are strong (e.g., top-ranked pair has min_seed |d_world_u| ≈ 1.06),
  but gate metrics differences are small (|Δblock|≈0.015, |Δdownshift|≈0.007, |d_suppression|≈0.165), therefore they do not meet the “evidence-chain meaning” requirement.

Interpretation (within Trial-10 scope):
- Consensus epochs are valid as an **annotation coordinate system** (Trial-9 PASS),
  but under current evidence, they do **not** induce stable, cross-seed distinguishable structure in gate / fail-closed statistics at the frozen thresholds.

