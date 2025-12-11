"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
实验：先知的必要性验证
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

实验目的：验证"先知不控制，只记录"的假设
实验方法：对照实验，3组测试
实验指标：存活周期、崩溃原因、盈利能力、多样性

实验组：
  - 对照组：Prophet主动控制（当前v7.0设计）
  - 实验组1：完全移除Prophet
  - 实验组2：Prophet静默（固定S/E，不动态计算）
  - 实验组3：Prophet只记录，不发布决策

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prometheus.core.moirai_v7 import MoiraiV7
from prometheus.core.prophet_v7 import ProphetV7
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.agent_v5 import AgentV5
from prometheus.core.supervisor import Supervisor
from prometheus.ledger.public_ledger import PublicLedger
from prometheus.ledger.private_ledger import PrivateLedger
from prometheus.core.world_signature import WorldSignature

import random
import time
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ExperimentResult:
    """实验结果记录"""
    experiment_name: str
    survival_cycles: int
    collapse_reason: Optional[str]
    max_capital: float
    final_capital: float
    max_agent_count: int
    final_agent_count: int
    final_diversity: float
    total_trades: int
    avg_roi: float
    
    def print_report(self):
        """打印实验报告"""
        print(f"\n{'='*70}")
        print(f"实验组: {self.experiment_name}")
        print(f"{'='*70}")
        print(f"存活周期:     {self.survival_cycles}")
        print(f"崩溃原因:     {self.collapse_reason or '未崩溃'}")
        print(f"最大资金:     ${self.max_capital:,.2f}")
        print(f"最终资金:     ${self.final_capital:,.2f}")
        print(f"资金变化:     {((self.final_capital/100000)-1)*100:+.2f}%")
        print(f"最大Agent数:  {self.max_agent_count}")
        print(f"最终Agent数:  {self.final_agent_count}")
        print(f"最终多样性:   {self.final_diversity:.3f}")
        print(f"总交易次数:   {self.total_trades}")
        print(f"平均ROI:      {self.avg_roi:+.2%}")
        print(f"{'='*70}\n")


class ProphetSilent:
    """实验组2：静默的先知（固定S/E，不动态计算）"""
    
    def __init__(self, bulletin_board, experience_db, public_ledger=None):
        self.bulletin_board = bulletin_board
        self.experience_db = experience_db
        self.public_ledger = public_ledger
        
        # 固定参数（来自历史经验）
        self.fixed_S = 0.3
        self.fixed_E = 0.5
        self.fixed_risk_level = 'normal'
    
    def run_decision_cycle(self, moirai_report, current_ws):
        """静默运行：只发布固定值，不计算"""
        announcement = {
            'S': self.fixed_S,
            'E': self.fixed_E,
            'risk_level': self.fixed_risk_level,
            'mode': 'silent',  # 标记为静默模式
        }
        
        self.bulletin_board.post('prophet_announcement', announcement)
        return announcement


class ProphetRecordOnly:
    """实验组3：只记录的先知（观察但不控制）"""
    
    def __init__(self, bulletin_board, experience_db, public_ledger=None):
        self.bulletin_board = bulletin_board
        self.experience_db = experience_db
        self.public_ledger = public_ledger
        self.observations = []
    
    def run_decision_cycle(self, moirai_report, current_ws):
        """只记录，不发布任何决策"""
        
        # 记录观察
        observation = {
            'cycle': len(self.observations),
            'agent_count': moirai_report.get('agent_count', 0),
            'total_capital': moirai_report.get('total_capital', 0),
            'world_signature': current_ws,
            'timestamp': time.time(),
        }
        self.observations.append(observation)
        
        # 记录到ExperienceDB
        if self.experience_db:
            self.experience_db.log_system_metrics(
                agent_count=observation['agent_count'],
                total_capital=observation['total_capital'],
                diversity=moirai_report.get('diversity', 0),
                market_state=str(current_ws)
            )
        
        # 不发布任何决策！让Moirai自己决定
        # bulletin_board会返回None，Moirai需要处理这种情况
        return None


def generate_market_data(cycle: int, phase: str = 'normal'):
    """生成模拟市场数据"""
    base_price = 50000
    
    if phase == 'bull':
        trend = cycle * 50
        volatility = random.uniform(100, 500)
    elif phase == 'bear':
        trend = -cycle * 30
        volatility = random.uniform(200, 800)
    elif phase == 'crash':
        trend = -cycle * 100
        volatility = random.uniform(500, 2000)
    else:  # normal
        trend = random.uniform(-100, 100)
        volatility = random.uniform(100, 300)
    
    price = base_price + trend + random.uniform(-volatility, volatility)
    volume = random.uniform(1000, 10000)
    
    return {
        'timestamp': time.time(),
        'close': price,
        'high': price * 1.01,
        'low': price * 0.99,
        'volume': volume,
    }


