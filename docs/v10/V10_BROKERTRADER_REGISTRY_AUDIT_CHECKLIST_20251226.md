# V10 BrokerTrader Registry Audit Checklist (Evidence gaps taxonomy) — 2025-12-26

目的：用 ExchangeAuditor 的只读交叉核验结果，持续发现并覆盖“入册漏洞”。  
方法：维护一个 append-only 的 discrepancy taxonomy：每新增一种漏洞，只允许新增条目，不允许改旧条目的语义。

适用范围：`execution_world`（OKX demo/live）。

依赖契约：
- BrokerTrader：`docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`
- 订单确认协议（P0–P5）：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
- ExchangeAuditor：`docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`

---

## 0) 词典字段（每条 discrepancy 必须包含）

- `discrepancy_type`：本表定义的类型
- `severity`：`FAIL | NOT_MEASURABLE | WARN`
- `exchange_evidence_anchor`：交易所可回查 JSON 的定位锚点（例如 `ordId` / `tradeId` / `billId` / 时间窗+分页游标）
- `local_evidence_anchor`：本地入册证据锚点（例如 `clOrdId` / `ordId_hash` / evidence_path + line_ref）
- `symptom`：可复核现象描述（不讲故事）
- `likely_root_causes`：典型根因（通信/分页/时窗/字段缺失/去重错误等）
- `required_fix`：必须补的证据/改动（面向实现）

---

## 1) Discrepancy taxonomy（append-only）

### 1.1 ack→status 链断裂（P2 未闭合）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `ack_without_terminal_status` | FAIL | 本地 `order_attempts` 显示 `ack_received=true`，但审计者无法在规定最终一致窗口内通过交易所查询得到终态（filled/canceled 等） | 订单查询失败/限频、查询时窗不覆盖、使用了错误的 id（hash 当 ordId）、网络退化未落盘 | 强制 P2 轮询直到终态或超时；落盘每次 status 响应；超时写 `truth_quality=degraded` 并触发执行冻结（后续版本才允许干预） |
| `ack_recorded_but_missing_order_id_binding` | FAIL | 本地只有 `clOrdId`，但缺少 `ordId` 或可用于回查的 `ordId_hash`，导致 join 断裂 | 下单回包未提取/脱敏、字段名不一致、日志裁剪 | 在 P1 回包中提取 ordId 并脱敏记录；若回包没有 ordId，必须在 P2 首次查询中补齐并入册 |

### 1.2 本地漏入册（exchange 可查，本地缺证据）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `terminal_status_without_local_record` | FAIL | 交易所可查到订单终态（基于 `clOrdId/ordId` 或时间窗），但本地 run_dir 缺少对应 `order_status_samples` 记录 | runner 绕过 BrokerTrader、入册写文件失败、异常未 STOP | 强制唯一入口；入册失败即 stop；补充写入错误事件 evidence |
| `exchange_order_unattributed` | FAIL | 交易所可回查到订单事实，但本地入册记录缺少 `agent_id_hash` 且也缺少 `lifecycle_scope`（无法判定这是 Agent 委托还是生命周期强平/收尾动作） | 生命周期强平未标注 scope、补救单临时写代码绕过、入册字段遗漏 | 规定：所有下单入册必须二选一提供归因锚点（agent_id_hash 或 lifecycle_scope）；缺失即 FAIL；修复为补字段并重跑最小 PROBE |
| `fills_present_but_not_recorded` | NOT_MEASURABLE | 交易所 fills 可查到 `ordId` 的成交，但本地无 fills 证据（仅能证明“没记录”，不能证明“没成交”） | 未实现 P3、分页没走完、时窗不对 | 若要做成交/费用结论必须实现并落盘 P3（含分页证据）；否则一律 NOT_MEASURABLE |
| `bills_present_but_not_recorded` | NOT_MEASURABLE | 交易所 bills 可查到与时间窗相关的账务事件，但本地无 bills 证据 | 未实现 P4、分页/时窗不足 | 若要做账务闭环必须实现 P4（含分页证据）；否则一律 NOT_MEASURABLE |

