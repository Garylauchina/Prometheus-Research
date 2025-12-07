#!/usr/bin/env python3
"""
快速检查VPS上的运行状态
"""
import paramiko
import sys

# VPS配置
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
    print("🔗 正在连接VPS: {}".format(VPS_HOST))
    print("="*70)
    
    try:
        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 连接
        ssh.connect(
            hostname=VPS_HOST,
            port=VPS_PORT,
            username=VPS_USER,
            password=VPS_PASSWORD,
            timeout=10
        )
        
        print("✅ SSH连接成功！\n")
        
        # 1. 检查Python进程
        print("="*70)
        print("📊 检查运行中的Python进程")
        print("="*70)
        output, error = execute_ssh_command(ssh, "ps aux | grep python | grep -v grep")
        if output.strip():
            print(output)
        else:
            print("⚠️  没有发现运行中的Python进程\n")
        
        # 2. 检查工作目录
        print("="*70)
        print("📁 检查Prometheus工作目录")
        print("="*70)
        output, error = execute_ssh_command(ssh, "ls -lh /root/Prometheus-Quant/*.log 2>&1 | head -10")
        print(output)
        
        # 3. 检查最近的日志文件
        print("="*70)
        print("📝 最近修改的日志文件")
        print("="*70)
        output, error = execute_ssh_command(ssh, "cd /root/Prometheus-Quant && ls -lht *.log 2>&1 | head -5")
        print(output)
        
        # 4. 检查是否有nohup进程
        print("="*70)
        print("🔍 检查nohup后台进程")
        print("="*70)
        output, error = execute_ssh_command(ssh, "ps aux | grep nohup | grep -v grep")
        if output.strip():
            print(output)
        else:
            print("⚠️  没有发现nohup后台进程\n")
        
        # 5. 检查最近的日志内容（尾部）
        print("="*70)
        print("📄 检查ultimate_1000x_output.log的最新内容")
        print("="*70)
        output, error = execute_ssh_command(ssh, "cd /root/Prometheus-Quant && tail -50 ultimate_1000x_output.log 2>&1")
        print(output)
        
        # 6. 检查系统负载
        print("="*70)
        print("💻 VPS系统状态")
        print("="*70)
        output, error = execute_ssh_command(ssh, "uptime")
        print("Uptime:", output)
        output, error = execute_ssh_command(ssh, "free -h")
        print("\nMemory:")
        print(output)
        
        # 7. 检查当前目录
        print("="*70)
        print("📂 当前工作目录内容")
        print("="*70)
        output, error = execute_ssh_command(ssh, "cd /root/Prometheus-Quant && pwd && ls -lh | head -20")
        print(output)
        
        ssh.close()
        print("="*70)
        print("✅ 检查完成")
        print("="*70)
        
    except paramiko.ssh_exception.AuthenticationException:
        print("❌ 认证失败：用户名或密码错误")
        sys.exit(1)
    except paramiko.ssh_exception.NoValidConnectionsError:
        print("❌ 连接失败：无法连接到VPS")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

