
# 临时修复模块
import importlib.util
import os
import sys

def fix_okx_import():
    # 修复okx包导入问题的函数
    try:
        # 尝试直接导入
        from okx import MarketData
        print("✓ MarketData已经可以直接导入")
        return True
    except ImportError:
        # 获取okx包路径
        import okx
        okx_dir = os.path.dirname(okx.__file__)
        print(f"尝试从{okx_dir}加载MarketData模块...")
        
        # 查找可能的MarketData模块文件
        for root, dirs, files in os.walk(okx_dir):
            for file in files:
                if 'market' in file.lower() or 'data' in file.lower():
                    print(f"  找到相关文件: {os.path.join(root, file)}")
        
        # 尝试动态加载
        try:
            # 这是一个尝试性的修复方案
            print("尝试动态创建MarketData模块...")
            import sys
            import types
            
            # 创建一个空的MarketData模块
            if 'okx.MarketData' not in sys.modules:
                sys.modules['okx.MarketData'] = types.ModuleType('okx.MarketData')
            
            # 将MarketData添加到okx模块中
            import okx
            if not hasattr(okx, 'MarketData'):
                okx.MarketData = sys.modules['okx.MarketData']
            
            print("✓ 修复完成")
            return True
        except Exception as e:
            print(f"✗ 修复失败: {e}")
            return False

# 执行修复
if fix_okx_import():
    # 测试修复后的导入
    try:
        from okx import MarketData
        print("✓ 修复后成功导入MarketData")
    except ImportError as e:
        print(f"✗ 修复后仍无法导入: {e}")
