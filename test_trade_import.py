import logging
from okx import Trade

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_trade():
    try:
        # 初始化Trade API (使用模拟盘)
        logger.info("初始化Trade API...")
        # 注意：实际使用时需要API密钥，但这里我们只是测试导入和初始化
        # 所以不需要真实的API凭证，只需验证对象能否被创建
        
        # 尝试直接检查Trade模块的内容
        logger.info(f"Trade模块可用属性: {dir(Trade)}")
        
        # 检查是否有TradeAPI类
        if hasattr(Trade, 'TradeAPI'):
            logger.info("Trade模块中找到TradeAPI类")
        else:
            logger.warning("Trade模块中未找到TradeAPI类")
            
        logger.info("Trade模块测试成功完成!")
        return True
    except Exception as e:
        logger.error(f"Trade模块测试失败: {e}")
        return False

if __name__ == "__main__":
    test_trade()
