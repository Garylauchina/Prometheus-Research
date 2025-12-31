# OKX 交易所 BTC/USDT 永续合约规则说明（SSOT / 逐段粘贴核对用）— 2025-12-31

目的：把 OKX 的 **BTC/USDT 永续合约（swap）规则**冻结为一份可审计、可逐条对照代码实现的 SSOT。  
后续你将逐段粘贴官方规则文本；我们只做 **additive-only 追加**，并在每段后给出“代码核对点”。

本文件只允许追加（additive-only）。

---

## 0) How to use（流程）

你每次粘贴一段官方规则后，我会：
- 把该段原文放入对应章节的“Quoted Rules（verbatim）”
- 提取出 machine-checkable 的约束点（字段/枚举/范围/条件）
- 列出需要在 Quant 代码中核对的位置（文件路径 + 关键字段/函数名）

观测纪律（冻结）：
- 我们不强求“每次交易必须成功”；成功/失败都是有效样本。
- 硬要求是：每次交易尝试的结果与原因必须落盘为可审计证据（成功/拒绝/超时/不可测量），并能 join 回交易链与错误篓子（Step96）。

---

## 1) Instrument Identity（合约标识）

### 1.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 页面信息，待后续补充官方链接/原文出处）

- BTCUSDT 永续
- 结算货币：USDT

### 1.2 Code checkpoints

- Quant（V11）下单/查询 instId 是否使用 OKX 的永续合约标识（通常为 `BTC-USDT-SWAP`）：
  - `prometheus/v11/ops/first_flight.py`（`--inst` 默认值）
  - `prometheus/v11/connectors/okx_native_writer.py`（place/query payload 的 `instId`）
  - `prometheus/v11/auditor/exchange_auditor.py`（orders-history 查询使用的 instId 来源于 `run_manifest.world_parameters.inst_id`）

---

## 2) Trading Mode / Margin Mode（交易模式/保证金模式）

### 2.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 产品文档节选：合约盈亏计算；发布 2022-06-20，更新 2025-04-01）

涉及模式：
- 单币种保证金模式——全仓
- 跨币种保证金模式——全仓
- 单币种/跨币种/投资组合保证金模式——逐仓

涉及“持仓模式/开平逻辑”：
- 开平仓模式
- 买卖模式

术语：
- 持仓量：买卖模式下，多仓持仓量为正数，空仓持仓量为负数
- 可平量：仅开平仓模式展示；可平量 = 持仓量 - 平仓挂单占用仓位数量
- 收益：当前仓位未实现盈亏
- 收益率：收益 / 开仓保证金

### USDT 保证金合约（你当前关心的 BTCUSDT 永续属于该类）未实现盈亏（收益）公式：
- 多仓收益 = 面值 * |张数| * 合约乘数 *（标记价格 - 开仓均价）
- 空仓收益 = 面值 * |张数| * 合约乘数 *（开仓均价 - 标记价格）

### 初始保证金（USDT 保证金）：
- 初始保证金 = 面值 * |张数| * 合约乘数 * 标记价格 / 杠杆倍数

### 维持保证金（USDT 保证金）：
- 维持保证金 = 面值 * |张数| * 合约乘数 * 维持保证金率 * 标记价格

### 逐仓模式额外公式（USDT 保证金）：
- 预估强平价（多仓）= (保证金余额 - 面值 * |张数| * 开仓均价) / (面值 * |张数| * (维持保证金率 + 手续费率 - 1))
- 预估强平价（空仓）= (保证金余额 + 面值 * |张数| * 开仓均价) / (面值 * |张数| * (维持保证金率 + 手续费率 + 1))
- 保证金余额：开仓保证金 + 手动追加（或减少）的保证金
- 保证金率（USDT 保证金）= (保证金余额 + 收益) / (面值 * |张数| * 标记价格 * (维持保证金率 + 手续费率))

### 2.2 Code checkpoints

