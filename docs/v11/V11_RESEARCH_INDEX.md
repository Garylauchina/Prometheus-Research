# V11 Research Index / V11 研究入口（中文为主）

## Start Here

这是 V11 文档的统一入口（SSOT index）。  
从现在开始，V11 新增文档只写入 `docs/v11/`。

---

## Execution World (SSOT Anchors)

> 说明：当前 V11 的大量 SSOT 文档仍位于 `docs/v10/`（历史原因）。  
> 迁移将采用“渐进搬迁 + 原路径 stub 指针文件”的方式，避免旧链接断裂。

临时入口（旧路径，稍后迁移）：
- Baseline Changelog: `docs/v11/V11_BASELINE_CHANGELOG_20251226.md`
- Execution World Design: `docs/v11/V11_DESIGN_EXECUTION_WORLD_20251227.md`
- Closure Allowlist: `docs/v11/V11_EXECUTION_WORLD_CLOSURE_ALLOWLIST_20251227.md`
- Programmer AI Operating Rules: `docs/v11/V11_PROGRAMMER_AI_OPERATING_RULES_20251227.md`

---

## Step Docs (migrated from docs/v10/)

## Step Map (Step 27–96, machine-readable quick view)

说明（避免“Step 不全”的误解）：
- 本仓库当前**没有**独立的 Step 0–26 文档；V11 的 “Step26 Evidence Verifier Gate” 通过 Step27–29 的 SSOT/CI Gate 文档间接覆盖。
- 因此，本 index 的“全量 steps”按现状定义为：**Step 27–96**（后续若补齐 Step0–26，会在此处追加入口，不改既有编号）。

术语冻结（避免啰嗦且避免混淆）：
- **First Flight**（首飞准备，truth-backed）：从 first_flight 开始的所有模块测试必须 **真实对接交易所**（OKX demo，后续可扩展 live），并在 `run_dir` 内落盘交易所真值（至少 `orders_history.jsonl`；若 filled 则 `fills.jsonl`/`bills.jsonl` 必须存在且可 join）。没有交易所真值落盘 → **一概不采信**（哪怕本地证据链自洽）。
- **Real Flight**（真首飞/真实飞行）：在 First Flight 各模块 truth-backed 测试通过后，执行一次“干净的真实运行入口”，做最小闭环样本与后续稳定窗口运行。
- 明确排除：任何 `run_manifest.broker_trader_test.client_order_ids` 中的启动自检单，不计入 First/Real Flight（避免“自检单冒充 agent 行为”）。

