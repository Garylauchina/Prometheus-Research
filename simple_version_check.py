import okx

# 获取OKX版本
version = getattr(okx, '__version__', '未知')
print(f"OKX包版本: {version}")

# 尝试导入核心模块
print("\n尝试导入核心模块:")
try:
    from okx import MarketData
    print("✓ 成功导入MarketData")
except ImportError as e:
    print(f"✗ 无法导入MarketData: {e}")

try:
    from okx import Trade
    print("✓ 成功导入Trade")
except ImportError as e:
    print(f"✗ 无法导入Trade: {e}")

try:
    from okx import Account
    print("✓ 成功导入Account")
except ImportError as e:
    print(f"✗ 无法导入Account: {e}")

# 测试兼容性模块
print("\n测试兼容性模块:")
try:
    from adapters.okx_compat import apply_compatibility_fixes
    results = apply_compatibility_fixes()
    print(f"兼容性修复结果: {results}")
except Exception as e:
    print(f"兼容性测试失败: {e}")