- **模式字段是否显式落盘**（truth-first / 可审计）：
  - 下单 payload 是否显式包含 `tdMode`（cross/isolated），并与 SSOT 中“全仓/逐仓”一致
  - 如果 OKX 还要求 `mgnMode`/posMode 之类字段（取决于接口/账户设置），必须在代码与证据中明确
  - 核对点（Quant）：`prometheus/v11/connectors/okx_native_writer.py` 下单 params 构造（当前已见 `tdMode="cross"`）

- **posSide / 开平 vs 买卖模式的兼容性**：
  - 代码必须明确自己采用哪一种持仓模式（双向 posSide vs 单向净持仓），否则会出现“能下单但语义不一致/平仓失败”
  - 核对点：
    - 下单参数是否包含 `posSide`（long/short）或等价字段
    - 平仓逻辑是否依赖“开平仓模式”的可平量语义（若依赖必须有证据）

- **Mark price（标记价格）作为关键真值输入**：
  - 文档公式大量使用标记价格：任何 margin/强平/未实现盈亏的解释都必须引用 **交易所真值的 mark price**（或明确 NOT_MEASURABLE）
  - 核对点：`okx_market_raw.jsonl`/对应 market data 证据里是否落盘 markPx，并能 join 到 run/tick

- **严禁内部模拟当真值**：
  - 上述公式若在 Quant 内部被计算，只能作为 derived/explanatory，并且输入必须来自 fills/bills/positions/market truth
  - 否则必须输出 `null + reason_code`（与 V11 baseline 一致）

---

## 3) Leverage（杠杆）

### 3.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 页面信息）

- 杠杆倍数：0.01~100.00

提炼（用于基因/决策/交易所规则对齐）：
- 交易所规则给出的可用范围是 **0.01 ~ 100.00**（连续小数区间）
- 交易所实际接口可能存在 **量化/取整/步进（step）** 约束（例如 0.01 步进、或不同 instId 不同规则）；当前粘贴材料未给出明确条款
- 因此任何“基因杠杆偏好”必须显式声明：
  - **基因域**（例如 log10/ln 表示）与
  - **交易所可用域**（0.01~100.00）之间的映射规则，以及
  - **量化规则来源**（官方条款或 set-leverage 真值回执/报错回执）

### 3.2 Code checkpoints

- Quant（V11）当前实现是否存在“杠杆偏好→交易所设置→真值落盘”的链路：
  - **Decision 输出**：`decision_trace.jsonl` 是否写入 `leverage_target`
  - **Trader 输入**：`order_attempts.jsonl` / `okx_api_calls.jsonl` 是否写入 `leverage_target`
  - **交易所真值**：是否存在 set-leverage 调用证据（okx_api_calls endpoint）或 positions 真值可回查当前杠杆
- 若当前未实现 set-leverage：必须明确写入 `leverage_applied=null + reason_code`（不能沉默）

- 建议（v0）：
  - 基因保存 `lever_gene_log10`（例：范围 \([-2, 2]\)）
  - 交易前派生 `leverage_target`：`raw = 10 ** lever_gene_log10` → clamp 到 \([0.01, 100.00]\)
  - `quantize(raw)` 的规则若未知：必须 NOT_MEASURABLE 或通过 set-leverage 的回执/报错来确定（并把回执落盘）

---

## 4) Order Types & Params（下单类型与参数）

### 4.1 Quoted Rules（verbatim）

（等待粘贴）

### 4.2 Code checkpoints

（等待提取）

---

## 5) Min Size / Lot / Tick Size（最小下单量/合约面值/价格精度）

### 5.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 页面信息）

- 合约面值：0.01 BTC
- 价格精度：0.1

### 5.2 Code checkpoints

- 合约面值（ctVal）对 `sz`（合约张数）与“币本位数量（BTC）”之间的换算：
  - 若 `ctVal = 0.01 BTC`，则 `1 contract == 0.01 BTC`
  - Quant 内部若以 BTC 作为最小下单量约束（例如 `min_order_size_btc=0.01`），则在下单到 OKX 的 `sz` 应至少为 `1`
  - 核对点：`prometheus/v11/connectors/okx_native_writer.py` 的 size 约束/下单 payload `sz`