First Flight 核心事实（冻结补充）：
- 杠杆（leverage）必须做 **truth binding**：Agent 基因存在“杠杆偏好”不等于交易所实际使用了该杠杆；First Flight 阶段必须把 leverage 写入决策输出与交易链入册，并能用交易所真值核验。见：`docs/v11/V11_NOTE_LEVERAGE_PREFERENCE_TRUTH_BINDING_20251231.md`。
- 执行反馈（fill_ratio）进入 **M（friction feedback）**：v0 窗口固定为上一 tick（t-1），无事件/不可测 → mask=0；同时区分 **个体** 与 **群体** 两条通道，并提供两条正交基因权重用于单项消融（只开 self / 只开 group / 都开 / 都关）。来源：
  - baseline：`docs/v11/V11_BASELINE_CHANGELOG_20251226.md`
  - E/I/M/C 口径与封存 C 意图默认不入决策：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`
  - 交易员错误篓子与 Agent-facing 投影（fill_ratio + 权重基因）：`docs/v11/V11_STEP96_EXCHANGE_ERROR_BASKET_20251231.md`
  - 执行质量（fill_ratio 属于 Step95 的可审计标量）：`docs/v11/V11_STEP95_EXECUTION_QUALITY_AND_SLIPPAGE_EVIDENCE_20251231.md`

快速定位（按主题）：
- **证据链 / 审计链**：Step27–46、Step85–89
- **I/C 探针与消融**：Step47–54
- **验收与 CI**：Step55–56、Step62/64/66/69/71/73/75/77
- **Research bundle / Cross-run index**：Step65–71
- **冻结机制**：Step74–84
- **交易链扩展**：Step91–92
- **稳定窗口运营**：Step93
- **未来扩展 SSOT（尚未实现）**：Step94–96

## Work Plan (ordered) — optimize cadence

唯一关注点（frozen）：
- **First Flight / Real Flight**：只认“交易所真值落盘可核验”的闭环（决策→下单→真值入册→审计/错误），且明确排除 `broker_trader_test` 启动自检单。

节奏原则（frozen）：
- **Truth-first**：从 first_flight 起所有测试必须对接交易所 demo 并落盘真值；fixtures 只能作为补充（不得作为采信依据）。
- **入口拆分**：first_flight 使用专门 run 入口；real_flight 使用另一个干净入口；停止使用 `run_v11_service.py` 作为 flight 入口（标记 deprecated，不作为验收命令）。

四阶段推进顺序（frozen，避免节奏分散）：
- **Stage 1 — Mac First Flight**：在 Mac 本地先把 First Flight 的各模块 truth-backed 测试跑通（每个 case 都必须有交易所真值落盘）。
- **Stage 2 — VPS First Flight**：在 VPS 复现同一套 First Flight（同一 Quant main HEAD，anchors 对齐），确认容器/权限/时钟/限流等真实环境仍可闭环。
- **Stage 3 — Mac Real Flight**：回到 Mac 实现/验证 `real_flight` 干净入口（不编排 tools，只负责真实运行与落盘）。
- **Stage 4 — VPS Real Flight**：部署 `real_flight` 到 VPS 作为正式运行入口，并纳入 Step93 稳定窗口周检/日检纪律。

里程碑（按顺序；任一未完成则不进入下一步）：
- **M0 — Decision Sanity Gate (Quant + evidence-level)**：先证明“决策链本身可信”，否则 First/Real Flight 没意义。
  - 触及链路：**输入合同（feature/probe）→ Ledger/I 真值 → DecisionEngine → decision_trace → intent 统计**
  - 依据 SSOT：
    - Step27（Step26 最小审计清单）：`docs/v11/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
    - Step47（I 真值三元组/禁止伪 0）：`docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`
    - Step52（维度/布局对齐 fail-closed）：`docs/v11/V11_STEP52_FEATURE_DIM_DECISION_ENGINE_GENOME_ALIGNMENT_20251230.md`
    - Design（execution_world hard rules）：`docs/v11/V11_DESIGN_EXECUTION_WORLD_20251227.md`
  - 子步骤（必须全部满足）：
    - **Contract frozen**：run_manifest 内记录 `feature_contract_version + feature_dimension + decision_input_dim + genome_schema_version + alignment_check.passed=true`（Step52）。
    - **Mask discipline**：decision_trace 必须能证明 MFStats/Comfort 等不可测时 `mask=0 + reason_code`，且 DecisionEngine 尊重 mask（Step27/Design）。
    - **I truth**：禁止把 unknown 写成 0；I 维度必须来自 Ledger truth，使用 `position_exposure_ratio + pos_side_sign + positions_truth_quality`（Step47）。
    - **Decision observability**：decision_trace 必须能统计 intent 分布（open/close/hold）与关键输入摘要（effective_features_count 等），避免“看不见决策，只看见交易”（Step27/Design）。
    - **Leverage present (truth-binding)**：对任何会触达写路径的 intent，decision_trace 必须包含 `leverage_target`，且 order_attempts/api_calls 必须包含 `leverage_target`（不得沉默）。
  - 最小验收命令（truth-backed run_dir 证据读法）：
    - 给定 `RUN_DIR`：检查 `run_manifest.json` 的 alignment_check 是否 passed，且 feature_dim==decision_input_dim。
    - 给定 `RUN_DIR`：从 `decision_trace.jsonl` 统计各类 intent 的数量（open/close/hold），并输出 masked/unknown 的比例摘要。
    - 给定 `RUN_DIR`：必须能在 `orders_history.jsonl` 找到至少一条与本 run 的 `clOrdId_namespace_prefix` 一致的订单终态记录（证明该 run 真实对接交易所）。
  - FAIL 条件（立刻停止后续里程碑）：
    - 维度不对齐 / alignment_check 缺失 / 伪 0（unknown 写 0）/ decision_trace 无法统计 intent（等价于“无法审计决策”）。
    - 缺少交易所真值落盘（至少 orders_history）：一概不采信。
- **M1 — Implement Step94 (Quant)**：新增 one‑shot 能力 + Step94 verifier（fail‑closed），用于证明 First/Real Flight。
  - 触及链路：**决策（core）→ 交易（ops/connector）→ 入册（evidence jsonl + manifest）→ 审计（auditor + Step88）**
  - 子步骤（必须全部完成）：
    - Runner/CLI：新增 `--force-one-shot-trade/--one-shot-*`（默认关闭），并确保 one‑shot **不走** `broker_trader_test` 路径。
    - Decision evidence：`decision_trace.jsonl` 必须写入 one‑shot 决策记录（可 join：run_id+tick+agent_id_hash+oneshot marker）。
    - Trade intent：通过 BrokerTrader 写入 one‑shot intent（显式标记为 non‑preflight：`flags.oneshot=true` 或 `lifecycle_scope="agent_live"`）。
    - Manifest：写入 `run_manifest.oneshot_closure_proof`（enabled/tick/action/agent_id_hash/client_order_id/ordId/step88_verdict）。
    - Verifier：新增 `verify_step94_oneshot_closure_proof.py`（read-only，fail‑closed，显式排除 broker_trader_test）。
  - 风险点（必须提前写死判据）：
    - **自检单污染**：任何 broker_trader_test 的 client_order_id 不得被当作 one‑shot；否则 FAIL。
    - **join-key 缺失**：one‑shot 必须能用 client_order_id ↔ clOrdId ↔ ordId join（否则 FAIL）。
  - 最小验收命令（必须可复制复跑）：
    - `PYTHONPATH="$PWD" python3 -m prometheus.v11.ops.run_v11_service -h | grep -nE "force-one-shot|one-shot|enable-preflight-test-order"`
    - `python3 tools/verify_step94_oneshot_closure_proof.py "$RUN_DIR"`
