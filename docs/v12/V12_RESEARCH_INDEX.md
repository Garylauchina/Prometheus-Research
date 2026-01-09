# V12 Research Index (English)

Positioning (frozen):
- **V10 = the evidence chain is born**
- **V11 = the evidence chain is industrialized**
- **V12 = world modeling + life system comes online**

This index is the single command center for V12 (SSOT index). From now on, new V12 documents must live under `docs/v12/` (additive-only).

---

## Start Here

V12’s first phase does one thing only: **world modeling**—turn it into reproducible facts, so genome design does not drift into subjective knobs.

Hard gates (frozen):
- **Genome expansion is postponed**: we only enter “new dimensions / expansion” after the world scanner is staged to functional completeness + tools verification passes + modeling SSOT is accepted. Otherwise everything is NOT_READY (avoid pre-baked subjective knobs).
- **Minimal genome refactor allowed (v0)**: only alignment/classification/naming convergence (e.g. `control_class`, mapping tables, dangling-knob scans). No new semantic dimensions.

Evolution constitution (frozen entry):
- **Epoch Constitution (maximal contiguous interval with invariant semantics)**: `docs/v12/V12_SSOT_EPOCH_CONSTITUTION_20260102.md`
  - Epochs are not time slices; they switch only on semantic breaks (operators/world contract/observation semantics).

Guiding axioms (frozen entry; not current tool acceptance items):
- **System-level vs Engineering-level axioms**: `docs/v12/V12_SSOT_AXIOMS_SYSTEM_AND_ENGINEERING_20260103.md`

Individual balance (Δ-event driven, frozen entry):
- **Agent Balance Delta + Exchange Auto Events**: `docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`
  - Broker emits Δbalance only (idempotent event_id + evidence_ref). Exchange-initiated events must be recorded truthfully (account-level truth).

Methodology reminders (frozen):
- Even millions of agents and tens of thousands of runs cover only a tiny fragment of evolutionary space. V12 does not aim to “cover the space”, but to find **repeatable, comparable, transferable local regularities** under an evidence contract.
- Therefore V12 priority is always: freeze world inputs / evidence discipline / NOT_MEASURABLE boundaries first, then mechanisms (metabolism / split reproduction) and genome dimensions.
- Any new dimension must pass **auditable + measurable + ablationable** verification before entering decision contracts; otherwise it is NOT_READY (see `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`).

Evidence path convention (frozen):
- V12 uses unified `runs_root/run_id` conventions: see “Evidence path convention” in `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`.

---

## V12 Mainline (light) — Version goals

This phase narrows to 6 items (dependency order):

- **World Feature Scanner (modeling tool, independent)**
  - Positioning: modeling/measurement tool, not production-required; no VPS container deployment requirement (see Scanner SSOT).
  - Scope: only “API-visible parameter structures” (request/response/schema + NOT_MEASURABLE boundaries); no order lifecycle/microstructure inference (e.g. fill_ratio).
  - Outputs: `market_snapshot.jsonl` + `okx_api_calls.jsonl` + `scanner_report.json` + `run_manifest.json` (strict JSONL / replayable / fail-closed).
  - Base-dimensions principle: Scanner-derived dimensions are **base dimensions**; evolution may down-weight them, but manual pruning is forbidden. Unknowns must be `null + reason_codes` (additive-only).

- **Interaction impedance probe (integrated into Scanner, independent measurement)**
  - Positioning: account-local truth (latency/reject/rate-limit buckets), used for modeling and later feedback; independent of Broker.
  - Outputs: `interaction_impedance.jsonl` (strict JSONL, append-only) + evidence references.

- **Genome refactor (alignment/classification, no expansion)**
  - Goal: separate agent-expressible vs proposable vs system facts (`control_class`), and complete dangling-knob scans + alignment table templates.

- **Tick polling loop (world-input main driver)**
  - Goal: drive world input via tick + REST snapshots first (no DSM/event-driven dependency).