- 价格精度（tick size）= 0.1：
  - 限价单 `px` 必须为 0.1 的整数倍；若使用市价单则不应填 `px`（或按 OKX 要求）
  - 核对点：`prometheus/v11/connectors/okx_native_writer.py` 的 `px` 构造与校验逻辑

---

## 6) Position Side & Offset（持仓方向/开平逻辑）

### 6.1 Quoted Rules（verbatim）

（等待粘贴）

### 6.2 Code checkpoints

（等待提取）

---

## 7) Fees / Funding（手续费/资金费率）

### 7.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 页面信息）

- 资金费率结算时间：每 8 小时结算一次

来源：用户粘贴（OKX 费率等级信息）

- 用户等级：普通用户
- 资产量（USD）< 100,000 或近 30 天交易量（USD）< 10,000,000
- 挂单成交手续费：0.0200%
- 吃单成交手续费：0.0500%
- 24 小时提币额度（USD）：10,000,000

来源：用户粘贴（OKX 产品文档节选：永续资金费规则介绍；发布 2020-12-21，更新 2025-11-17）

机制：
- 资金费用机制促使永续合约价格向指数价格收敛
- 资金费率为正：多仓支付给空仓；为负：空仓支付给多仓；平台不收服务费

结算时间：
- 一般：每天 8:00、16:00、24:00（UTC+8），每 8 小时收付一次
- 部分合约可能为 1/2/4 小时
- 毫秒级收取，不中断交易；核算可能持续约 1 分钟
- 核算前平仓则不收付；下线前核算则作废
- 收付时间可能根据市场情况实时调整

资金费率计算：
- 资金费率 = clamp [平均溢价指数 + clamp(利率 – 平均溢价指数, 0.05%, -0.05%), 上限, 下限]
- 利率 = 0.03% / (24 / 结算周期)
  - 例：BTCUSDT 永续，结算周期 8h ⇒ 利率 0.01%
- 溢价指数 = [max(0, 深度加权买价 - 指数价格) – max(0, 指数价格 – 深度加权卖价)] / 指数价格
- 平均溢价指数：过去一个结算周期到当前的溢价指数加权平均
- 深度加权买(卖)价：
  - 深度加权买(卖)价 = 深度加权金额 / 满足深度加权金额所需交易币数量
  - 深度加权金额 = 200 × 该合约最高杠杆倍数
- 资金费率每分钟计算；收付时使用最近时刻资金费率（例：16:00 使用 15:59）

资金费用计算：
- 资金费用 = 持仓仓位价值 × 资金费率
- U 本位合约：持仓仓位价值 = 合约张数 × 合约面值 × 合约乘数 × 标记价格
  - 例：10 张 BTCUSDT 永续多仓，mark=60,000，面值=0.01 BTC，乘数=1 ⇒ 价值=6,000 USDT；资金费=6,000×0.1%=6 USDT
- 币本位合约：持仓仓位价值 = 合约张数 × 合约面值 × 合约乘数 / 标记价格

资金费用收付方式：
- 平台收取资金费：全额收取；可能触发减仓或强平
  - 逐仓：从逐仓仓位保证金中收取；收取时不撤单
  - 全仓（单币种/跨币种/组合）：从全仓账户币种权益中收取；收取时不撤单
- 平台支付资金费：全额支付
  - 逐仓：支付到逐仓仓位保证金
  - 全仓：支付到全仓账户币种权益

### 7.2 Code checkpoints

- 资金费率结算周期（8h）是否需要进入：
  - 真值落盘（funding / bills 相关）与时间窗选择（auditor 的 bills-history/bills-archive）
  - 代谢/成本分析（Step92）后续对齐时是否使用该周期作为解释维度
- 目前 First Flight 的最低要求：若发生费用/资金费率相关账单，必须能在 `bills.jsonl` 真值落盘并可 join

