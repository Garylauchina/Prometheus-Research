#!/usr/bin/env python3
"""
检查VPS上的错误
"""
import paramiko
import time

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

def main():
    print("="*70)
    print("🔍 检查VPS错误")
    print("="*70)
    
    time.sleep(1)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    # 1. 检查进程
    print("\n📊 检查进程:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ps aux | grep vps_main | grep -v grep")
    if output.strip():
        print("✅ 进程运行中:")
        print(output)
    else:
        print("❌ 进程未运行")
    
    # 2. 检查日志文件
    print("\n📄 检查日志文件:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ls -lh /root/prometheus/prometheus_vps.log")
    print(output)
    
    # 3. 查看日志内容
    print("\n📝 日志内容:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "cat /root/prometheus/prometheus_vps.log")
    if output.strip():
        print(output)
    else:
        print("（日志为空）")
    
    # 4. 尝试手动启动并查看错误
    print("\n"+"="*70)
    print("🧪 尝试手动启动查看错误:")
    print("-"*70)
    output, error = execute_ssh_command(ssh, 
        "cd /root/prometheus && timeout 5 python vps_main.py --config config/vps_config.json 2>&1 || true"
    )
    print(output)
    if error.strip():
        print("STDERR:", error)
    
    # 5. 检查Python路径
    print("\n"+"="*70)
    print("🐍 检查Python环境:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "which python && python --version")
    print(output)
    
    # 6. 检查prometheus模块
    print("\n"+"="*70)
    print("📦 检查prometheus模块:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "cd /root/prometheus && python -c 'import prometheus.trading.live_engine; print(\"OK\")'")
    print(output if output.strip() else "❌ 模块加载失败")
    
    # 7. 检查live_engine.py是否更新
    print("\n"+"="*70)
    print("📝 检查live_engine.py:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "head -20 /root/prometheus/prometheus/trading/live_engine.py")
    print(output)
    
    ssh.close()
    print("\n"+"="*70)
    print("✅ 检查完成")
    print("="*70)

if __name__ == '__main__':
    main()

