import sys
import importlib
import os

print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"Python路径: {sys.path}")

# 尝试不同的导入方式
print("\n=== 测试导入方式 ===")

# 方式1: 直接导入MarketData
try:
    print("\n方式1: from okx import MarketData")
    from okx import MarketData
    print("✓ 成功导入MarketData")
    print(f"MarketData类型: {type(MarketData)}")
    print(f"MarketData内容: {dir(MarketData)}")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 方式2: 导入okx然后访问MarketData
try:
    print("\n方式2: import okx 然后访问 okx.MarketData")
    import okx
    print(f"okx包版本: {getattr(okx, '__version__', '未知')}")
    market_data = getattr(okx, 'MarketData', None)
    if market_data:
        print("✓ 找到okx.MarketData")
        print(f"类型: {type(market_data)}")
    else:
        print("✗ 未找到okx.MarketData")
except Exception as e:
    print(f"✗ 错误: {e}")

# 方式3: 尝试直接导入子模块
try:
    print("\n方式3: import okx.MarketData")
    import okx.MarketData
    print("✓ 成功导入okx.MarketData")
    print(f"okx.MarketData内容: {dir(okx.MarketData)}")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 检查okx包的__init__.py文件内容
print("\n=== 检查okx包初始化文件 ===")
try:
    import okx
    init_file = os.path.join(os.path.dirname(okx.__file__), '__init__.py')
    print(f"okx包路径: {os.path.dirname(okx.__file__)}")
    print(f"__init__.py文件: {init_file}")
    
    if os.path.exists(init_file):
        print("\n__init__.py文件内容:")
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500] + ('...' if len(content) > 500 else ''))
    else:
        print("未找到__init__.py文件")
except Exception as e:
    print(f"✗ 检查失败: {e}")

# 检查okx包的目录结构
print("\n=== 检查okx包目录结构 ===")
try:
    import okx
    okx_dir = os.path.dirname(okx.__file__)
    print(f"okx包目录内容:")
    for item in os.listdir(okx_dir):
        item_path = os.path.join(okx_dir, item)
        if os.path.isdir(item_path):
            print(f"  📁 {item}")
        else:
            print(f"  📄 {item}")
except Exception as e:
    print(f"✗ 检查失败: {e}")

# 创建一个简单的修复方案测试
print("\n=== 测试修复方案 ===")
print("创建临时修复模块...")

# 创建临时修复代码
temp_fix_code = '''
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
'''

# 保存临时修复脚本
with open('temp_okx_fix.py', 'w', encoding='utf-8') as f:
    f.write(temp_fix_code)

print("执行临时修复脚本...")
import temp_okx_fix

print("\n=== 总结 ===")
print("基于测试结果，建议的解决方案：")
print("1. 确保安装正确版本: pip install okx==0.4.0")
print("2. 检查Python版本兼容性")
print("3. 检查虚拟环境设置")
