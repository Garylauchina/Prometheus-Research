# Module Registry（核心模块速查）

面向“2分钟找对入口”。列出职责、关键类/方法、初始化/依赖、典型调用。

## 核心角色
- **Supervisor / Moirai**：监督/生命周期管理，创世、执行、淘汰、进化入口。  
  - 类：`prometheus.core.supervisor.Supervisor`，`prometheus.core.moirai.Moirai`
  - 关键方法：`run_cycle()`（监督+执行），`_genesis_create_agents()`（创世），`_lachesis_execute()`（执行下单），`_atropos_eliminate()`（淘汰）
  - 依赖：BulletinBoard，DiversityMonitor，EvolutionManagerV5，Ledger 系统
- **EvolutionManagerV5**：繁殖、变异、移民、家族多样性保护。  
  - 类：`prometheus.core.evolution_manager_v5.EvolutionManagerV5`
  - 关键方法：`evolve_population()`，`_clotho_weave_child()`，`inject_immigrants()`，`maybe_inject_immigrants()`（先知/战略层根据多样性触发）
  - 依赖：Moirai 提供种群上下文、Lineage/Genome
- **AgentV5**：执行层决策。  
  - 类：`prometheus.core.agent_v5.AgentV5`
  - 关键方法：`create_genesis()`，`make_trading_decision()`，`update_after_trade()`
  - 依赖：LineageVector，GenomeVector，Instinct，StrategyPool，Daimon
- **BulletinBoard**：信息发布与共享。  
  - 类：`prometheus.core.bulletin_board.BulletinBoard`
  - 关键方法：`publish()`，`collect()`
- **Dual Ledger System**：`PublicLedger` + `AgentAccountSystem`（私账）  
  - 类：`prometheus.ledger.public_ledger.PublicLedger`，`prometheus.ledger.agent_account.AgentAccountSystem`
  - 关键方法：`record_trade()`，`settle_pnl()`，`sync_with_exchange()`；Agent 侧挂载：`agent.account = AgentAccountSystem(...)`
  - 辅助：`prometheus.ledger.attach_accounts.attach_accounts(agents, public_ledger)` 幂等挂载
  - 用途：逐Agent持仓、盈亏、对账；真实/虚拟盘必备
- **OKX Exchange Wrapper**：统一下单/查询。  
  - 类：`prometheus.exchange.okx_api.OKXExchange`
  - 关键方法：`create_market_order()`/`place_order()`，`fetch_positions()`，`close_all_positions()`
  - 关键参数：`sandbox=True`（顶层启用），`tdMode`，`posSide`，`instId`（如 `BTC-USDT-SWAP`）
- **DiversityMonitor**：多样性监控与警报。  
  - 类：`prometheus.core.diversity_monitor.DiversityMonitor`
  - 关键方法：`monitor()`；指标：gene_entropy、strategy_entropy、lineage_entropy、active_families、diversity_score
  - 阈值：`DEFAULT_THRESHOLDS`，活跃家族动态阈值已放宽
- **V6 Facade（统一入口）**  
  - 类：`prometheus.facade.v6_facade.V6Facade`
  - 用途：创世+账簿挂载、run_cycle（监督/决策/执行/记账/监控/进化）、先知触发移民、清仓/对账占位、状态报告

## 必选 vs 可选（推荐开关）
- 必选（实盘/虚拟盘/严肃回测必须开启）：Supervisor/Moirai、Dual Ledger（PublicLedger+AgentAccountSystem）、DiversityMonitor、EvolutionManagerV5、BulletinBoard、OKXExchange 封装。
- 推荐但可配置：WorldSignature/Prophet、Mastermind 高阶策略、激进变异/移民策略（v5.3）、详细日志/解释性输出。
- 轻量模式：仅限探索性回测，可关闭高阶模块；需在结果标注“非正式评估”，且仍建议保留账簿以便对账。

## 标准调用顺序（最小骨架）
1) 初始化：BulletinBoard → Ledgers（Public + per-agent Account）→ DiversityMonitor → EvolutionManagerV5 → Moirai/Supervisor  
2) 创世：`moirai._genesis_create_agents(...)`，确保为每个 Agent 设置 `lineage.family_id`，并挂载 `AgentAccountSystem`  
3) 循环：`moirai.run_cycle()` 内部完成监督→决策→下单→记账→监控→淘汰→进化  
4) 进化：每若干周期调用 `evolution_manager.evolve_population()`，维护家族多样性与移民  
5) 对账：真实/虚拟盘必须通过 PublicLedger + AgentAccountSystem 同步交易与 PnL  

## 常见依赖关系
- OKX 交易 → 必须有 Dual Ledger（PublicLedger + AgentAccountSystem）→ 记账/对账/个体盈亏
- 进化/多样性 → 必须有 LineageVector（含 family_id）+ DiversityMonitor（阈值）  
- 创世/移民 → 使用 Moirai/EvolutionManager 提供的官方入口，避免手写简化版

## 典型文件入口
- 骨架/模板：`templates/STANDARD_TEST_TEMPLATE.py`
- 完整回测示例：`test_ultimate_1000x_COMPLETE.py`
- OKX 实盘/虚拟盘示例：`test_live_continuous.py`
- 审计/重写计划：`ARCHITECTURE_AUDIT_2025.md` · `CODE_AUDIT_REPORT.md` · `AUDIT_SUMMARY.md` · `templates/REWRITE_PLAN.md`

