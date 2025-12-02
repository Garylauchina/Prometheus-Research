"""
快速启动 OKX 模拟盘测试

使用配置文件快速启动
"""

import sys
import os

# 检查配置文件
config_path = 'config/okx_config.py'
if not os.path.exists(config_path):
    print("\n" + "="*70)
    print("  ⚠️  配置文件不存在")
    print("="*70)
    print("\n请按以下步骤设置：")
    print("1. 复制 config/okx_config.example.py 为 config/okx_config.py")
    print("2. 编辑 okx_config.py，填入您的OKX模拟盘API信息")
    print("3. 重新运行此脚本")
    print("\n或者直接运行: python examples/v4_okx_paper_trading.py")
    sys.exit(1)

# 导入配置
sys.path.insert(0, 'config')
from okx_config import OKX_PAPER_TRADING, TEST_CONFIG

# 导入测试系统
sys.path.insert(0, os.path.dirname(__file__))
from examples.v4_okx_paper_trading import OKXPaperTrading, PrometheusLiveTrading, TeeOutput
from datetime import datetime


def main():
    """主函数"""
    # 设置日志输出
    start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'okx_live_test_{start_timestamp}.txt'
    tee = TeeOutput(log_filename)
    original_stdout = sys.stdout
    
    # 先显示信息（不记录到日志）
    print("\n" + "="*70)
    print("  🚀 Prometheus v4.0 - OKX模拟盘快速测试")
    print("="*70)
    print(f"  📝 日志文件: {log_filename}")
    print("="*70)
    
    print(f"\n默认配置：")
    print(f"  交易对: {TEST_CONFIG['symbol']}")
    print(f"  间隔: {TEST_CONFIG['check_interval']}秒")
    print(f"  Agent数: {TEST_CONFIG['agent_count']}")
    
    # 灵活输入测试参数
    print("\n" + "-"*70)
    print("请设置测试参数（直接回车使用默认值）：")
    print("-"*70)
    
    duration_input = input(f"测试时长（分钟，回车=不限时）: ").strip()
    if duration_input == "":
        duration_minutes = None  # 不限时
        print("  ✅ 已设置为不限时运行（Ctrl+C停止）")
    else:
        try:
            duration_minutes = int(duration_input)
            print(f"  ✅ 测试时长: {duration_minutes}分钟")
        except:
            print("  ⚠️  输入无效，使用默认10分钟")
            duration_minutes = 10
    
    interval_input = input(f"检查间隔（秒，回车={TEST_CONFIG['check_interval']}）: ").strip()
    if interval_input == "":
        check_interval = TEST_CONFIG['check_interval']
    else:
        try:
            check_interval = int(interval_input)
        except:
            check_interval = TEST_CONFIG['check_interval']
    print(f"  ✅ 检查间隔: {check_interval}秒")
    
    print("\n" + "-"*70)
    confirm = input("开始测试? (y/n): ").lower()
    if confirm != 'y':
        print("已取消")
        return
    
    try:
        
        # 开始记录到日志
        sys.stdout = tee
        
        print("\n" + "="*70)
        print("  🚀 Prometheus v4.0 - OKX模拟盘快速测试")
        print("="*70)
        print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 连接OKX
        okx_trader = OKXPaperTrading(
            api_key=OKX_PAPER_TRADING['api_key'],
            api_secret=OKX_PAPER_TRADING['api_secret'],
            passphrase=OKX_PAPER_TRADING['passphrase']
        )
        
        # 启动Prometheus
        prometheus = PrometheusLiveTrading(okx_trader, log_file=log_filename)
        
        # 运行测试
        prometheus.run_live_test(
            duration_minutes=duration_minutes,
            check_interval=check_interval
        )
        
        print("\n✅ 测试完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复stdout并关闭日志文件
        sys.stdout = original_stdout
        tee.close()
        print(f"\n✅ 日志已保存到: {log_filename}")


if __name__ == '__main__':
    main()

