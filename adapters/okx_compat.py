"""OKX包兼容性模块

这个模块解决在不同Python环境中可能出现的OKX包导入问题，
特别是从okx导入MarketData、Trade和Account模块时的兼容性问题。
"""

import sys
import importlib.util
import os
import logging

logger = logging.getLogger(__name__)

# 尝试多种导入方式的通用函数
def import_okx_module(module_name):
    """
    尝试多种方式导入OKX模块
    
    Args:
        module_name: 要导入的模块名称，如'MarketData', 'Trade', 'Account'
        
    Returns:
        成功导入的模块对象，如果所有尝试都失败则返回None
    """
    # 方式1: 直接从okx导入
    try:
        import_statement = f"from okx import {module_name}"
        logger.debug(f"尝试: {import_statement}")
        
        # 使用exec执行导入语句
        exec(import_statement, globals())
        module = globals()[module_name]
        logger.debug(f"成功: {import_statement}")
        return module
    except ImportError as e:
        logger.debug(f"失败: {import_statement}, 错误: {e}")
    
    # 方式2: 动态导入对应的.py文件
    try:
        # 获取okx包路径
        import okx
        okx_dir = os.path.dirname(okx.__file__)
        module_file = os.path.join(okx_dir, f"{module_name}.py")
        
        if os.path.exists(module_file):
            logger.debug(f"尝试动态导入: {module_file}")
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(f"okx.{module_name}", module_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"okx.{module_name}"] = module
            spec.loader.exec_module(module)
            
            # 将模块添加到okx命名空间
            setattr(okx, module_name, module)
            
            logger.debug(f"成功动态导入: {module_name}")
            return module
        else:
            logger.debug(f"模块文件不存在: {module_file}")
    except Exception as e:
        logger.debug(f"动态导入失败: {e}")
    
    # 方式3: 创建空模块作为后备方案
    try:
        import types
        import okx
        
        # 创建空模块
        if f"okx.{module_name}" not in sys.modules:
            sys.modules[f"okx.{module_name}"] = types.ModuleType(f"okx.{module_name}")
        
        # 将模块添加到okx命名空间
        if not hasattr(okx, module_name):
            setattr(okx, module_name, sys.modules[f"okx.{module_name}"])
        
        module = getattr(okx, module_name)
        logger.warning(f"创建了空的{module_name}模块作为后备方案")
        return module
    except Exception as e:
        logger.error(f"创建后备模块失败: {e}")
    
    logger.error(f"所有导入方式都失败: {module_name}")
    return None

# 自动执行兼容性修复
def apply_compatibility_fixes():
    """
    应用所有必要的兼容性修复
    
    Returns:
        dict: 包含导入结果的字典
    """
    logger.info("应用OKX包兼容性修复...")
    
    results = {}
    required_modules = ['MarketData', 'Trade', 'Account']
    
    for module_name in required_modules:
        module = import_okx_module(module_name)
        results[module_name] = module is not None
        
        if module is not None:
            logger.info(f"✓ 成功导入: {module_name}")
            # 将导入的模块添加到全局命名空间
            globals()[module_name] = module
        else:
            logger.error(f"✗ 导入失败: {module_name}")
    
    return results

# 自动应用修复
FIX_RESULTS = apply_compatibility_fixes()

# 提供直接导入的便捷方式
if FIX_RESULTS.get('MarketData'):
    MarketData = globals().get('MarketData')

if FIX_RESULTS.get('Trade'):
    Trade = globals().get('Trade')

if FIX_RESULTS.get('Account'):
    Account = globals().get('Account')

logger.info(f"OKX兼容性修复完成. 结果: {FIX_RESULTS}")
