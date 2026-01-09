# V12 Research Index / V12 研究入口（中文为主）

定位（冻结）：
- **V10 = 证据链诞生**
- **V11 = 证据链工业化**
- **V12 = 世界建模与生命系统上线**

本 index 是 V12 的唯一指挥台（SSOT index）。从现在开始，V12 新增文档只写入 `docs/v12/`（additive-only）。

---

## Start Here

V12 的第一阶段只做一件事：**世界建模**，并将其变成可复现事实，避免基因维度设计漂移成主观拍脑袋。

硬 gate（冻结）：
- **基因扩维后置**：必须等“世界扫描器分批实现到阶段性全功能 + tools 验证通过 + 建模文档（SSOT）验收通过”，才能进入“新增维度/扩维”。否则一律视为 NOT_READY（避免先验基因导致漂移）。
- **允许的最小基因重构（v0）**：仅做“对齐/分类/命名收敛”（例如 `control_class`、映射表、悬空旋钮扫描），不引入未经验证的新维度语义。

演化宪法（冻结入口）：
- **Epoch Constitution（语义不变的最大连续区间）**：`docs/v12/V12_SSOT_EPOCH_CONSTITUTION_20260102.md`
  - Epoch 不是时间切片，只在“语义断裂”时切换（算子/世界合同/观测口径任一变化即切 epoch）

指导性公理（冻结入口；不作为当前版本的工具验收项）：
- **System-level vs Engineering-level axioms**：`docs/v12/V12_SSOT_AXIOMS_SYSTEM_AND_ENGINEERING_20260103.md`

个体 balance（Δ事件驱动，冻结入口）：
- **Agent Balance Delta + Exchange Auto Events**：`docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`
  - Broker 只推送 Δbalance（幂等 event_id + evidence_ref），交易所自动处置必须如实落盘（account-level truth）

方法论提醒（冻结）：
- 即使同时跑百万 Agent、跑万次实验，整体仍然只是演化空间中的**极小碎片**；V12 不追求“覆盖空间”，而追求在证据链约束下的 **可复现、可比较、可迁移的局部规律**。
- 因此，V12 的优先级始终是：先把世界输入/证据落盘/NOT_MEASURABLE 边界冻结成合同，再谈机制（新陈代谢/分裂繁殖）与基因维度。
- 任何新维度进入决策前必须先通过 **可审计+可测+可消融** 的验证；否则一律视为 NOT_READY（见：`docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`）。

证据路径约定（冻结）：
- V12 统一 `runs_root/run_id`：见 `docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md` 的 “Evidence path convention”。

---

## V12 Mainline (light) — 版本目标（轻装上阵）

本阶段把目标收敛为 6 件事（按依赖顺序）：

- **World Feature Scanner（建模工具，独立）**
  - 定位：建模/测量工具，不是系统运行必备；不要求部署到 VPS 容器（见 Scanner SSOT）。
  - 口径：只负责“API 可直接获取/返回的参数结构与字段空间”（request/response/schema + NOT_MEASURABLE 边界）；不承担订单生命周期/微结构推断（例如 fill_ratio）。
  - 产物：`market_snapshot.jsonl` + `okx_api_calls.jsonl` + `scanner_report.json` + `run_manifest.json`（strict JSONL / 可回放 / fail-closed）。
  - 基本维度原则：Scanner 落盘的维度特征属于 **基本维度（base dimensions）**，可被演化筛选，但不得人为删减；不可测必须走 `null + reason_codes` 的 NOT_MEASURABLE 纪律（只允许 additive 增补）。

- **Interaction impedance probe（并入 Scanner，独立测量）**
  - 定位：account-local truth（执行摩擦/延迟/拒单/限速桶），用于建模与后续裁决输入；不依赖 Broker。
  - 产物：`interaction_impedance.jsonl`（strict JSONL, append-only）+ 对应 probes 的证据回指（见 SSOT）。

- **Genome refactor（对齐/分类，不扩维）**
  - 目标：把“可表达/可提议/系统事实”分清（`control_class`），并完成悬空旋钮扫描与对齐表模板落盘。

- **Tick 周期轮询（世界输入主循环）**
  - 目标：先采用 tick + REST snapshot 的方式驱动世界输入（不依赖 DSM/event-driven）。

- **简单死亡判定（v0）**
  - 目标：定义一个最小、可审计、fail-closed 的死亡裁决接口（不引入复杂老化/不可逆损伤机制）。
  - 冻结红线：**绝对禁止**把“死亡裁决”偷偷变成 reward shaping 的一部分（见 Life SSOT）。

