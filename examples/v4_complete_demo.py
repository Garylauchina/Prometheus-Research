"""
Prometheus v4.0 - 完整示例

展示三层架构的完整工作流程：
1. Mastermind（主脑）- 战略决策
2. Supervisor（监督者）- 市场分析 + Agent监控
3. Agent（智能体）- 自主交易
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 导入核心组件
from prometheus.core import (
    # 三层架构
    Mastermind,
    Supervisor,
    AgentV4,
    
    # 公告板v4
    BulletinBoardV4,
    
    # 系统
    Valhalla,
    MedalSystem,
    NirvanaSystem,
    TradingPermissionSystem,
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def generate_market_data(periods=100):
    """生成模拟市场数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
    
    # 生成带趋势的价格
    base_price = 50000
    trend = np.linspace(0, 5000, periods)  # 上升趋势
    noise = np.random.randn(periods).cumsum() * 200
    
    close = base_price + trend + noise
    
    data = pd.DataFrame({
        'open': close + np.random.randn(periods) * 50,
        'high': close + abs(np.random.randn(periods) * 100),
        'low': close - abs(np.random.randn(periods) * 100),
        'close': close,
        'volume': np.random.randint(1000, 10000, periods)
    }, index=dates)
    
    # 确保high >= low
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Prometheus v4.0 - 完整演示")
    logger.info("=" * 60)
    
    # ========== 初始化系统 ==========
    logger.info("\n【步骤1】初始化系统组件...")
    
    # 公告板（三层架构）
    bulletin_board = BulletinBoardV4(max_bulletins_per_tier=50)
    
    # 英灵殿
    valhalla = Valhalla()
    
    # 奖章系统
    medal_system = MedalSystem()
    
    # 涅槃系统
    nirvana_system = NirvanaSystem()
    
    # 交易权限系统
    permission_system = TradingPermissionSystem()
    
    # 监督者（整合市场分析）
    supervisor = Supervisor(
        bulletin_board=bulletin_board,
        valhalla=valhalla,
        trading_permission_system=permission_system
    )
    
    # 主脑
    mastermind = Mastermind(
        bulletin_board=bulletin_board,
        nirvana_system=nirvana_system
    )
    
    logger.info("✅ 系统组件初始化完成")
    
    # ========== 创建Agent ==========
    logger.info("\n【步骤2】创建Agent群体...")
    
    agents = []
    for i in range(5):
        agent = AgentV4(
            agent_id=f"Agent{i+1:03d}",
            initial_capital=10000,
            bulletin_board=bulletin_board,
            permission_system=permission_system
        )
        agents.append(agent)
        supervisor.register_agent(agent)
    
    logger.info(f"✅ 创建了 {len(agents)} 个Agent")
    
    # ========== 生成市场数据 ==========
    logger.info("\n【步骤3】生成市场数据...")
    
    market_data = generate_market_data(periods=100)
    logger.info(f"✅ 生成了 {len(market_data)} 条市场数据")
    logger.info(f"   价格范围: {market_data['close'].min():.2f} - {market_data['close'].max():.2f}")
    
    # ========== 运行模拟 ==========
    logger.info("\n【步骤4】运行交易模拟...")
    logger.info("=" * 60)
    
    # 主脑发布战略公告
    logger.info("\n>>> Mastermind发布战略公告")
    mastermind.announce_strategy(
        strategy_type='conservative',
        parameters={
            'max_leverage': 2,
            'max_position_size': 0.3,
            'risk_level': 'medium'
        },
        reason='市场波动加剧，采取保守策略'
    )
    
    # 监督者进行综合监控
    logger.info("\n>>> Supervisor进行综合监控")
    supervisor.comprehensive_monitoring(market_data)
    
    # Agent读取公告
    logger.info("\n>>> Agent读取公告板")
    for agent in agents[:2]:  # 只展示前2个
        bulletins = bulletin_board.read(agent.agent_id, limit=3)
        logger.info(f"\n{agent.agent_id} 读取到 {len(bulletins)} 条公告:")
        for b in bulletins:
            logger.info(f"  [{b.tier.value}] {b.title} ({b.publisher})")
    
    # Agent进行交易决策（模拟）
    logger.info("\n>>> Agent进行交易决策")
    for agent in agents:
        # 这里是简化版，实际应该根据公告和市场数据决策
        logger.info(f"{agent.agent_id}: 分析市场，准备交易...")
        # agent.make_trading_decision(market_data)  # 实际实现
    
    # ========== 展示统计信息 ==========
    logger.info("\n" + "=" * 60)
    logger.info("【步骤5】系统统计信息")
    logger.info("=" * 60)
    
    # 公告板统计
    logger.info("\n📊 公告板统计:")
    bb_stats = bulletin_board.get_statistics()
    logger.info(f"  总发布: {bb_stats['total_posts']} 条")
    logger.info(f"  总阅读: {bb_stats['total_views']} 次")
    for tier, data in bb_stats['by_tier'].items():
        logger.info(f"  [{tier}] {data['count']}条公告, {data['total_views']}次阅读")
    
    # 监督者统计
    logger.info("\n📊 监督者统计:")
    sup_stats = supervisor.get_statistics()
    logger.info(f"  监控Agent数: {sup_stats['monitored_agents']}")
    logger.info(f"  总评估次数: {sup_stats['total_evaluations']}")
    logger.info(f"  群体快照数: {sup_stats['population_snapshots']}")
    
    # Agent状态
    logger.info("\n📊 Agent状态:")
    for agent in agents[:3]:  # 只展示前3个
        logger.info(f"  {agent.agent_id}: "
                   f"资金={agent.capital:.2f}, "
                   f"权限={agent.permission_level.value}")
    
    # 英灵殿
    logger.info("\n🏛️ 英灵殿:")
    hall_stats = valhalla.get_statistics()
    logger.info(f"  总入选: {hall_stats['total_agents']}")
    logger.info(f"  外殿: {hall_stats['by_hall'][0]['count']}")
    logger.info(f"  大殿: {hall_stats['by_hall'][1]['count']}")
    logger.info(f"  内殿: {hall_stats['by_hall'][2]['count']}")
    
    # ========== 演示高级功能 ==========
    logger.info("\n" + "=" * 60)
    logger.info("【步骤6】演示高级功能")
    logger.info("=" * 60)
    
    # 市场状态
    logger.info("\n📈 当前市场状态:")
    if supervisor.current_market_state:
        state = supervisor.current_market_state
        logger.info(f"  趋势: {state.trend.value} (强度: {state.trend_strength:.2f})")
        logger.info(f"  动量: {state.momentum.value} (评分: {state.momentum_score:.2f})")
        logger.info(f"  波动率: {state.volatility.value} (评分: {state.volatility_score:.2f})")
        logger.info(f"  市场难度: {state.market_difficulty:.2f}")
        logger.info(f"  机会评分: {state.opportunity_score:.2f}")
        logger.info(f"  建议: {state.recommendation}")
    
    # 环境压力
    logger.info(f"\n🌍 环境压力: {supervisor.environment_pressure:.2f}")
    
    # 技术指标
    logger.info("\n📊 技术指标:")
    if supervisor.current_indicators:
        indicators = supervisor.current_indicators
        logger.info(f"  RSI: {indicators.momentum['RSI']:.2f}")
        logger.info(f"  ADX: {indicators.trend['ADX']:.2f}")
        logger.info(f"  ATR: {indicators.volatility['ATR']:.2f}")
        logger.info(f"  当前价格: {indicators.price['current']:.2f}")
    
    # ========== 完成 ==========
    logger.info("\n" + "=" * 60)
    logger.info("✅ 演示完成！")
    logger.info("=" * 60)
    
    # 展示系统架构
    logger.info("\n🏛️ Prometheus v4.0 三层架构:")
    logger.info("""
    ┌─────────────────────────────────────┐
    │      Mastermind（主脑）              │
    │  - 战略决策                          │
    │  - LLM Oracle                       │
    │  - 发布战略公告                      │
    └──────────────┬──────────────────────┘
                   │
                   ↓
    ┌─────────────────────────────────────┐
    │     公告板系统（三层）               │
    │  - 战略公告板（Mastermind）          │
    │  - 市场公告板（Supervisor）          │
    │  - 系统公告板（Supervisor）          │
    └──────────────┬──────────────────────┘
                   │
                   ↓
    ┌─────────────────────────────────────┐
    │      Supervisor（监督者）            │
    │  - 市场分析（技术指标+市场状态）     │
    │  - Agent监控（健康+权限+奖章）       │
    │  - 环境分析（压力+风险警告）         │
    └──────────────┬──────────────────────┘
                   │
                   ↓
    ┌─────────────────────────────────────┐
    │       Agent Population               │
    │  - 读取公告                          │
    │  - 自主交易                          │
    │  - 进化繁殖                          │
    └─────────────────────────────────────┘
    """)


if __name__ == "__main__":
    main()

