"""
公告板系统演示 - Prometheus v4.0

演示：
1. 公告板如何发布信息
2. 不同Agent如何选择性遵循
3. 同一公告导致不同行为
"""

import sys
sys.path.append('..')

from prometheus.core import (
    BulletinBoardSystem,
    AgentV4,
    Bulletin,
    BulletinType,
    Priority,
    AgentPersonality
)
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_agent_types():
    """创建三种不同类型的Agent"""
    
    # Agent A: 独立型 (低公告板权重)
    agent_a_gene = {
        'signal_weights': {
            'technical': 0.6,
            'opponent': 0.3,
            'bulletin': 0.1,  # 很低！几乎不参考
            'emotion': 0.0
        },
        'bulletin_sensitivity': {
            'global': 0.2,
            'market': 0.3,
            'system': 0.5,  # 只关注风险警告
            'social': 0.0    # 完全不关注社交
        },
        'max_position_size': 0.2,
        'stop_loss': 0.05,
        'take_profit': 0.10
    }
    
    agent_a_personality = AgentPersonality(
        independence=0.9,      # 高度独立
        herd_mentality=0.1,    # 不从众
        contrarian=0.7         # 逆向思维
    )
    
    # Agent B: 社交型 (高公告板权重)
    agent_b_gene = {
        'signal_weights': {
            'technical': 0.3,
            'opponent': 0.2,
            'bulletin': 0.5,  # 很高！高度参考
            'emotion': 0.0
        },
        'bulletin_sensitivity': {
            'global': 0.9,
            'market': 0.8,
            'system': 0.7,
            'social': 0.9    # 高度关注社交信号
        },
        'max_position_size': 0.2,
        'stop_loss': 0.05,
        'take_profit': 0.10
    }
    
    agent_b_personality = AgentPersonality(
        independence=0.2,      # 低独立性
        herd_mentality=0.9,    # 高度从众
        contrarian=0.1
    )
    
    # Agent C: 平衡型
    agent_c_gene = {
        'signal_weights': {
            'technical': 0.4,
            'opponent': 0.3,
            'bulletin': 0.3,  # 适度参考
            'emotion': 0.0
        },
        'bulletin_sensitivity': {
            'global': 0.6,
            'market': 0.7,
            'system': 0.8,  # 重视风险
            'social': 0.4
        },
        'max_position_size': 0.2,
        'stop_loss': 0.05,
        'take_profit': 0.10
    }
    
    agent_c_personality = AgentPersonality(
        independence=0.5,
        herd_mentality=0.5,
        contrarian=0.3
    )
    
    return [
        ('独立型Agent-A', agent_a_gene, agent_a_personality),
        ('社交型Agent-B', agent_b_gene, agent_b_personality),
        ('平衡型Agent-C', agent_c_gene, agent_c_personality)
    ]


