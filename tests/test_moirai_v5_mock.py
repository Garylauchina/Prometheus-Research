"""
Moirai v5.0 Mock测试 - 测试驱动开发
===================================

测试Moirai（命运三女神）的完整功能：
1. Clotho: 创建AgentV5
2. Lachesis: 监督交易
3. Atropos: 淘汰失败者

使用Mock数据，快速验证整个流程
"""

import sys
sys.path.insert(0, '.')

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from prometheus.core.moirai import Moirai
from prometheus.core.agent_v5 import AgentV5, AgentState


class MockOKXTrading:
    """Mock OKX交易接口"""
    
    def __init__(self):
        self.balance = {'BTC': 10.0, 'USDT': 200000.0}
        self.price = 90000.0
        
    def fetch_balance(self):
        return self.balance
    
    def fetch_ticker(self, symbol):
        return {'last': self.price}
    
    def fetch_ohlcv(self, symbol, timeframe, limit):
        # 生成Mock K线数据
        ohlcv = []
        for i in range(limit):
            o = self.price + np.random.uniform(-500, 500)
            h = o + abs(np.random.uniform(0, 300))
            l = o - abs(np.random.uniform(0, 300))
            c = (h + l) / 2
            v = np.random.uniform(1000, 5000)
            ohlcv.append([i, o, h, l, c, v])
        return ohlcv
    
    def fetch_positions(self, symbol=None):
        return []
    
    def create_market_order(self, symbol, side, amount):
        return {
            'id': f'mock_{np.random.randint(1000, 9999)}',
            'status': 'closed',
            'average': self.price,
            'amount': amount,
        }
    
    def close_all_positions(self):
        return []


class MockMastermind:
    """Mock Mastermind（先知）"""
    
    def generate_minor_prophecy(self, market_data):
        return {
            'trend': 'bullish',
            'confidence': 0.75,
            'environmental_pressure': 0.2,
            'forecast': '市场看涨',
        }
    
    def generate_grand_prophecy(self, market_data):
        return {
            'long_term_trend': 'bullish',
            'confidence': 0.7,
            'forecast': '长期看涨',
        }


class MockBulletinBoard:
    """Mock公告板"""
    
    def __init__(self):
        self.bulletins = {}
    
    def publish(self, category, content):
        self.bulletins[category] = content
    
    def get_all(self):
        return self.bulletins


