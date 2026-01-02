# V12 SSOT — OKX Account/Position + Pre-trade Parameter Space (BTC-USDT-SWAP) — v1 — 2026-01-03

目标：冻结“**非 order 但会改变订单语义/风险暴露/费用结果**”的参数空间，用于愚蠢 Agent 的碰撞实验：
- Agent/Decision 可以表达目标（例如 `leverage_target`），但系统必须把它映射到可执行接口并落盘真值
- 避免“系统默认/隐式状态”偷偷影响结果，导致不可复现

本文件 additive-only。

---

## 1) Scope（冻结）

- **exchange**: OKX
- **inst_id（v0 frozen）**: `BTC-USDT-SWAP`
- **spaces**：
  - **Account/Position state space（读真值）**：用于证明当前状态（lever/mgnMode/posMode…）
  - **Pre-trade config write space（写接口）**：用于把状态设到目标值（set-leverage / set-position-mode…）

与 order 参数空间的关系（冻结）：
- `POST /api/v5/trade/order` 的字段只覆盖“下单参数”
- 本文件覆盖“下单前置状态/账户模式”，两者必须共同对齐，才能保证碰撞实验可审计

SSOT anchors（只读）：
- Order param space (v1): `docs/v12/V12_SSOT_OKX_ORDER_PARAMETER_SPACE_V1_20260103.md`
- Balance delta + settlement: `docs/v12/V12_SSOT_AGENT_BALANCE_DELTA_AND_EXCHANGE_AUTO_EVENTS_20260102.md`

---

## 2) Canonical non-order knobs（冻结入口）

### 2.1 Knob vocabulary（v1）

| Knob | Type | Semantics | Agent expresses? | Gate controlled? | Evidence anchor |
|---|---:|---|---:|---:|---|
| `mgnMode` | string | `cross` / `isolated`（保证金模式） | yes (target) | yes | positions truth + pretrade write |
| `posMode` | string | `net` vs `long_short`（持仓模式/双向） | yes (target) | yes | account config truth + (optional) write |
| `posSide` | string | `long` / `short` / `net`（与 posMode 强相关） | yes (as order conditional) | yes | order params + positions truth |
| `leverage_target` | string/number | 目标杠杆倍数 | yes | yes | set-leverage call + positions truth |

冻结说明：
- 这些 knobs **不是** `order_api_parameter_space` 的字段，但会改变同一订单参数的含义与结果
- 因此必须进入对齐表与 verifier 验收闭环

---

## 3) Pre-trade write APIs（冻结入口）

### 3.1 Set leverage（必须硬化）

- **Endpoint**（冻结入口）：`POST /api/v5/account/set-leverage`
- **典型 request params**（冻结入口；以 OKX 文档/真实回执为准，后续只增不改）：
  - `instId`（string, required）
  - `mgnMode`（string, required: `cross|isolated`）
  - `lever`（string, required: leverage value）
  - `posSide`（string, conditional: when in long/short mode）

### 3.2 Set position mode（v1 入口，可能依账户能力）

- **Endpoint**（冻结入口，占位）：OKX 存在“设置持仓模式/双向模式”的能力面（具体 path 待 scanner/真实回执确认后冻结）
- 在未确认前：任何“切换 posMode”的写操作必须 NOT_MEASURABLE（`not_measurable:pos_mode_write_api_unknown`）

---

## 4) Truth read APIs（冻结入口）

目的：提供可机验的“状态真值”用于证明 pre-trade 配置已生效。

### 4.1 Positions truth（必须硬化）

- **Endpoint**（冻结入口）：OKX positions（具体 path 由 Quant/Scanner 真实实现确认；本 SSOT 先冻结字段语义）
- **必须可读字段（v1）**：
  - `instId`
  - `mgnMode`
  - `posSide`（若适用）
  - `lever`（实际杠杆倍数）

---

## 5) Evidence & join rules（冻结入口）

必须落盘：
- `exchange_api_calls.jsonl` / `okx_api_calls.jsonl`
  - 必须包含：`endpoint`、`params`、`success`、以及可解析的 `response_data`（避免 string parsing）
- `order_attempts.jsonl`
  - 必须记录：`leverage_target`（若决策表达）与应用状态字段（见下）
- positions truth evidence（建议落盘为 `position_snapshots.jsonl` 或等价文件；v1 作为入口占位）

Join anchors（冻结）：
- pretrade write call：`exchange_api_call_id`（或 request id）+ `endpoint=/account/set-leverage`
- positions snapshot：`snapshot_id`（或 ts_utc + account_id_hash + instId 的稳定组合键）
- order attempt：`client_order_id/clOrdId`

---

## 6) Verdict & NOT_MEASURABLE（冻结入口）

### 6.1 NOT_MEASURABLE reason_code vocabulary（v1）

- `not_measurable:set_leverage_api_unavailable`
- `not_measurable:set_leverage_param_unknown`
- `not_measurable:positions_truth_unavailable`
- `not_measurable:pos_mode_unknown`
- `not_measurable:pos_mode_write_api_unknown`

### 6.2 Fail-closed discipline（冻结）

- 若 Decision/Agent 表达了 `leverage_target`：
  - 必须存在可回指证据：要么
    - 1) `set-leverage` call 证据（write truth）+ 2) positions truth 证据（read truth）
    - 或者（v1 允许二选一入口）：
      - 仅 `set-leverage` call 证据（并明确 `positions_truth_not_checked` → NOT_MEASURABLE）
  - 任一关键证据缺失时：该 run 对“杠杆对齐”维度必须 NOT_MEASURABLE（禁止 PASS 假阳性）

---

## 7) Acceptance (V12.4 v1)（冻结入口）

PASS（v1，杠杆对齐最小闭环）：
- 在一个 verdict=PASS 的 broker+settlement run 中：
  - 观察到 `set-leverage` 的 api_call 证据（或等价配置写证据）
  - 且能在 positions truth 中证明 `lever` 与目标一致（若 positions truth 尚未纳入，必须将该项判 NOT_MEASURABLE）

FAIL：
- 决策/证据声称 leverage 已应用，但无任何可回放真值证据可回指（悬空真值）


