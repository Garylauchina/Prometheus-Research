"""
Prometheus v7.0 测试 - 使用真实AgentV5⭐⭐⭐

【符合三大铁律】：
1. ✅ 使用真实的AgentV5（不是Mock）
2. ✅ 严格按照数据字典创建Agent
3. ✅ 使用完整的交易生命周期

【测试目标】：
验证v7.0核心功能：
- Prophet三维监控
- Moirai双周期机制  
- ThreeDimensionMonitor异常检测

【数据字典依赖】：
- docs/core_structures/agent_v5_spec.md
- docs/core_structures/evolution_manager_spec.md
- docs/three_iron_laws/README.md

【注意】：
这是v7.0的过渡版本测试。
最终版本应该完全集成到v6 Facade中。

2025-12-10 23:55创建
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time
import numpy as np
from datetime import datetime

# ===== 按照数据字典导入⭐⭐⭐ =====
# 参见: docs/core_structures/agent_v5_spec.md
from prometheus.core.agent_v5 import AgentV5, LineageVector, GenomeVector, StrategyParams
from prometheus.core.meta_genome import MetaGenome

# 参见: docs/core_structures/evolution_manager_spec.md
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

# v7.0组件
from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.bulletin_board import BulletinBoard

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ⭐⭐⭐ 不再需要RealMoiraiWrapper！MoiraiV7直接管理agents


def create_real_agent(agent_id: str) -> AgentV5:
    """
    按照数据字典创建真实的AgentV5⭐⭐⭐
    
    参见: docs/core_structures/agent_v5_spec.md
    
    必需参数（7个）：
    1. agent_id: str
    2. initial_capital: float
    3. lineage: LineageVector(np.ndarray)
    4. genome: GenomeVector(np.ndarray)
    5. strategy_params: StrategyParams
    6. generation: int
    7. meta_genome: MetaGenome
    """
    
    # 1. agent_id
    # 已提供
    
    # 2. initial_capital
    initial_capital = 10000.0
    
    # 3. lineage: LineageVector
    # 必须传入numpy数组，维度10
    lineage = LineageVector(np.random.rand(10))
    
    # 4. genome: GenomeVector
    # 必须传入numpy数组，维度50
    genome = GenomeVector(np.random.rand(50))
    
    # 5. strategy_params: StrategyParams
    # ⭐ v7.0完整版：使用真正的StrategyParams.create_genesis()
    # 参见：prometheus/core/strategy_params.py
    from prometheus.core.strategy_params import StrategyParams
    
    strategy_params = StrategyParams.create_genesis()
    
    # 注意：create_genesis()使用Beta(2, 2)分布创建多样性参数
    # 所有参数都在0-1范围内，已经包含：
    # - position_size_base（基础仓位）
    # - holding_preference（持仓时长偏好）
    # - directional_bias（方向偏好）
    # - stop_loss_threshold（止损阈值）
    # - take_profit_threshold（止盈阈值）
    # - trend_following_strength（趋势跟踪强度）
    # - leverage_preference（杠杆偏好）
    # - generation（代数，默认0）
    # - parent_params（父代参数，默认None）
    
    # 6. generation
    generation = 0
    
    # 7. meta_genome
    meta_genome = MetaGenome()
    
    # 创建Agent（完整参数）⭐⭐⭐
    agent = AgentV5(
        agent_id=agent_id,
        initial_capital=initial_capital,
        lineage=lineage,
        genome=genome,
        strategy_params=strategy_params,
        generation=generation,
        meta_genome=meta_genome
    )
    
    # 初始化运行时必需属性
    agent.total_roi = 0.0
    agent.allocated_capital = initial_capital
    agent.profit_factor = 1.0
    agent.winning_trades = 0
    agent.losing_trades = 0
    agent.total_profit = 0.0
    agent.total_loss = 0.01  # 避免除零
    agent.awards = 0
    
    return agent


def run_v7_test_with_real_agents(
    total_cycles: int = 20,  # ⚡ 优化：50→20，加快验证
    initial_agent_count: int = 20,  # ⚡ 优化：100→20，加快账簿挂载
    market_scenario: str = "mixed"
):
    """
    使用真实AgentV5运行v7.0测试⭐⭐⭐
    
    【符合三大铁律】：
    ✅ 使用真实AgentV5（查询数据字典）
    ✅ 使用完整初始化参数
    ✅ 不为测试简化底层机制
    
    Args:
        total_cycles: 总周期数
        initial_agent_count: 初始Agent数量
        market_scenario: 市场场景
    """
    
    logger.info("="*80)
    logger.info("🚀 Prometheus v7.0 测试 - 使用真实AgentV5")
    logger.info("="*80)
    logger.info(f"   总周期: {total_cycles}")
    logger.info(f"   初始Agent: {initial_agent_count}")
    logger.info(f"   市场场景: {market_scenario}")
    logger.info(f"   使用真实AgentV5: ✅")
    logger.info("="*80)
    
    # ===== 1. 初始化数据库 =====
    import tempfile
    import os
    run_id = f"v7_real_agents_{int(time.time())}"
    db_path = os.path.join(tempfile.gettempdir(), f"{run_id}.db")
    exp_db = ExperienceDB(db_path=db_path)
    logger.info(f"✅ 数据库: {db_path}")
    
    # ===== 2. 初始化组件 =====
    bb = BulletinBoard(board_name="v7_test")
    
    prophet = ProphetV7(
        bulletin_board=bb,
        experience_db=exp_db,
        run_id=run_id
    )
    logger.info("✅ Prophet v7.0已初始化")
    
    # ===== 3. 创建真实Agent（按照数据字典）⭐⭐⭐ =====
    logger.info(f"\n🧬 创建{initial_agent_count}个真实AgentV5...")
    logger.info("   参见: docs/core_structures/agent_v5_spec.md")
    
    # ⭐ 直接创建agents列表（不使用wrapper）
    agents = []
    
    start_time = time.time()
    for i in range(initial_agent_count):
        agent = create_real_agent(f"real_agent_{i}")
        agents.append(agent)
        
        if (i + 1) % 20 == 0:
            logger.info(f"   已创建 {i+1}/{initial_agent_count} 个Agent...")
    
    creation_time = time.time() - start_time
    logger.info(f"✅ 创建完成，耗时{creation_time:.2f}秒")
    logger.info(f"   Agent类型: {type(agents[0]).__name__}")
    logger.info(f"   Agent数量: {len(agents)}")
    
    # 验证Agent完整性
    sample_agent = agents[0]
    logger.info(f"\n📋 Agent完整性检查:")
    logger.info(f"   ✅ agent_id: {sample_agent.agent_id}")
    logger.info(f"   ✅ initial_capital: {sample_agent.initial_capital}")
    logger.info(f"   ✅ lineage: {type(sample_agent.lineage).__name__}")
    logger.info(f"   ✅ genome: {type(sample_agent.genome).__name__}")
    logger.info(f"   ✅ generation: {sample_agent.generation}")
    logger.info(f"   ✅ meta_genome: {type(sample_agent.meta_genome).__name__}")
    
    # ===== 4. 挂载双账簿系统（遵循铁律）⭐⭐⭐ =====
    logger.info(f"\n💰 挂载双账簿系统...")
    logger.info("   参见: prometheus/ledger/attach_accounts.py")
    
    # 导入账簿系统
    from prometheus.core.ledger_system import PublicLedger, AgentAccountSystem
    from prometheus.ledger.attach_accounts import attach_accounts
    
    # 创建公共账簿
    public_ledger = PublicLedger()
    logger.info("   ✅ PublicLedger已创建")
    
    # 为所有Agent挂载账户（幂等）
    attach_accounts(agents, public_ledger)
    logger.info(f"   ✅ 账户已挂载到{len(agents)}个Agent")
    
    # 验证挂载
    missing_account = [a for a in agents if not hasattr(a, 'account')]
    if missing_account:
        raise Exception(f"❌ {len(missing_account)}个Agent缺少account！")
    missing_private = [a for a in agents if not hasattr(a.account, 'private_ledger')]
    if missing_private:
        raise Exception(f"❌ {len(missing_private)}个Agent的account缺少private_ledger！")
    
    logger.info(f"   ✅ 验证完成：所有Agent都有account和private_ledger")
    logger.info(f"   ✅ 双账簿系统挂载成功⭐⭐⭐")
    
    # ===== 5. 创建Moirai v7（先创建，暂不传EvolutionManager）⭐⭐⭐ =====
    logger.info(f"\n⚖️ 创建MoiraiV7...")
    logger.info("   参见: docs/core_structures/evolution_manager_spec.md")
    
    # ⭐ 先创建MoiraiV7（暂时传入None作为evolution_manager）
    moirai = MoiraiV7(
        bulletin_board=bb,
        evolution_manager=None,  # 暂时为None，稍后注入
        initial_agents=agents  # ⭐ 传入初始agents
    )
    # 将public_ledger传递给Moirai（用于对账）
    moirai.public_ledger = public_ledger
    logger.info("✅ Moirai v7.0已初始化（暂未注入EvolutionManager）")
    
    # ===== 6. 创建EvolutionManager并注入⭐⭐⭐ =====
    logger.info(f"\n🧬 创建EvolutionManagerV5...")
    
    evolution_mgr = EvolutionManagerV5(
        moirai=moirai,  # ⭐ 传入MoiraiV7实例
        elite_ratio=0.2,
        elimination_ratio=0.3,
        capital_pool=None,
        fitness_mode='profit_factor',
        retirement_enabled=True,
        medal_system_enabled=True,
        immigration_enabled=False
    )
    logger.info("✅ EvolutionManagerV5已初始化")
    
    # ⭐ 将EvolutionManager注入MoiraiV7
    moirai.evolution_manager = evolution_mgr
    logger.info("✅ EvolutionManagerV5已注入MoiraiV7")
    logger.info(f"   访问agents: moirai.agents ⭐")
    logger.info(f"   Agent数量: {len(moirai.agents)}")
    
    # ===== 7. 运行测试主循环 =====
    logger.info(f"\n🔄 开始运行{total_cycles}个周期...")
    
    history = {
        'cycle': [],
        'scale': [],
        'agent_count': [],
        'risk_level': [],
        'S': [],
        'E': []
    }
    
    current_price = 50000.0
    
    for cycle in range(1, total_cycles + 1):
        
        if cycle % 10 == 1:
            logger.info(f"\n{'='*60}")
            logger.info(f"📅 周期 {cycle}/{total_cycles}")
            logger.info("="*60)
        
        # 模拟市场数据
        market_data = generate_market_data(cycle, market_scenario, current_price)
        current_price = market_data['price']
        
        # 模拟Agent交易（使用moirai.agents）
        simulate_agent_trading(moirai.agents, market_data, market_scenario)
        
        # 模拟摩擦数据
        friction_data = generate_friction_data(market_scenario, cycle)
        
        # 模拟死亡统计
        death_stats = calculate_death_stats(moirai.agents, market_scenario)
        
        # 发布到BulletinBoard
        bb.publish('world_signature', market_data)
        bb.publish('friction_data', friction_data)
        bb.publish('death_stats', death_stats)
        
        # Prophet决策周期
        prophet.run_decision_cycle()
        
        # Moirai执行周期
        moirai.run_cycle(cycle=cycle, current_price=current_price)
        
        # 记录历史
        announcement = bb.get('prophet_announcement')
        history['cycle'].append(cycle)
        history['scale'].append(moirai.current_scale)
        history['agent_count'].append(len(moirai.agents))  # ⭐ 使用moirai.agents
        history['risk_level'].append(announcement.get('risk_level', 'safe'))
        history['S'].append(announcement.get('S', 0.5))
        history['E'].append(announcement.get('E', 0.0))
        
        # 周期性日志
        if cycle % 10 == 0:
            logger.info(f"\n📊 周期{cycle}状态:")
            logger.info(f"   Agent数量: {len(moirai.agents)}")  # ⭐ 使用moirai.agents
            logger.info(f"   系统规模: {moirai.current_scale:.0%}")
            logger.info(f"   风险等级: {announcement.get('risk_level', 'safe')}")
            logger.info(f"   价格: ${current_price:.2f}")
    
    # ===== 7. 测试结果 =====
    logger.info(f"\n" + "="*80)
    logger.info("📊 测试结果汇总")
    logger.info("="*80)
    
    logger.info(f"\n✅ 使用真实AgentV5:")
    logger.info(f"   Agent类型: {type(moirai.agents[0] if moirai.agents else None).__name__}")  # ⭐ 使用moirai.agents
    logger.info(f"   创建方式: 按照数据字典（agent_v5_spec.md）")
    
    logger.info(f"\n系统规模变化:")
    logger.info(f"   初始: {history['scale'][0]:.0%}")
    logger.info(f"   最终: {history['scale'][-1]:.0%}")
    logger.info(f"   变化: {(history['scale'][-1] - history['scale'][0]):.0%}")
    
    logger.info(f"\nAgent数量变化:")
    logger.info(f"   初始: {history['agent_count'][0]}")
    logger.info(f"   最终: {history['agent_count'][-1]}")
    logger.info(f"   变化: {history['agent_count'][-1] - history['agent_count'][0]:+d}")
    
    logger.info(f"\n风险分布:")
    risk_counts = {}
    for r in history['risk_level']:
        risk_counts[r] = risk_counts.get(r, 0) + 1
    for risk, count in sorted(risk_counts.items()):
        logger.info(f"   {risk}: {count}次 ({count/len(history['risk_level'])*100:.1f}%)")
    
    # 数据库统计
    if exp_db:
        risk_summary = exp_db.get_risk_summary(run_id)
        logger.info(f"\n数据库统计:")
        logger.info(f"   总记录: {risk_summary['total']}")
        logger.info(f"   safe: {risk_summary['safe']}")
        logger.info(f"   warning: {risk_summary['warning']}")
        logger.info(f"   danger: {risk_summary['danger']}")
        logger.info(f"   critical: {risk_summary['critical']}")
    
    logger.info(f"\n✅ 测试完成！数据库: {db_path}")
    
    exp_db.close()
    
    return history, db_path


# ===== 辅助函数（与之前相同）=====

def generate_market_data(cycle: int, scenario: str, current_price: float) -> dict:
    """生成模拟市场数据"""
    import random
    
    if scenario == "mixed":
        if cycle <= 15:
            price_change = random.uniform(0.01, 0.02)
        elif cycle <= 30:
            price_change = random.uniform(-0.02, -0.01)
        else:
            price_change = random.uniform(-0.005, 0.005)
        
        current_price *= (1 + price_change)
        
        if cycle == 35:
            price_change = -0.15
            current_price *= (1 + price_change)
            logger.warning(f"🚨 黑天鹅事件！价格暴跌{price_change:.0%}")
        
        return {
            'price': current_price,
            'price_change_24h': price_change * 12,
            'volatility_24h': abs(price_change) * 2,
            'volume_ratio': 1.0 + random.uniform(-0.2, 0.2)
        }


def generate_friction_data(scenario: str, cycle: int) -> dict:
    """生成摩擦数据"""
    import random
    
    base_slippage = 0.001
    base_latency = 0.02
    base_fill_rate = 0.98
    
    if cycle == 35:
        return {
            'slippage': base_slippage * 10,
            'latency_norm': base_latency * 5,
            'fill_rate': 0.5
        }
    
    return {
        'slippage': base_slippage * random.uniform(0.8, 1.2),
        'latency_norm': base_latency * random.uniform(0.8, 1.2),
        'fill_rate': base_fill_rate * random.uniform(0.98, 1.0)
    }


def calculate_death_stats(agents, scenario: str) -> dict:
    """计算死亡统计"""
    if not agents:
        return {'abnormal_deaths': 0, 'total_agents': 1, 'abnormal_death_rate': 0.0}
    
    # ⭐ 使用getattr防止新生Agent缺属性
    abnormal_deaths = sum(1 for a in agents if getattr(a, 'total_roi', 0) < -0.2)
    
    return {
        'abnormal_deaths': abnormal_deaths,
        'total_agents': len(agents),
        'abnormal_death_rate': abnormal_deaths / len(agents) if len(agents) > 0 else 0.0
    }


def simulate_agent_trading(agents, market_data, scenario):
    """
    模拟Agent交易（通过账簿系统）⭐⭐⭐
    
    参见: prometheus/training/mock_training_school.py (execute_trade方法)
    使用agent.account.record_trade()标准方式
    """
    import random
    from prometheus.core.ledger_system import Role
    
    current_price = market_data['price']
    price_change = market_data['price_change_24h'] / 12
    
    for agent in agents:
        # 确保Agent有account（应该在挂载时已经完成）
        if not hasattr(agent, 'account'):
            logger.warning(f"Agent {agent.agent_id} 缺少account，跳过交易")
            continue
        
        # 30%概率交易
        if random.random() < 0.3:
            # 根据市场趋势决定交易方向
            if scenario == "mixed" and price_change > 0:
                direction_bias = 0.7  # 牛市偏向做多
            elif scenario == "mixed" and price_change < 0:
                direction_bias = 0.3  # 熊市偏向做空
            else:
                direction_bias = 0.5  # 震荡随机
            
            is_long = random.random() < direction_bias
            
            # 计算交易金额（10%仓位）
            position_size = agent.current_capital * 0.1
            amount = position_size / current_price if current_price > 0 else 0
            
            # 模拟滑点（0.05%）
            slippage = 0.0005
            if is_long:
                fill_price = current_price * (1 + slippage)
                trade_type = 'buy'
            else:
                fill_price = current_price * (1 - slippage)
                trade_type = 'sell'
            
            try:
                # ⭐⭐⭐ 通过账簿系统记录交易（标准方式）
                # 测试框架以Moirai身份调用（遵守权限规则）
                agent.account.record_trade(
                    trade_type=trade_type,
                    price=fill_price,
                    amount=amount,
                    confidence=0.5,
                    caller_role=Role.MOIRAI  # ✅ 测试框架扮演Moirai角色
                )
                
                # 从private_ledger获取最新PnL
                # total_pnl = realized_pnl + unrealized_pnl
                realized_pnl = agent.account.private_ledger.total_pnl
                unrealized_pnl = agent.account.private_ledger.get_unrealized_pnl(current_price)
                total_pnl = realized_pnl + unrealized_pnl
                
                agent.total_pnl = total_pnl
                agent.total_roi = total_pnl / agent.initial_capital if agent.initial_capital > 0 else 0
                
                # 更新current_capital（账簿系统会自动管理资金）
                agent.current_capital = agent.account.private_ledger.virtual_capital
                
            except Exception as e:
                logger.warning(f"Agent {agent.agent_id} 交易失败: {e}")


if __name__ == "__main__":
    """运行测试"""
    
    print("\n" + "🚀 " + "="*58)
    print("🚀 Prometheus v7.0 - 使用真实AgentV5测试")
    print("🚀 符合三大铁律 ✅")
    print("🚀 " + "="*58 + "\n")
    
    history, db_path = run_v7_test_with_real_agents(
        total_cycles=1000,  # ⭐ 长期测试：1000周期（约4天，假设1周期=5分钟）
        initial_agent_count=100,
        market_scenario="mixed"
    )
    
    print("\n" + "🏆 " + "="*58)
    print("🏆 测试完成！")
    print("🏆 " + "="*58 + "\n")
    
    print(f"📊 关键数据:")
    print(f"   数据库路径: {db_path}")
    print(f"   系统规模: {history['scale'][0]:.0%} → {history['scale'][-1]:.0%}")
    print(f"   Agent数量: {history['agent_count'][0]} → {history['agent_count'][-1]}")
    print(f"   使用真实AgentV5: ✅")
    print()

