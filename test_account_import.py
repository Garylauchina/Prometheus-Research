import logging
from okx import Account

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_account():
    try:
        # 初始化Account API (使用模拟盘)
        logger.info("初始化Account API测试...")
        
        # 尝试直接检查Account模块的内容
        logger.info(f"Account模块可用属性: {dir(Account)}")
        
        # 检查是否有AccountAPI类
        if hasattr(Account, 'AccountAPI'):
            logger.info("Account模块中找到AccountAPI类")
        else:
            logger.warning("Account模块中未找到AccountAPI类")
            
        logger.info("Account模块测试成功完成!")
        return True
    except Exception as e:
        logger.error(f"Account模块测试失败: {e}")
        return False

if __name__ == "__main__":
    test_account()