### 1.6 生命周期强平失败（高风险事件）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `lifecycle_flatten_repeated_failure` | FAIL | 周期末触发 `system_flatten`，但多次尝试后仍无法证明仓位敞口归零（无终态/终态失败/positions 仍非零） | 通信退化/限频、账户被风控限制、交易所异常、流动性枯竭导致无法成交/无法撤单 | 限次重试+退避并入册每次尝试；超过阈值必须 STOP+IEB；失败需分型 reason_code 并保全所有 raw 证据 |

### 1.7 L1 分类缺失/不一致（执行过程中未做一级分类）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `missing_l1_classification` | FAIL | 发现入册的委托尝试/订单状态记录，但缺少 `l1_classification`（无法审计执行分型与触发动作是否正确） | BrokerTrader 未实现 L1 taxonomy 或日志字段漏写 | 强制所有入册记录补齐 `l1_classification`；更新 schema 冻结后重跑最小 PROBE |
| `l1_classification_mismatch` | WARN | `reason_code`/HTTP status/sCode 体现为明确拒绝或账户受限，但 L1 被标为 `L1_OK` 或不合理类别 | 误分类、缺少映射表、异常分支走错 | 以 `V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md` 的 reason_code→L1 映射表为准做一致性核对；补充单测/PROBE 覆盖关键分支 |

### 1.3 分页/完整性漏洞（最常见的“伪不一致”来源）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `paging_incomplete` | NOT_MEASURABLE | 端点响应存在 `hasMore=true`/游标未走完，但本地未继续拉取；无法证明集合闭包 | 限频/超时、实现偷懒、错误的退出条件 | 必须落盘分页参数与响应游标；hasMore 未清空则结论降级 NOT_MEASURABLE |
| `time_window_gap` | NOT_MEASURABLE | 查询时间窗存在缺口，导致部分订单/成交/账单落在缺口内 | tick 对齐错误、时区/毫秒处理错误 | 明确时间锚点（source_ts_ms_used）；用重叠窗口或连续游标，避免空洞 |

### 1.4 去重/幂等漏洞（导致重复/漏记）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `duplicate_bill_ids_in_registry` | FAIL | 本地 bills 入册出现相同 `billId` 多次（重复事件污染） | 去重键选错、并发写入 | 以 bills 行主键（billId/id）幂等；追加写入时必须检测重复并记录错误 |
| `duplicate_trade_ids_in_registry` | FAIL | 本地 fills 入册出现相同 `tradeId` 多次 | 去重键选错、分页游标回退 | 以 tradeId 幂等；记录分页游标，避免重复拉取 |

### 1.5 账单不可归因（不是错误，但必须识别）

| discrepancy_type | severity | symptom | likely_root_causes | required_fix |
|---|---|---|---|---|
| `bill_without_order_id` | WARN | bills 行没有 `ordId`（资金费/划转/系统调整等），无法归因到具体订单/Agent | 交易所业务类型本身如此 | 只能记为系统级事件；禁止硬分摊到 Agent；若需要归因必须依赖交易所提供的其他可回查关联键 |

---

## 2) 使用方式（最小流程）

1) BrokerTrader 先完整入册：`order_attempts.jsonl` + `order_status_samples.jsonl`（P1+P2）
2) ExchangeAuditor 以只读 key 做交叉核验，产出：
   - `auditor_report.json`
   - `auditor_discrepancies.jsonl`
3) 用本表把 `auditor_discrepancies` 映射为：
   - `FAIL / NOT_MEASURABLE / WARN`
   - 以及“下一次修复必须补什么证据”

---

## 3) 版本纪律（hard）

- 本文档 **append-only**：只允许新增 discrepancy 类型，不允许改既有条目的语义。
- 新增条目必须同时更新：
  - ExchangeAuditor 的 `auditor_discrepancies.jsonl` 生成逻辑（implementation repo）
  - Gate4 的裁决口径（若提升为 FAIL/硬门槛）


