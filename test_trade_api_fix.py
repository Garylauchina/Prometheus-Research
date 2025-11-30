#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus交易系统 - Trade.TradeAPI 修复测试

这个脚本专门测试Trade模块和TradeAPI类的可用性，确保修复有效。
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_trade_module_import():
    """测试Trade模块导入"""
    logger.info("=== 测试1: Trade模块导入测试 ===")
    try:
        from adapters.okx_compat import Trade
        logger.info(f"✓ 成功导入Trade模块: {Trade}")
        return True
    except ImportError as e:
        logger.error(f"✗ 导入Trade模块失败: {e}")
        return False

def test_trade_api_class():
    """测试TradeAPI类存在性"""
    logger.info("\n=== 测试2: TradeAPI类存在性测试 ===")
    try:
        from adapters.okx_compat import Trade
        
        if hasattr(Trade, 'TradeAPI'):
            logger.info(f"✓ Trade模块包含TradeAPI类: {Trade.TradeAPI}")
            return True
        else:
            logger.error("✗ Trade模块缺少TradeAPI类")
            logger.error(f"Trade模块属性: {dir(Trade)}")
            return False
    except Exception as e:
        logger.error(f"✗ TradeAPI类测试失败: {e}")
        return False

def test_trade_api_instantiation():
    """测试TradeAPI实例化"""
    logger.info("\n=== 测试3: TradeAPI实例化测试 ===")
    try:
        from adapters.okx_compat import Trade
        
        # 创建一个测试实例
        trade_api = Trade.TradeAPI(
            api_key='test_key',
            api_secret_key='test_secret',
            passphrase='test_passphrase',
            flag='1'
        )
        
        logger.info(f"✓ 成功实例化TradeAPI对象: {trade_api}")
        logger.info(f"✓ TradeAPI对象属性: {dir(trade_api)}")
        return True
    except Exception as e:
        logger.error(f"✗ TradeAPI实例化失败: {e}")
        return False

def test_order_manager_import():
    """测试OrderManager导入和初始化"""
    logger.info("\n=== 测试4: OrderManager导入和初始化测试 ===")
    
    # 创建最小配置
    mock_config = {
        'api_key': 'test_key',
        'secret_key': 'test_secret',
        'passphrase': 'test_passphrase',
        'flag': '1'
    }
    
    try:
        from adapters.order_manager import OrderManager
        
        # 尝试初始化
        manager = OrderManager(mock_config)
        
        logger.info("✓ 成功导入OrderManager类")
        logger.info("✓ 成功初始化OrderManager实例")
        
        # 验证trade_api属性
        if hasattr(manager, 'trade_api'):
            logger.info(f"✓ OrderManager包含trade_api属性: {manager.trade_api}")
            return True
        else:
            logger.error("✗ OrderManager缺少trade_api属性")
            return False
    except Exception as e:
        logger.error(f"✗ OrderManager测试失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return False

def main():
    """运行所有测试"""
    logger.info("开始Trade.TradeAPI修复测试")
    logger.info("=" * 50)
    
    tests = [
        test_trade_module_import,
        test_trade_api_class,
        test_trade_api_instantiation,
        test_order_manager_import
    ]
    
    all_passed = True
    
    for i, test_func in enumerate(tests, 1):
        if not test_func():
            all_passed = False
    
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("🎉 所有Trade.TradeAPI修复测试通过!")
        logger.info("\n修复确认:")
        logger.info("1. Trade模块可以成功导入")
        logger.info("2. Trade.TradeAPI类始终可用")
        logger.info("3. OrderManager可以成功初始化")
        return 0
    else:
        logger.error("❌ 部分Trade.TradeAPI修复测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main())
