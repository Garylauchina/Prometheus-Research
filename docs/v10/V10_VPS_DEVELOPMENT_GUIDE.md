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

**Self-trade (cross with ourselves) risk (mandatory, auditing-only)**:

- When multiple Agents (or multiple strategy loops) trade the same instrument under the same account, we may accidentally match our own orders (**self-trade / self-cross**).
- Risk: fake volume + fee loss + learning the “internal microstructure” instead of market structure.
- Requirement:
  - Prefer exchange-level STP (Self-Trade Prevention) if available; otherwise enforce an outer-shell execution policy (netting/aggregation) before we scale multi-agent execution.
  - Record the policy and capabilities in `run_manifest.json` (see fields below).
  - Preserve minimal raw fields needed for detection in `m_execution_raw.json` (or equivalent).

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
- `self_trade_prevention` (object, auditing-only):
  - `stp_supported` (bool | null)
  - `stp_enabled` (bool | null)
  - `execution_netting_enabled` (bool)  # whether we aggregate/net orders before sending
  - `self_trade_policy` ("forbid" | "allow" | "unknown")
  - `self_trade_detection_capability` ("strong" | "weak" | "none")  # based on available exchange fields

---

## 5.1 Two-tier artifact contract (HF screening vs Promote) / 两级产物契约（高频筛选 vs 晋级复盘）

**English (primary)**: High-frequency screening exists to **select genomes**, not to produce court-grade replay for every run.  
Therefore we define a two-tier artifact contract:

- **Tier-1: HF screening runs** → minimal accountability evidence (bounded disk)
- **Tier-2: Promote / audit runs** → full evidence chain (replay-grade)

中文（辅助）：高频筛选的目的只是筛选基因，因此不应“每个 run 全量留证据”把系统拖死；我们把全量证据留给少数晋级 run。

### A) Tier-1: HF screening run (minimal but accountable) / 一级：高频筛选（最小可追责）

**Run tagging / 口径标识（强制）**：

- `run_id` prefix: `HF_...`
- `run_manifest.meta.tier = "tier1_hf"`

**Must write (per run)**:

- `run_manifest.json` (full meta, but no requirement to store full raw streams)
- `execution_fingerprint.json` (aggregates + api_calls + error counters)
- `multiple_experiments_summary.json` (or HF summary)
- `gating_telemetry.json` (Fence Inventory tie-in; required for Principle 4 claims)
- `death_events.jsonl` (structured; one line per death; see below)
- `pool.jsonl` append record (genome + minimal metrics + evidence refs)

**Raw evidence policy (default)**:

- **Event-driven sampling** (recommended):
  - keep full records only for **errors / rejects / timeouts / forced liquidation / collapse / self-trade suspicion**
  - keep a small fixed sample for baseline (e.g., 1 out of N orders)
- Hard cap: define a per-run size budget (e.g., 50–200MB) and rotate/delete raw samples beyond the cap.

**Death analysis is mandatory (lightweight)**:

`death_events.jsonl` minimal fields:

- `ts_utc`, `tick` (if available)
- `agent_id` (or hashed), `death_reason`, `death_reason_source`
- `capital_triplet` snapshot (allocated/reserve/current_total or equivalent)
- `has_position`, `position_side` (or `null + reason`)
- `last_signal`, `state_final` (if available)
- `api_error_count_so_far` (from tracker/fingerprint)
- `fence_block_rate_summary` (top fences by block_count during recent window)

> Rule: Tier-1 cannot claim “natural selection structure” without fence telemetry and honest missing-field reasons.

### B) Tier-2: Promote / audit run (full evidence) / 二级：晋级复盘（全量证据链）

**Run tagging / 口径标识（强制）**：

- `run_id` prefix: `PROMOTE_...` or `AUDIT_...`
- `run_manifest.meta.tier = "tier2_full"`

**Must write (full chain)**:

- All artifacts in section 5, plus:
  - `m_execution_raw_part_*.json` + `m_execution_raw_index.json` + hashes
  - `positions_snapshot.json`
  - `positions_reconstruction_raw_part_*.json` + `positions_reconstruction_raw_index.json` + hashes
  - alignment evidence bundle (report + raw samples) for the actual execution library
- Optional but recommended:
  - Incident Evidence Bundle (IEB) if anomaly triggers (see C2.0 runbook)

**Promotion triggers / 晋级触发条件（建议）**：

- Top-K candidates by survival KPI or ROI (ballast / contributor / champion candidates)
- Any “interesting death” pattern:
  - mass death cluster
  - “no trades but died”
  - repeated order rejects / timeouts
  - suspected self-trade
  - three-dimensional resonance episodes (trend + friction spike + mass death)

### C) Storage isolation / 存储隔离（强制）

To avoid evidence pollution and disk blow-up:

- Separate roots:
  - Tier-1 HF runs: `/var/lib/prometheus-quant/runs_hf/`
  - Tier-2 audit runs: `/var/lib/prometheus-quant/runs/`
- Pools remain append-only:
  - stage1 live pool: `/var/lib/prometheus-quant/pools/stage1/pool.jsonl`
  - snapshots: `/var/lib/prometheus-quant/pools/stage1/snapshots/`

### D) Retention policy / 保留策略（建议默认）

- Tier-1 HF:
  - keep manifests/fingerprints/telemetry/pool records indefinitely (small)
  - keep raw samples for a limited window (e.g., 7–30 days) or until promoted
- Tier-2:
  - keep full evidence for promoted runs long-term
  - treat as audit-grade evidence; deletion requires an explicit record

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
- Execution interface diff log (OKX SDK vs CCXT): `docs/v10/V10_EXECUTION_INTERFACE_DIFF_LOG_OKX_CCXT.md`

---

## 9) Known pitfalls / 已知坑（优先排雷）

### 9.1 Mode configuration must be a CLI arg / mode 必须通过命令行参数传入

`prometheus/v10/ops/run_v10_service.py` parses mode from `--mode ...` (CLI), not from `MODE` env var.

中文：如果 Dockerfile/compose 把 `--mode` 写死或默认成不存在的值（例如 `okx_demo`），那么 `.env` 里的 `MODE=okx_demo_api` 也会被覆盖，导致 C0.5 无法启动。解决方案必须在 ops 外壳层完成：统一默认值，并确保 compose 用 `command:` 把 `--mode ${MODE}` 传进 CLI。


