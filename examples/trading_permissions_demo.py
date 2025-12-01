"""
交易权限系统演示 - Prometheus v4.0

演示：
1. 新手Agent从现货开始
2. 表现优秀逐步晋升
3. 获得更高杠杆和品种权限
4. 基因在权限允许下逐步表达
"""

import sys
sys.path.append('..')

from prometheus.core import (
    AgentV4,
    TradingPermissionSystem,
    RiskController,
    PermissionLevel,
    TradingProduct,
    AgentPersonality
)
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def simulate_agent_growth():
    """模拟Agent成长过程"""
    
    print("\n" + "="*80)
    print("场景1：创世Agent - 从新手起步")
    print("="*80)
    
    # 创建一个有高杠杆基因的Agent
    high_leverage_gene = {
        'leverage_appetite': 0.9,  # 基因上喜欢高杠杆
        'product_preference': {
            'spot': 0.3,
            'margin': 0.5,
            'perpetual': 0.9,      # 最喜欢永续合约
            'futures': 0.8,
            'options': 0.7
        },
        'signal_weights': {
            'technical': 0.5,
            'opponent': 0.3,
            'bulletin': 0.1,
            'emotion': 0.1
        },
        'max_position_size': 0.3,
        'stop_loss': 0.05,
        'take_profit': 0.10
    }
    
    agent = AgentV4(
        agent_id="HighLeverageGene-001",
        initial_capital=10000,
        gene=high_leverage_gene
    )
    
    print(f"\nAgent初始状态:")
    print(f"  - 权限级别: {agent.permission_level.value}")
    print(f"  - 基因杠杆偏好: {agent.gene['leverage_appetite']:.2f} (0.9 = 激进)")
    print(f"  - 基因品种偏好: 永续合约 ({agent.gene['product_preference']['perpetual']:.2f})")
    
    # 检查实际能用什么
    config = agent.permission_system.permissions[agent.permission_level]
    print(f"\n  实际权限:")
    print(f"  - 允许品种: {[p.value for p in config.allowed_products]}")
    print(f"  - 最大杠杆: {config.max_leverage}x")
    print(f"  - 最大仓位: {config.max_position_ratio*100}%")
    
    # 模拟市场数据
    market_data = {'price': 50000, 'volatility': 0.03}
    
    # 选择交易品种
    product = agent.select_trading_product(market_data)
    leverage = agent.calculate_leverage(market_data)
    
    print(f"\n  实际交易决策:")
    print(f"  - 选择品种: {product.value} (想用永续，但只能用现货)")
    print(f"  - 使用杠杆: {leverage:.1f}x (想用高杠杆，但只能1x)")
    print(f"\n  💡 基因被权限限制，潜力未释放！")
    
    print("\n" + "="*80)
    print("场景2：7天后 - 表现优秀，晋升中级")
    print("="*80)
    
    # 模拟优秀表现
    agent.days_alive = 7
    agent.total_pnl = 600  # 6%收益
    agent.current_capital = 10600
    agent.trade_count = 20
    agent.win_count = 9   # 45%胜率
    agent.capital_history = [10000, 10200, 10400, 10600]
    
    # 更新权限
    agent.update_permission_level()
    
    print(f"\nAgent当前状态:")
    print(f"  - 权限级别: {agent.permission_level.value}")
    
    config = agent.permission_system.permissions[agent.permission_level]
    print(f"  - 允许品种: {[p.value for p in config.allowed_products]}")
    print(f"  - 最大杠杆: {config.max_leverage}x")
    
    product = agent.select_trading_product(market_data)
    leverage = agent.calculate_leverage(market_data)
    
    print(f"\n  实际交易决策:")
    print(f"  - 选择品种: {product.value}")
    print(f"  - 使用杠杆: {leverage:.1f}x")
    print(f"\n  💡 基因开始表达！可以用杠杆了")
    
    print("\n" + "="*80)
    print("场景3：14天后 - 继续优秀，晋升高级")
    print("="*80)
    
    agent.days_alive = 14
    agent.total_pnl = 1600  # 16%收益
    agent.current_capital = 11600
    agent.trade_count = 45
    agent.win_count = 22   # 48.9%胜率
    agent.capital_history.extend([10800, 11000, 11400, 11600])
    
    agent.update_permission_level()
    
    print(f"\nAgent当前状态:")
    print(f"  - 权限级别: {agent.permission_level.value}")
    
    config = agent.permission_system.permissions[agent.permission_level]
    print(f"  - 允许品种: {[p.value for p in config.allowed_products]}")
    print(f"  - 最大杠杆: {config.max_leverage}x")
    
    product = agent.select_trading_product(market_data)
    leverage = agent.calculate_leverage(market_data)
    
    print(f"\n  实际交易决策:")
    print(f"  - 选择品种: {product.value} (终于可以用永续合约！)")
    print(f"  - 使用杠杆: {leverage:.1f}x")
    print(f"\n  ✨ 基因充分表达！高杠杆+永续合约策略解锁")
    
    print("\n" + "="*80)
    print("场景4：30天后 - 成为专家")
    print("="*80)
    
    agent.days_alive = 30
    agent.total_pnl = 3200  # 32%收益
    agent.current_capital = 13200
    agent.trade_count = 95
    agent.win_count = 48   # 50.5%胜率
    
    agent.update_permission_level()
    
    print(f"\nAgent当前状态:")
    print(f"  - 权限级别: {agent.permission_level.value}")
    
    config = agent.permission_system.permissions[agent.permission_level]
    print(f"  - 允许品种: {[p.value for p in config.allowed_products]}")
    print(f"  - 最大杠杆: {config.max_leverage}x")
    
    product = agent.select_trading_product(market_data)
    leverage = agent.calculate_leverage(market_data)
    
    print(f"\n  实际交易决策:")
    print(f"  - 选择品种: {product.value}")
    print(f"  - 使用杠杆: {leverage:.1f}x (可以用到20x！)")
    print(f"\n  🚀 专家级权限！全合约品种+高杠杆")