- **Simple death judgment (v0)**
  - Goal: minimal auditable, fail-closed death verdict interface (no complex aging/irreversible damage yet).
  - Hard red-line (frozen): death verdict must NOT be smuggled into reward shaping (see Life SSOT).

- **ROI-doubling split reproduction (v0)**
  - Goal: define reproduction trigger and evidence interfaces (do not require near-term doubling samples; acceptance is evidence closure).

SSOT entry points:
- Scanner (tool positioning + probes + optional impedance probe): `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
- Scanner E schema（REST snapshot）：`docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Base dimensions (E/I/M base-dimensions contract): `docs/v12/V12_SSOT_BASE_DIMENSIONS_EIM_V0_20260104.md`
- Interaction impedance evidence (v0 schema entry): `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md` (§1.1.1)
- Alignment / control_class：`docs/v12/V12_SSOT_OKX_ORDER_PARAMETER_SPACE_V1_20260103.md` + `docs/v12/V12_SSOT_OKX_ACCOUNT_POSITION_AND_PRETRADE_PARAMETER_SPACE_V1_20260103.md`
- Replay dataset (exchange snapshot → replay_truth baseline): `docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`
- Life (energy + death, red-line: death is NOT reward): `docs/v12/V12_SSOT_LIFE_ENERGY_AND_DEATH_V0_20260106.md`
- Ugly baseline (death-only, replay_truth): `docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`
- World-coupling experiment protocol (pre-registration + controls): `docs/v12/V12_SSOT_WORLD_COUPLING_EXPERIMENT_PROTOCOL_V0_20260107.md`
- D0 falsification death verdict (constitution-level stop rule): `docs/v12/V12_SSOT_D0_FALSIFICATION_DEATH_VERDICT_V0_20260107.md`
- Avoid Pit Handbook (append-only “pre-flight interrogation” gate): `docs/v12/V12_AVOID_PIT_HAND_BOOK_v1_20260108.md`
- Survival Space (E+M minimal contract): `docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md`
- Survival Difficulty (Local Reachability; M-frozen; measure next-step actionability neighborhood compression speed; SSOT v0): `docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- Survival Space v1.0.1 Fix-M extended validation (finalized artifacts): `docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`
- Survival Space v1.0.1 Fix-M extended validation milestone (append-only record): `docs/v12/V12_SURVIVAL_SPACE_EM_V1_0_1_FIX_M_EXTENDED_VALIDATION_MILESTONE_20260109.md`
- Survival Space poset/lattice falsification checklist (v0 draft): `docs/v12/V12_SURVIVAL_SPACE_POSET_LATTICE_FALSIFICATION_CHECKLIST_V0_DRAFT_20260109.md`
- Survival Space poset Round-1 result (incomparability test v0): `docs/v12/artifacts/survival_space_em/poset_round1_incomparability_v0_20260109/poset_round1_report.md`
- Survival Space poset §3 result (no informational gain test v0): `docs/v12/artifacts/survival_space_em/poset_section3_info_gain_v0_20260109/poset_section3_report.md`
- Survival Space poset Round-2 result (incomparability test v0; x2=downshift_rate): `docs/v12/artifacts/survival_space_em/poset_round2_incomparability_v0_20260109/poset_round2_report.md`
- Survival Space poset Round-2 §3 result (no informational gain test v0; dims=(suppression_ratio,downshift_rate)): `docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.md`
  - Verdict: **FAIL → poset is engineering-rejected for Survival Space v1.x; no further §1/§2 permitted**
- Survival Space execution checklist (acceptance gate): `docs/v12/V12_SURVIVAL_SPACE_EXPERIMENT_EXECUTION_CHECKLIST_V0_20260108.md`

Tools entry points (verifiers/tools):
- Base dimensions verifier (E/I/M): `python3 tools/v12/verify_base_dimensions_eim_v0.py --run_dir <RUN_DIR>`
- Scanner E schema verifier (market_snapshot canonical schema): `python3 tools/v12/verify_scanner_e_schema_v0.py --run_dir <RUN_DIR>`
- World structure gate (W0, world-coupling prerequisite): `python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`
- Genome alignment table verifier (V12.2, machine-readable): `python3 tools/v12/verify_genome_alignment_table_v0.py --input <genome_alignment_table.json>`
- Tick loop verifier (V12.3, sequence integrity): `python3 tools/v12/verify_tick_loop_v0.py --run_dir <RUN_DIR> --min_ticks <N>`
- Tick loop repeatability gate (V12.3, FAIL=0): `python3 tools/v12/verify_tick_loop_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --run_ids <run_id_1,run_id_2,...>`
- errors.jsonl summary (bucket statistics): `python3 tools/v12/summarize_errors_jsonl_v0.py --errors_jsonl <RUN_DIR>/errors.jsonl`
- Replay dataset builder: `python3 tools/v12/build_replay_dataset_v0.py --source_run_dir <QUANT_RUN_DIR> --output_root <DATASETS_ROOT>`
- Replay dataset verifier: `python3 tools/v12/verify_replay_dataset_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --max_jitter_ms 500`
- Ugly baseline verifier (death-only): `python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`
- Local Reachability verifier (Trial-0 / post-hoc evidence contract): `python3 tools/v12/verify_local_reachability_v0.py --run_dir <RUN_DIR>`
- Local Reachability summary (descriptive only, no thresholds/verdict): `python3 tools/v12/summarize_local_reachability_report_v0.py --run_dir <RUN_DIR> --output_json <RUN_DIR>/local_reachability_report.json`

## V12 mini-releases (recommended cadence)

Purpose: split V12 into controllable mini-releases. Each release completes one “auditable acceptance loop” to avoid goal explosion.

### Mainline mini-releases (light, recommended)

To avoid exponential complexity, the current mainline advances via “modeling tools + tick + life v0”, while DSM/event-driven are sealed/deferred.

- **V12.0 — Scanner v0 (REST snapshot, candidate schema, tools verification PASS)**
  - Scope: Mainline/Scanner
  - Acceptance: non-empty `market_snapshot.jsonl` + schema_verification PASS + replayable evidence (source_call_ids, etc.)
  - Note: schema `status` remains `candidate` (do not claim verified prematurely)

- **V12.0.1 — Scanner impedance probe v0 (optional write probes, independent)**
  - Scope: Mainline/Impedance (integrated into Scanner, default off)
  - Acceptance: when enabled, must produce `interaction_impedance.jsonl` (strict JSONL) and each record must include `account_id_hash + window + metrics + evidence_refs + verdict`; when disabled, must be explicitly NOT_MEASURABLE (no fake zeros).
  - Acceptance anchor (read-only, factual record):
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `e43ab4c`
    - Quant run_dir: `runs_v12_modeling_tool/run_scanner_v0_20260104T111402Z`
    - Research verifier:
      - `python3 tools/v12/verify_base_dimensions_eim_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_scanner_v0_20260104T111402Z`
      - expected: `PASS (exit 0)`

- **V12.1 — Scanner hardening (repeatability + strict evidence replayability)**
  - Scope: Mainline/Scanner iteration
  - Acceptance (machine-verifiable, frozen entry):
    - Run seed sweeps N times on the same machine (recommended N≥20) and produce auditable summary outputs
    - Run:
      - `python3 tools/v12/sweep_scanner_seeds.py --iterations N`
    - Pass conditions (v0.1):
      - `FAIL` count is 0 (fail-closed: missing required files / non-strict JSONL / schema break must be explicit FAIL)
      - `NOT_MEASURABLE` must be explainable (reason_codes aggregatable); no “overall PASS but critical fields silently missing”
    - E schema verification gate (added, frozen entry):
      - Batch-run E schema verifier across sweep run_ids; require `FAIL=0`
      - Run (example):
        - `python3 tools/v12/verify_scanner_e_schema_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --summary_json <seed_sweep_summary.json> --output <e_schema_gate_report.json>`
  - Repeatability acceptance anchor (read-only, factual record):
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `e43ab4c`
    - Quant outputs (local artifacts, not in git):
      - `runs_v12_modeling_tool/seed_sweep_summary_20260104T113247Z.json`
      - `runs_v12_modeling_tool/repeatability_reports_20260104T113247Z/aggregate.json`
    - Result: `100/100 PASS` (Research E/I/M verifier PASS, exit 0)
  - E schema gate 100x acceptance anchor (read-only, factual record):
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `4f360e4`
    - Quant outputs (local artifacts, not in git):
      - `runs_v12_modeling_tool/seed_sweep_summary_20260104T124247Z.json`
      - `runs_v12_modeling_tool/e_schema_gate_100x_20260104T124247Z/aggregate.json`
      - `runs_v12_modeling_tool/e_schema_gate_100x_20260104T124247Z/verify_*.json` (100 files)
    - Result: `E schema canonical PASS 100/100` + `FAIL 0/100` (exit 0)
    - Note: reports may include commentary; but all evidence `.jsonl` must be strict JSONL (no inline `//` comments).