- **ROI 翻倍繁殖（v0）**
  - 目标：定义繁殖触发与证据接口（不追求短期必然出现翻倍样本；验收以证据闭环为主）。

SSOT 入口：
- Scanner（工具定位 + probes + 可选阻抗探针）：`docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
- Scanner E schema（REST snapshot）：`docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
- Base dimensions（E/I/M 基础维度合同）：`docs/v12/V12_SSOT_BASE_DIMENSIONS_EIM_V0_20260104.md`
- Interaction impedance evidence（v0 schema 入口）：`docs/v12/V12_SSOT_UPLINK_DOWNLINK_PIPES_AND_EVIDENCE_20260101.md`（§1.1.1）
- Alignment / control_class：`docs/v12/V12_SSOT_OKX_ORDER_PARAMETER_SPACE_V1_20260103.md` + `docs/v12/V12_SSOT_OKX_ACCOUNT_POSITION_AND_PRETRADE_PARAMETER_SPACE_V1_20260103.md`
- Replay dataset（交易所快照 → replay_truth baseline）：`docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`
- Life（能量 + 死亡；红线：死亡不是 reward）：`docs/v12/V12_SSOT_LIFE_ENERGY_AND_DEATH_V0_20260106.md`
- Ugly baseline（只做死亡，replay_truth）：`docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`
- World-coupling 实验协议（预注册 + 消融/负对照）：`docs/v12/V12_SSOT_WORLD_COUPLING_EXPERIMENT_PROTOCOL_V0_20260107.md`
- D0 证伪死亡判决（宪法级停止规则）：`docs/v12/V12_SSOT_D0_FALSIFICATION_DEATH_VERDICT_V0_20260107.md`
- V12 避坑手册（append-only，上线前“六拷问”门禁）：`docs/v12/V12_AVOID_PIT_HAND_BOOK_v1_20260108.md`
- Survival Space（E+M 最小合同）：`docs/v12/V12_SSOT_SURVIVAL_SPACE_EM_V1_20260108.md`
- Survival Difficulty（Local Reachability；冻结 M；测量“下一步可行动邻域”收缩速度；SSOT v0）：`docs/v12/V12_SSOT_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_V0_20260109.md`
- World pressure 候选工具（EDoF v0；Trial-6 后工程否决）：`docs/v12/V12_SSOT_WORLD_PRESSURE_EFFECTIVE_DOF_V0_20260109.md`
- World pressure Trial-6（BTC do-or-die 定标；verdict=FAIL；工具退场）：`docs/v12/artifacts/world_pressure_edof/trial6_btc_do_or_die_v0_20260109/trial6_world_pressure_edof_report.md`
- World pressure 候选工具（Gate Transfer / Suppression v0；Trial-7 后工程否决）：`docs/v12/V12_SSOT_WORLD_PRESSURE_GATE_TRANSFER_V0_20260109.md`
- World pressure Trial-7（BTC do-or-die 定标；verdict=FAIL；工具退场）：`docs/v12/artifacts/world_pressure_gate_transfer/trial7_btc_do_or_die_v0_20260109/trial7_world_pressure_gate_transfer_report.md`
- World pressure 工具（Boundary Signal / Changepoint v0；Trial-8 PASS）：`docs/v12/V12_SSOT_WORLD_PRESSURE_BOUNDARY_SIGNAL_V0_20260109.md`
- World pressure Trial-8（BTC do-or-die 变点检测；verdict=PASS）：`docs/v12/artifacts/world_pressure_boundary/trial8_btc_do_or_die_changepoint_v0_20260109/trial8_world_pressure_boundary_report.md`
- Trial-9 BTC epoch 标注（从 world_u 变点生成；verdict=PASS；纯标注）：`docs/v12/artifacts/world_pressure_epoch_annotation/trial9_btc_epoch_annotation_v0_20260109/trial9_epoch_annotation_report.md`
- Trial-9 pre-reg（仅做 epoch 标注）：`docs/v12/pre_reg/V12_WORLD_PRESSURE_EPOCH_ANNOTATION_TRIAL9_BTC_V0_20260109.md`
- Local Reachability Trial-4（world-conditioned impedance，封存产物）：`docs/v12/artifacts/local_reachability/trial4_world_conditioned_impedance_v0_20260109/README.md`
- Local Reachability Trial-5（BTC 单世界定标，verdict=FAIL；lens 退场）：`docs/v12/artifacts/local_reachability/trial5_btc_world_pressure_calibration_v0_20260109/trial5_btc_world_pressure_calibration_report.md`
- Local Reachability Trial-5 pre-reg（冻结阈值 + stop rule）：`docs/v12/pre_reg/V12_SURVIVAL_DIFFICULTY_LOCAL_REACHABILITY_TRIAL5_BTC_WORLD_PRESSURE_CALIBRATION_V0_20260109.md`
- Survival Space v1.0.1 Fix-M 扩展验证（封存产物）：`docs/v12/artifacts/survival_space_em/v1_0_1_fixm_extended_validation_20260109/README.md`
- Survival Space v1.0.1 Fix-M 扩展验证里程碑（append-only 记录）：`docs/v12/V12_SURVIVAL_SPACE_EM_V1_0_1_FIX_M_EXTENDED_VALIDATION_MILESTONE_20260109.md`
- Survival Space 偏序/格 证伪清单（v0 草案）：`docs/v12/V12_SURVIVAL_SPACE_POSET_LATTICE_FALSIFICATION_CHECKLIST_V0_DRAFT_20260109.md`
- Survival Space 偏序 Round-1 结果（不可比饱和测试 v0）：`docs/v12/artifacts/survival_space_em/poset_round1_incomparability_v0_20260109/poset_round1_report.md`
- Survival Space 偏序 §3 结果（信息增益失败测试 v0）：`docs/v12/artifacts/survival_space_em/poset_section3_info_gain_v0_20260109/poset_section3_report.md`
- Survival Space 偏序 Round-2 结果（不可比饱和测试 v0；x2=downshift_rate）：`docs/v12/artifacts/survival_space_em/poset_round2_incomparability_v0_20260109/poset_round2_report.md`
- Survival Space 偏序 Round-2 §3 结果（信息增益失败测试 v0；dims=(suppression_ratio,downshift_rate)）：`docs/v12/artifacts/survival_space_em/poset_round2_section3_info_gain_v0_20260109/poset_round2_section3_report.md`
  - Verdict: **FAIL → 工程否决 poset 用于 Survival Space v1.x；禁止继续 §1/§2**
