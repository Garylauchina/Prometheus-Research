# V11 Incident — Old Runner Left Running (Observation Pollution) — 2025-12-30

## Summary (facts only)

During Step89 investigations, we discovered that the VPS still had long-running containers from older runs. This can pollute observation (web UI shows periodic orders) and makes any “truth acceptance” non-attributable unless we explicitly stop all background runners before running a fresh acceptance run.

This document is append-only and records the minimal facts needed for audit traceability.

## Environment

- **Host**: VPS (Vultr)
- **Observation**: OKX web UI showed periodic orders at ~15-minute cadence, consistent with a “tick_seconds=900” style legacy runner.

## Evidence (operator output)

### Docker containers found running (UTC time)

- **UTC timestamp**: 2025-12-30 18:05:55 UTC
- **docker ps** reported two containers:
  - `v10_run_20251225_185454_g4_vps_step1_96tick_a6f9519`
    - image: `ghcr.io/garylauchina/prometheus-quant@sha256:f77df35fe8d5a68166ed67f7b044446078ec93a0f03fd6746d9bdf67baa6b11c`
    - command: `v10-stage1`
    - running_for: ~4 days
  - `dreamy_dijkstra`
    - image: `prometheus-quant:v11-fix-errors-jsonl`
    - command: `python3 -`
    - running_for: ~2 hours

## Mitigation (stop-the-world)

### Stop legacy v10 container

- command: `docker stop v10_run_20251225_185454_g4_vps_step1_96tick_a6f9519`
- result: container stopped successfully

### Stop remaining v11 container

- command: `docker stop dreamy_dijkstra`
- result: container stopped successfully

### Post-condition

After the stop actions, `docker ps` showed **no running containers**.

## Required discipline (going forward)

Before any truth acceptance (Step89 or any real exchange write), we must:

- **Stop all background runners** on the same account/environment.
- **Record** `docker ps --no-trunc` output (before + after) as evidence.
- Preferably, have the runner write `build_git_sha` and `image_digest` into `run_manifest.json` so that “what produced the orders” is machine-attributable.


