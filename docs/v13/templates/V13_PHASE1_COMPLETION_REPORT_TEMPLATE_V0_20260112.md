# V13 Phase 1 — Capture Window Completion Report — TEMPLATE v0 — 2026-01-12

Status: **FROZEN (template, minimal, hard)**  
Additive-only.

Rules:
- Facts only. No causal explanation. No market interpretation.
- MUST include:
  - window verdict (from `verdict.md`)
  - contract verdict (from World Contract verifier JSON), when contract is runnable
  - window↔contract consistency self-check (mapping)
  - stop conditions checklist (review gate)

References:
- Window verdict ↔ Contract verdict mapping:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/spec/V13_WINDOW_VERDICT_CONTRACT_VERDICT_MAPPING_V0_20260112.md`
- Stop conditions checklist / review gate:
  - `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/ops/V13_PHASE1_STOP_CONDITIONS_CHECKLIST_V0_20260112.md`

---

## 0) Window pointers (facts)

- VPS: `<ip_or_hostname>`
- window_dir (absolute): `<vps_window_dir>`
- window_id: `<window_id>`

---

## 1) Window textual artifacts (V13 minimal contract; facts)

- `window.meta.yaml` (absolute): `<path>`
- `phenomena.log.md` (absolute): `<path>`
- `verdict.md` (absolute): `<path>`

Window verdict (from `verdict.md`, single token):
- `window_verdict`: `<MEASURABLE|NOT_MEASURABLE|INTERRUPTED|REJECTED_BY_WORLD>`

---

## 2) Observation summary (facts only)

### Time
- start_ts: `<iso8601>`
- end_ts: `<iso8601_or_null>`
- duration_hours: `<number>`
- observation_mode: `<live|interrupted|failed>`

### Connection (facts only)
- reconnects: `<number>`
- longest_outage_s: `<number>`
- errors: `<number>`

### Data counters (facts only)
- books_count: `<number_or_null>`
- trades_count: `<number_or_null>`
- disk_mb: `<number_or_null>`

---

## 3) Time sync facts (Phase 2+ recommended; facts only)

Copy from `window.meta.yaml.time_sync` if present.

- time_sync.method: `<systemd-timesyncd|chrony|ntpd|manual|other|null>`
- time_sync.checked_at_utc: `<iso8601_or_null>`
- time_sync.offset_estimate_ms: `<number_or_null>`
- time_sync.notes: `<one factual line or empty>`

---

## 4) Observation config fingerprint (Phase 2+ recommended; facts only)

Copy from `window.meta.yaml.observation_config_fingerprint` if present.

- observation_config_fingerprint: `<sha256:...|git:...|null>`

---

## 5) World Contract v0.2 (Contract Layer; facts only)

### 5.1 evidence.json
- evidence.json (absolute): `<path_or_null>`

### 5.2 Contract verifier output (when runnable)
- verifier_json (absolute): `<path_or_null>`
- contract_verdict: `<PASS|NOT_MEASURABLE|FAIL|null>`
- contract_reason_codes: `<json_array_or_null>`

---

## 6) Window ↔ Contract consistency self-check (REVIEW GATE; facts)

Mapping reference:
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/spec/V13_WINDOW_VERDICT_CONTRACT_VERDICT_MAPPING_V0_20260112.md`

Checklist:
- [ ] If `window_verdict == MEASURABLE`, then `contract_verdict == PASS` and verifier JSON exists
- [ ] If `window_verdict == NOT_MEASURABLE`, then `contract_verdict == NOT_MEASURABLE` and verifier JSON exists
- [ ] If `contract_verdict == FAIL`, then `window_verdict` is NOT `MEASURABLE` and NOT `NOT_MEASURABLE`
- [ ] If contract not runnable, `contract_verdict == null` and report states “no contract closure” as a fact

---

## 7) Stop conditions checklist (REVIEW GATE; copy & tick)

Copy the checklist from:
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/ops/V13_PHASE1_STOP_CONDITIONS_CHECKLIST_V0_20260112.md`

Then tick facts here (do not add explanations):

### §1 Window identification
- [ ] `window_id` is recorded (matches `window.meta.yaml`)
- [ ] `start_ts` / `end_ts` are recorded (or `end_ts: null` is explicit)
- [ ] `observation_mode` is recorded

### §2 Stop condition trigger (pick all that apply; facts only)
- [ ] Planned stop reached
- [ ] Manual operator stop
- [ ] Persistent disconnects beyond threshold
- [ ] Persistent subscription errors / auth failures
- [ ] API / WS rate-limit blocks observed
- [ ] Time sync check performed
- [ ] Time offset deemed unacceptable
- [ ] Disk pressure / quota exceeded
- [ ] OOM / process crash
- [ ] Host reboot / maintenance
- [ ] Required fields disappeared / changed types
- [ ] Recorder version changed mid-window

### §3 Post-stop actions (facts)
- [ ] Window textual artifacts exist: `window.meta.yaml`, `phenomena.log.md`, `verdict.md`
- [ ] If Contract was runnable: verifier JSON is archived and linked
- [ ] If Contract was not runnable: report states “no contract closure” as a fact

---

## 8) Attachments / pointers (facts)

- raw capture root (absolute, optional): `<path_or_null>`
- recorder logs (absolute, optional): `<path_or_null>`
- notes (absolute, optional): `<path_or_null>`