- 手续费（maker/taker）等级信息的代码核对点（truth-first）：
  - **不允许**把费率表当作执行世界真值来源（execution_world 真值必须来自交易所 bills/fills/orders JSON）
  - 允许用途（可选）：用于“期望费用区间”的 sanity check（必须标注为 derived/expectation，不得覆盖 bills 真值）
  - 主要核对点：`bills.jsonl` 中的 fee/feeCcy/execType（或等价字段）是否存在，且能按 `ordId` join 到 fills/orders
  - 若出现“费用不可回查/缺失”：应触发 NOT_MEASURABLE，并进入 Step96 错误篓子（reason_code 建议：`missing_bills_fee_truth`）

- 手续费/资金费不做本地计算（纪律）：
  - 我们不需要在 Quant 内实现交易所费率与资金费计算公式来“复算”真值
  - 最低要求是：能够在 `bills.jsonl`（或等价账单真值）中看到费用/资金费的真实扣/返，并可按 `ordId`/时间窗 join
  - 若只存在公式推导、却没有 bills 真值：必须判为 NOT_MEASURABLE（不能假装“已覆盖”）

- 资金费（funding）相关的 truth-first 核对点：
  - **真值入口**：资金费最终应体现在交易所账单（bills）真值中（通常为特定类型的 bill/execType），不能用公式“推算”当作真值落盘。
  - **mark price 依赖**：文档公式使用标记价格；若系统做任何解释性计算，必须引用落盘的 markPx（或明确 NOT_MEASURABLE）。
  - **杠杆相关耦合**：深度加权金额 = 200 × 最高杠杆倍数 ⇒ 杠杆上限不是“装饰字段”，会影响溢价指数的定义口径。若系统要对 funding 做解释，必须明确使用的“最高杠杆倍数”来源（instrument rule SSOT）并落盘 provenance。
  - **时间窗风险**：收付可能持续约 1 分钟，且收付时刻可调整 ⇒ auditor/bills 查询时间窗不能假设“整点即结束”，需要一定缓冲（否则可能 paging/coverage 不闭合，必须 NOT_MEASURABLE）。
  - **入篓要求**：若 bills 真值无法证明（缺失/权限/分页不闭合），必须写入 Step96（classification=TRUTH_PAGING_INCOMPLETE 或 TRUTH_MISSING_SNAPSHOT，按实际原因）。

---

## 8) Demo vs Live Differences（模拟盘 vs 实盘差异）

### 8.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 产品文档节选：模拟盘交易）

模拟盘交易说明：
- 目前可以进行 API 的模拟盘交易；部分功能不支持（如提币、充值、申购赎回等）
- 模拟盘的账户与欧易的账户互通；若已有欧易账户可直接登录
- 模拟盘 API 交易需要在模拟盘上创建 APIKey：
  - 登录欧易账户 → 交易 → 模拟交易 → 个人中心 → 创建模拟盘 APIKey → 开始模拟交易

### 8.2 Code checkpoints

- **Demo/Live 模式必须显式、可审计**：
  - `run_manifest.json` 必须能明确区分 demo 与 live（例如 `mode=okx_demo_api`）
  - demo 的关键差异（如功能不可用）不得“沉默失败”，必须进入 Step96 错误篓子
- **APIKey 分离纪律**：
  - demo key 与 live key 必须分离管理；禁止在证据中混淆（至少 env 名称/落盘字段要清晰）

---

## 9) API Endpoints & Required Headers（接口与必要头）

### 9.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 产品文档节选：模拟盘交易）

模拟盘 API 交易地址：
- REST：`https://www.okx.com`
- WebSocket 公共频道：`wss://wspap.okx.com:8443/ws/v5/public`
- WebSocket 私有频道：`wss://wspap.okx.com:8443/ws/v5/private`
- WebSocket 业务频道：`wss://wspap.okx.com:8443/ws/v5/business`

注意：模拟盘请求 header 需要添加：`x-simulated-trading: 1`

交易时效性（REST/WS 下单/改单类接口）：
- 如果请求中包含 `expTime`（Unix 时间戳毫秒），当服务器当前系统时间超过 expTime，则该请求不会被处理
- 目前支持的接口包括：
  - 下单 / 批量下单
  - 修改订单 / 批量修改订单
  - 信号交易的 POST / 下单

