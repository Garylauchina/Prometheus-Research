"""
快速验证测试 - 验证基因多样性修复
运行到第一次进化后自动停止（简化版，不卡顿）
"""
import sys
import os
import time
import subprocess
from datetime import datetime

def main():
    print("=" * 70)
    print("🧬 基因多样性修复验证测试")
    print("=" * 70)
    print()
    print("📝 测试将在后台运行5分钟")
    print("📄 日志文件: diversity_test_result.log")
    print()
    print("⏳ 启动测试...")
    
    log_file = "diversity_test_result.log"
    
    # 方式1: 直接运行并重定向到文件
    cmd = f'python examples/v4_okx_simplified_launcher.py > {log_file} 2>&1'
    
    try:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=os.getcwd()
        )
        
        print(f"✅ 测试进程已启动 (PID: {process.pid})")
        print()
        print("⏱️  等待5分钟后自动停止...")
        print("   （Mock模式30周期触发进化，约2.5分钟）")
        print()
        print("💡 您可以实时查看日志：")
        print(f"   Get-Content {log_file} -Tail 20 -Wait")
        print()
        
        # 定时检查
        start_time = time.time()
        check_interval = 30  # 每30秒检查一次
        max_wait = 300  # 最多等5分钟
        
        while time.time() - start_time < max_wait:
            time.sleep(check_interval)
            elapsed = int(time.time() - start_time)
            
            # 检查日志文件
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # 检查是否已触发进化
                        if '基因多样性' in content and '开始进化周期' in content:
                            print(f"\n✅ 检测到进化周期！({elapsed}秒)")
                            break
                except:
                    pass
            
            print(f"⏳ 已运行 {elapsed} 秒...")
        
        # 停止进程
        print("\n⏹️  停止测试进程...")
        try:
            process.terminate()
            process.wait(timeout=10)
        except:
            process.kill()
        
        print("✅ 测试完成！")
        print()
        
        # 分析结果
        analyze_results(log_file)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        if 'process' in locals():
            try:
                process.terminate()
            except:
                pass
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

def analyze_results(log_file):
    """分析测试结果"""
    print("=" * 70)
    print("📊 测试结果分析")
    print("=" * 70)
    
    if not os.path.exists(log_file):
        print("❌ 日志文件不存在")
        return
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 1. 检查创世
        if '创世完成' in content or 'Genesis' in content:
            print("✅ 创世成功")
        else:
            print("⚠️  未检测到创世完成")
        
        # 2. 检查系统盈亏显示
        import re
        pnl_matches = re.findall(r'系统总盈亏:\s*(\$[+-]?[\d.]+)', content)
        if pnl_matches:
            print(f"✅ 系统盈亏显示正常 (共 {len(pnl_matches)} 次)")
            print(f"   最后一次: {pnl_matches[-1]}")
        else:
            print("⚠️  未检测到系统盈亏显示")
        
        # 3. 检查进化
        if '开始进化周期' in content:
            evolution_count = content.count('开始进化周期')
            print(f"✅ 进化触发 {evolution_count} 次")
        else:
            print("⚠️  未检测到进化触发")
            return
        
        # 4. 检查基因多样性（最关键！）
        diversity_matches = re.findall(r'基因多样性:\s*([\d.]+)', content)
        if diversity_matches:
            print(f"\n🎯 基因多样性值:")
            for i, val in enumerate(diversity_matches, 1):
                diversity = float(val)
                if diversity > 0:
                    print(f"   第{i}次进化: {val} ✅ (成功！不再是0.00)")
                else:
                    print(f"   第{i}次进化: {val} ❌ (仍为0.00)")
            
            # 判断修复是否成功
            latest_diversity = float(diversity_matches[-1])
            print()
            if latest_diversity > 0:
                print("=" * 70)
                print("🎉 修复成功！基因多样性已不再是0.00！")
                print("=" * 70)
            else:
                print("=" * 70)
                print("⚠️  多样性仍为0.00，需要进一步调试")
                print("=" * 70)
        else:
            print("⚠️  未检测到基因多样性数据")
        
        # 5. 显示部分日志
        print("\n📋 最后20行日志:")
        print("-" * 70)
        lines = content.split('\n')
        for line in lines[-20:]:
            if line.strip():
                # 只显示关键行
                if any(kw in line for kw in ['价格', '盈亏', '预言', '进化', '多样性', '淘汰', '诞生']):
                    print(line[:150])  # 限制长度
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

if __name__ == "__main__":
    main()
    print("\n按任意键退出...")
    input()
