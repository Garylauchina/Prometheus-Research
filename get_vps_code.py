#!/usr/bin/env python3
"""
获取VPS上的关键代码文件
"""
import paramiko
import time

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command):
    """执行SSH命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(command)
    return stdout.read().decode('utf-8')

def main():
    print("="*70)
    print("📥 获取VPS上的vps_main.py代码")
    print("="*70)
    
    time.sleep(1)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    # 获取vps_main.py
    print("\n📄 vps_main.py (前200行):")
    print("-"*70)
    output = execute_ssh_command(ssh, "head -200 /root/prometheus/vps_main.py")
    print(output)
    
    # 查找交易相关的函数
    print("\n"+"="*70)
    print("🔍 查找交易相关函数:")
    print("-"*70)
    output = execute_ssh_command(ssh, "grep -n 'def.*trade\\|def.*order\\|def.*position' /root/prometheus/vps_main.py")
    print(output)
    
    # 查看是否有交易决策的代码
    print("\n"+"="*70)
    print("🔍 查找决策相关代码:")
    print("-"*70)
    output = execute_ssh_command(ssh, "grep -n 'decision\\|decide\\|vote' /root/prometheus/vps_main.py | head -20")
    print(output if output.strip() else "（没有找到）")
    
    # 查看配置中的共识阈值
    print("\n"+"="*70)
    print("⚙️  检查配置文件中的交易参数:")
    print("-"*70)
    output = execute_ssh_command(ssh, "cat /root/prometheus/config/vps_config.json | python3 -m json.tool")
    print(output)
    
    ssh.close()
    print("\n"+"="*70)
    print("✅ 获取完成")
    print("="*70)

if __name__ == '__main__':
    main()