- Survival Space 执行检查表（验收门禁）：`docs/v12/V12_SURVIVAL_SPACE_EXPERIMENT_EXECUTION_CHECKLIST_V0_20260108.md`

工具入口（verifiers/tools）：
- Base dimensions verifier（E/I/M）：`python3 tools/v12/verify_base_dimensions_eim_v0.py --run_dir <RUN_DIR>`
- Scanner E schema verifier（market_snapshot canonical schema）：`python3 tools/v12/verify_scanner_e_schema_v0.py --run_dir <RUN_DIR>`
- World structure gate（W0，world-coupling 前置门槛）：`python3 tools/v12/verify_world_structure_gate_v0.py --dataset_dir <DATASET_DIR> --k_windows 1,100,500 --p99_threshold 0.001 --min_samples 1000`
- Genome alignment table verifier（V12.2, machine-readable）：`python3 tools/v12/verify_genome_alignment_table_v0.py --input <genome_alignment_table.json>`
- Tick loop verifier（V12.3, sequence integrity）：`python3 tools/v12/verify_tick_loop_v0.py --run_dir <RUN_DIR> --min_ticks <N>`
- Tick loop repeatability gate（V12.3, FAIL=0）：`python3 tools/v12/verify_tick_loop_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --run_ids <run_id_1,run_id_2,...>`
- errors.jsonl summary（bucket statistics）：`python3 tools/v12/summarize_errors_jsonl_v0.py --errors_jsonl <RUN_DIR>/errors.jsonl`
- Replay dataset builder：`python3 tools/v12/build_replay_dataset_v0.py --source_run_dir <QUANT_RUN_DIR> --output_root <DATASETS_ROOT>`
- Replay dataset verifier：`python3 tools/v12/verify_replay_dataset_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --max_jitter_ms 500`
- Ugly baseline verifier（只做死亡）：`python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`
- Local Reachability verifier（Trial-0/后验证据合同）：`python3 tools/v12/verify_local_reachability_v0.py --run_dir <RUN_DIR>`
- Local Reachability summary（仅描述统计，无阈值/无裁决）：`python3 tools/v12/summarize_local_reachability_report_v0.py --run_dir <RUN_DIR> --output_json <RUN_DIR>/local_reachability_report.json`

