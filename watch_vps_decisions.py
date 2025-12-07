#!/usr/bin/env python3
"""
实时监控VPS上的决策
"""
import paramiko
import time

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command, timeout=5):
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        return stdout.read().decode('utf-8')
    except:
        return ""

def main():
    print("="*70)
    print("👀 实时监控VPS决策（每30秒刷新）")
    print("="*70)
    print("按Ctrl+C停止\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    try:
        cycle = 0
        while True:
            cycle += 1
            
            # 获取日志
            output = execute_ssh_command(ssh, "tail -80 /root/prometheus/prometheus_vps.log", timeout=5)
            
            # 清屏
            print("\033[2J\033[H")
            
            # 显示标题
            print("="*70)
            print(f"📊 监控周期 #{cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)
            
            # 提取关键信息
            lines = output.split('\n')
            
            # 找到最近的交易周期
            for i, line in enumerate(lines):
                if '🔄 交易周期' in line:
                    # 显示从这个周期开始的所有行
                    print('\n'.join(lines[i:]))
                    break
            
            # 检查是否有决策
            if '决策:' in output or ' BUY ' in output or ' SELL ' in output:
                print("\n" + "🎉"*35)
                print("🎉 发现交易决策！")
                print("🎉"*35)
            
            # 统计决策数量
            buy_lines = [l for l in lines if '决策统计' in l and '买' in l]
            if buy_lines:
                last_stat = buy_lines[-1]
                print("\n" + "-"*70)
                print(f"最新统计: {last_stat.split('决策统计:')[-1].strip()}")
                print("-"*70)
            
            # 等待30秒
            for i in range(30, 0, -1):
                print(f"\r⏳ 下次刷新: {i}秒... ", end='', flush=True)
                time.sleep(1)
            print()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