- **M2 — Harden Step91 write-chain joins (Quant)**：`order_attempts.jsonl` 必须落 `clOrdId/ordId`（additive-only）并能 join 到 `orders_history/fills/bills`；补齐必要 refs（connector/api call refs）。
  - 触及链路：**交易写路径（ops/connector）→ 入册（order_attempts）→ 审计 join（Step88/Step95）**
  - 子步骤：
    - `order_attempts.jsonl`（additive-only）：在一次 attempt 生命周期内补齐 `clOrdId`（client_order_id）与 `ordId`（exchange order id）。
    - 新增/补齐 connector call refs：能回指到 `okx_api_calls.jsonl`（或 Step91 的 `exchange_api_calls.jsonl`）。
    - 明确“exchange_rejected vs local_reject”分类边界（避免伪装真值）。
  - 风险点：
    - **时间窗/异步**：ordId 可能在 ack/查询后才能获得，必须定义“何时补写/如何补写”而不破坏 append-only（常见做法：同一 client_order_id 再写一条补充记录或在后续 attempt 记录中落 refs；不得改旧行）。
  - 最小验收命令：
    - 给定 `client_order_id`，能在 `orders_history.jsonl` 找到同 clOrdId，并拿到 ordId；若 filled 则 fills/bills 能按 ordId join。
- **M3 — Land Step96 trader error bucket (Quant)**：落盘 `exchange_error_events.jsonl` + `exchange_error_basket.json` + verifier；把 exchange/local/not_measurable（含 paging_incomplete）统一入篓。
  - 触及链路：**错误处理（trader视角）→ 入册（events jsonl）→ 汇总（basket json）→ verifier gate**
  - 子步骤：
    - 写入点：connector 写侧失败 / auditor 查询失败 / verifier NOT_MEASURABLE 都必须能写入 events（scope=agent/system）。
    - bucket_key：稳定可聚合（不包含 message），并能回指 evidence_refs/file/line。
    - verifier：schema 校验 + 聚合一致性校验（events → basket）。
  - 最小验收命令：
    - `python3 tools/verify_step96_exchange_error_basket.py "$RUN_DIR"`
- **M4 — Step95 v1 minimal execution quality (Quant)**：paging closure + 多 fills/bills 覆盖完整性；不可测量必须 NOT_MEASURABLE 且写入 Step96。
  - 触及链路：**审计/真值覆盖（auditor/materialization）→ 质量计算（Step95）→ 错误篓子（Step96）**
  - 子步骤：
    - paging_traces 闭合：对 orders/fills/bills 的分页链必须闭合；否则 NOT_MEASURABLE(reason_code=paging_incomplete) 并写入 Step96（TRUTH_PAGING_INCOMPLETE）。
    - auto-split 覆盖：同一 ordId 的多 fills/bills 视为正常；但必须证明“覆盖完整性”（否则 NOT_MEASURABLE）。
    - verifier：对 paging 不闭合必须输出 NOT_MEASURABLE（禁止 PASS）。
  - 最小验收命令：
    - `python3 tools/verify_step95_execution_quality.py "$RUN_DIR"`
- **M5 — Mac fixtures (Quant)**：最小场景集先跑绿（建议：S1 filled / S2 partial_fills / S4 exchange_rejected / S6 paging_incomplete）。
  - 验收判据：fixtures 全绿（CI/本地均可），无需访问真实交易所。
- **M6 — VPS single proof run**：仅在 M1–M4 通过后，在 VPS 跑一次 one‑shot 作为 First/Real Flight 证明；产出 run_id/run_dir 与 verifier 输出，写入 Quant 记录与本 index。
  - 验收判据：Step88 PASS + Step94 PASS（且 one‑shot 不在 broker_trader_test 列表）。

### Evidence Gate / Audit Chain (Step 27–46)