返回数据规则：
- 当返回数据中有 `code` 且没有 `sCode` 字段时：`code`/`msg` 代表请求结果或者报错原因
- 当返回中有 `sCode` 字段时：代表请求结果或者报错原因的是 `sCode`/`sMsg`，而不是 `code`/`msg`

instFamily 和 uly 参数说明（以 BTC 合约为例）：
- uly 是指数（如：BTC-USD），与盈亏结算和保证金币种（settleCcy）存在一对多关系
- instFamily 是交易品种（如：BTC-USD_UM），与 settleCcy 一一对应
- 对应关系表（节选）：
  - USDT 本位合约：uly=BTC-USDT，instFamily=BTC-USDT，settleCcy=USDT，永续 instId=BTC-USDT-SWAP
  - USDC 本位合约：uly=BTC-USDC，instFamily=BTC-USDC，settleCcy=USDC，永续 instId=BTC-USDC-SWAP
  - USDⓈ 本位合约：uly=BTC-USD，instFamily=BTC-USD_UM，settleCcy=USDⓈ，永续 instId=BTC-USD_UM-SWAP
  - 币本位合约：uly=BTC-USD，instFamily=BTC-USD，settleCcy=BTC，永续 instId=BTC-USD-SWAP
注：
- USDⓈ 代表 USD 以及多种 USD 稳定币（如 USD/USDC/USDG）
- 盈亏结算和保证金币种（settleCcy）来自“获取交易产品基础信息（私有）”接口返回字段

### 9.2 Code checkpoints

- **demo 必要头（硬要求）**：
  - OKX demo 请求必须带 `x-simulated-trading: 1`
  - 核对点（Quant）：
    - `prometheus/v11/connectors/okx_native_writer.py`：所有 write-path REST 请求是否统一加该头
    - `prometheus/v11/auditor/exchange_auditor.py`：read-only 请求是否也需要该头（以 OKX 要求为准；若需要必须一致）
    - `tools/run_v11_auditor.py`：同上（若由 runner 发起 read-only）
- **返回码解析纪律**：
  - 若响应包含 `sCode`，系统必须以 `sCode/sMsg` 作为“结果/错误原因”的真值字段落盘
  - 不得只记录 HTTP status 或只记录 `code/msg`
- **instId/instFamily/uly/settleCcy 的 SSOT 绑定**：
  - run_manifest 中的 `inst_id` 必须能明确对应 settleCcy（你当前是 USDT 本位：`BTC-USDT-SWAP`）
  - 若允许传入 instFamily/uly，必须落盘其来源与最终 resolved instId（derived 也要可审计）
- **expTime（交易时效性阈值）**：
  - 如系统要控制“延迟/时效风险”，应支持设置 `expTime` 并落盘（否则必须 NOT_MEASURABLE）
  - Step95（延迟证据）落地时，expTime 将作为外部阈值输入的一部分

---

## 10) Known Pitfalls / Error Codes（常见坑/错误码）

### 10.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 产品文档节选：交易所下单规则/交易限制/限速）

交易所层面的下单规则（挂单数限制）：
- 未成交订单（包括 post only、limit 和处理中的 taker 单）的最大挂单数：4,000 个
- 单个交易产品未成交订单最大挂单数：500 个（计入 500 限制的类型包括：Limit/Market/Post only/FOK/IOC/optimal limit IOC/TP/SL，以及各类策略触发的限价/市价委托等）
- 价差订单最大挂单数：所有价差订单挂单合计 500 个
- 策略委托订单最大挂单数：
  - TP/SL：100 个（每个 Instrument ID）
  - Trigger：500 个
  - Trailing stop：50 个
  - Iceberg：100 个
  - TWAP：20 个
- 网格策略最大个数：
  - 现货网格：100 个
  - 合约网格：100 个

交易限制规则（taker 匹配 maker 数量上限）：
- 当 taker 订单匹配的 maker 订单数量超过最大限制 1000 笔时，taker 订单将被取消
- 限价单：仅成交与 1000 笔 maker 订单相对应的部分，并取消剩余
- FOK：订单将直接被取消

