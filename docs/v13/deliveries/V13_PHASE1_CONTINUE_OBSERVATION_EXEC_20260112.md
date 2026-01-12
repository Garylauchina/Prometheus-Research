# Delivery — Quant Instructions — V13 Phase 1: Continue Observation (Collect More Windows) — 2026-01-12

> **注意：本指令文件需发布到VPS指令目录供程序员AI读取**  
> 架构师侧执行: `./tools/v13/publish_instruction_to_vps.sh <本文件路径>`  
> VPS路径: `/data/prometheus/v13_instructions/<FILENAME>`

Repo (Research): `/Users/liugang/Cursor_Store/Prometheus-Research`  
Target (Quant): Continue Phase 1 observation, collect more capture windows (facts only).

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_PHASE1_CONTINUE_OBSERVATION_EXEC_20260112.md`

---

## 0) Context (read first)

**Current status**:
- ✅ First 24h window completed: `BTC-USDT-SWAP_2026-01-09T20:04:48Z__24h`
- ✅ Window verdict: `MEASURABLE`
- ✅ Contract verdict: `PASS`
- ✅ Phenomenon observed: **cooperate** (stable observation, 0 reconnects, 0 errors)

**Phase 1 goal** (per V13 Dev Plan):
- Collect multiple windows (not necessarily long)
- Observe at least one of: cooperate / silence / refusal / drift
- We have seen "cooperate"; need more windows to check for other phenomena

**V13 pacing rule**:
- Continue observation-first approach
- Do NOT compute L / gates / adjudication yet
- Focus on: "what did the world do when we tried to observe?"

---

## 1) Continue running recorder (best-effort, no pressure)

### 1.1 Window duration (flexible)

**Options** (choose based on stability):
- **Short windows** (6h / 12h): Good for testing stability, faster feedback
- **Medium windows** (24h): Baseline (already proven)
- **Long windows** (48h / 72h): Only if short/medium windows are stable

**Rule**: No fixed requirement. Stop when:
- Planned duration reached, OR
- Stop condition triggered (see checklist in completion report template)

### 1.2 Recorder behavior (unchanged)

- Continue WebSocket capture (books5 + trades)
- Write raw JSONL files
- Generate 3 required window files on stop:
  - `window.meta.yaml`
  - `phenomena.log.md`
  - `verdict.md`
- Generate `evidence.json` (if applicable)

---

## 2) For each completed window: generate completion report

**Template reference**:
- VPS path: `/data/prometheus/v13_instructions/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md`

**Required steps**:
1. Read template from VPS instruction directory
2. Copy template structure
3. Fill facts only (no narrative)
4. Save as: `<window_dir>/V13_PHASE1_WINDOW_COMPLETION_REPORT.md`

**If contract is runnable**:
- Follow verifier instruction: `/data/prometheus/v13_instructions/V13_PHASE1_RUN_WORLD_CONTRACT_VERIFIER_ON_LIVE_WINDOW_EXEC_20260110.md`
- Run verifier and include verdict in completion report

---

## 3) What to observe (facts only, no interpretation)

### 3.1 Phenomena to record in `phenomena.log.md`

**Observed** (if any):
- Stable connection (no reconnects)
- Data gaps / missing periods
- API errors / rate limits
- Schema changes / field disappearance
- Connection drops / persistent disconnects

**Not observed** (if relevant):
- No gate activity
- No adjudication
- No specific phenomenon

**Notes** (factual only):
- Observation start/stop times
- Any interruption facts

### 3.2 Window verdict assignment

**Rules** (per V13 Capture Window Minimal Contract):
- `MEASURABLE`: Window produced measurable evidence chain
- `NOT_MEASURABLE`: Window failed measurability gate (missing key world evidence)
- `INTERRUPTED`: Observation did not complete as intended
- `REJECTED_BY_WORLD`: World actively refused observation

**Assign based on facts only** (no interpretation).

---

## 4) Return to Research (after each window completion)

**Send back** (facts only):
- Quant commit hash
- Window directory absolute path (VPS)
- Completion report absolute path (VPS)
- Verifier JSON (if contract was runnable)

**Do NOT send**:
- Analysis / interpretation
- Suggestions for "fixing" issues
- Market predictions / explanations

---

## 5) Stop conditions (if triggered, record as facts)

**Reference**: Stop conditions checklist (in completion report template)

**If any stop condition triggers**:
- Record in `phenomena.log.md` (facts only)
- Assign appropriate `verdict.md` token
- Generate completion report
- Return to Research

**Do NOT**:
- Try to "fix" the stop condition
- Continue running if stop condition is persistent
- Hide stop conditions in reports

---

## 6) Success criteria (Phase 1)

**We are successful if**:
- We have multiple windows (≥2) with 3 textual files each
- We can point to at least one observable phenomenon:
  - ✅ cooperate (already seen)
  - silence (if world goes silent)
  - refusal (if world refuses)
  - drift (if world changes behavior)

**We are NOT trying to**:
- Achieve perfect stability
- Collect 7-day continuous data
- Run adjudication
- Compute L / gates

---

## 7) Immediate next action

**Continue running recorder** (best-effort):
- Start new window (duration flexible)
- Collect data
- On stop: generate 3 window files + completion report
- Return facts to Research

**No pressure, no deadlines**. Focus on: "what did the world do?"

---

**Note**: This is Phase 1 observation-first. We are building a sensor, not a production system.