- Step 27: `docs/v11/V11_STEP27_STEP26_EVIDENCE_MIN_REVIEW_CHECKLIST_20251229.md`
- Step 28: `docs/v11/V11_STEP28_EVIDENCE_PACKAGING_GATE_20251229.md`
- Step 29: `docs/v11/V11_STEP29_CI_EVIDENCE_GATE_STEP26_20251229.md`
- Step 30: `docs/v11/V11_STEP30_RUN_END_EVIDENCE_GATE_IMPLEMENTED_20251229.md`
- Step 31: `docs/v11/V11_STEP31_EXTEND_EVIDENCE_VERIFIER_TIER1_20251229.md`
- Step 31 (Quant record): `docs/v11/V11_STEP31_TIER1_VERIFIER_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 32: `docs/v11/V11_STEP32_ORPHAN_DETECTION_MIN_MEASURABLE_20251229.md`
- Step 32 (Quant record): `docs/v11/V11_STEP32_ORPHAN_DETECTION_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 33: `docs/v11/V11_STEP33_FILLS_BILLS_JOIN_MIN_MEASURABLE_20251229.md`
- Step 33 (Quant record): `docs/v11/V11_STEP33_FILLS_BILLS_JOIN_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 34: `docs/v11/V11_STEP34_PAGING_TRACES_APPEND_ONLY_20251229.md`
- Step 34 (Quant record): `docs/v11/V11_STEP34_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 35: `docs/v11/V11_STEP35_REQUIRE_PAGING_TRACES_IN_GATES_20251229.md`
- Step 35 (Quant record): `docs/v11/V11_STEP35_REQUIRE_PAGING_TRACES_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 36: `docs/v11/V11_STEP36_AUDITOR_PAGING_COVERAGE_FIELDS_20251229.md`
- Step 36 (Quant record): `docs/v11/V11_STEP36_AUDITOR_PAGING_COVERAGE_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 37: `docs/v11/V11_STEP37_PAGING_QUERY_CHAIN_ID_20251229.md`
- Step 37 (Quant record): `docs/v11/V11_STEP37_PAGING_QUERY_CHAIN_ID_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 38: `docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IN_MANIFEST_20251229.md`
- Step 38 (Quant record): `docs/v11/V11_STEP38_AUDIT_SCOPE_ANCHORS_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 39: `docs/v11/V11_STEP39_AUDIT_SCOPE_ID_AS_GLOBAL_ANCHOR_20251229.md`
- Step 39 (Quant record): `docs/v11/V11_STEP39_AUDIT_SCOPE_ID_GLOBAL_ANCHOR_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 40: `docs/v11/V11_STEP40_MANIFEST_AUDIT_SCOPES_APPEND_ONLY_20251229.md`
- Step 40 (Quant record): `docs/v11/V11_STEP40_MANIFEST_AUDIT_SCOPES_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 41: `docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_20251229.md`
- Step 41 (Quant record): `docs/v11/V11_STEP41_EVIDENCE_REFS_STANDARD_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 42: `docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_20251229.md`
- Step 42 (Quant record): `docs/v11/V11_STEP42_EVIDENCE_REFS_HARDENING_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 43: `docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_20251229.md`
- Step 43 (Quant record): `docs/v11/V11_STEP43_EVIDENCE_REF_INDEX_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 44: `docs/v11/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_20251229.md`
- Step 44 (Quant record): `docs/v11/V11_STEP44_EVIDENCE_REFS_DEREFERENCE_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 45: `docs/v11/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_20251229.md`
- Step 45 (Quant record): `docs/v11/V11_STEP45_EVIDENCE_REFS_SEMANTIC_JOIN_VALIDATION_IMPLEMENTED_IN_QUANT_20251229.md`
- Step 46: `docs/v11/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_20251229.md`
- Step 46 (Quant record): `docs/v11/V11_STEP46_EVIDENCE_GATE_BUNDLE_FREEZE_IMPLEMENTED_IN_QUANT_20251229.md`

### I/C Probes + Ablation (Step 47–53)

- Step 47: `docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_20251230.md`
- Step 47 (Quant record): `docs/v11/V11_STEP47_GENE_FEATURE_LEDGER_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 48: `docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_20251230.md`
- Step 48 (Quant record): `docs/v11/V11_STEP48_I_C_PROBES_INJECTION_SSOT_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 49: `docs/v11/V11_STEP49_C_ABLATION_SWITCH_20251230.md`
- Step 49 (Quant record): `docs/v11/V11_STEP49_C_ABLATION_SWITCH_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 50: `docs/v11/V11_STEP50_MIN_ABLATION_EXPERIMENT_TEMPLATE_20251230.md`
- Step 50 (Quant record): `docs/v11/V11_STEP50_MIN_ABLATION_EXPERIMENT_TEMPLATE_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 51: `docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_20251230.md`
- Step 51 (Quant record): `docs/v11/V11_STEP51_MIN_ABLATION_RUN_AND_SUMMARY_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 52: `docs/v11/V11_STEP52_FEATURE_DIM_DECISION_ENGINE_GENOME_ALIGNMENT_20251230.md`
- Step 52 (Quant record): `docs/v11/V11_STEP52_FEATURE_DIM_DECISION_ENGINE_GENOME_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 53: `docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_20251230.md`
- Step 53 (Quant record): `docs/v11/V11_STEP53_ABLATION_COMPARE_REPORT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Gate Integration (Step 54)

- Step 54 (SSOT): `docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_20251230.md`
- Step 54 (Quant record): `docs/v11/V11_STEP54_STEP53_GATE_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Acceptance Protocol (Step 55)

