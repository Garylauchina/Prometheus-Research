import okx
import pkgutil
import sys

# 打印OKX包的内容
print("OKX包可用属性:")
print(dir(okx))

# 列出OKX包中的子模块
print("\nOKX包中的子模块:")
for _, name, is_pkg in pkgutil.iter_modules(okx.__path__):
    print(f"{name} {'(package)' if is_pkg else ''}")

# 打印OKX版本信息
print(f"\nOKX版本: {getattr(okx, '__version__', '未找到版本信息')}")

# 测试不同的导入方式
try:
    print("\n尝试导入方式1: from okx import MarketData")
    from okx import MarketData
    print("✓ 导入成功!")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

try:
    print("\n尝试导入方式2: from okx.MarketData import MarketData")
    from okx.MarketData import MarketData
    print("✓ 导入成功!")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

try:
    print("\n尝试导入方式3: from okx import MarketDataAPI")
    from okx import MarketDataAPI
    print("✓ 导入成功!")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

try:
    print("\n尝试导入方式4: from okx.MarketData import MarketDataAPI")
    from okx.MarketData import MarketDataAPI
    print("✓ 导入成功!")
except ImportError as e:
    print(f"✗ 导入失败: {e}")

# 检查是否有其他可能的行情数据模块
print("\n搜索其他可能的行情数据模块:")
try:
    # 尝试直接列出okx包下所有可能相关的模块
    for _, name, _ in pkgutil.iter_modules(okx.__path__):
        if 'market' in name.lower():
            print(f"找到相关模块: {name}")
except Exception as e:
    print(f"搜索失败: {e}")

# 尝试简单导入okx的所有模块，看能否找到行情数据相关功能
print("\n尝试直接导入并检查okx模块中的行情数据功能:")
try:
    # 检查是否有market或data相关的属性
    for attr in dir(okx):
        if 'market' in attr.lower() or 'data' in attr.lower():
            print(f"找到可能相关的属性: {attr}")
except Exception as e:
    print(f"检查失败: {e}")