# V10 VPS Development Guide (English) / VPS版本开发指导（中文）

## 0) Purpose / 目的

**English (primary)**: This document defines a **safe, auditable, deployable** VPS development workflow for V10.  
It is intentionally **engineering-first**: reproducibility, evidence integrity, rollback, and minimal privilege.

**中文（辅助）**：本文用于指导 V10 在 VPS 上的开发与部署，目标是：**安全、可审计、可回滚、可复核**。  
它是工程文档，不讨论“如何赚钱”，只讨论“如何保证证据链与运行可靠性”。

---

## 1) Non-negotiable principles / 不可动摇的原则

## Terminology / 术语对照（减少沟通成本）

- **Ballast** (stabilizers) / **压舱石**：系统的稳定底盘。目标是降低尾部风险与灭绝概率（不要求一定赚钱，但不能靠“零交易”逃避压力）。
- **Contributors** / **盈利贡献者**：提供可复核的正贡献（更接近“可重复现金流”，不要求极端峰值）。
- **Champions** / **旗手**：极少数在特定窗口显著拉开差距的尖峰个体（必须可追责、可复盘，不能成为系统炸弹）。

### P1. Core invariance / Core不变

- **Must not modify**: `prometheus/v10/core/` (world rules, capital model, features, decision logic, state machine).
- **No monkey patch / runtime injection**.

中文：**不动 core，不做动态替换**。任何产品化工作只能在外壳层（ops/runner/observability）完成。

### P2. Ecological fences ≠ decision logic / 生态围栏≠状态机

- Thresholds may exist only as:
  - lifecycle rules (death/repro/collapse/reboot),
  - auditing labels/metrics,
  - outer-shell rate limiting / kill switch,
  - real physical exchange constraints (margin/liquidation rules).
- They **must not** be injected into the decision path to “guide trading”.

中文：阈值可以存在，但只能当环境/审计/生死规则；决策必须保持 `Genome + Features -> Action`。

### P3. Evidence-first / 证据链优先

Every run must be reviewable by artifacts, not stories:

- `run_manifest.json` (version/config/environment)
- summary JSON (aggregates + invariants)
- execution fingerprint (demo/live)
- agent-level behaviors + genomes alignment (when enabled)

---

## 2) Stages / 分阶段推进（推荐）

### C0 — Docker local (developer laptop) / 本地Docker准VPS

Goal: A reproducible container that can start/stop, write artifacts, and rollback.

### C1 — VPS stage-1 sandbox (high-frequency evolution) / VPS一级沙盒（高频进化器）

Goal: generate a **Stage-1 gene pool** (append-only) under controlled friction model.

### C2 — VPS stage-2 sandbox (mid/low-frequency validation) / VPS二级沙盒（中低频复核器）

Goal: read **snapshots** from stage-1 pool for cold start, and run batch verification; produce stage-2 pool.

**Important**: Stage-2 must read stage-1 **snapshots**, never the live pool.

---

## 3) Architecture (minimal) / 最小架构

### Components / 组件

- **stage1_sandbox** (container): runs the high-frequency evolution runner
- **stage2_sandbox** (container): runs the mid/low-frequency verifier (later)
- **artifact volumes** (host-mounted):
  - `/var/lib/prometheus-quant/runs`
  - `/var/lib/prometheus-quant/pools`
  - `/var/log/prometheus-quant`
- **Optional**: Postgres for indexing (not required at the beginning)

### Storage model / 存储模型（建议）

**Primary = files (append-only)**:

- Stage-1 pool: `pool.jsonl` (one record per line)
- Snapshots: `snapshots/snapshot_<id>.jsonl` (read-only)

**Optional = DB for index only**:

- store run metadata, snapshot index, quick search
- do not use DB as the only source of truth in early phase

---

## 4) Security baseline / 安全基座（必须）

### 4.1 Supply chain safety / 供应链

- Pin Python version in Docker image tag.
- **Single source of truth for runtime**: deployment must run inside Docker with **Python 3.12** (local Python version is not a deployment guarantee).
- Lock dependencies (requirements pinned / uv.lock / poetry.lock).
- Record `git_commit` + `image_tag/digest` + `python_version` in `run_manifest.json`.

### 4.2 Runtime safety / 运行时

- Non-root user in containers.
- No privileged containers; avoid host networking.
- Only mount required volumes (runs/logs/pools).
- Secrets via environment variables or VPS private files (never in git).
- **Kill switch**: `/etc/prometheus-quant/STOP` triggers safe shutdown.

### 4.3 Audit safety / 审计

