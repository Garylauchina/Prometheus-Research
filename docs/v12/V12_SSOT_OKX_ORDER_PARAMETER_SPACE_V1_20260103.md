# V12 SSOT — OKX Order Parameter Space (BTC-USDT-SWAP) — v1 — 2026-01-03

目标：把 **OKX 下单参数空间**冻结为 V12 的可审计事实，用于：
- Decision/Agent probe 的输出合同对齐（禁止悬空旋钮）
- Proxy Trader/Broker 的落盘字段对齐（join keys 可机验）
- NOT_MEASURABLE 与生态 fences（限速/模式差异/条件字段）口径统一

本文件 additive-only。

---

## 1) Scope（冻结）

- **exchange**: OKX
- **inst_id（v0 frozen）**: `BTC-USDT-SWAP`
- **API**: `POST /api/v5/trade/order`（private REST）
- **demo header（冻结）**: `x-simulated-trading: 1`（见 V11 SSOT §9.2）

SSOT anchors（只读引用）：
- V11 order param anchor: `docs/v11/V11_OKX_BTCUSDT_SWAP_CONTRACT_RULES_SSOT_20251231.md`（§12）
- V12 alignment pipeline: `docs/v12/V12_SSOT_MODELING_DOCS_AND_GENOME_ALIGNMENT_20260101.md`

---

## 2) Canonical parameter table（冻结入口）

说明：
- “Decision/Agent probe 输出”只允许来自本表（或被明确标记为 system default / gate controlled）。
- `required_rule` 为 v1 冻结入口；后续只做 additive 追加（补充条件/枚举/错误码），不改旧语义。

| Field | Type | required_rule | enum / notes | Alignment class |
|---|---:|---|---|---|
| `instId` | string | required | v0 固定：`BTC-USDT-SWAP` | system_default_or_derived |
| `tdMode` | string | required | `cross` / `isolated` | agent_expressible + gate_controlled |
| `side` | string | required | `buy` / `sell` | agent_expressible |
| `posSide` | string | conditional | `long` / `short` / `net`（依持仓模式） | agent_expressible + gate_controlled |
| `ordType` | string | required | `market` / `limit` / `post_only` / `fok` / `ioc` / `optimal_limit_ioc`（以 OKX 文档枚举为准） | agent_expressible + gate_controlled |
| `sz` | string | required | 数量口径（合约张数）必须可追溯到 ctVal=0.01 BTC | agent_expressible + gate_controlled |
| `px` | string | conditional | `ordType=limit/post_only` 时必填；market 时必须为空或不传 | agent_expressible + gate_controlled |
| `clOrdId` | string | optional (recommended) | join key（强烈建议系统生成并落盘） | system_default_or_derived |
| `tag` | string | optional | 建议 system 写入短归因标识（run_id/agent_id_hash） | system_default_or_derived |
| `reduceOnly` | bool/string | optional | 是否只减仓 | agent_expressible + gate_controlled |
| `expTime` | string | optional | Unix ms；请求有效截止时间 | system_default_or_derived + gate_controlled |
| `attachAlgoOrds` | array | optional | TP/SL 等结构（待补齐官方字段表后冻结） | agent_expressible + gate_controlled |

---

## 2.1 Conditional rules (v1, frozen entry)

本节冻结“条件字段”的最小口径（只增不改）：

- `posSide`（conditional）：
  - 若账户为双向持仓模式：`posSide ∈ {"long","short"}` 且必须显式传递
  - 若账户为单向持仓模式：`posSide="net"` 或不传（以 OKX 账户模式为准）
  - 若系统无法确认账户持仓模式：必须 NOT_MEASURABLE（`not_measurable:position_mode_unknown`）且 gate 必须 fail-closed（拒绝下单或切换到明确模式）

- `px`（conditional）：
  - `ordType in {"limit","post_only"}` ⇒ `px` 必填
  - `ordType="market"` ⇒ `px` 必须为空或不传（禁止伪造 0）
  - 若系统无法确认 tick/精度：必须 NOT_MEASURABLE（`not_measurable:price_precision_unknown`）