def simulate_inheritance():
    """模拟权限继承"""
    
    print("\n" + "="*80)
    print("场景5：权限继承 - 优秀基因从更高起点开始")
    print("="*80)
    
    # 父母Agent（EXPERT级别）
    parent_gene = {
        'leverage_appetite': 0.7,
        'product_preference': {
            'spot': 0.2,
            'margin': 0.5,
            'perpetual': 0.8,
            'futures': 0.9,
            'options': 0.6
        },
        'signal_weights': {
            'technical': 0.5,
            'opponent': 0.3,
            'bulletin': 0.1,
            'emotion': 0.1
        },
        'max_position_size': 0.3,
        'stop_loss': 0.05,
        'take_profit': 0.10
    }
    
    parent = AgentV4(
        agent_id="Parent-Expert",
        initial_capital=50000,
        gene=parent_gene
    )
    
    # 模拟父母已经是EXPERT
    parent.permission_level = PermissionLevel.EXPERT
    
    print(f"父代Agent:")
    print(f"  - ID: {parent.agent_id}")
    print(f"  - 权限级别: {parent.permission_level.value}")
    
    # 繁殖子代
    child = AgentV4(
        agent_id="Child-001",
        initial_capital=20000,  # 继承更多资金
        gene=parent_gene,  # 继承基因
        parent_permission=parent.permission_level  # 继承权限
    )
    
    print(f"\n子代Agent:")
    print(f"  - ID: {child.agent_id}")
    print(f"  - 权限级别: {child.permission_level.value} (父母EXPERT，子代ADVANCED)")
    print(f"  - 初始资金: {child.initial_capital} (比创世Agent多)")
    
    config = child.permission_system.permissions[child.permission_level]
    print(f"\n  子代权限:")
    print(f"  - 允许品种: {[p.value for p in config.allowed_products]}")
    print(f"  - 最大杠杆: {config.max_leverage}x")
    
    print(f"\n  💡 优势：")
    print(f"  1. 跳过新手期（直接ADVANCED）")
    print(f"  2. 更多初始资金（奖励）")
    print(f"  3. 继承优秀基因")
    print(f"  4. 但仍需证明自己才能达到父母级别")


def simulate_risk_control():
    """模拟风控系统"""
    
    print("\n" + "="*80)
    print("场景6：风控系统 - 即使有权限也要通过风控")
    print("="*80)
    
    agent = AgentV4(
        agent_id="Risky-Agent",
        initial_capital=10000
    )
    
    # 假设Agent已经是EXPERT
    agent.permission_level = PermissionLevel.EXPERT
    agent.current_capital = 10000
    
    risk_controller = RiskController()
    
    print(f"\nAgent状态:")
    print(f"  - 权限级别: {agent.permission_level.value}")
    print(f"  - 最大杠杆: 20x")
    print(f"  - 当前资金: {agent.current_capital}")
    
    # 测试1：合理的交易
    trade1 = {
        'product': TradingProduct.PERPETUAL,
        'leverage': 5.0,
        'position_size': 0.2,
        'side': 'BUY'
    }
    
    market_data = {'volatility': 0.03}
    
    passed, reason = risk_controller.check_trade_risk(agent, trade1, market_data)
    print(f"\n交易1: 5x杠杆, 20%仓位")
    print(f"  - 风控结果: {'✅ 通过' if passed else '❌ 拒绝'}")
    print(f"  - 原因: {reason}")
    
    # 测试2：过高杠杆
    trade2 = {
        'product': TradingProduct.PERPETUAL,
        'leverage': 20.0,
        'position_size': 0.5,
        'side': 'BUY'
    }
    
    passed, reason = risk_controller.check_trade_risk(agent, trade2, market_data)
    print(f"\n交易2: 20x杠杆, 50%仓位")
    print(f"  - 风控结果: {'✅ 通过' if passed else '❌ 拒绝'}")
    print(f"  - 原因: {reason}")
    
    # 测试3：高波动下的高杠杆
    trade3 = {
        'product': TradingProduct.PERPETUAL,
        'leverage': 10.0,
        'position_size': 0.3,
        'side': 'BUY'
    }
    
    high_vol_market = {'volatility': 0.12}  # 12%波动
    
    passed, reason = risk_controller.check_trade_risk(agent, trade3, high_vol_market)
    print(f"\n交易3: 10x杠杆, 30%仓位, 高波动市场(12%)")
    print(f"  - 风控结果: {'✅ 通过' if passed else '❌ 拒绝'}")
    print(f"  - 原因: {reason}")
    
    print(f"\n  💡 风控系统作为最后一道防线！")