- Step 55 (SSOT): `docs/v11/V11_STEP55_STEP54_ACCEPTANCE_PROTOCOL_20251230.md`

---

### CI Gate (Step 56)

- Step 56 (SSOT): `docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_20251230.md`
- Step 56 (Quant record): `docs/v11/V11_STEP56_CI_GATE_STEP55_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Fixtures Contract (Step 57)

- Step 57 (SSOT): `docs/v11/V11_STEP57_STEP51_MIN_FIXTURES_CONTRACT_20251230.md`

---

### Fixtures Verifier (Step 58)

- Step 58 (SSOT): `docs/v11/V11_STEP58_FIXTURES_CONTRACT_VERIFIER_20251230.md`
- Step 58 (Quant record): `docs/v11/V11_STEP58_FIXTURES_CONTRACT_VERIFIER_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Compare Bundle (Step 59)

- Step 59 (SSOT): `docs/v11/V11_STEP59_COMPARE_BUNDLE_CONTRACT_20251230.md`
- Step 59 (Quant record): `docs/v11/V11_STEP59_COMPARE_BUNDLE_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Compare Bundle Gate Integration (Step 60)

- Step 60 (SSOT): `docs/v11/V11_STEP60_GATE_COMPARE_BUNDLE_INTEGRATION_20251230.md`
- Step 60 (Quant record): `docs/v11/V11_STEP60_GATE_COMPARE_BUNDLE_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Compare Bundle Index (Step 61)

- Step 61 (SSOT): `docs/v11/V11_STEP61_COMPARE_BUNDLE_INDEX_CONTRACT_20251230.md`
- Step 61 (Quant record): `docs/v11/V11_STEP61_COMPARE_BUNDLE_INDEX_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Index (Step 62)

- Step 62 (SSOT): `docs/v11/V11_STEP62_CI_GATE_STEP61_INDEX_20251230.md`
- Step 62 (Quant record): `docs/v11/V11_STEP62_CI_GATE_STEP61_INDEX_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Run-End Gate Optional for Index (Step 63)

- Step 63 (SSOT): `docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_20251230.md`
- Step 63 (Quant record): `docs/v11/V11_STEP63_RUN_END_GATE_COMPARE_BUNDLE_INDEX_OPTIONAL_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step63 Acceptance (Step 64)

- Step 64 (SSOT): `docs/v11/V11_STEP64_CI_GATE_STEP63_ACCEPTANCE_20251230.md`
- Step 64 (Quant record): `docs/v11/V11_STEP64_CI_GATE_STEP63_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Research Bundle Output (Step 65)

- Step 65 (SSOT): `docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_20251230.md`
- Step 65 (Quant record): `docs/v11/V11_STEP65_RESEARCH_BUNDLE_OUTPUT_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step65 Acceptance (Step 66)

- Step 66 (SSOT): `docs/v11/V11_STEP66_CI_GATE_STEP65_ACCEPTANCE_20251230.md`
- Step 66 (Quant record): `docs/v11/V11_STEP66_CI_GATE_STEP65_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Research Bundle Entrypoint (Step 67)

- Step 67 (SSOT): `docs/v11/V11_STEP67_RESEARCH_BUNDLE_ENTRYPOINT_CONTRACT_20251230.md`

---

### Run-End Gate for Entrypoint (Step 68)

- Step 68 (SSOT): `docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_20251230.md`
- Step 68 (Quant record): `docs/v11/V11_STEP68_RUN_END_GATE_STEP67_ENTRYPOINT_INTEGRATION_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step68 Acceptance (Step 69)

- Step 69 (SSOT): `docs/v11/V11_STEP69_CI_GATE_STEP68_ACCEPTANCE_20251230.md`
- Step 69 (Quant record): `docs/v11/V11_STEP69_CI_GATE_STEP68_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Cross-Run Research Entry Index (Step 70)

- Step 70 (SSOT): `docs/v11/V11_STEP70_CROSS_RUN_RESEARCH_ENTRY_INDEX_CONTRACT_20251230.md`

---

### CI Gate for Step70 Cross-Run Index (Step 71)