def create_world_signature(market_data, cycle):
    """创建世界签名"""
    return WorldSignature(
        volatility=random.uniform(0.1, 0.5),
        trend=random.uniform(-0.3, 0.3),
        volume_surge=random.uniform(0.8, 1.2),
        momentum=random.uniform(-0.2, 0.2),
        regime='unknown',
        cycle=cycle,
    )


def run_experiment(
    experiment_name: str,
    prophet_type: str,
    max_cycles: int = 200,
    enable_crash_phase: bool = False
) -> ExperimentResult:
    """
    运行单个实验
    
    Args:
        experiment_name: 实验名称
        prophet_type: Prophet类型 ('active', 'none', 'silent', 'record_only')
        max_cycles: 最大周期数
        enable_crash_phase: 是否启用崩盘阶段测试
    """
    print(f"\n🔬 开始实验: {experiment_name}")
    print(f"   Prophet模式: {prophet_type}")
    print(f"   最大周期: {max_cycles}")
    
    # 初始化组件
    bulletin_board = BulletinBoard("ExperimentBoard")
    experience_db = ExperienceDB()
    public_ledger = PublicLedger()
    
    # 根据实验组选择Prophet
    if prophet_type == 'active':
        prophet = ProphetV7(bulletin_board, experience_db, public_ledger)
    elif prophet_type == 'silent':
        prophet = ProphetSilent(bulletin_board, experience_db, public_ledger)
    elif prophet_type == 'record_only':
        prophet = ProphetRecordOnly(bulletin_board, experience_db, public_ledger)
    else:  # 'none'
        prophet = None
    
    # 初始化Moirai（需要适配无Prophet的情况）
    moirai = MoiraiV7(
        config={'initial_population': 10, 'max_population': 50},
        bulletin_board=bulletin_board,
        public_ledger=public_ledger
    )
    
    # 初始化进化管理器
    evolution_manager = EvolutionManagerV5(
        config={
            'mutation_rate': 0.1,
            'crossover_rate': 0.3,
            'elite_ratio': 0.2,
            'max_age': 50,
        },
        supervisor=None,
        experience_db=experience_db,
    )
    moirai.evolution_manager = evolution_manager
    
    # 初始化种群
    moirai._init_population()
    
    # 统计数据
    max_capital = 100000
    total_trades = 0
    collapse_reason = None
    
    try:
        for cycle in range(max_cycles):
            # 确定市场阶段
            if enable_crash_phase and cycle > max_cycles * 0.7:
                phase = 'crash'
            elif cycle < max_cycles * 0.3:
                phase = 'bull'
            elif cycle < max_cycles * 0.6:
                phase = 'normal'
            else:
                phase = 'bear'
            
            # 生成市场数据
            market_data = generate_market_data(cycle, phase)
            current_price = market_data['close']
            current_ws = create_world_signature(market_data, cycle)
            
            # Prophet决策（如果存在）
            if prophet:
                moirai_report = {
                    'agent_count': len(moirai.agents),
                    'total_capital': sum(a.current_capital for a in moirai.agents),
                    'diversity': moirai._calculate_diversity(),
                }
                prophet.run_decision_cycle(moirai_report, current_ws)
            
            # Moirai执行周期
            moirai.run_cycle(cycle=cycle, current_price=current_price)
            
            # 更新统计
            current_capital = sum(a.current_capital for a in moirai.agents)
            max_capital = max(max_capital, current_capital)
            
            # 检测崩溃条件
            if len(moirai.agents) == 0:
                collapse_reason = "种群灭绝"
                break
            
            if current_capital < 1000:  # 资金低于1000
                collapse_reason = "资金耗尽"
                break
            
            # 每50个周期报告进度
            if cycle % 50 == 0 and cycle > 0:
                print(f"   周期 {cycle}: Agents={len(moirai.agents)}, "
                      f"Capital=${current_capital:,.0f}, "
                      f"Phase={phase}")
    
    except Exception as e:
        collapse_reason = f"异常崩溃: {str(e)}"
        cycle = cycle if 'cycle' in locals() else 0
    
    # 收集最终结果
    final_capital = sum(a.current_capital for a in moirai.agents) if moirai.agents else 0
    final_diversity = moirai._calculate_diversity() if moirai.agents else 0
    avg_roi = sum(getattr(a, 'total_roi', 0) for a in moirai.agents) / len(moirai.agents) if moirai.agents else 0
    
    result = ExperimentResult(
        experiment_name=experiment_name,
        survival_cycles=cycle + 1,
        collapse_reason=collapse_reason,
        max_capital=max_capital,
        final_capital=final_capital,
        max_agent_count=moirai.config.get('max_population', 50),
        final_agent_count=len(moirai.agents),
        final_diversity=final_diversity,
        total_trades=total_trades,
        avg_roi=avg_roi,
    )
    
    return result


