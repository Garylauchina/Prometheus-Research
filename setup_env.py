"""
Prometheus v4.0 环境配置向导
帮助用户快速创建 .env 文件
"""

import os
import shutil

def setup_env():
    """环境配置向导"""
    print("=" * 60)
    print("🚀 Prometheus v4.0 环境配置向导")
    print("=" * 60)
    print()
    
    # 检查 .env 是否已存在
    if os.path.exists('.env'):
        print("⚠️  .env 文件已存在！")
        overwrite = input("是否覆盖现有配置？(y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ 配置取消")
            return
        print()
    
    # 检查是否有旧的 okx_config.py
    old_config_path = 'config/okx_config.py'
    migrate_from_old = False
    
    if os.path.exists(old_config_path):
        print("📦 检测到旧配置文件: config/okx_config.py")
        migrate = input("是否从旧配置迁移？(Y/n): ").strip().lower()
        if migrate != 'n':
            migrate_from_old = True
    
    print()
    print("请输入您的 OKX API 配置：")
    print("-" * 60)
    
    # 如果从旧配置迁移
    if migrate_from_old:
        print("🔄 正在从旧配置读取...")
        try:
            # 动态导入旧配置
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from config.okx_config import OKX_PAPER_TRADING
            
            api_key = OKX_PAPER_TRADING['api_key']
            api_secret = OKX_PAPER_TRADING['api_secret']
            passphrase = OKX_PAPER_TRADING['passphrase']
            
            print(f"✅ API Key: {api_key[:8]}...{api_key[-4:]}")
            print(f"✅ API Secret: {api_secret[:8]}...{api_secret[-4:]}")
            print(f"✅ Passphrase: {'*' * len(passphrase)}")
            print()
        except Exception as e:
            print(f"⚠️  读取旧配置失败: {e}")
            print("请手动输入配置...")
            migrate_from_old = False
    
    # 手动输入
    if not migrate_from_old:
        api_key = input("OKX API Key: ").strip()
        api_secret = input("OKX API Secret: ").strip()
        passphrase = input("OKX Passphrase: ").strip()
        
        if not all([api_key, api_secret, passphrase]):
            print("\n❌ 错误: 所有字段都必须填写！")
            return
    
    # 其他配置
    print()
    print("-" * 60)
    sandbox = input("使用模拟盘？(Y/n): ").strip().lower()
    use_sandbox = sandbox != 'n'
    
    log_level = input("日志级别 (DEBUG/INFO/WARNING/ERROR) [INFO]: ").strip().upper()
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        log_level = 'INFO'
    
    # 创建 .env 文件
    print()
    print("📝 正在创建 .env 文件...")
    
    env_content = f"""# Prometheus v4.0 配置文件
# ⚠️ 此文件包含敏感信息，不要提交到Git！

# OKX API 配置
OKX_API_KEY={api_key}
OKX_API_SECRET={api_secret}
OKX_PASSPHRASE={passphrase}

# 交易模式 (True=模拟盘, False=实盘)
OKX_SANDBOX={'True' if use_sandbox else 'False'}

# 日志级别 (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL={log_level}
"""
    
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ .env 文件创建成功！")
        print()
        
        # 验证配置
        print("🔍 验证配置...")
        try:
            from config.config import validate_config
            validate_config()
            print("✅ 配置验证通过！")
        except Exception as e:
            print(f"⚠️  配置验证失败: {e}")
        
        print()
        print("=" * 60)
        print("🎉 配置完成！您现在可以运行 Prometheus v4.0 了")
        print("=" * 60)
        print()
        print("启动命令:")
        print("  python run_simplified_launcher.py")
        print()
        
        # 提示是否备份旧配置
        if migrate_from_old:
            print("💡 提示: 旧配置文件仍保留在 config/okx_config.py")
            backup = input("是否备份旧配置？(Y/n): ").strip().lower()
            if backup != 'n':
                backup_path = 'config/okx_config.py.backup'
                shutil.copy(old_config_path, backup_path)
                print(f"✅ 已备份到: {backup_path}")
                print("   您可以安全删除 config/okx_config.py")
        
    except Exception as e:
        print(f"\n❌ 创建 .env 文件失败: {e}")
        return

if __name__ == "__main__":
    try:
        setup_env()
    except KeyboardInterrupt:
        print("\n\n❌ 配置已取消")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

