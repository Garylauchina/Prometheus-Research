#!/usr/bin/env python3
"""
快速重启VPS（简化版，无卡顿）
"""
import paramiko
import time

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command, timeout=5):
    """执行SSH命令，带超时"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8')
        return output
    except Exception as e:
        return f"Error: {e}"

def main():
    print("🚀 快速重启VPS系统\n")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("📡 连接中...", end=" ")
        ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
        print("✅")
        
        # 1. 停止旧进程
        print("⏹️  停止旧进程...", end=" ")
        execute_ssh_command(ssh, "pkill -f vps_main.py", timeout=3)
        time.sleep(2)
        print("✅")
        
        # 2. 启动新进程（使用python3）
        print("🚀 启动系统...", end=" ")
        cmd = "cd /root/prometheus && nohup python3 vps_main.py --config config/vps_config.json > /dev/null 2>&1 & echo $!"
        pid = execute_ssh_command(ssh, cmd, timeout=3).strip()
        print(f"✅ (PID: {pid})")
        
        # 3. 等待启动
        print("⏳ 等待15秒...")
        time.sleep(15)
        
        # 4. 检查进程
        print("📊 检查进程...", end=" ")
        output = execute_ssh_command(ssh, f"ps -p {pid} -o pid,cmd", timeout=3)
        if pid in output:
            print("✅ 运行中")
        else:
            print("❌ 未运行")
        
        # 5. 查看日志
        print("\n" + "="*70)
        print("📄 最新日志:")
        print("="*70)
        output = execute_ssh_command(ssh, "tail -50 /root/prometheus/prometheus_vps.log", timeout=5)
        print(output)
        
        print("\n" + "="*70)
        print("✅ 完成！系统已启动")
        print("="*70)
        print("\n💡 查看实时日志：")
        print("   python3 view_vps_log.py")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    main()

