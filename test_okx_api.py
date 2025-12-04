"""
OKX API 连接测试工具

用于诊断API配置问题
"""

import sys
import ccxt
import json

def test_api_connection():
    """测试API连接"""
    
    print("\n" + "="*70)
    print("  OKX API 连接诊断工具")
    print("="*70)
    
    # 输入API信息
    print("\n请输入API信息（直接复制粘贴）：")
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    passphrase = input("Passphrase: ").strip()
    
    if not all([api_key, api_secret, passphrase]):
        print("\n❌ API信息不完整")
        return
    
    print("\n" + "="*70)
    print("  测试1：基础配置")
    print("="*70)
    
    print(f"\nAPI Key长度: {len(api_key)}")
    print(f"API Secret长度: {len(api_secret)}")
    print(f"Passphrase长度: {len(passphrase)}")
    
    # 检查是否有隐藏字符
    if api_key != api_key.strip():
        print("⚠️  API Key包含前后空格")
    if api_secret != api_secret.strip():
        print("⚠️  API Secret包含前后空格")
    if passphrase != passphrase.strip():
        print("⚠️  Passphrase包含前后空格")
    
    print("\n" + "="*70)
    print("  测试2：默认配置连接")
    print("="*70)
    
    try:
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
        })
        
        print("\n✅ Exchange对象创建成功")
        print(f"   默认URL: {exchange.urls.get('api', 'N/A')}")
        
        # 尝试获取余额
        print("\n   尝试获取余额...")
        balance = exchange.fetch_balance()
        
        print("✅ 余额获取成功！")
        print(f"   USDT余额: {balance.get('USDT', {}).get('free', 'N/A')}")
        print(f"   总资产: {balance.get('total', {})}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        if "50101" in str(e):
            print("\n【错误50101分析】")
            print("这个错误表示：API密钥与环境不匹配")
            print("\n可能原因：")
            print("1. API是实盘创建的，但代码尝试连接模拟盘")
            print("2. API是模拟盘创建的，但代码尝试连接实盘")
            print("3. Passphrase输入错误")
            print("4. API密钥复制时有误")
    
    print("\n" + "="*70)
    print("  测试3：尝试不同配置")
    print("="*70)
    
    # 测试配置1：启用demo模式
    print("\n配置1: 启用demo模式")
    try:
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'demo': True,  # 模拟盘模式
            }
        })
        balance = exchange.fetch_balance()
        print("✅ Demo模式成功！")
        print(f"   USDT余额: {balance.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)[:100]}")
    
    # 测试配置2：明确指定为swap + demo
    print("\n配置2: Swap + Demo模式")
    try:
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'demo': True,
            }
        })
        balance = exchange.fetch_balance()
        print("✅ Swap+Demo配置成功")
        print(f"   USDT余额: {balance.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)[:100]}")
    
    # 测试配置3：尝试spot + demo
    print("\n配置3: Spot + Demo模式")
    try:
        exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'demo': True,
            }
        })
        balance = exchange.fetch_balance()
        print("✅ Spot+Demo配置成功")
        print(f"   USDT余额: {balance.get('USDT', {}).get('free', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ 失败: {str(e)[:100]}")
    
    print("\n" + "="*70)
    print("  诊断建议")
    print("="*70)
    
    print("\n如果所有测试都失败，请检查：")
    print("1. 【最重要】确认API在'模拟盘交易'页面创建")
    print("   - 不是在'资产'->'API管理'创建（那是实盘）")
    print("   - 应该在'交易'->'模拟盘交易'->'资产'->'API'创建")
    print("\n2. 检查Passphrase是否正确")
    print("   - 区分大小写")
    print("   - 没有多余空格")
    print("\n3. 检查API权限")
    print("   - 必须勾选'交易'权限")
    print("   - 可以勾选'读取'权限")
    print("\n4. 等待API生效")
    print("   - 新创建的API需要1-2分钟生效")
    print("\n5. 重新创建API")
    print("   - 如果以上都不行，删除旧API")
    print("   - 重新在'模拟盘交易'页面创建")


if __name__ == '__main__':
    try:
        test_api_connection()
    except KeyboardInterrupt:
        print("\n\n测试中断")
    except Exception as e:
        print(f"\n程序错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")

