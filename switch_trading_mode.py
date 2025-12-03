"""
Prometheus v4.0 - 交易模式切换工具
快速切换 mock 和 okx 模式
"""

import os
import sys

def read_env():
    """读取.env文件"""
    if not os.path.exists('.env'):
        return {}
    
    env_vars = {}
    with open('.env', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def write_env(env_vars):
    """写入.env文件"""
    with open('.env', 'w', encoding='utf-8') as f:
        f.write("# Prometheus v4.0 配置文件\n\n")
        f.write("# 交易数据源选择\n")
        f.write(f"TRADING_MODE={env_vars.get('TRADING_MODE', 'mock')}\n\n")
        
        f.write("# OKX API 配置\n")
        f.write(f"OKX_API_KEY={env_vars.get('OKX_API_KEY', 'your_api_key_here')}\n")
        f.write(f"OKX_API_SECRET={env_vars.get('OKX_API_SECRET', 'your_api_secret_here')}\n")
        f.write(f"OKX_PASSPHRASE={env_vars.get('OKX_PASSPHRASE', 'your_passphrase_here')}\n")
        f.write(f"OKX_SANDBOX={env_vars.get('OKX_SANDBOX', 'True')}\n\n")
        
        f.write("# 日志级别\n")
        f.write(f"LOG_LEVEL={env_vars.get('LOG_LEVEL', 'INFO')}\n")

def main():
    """主函数"""
    print("=" * 60)
    print("🔄 Prometheus v4.0 - 交易模式切换工具")
    print("=" * 60)
    print()
    
    # 读取当前配置
    env_vars = read_env()
    current_mode = env_vars.get('TRADING_MODE', 'mock')
    
    print(f"当前模式: {current_mode.upper()}")
    print()
    print("可用模式:")
    print("  1. mock  - 模拟数据（快速调试，无需网络）")
    print("  2. okx   - OKX模拟盘（真实环境测试）")
    print()
    
    # 获取用户选择
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    else:
        choice = input("请选择模式 (1/2 或 mock/okx): ").strip().lower()
    
    # 解析选择
    if choice in ['1', 'mock']:
        new_mode = 'mock'
    elif choice in ['2', 'okx']:
        new_mode = 'okx'
    else:
        print(f"❌ 无效选择: {choice}")
        return
    
    # 更新配置
    env_vars['TRADING_MODE'] = new_mode
    write_env(env_vars)
    
    print()
    print(f"✅ 已切换到 {new_mode.upper()} 模式")
    print()
    
    if new_mode == 'mock':
        print("📊 模拟数据模式特点:")
        print("  • ⚡ 快速响应，无网络延迟")
        print("  • 🚀 适合快速测试系统逻辑")
        print("  • 🎲 自动生成合理的价格波动")
        print("  • 💡 不需要API密钥")
    else:
        print("🌐 OKX模拟盘模式特点:")
        print("  • 📈 真实市场数据")
        print("  • 🔄 真实的API交互")
        print("  • ⚠️  需要配置API密钥")
        
        # 检查API配置
        if env_vars.get('OKX_API_KEY') == 'your_api_key_here':
            print()
            print("⚠️  警告: 检测到API密钥尚未配置")
            print("   请编辑 .env 文件填入真实的API密钥")
    
    print()
    print("重启系统后生效: python run_simplified_launcher.py")
    print()

if __name__ == "__main__":
    main()

