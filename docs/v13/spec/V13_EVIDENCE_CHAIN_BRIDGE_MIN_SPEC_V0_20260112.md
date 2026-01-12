# V13 Spec — Evidence Chain Bridge (raw/dataset → evidence.json) — min v0 — 2026-01-12

Status: **FROZEN (minimal, hard)**  
Additive-only.

Purpose:
- Define the **minimum, auditable** bridge from observation artifacts (raw capture / dataset) to `evidence.json`
- Ensure Contract Layer can be verified without narrative or hidden transformations

Non-goals:
- No strategy performance evaluation
- No market interpretation
- No “data cleaning” that changes facts

---

## §1 Inputs (facts, not assumptions)

This spec does **not** freeze directory structure. It freezes **semantic inputs**:

- **Window textual facts** (minimal contract):
  - `window.meta.yaml` (or `.md`)
  - `phenomena.log.md`
  - `verdict.md`
- **Raw capture artifacts** (optional but typical):
  - websocket `books5` messages (as recorded)
  - websocket `trades` messages (as recorded)
  - recorder runtime logs (as recorded)
- **Dataset artifacts** (optional; if produced):
  - a manifest describing sources and transformations (append-only, factual)
  - any derived tables/jsonl used for later life/analysis layers

---

## §2 Output: `evidence.json` (Contract Layer input)

The World Contract v0.2 requires:
- file: `evidence.json`
- format: JSON array of objects
- required fields and types are defined by:
  - `docs/v13/spec/world_contract_v0_2_spec.json`

Bridge rule (frozen):
- The bridge MUST output `evidence.json` that is **sufficient** for Contract verification.
- The bridge MUST NOT embed analysis or narrative in Contract fields.

---

## §3 Minimal record construction rules (frozen)

For each record in `evidence.json`:

- **`timestamp`**:
  - use an ISO8601 UTC timestamp string
  - MUST be derived from a factual source (e.g., window start/end, recorder event time); do not invent

- **`strategy_id`**:
  - MUST be a non-empty string
  - If Phase 1 observation has “no strategy execution”, use a stable sentinel like:
    - `strategy_id: "phase1_observer_only"`

- **`life_verdict`**:
  - MUST be a string (v0.2 does not constrain enum)
  - For Phase 1 observation-only windows, use:
    - `life_verdict: "n/a"`

- **`contract_reason_codes`**:
  - MUST be a list
  - For v0.2, it MUST be `[]` in any record intended to PASS gates (see Reason Consistency gate)

- **`ablation_flags`**:
  - MUST be a list (possibly empty)
  - For Phase 1 observation-only windows, use `[]`

- **`channels`**:
  - MUST be a list of strings describing what world evidence channels are present for this record
  - v0.2 required channels are:
    - `market_api`
    - `observation_window`

Channel inclusion rule (frozen):
- Include `observation_window` if the window textual facts exist and are internally consistent for the record.
- Include `market_api` only if the record is backed by market API / market feed evidence as frozen by the producing system.
- If any required channel is missing for any record, the Contract verifier will produce `NOT_MEASURABLE`.

---

## §4 Provenance & immutability hooks (frozen, minimal)

Bridge MUST produce an append-only manifest file (name not frozen) that records:
- which raw files were used (paths)
- how they were read (no lossy filtering rules without explicit declaration)
- a content fingerprint per source file (e.g., `sha256`)
- the exact command / version used to generate `evidence.json`

Note:
- This is a *bridge spec*; it does not mandate storage location or tooling.