def simulate_population_distribution():
    """模拟Agent群体的权限分布"""
    
    print("\n" + "="*80)
    print("场景7：群体分布 - 金字塔结构")
    print("="*80)
    
    # 创建100个Agent，模拟不同表现
    agents = []
    
    for i in range(100):
        agent = AgentV4(
            agent_id=f"Agent-{i:03d}",
            initial_capital=10000
        )
        
        # 模拟不同的表现
        performance = np.random.random()
        
        if performance < 0.3:  # 30%表现差
            agent.days_alive = np.random.randint(1, 7)
            agent.total_pnl = np.random.uniform(-500, 300)
            agent.win_count = np.random.randint(0, 5)
            agent.trade_count = np.random.randint(5, 15)
        
        elif performance < 0.7:  # 40%表现中等
            agent.days_alive = np.random.randint(7, 20)
            agent.total_pnl = np.random.uniform(300, 1500)
            agent.win_count = np.random.randint(8, 15)
            agent.trade_count = np.random.randint(15, 35)
        
        elif performance < 0.9:  # 20%表现良好
            agent.days_alive = np.random.randint(20, 40)
            agent.total_pnl = np.random.uniform(1500, 3000)
            agent.win_count = np.random.randint(20, 35)
            agent.trade_count = np.random.randint(35, 70)
        
        else:  # 10%表现优秀
            agent.days_alive = np.random.randint(40, 80)
            agent.total_pnl = np.random.uniform(3000, 6000)
            agent.win_count = np.random.randint(40, 70)
            agent.trade_count = np.random.randint(70, 120)
        
        agent.current_capital = agent.initial_capital + agent.total_pnl
        agent.capital_history = [agent.initial_capital, agent.current_capital]
        
        # 更新权限
        agent.update_permission_level()
        
        agents.append(agent)
    
    # 统计分布
    perm_system = TradingPermissionSystem()
    stats = perm_system.get_level_statistics(agents)
    
    print(f"\n100个Agent的权限分布:\n")
    
    levels = [
        (PermissionLevel.MASTER, "大师"),
        (PermissionLevel.EXPERT, "专家"),
        (PermissionLevel.ADVANCED, "高级"),
        (PermissionLevel.INTERMEDIATE, "中级"),
        (PermissionLevel.NOVICE, "新手")
    ]
    
    for level, name in levels:
        count = stats['counts'][level]
        percentage = stats['distribution'][level] * 100
        bar = "█" * int(percentage / 2)
        print(f"{name:6s} ({level.value:12s}): {count:3d} ({percentage:5.1f}%) {bar}")
    
    print(f"\n  💡 自然形成金字塔结构！")
    print(f"  - 少数精英在顶端（高杠杆高收益）")
    print(f"  - 大部分在中层（稳健成长）")
    print(f"  - 新手在底层（学习阶段）")


def main():
    """主函数"""
    
    print("\n" + "="*80)
    print("交易权限系统演示 - Prometheus v4.0")
    print("="*80)
    
    # 1. Agent成长过程
    simulate_agent_growth()
    
    # 2. 权限继承
    simulate_inheritance()
    
    # 3. 风控系统
    simulate_risk_control()
    
    # 4. 群体分布
    simulate_population_distribution()
    
    print("\n" + "="*80)
    print("演示完成！")
    print("="*80)
    print("\n核心要点：")
    print("1. 新手Agent受保护，从低风险品种开始")
    print("2. 表现优秀逐步晋升，解锁更多权限")
    print("3. 基因潜力随权限提升逐步表达")
    print("4. 优秀基因继承时从更高起点开始")
    print("5. 风控系统作为最后防线")
    print("6. 自然形成金字塔分布")
    print("\n就像游戏升级系统：渐进式自由 + 能力证明 = 可持续进化！")
    print()


if __name__ == "__main__":
    main()

