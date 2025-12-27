# V10 方法论工程验收标准（审查者版本）

> 目的：把“测量复杂系统的方法”从哲学叙事，落到**可复现、可审计、可证伪**的工程验收协议。  
> 立场：不预设“涌现应当长成什么样”。只裁决：系统是否确实利用了市场时间结构，并且结论在对照/消融下成立。

---

## 0. 总目标（裁决口径：以量化交易为实例的工程审查）

**方法有效** ≈ 在严格的可复现与可审计前提下：

- 在**真实时间结构**数据（A组）上，持续出现“利用时间结构”的证据；
- 在**零假设对照**（B组，破坏时间结构但保持单步波动分布）上，该证据显著变弱或消失；
- 在**消融/扰动**（C组）下，该证据按预期退化；
- 全流程不存在“口径错误/数值爆炸/账本不闭合”这类工程幻觉。

> 说明：我们用“量化交易”作为实例来检验演化方法论，因此裁判尺度必须来自交易世界的硬约束（净值、回撤、摩擦、强平、可持续性、可对账）。  
> 这里的“有效”不是“证明真理”，而是获得工程意义上的可信度增量。

---

## 1. Gate 0：工程与会计完整性（硬门槛）

任一项失败，直接判定本轮实验**无效**（先修尺子，再谈结论）。

- **G0.1 可复现**
  - 同一 commit + 同一 config + 同一 seed + 同一数据窗口 → 关键统计一致（允许浮点微差，但需在阈值内）。

- **G0.2 可审计（落盘，不只终端）**
  - 每次运行输出的 JSON/报告中必须包含：
    - 配置（阈值、agent数、ticks、seed列表、数据文件与时间窗）
    - 资金三元组：`allocated_capital / system_reserve / current_total`
    - 下葬与崩溃事件（时间戳/计数/原因）
    - 审计声明（mode、资金模型语义、下葬契约版本等）

- **G0.3 数值健康**
  - 不允许出现 `NaN/Inf/溢出`。出现即判该 run 作废，并必须定位原因。
  - **对照组构造不物理**导致溢出，也属于失败（对照无效）。

- **G0.4 统计口径正确**
  - 盈利/ROI等统计必须同时覆盖：
    - **全体（含死亡）**：例如 `profitable_agents_all`
    - **存活子集**：例如 `profitable_agents_alive`
  - 禁止混淆（例如把 `alive` 当分母导致“存活=盈利”的假象）。

- **G0.5 对照组物理合理**
  - 零假设必须破坏时间结构，但不能引入“现实中不可能的巨大跳变频率”。

- **G0.6 禁止“隐含预设策略”（Prior leakage audit）**
  - 目的：避免“尺子里塞了策略”，把后续所有 A/B 裁决污染掉。
  - 最低要求（任一失败 → 本轮实验无效）：
    - **特征侧**：不得直接硬编码典型交易指标/策略公式（如 RSI/MACD/均线交叉/专用微结构识别器）。允许“原始观测”与“物理可解释的变换”（归一化、tanh压缩、EMA平滑）——但必须在文档中声明。
    - **表达/执行侧**：不得用硬阈值把某种交易风格写死（除“生态/物理规则”外）；若存在硬阈值，必须列出清单并在 Gate 3 做消融验证。
    - **死基因/冗余维度**：如果基因包含不再生效的维度（例如阈值被路线升级后废弃），必须显式标注，否则“基因维度最小化”判定失败。
    - **隐含围栏审计（强制）**：防止“默认值/回退/硬分支/裁剪”悄悄改变行为空间，导致异常收敛。
      - 必须维护围栏清单（Fence Inventory）：列出所有会影响交易行为的 gate（含 ops 层）。
      - 必须落盘触发率遥测（Gating Telemetry）：每轮运行输出 `fence_id -> trigger_count/block_count`，并在高触发率时显式解释（生态 vs 人为）。
      - **原则4绑定**：围栏审计被用作对“演化是否遵从自然选择”的硬核检验（避免人为 gate 先把行为空间剪成策略）。
      - 参考协议：`docs/v10/V10_HIDDEN_FENCE_AUDIT_PROTOCOL_20251222.md`

