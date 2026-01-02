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

## 3) NOT_MEASURABLE rules（冻结入口）

以下为 v1 的最小 reason_code vocabulary（可追加）：
- `not_measurable:account_mode_unknown`：无法确定 tdMode/posSide 规则
- `not_measurable:position_mode_unknown`：无法确定 `posSide` 语义/必填条件
- `not_measurable:lot_size_rules_unknown`：数量最小单位/张数换算未冻结
- `not_measurable:price_precision_unknown`：`px` 精度/tick 未冻结
- `not_measurable:tp_sl_schema_unknown`：TP/SL 结构未冻结
- `not_measurable:demo_header_missing`：demo 请求缺少 `x-simulated-trading: 1`

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