## V12 mini-releases (recommended cadence)

目的：把 V12 拆成可控的小版本，每个版本只完成一个“可验收闭环”，避免目标爆炸。

### 主线 mini-releases（light, recommended）

为了避免复杂度指数叠加，当前主线以“建模工具 + tick + life v0”推进，DSM/event-driven 封存后置。

- **V12.0 — Scanner v0 (REST snapshot, candidate schema, tools verification PASS)**
  - 对应：Mainline/Scanner
  - 验收：`market_snapshot.jsonl` 非空 + schema_verification PASS + evidence 可回放（source_call_ids 等）
  - 备注：schema `status` 仍为 `candidate`（不提前宣称 verified）

- **V12.0.1 — Scanner impedance probe v0 (optional write probes, independent)**
  - 对应：Mainline/Impedance（并入 Scanner，但默认关闭）
  - 验收：启用时必须生成 `interaction_impedance.jsonl`（strict JSONL）且每条具备 `account_id_hash + window + metrics + evidence_refs + verdict`；未启用时必须显式 NOT_MEASURABLE（不得伪造 0）。
  - 验收样例锚点（只读，写实记录）：
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `e43ab4c`
    - Quant run_dir: `runs_v12_modeling_tool/run_scanner_v0_20260104T111402Z`
    - Research verifier:
      - `python3 tools/v12/verify_base_dimensions_eim_v0.py --run_dir /Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12_modeling_tool/run_scanner_v0_20260104T111402Z`
      - expected: `PASS (exit 0)`

- **V12.1 — Scanner hardening (repeatability + strict evidence replayability)**
  - 对应：Mainline/Scanner 迭代
  - 验收（机器可验，冻结入口）：
    - 在同一台机器上跑 N 次（建议 N≥20）的 seed sweep，形成可复核统计输出
    - 运行：
      - `python3 tools/v12/sweep_scanner_seeds.py --iterations N`
    - 通过条件（v0.1）：
      - `FAIL` 次数为 0（fail-closed：缺 required files / 非 strict JSONL / schema 破坏都必须显式 FAIL）
      - 对 `NOT_MEASURABLE` 的出现必须可解释（reason_codes 可统计），不得出现“整体 PASS 但关键字段静默缺失”
    - E schema verification gate（新增，冻结入口）：
      - 对 sweep 生成的 `run_ids` 批量执行 E schema verifier，要求 `FAIL=0`
      - 运行（示例）：
        - `python3 tools/v12/verify_scanner_e_schema_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --summary_json <seed_sweep_summary.json> --output <e_schema_gate_report.json>`
  - repeatability 验收样例锚点（只读，写实记录）：
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `e43ab4c`
    - Quant outputs (local artifacts, not in git):
      - `runs_v12_modeling_tool/seed_sweep_summary_20260104T113247Z.json`
      - `runs_v12_modeling_tool/repeatability_reports_20260104T113247Z/aggregate.json`
    - Result: `100/100 PASS` (Research E/I/M verifier PASS, exit 0)
  - E schema gate 100x 验收锚点（只读，写实记录）：
    - Quant branch: `v12-broker-uplink-v0`
    - Quant commit: `4f360e4`
    - Quant outputs (local artifacts, not in git):
      - `runs_v12_modeling_tool/seed_sweep_summary_20260104T124247Z.json`
      - `runs_v12_modeling_tool/e_schema_gate_100x_20260104T124247Z/aggregate.json`
      - `runs_v12_modeling_tool/e_schema_gate_100x_20260104T124247Z/verify_*.json` (100 files)
    - Result: `E schema canonical PASS 100/100` + `FAIL 0/100` (exit 0)
    - Note: 报告展示可带注释；但所有 evidence `.jsonl` 必须 strict JSONL（证据行内禁止 `//` 注释）。