- **G0.7 Core 变更触发“裁决失效”与回归门槛（强制）**
  - 目的：确保“裁决”对应同一个世界版本；避免改了世界规则却沿用旧结论。
  - 适用范围：任何 `prometheus/v10/core/` 的变更（包括特征、决策、资金/清算、生命周期、数值处理等）。
  - 强制规则：
    - 一旦 core 发生变更：此前所有裁决记录视为**不再可直接引用**，必须重做**最小回归裁决**。
    - **最小回归集合**（建议工程线）：至少重跑 Gate 1（A vs B2）；若变更触及窗口/稳健性或归因链，则必须相应重跑 Gate 2/3（窗口迁移、消融、v2/v3审计）。
  - 审计要求（必须落盘）：
    - 每次运行必须在 `run_manifest/summary.meta` 写入：`git_commit`（世界版本）+ `config_hash` + `python_version` + `docker_image_digest`（若适用）。

- **G0.8 强耦合外部系统介入 → 测量失效（强制，V8 Principle 0 对齐）**
  - 目的：避免目标系统被其它复杂系统以强耦合方式持续介入（改变规则、边界条件、观测通道），从而使“测量”退化为不可裁决的混合过程。
  - 定义（触发即失效）：
    - **强耦合介入**：任一外部系统（含人工操作/其它机器人/外部风控或执行代理）在 run 期间反复或持续地改变以下任一类要素：
      - 世界规则：账户模式/保证金参数/杠杆/交易权限等（导致“物理规则”漂移）
      - 边界条件：资金进出、持仓被外力开平、挂单被外力撤改（导致“系统边界”漂移）
      - 观测通道：数据源/字段语义/采样机制被替换或扰动（导致“观测口径”漂移）
  - 强制裁决语义：
    - 发生强耦合介入的 run 必须标记为 **Invalid / Not Measurable**（不得用于 Gate 1–3 的 A/B 裁决与机制归因）。
    - 若仅发生一次性、可量化、可比较的介入（例如明确记录的资金注入/参数切换），可降级为 **Inconclusive**，但必须给出证据与影响范围。
  - 最低证据要求（必须落盘）：
    - `run_manifest` 必须声明：本次 run 的“边界条件承诺”（例如账户独占/是否允许人工干预/是否允许其它系统共用同账户）。
    - 若检测或承认发生外部介入：必须追加落盘一条结构化事件（文件名可自定，但必须 append-only），包含 `ts_utc`、`type`、`what_changed`、`who/where`（可脱敏）、以及 `evidence_refs` 指向对应的交易所快照/日志。
  - 参考（概念来源）：`docs/v8/V8.md`（Principle 0: Disturbance is Measurable）

---

## 2. Gate 1：非随机性（必须有对照）

**核心问题**：系统的表现差异是否来自“时间结构”，而不是噪声/偶然。

### 2.1 实验组与对照组（最低配置）

- **A组（真实时间结构）**：真实历史数据原序列。
- **B组（零假设）**：破坏时间顺序，但保持单步波动分布近似真实。
  - 推荐：**打乱收益率（return/log-return）序列后重建价格**，而不是直接随机置换价格。

> 若B组跑不通或数值爆炸：对照无效，Gate 1 不能裁决。

### 2.2 主指标（Primary endpoints，已锁定）

为避免“挑好看的指标”，必须**预先固定**主指标（建议选2个，最多3个）。本项目现阶段锁定为2个：

- **Primary #1：`system_roi`（基于`current_total`）**
  - 定义：`system_roi = current_total / initial_total_capital - 1`
  - 口径：`current_total = allocated_capital + system_reserve`
- **Primary #2：`extinction_rate`（灭绝比例）**
  - 定义：`alive_agents == 0` 的 run 占比

> 说明：`profitable_agents_all` 对结构更敏感，但容易被“刷微利/阈值抖动”误导，因此降级为次指标（Secondary）。

### 2.2.1 次指标（Secondary endpoints，建议保留但不作为通过/失败唯一依据）

- **`profitable_agents_all`**：全体盈利人数/比例（含死亡）
- **回撤类**：`max_drawdown`（至少给分位数或置信区间）
- **换手/交易摩擦代理**：`total_trades`、（如可得）`avg_M7 / avg_M9`
- **存活结构**：`avg_alive_agents`、`avg_total_agents`（总谱系规模）

### 2.3 统计判定（建议）

对每个主指标，比较 A vs B：