- Step 71 (SSOT): `docs/v11/V11_STEP71_CI_GATE_STEP70_CROSS_RUN_INDEX_20251230.md`
- Step 71 (Quant record): `docs/v11/V11_STEP71_CI_GATE_STEP70_CROSS_RUN_INDEX_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Agent Metabolism Observability (Step 72)

- Step 72 (SSOT): `docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_20251230.md`
- Step 72.1 (SSOT): `docs/v11/V11_STEP72_1_AGENT_METABOLISM_CANDIDATES_AND_FILTER_20251230.md`
- Step 72.2 (SSOT): `docs/v11/V11_STEP72_2_AGENT_METABOLISM_PREIMPLEMENTATION_CHECKLIST_AND_LIFESPAN_VIEWS_20251230.md`
- Step 72 (Quant record): `docs/v11/V11_STEP72_AGENT_METABOLISM_OBSERVABILITY_CONTRACT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step72 Acceptance (Step 73)

- Step 73 (SSOT): `docs/v11/V11_STEP73_CI_GATE_STEP72_METABOLISM_ACCEPTANCE_20251230.md`
- Step 73 (Quant record): `docs/v11/V11_STEP73_CI_GATE_STEP72_METABOLISM_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Real-time Reconciliation Freeze (Step 74)

- Step 74 (SSOT): `docs/v11/V11_STEP74_REAL_TIME_RECONCILIATION_FREEZE_20251230.md`
- Step 74 (Quant record): `docs/v11/V11_STEP74_REAL_TIME_RECONCILIATION_FREEZE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step74 Acceptance (Step 75)

- Step 75 (SSOT): `docs/v11/V11_STEP75_CI_GATE_STEP74_EXECUTION_FREEZE_ACCEPTANCE_20251230.md`
- Step 75 (Quant record): `docs/v11/V11_STEP75_CI_GATE_STEP74_EXECUTION_FREEZE_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze E2E Wiring (Step 76)

- Step 76 (SSOT): `docs/v11/V11_STEP76_FREEZE_E2E_WIRING_AND_DEMO_20251230.md`
- Step 76 (Quant record): `docs/v11/V11_STEP76_FREEZE_E2E_WIRING_AND_DEMO_IMPLEMENTED_IN_QUANT_20251230.md`

---

### CI Gate for Step76 Freeze E2E (Step 77)

- Step 77 (SSOT): `docs/v11/V11_STEP77_CI_GATE_STEP76_FREEZE_E2E_ACCEPTANCE_20251230.md`
- Step 77 (Quant record): `docs/v11/V11_STEP77_CI_GATE_STEP76_FREEZE_E2E_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze Gate Non-Bypass Guard (Step 78)

- Step 78 (SSOT): `docs/v11/V11_STEP78_FREEZE_GATE_NON_BYPASS_GUARD_20251230.md`
- Step 78 (Quant record): `docs/v11/V11_STEP78_FREEZE_GATE_NON_BYPASS_GUARD_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze Precheck Dominance Guard (Step 79)

- Step 79 (SSOT): `docs/v11/V11_STEP79_FREEZE_PRECHECK_DOMINANCE_GUARD_20251230.md`
- Step 79 (Quant record): `docs/v11/V11_STEP79_FREEZE_PRECHECK_DOMINANCE_GUARD_IMPLEMENTED_IN_QUANT_20251230.md`
- Step 79 (Quant record, integrated): `docs/v11/V11_STEP79_FREEZE_PRECHECK_DOMINANCE_GUARD_INTEGRATED_IN_QUANT_20251230.md`

---

### Freeze Evidence Semantics Freeze (Step 80)

- Step 80 (SSOT): `docs/v11/V11_STEP80_FREEZE_EVIDENCE_SEMANTICS_FREEZE_20251230.md`
- Step 80 (Quant record): `docs/v11/V11_STEP80_FREEZE_EVIDENCE_SEMANTICS_FREEZE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze Evidence ↔ EvidenceRefs Alignment (Step 81)

- Step 81 (SSOT): `docs/v11/V11_STEP81_FREEZE_EVIDENCE_EVIDENCE_REFS_ALIGNMENT_20251230.md`
- Step 81 (Quant record): `docs/v11/V11_STEP81_FREEZE_EVIDENCE_EVIDENCE_REFS_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze EvidenceRefs Hardening (Step 82)

- Step 82 (SSOT): `docs/v11/V11_STEP82_FREEZE_EVIDENCE_REFS_HARDENING_20251230.md`
- Step 82 (Quant record): `docs/v11/V11_STEP82_FREEZE_EVIDENCE_REFS_HARDENING_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Freeze EvidenceRefs SHA256 Alignment (Step 83)

- Step 83 (SSOT): `docs/v11/V11_STEP83_FREEZE_EVIDENCE_REFS_SHA256_ALIGNMENT_20251230.md`
- Step 83 (Quant record): `docs/v11/V11_STEP83_FREEZE_EVIDENCE_REFS_SHA256_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251230.md`