- **V12.2 — Genome refactor v0 (alignment + control_class, no expansion)**
  - 对应：Mainline/Genome refactor
  - 验收（机器可验，冻结入口）：
    - `genome_alignment_table.json` 结构可机读，并通过 verifier：
      - `python3 tools/v12/verify_genome_alignment_table_v0.py --input docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json`（模板自检）
      - 对实际表：`python3 tools/v12/verify_genome_alignment_table_v0.py --input <genome_alignment_table.json>`
    - `control_class` 词表必须使用冻结集合：`system_fact|agent_expressible|agent_proposable|system_controlled`
    - 悬空旋钮扫描（dangling knobs）必须可运行且可解释：
      - 对任意一个 verdict=PASS 的 broker run_dir：
        - `python3 tools/v12/scan_alignment_drift_v0.py --run_dir <BROKER_RUN_DIR> --template docs/v12/V12_GENOME_ALIGNMENT_TABLE_V0_TEMPLATE_20260103.json`
      - 通过条件：`unmapped_attempt_fields` 为空（执行/审计元数据字段必须被过滤）
  - 验收样例锚点（只读，写实记录）：
    - Broker run_id: `run_broker_uplink_v0_20260102T093735Z`
    - Report: `runs_v12/run_broker_uplink_v0_20260102T093735Z/alignment_drift_report.json`
    - Result: `issue_count=0` + `unmapped_attempt_fields=[]` + `important_non_order_knobs_observed=[]` (PASS)

- **V12.3 — Tick loop v0 (polling world, evidence-first)**
  - 对应：Mainline/Tick
  - SSOT：`docs/v12/V12_SSOT_TICK_LOOP_V0_20260104.md`
  - 验收（机器可验，冻结入口）：
    - 运行产生单 run_dir，包含多 tick 的 `market_snapshot.jsonl` 序列（strict JSONL）
    - `market_snapshot.jsonl` 通过 E schema verifier：
      - `python3 tools/v12/verify_scanner_e_schema_v0.py --run_dir <RUN_DIR>`
    - tick 序列完整性通过 tick verifier（FAIL=0）：
      - `python3 tools/v12/verify_tick_loop_v0.py --run_dir <RUN_DIR> --min_ticks <N> --max_backward_ms 0`
    - fail-closed：缺 required files / JSONL 非 strict / ts 回退 / snapshot_id 重复 → FAIL
  - repeatability gate（建议作为 V12.3.1，冻结入口）：
    - 在同一环境跑 N 次 tick loop（N 建议 >=20），收集 run_ids
    - 对 run_ids 批量执行：
      - `python3 tools/v12/verify_tick_loop_repeatability_gate.py --runs_root <QUANT_RUNS_ROOT> --run_ids <...> --min_ticks 120 --max_backward_ms 0 --output <tick_gate_aggregate.json>`
    - 通过条件：`FAIL=0`（NOT_MEASURABLE 允许，但必须可统计原因）
    - 对每个 run 的 `errors.jsonl` 做统计归档（用于后续“交互阻抗/环境反馈”口径收敛）：
      - `python3 tools/v12/summarize_errors_jsonl_v0.py --errors_jsonl <RUN_DIR>/errors.jsonl --output <errors_summary.json>`
  - 验收样例锚点（只读，写实记录）：
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
    - Note: 报告展示可带注释；但所有 evidence `.jsonl` 必须 strict JSONL（证据行内禁止 `//` 注释）。
  - repeatability campaign（N=20, FAIL=0）锚点（只读，写实记录）：
    - Gate report: `runs_v12/tick_loop_gate_aggregate_v3.json` (Quant local artifact)
    - Run IDs file: `/tmp/tick_run_ids_campaign.txt` (local)
    - Errors summaries:
      - `runs_v12/tick_errors_summaries_campaign_20260104T191027Z/aggregate_errors_summary.json`
      - by_error_type (20 runs aggregated): `get_books_unavailable=19`, `get_index_tickers_unavailable=17`, `get_mark_price_unavailable=15`, `get_funding_rate_unavailable=13`, `get_ticker_unavailable=5`

