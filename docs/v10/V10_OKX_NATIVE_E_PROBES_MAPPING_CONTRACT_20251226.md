# V10 OKX Native E-Probes Mapping Contract (No Cross-Reference) / OKX原生E探针对齐契约

Date: 2025-12-26  
Scope: execution_world (okx_demo_api first, okx_live later)  
Principle: **We choose ONE API (OKX native REST/WS). We only guarantee probe mapping + evidence. We do NOT explain market truth.**

---

## 0) Definitions

- **Probe**: a scalar input feature consumed by Core decision (E/I/M/C).
- **Alignment (here)** means:
  - one probe ↔ one canonical OKX endpoint + one field path (or `unavailable`)
  - timestamp provenance recorded (`source_endpoint_used`, `source_ts_used`, `source_ts_ms_used`)
  - missing values are **not fabricated as 0** (must be `null/unknown` with quality flags)

---

## 1) Canonical OKX endpoints (E only)

We define canonical sources for E probes:

- **Ticker**: `GET /api/v5/market/ticker?instId=<instId>`
- **Orderbook (top-of-book/depth)**: `GET /api/v5/market/books?instId=<instId>&sz=5`
- **Candles (OHLCV)**: **not yet wired in current connector**  
  - If later enabled, must be explicitly versioned and added as a new canonical endpoint (breaking-change if E vector changes).

---

## 2) Required provenance fields (per tick, per E sampling)

Every tick_summary (or E-snapshot record) MUST include:

- `inst_id_used`
- `source_endpoint_used`
- `source_ts_used` (ISO8601 string from exchange if present; else local sampling time explicitly labeled)
- `source_ts_ms_used` (integer if exchange provides ms; else `null`)
- `input_quality_flags` = `ok | degraded | unavailable`
- `reason_code` (nullable string, required when not `ok`)

Hard rule: **If `input_quality_flags != "ok"`, any dependent probe values MUST be `null`** (or `value=0 + mask=1` if the vector format requires a number, but mask must be present and auditable).

---

## 3) E-Probes mapping table (v2 candidate set)

### 3.1 Minimal E set that is directly supported by OKX ticker/books (recommended for demo)

These probes are supported without inventing OHLC:

| Probe | Canonical endpoint | Field path | Notes |
|------|---------------------|-----------|------|
| `E_price_ref` | `/api/v5/market/ticker` | `data[0].last` or `data[0].markPx` (choose one and freeze) | Must freeze which one is used (mark vs last). |
| `E_bid_px` | `/api/v5/market/ticker` | `data[0].bidPx` | Top bid price. |
| `E_ask_px` | `/api/v5/market/ticker` | `data[0].askPx` | Top ask price. |
| `E_spread_px` | derived | `E_ask_px - E_bid_px` | Derived, but still auditable (inputs referenced). |
| `E_spread_bps` | derived | `(E_spread_px / E_price_ref) * 1e4` | Derived. |
| `E_high_24h` | `/api/v5/market/ticker` | `data[0].high24h` | 24h high. |
| `E_low_24h` | `/api/v5/market/ticker` | `data[0].low24h` | 24h low. |
| `E_vol_24h` | `/api/v5/market/ticker` | `data[0].vol24h` or `data[0].volCcy24h` | Must freeze which volume dimension is used. |
| `E_bid_sz_l1` | `/api/v5/market/books` | `data[0].bids[0][1]` | Requires books sample size ≥ 1. |
| `E_ask_sz_l1` | `/api/v5/market/books` | `data[0].asks[0][1]` | Requires books sample size ≥ 1. |

### 3.2 Unsupported probes under “ticker+books only” (must be removed or marked unavailable)

If we do not enable candles:

- `open/high/low/close/volume` (OHLCV per bar) are **unavailable** as true OHLC probes.
- Any probe that would require historical sequences must be explicitly versioned as a separate module/endpoint.

Hard rule: **Do not fabricate OHLC from ticker fields.**  
If a legacy feature vector still expects OHLC fields, they MUST be set to `null/unknown` with `input_quality_flags="unavailable"` (or omitted in a v2 feature contract).

---

## 4) Demo vs Live: policy (naming only, no explanation)

- `truth_profile=degraded_truth` (okx_demo_api): E probes may be available, but timestamp/latency/market friction are not claimed as real; must mark `impedance_fidelity` separately for M.
- `truth_profile=full_truth_pnl` (okx_live): E probes must still follow this mapping; missing critical probes may trigger STOP depending on Gate policy.

---

## 5) Acceptance (for E mapping only)

PASS if:
- Every tick writes provenance metadata listed in section 2
- Every probe in the “supported set” is either:
  - populated from the canonical endpoint field path, OR
  - explicitly `null` with `input_quality_flags != ok` and a non-empty `reason_code`

FAIL if:
- any missing probe is silently replaced with 0 **without a mask/quality reason**
- probe uses a different endpoint/field path than the mapping without a contract version bump

---

## 6) Raw-only rule (hard)

E probes are **raw observations**. We do not attempt to compute or infer complex structure.

- Allowed:
  - direct OKX native fields (ticker/books) and lightweight, physically interpretable transforms:
    - normalization / clipping / tanh compression
    - simple arithmetic derived from canonical fields (e.g., spread, spread_bps)
- Forbidden:
  - microstructure inference (order-flow imbalance models, impact/hidden liquidity estimation, etc.)
  - strategy-like technical indicators (RSI/MACD/MA-cross, etc.)

Missing data rule remains strict: **unknown with quality + reason_code**, never fabricated as 0.


