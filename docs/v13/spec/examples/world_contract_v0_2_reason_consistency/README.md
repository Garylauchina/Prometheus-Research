# V13 Spec Examples — World Contract v0.2 — Reason Consistency (min library) — 2026-01-12

Purpose:
- Lock the **boundary semantics** of Gate 6 (Reason Consistency) in the current verifier implementation.
- Provide minimal, copyable example cases.

Important:
- These examples are **structural**. They do not assert market meaning.
- The verifier output includes timestamps; examples therefore provide **expected verdict + reason_codes only**.

---

## Cases

### Case A — PASS (no reason codes, all required channels present)
- dir: `case_pass/`
- expected:
  - `verdict: PASS`
  - `reason_codes: []`

### Case B — FAIL (reason codes present while all prior gates pass)
- dir: `case_fail_reason_codes_present/`
- expected:
  - `verdict: FAIL`
  - `reason_codes: ["fail:invalid_reason_code"]`

Rationale (structural):
- In v0.2 verifier, Gate 6 fails closed if any record carries any `contract_reason_codes` even when enum-valid.

### Case C — NOT_MEASURABLE (missing a required channel)
- dir: `case_not_measurable_missing_channel_market_api/`
- expected:
  - `verdict: NOT_MEASURABLE`
  - `reason_codes: ["not_measurable:channel_missing:market_api"]`

