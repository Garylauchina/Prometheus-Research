"""最简单的进化测试"""
import sys
sys.path.insert(0, '.')

from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

result_file = 'test_output.txt'

with open(result_file, 'w', encoding='utf-8') as f:
    f.write("="*70 + "\n")
    f.write("v5.0进化测试\n")
    f.write("="*70 + "\n\n")
    
    try:
        # 1. 创建Moirai
        f.write("步骤1: 创建Moirai\n")
        moirai = Moirai(bulletin_board=None, num_families=50)
        moirai.next_agent_id = 1
        f.write("✅ Moirai创建成功\n\n")
        
        # 2. 创建Agent
        f.write("步骤2: 创建10个Agent\n")
        agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
        moirai.agents = agents
        f.write(f"✅ 创建了{len(agents)}个Agent\n\n")
        
        # 3. 设置交易结果
        f.write("步骤3: 设置交易结果\n")
        for i, agent in enumerate(agents):
            if i < 5:
                agent.total_pnl = 500
                agent.current_capital = 10500
                agent.trade_count = 10
                agent.win_count = 7
            else:
                agent.total_pnl = -300
                agent.current_capital = 9700
                agent.trade_count = 10
                agent.win_count = 3
        f.write("✅ 交易结果设置完成\n\n")
        
        # 4. 创建进化管理器
        f.write("步骤4: 创建进化管理器\n")
        evo = EvolutionManagerV5(moirai, num_families=50)
        f.write("✅ 进化管理器创建成功\n\n")
        
        # 5. 记录初始状态
        initial_count = len(moirai.agents)
        f.write(f"初始Agent数量: {initial_count}\n\n")
        
        # 6. 执行进化
        f.write("步骤5: 执行进化周期\n")
        evo.run_evolution_cycle(90000)
        f.write("✅ 进化周期完成\n\n")
        
        # 7. 检查结果
        final_count = len(moirai.agents)
        f.write("="*70 + "\n")
        f.write("结果:\n")
        f.write(f"  初始数量: {initial_count}\n")
        f.write(f"  最终数量: {final_count}\n")
        f.write(f"  新生数量: {evo.total_births}\n")
        f.write(f"  死亡数量: {evo.total_deaths}\n")
        f.write(f"  差额: {final_count - initial_count}\n")
        f.write("="*70 + "\n\n")
        
        # 8. 判断
        if abs(final_count - initial_count) <= 1:
            f.write("✅ 测试通过！\n")
            print("✅ 测试通过！查看 test_output.txt")
        else:
            f.write(f"❌ 测试失败！种群数量变化: {initial_count} -> {final_count}\n")
            print(f"❌ 测试失败！查看 test_output.txt")
            
    except Exception as e:
        f.write(f"\n❌ 错误: {e}\n")
        import traceback
        f.write(traceback.format_exc())
        print(f"❌ 出错了！查看 test_output.txt")
        raise

print(f"详细输出已写入: {result_file}")