def simulate_bulletin_impact(bulletin_board: BulletinBoardSystem, agents: list):
    """模拟公告板对Agent的影响"""
    
    print("\n" + "="*80)
    print("场景1：主脑发布「市场转熊」战略公告")
    print("="*80)
    
    # 发布公告
    bulletin_board.post_strategic(
        content="【主脑战略】市场状态判定：牛市转熊市。建议：降低风险，保守操作，减少仓位。",
        sentiment="negative",
        impact_level="high"
    )
    
    # 获取公告
    bulletins = bulletin_board.global_board.get_recent(hours=24)
    
    # 模拟市场数据
    market_data = {
        'price': 50000,
        'bulletins': bulletins
    }
    
    print("\n各Agent的反应：\n")
    
    for agent_name, agent in agents:
        # 处理公告
        bulletin_signal = agent.bulletin_processor.process_bulletins(bulletins)
        
        # 模拟其他信号
        technical_signal = 0.5  # 技术面看多
        opponent_signal = 0.3   # 对手恐慌
        
        # 信号融合
        weights = agent.gene['signal_weights']
        final_signal = (
            technical_signal * weights['technical'] +
            opponent_signal * weights['opponent'] +
            bulletin_signal * weights['bulletin']
        )
        
        total_weight = weights['technical'] + weights['opponent'] + weights['bulletin']
        final_signal /= total_weight
        
        # 决策
        decision = 'BUY' if final_signal > 0.1 else ('SELL' if final_signal < -0.1 else 'HOLD')
        
        print(f"{agent_name}:")
        print(f"  - 公告板权重: {weights['bulletin']:.2f}")
        print(f"  - 公告信号: {bulletin_signal:+.2f}")
        print(f"  - 技术信号: {technical_signal:+.2f}")
        print(f"  - 对手信号: {opponent_signal:+.2f}")
        print(f"  - 综合信号: {final_signal:+.2f}")
        print(f"  - 决策: {decision}")
        print()
    
    print("\n" + "="*80)
    print("场景2：系统发布「风险警告」")
    print("="*80)
    
    # 发布风险警告
    bulletin_board.post_risk_warning(
        content="【系统警告】检测到大量止损集中于50000点位，可能触发连锁止损，建议谨慎。",
        severity="high"
    )
    
    bulletins = bulletin_board.system_board.get_recent(hours=24)
    market_data['bulletins'] = bulletins
    
    print("\n各Agent的反应：\n")
    
    for agent_name, agent in agents:
        # 处理公告
        bulletin_signal = agent.bulletin_processor.process_bulletins(bulletins)
        
        # 获取对系统警告的敏感度
        system_sensitivity = agent.gene['bulletin_sensitivity']['system']
        
        print(f"{agent_name}:")
        print(f"  - 系统警告敏感度: {system_sensitivity:.2f}")
        print(f"  - 公告信号: {bulletin_signal:+.2f}")
        
        if system_sensitivity > 0.6:
            print(f"  - 反应: 高度警惕，立即平仓或减仓")
        elif system_sensitivity > 0.3:
            print(f"  - 反应: 适度关注，观察市场")
        else:
            print(f"  - 反应: 几乎忽略，继续执行策略")
        print()
    
    print("\n" + "="*80)
    print("场景3：传奇Agent发布套利信号")
    print("="*80)
    
    # Agent发布社交信号
    bulletin_board.post_agent_signal(
        agent_id="Agent-045",
        signal={
            'description': '发现：凌晨2-4点某Bot有规律性行为，可套利',
            'confidence': 0.85,
            'sentiment': 'positive'
        },
        credibility=0.95  # 传奇Agent，高信誉
    )
    
    bulletins = bulletin_board.social_board.get_recent(hours=24)
    
    print("\n各Agent的反应：\n")
    
    for agent_name, agent in agents:
        # 获取对社交信号的敏感度
        social_sensitivity = agent.gene['bulletin_sensitivity']['social']
        
        print(f"{agent_name}:")
        print(f"  - 社交信号敏感度: {social_sensitivity:.2f}")
        
        if social_sensitivity > 0.7:
            print(f"  - 反应: 高度关注，学习并尝试这个模式")
        elif social_sensitivity > 0.3:
            print(f"  - 反应: 谨慎观察，先验证再决定")
        else:
            print(f"  - 反应: 完全忽略，我有自己的策略")
        print()
    
    # 统计
    print("\n" + "="*80)
    print("公告板统计")
    print("="*80)
    stats = bulletin_board.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


def simulate_learning():
    """模拟Agent学习公告可信度"""
    
    print("\n" + "="*80)
    print("场景4：Agent学习公告可信度")
    print("="*80)
    
    # 创建Agent
    agent = AgentV4(
        agent_id="Learner-001",
        initial_capital=10000
    )
    
    print(f"\n初始信任度:")
    for bulletin_type, trust in agent.bulletin_processor.learned_trust.items():
        print(f"  {bulletin_type}: {trust:.2f}")
    
    # 模拟10次交易
    print(f"\n模拟10次遵循公告的交易结果:\n")
    
    for i in range(10):
        bulletin_type = np.random.choice(['global', 'market', 'system', 'social'])
        result = np.random.uniform(-0.05, 0.05)  # 盈亏
        
        agent.bulletin_processor.record_outcome(bulletin_type, True, result)
        
        outcome = "盈利" if result > 0 else "亏损"
        print(f"交易 {i+1}: 遵循{bulletin_type}公告 → {outcome} {result:+.2%}")
    
    print(f"\n学习后的信任度:")
    for bulletin_type, trust in agent.bulletin_processor.learned_trust.items():
        print(f"  {bulletin_type}: {trust:.2f}")
    
    print("\n💡 信任度会根据历史表现动态调整！")


def main():
    """主函数"""
    
    print("\n" + "="*80)
    print("公告板系统演示 - Prometheus v4.0")
    print("="*80)
    
    # 1. 创建公告板系统
    bulletin_board = BulletinBoardSystem()
    
    # 2. 创建三种类型的Agent
    agent_configs = create_agent_types()
    agents = []
    
    for agent_name, gene, personality in agent_configs:
        agent = AgentV4(
            agent_id=agent_name,
            initial_capital=10000,
            gene=gene,
            personality=personality
        )
        agents.append((agent_name, agent))
    
    # 3. 模拟公告板影响
    simulate_bulletin_impact(bulletin_board, agents)
    
    # 4. 模拟学习过程
    simulate_learning()
    
    print("\n" + "="*80)
    print("演示完成！")
    print("="*80)
    print("\n关键要点：")
    print("1. 公告板发布信息，但不强制执行")
    print("2. 每个Agent根据基因（先天）和性格（特质）选择是否遵循")
    print("3. Agent通过学习（后天）调整对公告的信任度")
    print("4. 同一公告导致不同Agent做出不同决策 → 多样性！")
    print()


if __name__ == "__main__":
    main()

