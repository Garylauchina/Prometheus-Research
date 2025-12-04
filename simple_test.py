#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""自包含的v5.0进化测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUTPUT_FILE = 'RESULT.txt'

def write_output(msg):
    """写入输出"""
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg)

def main():
    # 清空输出文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('')
    
    write_output("="*70)
    write_output("v5.0 进化系统测试")
    write_output("="*70)
    
    try:
        write_output("\n[1/6] 导入模块...")
        from prometheus.core.moirai import Moirai
        from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
        write_output("✅ 模块导入成功")
        
        write_output("\n[2/6] 创建Moirai...")
        moirai = Moirai(bulletin_board=None, num_families=50)
        moirai.next_agent_id = 1
        write_output("✅ Moirai创建成功")
        
        write_output("\n[3/6] 创建10个Agent...")
        agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
        moirai.agents = agents
        write_output(f"✅ 创建了 {len(agents)} 个Agent")
        
        write_output("\n[4/6] 模拟交易结果...")
        for i, agent in enumerate(agents):
            if i < 5:  # 前5个盈利
                agent.total_pnl = 500
                agent.current_capital = 10500
                agent.trade_count = 10
                agent.win_count = 7
            else:  # 后5个亏损
                agent.total_pnl = -300
                agent.current_capital = 9700
                agent.trade_count = 10
                agent.win_count = 3
        write_output("✅ 交易结果设置完成")
        
        write_output("\n[5/6] 创建进化管理器...")
        evo = EvolutionManagerV5(moirai, num_families=50)
        write_output("✅ 进化管理器创建成功")
        
        initial_count = len(moirai.agents)
        write_output(f"\n初始种群: {initial_count} 个Agent")
        
        write_output("\n[6/6] 执行进化周期...")
        evo.run_evolution_cycle(90000)
        write_output("✅ 进化周期执行完成")
        
        final_count = len(moirai.agents)
        
        write_output("\n" + "="*70)
        write_output("测试结果:")
        write_output("="*70)
        write_output(f"初始数量: {initial_count}")
        write_output(f"最终数量: {final_count}")
        write_output(f"新生数量: {evo.total_births}")
        write_output(f"死亡数量: {evo.total_deaths}")
        write_output(f"差额: {final_count - initial_count:+d}")
        write_output("="*70)
        
        # 判断
        if abs(final_count - initial_count) <= 1:
            write_output("\n✅✅✅ 测试通过！ ✅✅✅")
            return 0
        else:
            write_output(f"\n❌ 测试失败：种群数量变化过大 ({initial_count} -> {final_count})")
            return 1
            
    except Exception as e:
        write_output(f"\n❌❌❌ 发生错误 ❌❌❌")
        write_output(f"错误信息: {str(e)}")
        import traceback
        write_output("\n完整错误堆栈:")
        write_output(traceback.format_exc())
        return 2

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

