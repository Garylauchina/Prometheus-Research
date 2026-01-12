# V13 Research Index（中文）

定位（冻结）：
- **V13 不是修复 V12 的失败，而是接受它们作为世界事实**：沉默/拒绝/不可测与结构显影同级。

---

## Start Here / 从这里开始

- **V13 One-Page SSOT（启动摘要）**：
  - `docs/v13/V13_SSOT_STARTUP_ONE_PAGE_V0_20260110.md`
- **V13 开发计划（初稿）**：
  - `docs/v13/V13_DEV_PLAN_V0_20260110.md`
- **V13 Phenomena Log Protocol（草案）**：
  - `docs/v13/V13_PHENOMENA_LOG_PROTOCOL_V0_20260110.md`
- **V13 Capture Window 最小合同（冻结）**：
  - `docs/v13/V13_SSOT_CAPTURE_WINDOW_MIN_CONTRACT_V0_20260110.md`
- **V13 World Contract v0.2（冻结）**：
  - `docs/v13/V13_SSOT_WORLD_CONTRACT_V0_2_20260110.md`
  - spec: `docs/v13/spec/world_contract_v0_2_spec.json`
  - verifier: `python3 tools/v13/verify_world_contract_v0_2.py --run_dir <RUN_DIR>`
- **V13 World Contract v0.2（Quant 交付封存）**：
  - `docs/v13/artifacts/v13_world_contract_v0_2_delivery_20260110/README.md`
- **V13 Phase 1（Live Window Contract Layer 验证封存）**：
  - `docs/v13/artifacts/v13_phase1_live_window_verifier_v0_20260110/README.md`
- **V13 Phase 1（首个 24h window 完成封存；verdict=MEASURABLE）**：
  - `docs/v13/artifacts/v13_phase1_24h_window_v0_20260112/README.md`
- **V13 Phase 2（现象命名注册表，append-only）**：
  - `docs/v13/phenomena/V13_PHENOMENA_NAMING_REGISTRY_V0_20260112.jsonl`

- **V13 Spec（冻结增量：window↔contract 映射 / evidence bridge / stop conditions / reason examples）**：
  - `docs/v13/spec/V13_WINDOW_VERDICT_CONTRACT_VERDICT_MAPPING_V0_20260112.md`
  - `docs/v13/spec/V13_EVIDENCE_CHAIN_BRIDGE_MIN_SPEC_V0_20260112.md`
  - `docs/v13/ops/V13_PHASE1_STOP_CONDITIONS_CHECKLIST_V0_20260112.md`
  - `docs/v13/spec/examples/world_contract_v0_2_reason_consistency/README.md`

- **V13 Ops（Phase 1 完成报告模板 + review gate）**：
  - `docs/v13/templates/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_V0_20260112.md`
  - `docs/v13/deliveries/V13_PHASE1_COMPLETION_REPORT_TEMPLATE_AND_REVIEW_GATE_EXEC_20260112.md`
- **V13 VPS 工作流程（冻结）**：
  - `docs/ops/V13_VPS_WORKFLOW_V0_20260112.md`（指令发布：cat输出；交付物读取：SSH）
  - `tools/v13/fetch_vps_delivery.sh`（辅助脚本：从VPS拉取交付物）
- **V13 Quant 交付封存（Kickoff/VPS）**：
  - `docs/v13/artifacts/v13_kickoff_quant_delivery_v0_20260110/README.md`
- **V13 Trial-12 Phase 1（VPS 部署成功封存）**：
  - `docs/v13/artifacts/v13_trial12_vps_deployment_v0_20260110/README.md`

---

## 备注（冻结）

- V13 不承诺 replay 裁决资格；缺失关键世界证据时，必须输出 NOT_MEASURABLE（不补、不猜、不用 proxy）。

