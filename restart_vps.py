#!/usr/bin/env python3
"""
重启VPS系统（使用python3）
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
    print("🚀 重启VPS系统")
    print("="*70)
    
    time.sleep(1)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    # 1. 停止旧进程
    print("\n⏹️  停止旧进程...")
    execute_ssh_command(ssh, "pkill -f vps_main.py")
    time.sleep(2)
    print("✅ 完成")
    
    # 2. 清空日志
    print("\n📝 清空日志...")
    execute_ssh_command(ssh, "echo '' > /root/prometheus/prometheus_vps.log")
    print("✅ 完成")
    
    # 3. 启动（使用python3）
    print("\n🚀 启动系统（使用python3）...")
    cmd = (
        "cd /root/prometheus && "
        "nohup python3 vps_main.py --config config/vps_config.json "
        "> /dev/null 2>&1 & "
        "echo $!"
    )
    output, _ = execute_ssh_command(ssh, cmd)
    new_pid = output.strip()
    print(f"✅ 系统已启动 (PID: {new_pid})")
    
    # 4. 等待启动
    print("\n⏳ 等待10秒...")
    time.sleep(10)
    
    # 5. 检查进程
    print("\n📊 检查进程状态:")
    output, _ = execute_ssh_command(ssh, f"ps -fp {new_pid}")
    if output.strip() and new_pid in output:
        print("✅ 进程运行正常")
        print(output)
    else:
        print("❌ 进程未运行，查看错误...")
        output, _ = execute_ssh_command(ssh, "cat /root/prometheus/prometheus_vps.log | head -50")
        print(output)
    
    # 6. 查看初始日志
    print("\n"+"="*70)
    print("📄 初始日志:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "tail -50 /root/prometheus/prometheus_vps.log")
    print(output)
    
    # 7. 实时监控
    print("\n"+"="*70)
    print("📊 实时监控（2分钟）...")
    print("="*70)
    
    try:
        for i in range(12):
            time.sleep(10)
            output, _ = execute_ssh_command(ssh, "tail -40 /root/prometheus/prometheus_vps.log")
            
            print(f"\n[{i+1}/12] {time.strftime('%H:%M:%S')}")
            print("-"*70)
            print(output[-1000:])  # 最后1000字符
            
            # 检查决策
            if "决策:" in output or "BUY" in output or "SELL" in output or "决策统计" in output:
                print("\n" + "="*70)
                print("🎉 发现决策记录！")
                print("="*70)
                break
    
    except KeyboardInterrupt:
        print("\n⏹️  监控已停止")
    
    ssh.close()
    print("\n"+"="*70)
    print("✅ 完成")
    print("="*70)

if __name__ == '__main__':
    main()

