# Trial-2 ratio explosion cases (audit note)
- generated_at_utc: 2026-01-07T05:09:33.251245Z
- input: `trial_2_sweep_summary.json` sha256=f95425801ab5d1c57f73309d22a5b4cb32c1a0099b9a3ba184a7f3cde4d420c9
- pair_count: 60
- case_count: 5

## Meaning (factual)
- These cases occur when `gap_on` is near 0, causing `denom=max(1,abs(gap_on))` to clamp and ratios to become extreme.
- They are kept for audit; they do not override the pre-registered threshold rule by themselves.

## Top cases (by |reduction_ratio|)
- g_hi=0.65 seed=3019 gap_on=-2 gap_shuffle=-194 rr=96.000000 flags=abs_gap_on_lt_10,reduction_ratio_gt_5 on=run_temporal_only_falsification_v0_20260107T045502Z_ns1767761702192052000_seed3019_on shuffle=run_temporal_only_falsification_v0_20260107T045502Z_ns1767761702713844000_seed3019_shuffle
- g_hi=0.65 seed=3013 gap_on=-5 gap_shuffle=-285 rr=56.000000 flags=abs_gap_on_lt_10,reduction_ratio_gt_5 on=run_temporal_only_falsification_v0_20260107T045455Z_ns1767761695411324000_seed3013_on shuffle=run_temporal_only_falsification_v0_20260107T045455Z_ns1767761695905608000_seed3013_shuffle
- g_hi=0.6 seed=3018 gap_on=38 gap_shuffle=-188 rr=5.947368 flags=reduction_ratio_gt_5 on=run_temporal_only_falsification_v0_20260107T045438Z_ns1767761678969780000_seed3018_on shuffle=run_temporal_only_falsification_v0_20260107T045439Z_ns1767761679612807000_seed3018_shuffle
- g_hi=0.55 seed=3013 gap_on=65 gap_shuffle=-285 rr=5.384615 flags=reduction_ratio_gt_5 on=run_temporal_only_falsification_v0_20260107T045413Z_ns1767761653536234000_seed3013_on shuffle=run_temporal_only_falsification_v0_20260107T045414Z_ns1767761654009655000_seed3013_shuffle
- g_hi=0.6 seed=3013 gap_on=67 gap_shuffle=-285 rr=5.253731 flags=reduction_ratio_gt_5 on=run_temporal_only_falsification_v0_20260107T045433Z_ns1767761673950052000_seed3013_on shuffle=run_temporal_only_falsification_v0_20260107T045434Z_ns1767761674437774000_seed3013_shuffle