- Append-only pools (no overwrite).
- Batch evaluation (avoid streaming updates that blur experiment boundaries).
- Config versioning: write config snapshot into `run_manifest.json`.
- **Execution interface alignment (mandatory)**: record `exchange_lib/env/symbol_in_use` and ship a sanitized alignment evidence bundle (raw samples + mapping report). Switching CCXT ↔ SDK is treated as a “world difference”.

**Execution interface difference log (mandatory, append-only)**:

- Every observed CCXT ↔ OKX SDK discrepancy must be recorded with evidence references (run_id + raw samples + impact).
- Canonical log: `docs/v10/V10_EXECUTION_INTERFACE_DIFF_LOG_OKX_CCXT.md`

---

## 5) Artifact contract / 产物契约（必须落盘）

Per run directory (example):

- `run_manifest.json`
- `multiple_experiments_summary.json` (or single-run summary)
- `execution_fingerprint.json` (demo/live required; offline can be null+reason)
- `behaviors_run_<id>.json` (optional, when enabled)
- `genomes_run_<id>.npy` (optional, when enabled)

Minimum fields in `run_manifest.json`:

- `git_commit`
- `docker_image` (tag or digest)
- `python_version` (inside container)
- `mode` (offline/okx_demo/okx_live)
- `window` (name/start/len if applicable)
- `ablation` (name/details if applicable)
- `config_hash` and a dumped config section (or file reference)
- `results_dir`
- `start_time`, `end_time`
- `positions_quality` (e.g. "exchange_reported" | "reconstructed_from_fills" | "unreliable" | "unknown")
- `impedance_fidelity` (e.g. "simulated" | "demo_proxy" | "live_calibrated" | "unknown")

---

## 6) Stage-1 gene pool (append-only) / 一级火种库（只增不改）

### Record schema (minimal) / 记录最小字段

- `id` (uuid or monotonic id)
- `created_at`
- `source`:
  - `git_commit`, `docker_image`, `run_id`, `seed`, `mode`, `window`, `ablation`
- `genome_vector_342` (base64 or list; choose one and stick to it)
- `metrics_summary` (small dict):
  - survival/death flags, costs summary, sanity checks
- `fingerprint_ref` (path to execution_fingerprint.json or run_id)

### Snapshot rule / 快照规则

- Create periodic snapshots: `snapshot_<id>.jsonl`
- Stage-2 is allowed to read snapshots only.

---

## 7) What “success” means (engineering) / 工程成功标准

- Starts/stops reliably on VPS (systemd or docker compose)
- Artifacts always written (manifest + summary)
- No log spam / no infinite loops after collapse
- Reproducible build (same commit → same image tag)
- Rollback is one command (previous image tag)

---

## 7.1 Survival-first KPI (“Stay alive”) / 第一指标：活着（必须落盘）

**English (primary)**: For C-stage, the #1 KPI is **staying alive**. We do not expect “never crash”; we require that the system’s **internal-collapse interval** becomes measurable and improvable over time.

**中文（辅助）**：C阶段第一指标就是**活着**。我们不追求永不崩溃，而是要把“内部崩溃间隔”变成可测、可拉长的曲线。

### Definitions / 口径定义（审计层，不进决策路径）

- **Internal-collapse event / 内部崩溃事件**（任一触发即记为一次事件）：
  - **Extinction**: `alive_agents == 0`
  - **Financial collapse**: `system_reserve <= 0`（或项目定义的等价条件）

- **Time-to-first-internal-collapse / 首次内部崩溃时间**：
  - 从 run 开始到第一次内部崩溃事件发生的墙钟时间（或 ticks）。

- **Internal-collapse interval / 内部崩溃间隔**：
  - 相邻两次内部崩溃事件之间的墙钟时间（或 ticks）。

- **Restart time / 冷启动耗时**：
  - 从检测到内部崩溃到系统恢复到“再次可产生有效产物/再次可下单”的时间。

### Artifact requirements / 落盘要求（强制）

Each run must record the following in `run_manifest.json` and/or `summary.meta`:

- `internal_collapse_detected` (bool)
- `internal_collapse_reason` ("extinction" | "financial" | "both" | null)
- `internal_collapse_time` (UTC timestamp, if occurred)
- `time_to_first_internal_collapse_seconds` (number or null)
- `restart_time_seconds` (number or null, if restart mechanism exists)

**Note**: This is an auditing metric only. It must not be used as a hard threshold inside the decision/state machine path (see “ecological fences ≠ decision logic”).

---

## 8) References / 参考

- Acceptance criteria (Gate 4 included): `docs/v10/V10_ACCEPTANCE_CRITERIA.md`
- V10 evidence chain index: `docs/v10/V10_RESEARCH_INDEX.md`