- **V12.2 — Genome refactor v0 (alignment + control_class, no expansion)**
  - Scope: Mainline/Genome refactor
  - Acceptance (machine-verifiable, frozen entry):
    - `genome_alignment_table.json` must be machine-readable and pass verifier:
      - `python3 tools/v12/verify_genome_alignment_table_v0.py --input docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json` (template self-check)
      - For a real table: `python3 tools/v12/verify_genome_alignment_table_v0.py --input <genome_alignment_table.json>`
    - `control_class` must be from the frozen set: `system_fact|agent_expressible|agent_proposable|system_controlled`
    - Dangling knob scan must be runnable and explainable:
      - For any broker run_dir with verdict=PASS:
        - `python3 tools/v12/scan_alignment_drift_v0.py --run_dir <BROKER_RUN_DIR> --template docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json`
      - Pass condition: `unmapped_attempt_fields` is empty (execution/audit metadata must be filtered out)
  - Acceptance anchor (read-only, factual record):
    - Broker run_id: `run_broker_uplink_v0_20260102T093735Z`
    - Report: `runs_v12/run_broker_uplink_v0_20260102T093735Z/alignment_drift_report.json`
    - Result: `issue_count=0` + `unmapped_attempt_fields=[]` + `important_non_order_knobs_observed=[]` (PASS)