- 连续指标（如`system_roi`、盈利人数）：推荐 **Mann–Whitney U**（非参数，稳健）。
- 比例指标（如灭绝率）：推荐 **费舍尔精确检验**或比例检验。

**通过条件**（工程审查线，非真理）：

- 统计显著：`p < 0.05`（多指标需多重校正或只对主指标检验）
- 同时具备**最小效应量**（例如 `system_roi` 差异 ≥ 2pp；或盈利人数差异 ≥ 50%）

---

## 3. Gate 2：稳健性（可重复、可迁移、不靠偶然）

- **G2.1 seed规模**
  - 建议 `n_seeds >= 30`（至少30；更强建议50/100用于稳定性评估）。

- **G2.2 稳定性呈现**
  - 不只给均值：必须给中位数/分位数/置信区间，避免被极端值带偏。

- **G2.3 时间窗迁移**
  - 至少两个不重叠窗口（或两种市场状态窗口）中，A>B结论方向一致。

- **G2.4 避免信息泄漏**
  - 禁止使用未来信息（包括归一化、滚动窗口实现错误等）。

- **G2.5 赢家口径固定（B阶段v2硬化）**
  - 目的：避免“各组各自挑分位数”导致口径漂移，让“赢家/尾部”可比较、可复核。
  - 最低要求（必须同时做两套赢家阈值）：
    - **绝对阈值**：`roi_lifetime >= +5%`（可替换为+2%/+10%，但必须预先声明并固定）
    - **锚定阈值（A锚定）**：用 A 组阈值（优先 `q90_A`）作为同一把尺子，应用到 A 与 B（同一阈值）
  - **退化处理（强制）**：若 `q90_A <= 0`，不得用 `roi>=q90_A`（退化为近似 `roi>=0`）
    - 优先改用：`q95_A`
    - 次选：`q90_A_pos`（在 `roi_lifetime>0` 子集中取0.9分位数；样本数≥50）
    - 兜底：绝对阈值 `+5%`
  - 输出要求：
    - `q90_A`、最终 anchor 方法与阈值数值（method/value）
    - `winner_rate_abs` 与 `winner_rate_anchor`（A/B）
  - 参考协议：`docs/v10/V10_B_STAGE_V2_PROTOCOL_WINNER_DEFINITION_AND_SIGN_CONSISTENCY.md`

---

## 4. Gate 3：因果归因（消融/扰动）

**目的**：证明你测到的差异来自你声称的观测通道，而不是隐藏漏洞。

- **G3.1 观测通道消融（ablation）**
  - 例：将某一类输入置空（如 `M={}` 或 `C={}`）。
  - 预期：A>B 的主指标差异应显著减弱或消失。

- **G3.2 小扰动敏感性**
  - 对关键阈值做小范围扰动（例如 ±20%），结论不应完全翻盘。

- **G3.3 Prior leakage 消融（强制）**
  - 目的：证明你看到的差异不是“隐含预设”带来的假阳性。
  - 最低两组（建议都做 A vs B）：
    - **M消融**：`M={}`（或全部置零） → 若 A>B 信号主要靠 M 通道，应显著退化。
    - **C消融**：`C={}`（或全部置零） → 若 A>B 信号主要靠群体态，应显著退化。
  - 输出：把“消融前后”主指标差异（均值/中位数/分位数 + p值 + 效应量）写入裁决摘要。

- **G3.4 IN/OUT 同向性审计（B阶段v2强制）**
  - 目的：把“Top权重列表”推进到更像机制的证据：同一输入通道在 OUT/IN 两套网络里方向一致。
  - 方法：在关键人群（至少：`alive`、`winner_abs`、`winner_anchor`）上：
    - 按 |Cohen’s d| 选 Top-N 权重（建议 N≥50）
    - 对 W1 权重按 `(feature_idx, hidden_idx)` 将 OUT 与 IN 配对
    - 检查 `sign(delta_OUT) == sign(delta_IN)` 的比例
  - 通过条件（建议工程线）：`consistency_rate >= 0.8` 且 `n_pairs` 充分（例如 ≥ 20）
  - 输出必须落盘并写入裁决摘要（含 pairs_top 示例）

