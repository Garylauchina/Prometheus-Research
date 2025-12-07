# Mock 训练 Playbook（v6 主干）

目标：在保持 v6 单一路径的前提下，用 MockExchange/数据回放进行高保真训练与进化，输出可重复、可对比的结果。

## 必选链路
- Supervisor/Moirai（run_cycle 统一）
- AgentV5 + Daimon
- 双账簿：PublicLedger + AgentAccountSystem（强制挂载，对账一致）
- EvolutionManagerV5（先知策略触发移民，多样性保护）
- BulletinBoard
- DiversityMonitor（动态阈值）
- MockExchange（接口与 OKXExchange 对齐）

## 数据与场景
- 数据源：历史回放或合成扰动（趋势/震荡/崩盘/闪崩/低流动）。
- 可脚本化场景序列，支持切换 regime。

## 配置要点
- 滑点/手续费/延迟/拒单率/部分成交：默认启用“现实”组合，明确标注“轻量/理想化”仅供探索。
- 随机种子：固定；记录配置哈希、数据集版本，保证可重复。
- 账簿/对账：所有成交回执进入双账簿，定期对账（Mock 持仓 vs Ledger）。

## 进化与多样性
- 使用 EvolutionManagerV5 + DiversityMonitor，按需调低变异/移民频率以提高可重复性。
- 先知触发移民：基于多样性指标/趋势信号，调用 `maybe_inject_immigrants`。

## 评估指标
- 收益/回撤/Sharpe/盈亏分布
- 成本/摩擦：滑点占比、手续费占比、拒单率、延迟敏感度
- 多样性：gene/lineage/strategy entropy，active_families，diversity_score
- 稳定性：极端场景存活率，策略/家族持久度

## 输出与标识
- 日志与配置：记录配置文件、随机种子、数据集版本、参数哈希。
- 结果标注：必须标明“Mock/不可直接外推实盘”；后续需在虚拟盘/实盘进行对比验证。

## 检查清单
- [ ] 账簿已挂载且对账通过
- [ ] MockExchange 参数符合“现实”基线（除非刻意做轻量测试）
- [ ] 随机种子/配置已记录
- [ ] 多样性监控开启，移民策略按需触发
- [ ] 输出结果已标注 Mock 性质

