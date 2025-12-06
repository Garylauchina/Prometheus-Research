#!/usr/bin/env python3
"""
VPS监控脚本 v2.0（自动密码登录）
==================================

从本地Mac监控VPS上Prometheus的运行状态
使用.env文件存储VPS密码，自动登录

依赖：
    pip install paramiko python-dotenv

用法：
    python monitor_vps_v2.py
"""

import os
import re
from datetime import datetime

try:
    import paramiko
    from dotenv import load_dotenv
    DEPS_OK = True
except ImportError:
    DEPS_OK = False
    print("❌ 缺少依赖库！")
    print()
    print("请安装：")
    print("   pip install paramiko python-dotenv")
    print()
    exit(1)

# 加载.env配置
load_dotenv()

VPS_HOST = os.getenv('VPS_HOST', '45.76.97.37')
VPS_USER = os.getenv('VPS_USER', 'root')
VPS_PASSWORD = os.getenv('VPS_PASSWORD')
VPS_PORT = int(os.getenv('VPS_PORT', '22'))

if not VPS_PASSWORD:
    print("❌ 未找到VPS密码！")
    print()
    print("请创建 .env 文件并填入密码：")
    print("   cp vps_config_example.txt .env")
    print("   vim .env")
    print()
    exit(1)


class VPSMonitor:
    """VPS监控器"""
    
    def __init__(self):
        self.ssh = None
        self.connected = False
    
    def connect(self):
        """连接VPS"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            print(f"🔌 连接VPS: {VPS_USER}@{VPS_HOST}...")
            self.ssh.connect(
                hostname=VPS_HOST,
                port=VPS_PORT,
                username=VPS_USER,
                password=VPS_PASSWORD,
                timeout=10
            )
            self.connected = True
            print("✅ 连接成功")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def run_command(self, command):
        """执行命令"""
        if not self.connected:
            return None
        
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error and 'No such file' not in error:
                print(f"⚠️  警告: {error}")
            
            return output
        except Exception as e:
            print(f"❌ 命令执行失败: {e}")
            return None
    
    def get_latest_status(self):
        """获取最新状态"""
        output = self.run_command("tail -100 ~/prometheus/prometheus_vps.log 2>/dev/null")
        
        if not output:
            return None
        
        # 解析最新的交易周期信息
        cycles = re.findall(r'🔄 交易周期 #(\d+)', output)
        prices = re.findall(r'当前价格: \$([0-9,\.]+)', output)
        price_changes = re.findall(r'价格变化: ([+-]?[0-9\.]+%)', output)
        account_values = re.findall(r'账户总价值: \$([0-9,\.]+)', output)
        agents = re.findall(r'存活Agent: (\d+)/(\d+)', output)
        avg_capitals = re.findall(r'平均资金: \$([0-9,\.]+)', output)
        
        if cycles:
            return {
                'cycle': cycles[-1],
                'price': prices[-1] if prices else "N/A",
                'change': price_changes[-1] if price_changes else "N/A",
                'value': account_values[-1] if account_values else "N/A",
                'agents': f"{agents[-1][0]}/{agents[-1][1]}" if agents else "N/A",
                'avg_capital': avg_capitals[-1] if avg_capitals else "N/A",
                'total_cycles': len(cycles)
            }
        
        return None
    
    def get_evolution_count(self):
        """获取进化次数"""
        output = self.run_command("grep '开始进化' ~/prometheus/prometheus_vps.log 2>/dev/null | wc -l")
        return int(output.strip()) if output and output.strip().isdigit() else 0
    
    def get_error_count(self):
        """获取错误数量"""
        output = self.run_command("grep ERROR ~/prometheus/prometheus_vps.log 2>/dev/null | wc -l")
        return int(output.strip()) if output and output.strip().isdigit() else 0
    
    def check_process_running(self):
        """检查进程是否运行"""
        output = self.run_command("ps aux | grep vps_main.py | grep -v grep | wc -l")
        return int(output.strip()) > 0 if output and output.strip().isdigit() else False
    
    def get_start_time(self):
        """获取启动时间"""
        output = self.run_command("head -1 ~/prometheus/prometheus_vps.log 2>/dev/null")
        if output:
            match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', output)
            if match:
                return match.group(1)
        return "未知"
    
    def get_running_time(self):
        """计算运行时长"""
        start_time_str = self.get_start_time()
        if start_time_str == "未知":
            return "未知"
        
        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - start_time
            
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if days > 0:
                return f"{days}天{hours}小时{minutes}分钟"
            elif hours > 0:
                return f"{hours}小时{minutes}分钟"
            else:
                return f"{minutes}分钟"
        except:
            return "未知"
    
    def get_recent_cycles(self, n=5):
        """获取最近N个周期的详细信息"""
        output = self.run_command(f"tail -300 ~/prometheus/prometheus_vps.log 2>/dev/null")
        
        if not output:
            return []
        
        cycles = []
        lines = output.split('\n')
        
        current_cycle = {}
        for line in lines:
            if '🔄 交易周期' in line:
                if current_cycle:
                    cycles.append(current_cycle)
                match = re.search(r'#(\d+)', line)
                current_cycle = {'cycle': match.group(1) if match else '?'}
            elif '当前价格' in line and current_cycle:
                match = re.search(r'\$([0-9,\.]+)', line)
                current_cycle['price'] = match.group(1) if match else 'N/A'
            elif '价格变化' in line and current_cycle:
                match = re.search(r'([+-]?[0-9\.]+%)', line)
                current_cycle['change'] = match.group(1) if match else 'N/A'
            elif '账户总价值' in line and current_cycle:
                match = re.search(r'\$([0-9,\.]+)', line)
                current_cycle['value'] = match.group(1) if match else 'N/A'
            elif '存活Agent' in line and current_cycle:
                match = re.search(r'(\d+)/(\d+)', line)
                current_cycle['agents'] = match.group(0) if match else 'N/A'
            elif '平均资金' in line and current_cycle:
                match = re.search(r'\$([0-9,\.]+)', line)
                current_cycle['avg_capital'] = match.group(1) if match else 'N/A'
        
        if current_cycle:
            cycles.append(current_cycle)
        
        return cycles[-n:] if len(cycles) > n else cycles
    
    def disconnect(self):
        """断开连接"""
        if self.ssh:
            self.ssh.close()
            self.connected = False
    
    def display_status(self):
        """显示完整状态"""
        print()
        print("=" * 80)
        print("🚀 Prometheus VPS 实时监控 v2.0")
        print("=" * 80)
        print()
        
        # 系统状态
        print("📊 系统状态:")
        is_running = self.check_process_running()
        if is_running:
            print("   ✅ 进程状态: 运行中")
        else:
            print("   ❌ 进程状态: 未运行")
            print()
            print("💡 如需启动系统：")
            print(f"   ssh {VPS_USER}@{VPS_HOST}")
            print("   cd ~/prometheus && source venv/bin/activate")
            print("   screen -S prometheus")
            print("   python vps_main.py --config config/vps_config.json")
            print()
            return
        
        start_time = self.get_start_time()
        running_time = self.get_running_time()
        print(f"   ⏰ 启动时间: {start_time}")
        print(f"   ⏱️  运行时长: {running_time}")
        
        error_count = self.get_error_count()
        if error_count > 0:
            print(f"   ⚠️  错误数量: {error_count}条")
        else:
            print(f"   ✅ 错误数量: 0条")
        
        evolution_count = self.get_evolution_count()
        print(f"   🧬 进化次数: {evolution_count}次")
        
        print()
        
        # 最新状态
        print("📈 当前交易状态:")
        status = self.get_latest_status()
        
        if status:
            print(f"   🔄 交易周期: #{status['cycle']} (共{status['total_cycles']}个周期)")
            print(f"   💰 BTC价格: ${status['price']}")
            print(f"   📊 价格变化: {status['change']}")
            print(f"   💼 账户总价值: ${status['value']}")
            print(f"   👥 存活Agent: {status['agents']}")
            print(f"   📊 平均资金: ${status['avg_capital']}")
        else:
            print("   ⚠️  无法获取最新状态")
        
        print()
        
        # 最近5个周期
        print("📊 最近5个周期:")
        recent = self.get_recent_cycles(5)
        if recent:
            for cycle in recent:
                price_change = cycle.get('change', 'N/A')
                change_icon = "📈" if price_change.startswith('+') else "📉" if price_change.startswith('-') else "➡️"
                print(f"   周期#{cycle.get('cycle', '?'):>4}: "
                      f"${cycle.get('price', 'N/A'):>10} {change_icon} {price_change:>7} | "
                      f"Agent: {cycle.get('agents', 'N/A'):>5} | "
                      f"平均: ${cycle.get('avg_capital', 'N/A'):>10}")
        else:
            print("   暂无数据")
        
        print()
        print("=" * 80)
        print()
        
        # 快捷命令提示
        print("💡 更多操作:")
        print(f"   查看实时日志: ssh {VPS_USER}@{VPS_HOST} 'tail -f ~/prometheus/prometheus_vps.log'")
        print(f"   重新连接screen: ssh {VPS_USER}@{VPS_HOST} -t 'screen -r prometheus'")
        print(f"   再次监控: python monitor_vps_v2.py")
        print()


def main():
    """主函数"""
    monitor = VPSMonitor()
    
    try:
        if monitor.connect():
            monitor.display_status()
    except KeyboardInterrupt:
        print("\n\n⏹️  已中断")
    finally:
        monitor.disconnect()


if __name__ == "__main__":
    main()