- `expTime`（optional, system-level）：
  - v1 建议由系统写入（避免网络延迟/交易所繁忙导致处理不确定）
  - 若设置：必须为 Unix ms string；若当前系统时间超过 expTime，交易所将不处理请求（见 V11 SSOT 用户粘贴段落）

- `attachAlgoOrds`（optional, TP/SL schema）：
  - v1 暂不冻结其内部结构（`not_measurable:tp_sl_schema_unknown`）
  - 若 Agent/Decision 试图表达 TP/SL：必须将其归类为 NOT_MEASURABLE 或显式 gate reject（禁止静默丢失）

---

## 3) NOT_MEASURABLE rules（冻结入口）

以下为 v1 的最小 reason_code vocabulary（可追加）：
- `not_measurable:account_mode_unknown`：无法确定 tdMode/posSide 规则
- `not_measurable:position_mode_unknown`：无法确定 `posSide` 语义/必填条件
- `not_measurable:lot_size_rules_unknown`：数量最小单位/张数换算未冻结
- `not_measurable:price_precision_unknown`：`px` 精度/tick 未冻结
- `not_measurable:tp_sl_schema_unknown`：TP/SL 结构未冻结
- `not_measurable:demo_header_missing`：demo 请求缺少 `x-simulated-trading: 1`
- `not_measurable:rate_limited`：请求被限速（含 50011/50061 等）
- `not_measurable:order_limit_reached`：触达挂单上限/策略单上限等生态 fences
- `not_measurable:maker_1000_match_limit`：taker 单触达 1000 笔 maker 匹配限制导致取消/部分成交
- `not_measurable:api_response_schema_drift`：返回中 code/sCode 语义不一致或字段漂移

---

## 3.1 Ecology fences (v1, frozen entry)

本节把你之前粘贴的“交易所层面的限制”冻结为 v1 入口（只增不改，细节可追加）：

- **挂单上限（冻结入口）**：
  - 未成交订单总上限：4000
  - 单产品未成交订单上限：500（含 limit/market/post_only/FOK/IOC/optimal_limit_ioc/TP-SL 等计入类型）

- **taker 匹配上限（冻结入口）**：
  - 当 taker 单匹配的 maker 订单数量超过 1000：
    - limit：仅成交与 1000 笔 maker 对应部分，其余取消
    - FOK：直接取消

- **限速语义（冻结入口）**：
  - `50011`：接口限速（用户请求频率过快）
  - `50061`：子账户维度限速（2s 内订单相关请求计数上限）
  - 发生限速时必须落盘并 NOT_MEASURABLE（`not_measurable:rate_limited`），禁止静默重试导致证据缺口

- **返回语义（冻结入口）**：
  - 若返回中存在 `sCode/sMsg`：以 `sCode/sMsg` 为准（而不是 code/msg）
  - 若返回中只有 `code/msg`：以 `code/msg` 为准
  - 任意解析失败/字段漂移必须 NOT_MEASURABLE（`not_measurable:api_response_schema_drift`）

---

## 4) Evidence sources & join keys（冻结入口）

必须落盘并可机 join：
- `order_attempts.jsonl`：保存 Agent 提案字段 + gate 结果
- `exchange_api_calls.jsonl` / `okx_api_calls.jsonl`：保存实际请求 params（至少含 `clOrdId/ordId`）
- `fills.jsonl` / `bills.jsonl`：truth materialization（PASS 分支）

关键 join keys（冻结）：
- `clOrdId`（client_order_id）
- `ordId`（exchange_order_id）

---

## 5) Acceptance (V12.4)（冻结入口）

PASS（v1）：
- 能从 PASS 的 broker run_dir 中观察到：`exchange_api_calls` 的请求 params 字段集合 ⊆ 本表字段集合
- “悬空旋钮扫描”输出 `unmapped_attempt_fields=[]`

FAIL：
- 出现无法映射到本表的“下单参数旋钮”（例如 Decision 输出了不存在字段）


