# V13 SSOT — Capture Window Minimal Contract v0 — 2026-01-10

Status: **FROZEN (minimal, hard)**  
Additive-only.

Purpose:
- Freeze **very little but very hard**: the existence semantics of a capture window and the minimal textual facts we must preserve.
- Avoid freezing directory structure, binary artifacts, naming conventions, or replay assumptions at this stage.

---

## §1 Window existence semantics (frozen)

Definition:

> A **Capture Window** is one observation attempt where **we tried to observe**, and the world gave an outcome (including silence).

NOT a window:
- not merely a time interval
- not necessarily a complete dataset
- not necessarily “a set of required files must be complete”

Interpretation rule (frozen):
- The world’s silence/refusal/drift during a window is a **first-class outcome**, not an engineering failure.

---

## §2 Minimal required textual artifacts per window (frozen)

For each window, **exactly three textual fact files MUST exist** (no other structure required).

### §2.1 `window.meta.yaml` (or `window.meta.md`)

MUST contain facts only (no analysis):
- `window_id` (unique)
- `start_ts` (ISO8601 or unix ms; be consistent within file)
- `end_ts` (if unknown/unbounded, must explicitly write `end_ts: null` and explain only as a fact like “still running”)
- `observation_mode` in {`live`, `interrupted`, `failed`}
- `connection_status_summary` (one short line; factual)

Notes:
- YAML is preferred (`window.meta.yaml`).
- If Markdown is used, file must be named `window.meta.md` and include the same fields in a simple key-value block.

#### §2.1.1 Additional factual fields (frozen as **recommended**, Phase 2+)

These fields do **not** change the minimal existence semantics, but they harden auditability.

Recommended:
- `observation_config_fingerprint`
  - a stable fingerprint of the observation configuration used for this window
  - allowed forms:
    - `sha256:<64-hex>`
    - `git:<commit_sha>` (if config is fully captured by a commit)
- `time_sync`
  - `time_sync.method` (e.g., `systemd-timesyncd`, `chrony`, `ntpd`, `manual`)
  - `time_sync.checked_at_utc` (ISO8601)
  - `time_sync.offset_estimate_ms` (number; signed; if unknown, use `null`)
  - `time_sync.notes` (one factual line; optional)

Grandfathering:
- Windows created before 2026-01-12 may omit these fields without being considered invalid windows.

### §2.2 `phenomena.log.md`

This is the **core V13 product** for a window. It is allowed to be extremely short.

Format is intentionally minimal (facts only):
- `Observed:` (bullet list; may be empty)
- `Not observed:` (bullet list; may be empty)
- `Notes:` (optional; factual, e.g., “observation stopped at T3”)

Allowed:
- 1 line
- 3 lines
- “nothing observed”

Forbidden:
- causal explanations
- attribution or conclusions

### §2.3 `verdict.md`

The entire file MUST be exactly one of the following uppercase tokens (no other text):
- `MEASURABLE`
- `NOT_MEASURABLE`
- `INTERRUPTED`
- `REJECTED_BY_WORLD`

Meaning (frozen, descriptive only):
- `MEASURABLE`: the window produced a chain that passes the current measurability gates.
- `NOT_MEASURABLE`: the window truthfully failed a measurability gate (missing key world evidence).
- `INTERRUPTED`: the observation attempt did not complete as intended (operator/network/runtime stop).
- `REJECTED_BY_WORLD`: the world actively refused observation (e.g., persistent blocks / hard denials).  
  (Do not justify inside `verdict.md`; justification belongs only as factual bullets in `phenomena.log.md`.)

---

## §3 What is explicitly NOT frozen now (frozen list)

- No fixed directory depth.
- No requirement that any binary/raw data files exist.
- No forced artifacts naming convention.
- No rule that a window must yield a replay dataset.
- No “one window must be reusable” assumption.

---

## §4 Recommended (non-binding) layout (NOT frozen)

Engineers may find this convenient, but it is not a contract:

```
docs/v13/phenomena/
  windows/
    <WINDOW_ID>/
      window.meta.yaml
      phenomena.log.md
      verdict.md
      (optional) raw/
      (optional) notes/
```