- **V12.3.2 — Replay dataset v0（交易所快照录制 → replay_truth baseline）**
  - 对应：Baseline 基建（离线回放 + seed 稳定性压力测试）
  - SSOT：`docs/v12/V12_SSOT_REPLAY_DATASET_V0_20260106.md`
  - 验收（机器可验）：
    - 从 Quant 已落盘的 canonical `market_snapshot.jsonl` 的 run_dir 构建 dataset
    - dataset verifier 必须 PASS（或因 tick jitter 判 NOT_MEASURABLE；硬 FAIL 仅用于缺证据/非 strict JSONL/ts 回退/重复等）：
      - `python3 tools/v12/verify_replay_dataset_v0.py --dataset_dir <DATASET_DIR> --min_ticks 1000 --max_jitter_ms 500`
    - 硬规则：dataset 属于**本地产物**（不可提交到 git）；git 只纳入 SSOT + verifier
  - 验收锚点（只读，写实记录）：
    - Quant tick run_id：`run_tick_loop_v0_20260106T083725Z`
    - Quant tick run_dir：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_tick_loop_v0_20260106T083725Z`
    - Dataset dir（本地产物）：`/Users/liugang/Cursor_Store/Prometheus-Quant/datasets_v12/dataset_replay_v0_BTC-USDT-SWAP_20260106T083725.364788Z_20260106T105939.297603Z_1000ms`
    - Dataset verifier verdict：`NOT_MEASURABLE`（tick interval unstable: 2225/4999, ratio=0.445；delta_ms_min=941, delta_ms_max=13211）

- **V12.3.3 — Ugly baseline v0（只做死亡，replay_truth；证据闭合）**
  - 对应：Baseline 校准（管线 + 红线执行）
  - SSOT：`docs/v12/V12_SSOT_UGLY_BASELINE_DEATH_ONLY_V0_20260106.md`
  - Verifier：
    - `python3 tools/v12/verify_ugly_baseline_death_only_v0.py --run_dir <RUN_DIR> --steps_target 5000`
  - 验收锚点（只读，写实记录）：
    - Baseline run_dir：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/run_ugly_baseline_v0_20260106T115105Z`
    - Verifier verdict：`PASS`
    - Extinction tick（观测）：`100`（agent_count=100, E0=100, delta=-1）

- **V12.3.4 — Ugly baseline v0_dirty（随机 action_cost；50-seed 扫描）**
  - 对应：快速打破确定性（仍然 **禁止 reward→energy**，红线不变）
  - 状态：实验扩展（不替代 v0_baseline 的验收锚点）
  - 证据（本地产物）：
    - Summary JSON：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_dirty_random_cost_50seeds_CLEAN_summary_20260106T121350Z.json`
    - Acceptance report：`/tmp/V12_UGLY_BASELINE_V0_DIRTY_ACCEPTANCE_20260106.md`
  - 结果（50 seeds, survival_cost_uniform_max=2.0）：
    - extinction_tick mean=55.56, std=1.00, range=[54,59]
  - Quant commits（实现事实）：
    - `5f9134e` feat：增加 v0_dirty_random_cost 扩展（mode/rng_seed/survival_cost_uniform_max）
    - `f555f67` fix：修复 run_id 冲突（纳秒 + seed 后缀）

- **V12.3.5 — Ugly baseline v0.1（decision-cost；确定性负对照）**
  - 对应：证明“读取世界输入”≠“世界影响生死”（必须把世界接入 action_cost/impedance_cost 才会影响能量）
  - 证据（本地产物）：
    - Summary JSON：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_1_decision_cost_50seeds_summary_20260106T123740Z.json`
  - 结果（50 seeds）：
    - extinction_tick：mean=67, std=0.0, range=[67,67]
    - reject/invalid：0%（invalid_ratio_mean=0.0）
  - 冻结解释：只要每 tick 给所有 alive agent 相同成本，灭绝必然确定性。

- **V12.3.5.1 — Ugly baseline v0.1 reject-stress（invalid 重罚 action_cost；20000 steps + dataset wrap）**
  - 对应：强行让“proposal invalid / 类 reject”事件变成**可测**（目标 reject_rate ≥ 20%），用于检验“世界 → proposal → cost → death”链条是否真实连通。
  - 证据（本地产物；用户汇报的 raw 输出）：
    - Runs root：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/`（101 个 run_dirs：100-seed sweep + 1 smoke）
    - Raw summary JSON：`runs_v12/v0_1_reject_stress_100seeds_raw_summary.json`
    - Raw text bundle：`docs/v12/V12_V0_1_REJECT_STRESS_100SEED_RAW_OUTPUT_20260106.txt`
  - 结果（100-seed 列表；用户汇报）：
    - extinction_tick：mean=27.40, std=2.92, range=[22,35]
    - reject_rate：mean=30.20%, std=1.31%
  - 朋友 gate 判据（写实）：
    - `reject_rate > 20%` ⇒ **PASS（链条未断）**
    - `extinction std > 10~20` ⇒ **未满足**（std=2.92）
  - 备注（尺度现实）：在 `E0=100` 且 invalid 罚 `10..30` 的能量尺度下，早灭绝是预期；20000 steps 大部分 tick 会变成“灭绝后记录”。若要观测“存活尾巴/阶段性稳定”，必须对齐时间尺度（例如提高 E0 或降低罚则），但仍保持红线不变（禁止 reward→energy）。

- **V12.3.5.2 — Ugly baseline v0.3 reject-stress（动态阈值 + 更狠罚；30000 steps + dataset wrap）**
  - 对应：进一步加大 reject-stress（动态 invalid 阈值），并把 steps 拉到 30000，尝试观察“尾巴/阶段性稳定”是否出现。
  - 证据（本地产物；用户汇报的 raw 输出）：
    - Quant commit：`8172caa`（branch：`v12-broker-uplink-v0`）
    - Runs root：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/`（用户汇报 154 个 run_dirs）
    - Summary JSON：`runs_v12/v0_3_reject_stress_150seeds_raw_summary_20260106T152605Z.json`
    - Raw bundle：`/tmp/V0_3_REJECT_STRESS_FINAL_RAW_OUTPUT_20260106.txt`
  - 结果（150 值列表；用户汇报）：
    - extinction_tick：mean=13.95, std=1.42, range=[12,18]
    - reject_rate：mean=78.58%, std=6.53%
  - 朋友 gate 判据（写实）：
    - `reject_rate mean >= 30%` ⇒ **PASS**
  - 备注（尺度现实）：平均 ~14 tick 灭绝意味着 30000 steps 仍然主要是在记录“灭绝后 ticks”；若要观测“尾巴/阶段性稳定”，必须先对齐时间尺度（提高 E0 / 降低罚则），同时保持红线不变（禁止 reward→energy）。

