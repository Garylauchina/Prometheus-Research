"""
Prometheus v4.0 - 三层架构集成测试

测试Mastermind -> Supervisor -> Agent的完整数据流
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prometheus.core import (
    Mastermind,
    Supervisor,
    AgentV4,
    BulletinBoardV4,
    Valhalla,
    TradingPermissionSystem,
)


class TestThreeLayerArchitecture(unittest.TestCase):
    """三层架构集成测试"""
    
    def setUp(self):
        """初始化系统"""
        # 公告板
        self.bulletin_board = BulletinBoardV4()
        
        # 英灵殿
        self.valhalla = Valhalla()
        
        # 权限系统
        self.permission_system = TradingPermissionSystem()
        
        # 监督者
        self.supervisor = Supervisor(
            bulletin_board=self.bulletin_board,
            valhalla=self.valhalla,
            trading_permission_system=self.permission_system
        )
        
        # 主脑
        self.mastermind = Mastermind(
            initial_capital=100000,
            bulletin_board=self.bulletin_board
        )
        
        # Agent
        self.agents = []
        for i in range(3):
            agent = AgentV4(
                agent_id=f"TestAgent{i+1:03d}",
                initial_capital=10000,
                bulletin_board=self.bulletin_board,
                permission_system=self.permission_system
            )
            self.agents.append(agent)
            self.supervisor.register_agent(agent)
    
    def _generate_market_data(self):
        """生成测试市场数据"""
        np.random.seed(42)
        periods = 100
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        close = 50000 + np.linspace(0, 2000, periods) + np.random.randn(periods).cumsum() * 100
        
        data = pd.DataFrame({
            'open': close + np.random.randn(periods) * 50,
            'high': close + abs(np.random.randn(periods) * 100),
            'low': close - abs(np.random.randn(periods) * 100),
            'close': close,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        return data
    
    def test_mastermind_to_agent_flow(self):
        """测试Mastermind → 公告板 → Agent数据流"""
        print(f"\n{'='*60}")
        print("测试Mastermind → Agent数据流")
        print(f"{'='*60}")
        
        # 1. Mastermind发布战略公告
        print("\n1. Mastermind发布战略公告")
        self.mastermind.announce_strategy(
            strategy_type='conservative',
            parameters={
                'max_leverage': 2,
                'max_position': 0.3
            },
            reason='测试'
        )
        
        # 验证公告板有公告
        strategic_bulletins = self.bulletin_board.get_latest('strategic', count=1)
        self.assertEqual(len(strategic_bulletins), 1)
        print("   ✅ 战略公告已发布")
        
        # 2. Agent读取公告
        print("\n2. Agent读取公告")
        for agent in self.agents:
            bulletins = agent.read_bulletins(limit=5)
            self.assertGreater(len(bulletins), 0)
            print(f"   ✅ {agent.agent_id}读取到{len(bulletins)}条公告")
        
        # 3. Agent解读公告
        print("\n3. Agent解读公告")
        agent = self.agents[0]
        bulletins = agent.read_bulletins(limit=1)
        interpretation = agent.interpret_bulletin(bulletins[0])
        
        self.assertIn('accept', interpretation)
        self.assertIn('confidence', interpretation)
        self.assertIn('action', interpretation)
        
        print(f"   解读结果:")
        print(f"   - 是否接受: {interpretation['accept']}")
        print(f"   - 信心度: {interpretation['confidence']:.2f}")
        print(f"   - 行动: {interpretation['action']}")
    
    def test_supervisor_to_agent_flow(self):
        """测试Supervisor → 公告板 → Agent数据流"""
        print(f"\n{'='*60}")
        print("测试Supervisor → Agent数据流")
        print(f"{'='*60}")
        
        # 1. Supervisor进行综合监控
        print("\n1. Supervisor进行综合监控")
        market_data = self._generate_market_data()
        self.supervisor.comprehensive_monitoring(market_data)
        
        # 验证市场公告
        market_bulletins = self.bulletin_board.get_latest('market', count=1)
        self.assertGreater(len(market_bulletins), 0)
        print("   ✅ 市场公告已发布")
        
        # 验证系统公告
        system_bulletins = self.bulletin_board.get_latest('system', count=1)
        self.assertGreater(len(system_bulletins), 0)
        print("   ✅ 系统公告已发布")
        
        # 2. Agent读取公告
        print("\n2. Agent读取公告")
        agent = self.agents[0]
        bulletins = agent.read_bulletins(limit=10)
        
        # 应该有市场和系统公告
        has_market = any(b['tier'] == 'market' for b in bulletins)
        has_system = any(b['tier'] == 'system' for b in bulletins)
        
        self.assertTrue(has_market)
        self.assertTrue(has_system)
        
        print(f"   ✅ Agent读取到市场公告: {has_market}")
        print(f"   ✅ Agent读取到系统公告: {has_system}")
    
    def test_complete_decision_flow(self):
        """测试完整决策流程"""
        print(f"\n{'='*60}")
        print("测试完整决策流程")
        print(f"{'='*60}")
        
        # 1. Mastermind发布战略
        print("\n1. Mastermind发布战略")
        self.mastermind.announce_strategy(
            strategy_type='aggressive',
            parameters={'max_leverage': 5},
            reason='牛市来临'
        )
        
        # 2. Supervisor分析市场
        print("\n2. Supervisor分析市场")
        market_data = self._generate_market_data()
        self.supervisor.comprehensive_monitoring(market_data)
        
        # 3. Agent综合决策
        print("\n3. Agent综合决策")
        agent = self.agents[0]
        decision = agent.process_bulletins_and_decide()
        
        self.assertIn('decision', decision)
        self.assertIn('action', decision)
        self.assertIn('reason', decision)
        
        print(f"   决策结果:")
        print(f"   - 决策类型: {decision['decision']}")
        print(f"   - 行动: {decision['action']}")
        print(f"   - 原因: {decision['reason']}")
        
        if 'accepted_count' in decision:
            print(f"   - 接受公告: {decision['accepted_count']}/{decision['total_count']}")
    
    def test_market_analysis_integration(self):
        """测试市场分析整合"""
        print(f"\n{'='*60}")
        print("测试市场分析整合")
        print(f"{'='*60}")
        
        market_data = self._generate_market_data()
        
        # Supervisor综合监控
        self.supervisor.comprehensive_monitoring(market_data)
        
        # 验证市场指标
        self.assertIsNotNone(self.supervisor.current_indicators)
        self.assertIsNotNone(self.supervisor.current_market_state)
        
        print("\n市场状态:")
        state = self.supervisor.current_market_state
        print(f"  趋势: {state.trend.value}")
        print(f"  动量: {state.momentum.value}")
        print(f"  波动率: {state.volatility.value}")
        print(f"  市场难度: {state.market_difficulty:.2f}")
        print(f"  机会评分: {state.opportunity_score:.2f}")
        
        # 验证环境压力
        self.assertGreaterEqual(self.supervisor.environment_pressure, 0)
        self.assertLessEqual(self.supervisor.environment_pressure, 1)
        
        print(f"\n环境压力: {self.supervisor.environment_pressure:.2f}")
    
    def test_agent_permission_system(self):
        """测试Agent权限系统"""
        print(f"\n{'='*60}")
        print("测试Agent权限系统")
        print(f"{'='*60}")
        
        agent = self.agents[0]
        
        # 初始权限
        initial_level = agent.permission_level
        print(f"\n初始权限: {initial_level.value}")
        
        # 模拟交易表现
        agent.trade_count = 20
        agent.win_count = 15
        agent.total_pnl = 2000
        
        # Supervisor监控
        market_data = self._generate_market_data()
        self.supervisor.comprehensive_monitoring(market_data)
        
        print(f"交易表现: {agent.win_count}/{agent.trade_count} 胜, PnL={agent.total_pnl}")


class TestSupervisorIntegration(unittest.TestCase):
    """Supervisor集成测试"""
    
    def setUp(self):
        """初始化"""
        self.bulletin_board = BulletinBoardV4()
        self.valhalla = Valhalla()
        self.permission_system = TradingPermissionSystem()
        
        self.supervisor = Supervisor(
            bulletin_board=self.bulletin_board,
            valhalla=self.valhalla,
            trading_permission_system=self.permission_system
        )
        
        # 创建测试Agent
        self.agents = []
        for i in range(5):
            agent = AgentV4(
                agent_id=f"Agent{i+1:03d}",
                initial_capital=10000,
                bulletin_board=self.bulletin_board
            )
            self.agents.append(agent)
            self.supervisor.register_agent(agent)
    
    def _generate_market_data(self):
        """生成市场数据"""
        np.random.seed(42)
        periods = 100
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        close = 50000 + np.linspace(0, 2000, periods) + np.random.randn(periods).cumsum() * 100
        
        data = pd.DataFrame({
            'open': close + np.random.randn(periods) * 50,
            'high': close + abs(np.random.randn(periods) * 100),
            'low': close - abs(np.random.randn(periods) * 100),
            'close': close,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        return data
    
    def test_comprehensive_monitoring(self):
        """测试综合监控"""
        print(f"\n{'='*60}")
        print("测试Supervisor综合监控")
        print(f"{'='*60}")
        
        market_data = self._generate_market_data()
        
        # 执行综合监控
        self.supervisor.comprehensive_monitoring(market_data)
        
        # 验证市场分析完成
        self.assertIsNotNone(self.supervisor.current_indicators)
        self.assertIsNotNone(self.supervisor.current_market_state)
        
        print("\n✅ 市场分析完成")
        print(f"   趋势: {self.supervisor.current_market_state.trend.value}")
        
        # 验证环境压力计算
        self.assertGreaterEqual(self.supervisor.environment_pressure, 0)
        self.assertLessEqual(self.supervisor.environment_pressure, 1)
        
        print(f"\n✅ 环境压力: {self.supervisor.environment_pressure:.2f}")
        
        # 验证公告发布
        market_bulletins = self.bulletin_board.get_latest('market', count=1)
        system_bulletins = self.bulletin_board.get_latest('system', count=1)
        
        self.assertGreater(len(market_bulletins), 0)
        self.assertGreater(len(system_bulletins), 0)
        
        print("\n✅ 公告已发布")
        print(f"   市场公告: {len(market_bulletins)}条")
        print(f"   系统公告: {len(system_bulletins)}条")


class TestEndToEndScenarios(unittest.TestCase):
    """端到端场景测试"""
    
    def test_complete_trading_cycle(self):
        """测试完整交易周期"""
        print(f"\n{'='*60}")
        print("端到端场景：完整交易周期")
        print(f"{'='*60}")
        
        # 初始化系统
        bulletin_board = BulletinBoardV4()
        supervisor = Supervisor(bulletin_board=bulletin_board)
        mastermind = Mastermind(bulletin_board=bulletin_board)
        
        # 创建Agent
        agent = AgentV4(
            agent_id="Trader001",
            initial_capital=10000,
            bulletin_board=bulletin_board
        )
        supervisor.register_agent(agent)
        
        # 生成市场数据
        np.random.seed(42)
        periods = 100
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        close = 50000 + np.linspace(0, 2000, periods) + np.random.randn(periods).cumsum() * 100
        
        market_data = pd.DataFrame({
            'open': close + np.random.randn(periods) * 50,
            'high': close + abs(np.random.randn(periods) * 100),
            'low': close - abs(np.random.randn(periods) * 100),
            'close': close,
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        market_data['high'] = market_data[['open', 'high', 'close']].max(axis=1)
        market_data['low'] = market_data[['open', 'low', 'close']].min(axis=1)
        
        # 完整流程
        print("\n【步骤1】Mastermind制定策略")
        mastermind.announce_strategy(
            strategy_type='balanced',
            parameters={'max_leverage': 3},
            reason='平衡市场策略'
        )
        print("   ✅ 战略已发布")
        
        print("\n【步骤2】Supervisor分析市场")
        supervisor.comprehensive_monitoring(market_data)
        print("   ✅ 市场分析完成")
        print(f"   市场难度: {supervisor.current_market_state.market_difficulty:.2f}")
        print(f"   环境压力: {supervisor.environment_pressure:.2f}")
        
        print("\n【步骤3】Agent读取公告")
        bulletins = agent.read_bulletins(limit=10)
        print(f"   ✅ 读取{len(bulletins)}条公告")
        
        print("\n【步骤4】Agent做出决策")
        decision = agent.process_bulletins_and_decide()
        print(f"   ✅ 决策: {decision['decision']}")
        print(f"   行动: {decision['action']}")
        print(f"   原因: {decision['reason']}")
        
        # 验证
        self.assertEqual(len(bulletins), 3)  # 战略+市场+系统
        self.assertIn(decision['decision'], ['bulletin_guided', 'all_rejected', 'no_info'])
        
        print("\n✅ 完整交易周期测试通过")


def run_tests():
    """运行所有集成测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestThreeLayerArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestSupervisorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("集成测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

