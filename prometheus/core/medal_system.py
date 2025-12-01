"""
奖章制度系统 - Prometheus v4.0
监督者颁发的荣誉系统，影响基因库收录和Agent性格
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MedalType(Enum):
    """奖章类型"""
    # 盈利相关
    PROFIT_MASTER = "profit_master"           # 盈利大师 - 总收益 > 50%
    CONSISTENT_EARNER = "consistent_earner"   # 稳定盈利 - 连续30天盈利
    QUICK_PROFIT = "quick_profit"             # 快速盈利 - 7天盈利 > 20%
    
    # 风险控制
    RISK_MANAGER = "risk_manager"             # 风险大师 - 最大回撤 < 10%
    STOP_LOSS_KING = "stop_loss_king"         # 止损之王 - 严格执行止损
    SURVIVOR = "survivor"                     # 幸存者 - 存活 > 90天
    
    # 交易技巧
    HIGH_WIN_RATE = "high_win_rate"           # 高胜率 - 胜率 > 70%
    SHARP_TRADER = "sharp_trader"             # 夏普高手 - Sharpe > 2.0
    TREND_MASTER = "trend_master"             # 趋势大师 - 在趋势中盈利
    
    # 逆境求生
    COMEBACK_HERO = "comeback_hero"           # 绝地反击 - 从30%恢复到100%
    LAST_STAND_WINNER = "last_stand_winner"   # 拼搏胜利 - 拼死一搏成功
    PHOENIX = "phoenix"                       # 凤凰涅槃 - 多次从困境中复活
    
    # 适应能力
    MARKET_ADAPTOR = "market_adaptor"         # 市场适应 - 适应多种市场环境
    VERSATILE = "versatile"                   # 全能型 - 多策略盈利
    QUICK_LEARNER = "quick_learner"           # 快速学习 - 短时间内改善表现
    
    # 群体贡献
    GENE_CONTRIBUTOR = "gene_contributor"     # 基因贡献 - 子代表现优秀
    DIVERSITY_KEEPER = "diversity_keeper"     # 多样性守护 - 独特策略
    ELDER = "elder"                           # 长老 - 存活最久的Agent之一
    
    # 特殊成就
    LEGEND = "legend"                         # 传奇 - 拥有5个以上其他奖章
    PERFECT_MONTH = "perfect_month"           # 完美月 - 30天无亏损交易
    HUNDRED_TRADES = "hundred_trades"         # 百战勇士 - 完成100笔交易


@dataclass
class Medal:
    """奖章数据"""
    medal_type: MedalType
    awarded_at: datetime
    reason: str
    agent_id: str
    metrics: Dict  # 获得时的相关指标
    
    def __str__(self):
        return f"🏅 {self.medal_type.value} ({self.awarded_at.strftime('%Y-%m-%d')})"


@dataclass
class MedalCriteria:
    """奖章评判标准"""
    name: str
    description: str
    check_function: str  # 检查函数名
    difficulty: int  # 难度等级 1-5
    influence_on_confidence: float  # 对信心的影响 0-0.2
    influence_on_personality: Dict  # 对性格的影响
    
    # 收录基因库的权重
    gene_pool_weight: float = 1.0


class MedalSystem:
    """
    奖章制度系统
    
    职责：
    1. 评估Agent表现，颁发奖章
    2. 统计Agent奖章数量
    3. 影响基因库收录标准
    4. 影响Agent性格和信心
    """
    
    # 奖章标准定义
    MEDAL_CRITERIA = {
        MedalType.PROFIT_MASTER: MedalCriteria(
            name="盈利大师",
            description="总收益超过50%",
            check_function="check_profit_master",
            difficulty=4,
            influence_on_confidence=0.15,
            influence_on_personality={'optimism': 0.1, 'confidence': 0.15},
            gene_pool_weight=2.0
        ),
        MedalType.CONSISTENT_EARNER: MedalCriteria(
            name="稳定盈利",
            description="连续30天保持盈利",
            check_function="check_consistent_earner",
            difficulty=4,
            influence_on_confidence=0.12,
            influence_on_personality={'discipline': 0.15, 'patience': 0.1},
            gene_pool_weight=2.5
        ),
        MedalType.RISK_MANAGER: MedalCriteria(
            name="风险大师",
            description="最大回撤小于10%",
            check_function="check_risk_manager",
            difficulty=3,
            influence_on_confidence=0.10,
            influence_on_personality={'discipline': 0.15, 'risk_tolerance': -0.05},
            gene_pool_weight=1.8
        ),
        MedalType.HIGH_WIN_RATE: MedalCriteria(
            name="高胜率",
            description="胜率超过70%",
            check_function="check_high_win_rate",
            difficulty=3,
            influence_on_confidence=0.12,
            influence_on_personality={'confidence': 0.1},
            gene_pool_weight=1.5
        ),
        MedalType.COMEBACK_HERO: MedalCriteria(
            name="绝地反击",
            description="从30%资金恢复到100%",
            check_function="check_comeback_hero",
            difficulty=5,
            influence_on_confidence=0.20,
            influence_on_personality={'survival_will': 0.2, 'optimism': 0.15},
            gene_pool_weight=3.0
        ),
        MedalType.LAST_STAND_WINNER: MedalCriteria(
            name="拼搏胜利",
            description="拼死一搏成功翻盘",
            check_function="check_last_stand_winner",
            difficulty=5,
            influence_on_confidence=0.18,
            influence_on_personality={'aggression': 0.1, 'survival_will': 0.15},
            gene_pool_weight=2.8
        ),
        MedalType.SURVIVOR: MedalCriteria(
            name="幸存者",
            description="存活超过90天",
            check_function="check_survivor",
            difficulty=3,
            influence_on_confidence=0.08,
            influence_on_personality={'adaptability': 0.1, 'patience': 0.1},
            gene_pool_weight=1.5
        ),
        MedalType.SHARP_TRADER: MedalCriteria(
            name="夏普高手",
            description="夏普比率超过2.0",
            check_function="check_sharp_trader",
            difficulty=4,
            influence_on_confidence=0.15,
            influence_on_personality={'discipline': 0.1},
            gene_pool_weight=2.2
        ),
        MedalType.LEGEND: MedalCriteria(
            name="传奇",
            description="拥有5个以上奖章",
            check_function="check_legend",
            difficulty=5,
            influence_on_confidence=0.20,
            influence_on_personality={'confidence': 0.2, 'competitiveness': 0.15},
            gene_pool_weight=5.0
        ),
    }
    
    def __init__(self):
        """初始化奖章系统"""
        # Agent奖章记录 {agent_id: [Medal]}
        self.agent_medals: Dict[str, List[Medal]] = {}
        
        # 颁发历史
        self.award_history: List[Dict] = []
        
        logger.info("奖章系统已初始化")
    
    def evaluate_and_award(self, agent_data: Dict) -> List[Medal]:
        """
        评估Agent并颁发奖章
        
        Args:
            agent_data: Agent数据
            
        Returns:
            List[Medal]: 新获得的奖章列表
        """
        agent_id = agent_data['agent_id']
        newly_awarded = []
        
        # 获取已有奖章
        existing_medals = set(
            m.medal_type for m in self.agent_medals.get(agent_id, [])
        )
        
        # 检查每种奖章
        for medal_type, criteria in self.MEDAL_CRITERIA.items():
            # 如果已经有了，跳过
            if medal_type in existing_medals:
                continue
            
            # 检查是否满足条件
            check_func = getattr(self, criteria.check_function, None)
            if check_func and check_func(agent_data):
                medal = self._award_medal(agent_id, medal_type, agent_data)
                newly_awarded.append(medal)
        
        return newly_awarded
    
    def _award_medal(self, agent_id: str, medal_type: MedalType, agent_data: Dict) -> Medal:
        """
        颁发奖章
        
        Args:
            agent_id: Agent ID
            medal_type: 奖章类型
            agent_data: Agent数据
            
        Returns:
            Medal: 奖章对象
        """
        criteria = self.MEDAL_CRITERIA[medal_type]
        
        medal = Medal(
            medal_type=medal_type,
            awarded_at=datetime.now(),
            reason=criteria.description,
            agent_id=agent_id,
            metrics={
                'total_return': agent_data.get('total_return', 0),
                'win_rate': agent_data.get('win_rate', 0),
                'days_alive': agent_data.get('days_alive', 0),
                'sharpe_ratio': agent_data.get('sharpe_ratio', 0)
            }
        )
        
        # 记录
        if agent_id not in self.agent_medals:
            self.agent_medals[agent_id] = []
        self.agent_medals[agent_id].append(medal)
        
        # 记录历史
        self.award_history.append({
            'agent_id': agent_id,
            'medal_type': medal_type.value,
            'awarded_at': medal.awarded_at,
            'difficulty': criteria.difficulty
        })
        
        logger.info(f"🎖️  颁发奖章给 {agent_id}: {criteria.name} - {criteria.description}")
        
        return medal
    
    # ========================================
    # 奖章检查函数
    # ========================================
    
    def check_profit_master(self, data: Dict) -> bool:
        """检查：盈利大师"""
        return data.get('total_return', 0) > 0.5
    
    def check_consistent_earner(self, data: Dict) -> bool:
        """检查：稳定盈利"""
        return (
            data.get('days_alive', 0) >= 30 and
            data.get('total_return', 0) > 0 and
            data.get('consecutive_losses', 0) < 3
        )
    
    def check_risk_manager(self, data: Dict) -> bool:
        """检查：风险大师"""
        return (
            data.get('max_drawdown', 1.0) < 0.1 and
            data.get('trade_count', 0) > 20
        )
    
    def check_high_win_rate(self, data: Dict) -> bool:
        """检查：高胜率"""
        return (
            data.get('win_rate', 0) > 0.7 and
            data.get('trade_count', 0) > 30
        )
    
    def check_comeback_hero(self, data: Dict) -> bool:
        """检查：绝地反击"""
        return (
            data.get('min_capital_ratio', 1.0) < 0.35 and  # 曾经低于35%
            data.get('current_capital_ratio', 0) >= 1.0     # 恢复到100%
        )
    
    def check_last_stand_winner(self, data: Dict) -> bool:
        """检查：拼搏胜利"""
        return data.get('last_stand_success', False)
    
    def check_survivor(self, data: Dict) -> bool:
        """检查：幸存者"""
        return data.get('days_alive', 0) >= 90
    
    def check_sharp_trader(self, data: Dict) -> bool:
        """检查：夏普高手"""
        return (
            data.get('sharpe_ratio', 0) > 2.0 and
            data.get('trade_count', 0) > 50
        )
    
    def check_legend(self, data: Dict) -> bool:
        """检查：传奇"""
        agent_id = data['agent_id']
        medal_count = len(self.agent_medals.get(agent_id, []))
        return medal_count >= 5
    
    # ========================================
    # 奖章影响系统
    # ========================================
    
    def calculate_medal_influence_on_confidence(self, agent_id: str) -> float:
        """
        计算奖章对信心的影响
        
        Args:
            agent_id: Agent ID
            
        Returns:
            float: 信心增量 (0-1)
        """
        medals = self.agent_medals.get(agent_id, [])
        if not medals:
            return 0.0
        
        total_influence = 0.0
        for medal in medals:
            criteria = self.MEDAL_CRITERIA.get(medal.medal_type)
            if criteria:
                total_influence += criteria.influence_on_confidence
        
        # 奖章数量也有额外加成
        medal_count_bonus = min(len(medals) * 0.02, 0.15)
        
        return min(total_influence + medal_count_bonus, 0.5)  # 最大0.5
    
    def calculate_medal_influence_on_personality(self, agent_id: str) -> Dict[str, float]:
        """
        计算奖章对性格的影响
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Dict: 性格调整 {trait: adjustment}
        """
        medals = self.agent_medals.get(agent_id, [])
        if not medals:
            return {}
        
        personality_adjustments = {}
        
        for medal in medals:
            criteria = self.MEDAL_CRITERIA.get(medal.medal_type)
            if criteria and criteria.influence_on_personality:
                for trait, adjustment in criteria.influence_on_personality.items():
                    personality_adjustments[trait] = (
                        personality_adjustments.get(trait, 0) + adjustment
                    )
        
        return personality_adjustments
    
    def calculate_gene_pool_score(self, agent_id: str, base_fitness: float) -> float:
        """
        计算进入基因库的综合得分
        
        奖章数量和质量是关键标准
        
        Args:
            agent_id: Agent ID
            base_fitness: 基础适应度
            
        Returns:
            float: 综合得分 (0-10)
        """
        medals = self.agent_medals.get(agent_id, [])
        
        if not medals:
            # 没有奖章，很难进入基因库
            return base_fitness * 0.5
        
        # 计算奖章权重总和
        medal_weight = 0.0
        for medal in medals:
            criteria = self.MEDAL_CRITERIA.get(medal.medal_type)
            if criteria:
                medal_weight += criteria.gene_pool_weight
        
        # 综合得分 = 基础适应度 + 奖章加权
        score = base_fitness * 3 + medal_weight
        
        # 传奇奖章额外加成
        if any(m.medal_type == MedalType.LEGEND for m in medals):
            score *= 1.5
        
        return min(score, 10.0)
    
    def is_qualified_for_gene_pool(self, agent_id: str, base_fitness: float) -> bool:
        """
        判断是否有资格进入基因库
        
        v4.0标准：必须有奖章才能进入基因库
        
        Args:
            agent_id: Agent ID
            base_fitness: 基础适应度
            
        Returns:
            bool: 是否有资格
        """
        medals = self.agent_medals.get(agent_id, [])
        medal_count = len(medals)
        
        # 基本要求：至少1个奖章
        if medal_count == 0:
            return False
        
        # 计算得分
        score = self.calculate_gene_pool_score(agent_id, base_fitness)
        
        # 门槛：得分 > 3.0
        return score > 3.0
    
    def get_agent_medals(self, agent_id: str) -> List[Medal]:
        """获取Agent的所有奖章"""
        return self.agent_medals.get(agent_id, [])
    
    def get_medal_count(self, agent_id: str) -> int:
        """获取Agent奖章数量"""
        return len(self.agent_medals.get(agent_id, []))
    
    def get_statistics(self) -> Dict:
        """
        获取奖章系统统计
        
        Returns:
            Dict: 统计信息
        """
        total_medals_awarded = sum(len(medals) for medals in self.agent_medals.values())
        
        # 各类奖章数量统计
        medal_type_counts = {}
        for medals in self.agent_medals.values():
            for medal in medals:
                medal_type = medal.medal_type.value
                medal_type_counts[medal_type] = medal_type_counts.get(medal_type, 0) + 1
        
        # 最多奖章的Agent
        top_agents = sorted(
            [(agent_id, len(medals)) for agent_id, medals in self.agent_medals.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_agents_with_medals': len(self.agent_medals),
            'total_medals_awarded': total_medals_awarded,
            'medal_type_distribution': medal_type_counts,
            'top_agents': top_agents,
            'award_history_count': len(self.award_history)
        }