- **G3.5 赢家人群分层稳定性（B阶段v3）**
  - 目的：验证“赢家机制”在不同强度层（交易数/胜率/信号强度）下仍稳定，而非单点偶然。
  - 方法：在 **锚定赢家**（anchor winner）集合内，对以下维度做分层（推荐三分位）：
    - `total_trades`
    - `win_rate`
    - `last_signal`
  - **v3.1（强制兜底：分箱退化时启用）**
    - 触发条件：若某个分层维度出现分位点退化（切点重复/空箱/绝大多数样本集中导致分箱无效），不得硬解释为“机制不存在”。
    - 处理方式：必须启用更稳健的分箱尺子之一，并在裁决中落盘声明所用方法与阈值：
      - `log1p(x)` 后分箱，或
      - 固定阈值分箱（由“样本下限”驱动选择阈值，而不是拍脑袋）
    - 目标：让该分层维度在每个有效箱内满足 Gate 3.5 的样本下限要求（见下）。
  - 每个分箱要求：`nA>=30` 且 `nB>=30` 才纳入结论；样本不足/退化分箱必须显式标注为“无效证据”，不得硬解释。
  - 通过条件（建议工程线）：在有效分箱中，同向性（G3.4）保持高一致（例如 ≥0.8），且关键通道重复出现（允许少量波动，但不得完全翻盘）。
  - 输出：给出每个分箱的样本量、同向性、Top通道摘要。

---

## 5. Gate 4：走向虚拟盘/实盘的最低可用门槛（非盈利门槛）

通过 Gate 1–3 之后，才讨论是否进入虚拟盘/实盘工程。

- **G4.1 运行稳定**
  - 无刷屏、无溢出、无长期无意义循环（崩溃后应停止或只打印一次）。

- **G4.2 产物可管理**
  - 所有关键指标落盘、可聚合、可复核（不靠grep挖日志）。

- **G4.3 执行环境指纹测试（若上OKX demo/live）**
  - 以极小额订单测量：滑点分布、部分成交比例、延迟分布、fee一致性，并落盘。

