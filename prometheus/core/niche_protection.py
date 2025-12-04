"""
生态位保护系统 (Niche Protection System) - Prometheus v5.1
=========================================================

防止策略单一化，维持生态多样性

核心概念：
- 生态位（Niche）= 策略类型（TrendFollowing、GridTrading等）
- 同策略竞争激烈，跨策略相对保护
- 少数派策略获得评估加成

Author: Prometheus Team
Version: 5.1
Date: 2025-12-04
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class NicheStatus:
    """策略生态位状态"""
    strategy_type: str          # 策略类型
    agent_count: int            # 该策略的Agent数量
    population_ratio: float     # 占总体的比例
    diversity_bonus: float      # 多样性奖励（0-1）
    competition_penalty: float  # 竞争惩罚（0-1）


class NicheProtectionSystem:
    """
    生态位保护系统
    
    功能：
    1. 分析策略分布
    2. 计算多样性奖励
    3. 应用竞争惩罚
    4. 保护少数派策略
    """
    
    # 配置参数
    MIN_DIVERSITY_RATIO = 0.05      # 最小多样性比例（每种策略至少5%）
    MAX_STRATEGY_RATIO = 0.60       # 最大策略占比（单一策略不超过60%）
    COMPETITION_FACTOR = 2.0        # 竞争因子（同策略内竞争强度）
    PROTECTION_FACTOR = 1.5         # 保护因子（少数派策略保护强度）
    
    def __init__(
        self,
        min_diversity_ratio: float = MIN_DIVERSITY_RATIO,
        max_strategy_ratio: float = MAX_STRATEGY_RATIO,
        enable_protection: bool = True,
    ):
        """
        初始化生态位保护系统
        
        Args:
            min_diversity_ratio: 最小多样性比例
            max_strategy_ratio: 最大策略占比
            enable_protection: 是否启用保护机制
        """
        self.min_diversity_ratio = min_diversity_ratio
        self.max_strategy_ratio = max_strategy_ratio
        self.enable_protection = enable_protection
        
        logger.info(
            f"生态位保护系统已初始化 | "
            f"最小多样性={min_diversity_ratio:.0%} | "
            f"最大占比={max_strategy_ratio:.0%}"
        )
    
    def analyze_strategy_distribution(
        self,
        agents: List
    ) -> Dict[str, NicheStatus]:
        """
        分析策略分布
        
        Args:
            agents: Agent列表
        
        Returns:
            Dict[str, NicheStatus]: 策略生态位状态字典
        """
        if not agents:
            return {}
        
        # 统计每个Agent的主要策略
        strategy_counts = Counter()
        agent_strategies = {}
        
        for agent in agents:
            # 获取Agent的主要策略
            primary_strategy = self._get_primary_strategy(agent)
            strategy_counts[primary_strategy] += 1
            agent_strategies[agent.agent_id] = primary_strategy
        
        total_agents = len(agents)
        
        # 计算每个策略的生态位状态
        niche_statuses = {}
        
        for strategy_type, count in strategy_counts.items():
            ratio = count / total_agents
            
            # 计算多样性奖励（少数派策略获得更高奖励）
            diversity_bonus = self._calculate_diversity_bonus(ratio)
            
            # 计算竞争惩罚（占比越高，竞争越激烈）
            competition_penalty = self._calculate_competition_penalty(ratio)
            
            niche_statuses[strategy_type] = NicheStatus(
                strategy_type=strategy_type,
                agent_count=count,
                population_ratio=ratio,
                diversity_bonus=diversity_bonus,
                competition_penalty=competition_penalty,
            )
        
        # 日志输出
        logger.info(f"📊 策略生态位分析:")
        for status in niche_statuses.values():
            logger.info(
                f"   {status.strategy_type:20s}: "
                f"{status.agent_count:3d}个 ({status.population_ratio:5.1%}) | "
                f"多样性奖励+{status.diversity_bonus:4.1%} | "
                f"竞争惩罚-{status.competition_penalty:4.1%}"
            )
        
        return niche_statuses
    
    def _get_primary_strategy(self, agent) -> str:
        """
        获取Agent的主要策略
        
        Args:
            agent: Agent对象
        
        Returns:
            str: 主要策略名称
        """
        if hasattr(agent, 'active_strategies') and agent.active_strategies:
            # 返回第一个激活的策略
            return agent.active_strategies[0].name
        elif hasattr(agent, 'strategy_pool') and agent.strategy_pool:
            # 返回策略池中的第一个策略
            return agent.strategy_pool[0].name
        elif hasattr(agent, 'meta_genome') and agent.meta_genome:
            # 根据元基因组的策略偏好判断
            prefs = agent.meta_genome.get_strategy_preferences()
            return max(prefs, key=prefs.get)
        else:
            # 默认
            return "Unknown"
    
    def _calculate_diversity_bonus(self, population_ratio: float) -> float:
        """
        计算多样性奖励
        
        少数派策略获得更高奖励
        
        Args:
            population_ratio: 策略占比
        
        Returns:
            float: 多样性奖励（0-1）
        """
        if not self.enable_protection:
            return 0.0
        
        # 占比越低，奖励越高
        if population_ratio < self.min_diversity_ratio:
            # 极少数派：最高奖励
            bonus = self.PROTECTION_FACTOR * (1 - population_ratio)
        elif population_ratio < 0.2:
            # 少数派：高奖励
            bonus = self.PROTECTION_FACTOR * (0.5 - population_ratio)
        elif population_ratio < 0.4:
            # 中等规模：低奖励
            bonus = 0.1 * (0.4 - population_ratio)
        else:
            # 多数派：无奖励
            bonus = 0.0
        
        return max(0.0, min(1.0, bonus))
    
    def _calculate_competition_penalty(self, population_ratio: float) -> float:
        """
        计算竞争惩罚
        
        同策略Agent越多，竞争越激烈
        
        Args:
            population_ratio: 策略占比
        
        Returns:
            float: 竞争惩罚（0-1）
        """
        if not self.enable_protection:
            return 0.0
        
        # 占比越高，惩罚越大
        if population_ratio > self.max_strategy_ratio:
            # 严重过剩：高惩罚
            penalty = self.COMPETITION_FACTOR * (population_ratio - self.max_strategy_ratio)
        elif population_ratio > 0.4:
            # 过剩：中等惩罚
            penalty = 0.5 * (population_ratio - 0.4)
        elif population_ratio > 0.2:
            # 正常竞争：低惩罚
            penalty = 0.2 * (population_ratio - 0.2)
        else:
            # 少数派：无惩罚
            penalty = 0.0
        
        return max(0.0, min(1.0, penalty))
    
    def apply_niche_adjustment(
        self,
        agent,
        base_score: float,
        niche_statuses: Dict[str, NicheStatus]
    ) -> Tuple[float, str]:
        """
        应用生态位调整
        
        Args:
            agent: Agent对象
            base_score: 基础评分
            niche_statuses: 策略生态位状态
        
        Returns:
            Tuple[float, str]: (调整后评分, 调整原因)
        """
        if not self.enable_protection:
            return base_score, "无生态位保护"
        
        # 获取Agent的策略
        strategy = self._get_primary_strategy(agent)
        
        if strategy not in niche_statuses:
            return base_score, f"未知策略{strategy}"
        
        status = niche_statuses[strategy]
        
        # 计算调整
        adjustment = status.diversity_bonus - status.competition_penalty
        adjusted_score = base_score * (1 + adjustment)
        
        # 生成调整原因
        if adjustment > 0:
            reason = f"少数派保护+{adjustment:.1%}"
        elif adjustment < 0:
            reason = f"同策略竞争{adjustment:.1%}"
        else:
            reason = "无调整"
        
        return adjusted_score, reason
    
    def check_diversity_health(
        self,
        niche_statuses: Dict[str, NicheStatus]
    ) -> Dict[str, any]:
        """
        检查生态多样性健康度
        
        Args:
            niche_statuses: 策略生态位状态
        
        Returns:
            Dict: 健康度报告
        """
        if not niche_statuses:
            return {
                'health': 'unknown',
                'diversity_score': 0.0,
                'warnings': ['无策略分布数据'],
            }
        
        warnings = []
        
        # 1. 检查策略数量
        strategy_count = len(niche_statuses)
        if strategy_count < 2:
            warnings.append(f"策略数量过少：只有{strategy_count}种")
        
        # 2. 检查单一策略占比
        for status in niche_statuses.values():
            if status.population_ratio > self.max_strategy_ratio:
                warnings.append(
                    f"{status.strategy_type}占比过高：{status.population_ratio:.1%}"
                )
        
        # 3. 检查是否有濒危策略
        for status in niche_statuses.values():
            if status.population_ratio < self.min_diversity_ratio:
                warnings.append(
                    f"{status.strategy_type}濒临灭绝：仅{status.population_ratio:.1%}"
                )
        
        # 4. 计算多样性分数（Shannon熵）
        import numpy as np
        ratios = [status.population_ratio for status in niche_statuses.values()]
        diversity_score = -sum(r * np.log(r) if r > 0 else 0 for r in ratios)
        max_diversity = np.log(len(niche_statuses))
        normalized_diversity = diversity_score / max_diversity if max_diversity > 0 else 0
        
        # 5. 判断健康度
        if normalized_diversity > 0.9:
            health = 'excellent'
        elif normalized_diversity > 0.7:
            health = 'good'
        elif normalized_diversity > 0.5:
            health = 'fair'
        elif normalized_diversity > 0.3:
            health = 'poor'
        else:
            health = 'critical'
        
        return {
            'health': health,
            'diversity_score': normalized_diversity,
            'strategy_count': strategy_count,
            'warnings': warnings,
        }
    
    def get_protection_summary(
        self,
        niche_statuses: Dict[str, NicheStatus]
    ) -> str:
        """
        获取生态位保护摘要
        
        Args:
            niche_statuses: 策略生态位状态
        
        Returns:
            str: 摘要文本
        """
        health_report = self.check_diversity_health(niche_statuses)
        
        summary = f"生态多样性: {health_report['health']} ({health_report['diversity_score']:.2f})\n"
        summary += f"策略数量: {health_report['strategy_count']}\n"
        
        if health_report['warnings']:
            summary += "⚠️  警告:\n"
            for warning in health_report['warnings']:
                summary += f"  - {warning}\n"
        
        return summary

