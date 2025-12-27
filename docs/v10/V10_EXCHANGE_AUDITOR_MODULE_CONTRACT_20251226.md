# V10 ExchangeAuditor Module Contract (Read-only cross-check) — 2025-12-26

目的：为 BrokerTrader（执行+入册）提供一个**独立的只读审计通道**，用交易所可回查 JSON 做交叉核验，识别通信/异步/分页漏取导致的证据缺口与关联断裂。

定位：**审计者不是第二个交易入口**。它不参与运行时执行与决策，不产生任何写操作。

---

## 0) 硬规则（hard）

1) **只读密钥 + 权限隔离**
- 必须使用独立的审计 API key（与 BrokerTrader 的执行 key 分离）。
- 权限必须是只读（账户/持仓/订单/成交/账单查询），禁止任何下单/撤单/平仓能力。

2) **禁止写操作（hard fail）**
- 审计模块调用到任何写端点（place/cancel/amend/close/transfer 等）直接 FAIL，并生成 IEB/incident 证据（说明权限配置错误）。

3) **不影响执行**
- 审计模块不得被 runner 用作“补漏执行逻辑”，只能产出审计报告与异常清单。
- **本版本范围（2025-12-26）**：只做到“落盘”，不讨论也不实现任何运行时干预（freeze/stop/自动修复）。
- 后续若要引入运行时干预，必须单独立契约与验收门槛（避免把“审计”偷偷变成“第二套控制逻辑”）。

4) **真值口径一致**
- 审计使用与 BrokerTrader 相同的“订单确认协议”口径（P0–P5）：
  - `docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`

---

## 1) 审计输入（Input）

审计模块不直接读“内存状态”，只接受：

- `run_dir`（包含 BrokerTrader/ledger 的入册证据文件）
- `run_id`
- 审计范围参数：
  - 时间窗（start/end）
  - 订单集合（例如从 `order_attempts.jsonl` 提取的 `clOrdId/ordId_hash`）
  - 采样策略（全量/抽样）

---

## 1.5) 默认调用时机（编排约束，non-invasive）

默认编排建议（本版本）：

- **每个轮回周期结束时**，系统调用一次 ExchangeAuditor，对当期 `run_dir` 做只读交叉核验并落盘：
  - `auditor_report.json`
  - `auditor_discrepancies.jsonl`
- 然后再生成/更新 `FILELIST.ls.txt` 与 `SHA256SUMS.txt`，最后停止运行。

说明：
- 这只是“runner 编排约束”，不要求改变审计模块功能。
- 未来若改为“定期审计”（例如每 N ticks/每 M 分钟一次），只需要调整调用频率，不需要修改审计模块接口与语义。

---

## 2) 允许/禁止的交易所端点（Policy）

允许（只读）：
- orders 查询：orders-history / order status（以 OKX 官方 API 实际命名为准）
- fills 查询
- account bills 查询
- positions / balance / equity 查询
- public market data（可选）

禁止（写）：
- place order / cancel / amend / close positions / transfers / leverage changes 等一切会改变账户状态的端点

---

## 3) 审计输出（Evidence artifacts，append-only）

最小产物（必须）：

- `auditor_report.json`
  - `run_id`
  - `auditor_contract_version`
  - `audit_scope`（时间窗/采样策略/请求分页口径）
  - `verdict`：`PASS | NOT_MEASURABLE | FAIL`
  - `summary_counts`：
    - `orders_acked_count`
    - `orders_confirmed_terminal_count`（P2 完成数）
    - `orders_missing_terminal_count`
    - `fills_checked_count`
    - `bills_checked_count`
    - `paging_incomplete_count`
  - `truth_quality` 与 `reason_code` 统计

- `auditor_discrepancies.jsonl`（每条一条异常，append-only）
  - 类型示例：
    - `ack_without_terminal_status`
    - `terminal_status_without_local_record`（交易所能查到但本地没入册）
    - `fills_present_but_not_recorded`
    - `bills_present_but_not_recorded`
    - `paging_incomplete`
    - `forbidden_write_endpoint_attempted`（hard fail）

建议产物（可选）：
- `auditor_raw_samples_index.json`（脱敏 raw 样本索引 + hash）

---

## 4) 裁决口径（PASS / NOT_MEASURABLE / FAIL）

- PASS（最小）：
  - 对所有 `ack_received=true` 的订单，审计者也能通过交易所查询复现其终态（P2），且未发现“本地漏入册”的关键断裂。

- NOT_MEASURABLE：
  - 因交易所限制/限频/字段缺失/分页不可证明完整性导致无法完成 P3/P4 的闭环，但已 `truth_quality=degraded/unknown + reason_code` 如实标注。

- FAIL（硬失败）：
  - 审计模块发生任何写端点调用（权限隔离失败）。
  - 审计发现：交易所存在可回查的订单/成交/账单事实，但本地入册证据缺失且无法解释（evidence chain broken）。

---

## 5) Freeze（接口冻结）

通过 Gate4/PROBE 接受后冻结：
- 审计策略输入字段（scope）
- `auditor_report.json` / `auditor_discrepancies.jsonl` schema
- `reason_code` 词表（additive-only）

破坏性变更必须：
- 升级 `auditor_contract_version`
- 重跑最小审计 PROBE 并更新 Research 文档链接


