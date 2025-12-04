"""
测试Mastermind预言在下跌市场的表现
模拟不同市场状态，验证看跌/看涨预言逻辑
"""

import sys
import logging
from datetime import datetime
from prometheus.core.mastermind import Mastermind
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.market_state_analyzer import MarketState, TrendState, MomentumState, VolatilityState

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def create_mock_market_state(trend_type='bull'):
    """
    创建模拟市场状态
    
    Args:
        trend_type: 'bull'(牛市), 'bear'(熊市), 'ranging'(震荡)
    """
    if trend_type == 'bull':
        # 牛市场景
        return MarketState(
            trend=TrendState.WEAK_UPTREND,
            trend_strength=60.0,
            momentum=MomentumState.NEUTRAL,
            momentum_score=55.0,
            volatility=VolatilityState.NORMAL,
            volatility_score=40.0,
            market_difficulty=0.3,
            opportunity_score=0.6,
            recommendation='适合做多',
            timestamp=datetime.now()
        )
    
    elif trend_type == 'bear':
        # 熊市场景
        return MarketState(
            trend=TrendState.WEAK_DOWNTREND,
            trend_strength=60.0,
            momentum=MomentumState.NEUTRAL,
            momentum_score=45.0,
            volatility=VolatilityState.NORMAL,
            volatility_score=40.0,
            market_difficulty=0.3,
            opportunity_score=0.4,
            recommendation='适合做空',
            timestamp=datetime.now()
        )
    
    elif trend_type == 'strong_bear':
        # 强熊市场景
        return MarketState(
            trend=TrendState.STRONG_DOWNTREND,
            trend_strength=80.0,
            momentum=MomentumState.OVERSOLD,
            momentum_score=25.0,
            volatility=VolatilityState.HIGH,
            volatility_score=70.0,
            market_difficulty=0.7,
            opportunity_score=0.2,
            recommendation='高风险',
            timestamp=datetime.now()
        )
    
    else:  # ranging
        # 震荡场景
        return MarketState(
            trend=TrendState.RANGING,
            trend_strength=30.0,
            momentum=MomentumState.NEUTRAL,
            momentum_score=50.0,
            volatility=VolatilityState.NORMAL,
            volatility_score=35.0,
            market_difficulty=0.5,
            opportunity_score=0.5,
            recommendation='观望',
            timestamp=datetime.now()
        )

def test_prophecy_scenarios():
    """测试不同市场场景下的预言"""
    
    bulletin_board = BulletinBoard()
    mastermind = Mastermind(bulletin_board=bulletin_board)
    
    scenarios = [
        ('bull', '牛市（温和上涨）'),
        ('bear', '熊市（温和下跌）'),
        ('strong_bear', '强熊市（强势下跌）'),
        ('ranging', '震荡市')
    ]
    
    print("="*70)
    print("🧪 Mastermind预言逻辑测试")
    print("="*70)
    print()
    
    for scenario_type, scenario_name in scenarios:
        mock_market_state = create_mock_market_state(scenario_type)
        
        # 准备Agent表现统计（模拟不同场景）
        if scenario_type == 'bear':
            agent_stats = {
                'avg_pnl': -1500,      # 平均亏损
                'losing_ratio': 0.65,  # 65%亏损
                'avg_drawdown': -0.15
            }
        elif scenario_type == 'strong_bear':
            agent_stats = {
                'avg_pnl': -6000,      # 严重亏损
                'losing_ratio': 0.85,  # 85%亏损
                'avg_drawdown': -0.35
            }
        else:
            agent_stats = {
                'avg_pnl': 500,
                'losing_ratio': 0.4,
                'avg_drawdown': -0.05
            }
        
        # 生成小预言
        prophecy = mastermind.minor_prophecy(
            market_data=None,
            current_market_state=mock_market_state,
            top_performers=[],
            agent_performance_stats=agent_stats
        )
        
        if prophecy:
            print(f"📊 场景：{scenario_name}")
            print(f"   趋势：{mock_market_state.trend.value}")
            print(f"   趋势强度：{mock_market_state.trend_strength:.1f}")
            print(f"   动量得分：{mock_market_state.momentum_score:.1f}")
            print(f"   Agent表现：平均PnL ${agent_stats['avg_pnl']:+.0f}, 亏损率{agent_stats['losing_ratio']:.0%}")
            print()
            print(f"🔮 预言结果：")
            print(f"   走势预测：{prophecy['trend_forecast']}")
            print(f"   预测信心：{prophecy['forecast_confidence']:.0%}")
            print(f"   看涨得分：{prophecy['bullish_score']:.2f}")
            print(f"   环境压力：{prophecy['environmental_pressure']:.2f} - {prophecy['pressure_description']}")
            print(f"   风险等级：{prophecy['risk_level']}")
            print()
            
            # 验证结果
            if scenario_type in ['bear', 'strong_bear']:
                if '看跌' in prophecy['trend_forecast']:
                    print(f"   ✅ 验证通过：熊市场景正确预测为看跌")
                else:
                    print(f"   ❌ 验证失败：熊市场景未预测为看跌！")
            elif scenario_type == 'bull':
                if '看涨' in prophecy['trend_forecast']:
                    print(f"   ✅ 验证通过：牛市场景正确预测为看涨")
                else:
                    print(f"   ❌ 验证失败：牛市场景未预测为看涨！")
            else:  # ranging
                if '震荡' in prophecy['trend_forecast']:
                    print(f"   ✅ 验证通过：震荡场景正确预测为震荡")
                else:
                    print(f"   ⚠️  注意：震荡场景预测为{prophecy['trend_forecast']}")
            
            print("-"*70)
            print()

if __name__ == '__main__':
    try:
        test_prophecy_scenarios()
        print("="*70)
        print("✅ 预言逻辑测试完成")
        print("="*70)
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

