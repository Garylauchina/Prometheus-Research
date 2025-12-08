"""
对手盘市场综合测试

测试AdversarialMarket的核心功能：
  1. 对手盘种群创建
  2. 订单撮合
  3. 价格冲击
  4. 市场统计
"""

import pytest
from prometheus.v6.self_play.adversarial_market import AdversarialMarket


class TestAdversarialMarket:
    """对手盘市场测试套件"""
    
    def setup_method(self):
        """每个测试前初始化"""
        self.market = AdversarialMarket()
    
    # ===== 对手盘生成测试 =====
    
    def test_create_adversarial_population(self):
        """测试：创建对手盘种群"""
        adversaries = self.market.create_adversarial_population(num_adversaries=10)
        
        assert len(adversaries) == 10
        assert all(adv.role == 'adversary' for adv in adversaries)
        
        # 验证类型分布
        types = [adv.agent_type for adv in adversaries]
        assert 'market_maker' in types
        assert 'trend_follower' in types
    
    def test_create_custom_distribution(self):
        """测试：自定义类型分布"""
        distribution = {
            'market_maker': 1.0,  # 100% 做市商
            'trend_follower': 0.0,
            'contrarian': 0.0,
            'arbitrageur': 0.0,
            'noise_trader': 0.0
        }
        
        adversaries = self.market.create_adversarial_population(
            num_adversaries=5,
            type_distribution=distribution
        )
        
        assert len(adversaries) == 5
        assert all(adv.agent_type == 'market_maker' for adv in adversaries)
    
    # ===== 订单撮合测试 =====
    
    def test_simulate_order_matching_empty(self):
        """测试：无订单的撮合"""
        trades, new_price = self.market.simulate_order_matching(
            orders=[],
            current_price=100.0,
            cycle=0
        )
        
        # 无主订单，但可能有对手盘订单
        # 至少价格应该被更新
        assert new_price > 0
    
    def test_simulate_order_matching_with_orders(self):
        """测试：有订单的撮合"""
        # 创建对手盘
        self.market.create_adversarial_population(num_adversaries=5)
        
        # 创建主订单
        main_orders = [
            {'agent_id': 'MAIN001', 'side': 'buy', 'amount': 1.0, 'type': 'market'},
            {'agent_id': 'MAIN002', 'side': 'sell', 'amount': 1.0, 'type': 'market'}
        ]
        
        trades, new_price = self.market.simulate_order_matching(
            orders=main_orders,
            current_price=100.0,
            cycle=1
        )
        
        # 应该有成交
        assert len(trades) >= 2  # 至少2笔（主订单）
        assert new_price > 0
    
    # ===== 价格冲击测试 =====
    
    def test_calculate_slippage_buy(self):
        """测试：买单滑点"""
        actual_price = self.market.calculate_slippage(
            order_amount=10.0,
            order_side='buy',
            market_price=100.0
        )
        
        # 买单应该推高价格
        assert actual_price >= 100.0
    
    def test_calculate_slippage_sell(self):
        """测试：卖单滑点"""
        actual_price = self.market.calculate_slippage(
            order_amount=10.0,
            order_side='sell',
            market_price=100.0
        )
        
        # 卖单应该压低价格
        assert actual_price <= 100.0
    
    # ===== 统计信息测试 =====
    
    def test_get_market_statistics(self):
        """测试：获取市场统计"""
        # 创建对手盘
        self.market.create_adversarial_population(num_adversaries=10)
        
        stats = self.market.get_market_statistics()
        
        assert 'order_book' in stats
        assert 'adversaries' in stats
        assert stats['total_adversaries'] == 10
    
    # ===== 重置测试 =====
    
    def test_reset_market(self):
        """测试：重置市场"""
        # 创建对手盘
        self.market.create_adversarial_population(num_adversaries=5)
        
        # 重置
        self.market.reset()
        
        stats = self.market.get_market_statistics()
        assert stats['total_adversaries'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

