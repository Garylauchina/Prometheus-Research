"""
Simple Evolution Demo - 简单进化系统演示

展示如何使用Evolution模块的核心功能
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolution import EnhancedCapitalPool, EnvironmentalPressure
import random


class MockAgent:
    """模拟Agent类"""
    def __init__(self, agent_id, capital, roi=0.0):
        self.id = agent_id
        self.capital = capital
        self.initial_capital = capital
        self.roi = roi
        self.is_alive = True
        self.trade_count = 0
        self.age = 0
    
    def update(self):
        """模拟更新"""
        self.age += 1
        # 随机ROI变化
        self.roi += random.uniform(-0.05, 0.05)
        self.capital = self.initial_capital * (1 + self.roi)
        self.trade_count += random.randint(0, 2)


def demo_capital_pool():
    """演示资金池功能"""
    print("\n" + "="*60)
    print("📊 资金池系统演示")
    print("="*60)
    
    # 创建资金池
    pool = EnhancedCapitalPool(initial_capital=10000)
    print(f"\n初始状态: {pool}")
    
    # 场景1: 分配资金给3个Agent
    print("\n场景1: 创建3个Agent")
    for i in range(3):
        success = pool.allocate_to_agent(2000)
        print(f"  Agent {i+1} 分配: {'成功' if success else '失败'}")
    print(f"  {pool}")
    
    # 场景2: Agent死亡，回收资金
    print("\n场景2: Agent 1死亡")
    recycled = pool.recycle_from_death(1500, recovery_rate=1.0)
    print(f"  回收资金: ${recycled:,.2f}")
    print(f"  {pool}")
    
    # 场景3: 繁殖资助
    print("\n场景3: 资助新Agent繁殖")
    subsidy = pool.subsidize_reproduction(800)
    print(f"  资助金额: ${subsidy:,.2f}")
    print(f"  {pool}")
    
    # 查看性能指标
    print("\n性能指标:")
    metrics = pool.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value:.2%}")


def demo_environmental_pressure():
    """演示环境压力系统"""
    print("\n" + "="*60)
    print("🌡️ 环境压力系统演示")
    print("="*60)
    
    pressure = EnvironmentalPressure()
    
    # 场景1: 平静市场（繁荣期）
    print("\n场景1: 平静市场")
    market1 = {
        'high_vol': 0.2, 
        'extreme_high_vol': 0.0,
        'fear': 0.1, 
        'extreme_fear': 0.0
    }
    agents1 = [MockAgent(i, 2000, 0.08) for i in range(15)]
    pool1 = {'utilization': 0.65}
    
    p1 = pressure.update(market1, agents1, pool1)
    phase1 = pressure.get_phase()
    print(f"  压力值: {p1:.2%}")
    print(f"  阶段: {phase1[1]}")
    
    # 场景2: 危机市场
    print("\n场景2: 危机市场")
    market2 = {
        'high_vol': 0.7, 
        'extreme_high_vol': 0.5,
        'fear': 0.6, 
        'extreme_fear': 0.8
    }
    agents2 = [MockAgent(i, 1500, -0.15) for i in range(15)]
    for i in range(7, 15):
        agents2[i].is_alive = False  # 只有7个存活
    pool2 = {'utilization': 0.95}
    
    p2 = pressure.update(market2, agents2, pool2)
    phase2 = pressure.get_phase()
    print(f"  压力值: {p2:.2%}")
    print(f"  阶段: {phase2[1]}")
    
    # 场景3: 配置调整
    print("\n场景3: 根据压力调整配置")
    base_config = {
        'min_roi': 0.05,
        'min_trades': 2,
        'pool_subsidy_ratio': 0.30
    }
    
    adjusted = pressure.adjust_reproduction_config(base_config)
    print(f"  原配置: ROI>{base_config['min_roi']:.1%}, "
          f"交易>={base_config['min_trades']}, "
          f"资助{base_config['pool_subsidy_ratio']:.0%}")
    print(f"  调整后: ROI>{adjusted['min_roi']:.1%}, "
          f"交易>={adjusted['min_trades']}, "
          f"资助{adjusted['pool_subsidy_ratio']:.0%}")


def demo_integrated_system():
    """演示完整集成"""
    print("\n" + "="*60)
    print("🚀 完整系统集成演示")
    print("="*60)
    
    # 初始化
    pool = EnhancedCapitalPool(10000)
    pressure = EnvironmentalPressure()
    agents = []
    
    # 创建初始Agent
    print("\n创建5个初始Agent")
    for i in range(5):
        if pool.allocate_to_agent(1500):
            agent = MockAgent(i, 1500)
            agents.append(agent)
            print(f"  Agent {i} 创建成功")
    
    # 模拟10个周期
    print("\n开始模拟10个周期...")
    for cycle in range(10):
        print(f"\n--- 周期 {cycle + 1} ---")
        
        # 更新所有Agent
        for agent in agents:
            if agent.is_alive:
                agent.update()
        
        # 模拟市场特征
        market = {
            'high_vol': random.uniform(0.2, 0.7),
            'extreme_high_vol': random.uniform(0, 0.3),
            'fear': random.uniform(0.1, 0.6),
            'extreme_fear': random.uniform(0, 0.4)
        }
        
        # 更新压力
        p = pressure.update(market, agents, pool.get_status())
        phase = pressure.get_phase()
        
        print(f"压力: {p:.2%}, {phase[1]}")
        print(f"存活Agent: {sum(1 for a in agents if a.is_alive)}")
        print(f"平均ROI: {sum(a.roi for a in agents if a.is_alive) / sum(1 for a in agents if a.is_alive):.2%}")
        
        # 每5个周期进行进化
        if (cycle + 1) % 5 == 0:
            print("\n🧬 进化周期!")
            
            # 死亡检查
            for agent in agents:
                if agent.is_alive and agent.roi < -0.20:
                    recycled = pool.recycle_from_death(agent.capital)
                    agent.is_alive = False
                    print(f"  💀 Agent {agent.id} 死亡，回收${recycled:.2f}")
            
            # 繁殖检查
            config = pressure.adjust_reproduction_config({
                'min_roi': 0.05,
                'min_trades': 3,
                'pool_subsidy_ratio': 0.30
            })
            
            for agent in agents:
                if agent.is_alive and agent.roi > config['min_roi'] and agent.trade_count >= config['min_trades']:
                    # 父代转移
                    parent_transfer = agent.capital * 0.20
                    # 资金池资助
                    subsidy = pool.subsidize_reproduction(agent.initial_capital * config['pool_subsidy_ratio'])
                    
                    if subsidy > 0:
                        new_capital = parent_transfer + subsidy
                        new_agent = MockAgent(len(agents), new_capital, 0)
                        agents.append(new_agent)
                        agent.capital -= parent_transfer
                        print(f"  🐣 Agent {len(agents)-1} 诞生! 资金: ${new_capital:.2f}")
    
    # 最终状态
    print("\n" + "="*60)
    print("📊 最终状态")
    print("="*60)
    print(f"\n资金池: {pool}")
    print(f"\nAgent统计:")
    print(f"  总数: {len(agents)}")
    print(f"  存活: {sum(1 for a in agents if a.is_alive)}")
    print(f"  死亡: {sum(1 for a in agents if not a.is_alive)}")
    
    metrics = pool.get_metrics()
    print(f"\n资金池指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.2%}")


if __name__ == "__main__":
    print("\n🎮 Evolution System 演示程序")
    print("="*60)
    
    # 运行所有演示
    demo_capital_pool()
    demo_environmental_pressure()
    demo_integrated_system()
    
    print("\n" + "="*60)
    print("✅ 演示完成!")
    print("="*60)

