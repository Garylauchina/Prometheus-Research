"""
OKX兼容性修复测试脚本

这个脚本测试我们的兼容性修复是否有效，确保在各种环境中都能正确导入和使用OKX相关模块。
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('compatibility_test')

def test_all_okx_imports():
    """测试所有OKX相关导入"""
    logger.info("=== 开始测试OKX兼容性修复 ===")
    
    results = {}
    
    # 1. 测试直接从兼容性模块导入
    logger.info("\n1. 测试从兼容性模块直接导入:")
    try:
        from adapters.okx_compat import MarketData, Trade, Account
        logger.info("✓ 成功从okx_compat导入所有模块")
        logger.info(f"  MarketData: {type(MarketData)}")
        logger.info(f"  Trade: {type(Trade)}")
        logger.info(f"  Account: {type(Account)}")
        results['compat_import'] = True
    except ImportError as e:
        logger.error(f"✗ 从okx_compat导入失败: {e}")
        results['compat_import'] = False
    
    # 2. 测试market_data.py导入
    logger.info("\n2. 测试market_data.py导入:")
    try:
        from adapters.market_data import MarketDataManager
        logger.info("✓ 成功导入MarketDataManager")
        results['market_data'] = True
    except Exception as e:
        logger.error(f"✗ 导入market_data失败: {e}")
        results['market_data'] = False
    
    # 3. 测试order_manager.py导入
    logger.info("\n3. 测试order_manager.py导入:")
    try:
        from adapters.order_manager import Order
        logger.info("✓ 成功导入Order")
        results['order_manager'] = True
    except Exception as e:
        logger.error(f"✗ 导入order_manager失败: {e}")
        results['order_manager'] = False
    
    # 4. 测试account_sync.py导入
    logger.info("\n4. 测试account_sync.py导入:")
    try:
        from adapters.account_sync import AccountSync
        logger.info("✓ 成功导入AccountSync")
        results['account_sync'] = True
    except Exception as e:
        logger.error(f"✗ 导入account_sync失败: {e}")
        results['account_sync'] = False
    
    # 5. 测试OKX适配器导入
    logger.info("\n5. 测试OKX适配器导入:")
    try:
        from adapters.okx_adapter import OKXTradingAdapter
        logger.info("✓ 成功导入OKXTradingAdapter")
        results['okx_adapter'] = True
    except Exception as e:
        logger.error(f"✗ 导入okx_adapter失败: {e}")
        results['okx_adapter'] = False
    
    # 6. 测试模块功能
    logger.info("\n6. 测试模块功能:")
    try:
        from adapters.okx_compat import MarketData
        # 检查MarketData是否包含MarketAPI类
        has_market_api = hasattr(MarketData, 'MarketAPI')
        logger.info(f"  MarketData包含MarketAPI类: {has_market_api}")
        results['market_api_check'] = has_market_api
    except Exception as e:
        logger.error(f"✗ 功能测试失败: {e}")
        results['market_api_check'] = False
    
    # 总结
    logger.info("\n=== 兼容性测试总结 ===")
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        logger.info(f"{test_name}: {status}")
    
    if all_passed:
        logger.info("\n🎉 所有测试都通过了！兼容性修复有效。")
    else:
        logger.error("\n❌ 部分测试失败，需要进一步调试。")
    
    return all_passed

def print_environment_info():
    """打印环境信息"""
    logger.info("=== 环境信息 ===")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"操作系统: {sys.platform}")
    logger.info(f"当前目录: {os.getcwd()}")
    
    # 检查okx包
    try:
        import okx
        logger.info(f"OKX包版本: {getattr(okx, '__version__', '未知')}")
        logger.info(f"OKX包路径: {os.path.dirname(okx.__file__)}")
    except ImportError:
        logger.warning("未安装okx包")

if __name__ == "__main__":
    print_environment_info()
    success = test_all_okx_imports()
    
    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)
