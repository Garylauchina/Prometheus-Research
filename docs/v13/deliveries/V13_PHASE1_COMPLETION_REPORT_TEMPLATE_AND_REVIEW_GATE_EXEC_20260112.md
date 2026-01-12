# Delivery — Quant Instructions — V13 Phase 1: Completion Report Template + Review Gates (stop conditions + verdict mapping) — 2026-01-12

Repo (Research): `/Users/liugang/Cursor_Store/Prometheus-Research`  
Target (Quant): produce completion report for every capture window (facts only).

This instruction file (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md`

---

## 0) What changed (read first)

We are engineering Phase 1 stop conditions into an auditable **review gate**, and freezing consistency between:
- window verdict (`verdict.md`), and
- contract verdict (World Contract v0.2 verifier).

This is **not** analysis. It is evidence-chain hygiene.

---

## 1) Use the frozen completion report template (copy verbatim, then fill facts)

Template (absolute path):
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/templates/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_V0_20260112.md`

Rules:
- Facts only.
- No narrative/causal explanations.
- Must include:
  - window verdict token
  - contract verdict (when runnable)
  - mapping consistency self-check (tick boxes)
  - stop conditions checklist (tick boxes)

---

## 2) Mandatory references (do not edit)

### 2.1 Window verdict ↔ Contract verdict mapping (frozen)
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/spec/V13_WINDOW_VERDICT_CONTRACT_VERDICT_MAPPING_V0_20260112.md`

### 2.2 Stop conditions checklist / review gate (frozen)
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/ops/V13_PHASE1_STOP_CONDITIONS_CHECKLIST_V0_20260112.md`

---

## 3) Where to store the report (Quant side; suggested only)

Suggested (non-binding):
- `<window_dir>/V13_PHASE1_WINDOW_COMPLETION_REPORT.md`

The report MUST include absolute paths to:
- `window.meta.yaml`
- `phenomena.log.md`
- `verdict.md`
- `evidence.json` (if produced)
- verifier JSON (if runnable)

---

## 4) When contract is runnable, run verifier and archive JSON (facts only)

Follow existing delivery:
- `/Users/liugang/Cursor_Store/Prometheus-Research/docs/v13/deliveries/V13_PHASE1_RUN_WORLD_CONTRACT_VERIFIER_ON_LIVE_WINDOW_EXEC_20260110.md`

Then paste:
- `contract_verdict`
- `contract_reason_codes`
- verifier JSON absolute path
into the completion report.

---

## 5) Return to Research (facts only)

Send back:
- Quant commit hash
- window_dir absolute path
- completion report absolute path
- (if any) verifier JSON content or file pointer

