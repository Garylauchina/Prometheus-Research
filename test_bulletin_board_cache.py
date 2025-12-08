"""
BulletinBoard WorldSignature缓存测试
====================================

验证：
1. Prophet发布时自动缓存WorldSignature对象
2. 从BulletinBoard获取缓存对象（无需重复解析）
3. 性能优化：1次解析 vs 50次解析
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from prometheus.core.prophet import Prophet
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.world_signature_simple import WorldSignatureSimple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_mock_data(cycles=100):
    """生成简单的模拟数据"""
    timestamps = [datetime.now() + timedelta(hours=i) for i in range(cycles)]
    prices = [50000 * (1 + 0.001 * i) for i in range(cycles)]
    
    data = []
    for i, timestamp in enumerate(timestamps):
        price = prices[i]
        data.append({
            'timestamp': timestamp,
            'open': price,
            'high': price * 1.01,
            'low': price * 0.99,
            'close': price,
            'volume': 1000
        })
    
    return pd.DataFrame(data)

def main():
    logger.info("="*80)
    logger.info("BulletinBoard WorldSignature缓存测试")
    logger.info("="*80)
    logger.info("")
    
    # 1. 初始化
    bulletin_board = BulletinBoard(board_name="cache_test")
    prophet = Prophet(bulletin_board=bulletin_board)
    
    # 2. 生成数据
    market_data = generate_mock_data(cycles=100)
    logger.info(f"✅ 生成{len(market_data)}根K线")
    logger.info("")
    
    # 3. Prophet制定战略（会自动缓存）
    logger.info("测试：Prophet制定战略并缓存WorldSignature")
    logger.info("-"*80)
    
    strategy = prophet.genesis_strategy(
        initial_market_data=market_data,
        agent_count=50,
        genesis_mode='adaptive'
    )
    
    # 4. 验证缓存
    logger.info("")
    logger.info("="*80)
    logger.info("验证缓存")
    logger.info("="*80)
    
    # 检查1：缓存是否存在
    cached_ws = bulletin_board.get_current_world_signature()
    check1 = cached_ws is not None
    logger.info(f"{'✅' if check1 else '❌'} 缓存WorldSignature对象存在")
    
    # 检查2：缓存对象类型正确
    check2 = isinstance(cached_ws, WorldSignatureSimple) if cached_ws else False
    logger.info(f"{'✅' if check2 else '❌'} 缓存对象类型正确: {type(cached_ws).__name__}")
    
    # 检查3：缓存对象与Prophet的current_ws一致
    check3 = cached_ws is prophet.get_current_world_signature() if cached_ws else False
    logger.info(f"{'✅' if check3 else '❌'} 缓存对象与Prophet.current_ws一致（同一对象）")
    
    # 检查4：缓存对象可用
    if cached_ws:
        check4 = hasattr(cached_ws, 'vector') and len(cached_ws.vector) == 14
        logger.info(f"{'✅' if check4 else '❌'} 缓存对象可用（14维向量）")
    else:
        check4 = False
        logger.info(f"❌ 缓存对象为空")
    
    logger.info("")
    logger.info("="*80)
    logger.info("性能对比")
    logger.info("="*80)
    
    # 模拟50个Agent读取（传统方式 vs 缓存方式）
    import time
    import json
    
    # 传统方式：每个Agent都解析JSON
    logger.info("传统方式：每个Agent解析JSON")
    start = time.time()
    for i in range(50):
        # 模拟读取BulletinBoard
        bulletins = bulletin_board.get_recent(hours=1)
        if bulletins:
            content = json.loads(bulletins[0].content)
            if 'world_signature' in content:
                ws = WorldSignatureSimple.from_dict(content['world_signature'])
    end = time.time()
    time_traditional = (end - start) * 1000
    logger.info(f"  耗时: {time_traditional:.2f}ms（50个Agent）")
    
    # 缓存方式：直接获取对象
    logger.info("缓存方式：直接获取对象")
    start = time.time()
    for i in range(50):
        ws = bulletin_board.get_current_world_signature()
    end = time.time()
    time_cached = (end - start) * 1000
    logger.info(f"  耗时: {time_cached:.2f}ms（50个Agent）")
    
    # 性能提升
    speedup = time_traditional / time_cached if time_cached > 0 else float('inf')
    logger.info(f"  性能提升: {speedup:.1f}x")
    
    logger.info("")
    logger.info("="*80)
    
    # 总结
    all_checks = [check1, check2, check3, check4]
    passed = sum(all_checks)
    total = len(all_checks)
    
    if passed == total:
        logger.info(f"🎉 全部通过！（{passed}/{total}）")
        logger.info("")
        logger.info("✅ BulletinBoard缓存机制工作正常")
        logger.info("✅ Prophet自动缓存WorldSignature")
        logger.info(f"✅ 性能提升：{speedup:.1f}x")
        logger.info("✅ 为Daimon决策做好准备")
    else:
        logger.error(f"❌ 部分失败（{passed}/{total}）")
    
    logger.info("="*80)

if __name__ == "__main__":
    main()

