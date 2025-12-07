#!/usr/bin/env python3
"""
部署修复到VPS
===========

步骤：
1. 停止当前运行的vps_main.py
2. 备份原来的live_engine.py
3. 上传修复版本
4. 重启vps_main.py
5. 实时监控日志
"""

import paramiko
import time
import sys

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command, wait=True):
    """执行SSH命令"""
    stdin, stdout, stderr = ssh.exec_command(command)
    if wait:
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return output, error
    return None, None

def upload_file(ssh, local_path, remote_path):
    """上传文件"""
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()

def main():
    print("="*70)
    print("🚀 部署修复到VPS")
    print("="*70)
    
    time.sleep(1)
    
    # 连接VPS
    print("\n📡 连接VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    print("✅ 连接成功")
    
    # 1. 检查当前运行的进程
    print("\n"+"="*70)
    print("🔍 检查运行中的进程...")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ps aux | grep vps_main.py | grep -v grep")
    if output.strip():
        print(output)
        pid = output.strip().split()[1]
        print(f"\n⚠️  发现运行中的进程 (PID: {pid})")
        
        # 自动停止进程
        print(f"⏹️  停止进程 {pid}...")
        execute_ssh_command(ssh, f"kill {pid}")
        time.sleep(2)
        print("✅ 进程已停止")
    else:
        print("✅ 没有运行中的进程")
    
    # 2. 备份原文件
    print("\n"+"="*70)
    print("💾 备份原文件...")
    print("-"*70)
    execute_ssh_command(ssh, 
        "cp /root/prometheus/prometheus/trading/live_engine.py "
        "/root/prometheus/prometheus/trading/live_engine.py.backup.$(date +%Y%m%d_%H%M%S)"
    )
    print("✅ 备份完成")
    
    # 3. 上传修复版本
    print("\n"+"="*70)
    print("📤 上传修复版本...")
    print("-"*70)
    local_file = "prometheus/trading/live_engine_fixed.py"
    remote_file = "/root/prometheus/prometheus/trading/live_engine.py"
    
    try:
        upload_file(ssh, local_file, remote_file)
        print("✅ 上传成功")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        ssh.close()
        return
    
    # 4. 显示修改内容
    print("\n"+"="*70)
    print("📝 关键修改:")
    print("-"*70)
    print("""
    1. 决策阈值: 0.1% → 0.01% (降低10倍)
    2. 决策日志: DEBUG → INFO (可见)
    3. 决策统计: 显示买/卖/持有数量
    4. 详细记录: Agent ID + 资金
    """)
    
    # 5. 自动重启
    print("\n"+"="*70)
    print("🔄 准备重启系统")
    print("-"*70)
    
    # 6. 重启系统
    print("\n🚀 重启系统...")
    
    # 清空旧日志
    print("📝 清空旧日志...")
    execute_ssh_command(ssh, "echo '' > /root/prometheus/prometheus_vps.log")
    print("✅ 日志已清空")
    
    # 后台启动
    cmd = (
        "cd /root/prometheus && "
        "nohup python vps_main.py --config config/vps_config.json "
        "> /dev/null 2>&1 & "
        "echo $!"
    )
    output, _ = execute_ssh_command(ssh, cmd)
    new_pid = output.strip()
    
    print(f"✅ 系统已重启 (PID: {new_pid})")
    
    # 7. 等待启动
    print("\n⏳ 等待系统启动...")
    time.sleep(5)
    
    # 8. 检查进程
    output, _ = execute_ssh_command(ssh, f"ps -p {new_pid} -o pid,cmd")
    if new_pid in output:
        print("✅ 系统运行正常")
    else:
        print("❌ 系统可能启动失败，请检查日志")
    
    # 9. 显示最新日志
    print("\n"+"="*70)
    print("📄 最新日志 (实时更新中):")
    print("-"*70)
    
    # 实时监控日志（最多2分钟）
    print("\n⏱️  监控日志2分钟，看是否有决策触发...")
    print("（按Ctrl+C随时停止）\n")
    
    try:
        for i in range(12):  # 12次 × 10秒 = 2分钟
            output, _ = execute_ssh_command(ssh, "tail -30 /root/prometheus/prometheus_vps.log")
            
            # 清屏并显示
            print("\033[2J\033[H")  # 清屏
            print("="*70)
            print(f"📊 日志监控 ({i+1}/12) - {time.strftime('%H:%M:%S')}")
            print("="*70)
            print(output)
            
            # 检查是否有决策记录
            if "决策:" in output or "BUY" in output or "SELL" in output:
                print("\n" + "="*70)
                print("🎉 发现决策记录！修复有效！")
                print("="*70)
                break
            
            if i < 11:
                time.sleep(10)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    
    ssh.close()
    
    print("\n"+"="*70)
    print("✅ 部署完成")
    print("="*70)
    print("\n📝 后续操作:")
    print("  1. 继续监控: python view_vps_log.py")
    print("  2. 查看进程: ssh root@45.76.97.37 'ps aux | grep vps_main'")
    print("  3. 停止系统: ssh root@45.76.97.37 'pkill -f vps_main.py'")
    print()

if __name__ == '__main__':
    main()