---

### EvidenceRefs Multi-line Range Validation (Step 84)

- Step 84 (SSOT): `docs/v11/V11_STEP84_EVIDENCE_REFS_MULTI_LINE_RANGE_VALIDATION_20251230.md`
- Step 84 (Quant record): `docs/v11/V11_STEP84_EVIDENCE_REFS_MULTI_LINE_RANGE_VALIDATION_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Runtime EvidenceRefs Auto-Generation (Step 85)

- Step 85 (SSOT): `docs/v11/V11_STEP85_RUNTIME_EVIDENCE_REFS_AUTOGEN_20251230.md`
- Step 85 (Quant record): `docs/v11/V11_STEP85_RUNTIME_EVIDENCE_REFS_AUTOGEN_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Backfill View Verifier (Step 86)

- Step 86 (SSOT): `docs/v11/V11_STEP86_BACKFILL_VIEW_VERIFIER_20251230.md`
- Step 86 (Quant record): `docs/v11/V11_STEP86_BACKFILL_VIEW_VERIFIER_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Generic EvidenceRefs Backfill View Bundle (Step 87)

- Step 87 (SSOT): `docs/v11/V11_STEP87_GENERIC_EVIDENCE_REFS_BACKFILL_VIEW_BUNDLE_20251230.md`
- Step 87 (Quant record): `docs/v11/V11_STEP87_GENERIC_EVIDENCE_REFS_BACKFILL_VIEW_BUNDLE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Order Confirmation EvidenceRefs Bundle (Step 88)

- Step 88 (SSOT): `docs/v11/V11_STEP88_ORDER_CONFIRMATION_EVIDENCE_REFS_BUNDLE_20251230.md`
- Step 88 (Quant record): `docs/v11/V11_STEP88_ORDER_CONFIRMATION_EVIDENCE_REFS_BUNDLE_IMPLEMENTED_IN_QUANT_20251230.md`

---

### Real Run Acceptance (Step 89)

