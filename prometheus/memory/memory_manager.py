#!/usr/bin/env python3
"""
Memory Layer - 系统智慧层（Level 0）
=========================================

职责：
1. 记录所有Agent的经验（死亡、成功、交易）
2. 分析模式，提炼智慧
3. 为上层提供指导

设计原则：
1. 统一入口：所有Memory操作通过MemoryManager
2. 单向信息流：向上接收，向下指导
3. 封装内部：外部不直接访问Registry
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    DEATH = "death"              # Agent死亡
    SUCCESS = "success"          # 达成里程碑
    TRADE = "trade"              # 交易记录
    EVOLUTION = "evolution"      # 进化事件


class WisdomQuery(Enum):
    """智慧查询类型"""
    SURVIVAL_LESSONS = "survival_lessons"      # 生存教训
    SUCCESS_PATTERNS = "success_patterns"      # 成功模式
    DEATH_CAUSES = "death_causes"              # 死因分析
    CHAMPION_STRATEGIES = "champion_strategies" # 冠军策略
    MARKET_INSIGHTS = "market_insights"        # 市场洞察


@dataclass
class MemoryEvent:
    """统一的事件格式"""
    event_type: EventType
    agent_id: str
    timestamp: datetime
    cycle: int
    
    # Agent状态快照
    agent_state: Dict
    
    # 市场状态
    market_state: Dict
    
    # 事件特定数据
    event_data: Dict


@dataclass
class WisdomPackage:
    """智慧包 - 传承给新Agent的智慧"""
    survival_lessons: List[str]      # 生存教训（从死亡学）
    success_patterns: List[str]      # 成功模式（从成功学）
    champion_strategies: List[Dict]  # 冠军策略（榜样）
    warnings: List[str]              # 警示信息
    recommendations: List[str]       # 行动建议
    
    # 元数据
    generation: int                  # 代际
    total_deaths: int                # 累计死亡
    total_successes: int             # 累计成功


class MemoryManager:
    """
    Memory Layer的统一管理者
    
    这是Memory Layer的唯一对外接口！
    外部只能通过MemoryManager访问Memory功能。
    """
    
    def __init__(self):
        """初始化Memory Layer"""
        # 内部组件（外部不可直接访问）
        from prometheus.memory.death_registry import DeathRegistry
        from prometheus.memory.success_registry import SuccessRegistry
        from prometheus.memory.experience_db import ExperienceDatabase
        from prometheus.memory.strategy_analyzer import StrategyAnalyzer
        
        self._death_registry = DeathRegistry()
        self._success_registry = SuccessRegistry()
        self._experience_db = ExperienceDatabase()
        self._strategy_analyzer = StrategyAnalyzer()
        
        # 统计
        self.generation = 0
        self.total_events = 0
        
        logger.info("✅ Memory Layer已初始化")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 向上接口：接收事件（From Moirai/Evolution）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def record_event(self, event: MemoryEvent):
        """
        记录事件（统一入口）
        
        调用者：Moirai、EvolutionManager
        
        Args:
            event: 标准化的事件对象
        """
        self.total_events += 1
        
        # 路由到具体处理
        if event.event_type == EventType.DEATH:
            self._handle_death(event)
        elif event.event_type == EventType.SUCCESS:
            self._handle_success(event)
        elif event.event_type == EventType.TRADE:
            self._handle_trade(event)
        elif event.event_type == EventType.EVOLUTION:
            self._handle_evolution(event)
        
        # 存储到经验数据库
        self._experience_db.store(event)
        
        # 触发分析（每100个事件分析一次）
        if self.total_events % 100 == 0:
            self._trigger_analysis()
    
    def record_death(self, agent, reason: str, market_state: Dict, cycle: int):
        """
        记录Agent死亡（便捷方法）
        
        调用者：Moirai.atropos_cut()
        """
        event = MemoryEvent(
            event_type=EventType.DEATH,
            agent_id=agent.agent_id,
            timestamp=datetime.now(),
            cycle=cycle,
            agent_state=self._capture_agent_state(agent),
            market_state=market_state,
            event_data={
                'death_reason': reason,
                'final_capital': agent.current_capital,
                'total_return': (agent.current_capital / agent.initial_capital - 1)
            }
        )
        
        self.record_event(event)
        logger.info(f"💀 记录死亡: {agent.agent_id}, 原因: {reason}")
    
    def record_success(self, agent, milestone: str, cycle: int):
        """
        记录成功事件（便捷方法）
        
        调用者：Moirai或Evolution（当Agent达成里程碑时）
        """
        event = MemoryEvent(
            event_type=EventType.SUCCESS,
            agent_id=agent.agent_id,
            timestamp=datetime.now(),
            cycle=cycle,
            agent_state=self._capture_agent_state(agent),
            market_state={},  # 可选
            event_data={
                'milestone': milestone,
                'performance_snapshot': self._capture_performance(agent)
            }
        )
        
        self.record_event(event)
        logger.info(f"🌟 记录成功: {agent.agent_id}, 里程碑: {milestone}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 向下接口：提供智慧（To Moirai/Agent）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_wisdom_for_newborn(self, parent1=None, parent2=None, 
                               family_id: Optional[str] = None) -> WisdomPackage:
        """
        为新生Agent准备智慧包
        
        调用者：Moirai.clotho_spin_thread()（创建新Agent时）
        
        Returns:
            WisdomPackage: 包含所有需要传承的智慧
        """
        # 1. 系统级教训（Top 5死因）
        survival_lessons = self._death_registry.get_survival_lessons(count=5)
        
        # 2. 成功模式（Top 5成功策略）
        success_patterns = self._success_registry.get_success_patterns(count=5)
        
        # 3. 冠军策略（Top 3 Agent）
        champion_strategies = self._success_registry.get_champion_strategies(count=3)
        
        # 4. 家族特定警示
        warnings = []
        if family_id:
            family_deaths = self._death_registry.get_deaths_by_family(family_id)
            warnings = [d.warning for d in family_deaths[-3:]]
        
        # 5. 父母特定警示
        if parent1 or parent2:
            for parent in [parent1, parent2]:
                if parent and hasattr(parent, 'death_record'):
                    warnings.append(parent.death_record.warning)
        
        # 6. 当前最佳建议
        recommendations = self._strategy_analyzer.get_current_best_practices()
        
        wisdom = WisdomPackage(
            survival_lessons=survival_lessons,
            success_patterns=success_patterns,
            champion_strategies=champion_strategies,
            warnings=warnings,
            recommendations=recommendations,
            generation=self.generation,
            total_deaths=len(self._death_registry.all_deaths),
            total_successes=len(self._success_registry.all_successes)
        )
        
        logger.debug(f"✨ 准备智慧包: {len(survival_lessons)}条教训, {len(success_patterns)}个模式")
        
        return wisdom
    
    def query_wisdom(self, query_type: WisdomQuery, context: Dict = None) -> Any:
        """
        查询特定类型的智慧
        
        调用者：Moirai、Prophet、Agent
        
        Args:
            query_type: 查询类型
            context: 查询上下文（可选）
        
        Returns:
            根据查询类型返回不同数据
        """
        if query_type == WisdomQuery.SURVIVAL_LESSONS:
            return self._death_registry.get_survival_lessons()
        
        elif query_type == WisdomQuery.SUCCESS_PATTERNS:
            return self._success_registry.get_success_patterns()
        
        elif query_type == WisdomQuery.DEATH_CAUSES:
            return self._death_registry.get_death_statistics()
        
        elif query_type == WisdomQuery.CHAMPION_STRATEGIES:
            return self._success_registry.get_champion_strategies()
        
        elif query_type == WisdomQuery.MARKET_INSIGHTS:
            return self._strategy_analyzer.get_market_insights(context)
        
        return None
    
    def check_decision_safety(self, agent, decision: Dict, 
                             market_state: Dict) -> tuple[bool, str]:
        """
        检查决策是否安全（基于历史经验）
        
        调用者：Daimon.guide()（决策前检查）
        
        Returns:
            (是否安全, 警告信息)
        """
        action = decision.get('action')
        
        # 检查是否会重复历史上的致命错误
        dangerous_patterns = self._death_registry.get_dangerous_patterns()
        
        for pattern in dangerous_patterns:
            if self._matches_pattern(action, market_state, pattern):
                warning = f"⚠️ {pattern['warning']} ({pattern['death_count']}次死亡)"
                return False, warning
        
        return True, ""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 内部方法（Private，外部不调用）
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _handle_death(self, event: MemoryEvent):
        """处理死亡事件（内部）"""
        self._death_registry.record(event)
    
    def _handle_success(self, event: MemoryEvent):
        """处理成功事件（内部）"""
        self._success_registry.record(event)
    
    def _handle_trade(self, event: MemoryEvent):
        """处理交易事件（内部）"""
        # 可选：记录所有交易用于回放分析
        pass
    
    def _handle_evolution(self, event: MemoryEvent):
        """处理进化事件（内部）"""
        self.generation += 1
    
    def _trigger_analysis(self):
        """触发周期性分析（内部）"""
        recent_events = self._experience_db.get_recent(100)
        self._strategy_analyzer.analyze(recent_events)
    
    def _capture_agent_state(self, agent) -> Dict:
        """捕获Agent状态快照（内部）"""
        return {
            'capital': agent.current_capital,
            'initial_capital': agent.initial_capital,
            'total_return': (agent.current_capital / agent.initial_capital - 1),
            'trade_count': agent.trade_count,
            'cycles_survived': getattr(agent, 'cycles_survived', 0),
            'genome': agent.genome.to_dict() if hasattr(agent, 'genome') else {},
            'instinct': agent.instinct.to_dict() if hasattr(agent, 'instinct') else {},
        }
    
    def _capture_performance(self, agent) -> Dict:
        """捕获Agent性能指标（内部）"""
        return {
            'total_return': (agent.current_capital / agent.initial_capital - 1),
            'sharpe_ratio': getattr(agent, 'sharpe_ratio', 0),
            'max_drawdown': getattr(agent, 'max_drawdown', 0),
            'win_rate': getattr(agent, 'win_rate', 0),
        }
    
    def _matches_pattern(self, action: str, market_state: Dict, 
                        pattern: Dict) -> bool:
        """检查是否匹配危险模式（内部）"""
        # 实现模式匹配逻辑
        return False  # Placeholder
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 统计和报告
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def get_statistics(self) -> Dict:
        """获取Memory统计信息"""
        return {
            'generation': self.generation,
            'total_events': self.total_events,
            'total_deaths': len(self._death_registry.all_deaths),
            'total_successes': len(self._success_registry.all_successes),
            'top_death_causes': self._death_registry.get_top_causes(5),
            'top_success_patterns': self._success_registry.get_top_patterns(5),
        }
    
    def generate_report(self) -> str:
        """生成Memory Layer报告"""
        stats = self.get_statistics()
        
        report = f"""
╔═══════════════════════════════════════════════════════════╗
║           Memory Layer 智慧报告                            ║
╠═══════════════════════════════════════════════════════════╣
║ 代际: {stats['generation']}                                ║
║ 总事件: {stats['total_events']}                            ║
║ 累计死亡: {stats['total_deaths']}                          ║
║ 累计成功: {stats['total_successes']}                       ║
╠═══════════════════════════════════════════════════════════╣
║ Top 5 死因:                                               ║
"""
        for i, (cause, count) in enumerate(stats['top_death_causes'], 1):
            report += f"║  {i}. {cause}: {count}次\n"
        
        report += """╠═══════════════════════════════════════════════════════════╣
║ Top 5 成功模式:                                           ║
"""
        for i, pattern in enumerate(stats['top_success_patterns'], 1):
            report += f"║  {i}. {pattern}\n"
        
        report += "╚═══════════════════════════════════════════════════════════╝"
        
        return report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 全局单例（系统唯一的Memory Layer实例）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取全局Memory Manager（单例模式）"""
    global _global_memory_manager
    
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    
    return _global_memory_manager


def reset_memory_manager():
    """重置Memory Manager（用于测试）"""
    global _global_memory_manager
    _global_memory_manager = None

