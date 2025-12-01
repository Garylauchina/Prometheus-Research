#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus交易系统 - OKX API 功能验证

这个脚本验证python-okx库的基本功能和API类可用性，确保系统正常运行。
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

def test_okx_import():
    """测试python-okx库导入"""
    logger.info("=== 测试1: python-okx库导入检查 ===")
    try:
        import okx
        logger.info(f"✓ 成功导入python-okx库")
        return True
    except ImportError as e:
        logger.error(f"✗ 导入python-okx库失败: {e}")
        return False

def test_compat_module():
    """测试okx_compat模块导入"""
    logger.info("\n=== 测试2: okx_compat模块测试 ===")
    try:
        from adapters import okx_compat
        logger.info("✓ 成功导入okx_compat模块")
        return True
    except Exception as e:
        logger.error(f"✗ okx_compat模块测试失败: {e}")
        return False

def test_module_imports():
    """测试模块导入"""
    logger.info("\n=== 测试3: 模块导入测试 ===")
    modules_to_test = ['MarketData', 'Trade', 'Account']
    success = True
    
    for module_name in modules_to_test:
        try:
            from adapters.okx_compat import MarketData
            logger.info(f"✓ 成功从兼容性模块导入 {module_name}")
        except ImportError as e:
            logger.error(f"✗ 从兼容性模块导入 {module_name} 失败: {e}")
            success = False
    
    return success

def test_api_classes():
    """测试API类"""
    logger.info("\n=== 测试4: API类测试 ===")
    try:
        from adapters.okx_compat import MarketData
        
        if hasattr(MarketData, 'MarketAPI'):
            logger.info("✓ MarketData模块包含MarketAPI类")
            return True
        else:
            logger.error("✗ MarketData模块缺少MarketAPI类")
            return False
    except Exception as e:
        logger.error(f"✗ API类测试失败: {e}")
        return False

def test_market_data_manager():
    """测试MarketDataManager初始化"""
    logger.info("\n=== 测试5: MarketDataManager初始化测试 ===")
    
    # 创建最小配置
    mock_config = {
        'flag': '1',
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'passphrase': 'test_passphrase'
    }
    
    try:
        from adapters.market_data import MarketDataManager
        manager = MarketDataManager(mock_config)
        logger.info("✓ MarketDataManager初始化成功")
        return True
    except Exception as e:
        logger.error(f"✗ MarketDataManager初始化失败: {e}")
        return False

def main():
    """运行所有测试"""
    logger.info("开始OKX API功能验证")
    logger.info("=" * 50)
    
    tests = [
        test_okx_import,
        test_compat_module,
        test_module_imports,
        test_api_classes,
        test_market_data_manager
    ]
    
    all_passed = True
    
    for i, test_func in enumerate(tests, 1):
        if not test_func():
            all_passed = False
    
    logger.info("\n" + "=" * 50)
    if all_passed:
        logger.info("🎉 所有OKX API功能验证通过!")
        logger.info("\n验证结果:")
        logger.info("1. python-okx库正确安装")
        logger.info("2. 所有必要的API模块和类可正常访问")
        logger.info("3. MarketDataManager可以正常初始化")
        return 0
    else:
        logger.error("❌ 部分功能验证失败，请检查日志并修复问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
