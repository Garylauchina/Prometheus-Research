"""
Personal Insights - Agent的个体记忆系统
====================================

PersonalInsights是Agent的"经验库"，存储学到的知识和模式。

设计哲学：
- 轻量级：压缩的、结构化的记忆，不是原始数据
- 可查询：Daimon可以快速查询历史经验
- 可学习：通过冥思（Meditation）和顿悟（Epiphany）更新

与其他记忆系统的区别：
- Private Ledger：存储原始交易记录（财务数据）
- PersonalInsights：存储学到的模式和策略效果（知识数据）
- BulletinBoard：存储公共市场信息（共享数据）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque, defaultdict
import time


@dataclass
class StrategyPerformance:
    """
    策略效果记录
    
    Attributes:
        strategy_name: 策略名称
        total_uses: 总使用次数
        win_count: 成功次数
        loss_count: 失败次数
        total_pnl: 总盈亏
        avg_pnl: 平均盈亏
        win_rate: 胜率
        last_used: 最后使用时间
    """
    strategy_name: str
    total_uses: int = 0
    win_count: int = 0
    loss_count: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    win_rate: float = 0.0
    last_used: float = 0.0
    
    def update(self, pnl: float):
        """更新策略效果"""
        self.total_uses += 1
        self.total_pnl += pnl
        self.avg_pnl = self.total_pnl / self.total_uses
        
        if pnl > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        self.win_rate = self.win_count / self.total_uses if self.total_uses > 0 else 0
        self.last_used = time.time()


@dataclass
class LearnedPattern:
    """
    学到的市场模式
    
    Attributes:
        pattern_type: 模式类型（如"高波动震荡"）
        condition: 触发条件描述
        success_rate: 成功率
        recommended_action: 推荐行动
        sample_count: 样本数量
    """
    pattern_type: str
    condition: str
    success_rate: float
    recommended_action: str
    sample_count: int = 0


@dataclass
class MeditationRecord:
    """
    冥思记录
    
    Attributes:
        timestamp: 冥思时间
        insights: 获得的洞察
        patterns_discovered: 发现的新模式数量
        strategies_adjusted: 调整的策略数量
    """
    timestamp: float
    insights: List[str]
    patterns_discovered: int = 0
    strategies_adjusted: int = 0


@dataclass
class Epiphany:
    """
    顿悟记录
    
    顿悟是突然的质变，可能导致：
    - 解锁新策略
    - 大幅提升某个本能
    - 发现新的市场规律
    
    Attributes:
        timestamp: 顿悟时间
        trigger: 触发原因
        effect: 顿悟效果
        magnitude: 影响程度（0-1）
    """
    timestamp: float
    trigger: str
    effect: str
    magnitude: float


class PersonalInsights:
    """
    个体记忆系统
    
    存储Agent的学习成果和经验
    """
    
    def __init__(self, max_history: int = 100):
        """
        初始化个体记忆
        
        Args:
            max_history: 保留的历史记录数量
        """
        # 策略效果追踪
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        
        # 学到的模式
        self.learned_patterns: List[LearnedPattern] = []
        
        # 市场环境偏好（在什么环境下表现好）
        self.regime_preferences: Dict[str, float] = {
            'bullish': 0.0,      # 牛市表现
            'bearish': 0.0,      # 熊市表现
            'volatile': 0.0,     # 高波动表现
            'stable': 0.0,       # 稳定市场表现
        }
        
        # 冥思历史
        self.meditation_history: deque = deque(maxlen=max_history)
        
        # 顿悟历史
        self.epiphanies: List[Epiphany] = []
        
        # 个人统计缓存（用于快速查询）
        self.personal_stats_cache: Dict = {
            'total_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'best_strategy': None,
            'worst_strategy': None,
            'last_update': 0.0,
        }
    
    # ==================== 策略效果追踪 ====================
    
    def record_strategy_result(self, strategy_name: str, pnl: float):
        """
        记录策略使用结果
        
        Args:
            strategy_name: 策略名称
            pnl: 本次盈亏
        """
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(strategy_name)
        
        self.strategy_performance[strategy_name].update(pnl)
        
        # 更新缓存
        self._update_stats_cache()
    
    def get_strategy_performance(self, strategy_name: str) -> Optional[StrategyPerformance]:
        """获取策略效果"""
        return self.strategy_performance.get(strategy_name)
    
    def get_best_strategy(self) -> Optional[str]:
        """获取表现最好的策略"""
        if not self.strategy_performance:
            return None
        
        best = max(
            self.strategy_performance.values(),
            key=lambda p: p.avg_pnl if p.total_uses >= 3 else -float('inf')
        )
        
        return best.strategy_name if best.total_uses >= 3 else None
    
    def get_worst_strategy(self) -> Optional[str]:
        """获取表现最差的策略"""
        if not self.strategy_performance:
            return None
        
        worst = min(
            self.strategy_performance.values(),
            key=lambda p: p.avg_pnl if p.total_uses >= 3 else float('inf')
        )
        
        return worst.strategy_name if worst.total_uses >= 3 else None
    
    # ==================== 市场环境学习 ====================
    
    def update_regime_preference(self, regime: str, pnl: float):
        """
        更新市场环境偏好
        
        Args:
            regime: 市场环境类型
            pnl: 盈亏
        """
        if regime in self.regime_preferences:
            # 指数移动平均
            alpha = 0.1
            self.regime_preferences[regime] = (
                (1 - alpha) * self.regime_preferences[regime] + alpha * pnl
            )
    
    def get_regime_preference(self, regime: str) -> float:
        """获取在特定市场环境下的表现"""
        return self.regime_preferences.get(regime, 0.0)
    
    # ==================== 模式学习 ====================
    
    def add_learned_pattern(self, pattern: LearnedPattern):
        """添加学到的模式"""
        # 检查是否已存在相似模式
        for existing in self.learned_patterns:
            if existing.pattern_type == pattern.pattern_type:
                # 更新现有模式
                existing.success_rate = (
                    existing.success_rate * existing.sample_count + 
                    pattern.success_rate * pattern.sample_count
                ) / (existing.sample_count + pattern.sample_count)
                existing.sample_count += pattern.sample_count
                return
        
        # 添加新模式
        self.learned_patterns.append(pattern)
    
    def find_matching_pattern(self, current_conditions: Dict) -> Optional[LearnedPattern]:
        """
        查找匹配当前条件的模式
        
        Args:
            current_conditions: 当前市场条件
        
        Returns:
            LearnedPattern: 匹配的模式，如果没有则返回None
        """
        # v5.0简化版：直接返回成功率最高的模式
        if not self.learned_patterns:
            return None
        
        best_pattern = max(
            self.learned_patterns,
            key=lambda p: p.success_rate if p.sample_count >= 5 else 0
        )
        
        return best_pattern if best_pattern.sample_count >= 5 else None
    
    # ==================== 冥思（Meditation）====================
    
    def meditate(self, recent_trades: List[Dict]) -> MeditationRecord:
        """
        冥思：反思最近的交易，学习模式
        
        Args:
            recent_trades: 最近的交易记录
        
        Returns:
            MeditationRecord: 冥思记录
        """
        insights = []
        patterns_discovered = 0
        strategies_adjusted = 0
        
        # 分析最近的交易
        if len(recent_trades) >= 10:
            # 1. 分析策略效果
            strategy_results = defaultdict(list)
            for trade in recent_trades:
                strategy = trade.get('strategy', 'Unknown')
                pnl = trade.get('pnl', 0)
                strategy_results[strategy].append(pnl)
            
            # 发现策略效果模式
            for strategy, pnls in strategy_results.items():
                avg_pnl = sum(pnls) / len(pnls)
                if avg_pnl > 0.01:
                    insights.append(f"{strategy}策略表现良好(平均+{avg_pnl:.2%})")
                elif avg_pnl < -0.01:
                    insights.append(f"{strategy}策略表现不佳(平均{avg_pnl:.2%})")
            
            # 2. 分析市场环境
            # TODO: 更复杂的模式识别
            
            patterns_discovered = len(insights)
        
        # 创建冥思记录
        record = MeditationRecord(
            timestamp=time.time(),
            insights=insights,
            patterns_discovered=patterns_discovered,
            strategies_adjusted=strategies_adjusted,
        )
        
        self.meditation_history.append(record)
        
        return record
    
    # ==================== 顿悟（Epiphany）====================
    
    def trigger_epiphany(self, trigger: str, effect: str, magnitude: float = 0.5) -> Epiphany:
        """
        触发顿悟
        
        Args:
            trigger: 触发原因
            effect: 顿悟效果
            magnitude: 影响程度（0-1）
        
        Returns:
            Epiphany: 顿悟记录
        """
        epiphany = Epiphany(
            timestamp=time.time(),
            trigger=trigger,
            effect=effect,
            magnitude=magnitude,
        )
        
        self.epiphanies.append(epiphany)
        
        return epiphany
    
    # ==================== 快速查询 ====================
    
    def get_quick_stats(self) -> Dict:
        """
        获取快速统计（用于Daimon的experience_voice）
        
        Returns:
            Dict: 统计数据
        """
        return self.personal_stats_cache.copy()
    
    def _update_stats_cache(self):
        """更新统计缓存"""
        total_trades = sum(p.total_uses for p in self.strategy_performance.values())
        total_pnl = sum(p.total_pnl for p in self.strategy_performance.values())
        total_wins = sum(p.win_count for p in self.strategy_performance.values())
        
        self.personal_stats_cache = {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'win_rate': total_wins / total_trades if total_trades > 0 else 0,
            'best_strategy': self.get_best_strategy(),
            'worst_strategy': self.get_worst_strategy(),
            'last_update': time.time(),
        }
    
    # ==================== 序列化 ====================
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        return {
            'strategy_performance': {
                name: {
                    'total_uses': perf.total_uses,
                    'win_count': perf.win_count,
                    'loss_count': perf.loss_count,
                    'total_pnl': perf.total_pnl,
                    'avg_pnl': perf.avg_pnl,
                    'win_rate': perf.win_rate,
                }
                for name, perf in self.strategy_performance.items()
            },
            'regime_preferences': self.regime_preferences,
            'learned_patterns': [
                {
                    'pattern_type': p.pattern_type,
                    'condition': p.condition,
                    'success_rate': p.success_rate,
                    'recommended_action': p.recommended_action,
                    'sample_count': p.sample_count,
                }
                for p in self.learned_patterns
            ],
            'epiphanies_count': len(self.epiphanies),
            'meditation_count': len(self.meditation_history),
        }

