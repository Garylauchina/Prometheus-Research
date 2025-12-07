#!/usr/bin/env python3
"""
详细检查VPS上运行的Python进程
"""
import paramiko

VPS_HOST = "45.76.97.37"
VPS_USER = "root"
VPS_PASSWORD = "9a%ZwL}gfx+c8eVz"
VPS_PORT = 22

def execute_ssh_command(ssh, command):
    """执行SSH命令并返回输出"""
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return output, error

def main():
    print("="*70)
    print("🔍 详细检查VPS上的Python进程 (PID: 4558)")
    print("="*70)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VPS_HOST, VPS_PORT, VPS_USER, VPS_PASSWORD, timeout=10)
    
    # 1. 检查进程详细信息
    print("\n📊 进程详细信息:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ps -fp 4558")
    print(output)
    
    # 2. 检查进程的工作目录
    print("\n📁 进程工作目录:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "pwdx 4558")
    print(output)
    
    # 3. 查看进程的完整命令行
    print("\n💻 完整命令行:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "cat /proc/4558/cmdline | tr '\\0' ' '")
    print(output)
    
    # 4. 检查进程打开的文件
    print("\n📄 进程打开的日志文件:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "lsof -p 4558 | grep -E '(log|txt|json|csv)'")
    print(output if output.strip() else "（没有找到日志文件）")
    
    # 5. 找到实际工作目录并列出文件
    output, _ = execute_ssh_command(ssh, "pwdx 4558 | awk '{print $2}'")
    work_dir = output.strip()
    
    if work_dir:
        print(f"\n📂 工作目录内容: {work_dir}")
        print("-"*70)
        output, _ = execute_ssh_command(ssh, f"ls -lht {work_dir}/*.log 2>&1 | head -10")
        print(output)
        
        print(f"\n📂 工作目录所有文件:")
        print("-"*70)
        output, _ = execute_ssh_command(ssh, f"ls -lh {work_dir} | head -30")
        print(output)
        
        # 6. 检查是否有输出重定向
        print(f"\n📝 检查nohup.out或其他输出文件:")
        print("-"*70)
        output, _ = execute_ssh_command(ssh, f"ls -lh {work_dir}/nohup.out {work_dir}/*.out 2>&1")
        print(output)
        
        # 7. 查看最近的日志内容
        print(f"\n📄 最近的日志内容:")
        print("-"*70)
        output, _ = execute_ssh_command(ssh, f"tail -100 {work_dir}/vps_main.log 2>&1 || tail -100 {work_dir}/nohup.out 2>&1 || echo '未找到日志文件'")
        print(output)
    
    # 8. 检查config文件
    print("\n⚙️  配置文件内容:")
    print("-"*70)
    if work_dir:
        output, _ = execute_ssh_command(ssh, f"cat {work_dir}/config/vps_config.json 2>&1")
        print(output)
    
    # 9. 检查进程运行时长
    print("\n⏱️  进程运行时长:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ps -eo pid,etime,cmd | grep 4558 | grep -v grep")
    print(output)
    
    # 10. 检查CPU和内存使用
    print("\n💾 资源使用:")
    print("-"*70)
    output, _ = execute_ssh_command(ssh, "ps -p 4558 -o pid,%cpu,%mem,vsz,rss,cmd")
    print(output)
    
    ssh.close()
    print("="*70)
    print("✅ 检查完成")
    print("="*70)

if __name__ == '__main__':
    main()