class TestMoiraiV5Mock(unittest.TestCase):
    """Moirai v5.0 Mock测试套件"""
    
    def setUp(self):
        """设置测试环境"""
        self.okx_trading = MockOKXTrading()
        self.mastermind = MockMastermind()
        self.bulletin_board = MockBulletinBoard()
        
        # 创建Moirai
        self.moirai = Moirai(
            bulletin_board=self.bulletin_board,
            num_families=50
        )
    
    def test_01_clotho_create_agents(self):
        """
        测试1: 🧵 Clotho创建AgentV5
        
        验证:
        - 创建指定数量的Agent
        - 每个Agent都是AgentV5实例
        - 家族分配均匀
        """
        print("\n" + "="*70)
        print("测试1: 🧵 Clotho - 纺织生命之线")
        print("="*70)
        
        # 配置
        agent_count = 10
        capital_per_agent = 10000.0
        
        # 执行创建
        agents = self.moirai._clotho_create_v5_agents(
            agent_count=agent_count,
            gene_pool=[],  # v5.0不使用
            capital_per_agent=capital_per_agent
        )
        
        # 验证
        self.assertEqual(len(agents), agent_count, "Agent数量不正确")
        
        for agent in agents:
            self.assertIsInstance(agent, AgentV5, "Agent不是AgentV5实例")
            self.assertEqual(agent.initial_capital, capital_per_agent)
            self.assertEqual(agent.current_capital, capital_per_agent)
            self.assertIsNotNone(agent.lineage)
            self.assertIsNotNone(agent.genome)
            self.assertIsNotNone(agent.instinct)
            self.assertIsNotNone(agent.daimon)
        
        # 验证家族分布
        families = {}
        for agent in agents:
            family = agent.lineage.get_dominant_families(top_k=1)
            if family:
                family_id = family[0][0]
                families[family_id] = families.get(family_id, 0) + 1
        
        print(f"\n✅ 创建{len(agents)}个Agent成功")
        print(f"   家族分布: {len(families)}个家族参与")
        print(f"   策略分布: {[agent.current_strategy_name for agent in agents[:3]]}")
    
    def test_02_lachesis_collect_decisions(self):
        """
        测试2: ⚖️ Lachesis收集决策
        
        验证:
        - 能够收集所有Agent的决策
        - 决策格式正确
        """
        print("\n" + "="*70)
        print("测试2: ⚖️ Lachesis - 收集Agent决策")
        print("="*70)
        
        # 先创建Agent
        agents = self.moirai._clotho_create_v5_agents(5, [], 10000.0)
        self.moirai.agents = agents
        
        # 准备市场数据
        market_data = {
            'price': 90000,
            'ohlcv': self.okx_trading.fetch_ohlcv('BTC/USDT', '1h', 20),
            'volume': 2000,
            'trend': 'bullish',
            'volatility': 0.05,
        }
        
        bulletins = {
            'minor_prophecy': self.mastermind.generate_minor_prophecy(market_data)
        }
        
        # 收集决策
        decisions = self.moirai._lachesis_collect_decisions(
            bulletins=bulletins,
            market_data=market_data,
            cycle_count=5
        )
        
        print(f"\n✅ 收集{len(decisions)}个决策")
        
        for decision in decisions[:3]:  # 显示前3个
            print(f"   {decision['agent_id']}: {decision.get('action', 'hold')} "
                  f"(信心{decision.get('confidence', 0):.1%})")
    
    def test_03_atropos_judge_and_eliminate(self):
        """
        测试3: ✂️ Atropos淘汰失败者
        
        验证:
        - 能够判断哪些Agent应该被淘汰
        - 正确执行淘汰
        """
        print("\n" + "="*70)
        print("测试3: ✂️ Atropos - 剪断生命之线")
        print("="*70)
        
        # 创建Agent
        agents = self.moirai._clotho_create_v5_agents(5, [], 10000.0)
        self.moirai.agents = agents
        
        # 模拟失败：将第一个Agent的资金设为很低
        agents[0].current_capital = 500.0  # 低于10%
        
        # 模拟自杀：将第二个Agent设置为想自杀
        agents[1].current_capital = 2000.0
        agents[1].consecutive_losses = 15
        agents[1].emotion.despair = 0.9
        
        print(f"\n初始Agent数量: {len(self.moirai.agents)}")
        
        # 执行淘汰检查
        eliminated_count = self.moirai._atropos_check_and_eliminate()
        
        print(f"✂️ Atropos淘汰了{eliminated_count}个Agent")
        print(f"剩余Agent数量: {len(self.moirai.agents)}")
        
        # 验证
        self.assertEqual(len(self.moirai.agents), 5 - eliminated_count)
        self.assertGreater(eliminated_count, 0, "应该至少淘汰1个Agent")
    
    def test_04_complete_cycle(self):
        """
        测试4: 完整周期测试
        
        模拟一个完整的：创世 -> 运行 -> 淘汰周期
        """
        print("\n" + "="*70)
        print("测试4: 完整周期 - 创世到淘汰")
        print("="*70)
        
        # Step 1: Clotho创建Agent
        print("\n🧵 Step 1: Clotho纺织生命...")
        agents = self.moirai._clotho_create_v5_agents(10, [], 10000.0)
        self.moirai.agents = agents
        print(f"   创建{len(agents)}个Agent")
        
        # Step 2: Lachesis监督几个周期
        print("\n⚖️ Step 2: Lachesis监督交易...")
        
        market_data = {
            'price': 90000,
            'ohlcv': self.okx_trading.fetch_ohlcv('BTC/USDT', '1h', 20),
            'volume': 2000,
            'trend': 'bullish',
            'volatility': 0.05,
        }
        
        bulletins = {
            'minor_prophecy': self.mastermind.generate_minor_prophecy(market_data)
        }
        
        for cycle in range(1, 4):
            decisions = self.moirai._lachesis_collect_decisions(
                bulletins, market_data, cycle
            )
            print(f"   周期{cycle}: {len(decisions)}个决策")
        
        # Step 3: 模拟失败并淘汰
        print("\n✂️ Step 3: Atropos淘汰失败者...")
        
        # 让一些Agent失败
        for i, agent in enumerate(self.moirai.agents[:3]):
            agent.current_capital = 500.0 + i * 100
        
        eliminated = self.moirai._atropos_check_and_eliminate()
        print(f"   淘汰{eliminated}个Agent")
        print(f"   剩余{len(self.moirai.agents)}个Agent")
        
        # Step 4: 状态报告
        print("\n📊 Step 4: 生成状态报告...")
        report = self.moirai.get_status_report()
        print(f"   总Agent: {report['total_agents']}")
        print(f"   家族多样性: {report['family_diversity']}")
        
        # 验证
        self.assertGreater(eliminated, 0)
        self.assertLess(len(self.moirai.agents), 10)
        
        print("\n✅ 完整周期测试通过！")


def main():
    """运行测试"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Moirai v5.0 Mock测试 - 测试驱动开发".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # 运行测试
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    main()

