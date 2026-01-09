# Local Reachability — Trial-1 Seed Sweep Expanded v0 (2026-01-09)

This bundle is generated in the Research repo to avoid overwriting Quant run_dir artifacts.

## What it contains

- `source_run_dirs.txt`: absolute paths of source Quant run_dirs (30)
- `source_map.json`: mapping from source run_dir -> artifact run_dir
- `runs/<run_id>/local_reachability.jsonl`: Trial-1 volatility-proxy output (strict JSONL)
- `run_dirs_file.txt`: list of artifact run dirs consumed by the aggregator
- `aggregate_report.json`: multi-run descriptive summary

## Observed outcome (descriptive)

- `aggregate.per_run_mean_feasible_ratio` is constant across all 30 runs:
  - min = p50 = p99 = max = mean = 0.7508444444444444

Interpretation is governed by the Trial-1 seed sweep pre-reg.
