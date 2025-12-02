"""
测试市场状态分析器
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prometheus.core.indicator_calculator import IndicatorCalculator
from prometheus.core.market_state_analyzer import (
    MarketStateAnalyzer,
    TrendState,
    MomentumState,
    VolatilityState
)


class TestMarketStateAnalyzer(unittest.TestCase):
    """市场状态分析器测试"""
    
    def setUp(self):
        """初始化"""
        self.analyzer = MarketStateAnalyzer()
        self.indicator_calculator = IndicatorCalculator()
    
    def _generate_market_data(self, trend_type='up', periods=100):
        """
        生成不同类型的市场数据
        
        Args:
            trend_type: 'up', 'down', 'ranging'
        """
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        base_price = 50000
        
        if trend_type == 'up':
            # 明显上升趋势
            trend = np.linspace(0, 5000, periods)
            noise = np.random.randn(periods) * 50
        elif trend_type == 'down':
            # 明显下降趋势
            trend = np.linspace(0, -5000, periods)
            noise = np.random.randn(periods) * 50
        else:  # ranging
            # 震荡市场
            trend = np.sin(np.linspace(0, 8 * np.pi, periods)) * 500
            noise = np.random.randn(periods) * 100
        
        close = base_price + trend + noise
        
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
    
    def test_analyze_uptrend(self):
        """测试上升趋势分析"""
        data = self._generate_market_data('up')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        # 应该识别为上升趋势
        self.assertIn(state.trend, [TrendState.STRONG_UPTREND, TrendState.WEAK_UPTREND])
        
        print(f"\n✅ 上升趋势识别: {state.trend.value}")
        print(f"   趋势强度: {state.trend_strength:.2f}")
    
    def test_analyze_downtrend(self):
        """测试下降趋势分析"""
        data = self._generate_market_data('down')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        # 应该识别为下降趋势
        self.assertIn(state.trend, [TrendState.STRONG_DOWNTREND, TrendState.WEAK_DOWNTREND])
        
        print(f"\n✅ 下降趋势识别: {state.trend.value}")
        print(f"   趋势强度: {state.trend_strength:.2f}")
    
    def test_analyze_ranging(self):
        """测试震荡市场分析"""
        data = self._generate_market_data('ranging')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        print(f"\n✅ 震荡市场识别: {state.trend.value}")
        print(f"   趋势强度: {state.trend_strength:.2f}")
    
    def test_market_difficulty_range(self):
        """测试市场难度在合理范围"""
        data = self._generate_market_data('up')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        self.assertGreaterEqual(state.market_difficulty, 0)
        self.assertLessEqual(state.market_difficulty, 1)
        
        print(f"\n✅ 市场难度范围正确: {state.market_difficulty:.2f}")
    
    def test_opportunity_score_range(self):
        """测试机会评分在合理范围"""
        data = self._generate_market_data('up')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        self.assertGreaterEqual(state.opportunity_score, 0)
        self.assertLessEqual(state.opportunity_score, 1)
        
        print(f"\n✅ 机会评分范围正确: {state.opportunity_score:.2f}")
    
    def test_recommendation_generated(self):
        """测试建议生成"""
        data = self._generate_market_data('up')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        self.assertIsNotNone(state.recommendation)
        self.assertGreater(len(state.recommendation), 0)
        
        print(f"\n✅ 建议生成成功: {state.recommendation}")
    
    def test_state_summary(self):
        """测试状态摘要"""
        data = self._generate_market_data('up')
        indicators = self.indicator_calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        summary = self.analyzer.get_state_summary(state)
        
        self.assertIn('trend', summary)
        self.assertIn('momentum', summary)
        self.assertIn('volatility', summary)
        self.assertIn('difficulty', summary)
        self.assertIn('opportunity', summary)
        
        print(f"\n✅ 状态摘要生成成功:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    def test_complete_analysis_flow(self):
        """测试完整分析流程"""
        print(f"\n{'='*60}")
        print("完整分析流程测试")
        print(f"{'='*60}")
        
        for trend_type in ['up', 'down', 'ranging']:
            print(f"\n--- {trend_type.upper()} 市场 ---")
            
            data = self._generate_market_data(trend_type)
            indicators = self.indicator_calculator.calculate_all(data)
            state = self.analyzer.analyze(indicators)
            
            print(f"趋势: {state.trend.value} (强度: {state.trend_strength:.2f})")
            print(f"动量: {state.momentum.value} (评分: {state.momentum_score:.2f})")
            print(f"波动率: {state.volatility.value} (评分: {state.volatility_score:.2f})")
            print(f"市场难度: {state.market_difficulty:.2f}")
            print(f"机会评分: {state.opportunity_score:.2f}")
            print(f"建议: {state.recommendation}")
            
            # 基本验证
            self.assertIsInstance(state.trend, TrendState)
            self.assertIsInstance(state.momentum, MomentumState)
            self.assertIsInstance(state.volatility, VolatilityState)


class TestMarketDifficultyCalculation(unittest.TestCase):
    """市场难度计算测试"""
    
    def setUp(self):
        self.analyzer = MarketStateAnalyzer()
        self.calculator = IndicatorCalculator()
    
    def test_high_volatility_increases_difficulty(self):
        """测试高波动增加市场难度"""
        # 生成高波动数据
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        
        # 高波动
        close = 50000 + np.random.randn(100).cumsum() * 500  # 大幅波动
        
        data = pd.DataFrame({
            'open': close + np.random.randn(100) * 200,
            'high': close + abs(np.random.randn(100) * 400),
            'low': close - abs(np.random.randn(100) * 400),
            'close': close,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        indicators = self.calculator.calculate_all(data)
        state = self.analyzer.analyze(indicators)
        
        print(f"\n✅ 高波动市场难度: {state.market_difficulty:.2f}")
        print(f"   波动率状态: {state.volatility.value}")
        
        # 高波动应该导致较高难度
        self.assertGreater(state.market_difficulty, 0.3)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMarketStateAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketDifficultyCalculation))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试总结")
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