- **V12.3 — Tick loop v0 (polling world, evidence-first)**
  - Scope: Mainline/Tick
  - SSOT: `docs/v12/V12_SSOT_TICK_LOOP_V0_20260104.md`
  - Acceptance (machine-verifiable, frozen entry):
    - Produce a single run_dir containing multi-tick `market_snapshot.jsonl` sequence (strict JSONL)
    - `market_snapshot.jsonl` passes E schema verifier:
      - `python3 tools/v12/verify_scanner_e_schema_v0.py --run_dir <RUN_DIR>`
    - Tick sequence integrity passes tick verifier (FAIL=0):
      - `python3 tools/v12/verify_tick_loop_v0.py --run_dir <RUN_DIR> --min_ticks <N> --max_backward_ms 0`
    - Fail-closed: missing required files / non-strict JSONL / ts rollback / duplicate snapshot_id → FAIL
  - Repeatability gate (recommended as V12.3.1, frozen entry):
    - Run tick loop N times in the same environment (recommended N≥20), collect run_ids
    - Batch-run against run_ids:
      - `python3 tools/v12/verify_tick_loop_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --run_ids <...> --min_ticks 120 --max_backward_ms 0 --output <tick_gate_aggregate.json>`
    - Pass condition: `FAIL=0` (NOT_MEASURABLE is allowed, but reasons must be aggregatable)
    - Summarize each run’s `errors.jsonl` (for later impedance/environment-feedback semantics):
      - `python3 tools/v12/summarize_errors_jsonl_v0.py --errors_jsonl <RUN_DIR>/errors.jsonl --output <errors_summary.json>`
  - Acceptance anchor (read-only, factual record):
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `790f984`
    - Quant run_dir: `runs_v12/run_tick_loop_v0_20260104T132154Z`
    - Evidence summary (reported):
      - `market_snapshot.jsonl`: 120 lines (120 ticks)
      - `okx_api_calls.jsonl`: 600 calls (5 endpoints × 120 ticks)
      - `errors.jsonl`: 8 records (network/connection errors)
    - Tick loop verifier:
      - `python3 tools/v12/verify_tick_loop_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_tick_loop_v0_20260104T132154Z --min_ticks 120 --max_backward_ms 0`
      - expected: `exit 0` + `verdict=NOT_MEASURABLE` (degraded but valid: errors.jsonl non-empty)
    - Note: reports may include commentary; but all evidence `.jsonl` must be strict JSONL (no inline `//` comments).
  - Repeatability campaign (N=20, FAIL=0) anchor (read-only, factual record):
    - Gate report: `runs_v12/tick_loop_gate_aggregate_v3.json` (Quant local artifact)
    - Run IDs file: `/tmp/tick_run_ids_campaign.txt` (local)
    - Errors summaries:
      - `runs_v12/tick_errors_summaries_campaign_20260104T191027Z/aggregate_errors_summary.json`
      - by_error_type (20 runs aggregated): `get_books_unavailable=19`, `get_index_tickers_unavailable=17`, `get_mark_price_unavailable=15`, `get_funding_rate_unavailable=13`, `get_ticker_unavailable=5`

