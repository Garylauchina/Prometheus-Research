"""
测试技术指标计算器
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prometheus.core.indicator_calculator import IndicatorCalculator, TechnicalIndicators


class TestIndicatorCalculator(unittest.TestCase):
    """技术指标计算器测试"""
    
    def setUp(self):
        """初始化测试数据"""
        self.calculator = IndicatorCalculator()
        self.market_data = self._generate_test_data()
    
    def _generate_test_data(self, periods=100):
        """生成测试用市场数据"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        # 生成带趋势的价格
        base_price = 50000
        trend = np.linspace(0, 2000, periods)
        noise = np.random.randn(periods).cumsum() * 100
        
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
    
    def test_calculate_all(self):
        """测试计算所有指标"""
        indicators = self.calculator.calculate_all(self.market_data)
        
        # 验证返回类型
        self.assertIsInstance(indicators, TechnicalIndicators)
        
        # 验证各个指标存在
        self.assertIn('ADX', indicators.trend)
        self.assertIn('RSI', indicators.momentum)
        self.assertIn('ATR', indicators.volatility)
        self.assertIn('OBV', indicators.volume)
        
        print(f"\n✅ 所有指标计算成功")
    
    def test_rsi_range(self):
        """测试RSI在合理范围内"""
        indicators = self.calculator.calculate_all(self.market_data)
        rsi = indicators.momentum['RSI']
        
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
        
        print(f"\n✅ RSI范围验证通过: {rsi:.2f}")
    
    def test_adx_range(self):
        """测试ADX在合理范围内"""
        indicators = self.calculator.calculate_all(self.market_data)
        adx = indicators.trend['ADX']
        
        self.assertGreaterEqual(adx, 0)
        self.assertLessEqual(adx, 100)
        
        print(f"\n✅ ADX范围验证通过: {adx:.2f}")
    
    def test_stochastic_range(self):
        """测试随机指标在合理范围内"""
        indicators = self.calculator.calculate_all(self.market_data)
        stoch_k = indicators.momentum['Stochastic_K']
        stoch_d = indicators.momentum['Stochastic_D']
        
        self.assertGreaterEqual(stoch_k, 0)
        self.assertLessEqual(stoch_k, 100)
        self.assertGreaterEqual(stoch_d, 0)
        self.assertLessEqual(stoch_d, 100)
        
        print(f"\n✅ Stochastic范围验证通过: K={stoch_k:.2f}, D={stoch_d:.2f}")
    
    def test_bollinger_bands_order(self):
        """测试布林带顺序正确"""
        indicators = self.calculator.calculate_all(self.market_data)
        
        upper = indicators.volatility['BB_upper']
        middle = indicators.volatility['BB_middle']
        lower = indicators.volatility['BB_lower']
        
        self.assertGreater(upper, middle)
        self.assertGreater(middle, lower)
        
        print(f"\n✅ 布林带顺序正确: {lower:.2f} < {middle:.2f} < {upper:.2f}")
    
    def test_atr_positive(self):
        """测试ATR为正值"""
        indicators = self.calculator.calculate_all(self.market_data)
        atr = indicators.volatility['ATR']
        
        self.assertGreater(atr, 0)
        
        print(f"\n✅ ATR为正值: {atr:.2f}")
    
    def test_indicator_summary(self):
        """测试指标摘要生成"""
        indicators = self.calculator.calculate_all(self.market_data)
        summary = self.calculator.get_indicator_summary(indicators)
        
        self.assertIn('trend', summary)
        self.assertIn('rsi', summary)
        self.assertIn('volatility', summary)
        
        print(f"\n✅ 指标摘要生成成功:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    def test_different_data_sizes(self):
        """测试不同数据量"""
        for periods in [50, 100, 200]:
            data = self._generate_test_data(periods)
            indicators = self.calculator.calculate_all(data)
            
            self.assertIsInstance(indicators, TechnicalIndicators)
            print(f"\n✅ {periods}条数据测试通过")
    
    def test_uptrend_detection(self):
        """测试上升趋势检测"""
        # 生成明显上升趋势数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        close = np.linspace(50000, 55000, 100)  # 明显上升
        
        data = pd.DataFrame({
            'open': close - 50,
            'high': close + 100,
            'low': close - 100,
            'close': close,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        indicators = self.calculator.calculate_all(data)
        
        # EMA应该按顺序排列（上升趋势）
        ema_9 = indicators.trend['EMA_9']
        ema_21 = indicators.trend['EMA_21']
        ema_55 = indicators.trend['EMA_55']
        
        print(f"\n✅ 上升趋势检测: EMA_9({ema_9:.2f}) > EMA_21({ema_21:.2f}) > EMA_55({ema_55:.2f})")
        self.assertGreater(ema_9, ema_21)
        self.assertGreater(ema_21, ema_55)


class TestIndicatorEdgeCases(unittest.TestCase):
    """边缘情况测试"""
    
    def setUp(self):
        self.calculator = IndicatorCalculator()
    
    def test_minimum_data_size(self):
        """测试最小数据量"""
        # 需要至少20条数据（CCI的默认周期）
        dates = pd.date_range(start='2024-01-01', periods=30, freq='1H')
        data = pd.DataFrame({
            'open': np.random.randn(30) + 50000,
            'high': np.random.randn(30) + 50100,
            'low': np.random.randn(30) + 49900,
            'close': np.random.randn(30) + 50000,
            'volume': np.random.randint(1000, 10000, 30)
        }, index=dates)
        
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        try:
            indicators = self.calculator.calculate_all(data)
            print(f"\n✅ 最小数据量测试通过（30条）")
        except Exception as e:
            self.fail(f"最小数据量测试失败: {e}")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorCalculator))
    suite.addTests(loader.loadTestsFromTestCase(TestIndicatorEdgeCases))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
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

