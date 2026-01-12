# V13 Ops — Phase 1 stop conditions checklist / review gate v0 — 2026-01-12

Status: **FROZEN (minimal, hard)**  
Additive-only.

Purpose:
- Make stop conditions auditable and repeatable.
- Convert “we stopped because …” into a **checklist of factual conditions**.

Rule:
- This checklist is a **review gate** for any Phase 1 completion report.
- Do not add explanations here; only tick facts and link to raw evidence.

---

## §1 Window identification

- [ ] `window_id` is recorded (matches `window.meta.yaml`)
- [ ] `start_ts` / `end_ts` are recorded (or `end_ts: null` is explicit)
- [ ] `observation_mode` is recorded

---

## §2 Stop condition trigger (pick all that apply; facts only)

### Operator / process
- [ ] Planned stop reached (e.g., 24h / 7d) — specify planned duration in report
- [ ] Manual operator stop — link to operator note or command log

### Connectivity / exchange refusal
- [ ] Persistent disconnects beyond threshold — link to recorder logs
- [ ] Persistent subscription errors / auth failures — link to recorder logs
- [ ] API / WS rate-limit blocks observed — link to raw messages or logs

### Time correctness
- [ ] Time sync check performed — reference `window.meta.yaml.time_sync`
- [ ] Time offset deemed unacceptable — include only measured offset fact

### Resource / infra
- [ ] Disk pressure / quota exceeded — link to `df -h` snapshot or logs
- [ ] OOM / process crash — link to system logs
- [ ] Host reboot / maintenance — link to system logs

### Schema / interface drift
- [ ] Required fields disappeared / changed types — link to raw payload sample
- [ ] Recorder version changed mid-window — link to config fingerprint change

---

## §3 Post-stop actions (facts)

- [ ] Window textual artifacts exist: `window.meta.yaml`, `phenomena.log.md`, `verdict.md`
- [ ] If Contract was runnable: world contract verifier JSON is archived and linked
- [ ] If Contract was not runnable: report states “no contract closure” as a fact

