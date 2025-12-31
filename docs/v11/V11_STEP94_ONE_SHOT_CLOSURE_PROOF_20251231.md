# V11 Step 94 — One‑Shot Closure Proof (Decision → Trade → Evidence → Verify) — SSOT — 2025-12-31

目的：解决一个长期悬而未决的问题——从 V10 开始一直缺少一次**可机核验**的完整闭环样本：

> 决策（Decision）→ 真实下单/成交（Trade, OKX demo）→ 证据落盘（Evidence）→ 核查通过（Verify）

本 Step 的定位是：**用一次“强制样本（one‑shot）”证明闭环可以真实发生**，而不是替代演化策略本身。

本文件只允许追加（additive-only）。

---

## 1) Scope（冻结）

覆盖：
- OKX demo API（真实写路径）
- 非 preflight / 非 broker_trader_test 的 agent‑level 交易样本（必须可区分）
- 复用 Step88（P0–P5）与 Step93（agent_roster + startup_flatten）作为下层依赖

不覆盖：
- “让 Agent 自然频繁交易”的策略设计（那是后续演化/策略问题）
- ROI/繁殖/tickless 等架构升级（稳定窗口禁止）

---

## 2) Hard Constraints（冻结）

- **Additive-only**：只允许新增 flag/新增 manifest 字段/新增证据文件/新增 verifier；不改旧字段语义。
- **Fail-closed honesty**：one‑shot 启用但不能证明闭环完成 → 必须 FAIL（不得 PASS/不得自相矛盾）。
- **Non‑preflight**：该样本必须明确标识为“非 preflight”，不得复用 `broker_trader_test` 路径，也不得混淆为自检单。
- **Single gateway**：所有写操作必须通过 BrokerTrader（不得绕过）。

---

## 3) Definitions（冻结）

### 3.0 Terminology alias (frozen)

为减少表达冗余，本 Step 内允许以下等价短语（语义必须严格一致）：
- **First Flight / Real Flight** == “非 preflight 的 agent 写路径闭环样本”，且该闭环必须 **真实对接交易所并落盘真值**（至少 orders_history；若 filled 则 fills/bills 必须可 join）
- 明确排除：任何 `run_manifest.broker_trader_test.client_order_ids` 中的启动自检单，不计入 First/Real Flight

### 3.1 One‑Shot Sample

一次 one‑shot sample 指一次明确的 agent‑level 写入尝试：
- intent_source = `decision_cycle`
- intent_kind ∈ {`agent_intent_open`, `agent_intent_close`}（按实现枚举）
- 需要满足 Step88 的 P0–P5 证据闭环（至少 orders_history 可证；若 filled 则 fills/bills 必须可证）

### 3.2 “Non‑preflight”的判定

必须满足以下至少一条：
- `order_attempts.jsonl` 记录包含 `lifecycle_scope="agent_live"`（或等价冻结 vocabulary），且该 scope 不属于 preflight vocabulary
- 或者 `order_attempts.jsonl` 记录包含 `flags.oneshot=true`（additive 新字段）

并且不得出现：
- `run_manifest.broker_trader_test.client_order_ids` 中包含该 one‑shot 的 `client_order_id`

补充硬规则（防止“启动自检单伪装 decision_cycle”污染观测）：
- 任何出现在 `run_manifest.broker_trader_test.client_order_ids` 中的订单（preflight 自检单）：
  - **不得**在 `order_attempts.jsonl` 中被标记为 `intent_source="decision_cycle"`
  - **不得**填写 `agent_id_hash`（必须为 null）
  - 建议（additive-only）：写入 `flags.preflight_test=true` 或 `lifecycle_scope="preflight_test"` 以便机器可判定
  - 该类订单不计入 Step94 的 one‑shot flight 证明样本

---

## 4) Required Evidence (run_dir)（冻结）

必须存在（依赖/复用）：
- Step93：`agent_roster.json`（agent→genome anchors）
- Step93：`run_manifest.json.startup_flatten`（启动清仓证据）
- Step88：`order_attempts.jsonl`（P0）
- Step88：`order_status_samples.jsonl` / `orders_history.jsonl`（P2 可证）
- Step88：`fills.jsonl`（若 filled；P3）
- Step88：`bills.jsonl`（若 filled；P4）
- Step88：`auditor_report.json`（P5）

