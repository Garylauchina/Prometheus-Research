"""
OKX API 深度调试工具
"""

import ccxt
import json

print("\n" + "="*70)
print("  OKX API 深度调试")
print("="*70)

api_key = input("\nAPI Key: ").strip()
api_secret = input("API Secret: ").strip()
passphrase = input("Passphrase: ").strip()

print("\n" + "="*70)
print("  测试各种demo配置方式")
print("="*70)

# 测试1: demo in options
print("\n【测试1】options: {'demo': True}")
try:
    exchange = ccxt.okx({
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
        'options': {'demo': True}
    })
    print(f"URLs: {exchange.urls}")
    balance = exchange.fetch_balance()
    print("✅ 成功！")
    print(f"余额: {balance.get('USDT', {}).get('free', 'N/A')}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试2: sandbox模式
print("\n【测试2】sandbox: True")
try:
    exchange = ccxt.okx({
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
        'sandbox': True
    })
    print(f"URLs: {exchange.urls}")
    balance = exchange.fetch_balance()
    print("✅ 成功！")
    print(f"余额: {balance.get('USDT', {}).get('free', 'N/A')}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试3: 直接设置URL
print("\n【测试3】手动设置test URL")
try:
    exchange = ccxt.okx({
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
    })
    
    # 检查是否有test URL
    if 'test' in exchange.urls:
        print(f"Test URL存在: {exchange.urls['test']}")
        exchange.urls['api'] = exchange.urls['test']
    else:
        print("❌ 没有test URL")
    
    print(f"当前API URL: {exchange.urls.get('api')}")
    balance = exchange.fetch_balance()
    print("✅ 成功！")
    print(f"余额: {balance.get('USDT', {}).get('free', 'N/A')}")
except Exception as e:
    print(f"❌ 失败: {e}")

# 测试4: 检查exchange信息
print("\n【测试4】Exchange信息")
try:
    exchange = ccxt.okx({
        'apiKey': api_key,
        'secret': api_secret,
        'password': passphrase,
    })
    
    print(f"Exchange ID: {exchange.id}")
    print(f"Exchange name: {exchange.name}")
    print(f"Has sandbox: {exchange.has.get('sandbox', False)}")
    print(f"URLs: {json.dumps(exchange.urls, indent=2)}")
    
    # 检查可用的选项
    if hasattr(exchange, 'options'):
        print(f"Options: {json.dumps(exchange.options, indent=2, default=str)}")
    
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "="*70)
print("  关键发现")
print("="*70)

print("""
根据ccxt文档，OKX可能不支持通过ccxt的标准方式切换到模拟盘。

【问题根源】
1. OKX的模拟盘API和实盘API使用相同的endpoint
2. 区别在于API Key本身的创建位置
3. 如果API Key是在实盘创建的，ccxt无法让它连接模拟盘

【解决方案】
唯一的解决方案是：
1. 确保API在正确的地方创建（模拟盘交易页面）
2. 访问 https://www.okx.com/trade-demo
3. 在该页面的"资产"->"API"中创建
4. 不是在主账户的API管理中创建

【验证方法】
如果您能在OKX模拟盘页面看到：
- 账户余额: 124,696 USDT
- 并且可以正常交易
那么您需要在**同一个页面**的API管理中创建API

【另一个选项】
如果ccxt无法连接模拟盘，可以考虑：
1. 使用OKX官方Python SDK
2. 或者使用历史数据回测（不连接API）
""")

input("\n按回车键退出...")