- Step 89 (SSOT): `docs/v11/V11_STEP89_REAL_RUN_ACCEPTANCE_MAC_PREFLIGHT_VPS_CONTAINER_20251230.md`
- Step 89 (Quant prereq fix): 修复 non-stub 模式下 runner 未注入 `freeze_manager` 导致的 fail-closed（code commit: `88a1be07c1b16a8af1f794eaedd97c7cd2653232`；repo: `https://github.com/Garylauchina/Prometheus-Quant.git`）
- Step 89 (SSOT addendum): 追加“运行记录锚点”要求（runs_root/run_id + build_git_sha + image_digest + 可复跑命令），防止“跑过但找不到证据/无法对齐镜像”
- Step 89 (Quant acceptance record): `docs/v11/V11_STEP89_REAL_RUN_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md`（Quant: [doc commit](https://github.com/Garylauchina/Prometheus-Quant/commit/2a8e25f39876940b99205e1781ce1da1ca4df167) / [view file @ doc commit](https://github.com/Garylauchina/Prometheus-Quant/blob/2a8e25f39876940b99205e1781ce1da1ca4df167/docs/v11/V11_STEP89_REAL_RUN_ACCEPTANCE_IMPLEMENTED_IN_QUANT_20251230.md)；[Errata commit](https://github.com/Garylauchina/Prometheus-Quant/commit/4797952cd14db6e58860b71ef5a47bbe44f1cb00)；anchors: run_id=`run_step89_phase_b_20251230T210849Z`, image_digest=`sha256:42d8fc4c...`, build_git_sha=`1f3e0a7...`）
- Step 89 (Quant CI truth anchor): main HEAD=`34124298055225b150f4944016070cafc995f999`（[V11 Evidence Gate run 20613243466](https://github.com/Garylauchina/Prometheus-Quant/actions/runs/20613243466) = success）
- Step 89 (Research closure): `docs/v11/V11_STEP89_REAL_RUN_ACCEPTANCE_CLOSURE_20251231.md` (PASS)

---

### CI Truth Policy & Alerting (Step 90)

- Step 90 (SSOT): `docs/v11/V11_STEP90_CI_TRUTH_POLICY_AND_ALERTING_20251231.md`

---

### Trade Chain Evidence Extension (Step 91)

- Step 91 (SSOT): `docs/v11/V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_20251231.md`
- Step 91 (Quant record): `V11_STEP91_TRADE_CHAIN_EVIDENCE_EXTENSION_IMPLEMENTED_IN_QUANT_20251231.md`（repo: `https://github.com/Garylauchina/Prometheus-Quant.git`；code commit: `9e4294c04751817de5737bf1d4ae1050f7a728da`；CI truth: `https://github.com/Garylauchina/Prometheus-Quant/actions/runs/20614483995` = success）

---

### Metabolism ↔ TradeChain Alignment (Step 92)

- Step 92 (SSOT): `docs/v11/V11_STEP92_METABOLISM_TRADECHAIN_ALIGNMENT_20251231.md`
- Step 92 (Quant record): `V11_STEP92_METABOLISM_TRADECHAIN_ALIGNMENT_IMPLEMENTED_IN_QUANT_20251231.md`（repo: `https://github.com/Garylauchina/Prometheus-Quant.git`；code commit: `9e4294c04751817de5737bf1d4ae1050f7a728da`；CI truth: `https://github.com/Garylauchina/Prometheus-Quant/actions/runs/20614483995` = success）

---

### Stability Window Protocol (Step 93)

- Step 93 (SSOT): `docs/v11/V11_STEP93_STABILITY_WINDOW_PROTOCOL_20251231.md`
- Step 93 (Quant fix, agent_roster + startup system_flatten, fail-closed): Quant main commit `10bdcfb` (`https://github.com/Garylauchina/Prometheus-Quant/commit/10bdcfb`)
- Step 93 (VPS weekly run, okx_demo_api, 10 ticks): run_id=`run_weekly_vps_okx_demo_api_20251231T082001Z`；build_git_sha=`c9172d0fda2d2e742e9976225a532c752daca6a7`；image_digest=`ghcr.io/garylauchina/prometheus-quant@sha256:336e4e45da427dea155c3ad3eaebb0de4c3b0c2136af411e09b22612360aad33`；Step88 verifier=PASS；status=`completed_with_evidence_gate_pass`
- Step 93 (VPS daily run, okx_demo_api, 96 ticks): run_id=`run_daily_vps_okx_demo_api_20251231T084358Z`；build_git_sha=`c9172d0fda2d2e742e9976225a532c752daca6a7`；image_digest=`ghcr.io/garylauchina/prometheus-quant@sha256:336e4e45da427dea155c3ad3eaebb0de4c3b0c2136af411e09b22612360aad33`；Step88 verifier=PASS；status=`completed_with_evidence_gate_pass`
- Step 93 (VPS daily run, okx_demo_api, 96 ticks, agent_roster + startup_flatten fix in effect): run_id=`run_daily_vps_okx_demo_api_20251231T094159Z`；build_git_sha=`10bdcfb7379e0ba9a72fed4f3732810e1ebd8a97`；image_digest=`ghcr.io/garylauchina/prometheus-quant@sha256:cba10ceb9459ad9dbc360238538ea9c66dbf037c89d08c3be828a2708ae9d4e0`；Step88 verifier=PASS；status=`completed_with_evidence_gate_pass`
- Step 93 (Incident, closed): Agent genome anchor not landed (clustering blocked): `docs/v11/V11_INCIDENT_AGENT_GENOME_ANCHOR_NOT_LANDED_FOR_CLUSTERING_20251231.md`

---

### One‑Shot Closure Proof (Step 94)

- Step 94 (SSOT): `docs/v11/V11_STEP94_ONE_SHOT_CLOSURE_PROOF_20251231.md`

---

### Execution Quality & Slippage Evidence (Step 95)

- Step 95 (SSOT): `docs/v11/V11_STEP95_EXECUTION_QUALITY_AND_SLIPPAGE_EVIDENCE_20251231.md`

---

### Exchange Error Basket (Step 96)

- Step 96 (SSOT): `docs/v11/V11_STEP96_EXCHANGE_ERROR_BASKET_20251231.md`

## Notes / Concepts

- CI Truth Rule (V11): Treat **only the latest successful workflow run on `main` HEAD** as the current truth. Do **NOT** infer system status from historical red runs or reruns on old SHAs (rerun does not include later fixes). For verification, always re-run on latest `main` (new commit / workflow dispatch).
- Time as Event Metrics (2025-12-30): `docs/v11/V11_NOTE_TIME_AS_EVENT_METRICS_20251230.md`
- Tickless / Event-Driven World (2025-12-30): `docs/v11/V11_NOTE_TICKLESS_EVENT_DRIVEN_WORLD_20251230.md`
- Incident (2025-12-30): Old runner left running (observation pollution): `docs/v11/V11_INCIDENT_OLD_RUNNER_LEFT_RUNNING_20251230.md`

---

## Migration Status

- Phase A（已执行）：新增 `docs/v11/` 并建立入口；更新全局 README 与 V10 index 的提示（零破坏）。
- Phase B1（已执行）：迁移 4 份 V11 核心锚点文档到 `docs/v11/`，并在旧路径保留 stub 指针文件（零断链）。
- Phase B2（已执行）：迁移 `V11_STEP*.md`（Step 27–53 等）从 `docs/v10/` 到 `docs/v11/`，并在旧路径保留 stub 指针文件。