- **V12.3.5.3 — Ugly baseline v0.4 tail_reject_stress（尾巴友好尺度；50000 steps；200 seeds）**
  - 对应：重新平衡 reject 过程以拉长存活、让尾部分布可见，同时严格保持红线（NO reward→energy；death 仅由 energy<=0）。
  - 证据（本地产物；用户汇报）：
    - Quant commits：`678e4a0`, `047629c`, `d81ba6d`（branch：`v12-broker-uplink-v0`）
    - Runs root：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/`（200 个 run_dirs：`seed[1..200]`）
    - Summary JSON：`runs_v12/v0_4_tail_reject_stress_200seeds_raw_summary_20260106T154931Z.json`
    - Summarizer：`tools/v12/summarize_v0_4_tail_reject_stress_200seeds_raw.py`（含 admit-rule 输出）
  - 结果（用户汇报）：
    - extinction_tick：mean=183, std=15.04, range=134
    - reject_rate：mean=50.06%（备注：略高于建议的 50% 上限）
  - Admit rule（用户汇报）：未触发（std=15.04 > 10 且 range=134 > 50）
  - 备注（朋友的“希望目标”）：若要求 `std>50` 且 `range>200`，本次仍**未达标**；但相对 v0.3（std 1.42, range 6）已证明尾部分布可被显著拉宽。

- **V12.3.5.4 — Ugly baseline v0.5 dirty_tail（early stop；100000 steps 目标；300 seeds）**
  - 对应：终极脏版压力测试，并加入“灭绝即停”的 **early stop**（现实约束）以避免浪费灭绝后的 ticks，从而让大 seed 扫描可行。
  - 证据（用户汇报）：
    - Quant commits：`d1f9a87`, `1195fa9`（branch：`v12-broker-uplink-v0`）
    - Runs root：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/`（用户汇报 305 个 run_dirs；seeds `1..300`）
    - Summary JSON：`runs_v12/v0_5_dirty_tail_300seeds_raw_summary_*.json`
    - Summarizer：`tools/v12/summarize_v0_5_dirty_tail_300seeds_raw.py`（4 个 gate checks）
  - 结果（用户汇报；启用 early stop）：
    - extinction_tick：mean=168, std=11.99, range=67（142..209）
    - reject_rate：mean=59.97%, std=0.45%
    - Alive@5000：0%（全部在 5000 前灭绝）
  - Gate checks（用户汇报）：0/4 通过（FAIL）
  - 事实备注：early stop 将有效 ticks 降到约 300×168 ≈ 50,400（相对 300×100,000 节省约 99.5%）。

