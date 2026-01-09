# V13 Phenomena Log Protocol (Draft) v0 — 2026-01-10

Purpose (V13-only):
- For each capture window, produce a **minimal, repeatable, non-interpretive** record of what the world did.
- No explanation, no summary, no attribution. Just facts + pointers.

Scope:
- Applies to any V13 real-time capture attempt (books5/trades) and its derived dataset/run artifacts.

---

## One capture window = one log entry

Create one markdown file per capture window under:
- `docs/v13/artifacts/v13_capture_windows/<WINDOW_ID>/PHENOMENA_LOG.md`

Where `<WINDOW_ID>` is frozen as:
- `<inst_id>_<start_utc>__<end_utc>` (example: `BTC-USDT-SWAP_2026-01-10T00:00Z__2026-01-17T00:00Z`)

---

## The 5 questions (answer with facts only)

1) **Did the world allow continuous connection?**
   - Start/stop timestamps
   - total disconnect events count
   - longest continuous outage duration
   - evidence pointer: `recorder_events.jsonl`

2) **Did the world go silent at some periods?**
   - any intervals with zero books updates / zero trades
   - how detected (frozen rule)
   - evidence pointer(s): raw streams

3) **Did schema / behavior drift occur?**
   - field missing/new field/format change
   - endpoint errors or throttle behavior changes
   - evidence pointer(s): raw responses + events

4) **Where did NOT_MEASURABLE appear (and why)?**
   - which gate(s): provenance / coverage / schema / verifier
   - first occurrence timestamp
   - counts
   - gate report file paths

5) **Any “unexpected but repeatable” phenomenon?**
   - state the observation (no story)
   - show at least 2 occurrences with timestamps
   - evidence pointers

---

## Hard bans (protocol-level)

- Do not introduce proxies to “fill holes”.
- Do not infer hidden variables.
- Do not rank outcomes as good/bad.

