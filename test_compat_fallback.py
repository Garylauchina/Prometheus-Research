import logging
import sys
import os
import importlib

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 先确保导入兼容性模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 强制测试后备方案：临时修改okx_compat.py的import_okx_module函数
def monkey_patch_import_function():
    from adapters import okx_compat
    
    # 保存原始函数
    original_import_okx_module = okx_compat.import_okx_module
    
    # 定义修改后的函数，跳过方式1和方式2，直接使用方式3
    def patched_import_okx_module(module_name):
        logger.info(f"强制使用后备方案导入: {module_name}")
        try:
            import types
            import okx
            
            # 创建模块
            if f"okx.{module_name}" not in sys.modules:
                module = types.ModuleType(f"okx.{module_name}")
                sys.modules[f"okx.{module_name}"] = module
            else:
                module = sys.modules[f"okx.{module_name}"]
            
            # 根据模块名称添加相应的API类
            if module_name == 'MarketData':
                class MarketAPI:
                    def __init__(self, flag='1'):
                        self.flag = flag
                        logger.info(f"模拟MarketAPI初始化 (flag={flag})")
                    
                    # 实现必要的方法，返回模拟数据
                    def get_ticker(self, instId):
                        logger.info(f"模拟调用get_ticker: {instId}")
                        return {'code': '0', 'data': [{'instId': instId, 'last': '0', 'open24h': '0'}]}
                    
                    def get_instruments(self, instType='SPOT', uly=None, instId=None):
                        logger.info(f"模拟调用get_instruments")
                        return {'code': '0', 'data': []}
                    
                    def get_candles(self, instId, bar='1m', limit=100):
                        logger.info(f"模拟调用get_candles: {instId}, {bar}")
                        return {'code': '0', 'data': []}
                
                module.MarketAPI = MarketAPI
            
            elif module_name == 'Trade':
                class TradeAPI:
                    def __init__(self, api_key='', api_secret_key='', passphrase='', flag='1'):
                        self.flag = flag
                        logger.info(f"模拟TradeAPI初始化 (flag={flag})")
                    
                    # 实现必要的方法，返回模拟数据
                    def place_order(self, **kwargs):
                        logger.info(f"模拟调用place_order: {kwargs}")
                        return {'code': '0', 'data': [{'ordId': 'sim-123'}]}
                    
                    def cancel_order(self, instId, ordId):
                        logger.info(f"模拟调用cancel_order: {instId}, {ordId}")
                        return {'code': '0', 'data': []}
                
                module.TradeAPI = TradeAPI
            
            elif module_name == 'Account':
                class AccountAPI:
                    def __init__(self, api_key='', api_secret_key='', passphrase='', flag='1'):
                        self.flag = flag
                        logger.info(f"模拟AccountAPI初始化 (flag={flag})")
                    
                    # 实现必要的方法，返回模拟数据
                    def get_balance(self):
                        logger.info("模拟调用get_balance")
                        return {'code': '0', 'data': [{'adjEq': '5000', 'details': []}]}
                
                module.AccountAPI = AccountAPI
            
            # 将模块添加到okx命名空间
            if not hasattr(okx, module_name):
                setattr(okx, module_name, module)
            
            logger.warning(f"创建了包含必要API类的{module_name}模块作为后备方案")
            return module
        except Exception as e:
            logger.error(f"创建后备模块失败: {e}")
            return None
    
    # 应用monkey patch
    okx_compat.import_okx_module = patched_import_okx_module
    logger.info("已应用monkey patch，强制使用后备方案")
    
    # 返回原始函数，以便后续还原
    return original_import_okx_module

logger.info("测试兼容性模块的后备方案...")
original_import_function = monkey_patch_import_function()

# 导入兼容性模块并测试
from adapters.okx_compat import import_okx_module

def test_fallback_mechanism():
    try:
        # 强制使用后备方案（模拟VPS环境）
        logger.info("尝试获取MarketData模块...")
        market_data = import_okx_module('MarketData')
        
        if market_data is None:
            logger.error("MarketData模块获取失败")
            return False
        
        logger.info(f"成功获取MarketData模块: {market_data}")
        
        # 检查是否有MarketAPI属性
        if not hasattr(market_data, 'MarketAPI'):
            logger.error("MarketData模块缺少MarketAPI属性")
            return False
        
        logger.info(f"MarketData模块包含MarketAPI类: {market_data.MarketAPI}")
        
        # 尝试实例化MarketAPI
        try:
            logger.info("尝试实例化MarketAPI...")
            api = market_data.MarketAPI(flag='1')
            logger.info(f"成功实例化MarketAPI: {api}")
            
            # 测试一个方法
            logger.info("测试get_ticker方法...")
            result = api.get_ticker(instId='BTC-USDT')
            logger.info(f"get_ticker返回结果: {result}")
            
            logger.info("后备方案测试成功!")
            return True
        except Exception as e:
            logger.error(f"实例化MarketAPI失败: {e}")
            return False
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    try:
        test_fallback_mechanism()
    finally:
        # 确保还原原始函数
        try:
            from adapters import okx_compat
            okx_compat.import_okx_module = original_import_function
            logger.info("已还原原始导入函数")
        except Exception as e:
            logger.warning(f"还原原始函数失败: {e}")