def compare_results(results: List[ExperimentResult]):
    """对比所有实验结果"""
    print("\n" + "="*70)
    print("实验对比总结")
    print("="*70)
    
    # 按存活周期排序
    sorted_results = sorted(results, key=lambda x: x.survival_cycles, reverse=True)
    
    print("\n📊 存活周期排名:")
    for i, result in enumerate(sorted_results, 1):
        print(f"  {i}. {result.experiment_name}: {result.survival_cycles} 周期")
    
    print("\n💰 资金表现排名:")
    sorted_by_capital = sorted(results, key=lambda x: x.final_capital, reverse=True)
    for i, result in enumerate(sorted_by_capital, 1):
        change = ((result.final_capital/100000)-1)*100
        print(f"  {i}. {result.experiment_name}: ${result.final_capital:,.0f} ({change:+.1f}%)")
    
    print("\n🧬 多样性表现:")
    for result in results:
        print(f"  {result.experiment_name}: {result.final_diversity:.3f}")
    
    print("\n💀 崩溃原因:")
    for result in results:
        print(f"  {result.experiment_name}: {result.collapse_reason or '未崩溃'}")
    
    print("\n" + "="*70)
    print("关键发现:")
    
    # 分析关键发现
    active_result = next((r for r in results if '主动控制' in r.experiment_name), None)
    none_result = next((r for r in results if '完全移除' in r.experiment_name), None)
    silent_result = next((r for r in results if '静默' in r.experiment_name), None)
    record_result = next((r for r in results if '只记录' in r.experiment_name), None)
    
    if active_result and none_result:
        if none_result.survival_cycles > active_result.survival_cycles * 0.5:
            print("  ⚠️  无Prophet的系统存活时间超过有Prophet的50%")
            print("      → Prophet的控制作用可能不如预期")
        else:
            print("  ✅ Prophet的控制显著延长了系统寿命")
    
    if silent_result and active_result:
        if abs(silent_result.survival_cycles - active_result.survival_cycles) < 20:
            print("  ⚠️  静默Prophet与主动Prophet表现接近")
            print("      → 动态计算可能不是必需的")
    
    if record_result:
        if record_result.collapse_reason:
            print(f"  📝 只记录的Prophet: {record_result.collapse_reason}")
        else:
            print("  🌟 只记录的Prophet完成了所有周期！")
            print("      → 核心假设得到验证：先知不需要控制")
    
    print("="*70 + "\n")


def main():
    """运行所有实验"""
    print("\n" + "="*70)
    print("实验：先知的必要性验证")
    print("="*70)
    print("\n实验设计:")
    print("  - 对照组: Prophet主动控制（当前v7.0）")
    print("  - 实验组1: 完全移除Prophet")
    print("  - 实验组2: Prophet静默（固定S/E）")
    print("  - 实验组3: Prophet只记录（不控制）")
    print("\n每组运行200个周期，包含牛市、震荡、熊市阶段")
    print("="*70)
    
    results = []
    
    # 对照组：主动控制
    result1 = run_experiment(
        experiment_name="对照组：Prophet主动控制",
        prophet_type='active',
        max_cycles=200
    )
    result1.print_report()
    results.append(result1)
    
    # 实验组1：完全移除
    result2 = run_experiment(
        experiment_name="实验组1：完全移除Prophet",
        prophet_type='none',
        max_cycles=200
    )
    result2.print_report()
    results.append(result2)
    
    # 实验组2：静默
    result3 = run_experiment(
        experiment_name="实验组2：Prophet静默（固定S/E）",
        prophet_type='silent',
        max_cycles=200
    )
    result3.print_report()
    results.append(result3)
    
    # 实验组3：只记录
    result4 = run_experiment(
        experiment_name="实验组3：Prophet只记录（不控制）",
        prophet_type='record_only',
        max_cycles=200
    )
    result4.print_report()
    results.append(result4)
    
    # 对比分析
    compare_results(results)


if __name__ == "__main__":
    main()