- **V12.3.2 — Replay dataset v0 (exchange snapshot recording → replay_truth baseline)**
  - Scope: Baseline infrastructure (offline replay, seed-stability stress)
  - SSOT: `docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`
  - Acceptance (machine-verifiable):
    - Build a dataset from a Quant run_dir that already contains canonical `market_snapshot.jsonl`
    - Verify dataset PASS (or NOT_MEASURABLE due to tick jitter; hard failures are reserved for missing evidence / non-strict JSONL / backward time / duplicates):
      - `python3 tools/v12/verify_replay_dataset_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --max_jitter_ms 500`
    - Hard rule: dataset is a **local artifact** (not committed to git); only SSOT + verifier are in git
  - Acceptance anchor (read-only, factual record):
    - Quant tick run_id: `run_tick_loop_v0_20260106T083725Z`
    - Quant tick run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_tick_loop_v0_20260106T083725Z`
    - Dataset dir (local artifact): `/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_BTC-USDT-SWAP_20260106T083725.364788Z_20260106T105939.297603Z_1000ms`
    - Dataset verifier verdict: `NOT_MEASURABLE` (tick interval unstable: violations=2225/4999, ratio=0.445; delta_ms_min=941, delta_ms_max=13211)

- **V12.3.3 — Ugly baseline v0 (death-only, replay_truth; evidence closure)**
  - Scope: Baseline calibration (plumbing + red-line enforcement)
  - SSOT: `docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`
  - Verifier:
    - `python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`
  - Acceptance anchor (read-only, factual record):
    - Baseline run_dir: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_ugly_baseline_v0_20260106T115105Z`
    - Verifier verdict: `PASS`
    - Extinction tick (observed): `100` (agent_count=100, E0=100, delta=-1)

- **V12.3.4 — Ugly baseline v0_dirty (random action_cost; 50-seed sweep)**
  - Scope: Fast sanity check to break determinism (still **no reward→energy**, red-line preserved)
  - Status: experimental extension (does NOT replace v0_baseline acceptance)
  - Evidence (local artifacts):
    - Summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_dirty_random_cost_50seeds_CLEAN_summary_20260106T121350Z.json`
    - Acceptance report: `/tmp/V12_UGLY_BASELINE_V0_DIRTY_ACCEPTANCE_20260106.md`
  - Result (50 seeds, survival_cost_uniform_max=2.0):
    - extinction_tick mean=55.56, std=1.00, range=[54,59]
  - Quant commits (implementation facts):
    - `5f9134e` feat: add v0_dirty_random_cost extension (mode/rng_seed/survival_cost_uniform_max)
    - `f555f67` fix: run_id collision (nanosecond + seed suffix)

- **V12.3.5 — Ugly baseline v0.1 (decision-cost; deterministic negative control)**
  - Scope: Show that “reading world input” alone does not imply world affects survival (must connect to action_cost/impedance_cost).
  - Evidence (local artifact):
    - Summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_1_decision_cost_50seeds_summary_20260106T123740Z.json`
  - Result (50 seeds):
    - extinction_tick: mean=67, std=0.0, range=[67,67]
    - reject/invalid: 0% (invalid_ratio_mean=0.0)
  - Interpretation (frozen): deterministic extinction is expected if all alive agents receive identical per-tick costs.

