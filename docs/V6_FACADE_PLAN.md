# V6 封装/兼容策略（草案）

目标：以统一封装取代多继承/多版本分叉，确立单一路径，隔离 legacy，减少调用歧义与臃肿。

## 主干架构（唯一推荐路径）
- 监督/生命周期：Supervisor/Moirai（统一 run_cycle 入口）
- Agent：AgentV5 + Daimon（决策中枢）
- 账簿：Dual Ledger（PublicLedger + AgentAccountSystem，强制挂载）
- 进化：EvolutionManagerV5（先知触发移民，多样性保护）
- 信息流：BulletinBoard
- 交易：OKXExchange 封装（含清仓、对账、sandbox 参数）
- 多样性：DiversityMonitor（动态阈值）

## Facade / 统一入口清单
- 创世/初始化：`facade.init_population(config)` → 内部调用 Moirai/Supervisor 创世、attach_accounts、公告/监控初始化
- 主循环：`facade.run_cycle(market_feed)` 或 `facade.run(duration/config)` → 内部调用监督+决策+下单+记账+监控+进化
- 进化干预：`facade.maybe_inject_immigrants(metrics, force=False)`（先知策略触发）
- 对账/清仓：`facade.reconcile()` / `facade.close_all()`（调用 OKXExchange + Ledger 同步）
- 日志/报告：`facade.report_status()`（人口、家族、多样性、资金）

## Legacy 隔离策略
- 将 v1–v3 旧框架、简化测试脚本标记 deprecated，移出默认入口；放入 `legacy/` 或仅保留为文档示例。
- AgentV4 等兼容模块保持在兼容命名空间，不在 Facade 中暴露。
- 简化/实验性测试若保留，必须声明“非正式评估”且不走正式报告管线。

## 配置优先，少继承
- 可选功能（WorldSignature/Prophet、高阶 Mastermind 策略、激进变异/移民、详细日志）通过配置/策略注入开启，默认保守。
- 不用继承分叉主干类，统一 Facade 接收策略/回调实现多态。

## 模板与入口收敛
- 标准测试模板为唯一起点（实盘/虚拟盘/严肃回测）。轻量回测模板可选，但结果不进入正式评估。
- OKX/回测脚本统一调用 Facade，禁止手写简化版调用链。

## 清理/迁移计划（建议）
1) 文档：更新 README 导航、DOCUMENT_MAP，注明 v6 主干与 legacy 隔离。
2) 代码：添加 Facade（高层封装），接入现有主干模块；移除/隔离旧入口，模板指向 Facade。
3) 测试：将核心测试迁移到 Facade；旧简化测试标 deprecated 或移到 legacy。

## Mock 训练场景（纳入 Facade）
- Exchange 适配：使用 MockExchange（撮合/手续费/滑点/延迟/拒单可配置），接口与 OKXExchange 对齐。
- 数据源：历史回放或合成扰动数据；支持多场景脚本化（趋势/震荡/崩盘/闪崩/低流动）。
- 必选链路：仍用 Supervisor/Moirai、Dual Ledger、EvolutionManagerV5、DiversityMonitor、BulletinBoard；下单/对账走 MockExchange + Ledger。
- 可重复性：固定随机种子，记录配置哈希、数据集版本；输出训练 run 配置、指标与日志。
- 评估指标：收益/回撤/Sharpe/滑点与费用占比/拒单率/延迟敏感度，多样性指标（gene/lineage/strategy entropy, active_families），极端场景存活率。
- 标识：输出标注“Mock/不可直接外推实盘”，后续需在虚拟盘/实盘对比验证。

