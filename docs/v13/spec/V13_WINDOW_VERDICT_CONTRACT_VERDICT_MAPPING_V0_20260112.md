# V13 Spec — Window verdict ↔ Contract verdict mapping v0 — 2026-01-12

Status: **FROZEN (minimal, hard)**  
Additive-only.

Purpose:
- Freeze a **consistency bridge** between:
  - Window-level `verdict.md` (capture window minimal contract), and
  - Contract-level verifier verdict (World Contract v0.2).
- Prevent ambiguous states (e.g., “window says MEASURABLE but Contract did not PASS”).

Scope:
- Applies to any window that claims `MEASURABLE` or `NOT_MEASURABLE`.
- Does **not** interpret markets/strategies; it is a structural consistency rule only.

---

## §1 Definitions (frozen)

### §1.1 Window verdict tokens (from minimal contract)
- `MEASURABLE`
- `NOT_MEASURABLE`
- `INTERRUPTED`
- `REJECTED_BY_WORLD`

### §1.2 Contract verdict tokens (World Contract v0.2)
- `PASS`
- `NOT_MEASURABLE`
- `FAIL`

---

## §2 Mapping table (frozen)

| Window `verdict.md` | Contract verdict REQUIRED? | Allowed Contract verdict(s) | Meaning (structural only) |
|---|---:|---|---|
| `MEASURABLE` | YES | `PASS` | Contract closure succeeded; measurement is permitted |
| `NOT_MEASURABLE` | YES | `NOT_MEASURABLE` | World evidence missing/refused (per contract gates) |
| `INTERRUPTED` | NO | (optional) `FAIL` or `NOT_MEASURABLE` or absent | Observation did not complete as intended; window-level outcome takes precedence |
| `REJECTED_BY_WORLD` | NO | (optional) `NOT_MEASURABLE` or absent | World refusal/silence/drift is asserted as a fact at window level; contract may or may not be runnable |

---

## §3 Consistency rules (frozen)

### §3.1 Hard rules
- If `verdict.md == MEASURABLE`, then a Contract verdict **MUST exist** and **MUST be `PASS`**.
- If `verdict.md == NOT_MEASURABLE`, then a Contract verdict **MUST exist** and **MUST be `NOT_MEASURABLE`**.
- If Contract verdict is `FAIL`, then `verdict.md` **MUST NOT** be `MEASURABLE` or `NOT_MEASURABLE`.

### §3.2 Recommended rule (non-binding, but preferred)
- If Contract verdict is `FAIL`, prefer setting window `verdict.md == INTERRUPTED` unless the window has factual `phenomena.log.md` bullets that justify `REJECTED_BY_WORLD`.

---

## §4 Operational note (non-binding)

To avoid confusion in reports:
- Always report both:
  - window verdict (`verdict.md`), and
  - contract verdict (World Contract verifier JSON)
in the same completion report when contract is runnable.

