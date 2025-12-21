# V10 Execution Interface Difference Log (OKX SDK vs CCXT) / 执行接口差异记录（OKX官方库 vs CCXT）

## 0) Purpose / 目的

**English (primary)**: This document is an **append-only audit log** for recording **observed** differences between OKX official SDK (or direct REST) and CCXT when running V10 in `okx_demo_api` / `okx_live` modes.  
It exists to prevent “self-deception”: the system must never silently learn “library quirks” instead of market structure.

**中文（辅助）**：本文是一个**只增不改**的差异审计日志，用来记录在 V10 的 `okx_demo_api / okx_live` 运行中，OKX 官方库（或直连REST）与 CCXT 在字段口径/行为/返回结构上的**实测差异**。  
目的：防止系统把“接口差异”当成市场结构，把证据链污染。

---

## 1) Non-goals / 不做什么

- Not a migration plan (no “switch library” decision here).
- Not a code change request.
- Not an opinion piece.

中文：这里不讨论换库，不提改架构，不写代码；只做“记录+证据引用”。

---

## 2) Golden rule / 黄金规则

**Record what you saw, not what you think.**

Minimum evidence for every entry:

- `run_id` + `git_commit` + `docker_image_digest` + `python_version`
- `env` (demo/live) + `symbol_in_use` + account mode hints (`tdMode`, `posMode`, `marginMode` if available)
- raw sample references (sanitized JSON) for both sides whenever possible
- mapping impact: which V10 internal fields/features are affected (E/I/M/C)
- a mitigation note (how the adapter should degrade: `null + reason`, fallback, or “not obtainable”)

---

## 3) Severity / 严重度分级（建议）

- **S3 (Fatal)**: breaks invariants or misleads core metrics (e.g., positions always empty but reported as valid).
- **S2 (High)**: affects I/M fidelity materially (posSide/tdMode misread; trades/fees missing).
- **S1 (Medium)**: partial field loss; can be degraded with `null + reason`.
- **S0 (Low)**: cosmetic/formatting differences only.

---

## 4) Entry template / 记录模板（复制后填写）

### Entry: DIFF-YYYYMMDD-<short>

- **Date (UTC)**:
- **Run**:
  - **run_id**:
  - **git_commit**:
  - **docker_image_digest**:
  - **python_version**:
- **Execution environment**:
  - **env**: demo | live
  - **exchange_id**: okx
  - **symbol_in_use**:
  - **market_type**: swap | spot | futures | margin | unknown
  - **account_mode hints**: tdMode/posMode/marginMode (if obtainable)
- **Libraries compared**:
  - **A**: CCXT (version if known)
  - **B**: OKX official SDK (name/version) or direct REST
- **Operation** (one of):
  - market data: ticker/ohlcv/orderbook
  - account: balance/positions
  - trading: create_order/cancel_order/fetch_order/fetch_my_trades
- **Observed difference (facts only)**:
  - **CCXT output**: (short description)
  - **OKX output**: (short description)
  - **Mismatch**: (what differs exactly)
- **Evidence**:
  - **ccxt_raw_sample_ref**: (path in run directory)
  - **okx_raw_sample_ref**: (path in run directory)
  - **alignment_report_ref**: (path in run directory)
- **Impact on V10 internal schema**:
  - **E**:
  - **I**:
  - **M**:
  - **C**:
- **Severity**: S0 | S1 | S2 | S3
- **Mitigation (adapter-level, no core changes)**:
  - degrade strategy: `null + reason` | fallback | mark as unreliable | block run
  - required manifest flags: e.g. `positions_quality`, `impedance_fidelity`
- **Decision**:
  - **Status**: open | understood | mitigated | accepted-risk
  - **Next verification** (what to run/collect next)

---

## 5) Known recurring hotspots / 已知高频雷区（先验清单）

> Note: These are *hypotheses / watchpoints* until logged as entries with evidence.

- **Positions in demo may be unreliable/empty**
  - Watch: `fetch_positions` returns empty while orders/trades exist.
  - Risk: I-features (has_position/direction) become untrustworthy.
- **`tdMode` / `posSide` / `marginMode` semantics**
  - Watch: one library infers defaults incorrectly (net vs long/short mode).
  - Risk: position direction is flipped or collapsed.
- **Trade/fee fields**
  - Watch: missing fee currency, fee amount, or partial fill details.
  - Risk: M-features (cost/impedance) are fabricated by heuristics.
- **Instrument ID vs symbol mapping**
  - Watch: `BTC/USDT:USDT` vs instrumentId mismatch.
  - Risk: data and execution refer to different instruments (silent world split).

---

## 6) Current entries / 当前已记录条目

### Entry: DIFF-20251221-G4.5-alignment-status-baseline

- **Date (UTC)**: 2025-12-21
- **Source**: Alignment mapping/audit summary (not yet a dual-run raw-sample diff entry)
- **Observed alignment status (facts)**:
  - **E (Environment)**: ✅ fully aligned (CCXT `fetch_ticker` / `fetch_ohlcv`)
  - **I (Identity)**: ⚠️ partial (demo `fetch_positions()` unreliable/empty; needs fallback)
  - **M (Market Interaction)**: ⚠️ partial (demo fidelity low; must be labeled as simulated)
  - **C (Community)**: ✅ aligned (no CCXT dependency)
- **Risks & mitigations (facts)**:
  - **HIGH (I1/I2 positions state)**:
    - risk: demo positions may be empty or inaccurate
    - mitigation: must implement an **internal position tracker** (reconstruct positions from order fills / trade stream)
  - **MEDIUM (M impedance fidelity)**:
    - risk: demo slippage/latency != real market friction
    - mitigation: demo runs must mark `impedance_fidelity: "simulated"`; production must recalibrate
- **Evidence references (pointers)**:
  - mapping report (Quant repo): `prometheus/v10/ops/CCXT_OKX_ALIGNMENT_AUDIT.md`
  - runtime artifacts (expected per run): `ccxt_alignment_report.json`, `ccxt_raw_samples.json`, `run_manifest.json`
- **Implementation note (from code read, not from runtime)**:
  - Current `okx_demo_api` connector (`prometheus/v10/ops/okx_api_connector.py`) is a direct REST client and does **not** expose a CCXT `exchange` instance by default.
  - Therefore, `run_v10_service.py`’s alignment self-check may be **skipped** (no exchange instance) unless an explicit CCXT exchange object is attached for audit calls.
- **Impact on V10 internal schema**:
  - **E**: OK (expected to be stable)
  - **I**: must not pretend “positions are obtainable” when they are not; use `null + reason` or internal tracker output
  - **M**: must label fidelity; do not compare demo M-distributions to live as if same-world
  - **C**: unaffected
- **Severity**: S2 (High) for I; S1 (Medium) for M
- **Decision**:
  - **Status**: open
  - **Next verification**:
    - produce a single `okx_demo_api` run with both: (a) CCXT raw samples and (b) OKX SDK/REST raw samples (sanitized), then record as a real diff entry.


