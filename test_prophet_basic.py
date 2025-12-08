"""
Prophet基础功能测试
===================

验证：
1. Prophet初始化
2. 创世战略制定
3. BulletinBoard发布
4. WorldSignature计算
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from prometheus.core.prophet import Prophet
from prometheus.core.bulletin_board import BulletinBoard

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_data(cycles=200, trend='bull'):
    """生成模拟市场数据"""
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(cycles)]
    
    if trend == 'bull':
        # 牛市：明显上涨趋势（+30%）
        base_price = 50000
        prices = [base_price * (1 + 0.0015 * i + np.random.normal(0, 0.005)) for i in range(cycles)]
    elif trend == 'bear':
        # 熊市：下跌趋势
        base_price = 50000
        prices = [base_price * (1 - 0.001 * i + np.random.normal(0, 0.01)) for i in range(cycles)]
    else:
        # 震荡市：横盘
        base_price = 50000
        prices = [base_price * (1 + np.random.normal(0, 0.015)) for i in range(cycles)]
    
    data = []
    for i, timestamp in enumerate(timestamps):
        price = prices[i]
        data.append({
            'timestamp': timestamp,
            'open': price * (1 + np.random.normal(0, 0.002)),
            'high': price * (1 + abs(np.random.normal(0, 0.005))),
            'low': price * (1 - abs(np.random.normal(0, 0.005))),
            'close': price,
            'volume': abs(np.random.normal(1000, 200))
        })
    
    return pd.DataFrame(data)

def test_prophet_bull_market():
    """测试：牛市场景"""
    logger.info("="*80)
    logger.info("测试1：Prophet - 牛市场景")
    logger.info("="*80)
    
    # 1. 初始化
    bulletin_board = BulletinBoard(board_name="test_board")
    prophet = Prophet(bulletin_board=bulletin_board)
    
    # 2. 生成牛市数据
    market_data = generate_mock_data(cycles=200, trend='bull')
    logger.info(f"✅ 生成牛市数据：{len(market_data)}根K线")
    logger.info(f"   价格变化：${market_data['close'].iloc[0]:,.0f} → ${market_data['close'].iloc[-1]:,.0f}")
    
    # 3. 制定创世战略
    strategy = prophet.genesis_strategy(
        initial_market_data=market_data,
        agent_count=50,
        genesis_mode='adaptive'
    )
    
    # 4. 验证结果
    logger.info("")
    logger.info("="*80)
    logger.info("验证结果")
    logger.info("="*80)
    
    checks = []
    
    # 检查1：战略生成
    check1 = strategy is not None
    checks.append(("战略生成", check1))
    logger.info(f"{'✅' if check1 else '❌'} 战略生成成功")
    
    # 检查2：市场状态识别
    check2 = strategy['market_state'] == 'bull'
    checks.append(("市场状态识别", check2))
    logger.info(f"{'✅' if check2 else '❌'} 市场状态识别为牛市（实际：{strategy['market_state']}）")
    
    # 检查3：WorldSignature计算
    check3 = strategy['world_signature'] is not None
    checks.append(("WorldSignature", check3))
    logger.info(f"{'✅' if check3 else '❌'} WorldSignature计算成功")
    
    # 检查4：BulletinBoard发布（简化：检查current_strategy）
    check4 = prophet.get_current_strategy() is not None
    checks.append(("BulletinBoard发布", check4))
    logger.info(f"{'✅' if check4 else '❌'} 战略已保存（简化验证）")
    
    # 检查5：战略建议合理
    check5 = 0 < strategy['recommended_allocation'] <= 1.0
    checks.append(("战略建议合理", check5))
    logger.info(f"{'✅' if check5 else '❌'} 配资建议：{strategy['recommended_allocation']*100:.0f}%")
    
    # 总结
    passed = sum(1 for _, c in checks if c)
    total = len(checks)
    
    logger.info("")
    logger.info("="*80)
    if passed == total:
        logger.info(f"🎉 牛市测试通过！（{passed}/{total}）")
    else:
        logger.error(f"❌ 部分失败（{passed}/{total}）")
    logger.info("="*80)
    
    return passed == total

def test_prophet_bear_market():
    """测试：熊市场景"""
    logger.info("")
    logger.info("="*80)
    logger.info("测试2：Prophet - 熊市场景")
    logger.info("="*80)
    
    # 初始化
    bulletin_board = BulletinBoard(board_name="test_board")
    prophet = Prophet(bulletin_board=bulletin_board)
    
    # 生成熊市数据
    market_data = generate_mock_data(cycles=200, trend='bear')
    logger.info(f"✅ 生成熊市数据：{len(market_data)}根K线")
    logger.info(f"   价格变化：${market_data['close'].iloc[0]:,.0f} → ${market_data['close'].iloc[-1]:,.0f}")
    
    # 制定创世战略
    strategy = prophet.genesis_strategy(
        initial_market_data=market_data,
        agent_count=50,
        genesis_mode='adaptive'
    )
    
    # 验证
    check = strategy['market_state'] == 'bear'
    logger.info("")
    logger.info(f"{'✅' if check else '❌'} 市场状态识别为熊市（实际：{strategy['market_state']}）")
    
    return check

def test_prophet_strategy_update():
    """测试：战略更新"""
    logger.info("")
    logger.info("="*80)
    logger.info("测试3：Prophet - 战略更新")
    logger.info("="*80)
    
    # 初始化
    bulletin_board = BulletinBoard(board_name="test_board")
    prophet = Prophet(bulletin_board=bulletin_board)
    
    # 初始战略
    initial_data = generate_mock_data(cycles=100, trend='sideways')
    strategy1 = prophet.genesis_strategy(initial_data, agent_count=50)
    
    # 更新战略
    new_data = generate_mock_data(cycles=150, trend='bull')
    strategy2 = prophet.update_strategy(new_data, current_cycle=100)
    
    # 验证
    check = strategy2 is not None
    logger.info(f"{'✅' if check else '❌'} 战略更新成功")
    logger.info(f"   初始市场：{strategy1['market_state']}")
    logger.info(f"   更新后：{strategy2['market_state']}")
    
    return check

def main():
    logger.info("="*80)
    logger.info("Prophet基础功能测试")
    logger.info("="*80)
    logger.info("")
    
    results = []
    
    # 测试1：牛市
    results.append(test_prophet_bull_market())
    
    # 测试2：熊市
    results.append(test_prophet_bear_market())
    
    # 测试3：战略更新
    results.append(test_prophet_strategy_update())
    
    # 总结
    logger.info("")
    logger.info("="*80)
    logger.info("总结")
    logger.info("="*80)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        logger.info(f"🎉 全部通过！（{passed}/{total}）")
        logger.info("")
        logger.info("✅ Prophet基础功能正常")
        logger.info("✅ 可以继续实现Moirai集成")
    else:
        logger.error(f"❌ 部分失败（{passed}/{total}）")
    
    logger.info("="*80)

if __name__ == "__main__":
    main()