限速（Rate limit）：
- 请求因限速被拒绝时，系统返回错误码 `50011`
- WebSocket 登录和订阅限速基于连接
- 公共未经身份验证的 REST 限速基于 IP 地址
- 私有 REST 限速基于 User ID（子账户具有单独 User ID）
- WebSocket 订单管理限速基于 User ID（子账户具有单独 User ID）
- 交易相关 API（下单/取消/修改）：
  - 限速在 REST 和 WebSocket 通道之间共享
  - 下单/修改/取消的限速相互独立
  - 限速在 Instrument ID 级别定义（期权除外）
  - 批量接口与单接口限速独立；但当批量接口仅发送一个订单时，该订单将被视为单订单并采用单订单限速

子账户限速（新增/修改计数）：
- 子账户维度：每 2 秒最多允许 1000 个订单相关请求（仅新订单及修改订单计入）
- 批量请求包含多个订单时，每个订单将被单独计数
- 超过限制返回 `50061`

### 10.2 Code checkpoints

- **挂单上限/策略单限制必须可见**：
  - 一旦触发挂单上限（4000/500/策略单限制），必须写入 Step96 错误篓子（不能只在 stdout 里打印）
- **1000 maker 上限是“交易所自动拆分/部分成交”核心触发条件**：
  - 若发生“部分成交 + 取消剩余”，必须能在 `orders_history.jsonl`/`fills.jsonl`/`bills.jsonl` 真值中被完整覆盖并可 join
  - 若 paging/覆盖不闭合导致无法证明完整成交集，必须 NOT_MEASURABLE 并入 Step96（例如 TRUTH_PAGING_INCOMPLETE）
- **限速错误码必须结构化落盘**：
  - `50011`（接口限速）与 `50061`（子账户 2 秒 1000 单限制）必须被识别并落盘（OKX 结构化 code/sCode + msg/sMsg）
  - 不得只记录 HTTP status（否则审计时无法复原真实拒绝原因）
- **批量接口“按单计数”**：
  - 批量下单/改单在证据中必须逐单落盘（每个订单一个 attempt / 一个 api-call 记录），否则无法复核“按单计数”的限速行为

- **查询限制/交易限制是生态围栏（必须如实记录）**：
  - 限速与分页上限是事件驱动设计的外部约束，不是实现细节
  - 要求：
    - auditor/runner 把每次分页请求写入 `paging_traces.jsonl`，并在 summary 给出 paging closure 状态
    - 一旦触发限速（50011/50061）或 paging 不闭合，必须进入 Step96（如 TRUTH_PAGING_INCOMPLETE）
    - 任何 NOT_MEASURABLE 必须区分：是 **交易所拒绝** 还是 **我们本地没查全**

---

## 11) PnL / Close Profit Formula（平仓收益公式）

### 11.1 Quoted Rules（verbatim）

来源：用户粘贴（OKX 页面信息）

- 平仓收益：
  - 多仓：数量 (币) × 平仓均价 – 数量 (币) × 开仓均价
  - 空仓：数量 (币) × 开仓均价 – 数量 (币) × 平仓均价

### 11.2 Code checkpoints

- 该公式使用的“数量(币)”是 **BTC 数量**，不是合约张数 `sz`：
  - `qty_btc = sz_contracts * ctVal_btc_per_contract`（此处 ctVal=0.01 BTC）
- 若 Quant 在 execution_world 中计算/展示任何 PnL（哪怕是 debug），必须：
  - 明确使用 `qty_btc` 还是 `sz`
  - 并且 PnL 的开平价来自交易所真值（fills/bills/positions），不得用内部模拟价冒充
- 建议核对点：
  - 若已有 PnL 计算：定位对应模块（通常在 ledger/metabolism/report）
  - 若暂未实现：至少在 SSOT 层冻结“PnL 不得来自内部模拟”的纪律（与 V11 baseline 一致）

## Change Log（追加区）

- 2025-12-31: 创建文件，用于逐段粘贴 OKX BTC/USDT 永续合约官方规则并对照 Quant 实现。
- 2025-12-31: 追加用户粘贴段落：合约面值/价格精度/杠杆范围/资金费率结算/PnL 公式，并生成对应代码核对点。


