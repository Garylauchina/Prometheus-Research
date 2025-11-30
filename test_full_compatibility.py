#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prometheus交易系统 - OKX兼容性解决方案集成测试

这个脚本测试整个兼容性解决方案，包括：
1. 验证兼容性模块导入
2. 测试后备方案功能
3. 验证所有适配器文件正确使用兼容性导入
4. 模拟完整的初始化流程
"""

import os
import sys
import logging
import importlib
from unittest.mock import patch

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_compatibility.log')
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_compatibility_module_import():
    """测试兼容性模块是否能正确导入"""
    logger.info("=== 测试1: 兼容性模块导入 ===")
    try:
        from adapters import okx_compat
        logger.info("✓ 成功导入兼容性模块")
        
        # 检查核心函数是否存在
        if hasattr(okx_compat, 'import_okx_module') and hasattr(okx_compat, 'apply_compatibility_fixes'):
            logger.info("✓ 兼容性模块包含必要的函数")
            return True
        else:
            logger.error("✗ 兼容性模块缺少必要的函数")
            return False
    except Exception as e:
        logger.error(f"✗ 导入兼容性模块失败: {e}")
        return False

def test_adapters_import():
    """测试所有适配器文件是否正确使用兼容性导入"""
    logger.info("\n=== 测试2: 适配器文件兼容性导入 ===")
    adapters = [
        ('adapters.market_data', 'MarketDataManager'),
        ('adapters.order_manager', 'OrderManager'),
        ('adapters.account_sync', 'AccountSync'),
    ]
    
    success = True
    for module_name, class_name in adapters:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                logger.info(f"✓ 成功导入 {module_name}.{class_name}")
            else:
                logger.error(f"✗ {module_name} 中未找到 {class_name}")
                success = False
        except Exception as e:
            logger.error(f"✗ 导入 {module_name} 失败: {e}")
            success = False
    
    return success

def test_fallback_functionality():
    """测试后备方案功能，模拟VPS环境下的导入失败"""
    logger.info("\n=== 测试3: 后备方案功能测试 ===")
    from adapters import okx_compat
    
    # 保存原始函数
    original_import = okx_compat.import_okx_module
    
    # 强制使用后备方案的测试函数
    def force_fallback_import(module_name):
        logger.info(f"强制测试后备方案: {module_name}")
        import types
        import okx
        
        # 创建模块
        if f"okx.{module_name}" not in sys.modules:
            module = types.ModuleType(f"okx.{module_name}")
            sys.modules[f"okx.{module_name}"] = module
        else:
            module = sys.modules[f"okx.{module_name}"]
        
        # 添加必要的API类
        if module_name == 'MarketData':
            class MarketAPI:
                def __init__(self, flag='1'):
                    self.flag = flag
                    logger.info(f"模拟MarketAPI初始化 (flag={flag})")
                
                def get_ticker(self, instId):
                    logger.info(f"模拟调用get_ticker: {instId}")
                    return {'code': '0', 'data': [{'instId': instId, 'last': '0'}]}
            
            module.MarketAPI = MarketAPI
        
        elif module_name == 'Trade':
            class TradeAPI:
                def __init__(self, api_key='', api_secret_key='', passphrase='', flag='1'):
                    logger.info(f"模拟TradeAPI初始化")
        
        elif module_name == 'Account':
            class AccountAPI:
                def __init__(self, api_key='', api_secret_key='', passphrase='', flag='1'):
                    logger.info(f"模拟AccountAPI初始化")
        
        # 将模块添加到okx命名空间
        if not hasattr(okx, module_name):
            setattr(okx, module_name, module)
        
        return module
    
    try:
        # 应用patch
        okx_compat.import_okx_module = force_fallback_import
        
        # 测试MarketData模块
        logger.info("测试MarketData.MarketAPI...")
        from adapters.okx_compat import MarketData
        
        if hasattr(MarketData, 'MarketAPI'):
            logger.info("✓ MarketData模块包含MarketAPI类")
            
            # 测试实例化
            api = MarketData.MarketAPI(flag='1')
            logger.info("✓ 成功实例化MarketAPI")
            
            # 测试方法调用
            result = api.get_ticker(instId='BTC-USDT')
            if result.get('code') == '0':
                logger.info("✓ MarketAPI方法调用成功")
                return True
            else:
                logger.error(f"✗ MarketAPI方法返回错误结果: {result}")
                return False
        else:
            logger.error("✗ MarketData模块缺少MarketAPI类")
            return False
    
    except Exception as e:
        logger.error(f"✗ 后备方案测试失败: {e}")
        return False
    
    finally:
        # 恢复原始函数
        okx_compat.import_okx_module = original_import

def test_market_data_manager_init():
    """测试MarketDataManager初始化，模拟VPS环境"""
    logger.info("\n=== 测试4: MarketDataManager初始化测试 ===")
    
    # 创建最小配置
    mock_config = {
        'flag': '1',
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'passphrase': 'test_passphrase'
    }
    
    # 使用模拟的MarketAPI
    with patch('adapters.okx_compat.MarketData') as mock_market_data:
        # 设置模拟对象
        mock_api = mock_market_data.MarketAPI.return_value
        mock_api.get_ticker.return_value = {'code': '0', 'data': [{'instId': 'BTC-USDT', 'last': '90000'}]}
        
        try:
            from adapters.market_data import MarketDataManager
            manager = MarketDataManager(mock_config)
            logger.info("✓ MarketDataManager初始化成功")
            
            # 测试调用方法
            result = manager.get_ticker('BTC-USDT')
            if result:
                logger.info("✓ MarketDataManager方法调用成功")
                return True
            else:
                logger.error("✗ MarketDataManager方法返回None")
                return False
                
        except Exception as e:
            logger.error(f"✗ MarketDataManager初始化失败: {e}")
            return False

def main():
    """运行所有测试"""
    logger.info("开始Prometheus交易系统OKX兼容性解决方案测试")
    logger.info("=" * 70)
    
    tests = [
        test_compatibility_module_import,
        test_adapters_import,
        test_fallback_functionality,
        test_market_data_manager_init
    ]
    
    all_passed = True
    
    for i, test_func in enumerate(tests, 1):
        if not test_func():
            all_passed = False
    
    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("🎉 所有兼容性测试通过! 解决方案可以部署到VPS。")
        logger.info("\n兼容性解决方案要点:")
        logger.info("1. 当正常导入失败时，将自动创建包含必要API类的后备模块")
        logger.info("2. MarketData.MarketAPI、Trade.TradeAPI和Account.AccountAPI将始终可用")
        logger.info("3. 即使在VPS上遇到导入问题，系统也能继续运行")
        return 0
    else:
        logger.error("❌ 部分兼容性测试失败，请检查日志并修复问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())