- **V12.3.5.1 — Ugly baseline v0.1 reject-stress (action_cost invalid penalty; 20000 steps + dataset wrap)**
  - Scope: force “proposal invalid / reject-like” events to become **measurable** (target reject_rate ≥ 20%), to test whether the “world → proposal → cost → death” chain is intact.
  - Evidence (local artifacts; raw output reported by user):
    - Runs root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (101 run_dirs: 100-seed sweep + 1 smoke)
    - Raw summary JSON: `runs_v12/v0_1_reject_stress_100seeds_raw_summary.json`
    - Raw text bundle: `docs/v12/V12_V0_1_REJECT_STRESS_100SEED_RAW_OUTPUT_20260106.txt`
  - Result (100-seed list; reported):
    - extinction_tick: mean=27.40, std=2.92, range=[22,35]
    - reject_rate: mean=30.20%, std=1.31%
  - Friend gate verdict (factual):
    - `reject_rate > 20%` ⇒ **PASS (chain intact)**
    - `extinction std > 10~20` ⇒ **NOT MET** (std=2.92)
  - Note (scale reality): with `E0=100` and invalid penalty `10..30`, extinction is expected to occur very early; 20000-step runs mostly record “post-extinction ticks”. Observing “survival tails / phase stability” requires aligning the time scale (e.g. increase E0 or reduce penalty), without touching the red-line (still no reward→energy).

- **V12.3.5.2 — Ugly baseline v0.3 reject-stress (dynamic threshold + harsher penalties; 30000 steps + dataset wrap)**
  - Scope: push reject-stress harder (dynamic invalid threshold), and run longer steps (30000) to test whether “tails / phase stability” can appear under a stronger reject process.
  - Evidence (local artifacts; raw output reported by user):
    - Quant commit: `8172caa` (branch: `v12-broker-uplink-v0`)
    - Runs root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (154 run_dirs reported)
    - Summary JSON: `runs_v12/v0_3_reject_stress_150seeds_raw_summary_20260106T152605Z.json`
    - Raw bundle: `/tmp/V0_3_REJECT_STRESS_FINAL_RAW_OUTPUT_20260106.txt`
  - Result (150 values list; reported):
    - extinction_tick: mean=13.95, std=1.42, range=[12,18]
    - reject_rate: mean=78.58%, std=6.53%
  - Friend gate verdict (factual):
    - `reject_rate mean >= 30%` ⇒ **PASS**
  - Note (scale reality): extinction at ~14 ticks implies the 30000-step run is still dominated by “post-extinction ticks”; “tails / phase stability” remain not observable unless the time scale is aligned (raise E0 and/or reduce penalties) while keeping the red-line (no reward→energy).

- **V12.3.5.3 — Ugly baseline v0.4 tail_reject_stress (tail-friendly scale; 50000 steps; 200 seeds)**
  - Scope: rebalance reject process to enable longer survival and visible tail distribution, while keeping the hard red-line (NO reward→energy; death is energy-only).
  - Evidence (local artifacts; reported):
    - Quant commits: `678e4a0`, `047629c`, `d81ba6d` (branch: `v12-broker-uplink-v0`)
    - Runs root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (200 run_dirs: `seed[1..200]`)
    - Summary JSON: `runs_v12/v0_4_tail_reject_stress_200seeds_raw_summary_20260106T154931Z.json`
    - Summarizer: `tools/v12/summarize_v0_4_tail_reject_stress_200seeds_raw.py` (includes admit-rule print)
  - Result (reported):
    - extinction_tick: mean=183, std=15.04, range=134
    - reject_rate: mean=50.06% (note: slightly above the suggested 50% upper bound)
  - Admit rule (reported): NOT triggered (std=15.04 > 10 AND range=134 > 50)
  - Note (friend’s “hope” target): if requiring `std>50` and `range>200`, this run set does **not** meet that stronger target yet; it does demonstrate a measurable tail widening relative to v0.3 (std 1.42, range 6).