- **V12.3.6 — Ugly baseline v0.2（impedance-cost；世界可测性影响能量）**
  - 对应：将世界可测性（snapshot quality）映射为 `impedance_cost` 进入能量（仍然禁止 reward→energy）。
  - 证据（本地产物）：
    - Summary JSON：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_impedance_cost_50seeds_summary_20260106T124935Z.json`
  - 结果（50 seeds）：
    - extinction_tick：mean=53.04, std=0.445, range=[52,54]
    - impedance_triggered_ratio：mean=0.0586, std=0.0
  - 事实备注：impedance_triggered_ratio 对 seed 不变（同一 replay dataset 的 quality 序列）；extinction 的差异来自条件成本抽样。

- **V12.3.7 — Ugly baseline v0.2_extreme（gauss 初始能量压力测试；5000 steps）**
  - 对应：在 death-only 红线不变（禁止 reward→energy）的前提下，专门测试 **初始能量分布（gauss init）** 对灭绝分布的影响。
  - 证据（本地产物）：
    - Summary JSON：`/Users/liugang/Cursor_Store/Prometheus-Quant/runs_v12/v0_2_extreme_summary_20260106T133241Z.json`
  - 结果（写实，来自 summary JSON）：
    - run_dirs=101（unique_seeds=100；`rng_seed=1` 重复跑了 2 次）
    - extinction_tick：mean=88.7921, std=5.7381, range=[77,100]
    - impedance_triggered_ratio：mean=0.0, std=0.0
  - 备注（fail-closed 口径）：由于 impedance_triggered_ratio=0.0，**这组 runs 并未触发“NOT_MEASURABLE snapshot → impedance_cost”分支**；因此只能将其视为“gauss-init 灭绝分布”的证据，而不是“高阻抗”证据。

- **V12.4 — Life v0（只做死亡，暂不做繁殖）**
  - 对应：Mainline/Life
  - 验收：死亡相关的“事件接口 + 证据落盘 + fail-closed”存在；繁殖明确后置。

---

### 封存/后置（capability sealed or deferred）

以下能力保留为“已验证/可选扩展”，但不作为当前主线依赖：

- DSM/WS ingestion（封存能力 + 长期稳定并入门槛）：`docs/v12/V12_SSOT_DOWNLINK_SUBSCRIPTION_MANAGER_20260101.md`
- 双管道 join（DSM↔Decision↔Broker）：后置到 DSM 长期稳定通过之后
- Settlement/账户级自动事件：保留为 life-system 的真值来源能力面，但不作为当前“建模工具 + tick + life v0”必备依赖

### M0 — World Feature Scanner v0（E: market info, single instId）

- **Scope (frozen)**:
  - Only `BTC-USDT-SWAP`
  - Read-only market info first (E/exogenous)
- **SSOT**:
  - World Feature Scanner: `docs/v11/V11_SSOT_WORLD_FEATURE_SCANNER_20260101.md`
  - Scanner v0 E schema (V12): `docs/v12/V12_SSOT_SCANNER_E_MARKET_SCHEMA_20260101.md`
  - OKX contract + order parameter space: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）
- **Acceptance**:
  - Scanner produces a run_dir with `run_manifest.json`, `okx_api_calls.jsonl`, `errors.jsonl`, `scanner_report.json`
  - Must produce non-empty `market_snapshot.jsonl`
  - Any endpoint failure must be NOT_MEASURABLE (with reason_code), never silent
  - Tools verification must pass for canonical schema (candidate→verified) before modeling can consume it

### M0.5 — WS ingestion only (event stream evidence, tick-consumable)

目的：解决“不用 WS 会限制后续事件驱动/新陈代谢/繁殖；直接上 WS 又是大工程”的两难：  
先把 WS 变成**可审计事件流输入**，但决策/演化系统先不强制改为 event-driven（仍可按 tick/采样消费）。

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

### M0.5 实施状态快照（只增不改，事实记录）

已实现（VPS REAL WS 验收通过）：
- 下行 evidence：`okx_ws_sessions.jsonl` / `okx_ws_requests.jsonl` / `okx_ws_messages.jsonl`
- canonical：`market_snapshot.jsonl`（含 `source_message_ids` 回放锚点）
- verifier：`tools/v12/verify_dsm_ws_ingestion_v0.py` 输出 PASS 时，manifest 必须同步 `verdict="PASS"`；若存在 `not_measurable:*` reason_codes，则 verdict 必须为 NOT_MEASURABLE（fail-closed）

当前冻结的最小通道集（v0.9.1 参考实现）：
- `tickers`（instId=`BTC-USDT-SWAP`）→ `last_px`
- `mark-price`（instId=`BTC-USDT-SWAP`）→ `mark_px`
- `books5`（instId=`BTC-USDT-SWAP`）→ `bid_px_1/ask_px_1/bid_sz_1/ask_sz_1`
- `index-tickers`（instId=`BTC-USDT`）→ `index_px`（注意 underlying 映射）
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


