# Prometheus V13 — SSOT: World Contract v0.2 (Frozen) — 2026-01-10

Additive-only.

Purpose:
- The World Contract is a **structural closure adjudicator**: it decides whether an observation run can produce **measurement conclusions**.
- It does **not** interpret markets, strategies, reflexivity, or world events.

Core principles (frozen):
- **Contract First**: no contract PASS ⇒ no measurement conclusion
- **Fail-Closed**: any gate failure ⇒ verdict (FAIL or NOT_MEASURABLE), no partial pass
- **Layer separation**:
  - Contract Layer: PASS / NOT_MEASURABLE / FAIL (evidence closure)
  - Life Layer: alive / dead (market kills strategies; record only)
  - Analysis Layer: unrestricted interpretation, but never enters Contract

Hard rule:
- **Life death ≠ Contract death**. The market can kill a strategy; it must not contaminate evidence closure.

---

## §1 Contract Spec (SSOT, machine-readable)

Canonical spec JSON (frozen):
- `docs/v13/spec/world_contract_v0_2_spec.json`

The verifier MUST be driven by the spec only (self-contained).

---

## §2 Evidence file (v0.2)

Required file:
- `evidence.json`

Evidence format (frozen for v0.2 verifier):
- JSON array of objects
- each object MUST contain the required fields defined in the spec

Notes:
- This is intentionally minimal. Window-level textual artifacts (V13 capture window minimal contract) are orthogonal and can exist without Contract PASS.

---

## §3 Verifier requirements (v0.2)

Mandatory properties:
- **Idempotent**: read-only; never modifies files
- **Self-contained**: rules come only from spec JSON
- **Fail-closed**: first failing gate produces a verdict immediately
- **No narrative**: reasons are gate-derived only (enum-checked)

---

## §4 Gate order (frozen; cannot change)

1) Required Files  
2) Evidence Parse  
3) Schema Verification  
4) Join Closure  
5) Channel Availability  
6) Reason Consistency

---

## §5 World events policy (frozen boundary)

`world_events` is NOT a Contract input:
- world events do NOT enter `contract_reason_codes`
- world events do NOT retroactively change a run verdict

The only allowed effect of world events:
- trigger a **fork** (new run_id), with a copied spec and new run metadata

---

## §6 Shadow / Exploration isolation (frozen boundary)

Shadow outputs:
- are **hypothesis generation only**
- MUST NOT enter Contract
- MUST NOT produce measurement conclusions

If Shadow graduates to a formal run:
- it must re-run under a full Contract closure with fresh evidence.