新增（Step94）：
- `decision_trace.jsonl` 中必须出现一条 one‑shot 决策记录（即使系统当前仍为 skeleton，也必须写下这条“决策证据”）。
- `run_manifest.json.oneshot_closure_proof`（additive 新字段，见 §5.2）

---

## 5) Runner Contract（冻结）

### 5.1 Flags（additive-only）

Runner 必须新增（默认关闭）：
- `--enable-preflight-test-order`：控制 preflight 固定自检单是否允许真实下单（默认 **false**）
- `--force-one-shot-trade`：启用 Step94 one‑shot（默认 **false**）
- `--one-shot-tick`：one‑shot 发生的 tick（默认 2）
- `--one-shot-action`：枚举（建议：`open_short`/`open_long`/`close_to_flat`），默认 `open_short`

### 5.2 Manifest section（additive-only）

`run_manifest.json.oneshot_closure_proof` 最小字段：
- `enabled`: bool
- `tick`: int
- `action`: string
- `agent_id_hash`: string
- `client_order_id`: string|null
- `ordId`: string|null
- `step88_verdict`: string|null（写明 PASS/NOT_MEASURABLE/FAIL）

硬规则：
- `enabled=true` 时，必须写入上述字段（不可省略）。

### 5.3 Execution order（non‑stub）

当 `--force-one-shot-trade` 启用时：
1) 必须先完成 Step93 `startup_flatten`（若失败 → FAIL‑CLOSED）
2) 写入一条 `decision_trace.jsonl` one‑shot 决策记录（明确标识 oneshot）
3) 通过 BrokerTrader 写入 one‑shot intent（标识为 non‑preflight）
4) 运行 auditor + Step88 verifier
5) 若无法证明 exchange truth（至少 orders_history 可证）→ FAIL‑CLOSED

---

## 6) Verifier Gate（冻结）

新增 `tools/verify_step94_oneshot_closure_proof.py`（read‑only）：

输入：
- run_dir

校验：
- `run_manifest.oneshot_closure_proof.enabled==true`
- `decision_trace.jsonl` 存在且能找到对应 one‑shot 记录（run_id + tick + agent_id_hash + oneshot marker）
- `order_attempts.jsonl` 存在且能找到对应 `client_order_id`（并且满足 non‑preflight 判定）
- `orders_history.jsonl` 中能找到该 `clOrdId`，状态为 terminal（filled/cancelled/rejected）
- 若 filled：`fills.jsonl`/`bills.jsonl` 必须能 join 到同一 ordId（或等价 join 证明）
- Step93 roster verifier PASS（可复用 `verify_step93_agent_roster.py`）
- Step88 verifier PASS

必须显式检查（fail-closed）：
- one‑shot 的 `client_order_id` **不在** `run_manifest.broker_trader_test.client_order_ids` 中
- 若 `run_manifest.broker_trader_test.client_order_ids` 非空：
  - 对其中任一 `client_order_id`，若在 `order_attempts.jsonl` 中出现 `intent_source="decision_cycle"` 或 `agent_id_hash!=null`，则判定为 **FAIL**（因为 preflight 自检单伪装为 agent 决策会破坏 Step94 的“non‑preflight”可核验性）

Verdict：
- 任一缺失/无法 join/无法证明闭环：FAIL（fail‑closed）

---

## 7) Acceptance（冻结）

一次 Step94 的 PASS 必须同时满足：
- Step93（agent_roster + startup_flatten）满足
- Step88 PASS
- Step94 verifier PASS

产出（用于 Research/Quant record）：
- commit SHA
- image_digest
- run_id + run_dir
- 关键 join 证明（client_order_id ↔ ordId ↔ fills/bills）
- Step94 verifier 输出

---

## 8) Change Log（追加区）

- 2025-12-31: 创建 Step94 SSOT（One‑Shot Closure Proof：非 preflight 的决策→交易→落盘→核查闭环样本）。