- **G4.3b 交易执行模块合同（Execution Engine，强制，demo/live）**
  - 目的：防止“执行逻辑散落主程序导致语义污染/审计断裂”，确保真实执行闭环可复核。
  - 强制规则（任一失败即 Gate 4 Fail）：
    - okx_demo_api / okx_live 下 **禁止伪造交易**：下单失败不得 simulated fill/假 ack/假 fill。
    - `fill_observed` 只能来自交易所可回查证据（order_status/fills），不得用本地假设替代。
    - public endpoint（instruments/ticker）必须用无鉴权方式调用，且失败也必须证据化（HTTP status + response 摘要）。
    - 必须提供 ops-only 最小 PROBE 证据包：instruments→选instId(live)→下单→回查→撤单→回查→SHA256。
    - **唯一交易入口（hard）**：execution_world 下，runner/测试程序 **禁止绕过代理交易员（BrokerTrader）** 直接调用 connector 下单/撤单/回查；所有订单生命周期必须经过 “执行 + 入册（append-only）” 的统一入口，否则视为审计黑洞 → Gate4 Fail。
  - 参考合同：`docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
  - 入口契约：`docs/v10/V10_BROKER_TRADER_MODULE_CONTRACT_20251226.md`

- **G4.3e 订单确认协议（hard，demo/live）**
  - 目的：解决通信/异步导致的不一致，保证“每一笔交易都能被交易所 JSON 回查复现”，避免内部伪账/伪成交。
  - 协议：`docs/v10/V10_ORDER_CONFIRMATION_PROTOCOL_20251226.md`
  - 最小 PASS（适用于 Step1/Probe）：
    - 对所有 `ack_received=true` 的订单，必须完成 **P2 Order Status**：可回查到终态（filled/canceled 等），且查询证据 append-only 落盘。
  - NOT_MEASURABLE（必须诚实标注，不得硬算）：
    - 任何关于 `fillSz/avgPx/fee/pnl/balance change` 的结论，若未完成对应层级（P3 fills / P4 bills），则一律 NOT_MEASURABLE。
    - 任一分页端点（orders-history/fills/bills）无法证明“已完整拉取”（例如 hasMore 未清空/游标未走完），相关结论一律 NOT_MEASURABLE。
  - FAIL（任一触发即 Gate4 Fail）：
    - 无交易所 JSON 证据却写入“成交/费用/仓位变化”等真值（内部伪造）。
    - 出现 ack 后长期无法完成 P2（或需 P3/P4 的断言）但仍继续发单（未执行 execution_freeze）。

- **G4.3f Run-end 只读审计（evidence-only，用于锁版前审查入册漏洞）**
  - 目的：在不干预系统的前提下，用交易所只读查询对 BrokerTrader 的入册完整性做一次交叉核验，暴露“漏入册/分页不完整/关联断裂”等漏洞。
  - 契约：
    - `docs/v10/V10_EXCHANGE_AUDITOR_MODULE_CONTRACT_20251226.md`
    - `docs/v10/V10_BROKERTRADER_REGISTRY_AUDIT_CHECKLIST_20251226.md`
  - 最小要求：
    - 每个 run 在结束时产出：`auditor_report.json` 与 `auditor_discrepancies.jsonl`
    - 上述审计产物必须被纳入 `FILELIST.ls.txt` 与 `SHA256SUMS.txt`（避免形成新的证据盲区）

> Note（本版本编排）：生命周期循环的默认收尾可以先不引入审计模块“参与编排”，但审计模块仍可作为独立工具在 run 结束后运行并落盘审计结果。若启用 G4.3f，则以上最小要求生效。

- **G4.3c 执行世界关键参数“传递与关联”审计（强制，demo/live）**
  - 目的：明确验收是否覆盖 **资金真值（exchange equity）**、**持仓/数量**、**订单ID关联** 三条证据链，避免“跑起来了但关键参数没落盘/不可回查”。
  - 适用范围：`okx_demo_api`、`okx_live`（`offline/okx_demo_sim` 必须写 `null + reason`）。
  - **资金参数（必须落盘且可复核）**：
    - `bootstrap_capital_value/bootstrap_capital_currency/bootstrap_capital_field` 必须出现在 `run_manifest.json`
    - preflight AFTER 快照为唯一启动资金来源（见 G4.3a 合同）
    - `capital_reconciliation_events.jsonl` 必须存在，且每条包含：`exchange_equity`、`allocated_capital`、`system_reserve_before/after`、`delta`、`action_taken`
  - **持仓参数（必须落盘“数量口径”）**：
    - preflight 必须落盘：`open_orders_after_count == 0` 与 `positions_after_count == 0`（或 `skipped + reason`；demo 若跳过必须诚实标注）
    - 若发生过任何真实订单 ack（`ack_received=true`），必须提供一种可审计的持仓证据路径：
      - A) 交易所 positions 快照（推荐），或
      - B) 基于 fills/order_status 的重建证据（见 G4.5 与 C0.7/C0.8/C0.9 类证据链）
  - **订单ID与可回查关联（必须）**：
    - 每个被认为 ack 的订单，必须至少具备：`clOrdId`（本地关联键）与 `ordId_hash`（脱敏关联键）
    - 必须存在 `order_status_samples.json`（append-only）或等价文件，能用 `clOrdId/ordId_hash` 回指交易所 `state/fillSz`
  - 证据引用：
    - 交易执行模块合同：`docs/v10/V10_EXECUTION_ENGINE_CONTRACT_OKX_DEMO_LIVE.md`
    - 启动前置契约：`docs/v10/V10_STARTUP_PREFLIGHT_AND_BOOTSTRAP_CONTRACT_20251223.md`
    - 对账模块合同：`docs/v10/V10_RECONCILIATION_MODULE_CONTRACT_OKX_EXECUTION_WORLD.md`

- **G4.3d 核心接口冻结（Execution + Reconciliation，强制，demo/live）**
  - 目的：一旦交易与对账验收通过，接口/证据 schema 锁定，避免后续“悄悄改字段/改语义”导致审计链不可比。
  - 强制规则（任一失败即 Gate 4 Fail）：
    - Execution Engine 工件 schema 冻结（见执行合同 §8）
    - Reconciliation 工件 schema 冻结（见对账合同 §5）
    - 允许向后兼容扩展：只允许新增字段；不得删除字段/更改类型/更改语义
    - 任何破坏性变更必须提升 version 并重做 Gate 4 的最小证据包回归

- **G4.3a 启动前置契约（Preflight + Bootstrap）（强制，demo/live）**
  - 目的：避免“系统以为自己空仓/有多少钱，但交易所实际不是”，导致后续证据链污染。
  - 强制顺序：connect check → BEFORE快照 → 撤单 → 平仓（flatten）→ AFTER快照 → 用 `balance_after` 作为启动资金
  - 失败行为：preflight 任一硬门槛失败必须 `aborted/interrupted` 并形成 IEB；禁止进入主循环。
  - 参考合同：`docs/v10/V10_STARTUP_PREFLIGHT_AND_BOOTSTRAP_CONTRACT_20251223.md`

- **G4.4 “生态围栏 ≠ 状态机”隔离原则（强制）**
  - 目的：防止系统在产品化阶段偷偷变成“人为策略”，破坏演化自由度与证据链可比性。
  - 一句话解释（产品化落地）：**阈值可以存在，但只作为“事后标签/审计口径/生死规则/外壳限流”；决策仍必须是 `Genome + Features -> Action`（不允许把阈值掺进决策路径来“指导”交易）。**
  - Design note / 设计注记（不改变规则，只澄清原则）：
    - **English (primary)**: Evolution needs genuine failure. Ecological fences exist to protect the system (capital, infra, audit), not to protect individual Agents from ever dying. Every prevented death by a hard-coded threshold is also a removed learning signal about where old strategies stop working.
    - **中文（辅助）**：演化需要真实的失败。生态围栏的目标是保护系统整体（资金、基础设施、审计链），不是保护单个 Agent 永远不死。每一次被硬阈值挡掉的死亡，都是我们放弃了一次“旧策略在哪里失效”的学习机会。
  - 强制规则：
    - **生态围栏**（如无风险基准/季度淘汰与繁殖门槛/资金守恒与崩溃重启/执行摩擦与资源上限）只能进入：
      - 生命周期层（death/repro/collapse/reboot）
      - 审计层（指标口径、分群标签、告警与回放）
      - 外壳限流层（例如最大频率/最大挂单数/kill switch），但不得改变“基因表达规则”
    - **禁止**把生态阈值直接写进状态机/决策路径（例如“signal>阈值才允许进场/加仓/减仓”这类硬门槛），除非该阈值被明确声明为“世界物理约束”（如交易所规则/保证金/强平）。
  - 审计要求（必须落盘）：
    - 每次运行必须写入 `run_manifest`/`summary.meta`：当期生态围栏配置（rf来源/阈值/执行环境指纹版本/限流参数）。
    - 若发现决策路径依赖新增生态阈值：Gate 4 **Fail**，必须回退或将其降级为“审计标签/生命周期规则”。

- **G4.5 执行接口对齐审计（CCXT/OKX SDK）（强制）**
  - 目的：防止“基因学到的是接口差异/实现细节”，而非市场结构；保证 V10 的基因表达与特征口径在产品化执行层仍可复核。
  - **关键口径：两个世界不能混裁（强制）**
    - **B阶段（离线实验世界）**：I/M 等特征来自系统内部状态与内部摩擦模型，因此“可得”；消融与A/B2裁决只在该世界内成立。
    - **C阶段（执行接口世界）**：I（positions）与 M（fills/fees/latency）必须从交易所/库返回获取；若 demo 不提供/不可靠，必须 `null + reason` 或标记 `simulated`，并给出 fallback 证据链。**不得因为 demo 缺失而倒推 B 阶段消融结论无效。**
  - **自成交（self-trade / self-cross）风险（强制：先记录，再扩展）**
    - 风险：同一账户下多 Agent/多循环同时交易同一合约时，可能发生“我们自己的买单和卖单互相成交”，导致虚假成交量与手续费损耗，并污染学习/归因。
    - 最低要求（必须落盘）：
      - `run_manifest` 记录：是否支持/启用 STP（Self-Trade Prevention）、是否做执行净额/聚合、以及当前检测能力强弱。
      - raw evidence（如 `m_execution_raw.json`）保留最小字段以支持事后检测（脱敏可）。
    - 说明：此条是执行层“世界物理约束/风险”，属于审计与外壳执行策略，不得渗入 core 决策路径。
  - 强制规则：
    - 必须通过 **统一适配层（adapter）** 接入交易所；业务逻辑不得散落依赖 CCXT/SDK 的原始字段名。
    - 必须在 `run_manifest/summary.meta` 记录：`exchange_lib`（ccxt/okx_sdk）、`exchange_id`（okx）、`env`（demo/live）、`symbol_in_use`（实际使用的symbol）、以及 `connect_check_ok`。
    - **切换执行库（ccxt ↔ okx_sdk）视为世界差异**：需做最小回归验证（至少 Gate 4 的执行指纹与“活着指标”仍可落盘且口径不漂移；必要时回归 Gate 1）。
  - 落盘要求（必须提供“证据包”，脱敏可）：
    - `ccxt_alignment_report.json`（或等价）：字段映射表、缺失字段的降级策略、已知风险点（posSide/tdMode/fee/partial fill等）
    - `ccxt_raw_samples.json`（或等价）：至少包含 ticker/ohlcv/orderbook/positions/balance/order/trade 的原始响应样例（敏感字段置空）
  - 通过条件（建议工程线）：
    - `okx_demo_api` 模式下 `api_calls > 0` 且 `connect_check_ok=true`
    - 对齐证据包存在并被 run_manifest 引用
    - 关键字段缺失时必须 `null + reason`，不得伪装为真实可得

- **G4.6 Incident Runbook + 证据包标准（C2.0）（强制）**
  - 目的：当进入执行接口世界（demo/live）后，任何异常都能做到“先止血、先保全证据、再复盘”，避免临场改 core 造成证据污染与口径漂移。
  - 强制规则：
    - 事故处置阶段只允许 ops/infra 动作（限流、STOP、kill switch），**禁止**修改 `prometheus/v10/core/`
    - 必须能形成最小“Incident Evidence Bundle（IEB）”，并能指回 run_id 与 artifacts
    - 必须把“三维共振”类重大风险信号（趋势 + 摩擦激增 + 群体死亡）作为升级条件写入处置流程（不要求自动化，但要求可审计）
  - 参考协议：`docs/v10/V10_INCIDENT_RUNBOOK_C2_0_20251222.md`

- **G4.7 Gate 4（VPS）：OKX Demo 演化内核（真实下单、无代理、无人工围栏）（强制，demo）**
  - 目的：在 **VPS（Docker）** 环境，用 OKX Demo **真实下单**驱动多 Agent 演化闭环，同时保持“证据优先 + 可审计 + 可复盘”。
  - 背景（执行环境变更）：国内环境难以稳定直连 OKX；依赖代理访问存在被交易所风控与“观测通道漂移”的风险，因此 Gate 4 的执行世界以 VPS 为准。
  - 强制口径（任一失败 → Gate 4 Fail）：
    - **真实下单**：`okx_demo_api` 下任何 order intent 必须走交易所真实下单链路。
    - **禁止伪造交易**：下单失败不得 simulated fill/假 ack/假 fill（与 G4.3b 一致）。
    - **无人工围栏**：不得以“每 N tick 必须下单/必须成交”作为通过门槛，更不得将该类频次约束注入 Agent 决策路径。
      - 允许：生态围栏（STOP/限流/资金守恒）与事后审计标签。
    - **NO_TRADE 证据化**：若运行中无交易发生，必须将 run 明确标注为 `NO_TRADE`（基于落盘证据），该 run 对“成交/手续费闭环”结论视为 **证据不足（Inconclusive）**，但不因“未交易”本身判定失败。
    - **决策链运行证据（强制，observe-only 语义闭环）**：
      - 目的：区分“Agent 主动观望” vs “决策链未运行/观测链断裂”。
      - 强制要求：必须提供 append-only 的 tick 级决策轨迹证据（文件名可不同，但语义等价，如 `decision_trace.jsonl`），至少包含：`ts_utc`、`tick`、`run_id`、`agent_id_hash`（或等价主体标识）、`action`（例如 hold/open/close/none）。
      - 裁决语义：若缺失该证据，则任何 `NO_TRADE` 只能判为“观测到无交易”，但**无法断言**是 Agent 的自主决策（记为 Inconclusive/证据不完备）。
    - **执行世界的模块封装 + 审计 + 锁版（强制）**：
      - 要求：交易所通信模块（Connector）与交易执行模块（ExecutionEngine）必须独立封装，不得散落在测试主程序中。
      - 要求：封装后必须通过 ops-only 的最小 PROBE 证据包验收，验收通过后 **接口/证据 schema 冻结**（只允许向后兼容扩展）。
      - 参考协议：`docs/v10/V10_MODULE_PROBE_AND_INTERFACE_FREEZE_PROTOCOL_20251225.md`
    - **禁止“内部持仓模拟”（强制）**：
      - 在 `okx_demo_api` / `okx_live` 中，core/decision 只能产出 intent，不得直接改写 internal positions/state 来“模拟成交”。
      - 任一 internal positions/state 变化必须能指回交易所可回查证据（order_status/fills/positions truth），否则该 run 判为 **Invalid / Not Measurable**。
  - 参考协议：`docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_VPS.md`（主） / `docs/v10/V10_GATE4_OKX_DEMO_EVOLUTION_MAC.md`（deprecated）
  - **无代理执行规则（硬门槛）**：
    - 若 run 的 OKX 交互依赖不透明代理/VPN 路径，且该路径可能在 run 期间改变或触发风控，则该 run 必须标记为 **Not Measurable**（观测通道漂移，见 G0.8）。
  - **人工筛选/聚类就绪（验收项，偏“证据完备”而非“结论正确”）**：
    - 目的：允许在不破坏原始证据的前提下，对每个 96 ticks 审判窗口做**只读**的死亡/繁殖聚类分析。
    - 强制口径：
      - 必须输出 append-only 的生命周期证据文件（命名可不同，但语义必须等价）：`death_events.jsonl` 与 `birth_events.jsonl`（或等价物）。
      - 每条事件至少包含：`ts_utc`、`tick`、`run_id`、以及可用于聚类的最小字段（例如 ROI/原因/寿命/资本分裂等）；并含可追溯的主体标识（如 `agent_id_hash` / `parent_id_hash` / `child_id_hash`）。
      - 若某 run 在窗口内无死亡/无繁殖：允许 0 事件，但必须在报告中 **证据化为 0**（不得靠口头说明）。
    - 分层裁决（避免“讲故事”）：
      - **行为/生态层聚类（可立即做）**：满足以上 lifecycle 证据 + `decision_trace.jsonl`（或等价物）即可；可聚类的对象是“决策轨迹/死因/ROI窗口/寿命”等。
      - **基因层聚类（必须额外证据）**：若要宣称“按基因簇解释死亡/繁殖差异”，必须在同一 `run_dir/` 提供 `genomes_snapshot.jsonl`（或等价物），并与 `run_id` 绑定、可校验（纳入 `FILELIST.ls.txt` + `SHA256SUMS.txt`）。
        - 最小字段：`ts_utc`、`run_id`、`tick`（建议 1 或 96）、`agent_id_hash`、`genome_hash`。
        - 若缺失：该 run 的“基因层聚类”一律判为 **Inconclusive（证据不完备）**，不得用推测替代。
  - **模拟→API 市场数据切换的高风险缺口（不打断当前 24h，但必须纳入下一轮验收）**：
    - 背景：从离线/模拟市场输入切到 OKX API 实时输入后，最容易出现“市场输入链路断裂/错对齐/静默降级”的隐蔽漏洞，导致出现“静默市场”而非策略真实观望。
    - **D1 market→decision 输入闭环证据（必须补齐）**：
      - 要求：在 `decision_trace.jsonl`（或等价物）里证据化“决策实际使用的市场输入”，至少包含：
        - `inst_id_used`、`source_ts_used`、`mark_price_used`（或 `mid_used`）
        - `market_context_hash`（或 `features_hash`）
        - `policy_version` / `decision_contract_version`
      - 并提供 tick 级市场锚点记录（可嵌入 tick_summary 或单独 `market_observations.jsonl`），用于交叉校验 hash/字段。
    - **D2 静默降级检测（必须补齐）**：
      - 要求：当 API 错误/超时导致使用默认值、缓存值、陈旧值时，必须在决策证据中显式标注：
        - `reason_code` / `input_quality_flags`（例如 stale/default/degraded）
      - 禁止“吞异常后静默用 0/上次值”却不留证据。

---

## 6. 最终裁决输出格式（强制）

每轮验收必须输出“一页裁决摘要”（Markdown或JSON均可）：

- Gate 0–4：逐项 **Pass/Fail**（Fail必须给原因与复核路径/命令）
- A vs B：主指标的均值/中位数/分位数 + p值 + 效应量
- 结论：**通过 / 不通过 / 证据不足**
- 下一步：只允许提出**最小改动**（优先补证据，不优先改世界规则）

---

## 7. 待确认项（剩余需锁定）

- **对照组B的生成方式与参数**：默认采用“打乱log-return重建价格”的方案。
- **最小效应量阈值**：例如system_roi差异≥2pp、盈利人数差异≥50%等。


