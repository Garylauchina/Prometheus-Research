#!/usr/bin/env python3
"""
查看VPS上的实盘日志
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
    output = stdout.read().decode('utf-8')
    return output

def main():
    print("="*70)
    print("📄 查看VPS实盘日志")
    print("="*70)
    
    time.sleep(1)  # 等待1秒避免连接太快
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    # 查看最近的日志
    print("\n📊 最近100行日志:")
    print("-"*70)
    output = execute_ssh_command(ssh, "tail -100 /root/prometheus/prometheus_vps.log")
    print(output)
    
    print("\n"+"="*70)
    print("🔍 查找最近的交易记录:")
    print("-"*70)
    output = execute_ssh_command(ssh, "grep -E '(开仓|平仓|下单|订单)' /root/prometheus/prometheus_vps.log | tail -20")
    if output.strip():
        print(output)
    else:
        print("（没有找到交易记录）")
    
    print("\n"+"="*70)
    print("📈 查找最近的Agent决策:")
    print("-"*70)
    output = execute_ssh_command(ssh, "grep -E '(决策|投票|共识)' /root/prometheus/prometheus_vps.log | tail -20")
    if output.strip():
        print(output)
    else:
        print("（没有找到决策记录）")
    
    print("\n"+"="*70)
    print("⚠️  查找错误信息:")
    print("-"*70)
    output = execute_ssh_command(ssh, "grep -iE '(error|错误|failed|失败|exception)' /root/prometheus/prometheus_vps.log | tail -10")
    if output.strip():
        print(output)
    else:
        print("✅ 没有发现错误")
    
    print("\n"+"="*70)
    print("📊 统计信息:")
    print("-"*70)
    
    # 统计日志行数
    output = execute_ssh_command(ssh, "wc -l /root/prometheus/prometheus_vps.log")
    print(f"总日志行数: {output.strip().split()[0]}")
    
    # 统计运行周期
    output = execute_ssh_command(ssh, "grep -c '交易周期\\|cycle\\|Cycle' /root/prometheus/prometheus_vps.log || echo '0'")
    print(f"交易周期数: {output.strip()}")
    
    # 查看日志开始时间
    output = execute_ssh_command(ssh, "head -1 /root/prometheus/prometheus_vps.log")
    print(f"日志开始: {output.strip()[:100]}")
    
    # 查看日志最新时间
    output = execute_ssh_command(ssh, "tail -1 /root/prometheus/prometheus_vps.log")
    print(f"日志最新: {output.strip()[:100]}")
    
    ssh.close()
    print("\n"+"="*70)
    print("✅ 检查完成")
    print("="*70)

if __name__ == '__main__':
    main()

