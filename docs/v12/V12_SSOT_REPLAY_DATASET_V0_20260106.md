# V12 SSOT — Replay Dataset v0 (Exchange Snapshot → replay_truth baseline) — 2026-01-06

Goal: freeze a **replayable, machine-verifiable baseline dataset** built from real exchange snapshot evidence.

This dataset is used for “ugly baseline” experiments (death-only first; reproduction deferred), to stress-test **seed stability** and expose fake structures.

Additive-only.

---

## 0) Terms (frozen)

- **Exchange snapshot data**: canonical `market_snapshot.jsonl` samples obtained from a real exchange (OKX) via REST/WS, already recorded under a Quant `run_dir`.
- **Replay dataset**: a packaged, immutable dataset directory derived from a single source run_dir, intended to be replayed offline.
- **truth_profile**: for baseline experiments using this dataset, truth_profile is `replay_truth` (NOT live trading).

---

## 1) Non-goals (frozen)

- No order placement, no settlement, no account/bills truth. This is **world-input only**.
- No “high-frequency fantasies”: v0 targets coarse ticks (recommended: 1000ms).

---

## 2) Dataset identity (frozen)

### 2.1 dataset_id (recommended format)

`dataset_replay_v0_<inst_id>_<start_utc>_<end_utc>_<tick_ms>`

Example:

`dataset_replay_v0_BTC-USDT-SWAP_20260106T000000Z_20260106T013000Z_1000ms`

### 2.2 dataset_kind (required)

`dataset_kind = "replay_snapshot_v0"`

---

## 3) Required files (fail-closed)

All required files must exist. Missing any required file => dataset verifier FAIL.

- `dataset_manifest.json` (JSON object)
- `market_snapshot.jsonl` (strict JSONL, non-empty)

Optional but recommended (for auditability):
- `okx_api_calls.jsonl` (strict JSONL)
- `errors.jsonl` (strict JSONL; may be empty)
- `source_run_manifest.json` (copied from source `run_manifest.json`)

---

## 4) dataset_manifest.json contract (frozen)

Minimal required keys:

- `dataset_kind` (string, must be `"replay_snapshot_v0"`)
- `dataset_id` (string)
- `created_at_utc` (string, ISO8601 with `Z`)
- `source` (object):
  - `source_run_dir` (string, absolute path at build time)
  - `source_run_id` (string|null)
  - `source_run_kind` (string|null)
- `world_contract` (object):
  - `truth_profile` (string, must be `"replay_truth"`)
  - `inst_id` (string, v0 recommended fixed: `BTC-USDT-SWAP`)
  - `tick_interval_ms` (int, recommended: `1000`)
  - `schema_contract` (string, path of the canonical E schema SSOT)
- `files` (object):
  - at least `market_snapshot.jsonl` entry with:
    - `path` (string)
    - `sha256` (string)
    - `record_count` (int)

Hard rule: `dataset_manifest.json` must NOT contain secrets.

---

## 5) market_snapshot.jsonl contract (frozen by reference)

`market_snapshot.jsonl` must follow the canonical E schema:

- `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`

Additionally required by this replay dataset contract:

- **Single inst_id**: all records must have the same `inst_id` and match `world_contract.inst_id`
- **Monotonic ts**: `ts_utc` must be monotonic non-decreasing (no backward)
- **Fixed tick interval**: consecutive `ts_utc` deltas must be close to `tick_interval_ms` within a configured jitter budget

---

## 6) Acceptance: building the baseline dataset (v0)

PASS requires:

- Required files exist
- `market_snapshot.jsonl` is strict JSONL and non-empty
- `inst_id` constant and matches manifest
- `snapshot_id` unique within the dataset
- `ts_utc` monotonic non-decreasing
- Tick delta is within jitter budget for the vast majority of records (see verifier)

NOT_MEASURABLE (allowed, but not recommended for baseline) when:

- Evidence is strict and complete, but tick deltas show moderate drift/jitter beyond the preferred budget

FAIL when:

- Missing required files
- Non-strict JSONL
- `ts_utc` goes backward
- `snapshot_id` duplicates
- Mixed `inst_id`

---

## 7) Tools (frozen entry)

In Prometheus-Research:

- Build:
  - `python3 tools/v12/build_replay_dataset_v0.py --source_run_dir <QUANT_RUN_DIR> --output_root <DATASETS_ROOT>`
- Verify:
  - `python3 tools/v12/verify_replay_dataset_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --max_jitter_ms 500`


