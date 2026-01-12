# Delivery (TEMP) — V13 Kickoff Notice to Quant Programmer + Branch/Work Instructions — 2026-01-10

Repo (Quant): `/Users/liugang/Cursor_Store/Prometheus-Quant`

This instruction file (Research, absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_KICKOFF_TO_QUANT_PROGRAMMER_EXEC_20260110.md`

## 0) What changed: V13 is live (read first)

V13 is not “fix V12”. It accepts:
- world silence / refusal / drift are first-class outputs
- `NOT_MEASURABLE` is a valid verdict, not an engineering failure
- **no proxy** is allowed to enter adjudication (no synthetic world evidence)

Please read (short):
- V13 One-Page SSOT: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/V13_SSOT_STARTUP_ONE_PAGE_V0_20260110.md`
- V13 Dev Plan: `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/V13_DEV_PLAN_V0_20260110.md`

Hard freeze (very small but very hard):
- V13 Capture Window minimal contract:  
  `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/V13_SSOT_CAPTURE_WINDOW_MIN_CONTRACT_V0_20260110.md`

Key takeaway:
- Each Capture Window MUST produce **three textual fact files** (exact names):
  - `window.meta.yaml` (or `window.meta.md`)
  - `phenomena.log.md`
  - `verdict.md` (content must be exactly one uppercase token: `MEASURABLE` / `NOT_MEASURABLE` / `INTERRUPTED` / `REJECTED_BY_WORLD`)
- Do **NOT** freeze directory depth or require raw/binary files at this stage.

---

## 1) Branch prep (Quant)

In `/Users/liugang/Cursor_Store/Prometheus-Quant`, create a new branch from current `main`:

```bash
cd /Users/liugang/Cursor_Store/Prometheus-Quant
git checkout main
git pull
git checkout -b v13_trial12_live_recorder_v0_20260110
```

Rules:
- One branch for V13 Trial-12 recorder work only.
- Every run/capture must print rerun/reproduce commands and record params in a manifest.

---

## 2) Immediate work item: continue Trial-12 (real-time capture → replay dataset)

This is the current do-or-die path after Trial-11/11T were blocked.

V13 pacing override (important):
- For the next **7–10 days**, we are in **Phase 1 (Observation-first)**:
  - ✅ focus on capture stability + append-only raw evidence + 3 window text files
  - ❌ do NOT compute `L` / gates
  - ❌ do NOT run adjudication
  - ❌ do NOT require 7-day continuity before reporting anything
  - ❌ do NOT force replay dataset build unless explicitly requested later

Success criteria for Phase 1:
- We can see at least one of: cooperate / silence / refusal / drift.

Operational constraint (accepted):
- If local environment cannot use WebSocket, Phase 1 live capture MUST run on a VPS.
- This is not a bug; it is part of the world/observation condition in V13.
- Trial-12 pre-reg (Research):  
  `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/pre_reg/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_V0_20260109.md`
- Trial-12 delivery (Quant instructions):  
  `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v12/deliveries/V12_TRIAL12_REALTIME_ORDERBOOK_CAPTURE_E_CONTRACT_EXEC_20260109.md`

### Hard bans (repeat)

- ❌ Do NOT synthesize bid/ask from `last_px` (no fixed spread, no symmetric spread).
- ❌ Do NOT use trade-derived quotes as “order-book restoration”.
- ✅ If world evidence is missing: output `NOT_MEASURABLE` (do not patch with proxies).

---

## 3) V13 requirement added on top of Trial-12: window files (3 textual facts)

For each capture window you start, you MUST create these 3 files somewhere on disk (location is free):

### 3.1 `window.meta.yaml` (facts only)

Minimal fields (example):
```yaml
window_id: BTC-USDT-SWAP_2026-01-10T00:00Z__2026-01-17T00:00Z
start_ts: 2026-01-10T00:00:00Z
end_ts: null
observation_mode: live
connection_status_summary: "connected; reconnects=3; longest_outage_s=45"
```

### 3.2 `phenomena.log.md` (facts only; can be very short)

Template (example):
```md
Observed:
- prolonged silence between T1–T2
- schema field X disappeared

Not observed:
- no gate activity

Notes:
- observation attempt stopped at T3
```

Allowed: 1 line / 3 lines / “nothing observed”.

### 3.3 `verdict.md` (single token only)

File content must be exactly one of:
- `MEASURABLE`
- `NOT_MEASURABLE`
- `INTERRUPTED`
- `REJECTED_BY_WORLD`

No reasons inside `verdict.md`.

---

## 4) Suggested (non-binding) layout (for convenience only)

You MAY use:

```
/Users/liugang/Cursor_Store/Prometheus-Quant/live_capture_v13/windows/<WINDOW_ID>/
  window.meta.yaml
  phenomena.log.md
  verdict.md
  raw/               (optional)
  notes/             (optional)
```

But remember: only the 3 files’ **existence + semantics** are frozen.

---

## 5) What to send back to Research after first 24h (even if incomplete)

Please return:
- Quant commit hash on your branch
- capture root absolute path
- one window’s 3 files absolute paths:
  - `window.meta.yaml` (or `.md`)
  - `phenomena.log.md`
  - `verdict.md`
- a short note: are we seeing continuous observability or repeated breaks/silence?

Do NOT over-analyze. Facts only.

---

## 5.1) Phase 1 reporting review gate (added 2026-01-12; mandatory going forward)

For every capture window (including 24h / 7d milestones), produce a completion report using the frozen template:
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/templates/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_V0_20260112.md`

And follow the reporting instruction:
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md`

---

## 6) What to send back after 7 days (Trial-12 milestone)

This section is intentionally **de-emphasized** under V13 pacing.

Only if we have accumulated enough windows and the research side explicitly moves us to Phase 3, then we will request:
- dataset_dir build
- gates
- minimal runs

Until then:
- keep capturing
- keep writing window files
- keep returning facts (not interpretations)

