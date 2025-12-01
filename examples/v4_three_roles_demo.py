"""
Prometheus v4.0 三大角色系统演示

展示主脑、监督者、Agent 如何协作运行
"""

import logging
from prometheus.core import (
    Mastermind, Supervisor, AgentV4,
    MarketRegime, AgentState
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数 - 演示三大角色系统"""
    
    print("=" * 80)
    print("Prometheus v4.0 - 三大角色自主进化交易系统演示")
    print("=" * 80)
    print()
    
    # ========================================
    # 1. 初始化主脑
    # ========================================
    print("【第一步】初始化主脑...")
    mastermind = Mastermind(initial_capital=100000.0)
    print(f"✓ 主脑已就位，管理资金: ${mastermind.initial_capital:,.2f}")
    print()
    
    # ========================================
    # 2. 初始化监督者
    # ========================================
    print("【第二步】初始化监督者...")
    supervisor = Supervisor(
        suicide_threshold=0.8,      # 绝望指数 > 0.8 建议自杀
        last_stand_threshold=0.6    # 濒危指数 > 0.6 建议拼搏
    )
    print("✓ 监督者已就位，开始监控...")
    print()
    
    # ========================================
    # 3. 创建 Agent 群体
    # ========================================
    print("【第三步】创建 Agent 群体...")
    agents = []
    for i in range(5):
        agent = AgentV4(
            agent_id=f"Agent-{i+1:03d}",
            initial_capital=10000.0
        )
        agents.append(agent)
        print(f"  ✓ {agent.agent_id} 诞生 | 激进度: {agent.personality.aggression:.2f} | "
              f"生存意志: {agent.personality.survival_will:.2f}")
    print()
    
    # ========================================
    # 4. 模拟市场数据
    # ========================================
    print("【第四步】模拟市场环境...")
    market_data = {
        'timestamp': '2025-12-01 10:00:00',
        'price': 50000.0,
        'volume': 1000000,
        'trend': 'bullish'
    }
    print(f"✓ 市场状态: {market_data}")
    print()
    
    # ========================================
    # 5. 主脑战略决策
    # ========================================
    print("【第五步】主脑进行战略决策...")
    agent_statistics = {
        'avg_performance': 0.05,  # 平均收益 5%
        'total_agents': len(agents),
        'avg_fitness': 0.6
    }
    
    system_metrics = {
        'drawdown': 0.1,
        'diversity': 0.7
    }
    
    decision = mastermind.make_strategic_decision(
        market_data=market_data,
        agent_statistics=agent_statistics,
        system_metrics=system_metrics
    )
    
    print(f"✓ 战略决策完成:")
    print(f"  - 市场状态: {decision['market_regime']}")
    print(f"  - 资金利用率: {decision['strategy'].total_capital_utilization:.1%}")
    print(f"  - 淘汰压力: {decision['strategy'].selection_pressure:.2f}")
    print(f"  - 系统健康: {decision['health']['overall_health']}")
    print()
    
    # ========================================
    # 6. 模拟 Agent 遭遇困境
    # ========================================
    print("【第六步】模拟 Agent 遭遇困境...")
    
    # 模拟 Agent-003 陷入困境
    struggling_agent = agents[2]
    struggling_agent.current_capital = 3000  # 亏损 70%
    struggling_agent.consecutive_losses = 8
    struggling_agent.days_alive = 15
    struggling_agent.trade_count = 30
    struggling_agent.win_count = 8
    
    print(f"⚠️  {struggling_agent.agent_id} 陷入困境:")
    print(f"  - 当前资金: ${struggling_agent.current_capital:.2f} (剩余 {struggling_agent.current_capital/struggling_agent.initial_capital:.1%})")
    print(f"  - 连续亏损: {struggling_agent.consecutive_losses} 次")
    print(f"  - 胜率: {struggling_agent.win_count/struggling_agent.trade_count:.1%}")
    print()
    
    # ========================================
    # 7. 监督者评估 Agent
    # ========================================
    print("【第七步】监督者评估 Agent 群体...")
    
    agents_data = []
    for agent in agents:
        agents_data.append({
            'agent_id': agent.agent_id,
            'current_capital': agent.current_capital,
            'initial_capital': agent.initial_capital,
            'consecutive_losses': agent.consecutive_losses,
            'consecutive_wins': agent.consecutive_wins,
            'days_alive': agent.days_alive,
            'trade_count': agent.trade_count,
            'win_count': agent.win_count,
            'win_rate': agent.win_count / max(agent.trade_count, 1),
            'total_pnl': agent.total_pnl,
            'fitness_score': 0.5,  # 简化
            'market_adaptation': 0.5,
            'recent_trend': -0.3,
            'market_opportunity': 0.6,
            'survival_will': agent.personality.survival_will,
            'personality_aggression': agent.personality.aggression
        })
    
    population_stats = supervisor.monitor_population(
        agents_data=agents_data,
        environmental_pressure=decision['strategy'].environmental_pressure
    )
    
    print(f"✓ 群体监控完成:")
    print(f"  - 健康: {population_stats['health_counts']['healthy']} 个")
    print(f"  - 警告: {population_stats['health_counts']['warning']} 个")
    print(f"  - 危急: {population_stats['health_counts']['critical']} 个")
    print(f"  - 濒死: {population_stats['health_counts']['dying']} 个")
    print()
    
    # 检查困境 Agent 的评估结果
    for report in population_stats['reports']:
        if report.agent_id == struggling_agent.agent_id:
            print(f"📊 {struggling_agent.agent_id} 详细评估:")
            print(f"  - 绝望指数: {report.despair_index:.2f}")
            print(f"  - 濒危指数: {report.endangered_index:.2f}")
            print(f"  - 健康状态: {report.health_status}")
            print(f"  - 建议行动: {report.recommended_action}")
            print()
    
    # ========================================
    # 8. Agent 自主决策
    # ========================================
    print("【第八步】Agent 自主决策...")
    
    # 更新困境 Agent 的状态
    struggling_agent.update_emotional_state()
    
    print(f"💭 {struggling_agent.agent_id} 的情绪状态:")
    print(f"  - 绝望: {struggling_agent.emotion.despair:.2f}")
    print(f"  - 恐惧: {struggling_agent.emotion.fear:.2f}")
    print(f"  - 信心: {struggling_agent.emotion.confidence:.2f}")
    print()
    
    # 检查是否自杀
    if struggling_agent.should_commit_suicide():
        print(f"💀 {struggling_agent.agent_id} 决定自杀...")
        struggling_agent.commit_suicide()
        print(f"  ✓ 已执行自杀，原因: {struggling_agent.death_reason.value}")
    
    # 检查是否拼死一搏
    elif struggling_agent.should_enter_last_stand():
        print(f"⚔️  {struggling_agent.agent_id} 决定拼死一搏！")
        struggling_agent.enter_last_stand()
        print(f"  ✓ 已进入拼搏模式")
        print(f"  - 仓位提升至: {struggling_agent.gene['max_position_size']:.2f}")
        print(f"  - 止损: {struggling_agent.gene['stop_loss']:.3f}")
        print(f"  - 止盈: {struggling_agent.gene['take_profit']:.3f}")
    
    print()
    
    # ========================================
    # 9. 系统风险预警
    # ========================================
    print("【第九步】系统风险检测...")
    alerts = supervisor.detect_system_risks(population_stats)
    
    if alerts:
        print(f"⚠️  检测到 {len(alerts)} 个风险:")
        for alert in alerts:
            print(f"  [{alert['level'].upper()}] {alert['type']}: {alert['message']}")
    else:
        print("✓ 系统运行正常，无风险警报")
    print()
    
    # ========================================
    # 10. 总结
    # ========================================
    print("=" * 80)
    print("演示总结")
    print("=" * 80)
    print()
    print("✅ v4.0 三大角色系统核心特性:")
    print()
    print("1. 【主脑】战略决策层")
    print("   - 分析市场宏观状态")
    print("   - 制定全局策略和参数")
    print("   - 不直接干预 Agent 行为")
    print()
    print("2. 【监督者】观察评估层")
    print("   - 实时监控 Agent 状态")
    print("   - 计算绝望/濒危指数")
    print("   - 发现系统性风险")
    print("   - 提供建议但不强制执行")
    print()
    print("3. 【Agent】完全自主层")
    print("   - 拥有性格和情绪")
    print("   - 自主决定交易策略")
    print("   - 自主选择生死(自杀/拼搏)")
    print("   - 不受外部强制干预")
    print()
    print("🔑 关键原则:")
    print("   ✓ 信息单向流动：主脑 → 监督者 → Agent (制定规则)")
    print("   ✓ 反馈循环：Agent 表现 → 监督者评估 → 主脑调整")
    print("   ✓ 完全自主：Agent 在规则内自由决策")
    print("   ✓ 自然选择：通过环境压力而非强制干预")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()