- **V12.3.5.4 — Ugly baseline v0.5 dirty_tail (early stop; 100000 steps target; 300 seeds)**
  - Scope: “ultimate dirty” stress with **early stop on extinction** (reality constraint) to enable large seed campaigns without wasting post-extinction ticks.
  - Evidence (reported):
    - Quant commits: `d1f9a87`, `1195fa9` (branch: `v12-broker-uplink-v0`)
    - Runs root: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/` (305 run_dirs reported; seeds `1..300`)
    - Summary JSON: `runs_v12/v0_5_dirty_tail_300seeds_raw_summary_*.json`
    - Summarizer: `tools/v12/summarize_v0_5_dirty_tail_300seeds_raw.py` (4 gate checks)
  - Result (reported; early stop enabled):
    - extinction_tick: mean=168, std=11.99, range=67 (142..209)
    - reject_rate: mean=59.97%, std=0.45%
    - alive@5000: 0% (all extinct before tick 5000)
  - Gate checks (reported): 0/4 passed (FAIL)
  - Note (factual): early stop reduced effective ticks to ~300×168 ≈ 50,400 (≈99.5% saved vs 300×100,000).

- **V12.3.6 — Ugly baseline v0.2 (impedance-cost; world measurability affects energy)**
  - Scope: Map world measurability (snapshot quality) into energy via `impedance_cost` (still no reward→energy).
  - Evidence (local artifact):
    - Summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_impedance_cost_50seeds_summary_20260106T124935Z.json`
  - Result (50 seeds):
    - extinction_tick: mean=53.04, std=0.445, range=[52,54]
    - impedance_triggered_ratio: mean=0.0586, std=0.0
  - Note (factual): impedance_triggered_ratio is constant across seeds (same replay dataset quality sequence); extinction variation comes from cost sampling conditional on that sequence.

- **V12.3.7 — Ugly baseline v0.2_extreme (gauss init stress; 5000 steps)**
  - Scope: stress-test extinction distribution sensitivity to **initial energy distribution** (gauss init) under the death-only red-line (no reward→energy).
  - Evidence (local artifact):
    - Summary JSON: `/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_extreme_summary_20260106T133241Z.json`
  - Result (factual, from summary JSON):
    - run_dirs=101 (unique_seeds=100; `rng_seed=1` was run twice)
    - extinction_tick: mean=88.7921, std=5.7381, range=[77,100]
    - impedance_triggered_ratio: mean=0.0, std=0.0
  - Note (fail-closed semantics): since impedance_triggered_ratio is 0.0, **this run set did not exercise the “NOT_MEASURABLE snapshot → impedance_cost” branch**; treat it as “gauss-init extinction distribution” evidence, not as “high-impedance” evidence.

- **V12.4 — Life v0 (death-only baseline, no reproduction yet)**
  - Scope: Mainline/Life
  - Acceptance: evidence-backed **death** interfaces exist (event interfaces + evidence persistence + fail-closed). Reproduction is explicitly deferred.

---

### Capability sealed / deferred

The following capabilities are validated/optional, but are not mainline dependencies for now:

- DSM/WS ingestion (sealed capability + stability integration gate): `docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
- Dual-pipe joins (DSM↔Decision↔Broker): deferred until DSM long-run stability passes
- Settlement / account-level auto events: preserved as a life-system truth capability, but not required for “modeling tools + tick + life v0”

### M0 — World Feature Scanner v0 (E: market info, single instId)

- **Scope (frozen)**:
  - Only `BTC-USDT-SWAP`
  - Read-only market info first (E/exogenous)
- **SSOT**:
  - World Feature Scanner: `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
  - Scanner v0 E schema (V12): `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - OKX contract + order parameter space: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md` (§12)
