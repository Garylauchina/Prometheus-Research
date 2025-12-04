"""最小化测试 - 立即写入结果"""
import sys
sys.path.insert(0, '.')

# 立即写入开始标记
with open('run_test_result.txt', 'w', encoding='utf-8') as f:
    f.write("测试开始...\n")

try:
    from prometheus.core.moirai import Moirai
    from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write("导入成功\n")
    
    # 创建
    moirai = Moirai(bulletin_board=None, num_families=50)
    moirai.next_agent_id = 1
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write("Moirai创建成功\n")
    
    # 创建Agent
    agents = moirai._clotho_create_v5_agents(10, [], 10000.0)
    moirai.agents = agents
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write(f"创建了{len(agents)}个Agent\n")
    
    # 设置交易结果
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
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write("交易结果设置完成\n")
    
    # 创建进化管理器
    evo = EvolutionManagerV5(moirai, num_families=50)
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write("进化管理器创建成功\n")
        f.write(f"初始: {len(moirai.agents)}\n")
    
    # 执行进化
    evo.run_evolution_cycle(90000)
    
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write("进化完成\n")
        f.write(f"最终: {len(moirai.agents)}\n")
        f.write(f"新生: {evo.total_births}\n")
        f.write(f"死亡: {evo.total_deaths}\n")
        
        if abs(len(moirai.agents) - 10) <= 1:
            f.write("\n✅ 测试通过！\n")
        else:
            f.write(f"\n❌ 测试失败：10 -> {len(moirai.agents)}\n")
            
except Exception as e:
    with open('run_test_result.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n❌ 错误: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

print("完成，查看 run_test_result.txt")

