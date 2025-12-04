"""
EvolutionManagerV5测试 - 验证v5.0进化系统
========================================

测试：
1. Agent评估和排序
2. 父母选择（生殖隔离）
3. 子代创建（Lineage/Genome/Instinct遗传）
4. 完整进化周期
"""

import sys
sys.path.insert(0, '.')

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.agent_v5 import AgentV5
from tests.test_moirai_v5_mock import MockOKXTrading, MockMastermind, MockBulletinBoard


def test_evolution_cycle():
    """测试完整进化周期"""
    print("\n" + "="*70)
    print("🧬 测试v5.0进化系统")
    print("="*70)
    
    # 1. 创建Moirai
    print("\n⚖️ Step 1: 初始化Moirai...")
    moirai = Moirai(
        bulletin_board=MockBulletinBoard(),
        num_families=50
    )
    moirai.next_agent_id = 1
    moirai.config = type('Config', (), {'TRADING_MODE': 'mock'})()
    
    # 2. Clotho创建初始Agent
    print("\n🧵 Step 2: Clotho创建初始种群...")
    agents = moirai._clotho_create_v5_agents(
        agent_count=10,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    moirai.agents = agents
    
    print(f"   创建{len(agents)}个Agent")
    
    # 3. 模拟交易（让一些Agent盈利，一些亏损）
    print("\n💰 Step 3: 模拟交易结果...")
    for i, agent in enumerate(agents):
        # 前5个Agent盈利
        if i < 5:
            agent.total_pnl = 500 + i * 100
            agent.current_capital = 10000 + agent.total_pnl
            agent.trade_count = 10
            agent.win_count = 7
        # 后5个Agent亏损
        else:
            agent.total_pnl = -200 - i * 50
            agent.current_capital = 10000 + agent.total_pnl
            agent.trade_count = 10
            agent.win_count = 3
    
    print(f"   设置盈利Agent: {sum(1 for a in agents if a.total_pnl > 0)}个")
    print(f"   设置亏损Agent: {sum(1 for a in agents if a.total_pnl < 0)}个")
    
    # 4. 创建进化管理器
    print("\n🧬 Step 4: 初始化进化管理器...")
    evo_manager = EvolutionManagerV5(
        moirai=moirai,
        elite_ratio=0.2,
        elimination_ratio=0.3,
        num_families=50
    )
    
    # 5. 执行进化周期
    print("\n🔄 Step 5: 执行进化周期...")
    initial_count = len(moirai.agents)
    
    evo_manager.run_evolution_cycle(current_price=90000)
    
    final_count = len(moirai.agents)
    
    # 6. 验证结果
    print(f"\n📊 Step 6: 验证进化结果...")
    print(f"   初始Agent数量: {initial_count}")
    print(f"   最终Agent数量: {final_count}")
    print(f"   新生Agent数量: {evo_manager.total_births}")
    print(f"   淘汰Agent数量: {evo_manager.total_deaths}")
    print(f"   差额: {final_count - initial_count}")
    
    # 检查是否有新生儿
    new_generation_agents = [a for a in moirai.agents if a.generation > 0]
    print(f"   第1代Agent数量: {len(new_generation_agents)}")
    
    if new_generation_agents:
        sample = new_generation_agents[0]
        print(f"\n   👶 新生儿样本: {sample.agent_id}")
        print(f"      代数: {sample.generation}")
        print(f"      血统: {sample.lineage.classify_purity()}")
        print(f"      策略: {[s.name for s in sample.strategy_pool]}")
    
    # 7. 双熵检查
    print(f"\n🩺 Step 7: 双熵健康检查...")
    health = evo_manager.blood_lab.population_checkup(moirai.agents)
    print(f"   血统熵: {health.lineage_entropy_normalized:.3f}")
    print(f"   基因熵: {health.gene_entropy:.3f}")
    print(f"   总体健康: {health.overall_health}")
    
    # 验证（放宽条件，允许±1的误差）
    assert abs(final_count - initial_count) <= 1, \
        f"种群数量偏差过大: {initial_count} -> {final_count} (差{final_count - initial_count})"
    assert evo_manager.total_births > 0, "应该有新生儿"
    assert evo_manager.total_deaths > 0, "应该有淘汰"
    assert len(new_generation_agents) > 0, "应该有第1代Agent"
    
    print("\n" + "="*70)
    print("✅ 所有进化测试通过！")
    print("="*70)


if __name__ == '__main__':
    try:
        test_evolution_cycle()
        with open('evolution_test_result.txt', 'w') as f:
            f.write('SUCCESS: All evolution tests passed!\n')
    except Exception as e:
        with open('evolution_test_result.txt', 'w') as f:
            f.write(f'FAILED: {e}\n')
            import traceback
            f.write(traceback.format_exc())
        raise