- **Acceptance**:
  - Scanner produces a run_dir with `run_manifest.json`, `okx_api_calls.jsonl`, `errors.jsonl`, `scanner_report.json`
  - Must produce non-empty `market_snapshot.jsonl`
  - Any endpoint failure must be NOT_MEASURABLE (with reason_code), never silent
  - Tools verification must pass for canonical schema (candidate→verified) before modeling can consume it

### M0.5 — WS ingestion only (event stream evidence, tick-consumable)

Purpose: resolve the dilemma “no WS blocks event-driven/metabolism/reproduction; jumping straight to WS is a big project”.  
First, make WS an **auditable event-stream input**, while the decision/evolution system is not forced to go event-driven yet (still tick/sample consumable).

- **Scope (frozen)**:
  - OKX public WS (`/ws/v5/public`) only
  - Evidence-only ingestion: subscribe + message stream persisted
  - Map WS messages → canonical `market_snapshot.jsonl` (or future `market_event_ref`) with mask discipline
- **SSOT**:
  - Scanner v0/v0.5 schema: `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - Downlink subscription manager (DSM): `docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
  - Uplink/Downlink pipes + evidence + join keys: `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`
- **Acceptance**:
  - WS sessions/requests/messages evidence exists (append-only)
  - `market_snapshot.jsonl` can be produced from WS without breaking schema_verification rules
  - No silent reconnect/subscription loss (must be visible as NOT_MEASURABLE reasons)

### M0.5 Implementation status snapshot (append-only factual record)

Implemented (VPS REAL WS acceptance passed):
- Downlink evidence: `okx_ws_sessions.jsonl` / `okx_ws_requests.jsonl` / `okx_ws_messages.jsonl`
- Canonical: `market_snapshot.jsonl` (with `source_message_ids` replay anchors)
- Verifier rule: when `tools/v12/verify_dsm_ws_ingestion_v0.py` outputs PASS, the manifest must sync `verdict="PASS"`; if any `not_measurable:*` reason_codes exist, verdict must be NOT_MEASURABLE (fail-closed)

Frozen minimal channel set (v0.9.1 reference implementation):
- `tickers`（instId=`BTC-USDT-SWAP`）→ `last_px`
- `mark-price`（instId=`BTC-USDT-SWAP`）→ `mark_px`
- `books5`（instId=`BTC-USDT-SWAP`）→ `bid_px_1/ask_px_1/bid_sz_1/ask_sz_1`
- `index-tickers` (instId=`BTC-USDT`) → `index_px` (note the underlying mapping)
- `funding-rate`（instId=`BTC-USDT-SWAP`）→ `funding_rate/next_funding_ts_ms`

### M1 — Modeling docs from scanner (SSOT, additive-only)

- Freeze:
  - Market feature schema (E dims) + mask/quality/reason_code
  - Exchange API parameter spaces (order/cancel/replace, etc.)
  - NOT_MEASURABLE conditions and ecological fences (rate limits, endpoint availability)
- **SSOT**:
  - Modeling docs pipeline + genome alignment table: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`

### M2 — Genome refactor aligned to parameter spaces

- Freeze:
  - Genome dimensions must map to exchange parameter spaces (no invented knobs)
  - Separate: agent expresses vs system defaults vs gate decisions

### M3 — Event-driven (initial)

- Market data: WS push (with evidence discipline)
- Trading: REST (request/response evidence)

### M4 — Life system (metabolism + split reproduction)

- Metabolism replaces “death judgment”
- Capital-doubling split reproduction replaces “reproduction judgment”

---

## Cross-version anchors (read-only)

- V11 index: `docs/v11/V11_RESEARCH_INDEX.md`
- Agent probing + Proxy Trader: `docs/v11/V11_SSOT_AGENT_PROBING_AND_PROXY_TRADER_MODEL_20260101.md`
- Trade chain evidence: `docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`


