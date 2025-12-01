"""
公告板系统 - Prometheus v4.0
提供环境信息，Agent自主选择是否遵循
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BulletinType(Enum):
    """公告类型"""
    MASTERMIND_STRATEGIC = "global"    # 主脑战略
    MARKET_EVENT = "market"            # 市场事件
    RISK_WARNING = "system"            # 系统风险
    AGENT_SIGNAL = "social"            # Agent信号


class Priority(Enum):
    """优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Bulletin:
    """公告"""
    bulletin_id: str
    type: BulletinType
    timestamp: datetime
    content: str
    priority: Priority
    source: str
    
    # 元数据
    tags: List[str] = None
    sentiment: Optional[str] = None  # positive/negative/neutral
    impact_level: Optional[str] = None  # high/medium/low
    expires: Optional[datetime] = None
    
    # 效果追踪
    view_count: int = 0
    followed_count: int = 0
    effectiveness_score: float = 0.0


class BulletinBoard:
    """公告板基类"""
    
    def __init__(self, board_name: str, max_bulletins: int = 100):
        """
        初始化公告板
        
        Args:
            board_name: 公告板名称
            max_bulletins: 最大公告数量
        """
        self.board_name = board_name
        self.max_bulletins = max_bulletins
        self.bulletins: List[Bulletin] = []
        self.bulletin_counter = 0
        
    def post(self, 
             content: str,
             priority: Priority = Priority.MEDIUM,
             source: str = "system",
             **kwargs) -> Bulletin:
        """
        发布公告
        
        Args:
            content: 公告内容
            priority: 优先级
            source: 来源
            **kwargs: 其他元数据
            
        Returns:
            Bulletin: 发布的公告
        """
        self.bulletin_counter += 1
        
        bulletin = Bulletin(
            bulletin_id=f"{self.board_name}-{self.bulletin_counter:06d}",
            type=kwargs.get('type', BulletinType.MARKET_EVENT),
            timestamp=datetime.now(),
            content=content,
            priority=priority,
            source=source,
            tags=kwargs.get('tags', []),
            sentiment=kwargs.get('sentiment'),
            impact_level=kwargs.get('impact_level'),
            expires=kwargs.get('expires', datetime.now() + timedelta(days=7))
        )
        
        self.bulletins.append(bulletin)
        
        # 清理旧公告
        if len(self.bulletins) > self.max_bulletins:
            self._cleanup()
        
        logger.info(f"📢 [{self.board_name}] 发布公告: {content[:50]}...")
        
        return bulletin
    
    def get_recent(self, hours: int = 24, min_priority: Priority = Priority.LOW) -> List[Bulletin]:
        """
        获取最近的公告
        
        Args:
            hours: 最近几小时
            min_priority: 最低优先级
            
        Returns:
            List[Bulletin]: 公告列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_bulletins = [
            b for b in self.bulletins
            if b.timestamp > cutoff_time and not self._is_expired(b)
        ]
        
        # 按优先级排序
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        
        recent_bulletins.sort(key=lambda x: (priority_order[x.priority], -x.timestamp.timestamp()))
        
        return recent_bulletins
    
    def _is_expired(self, bulletin: Bulletin) -> bool:
        """检查是否过期"""
        if bulletin.expires:
            return datetime.now() > bulletin.expires
        return False
    
    def _cleanup(self):
        """清理过期和低价值公告"""
        # 移除过期
        self.bulletins = [b for b in self.bulletins if not self._is_expired(b)]
        
        # 如果还是太多，移除最旧的低优先级公告
        if len(self.bulletins) > self.max_bulletins:
            self.bulletins.sort(key=lambda x: (x.priority.value, -x.timestamp.timestamp()))
            self.bulletins = self.bulletins[:self.max_bulletins]


class BulletinBoardSystem:
    """
    完整的公告板系统
    
    四层公告板：
    1. 全局公告板（主脑）
    2. 市场公告板（外部信息）
    3. 系统公告板（监督者）
    4. 社交公告板（Agent）
    """
    
    def __init__(self):
        """初始化四层公告板"""
        self.global_board = BulletinBoard("Global")
        self.market_board = BulletinBoard("Market")
        self.system_board = BulletinBoard("System")
        self.social_board = BulletinBoard("Social", max_bulletins=200)
        
        logger.info("公告板系统已初始化（四层）")
    
    def post_strategic(self, content: str, **kwargs):
        """主脑发布战略公告"""
        return self.global_board.post(
            content=content,
            type=BulletinType.MASTERMIND_STRATEGIC,
            source="Mastermind",
            priority=Priority.HIGH,
            **kwargs
        )
    
    def post_market_event(self, content: str, impact: str, sentiment: str, **kwargs):
        """发布市场事件"""
        return self.market_board.post(
            content=content,
            type=BulletinType.MARKET_EVENT,
            source="External",
            impact_level=impact,
            sentiment=sentiment,
            priority=Priority.HIGH if impact == 'high' else Priority.MEDIUM,
            **kwargs
        )
    
    def post_risk_warning(self, content: str, severity: str, **kwargs):
        """监督者发布风险警告"""
        priority_map = {
            'critical': Priority.CRITICAL,
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM
        }
        
        return self.system_board.post(
            content=content,
            type=BulletinType.RISK_WARNING,
            source="Supervisor",
            priority=priority_map.get(severity, Priority.MEDIUM),
            **kwargs
        )
    
    def post_agent_signal(self, agent_id: str, signal: Dict, credibility: float, **kwargs):
        """Agent发布信号"""
        content = f"Agent {agent_id}: {signal.get('description', '')}"
        
        return self.social_board.post(
            content=content,
            type=BulletinType.AGENT_SIGNAL,
            source=agent_id,
            priority=Priority.LOW,
            sentiment=signal.get('sentiment'),
            credibility=credibility,
            **kwargs
        )
    
    def get_bulletins_for_agent(self, agent_subscription: Dict) -> List[Bulletin]:
        """
        根据Agent订阅获取相关公告
        
        Args:
            agent_subscription: Agent的订阅配置
            
        Returns:
            List[Bulletin]: 相关公告列表
        """
        bulletins = []
        
        if agent_subscription.get('global', True):
            bulletins.extend(self.global_board.get_recent(hours=24))
        
        if agent_subscription.get('market', True):
            bulletins.extend(self.market_board.get_recent(hours=6))
        
        if agent_subscription.get('system', True):
            bulletins.extend(self.system_board.get_recent(hours=12))
        
        if agent_subscription.get('social', False):
            bulletins.extend(self.social_board.get_recent(hours=1))
        
        return bulletins
    
    def get_statistics(self) -> Dict:
        """获取公告板统计"""
        return {
            'global_bulletins': len(self.global_board.bulletins),
            'market_bulletins': len(self.market_board.bulletins),
            'system_bulletins': len(self.system_board.bulletins),
            'social_bulletins': len(self.social_board.bulletins),
            'total_bulletins': (
                len(self.global_board.bulletins) +
                len(self.market_board.bulletins) +
                len(self.system_board.bulletins) +
                len(self.social_board.bulletins)
            )
        }


class AgentBulletinProcessor:
    """
    Agent的公告处理器
    
    负责：
    1. 过滤相关公告
    2. 解读公告内容
    3. 转换为交易信号
    4. 学习公告效果
    """
    
    def __init__(self, agent):
        """
        初始化
        
        Args:
            agent: Agent实例
        """
        self.agent = agent
        
        # 学习到的信任度
        self.learned_trust = {
            'global': 0.5,
            'market': 0.5,
            'system': 0.5,
            'social': 0.5
        }
        
        # 历史记录
        self.bulletin_history = []
    
    def process_bulletins(self, bulletins: List[Bulletin]) -> float:
        """
        处理公告，返回信号
        
        Args:
            bulletins: 公告列表
            
        Returns:
            float: -1.0到1.0的交易信号
        """
        if not bulletins:
            return 0.0
        
        signal = 0.0
        total_weight = 0.0
        
        for bulletin in bulletins:
            # 1. 基因敏感度（先天）
            gene_sensitivity = self.agent.gene.get('bulletin_sensitivity', {}).get(
                bulletin.type.value, 0.5
            )
            
            # 2. 学习的信任度（后天）
            learned_trust = self.learned_trust.get(bulletin.type.value, 0.5)
            
            # 3. 综合权重
            weight = gene_sensitivity * learned_trust
            
            # 4. 权重太低则忽略
            if weight < 0.1:
                continue
            
            # 5. 解读公告
            bulletin_signal = self._interpret_bulletin(bulletin)
            
            # 6. 时间衰减
            time_decay = self._calculate_time_decay(bulletin)
            
            # 7. 累加
            signal += bulletin_signal * weight * time_decay
            total_weight += weight * time_decay
            
            # 记录查看
            bulletin.view_count += 1
        
        # 8. 归一化
        return signal / total_weight if total_weight > 0 else 0.0
    
    def _interpret_bulletin(self, bulletin: Bulletin) -> float:
        """
        解读公告内容
        
        不同Agent可能有不同解读！
        """
        signal = 0.0
        
        # 基于公告内容提取信号
        content_lower = bulletin.content.lower()
        
        # 关键词分析
        bullish_keywords = ['bullish', 'buy', 'long', 'pump', 'moon']
        bearish_keywords = ['bearish', 'sell', 'short', 'dump', 'crash']
        
        bullish_score = sum(1 for kw in bullish_keywords if kw in content_lower)
        bearish_score = sum(1 for kw in bearish_keywords if kw in content_lower)
        
        if bullish_score > bearish_score:
            signal = 0.5 + (bullish_score - bearish_score) * 0.1
        elif bearish_score > bullish_score:
            signal = -0.5 - (bearish_score - bullish_score) * 0.1
        
        # 应用性格偏差
        signal = self._apply_personality_bias(signal, bulletin)
        
        return max(-1.0, min(1.0, signal))
    
    def _apply_personality_bias(self, signal: float, bulletin: Bulletin) -> float:
        """
        性格影响对公告的解读
        """
        # 逆向型：反向解读
        if self.agent.personality.contrarian > 0.7:
            signal *= -0.5
        
        # 从众型：放大信号
        if self.agent.personality.herd_mentality > 0.7:
            signal *= 1.5
        
        # 谨慎型：只关注负面
        if self.agent.personality.risk_tolerance < 0.3:
            if signal > 0:
                signal *= 0.5  # 减弱看多
            else:
                signal *= 1.5  # 放大看空
        
        # 乐观型：偏乐观
        if self.agent.personality.optimism > 0.7:
            signal += 0.1
        
        return signal
    
    def _calculate_time_decay(self, bulletin: Bulletin) -> float:
        """
        计算时间衰减
        
        信息越旧，权重越低
        """
        age_hours = (datetime.now() - bulletin.timestamp).total_seconds() / 3600
        
        # 不同类型公告衰减速度不同
        decay_rates = {
            BulletinType.MASTERMIND_STRATEGIC: 0.05,  # 战略公告衰减慢
            BulletinType.MARKET_EVENT: 0.2,           # 市场事件衰减快
            BulletinType.RISK_WARNING: 0.15,          # 风险警告中等
            BulletinType.AGENT_SIGNAL: 0.3            # 社交信号衰减最快
        }
        
        decay_rate = decay_rates.get(bulletin.type, 0.15)
        decay_factor = 1.0 / (1.0 + age_hours * decay_rate)
        
        return decay_factor
    
    def record_outcome(self, bulletin_type: str, followed: bool, result: float):
        """
        记录公告效果（用于学习）
        
        Args:
            bulletin_type: 公告类型
            followed: 是否遵循
            result: 结果（盈亏）
        """
        self.bulletin_history.append({
            'type': bulletin_type,
            'followed': followed,
            'result': result,
            'timestamp': datetime.now()
        })
        
        # 更新学习的信任度
        self._update_trust(bulletin_type, result if followed else 0)
    
    def _update_trust(self, bulletin_type: str, result: float):
        """
        更新对某类公告的信任度
        
        强化学习：好结果增加信任，坏结果降低信任
        """
        learning_rate = self.agent.personality.learning_rate
        
        current_trust = self.learned_trust.get(bulletin_type, 0.5)
        
        # 简单的增量更新
        if result > 0:
            new_trust = current_trust + learning_rate * 0.1
        else:
            new_trust = current_trust - learning_rate * 0.1
        
        # 限制范围
        self.learned_trust[bulletin_type] = max(0.0, min(1.0, new_trust))


class BulletinBoardSystem:
    """
    完整的公告板系统
    """
    
    def __init__(self):
        """初始化四层公告板"""
        self.global_board = BulletinBoard("Global")
        self.market_board = BulletinBoard("Market")
        self.system_board = BulletinBoard("System")
        self.social_board = BulletinBoard("Social", max_bulletins=200)
        
        logger.info("公告板系统已初始化")
    
    def post(self, board_type: str, content: str, **kwargs) -> Bulletin:
        """
        通用发布接口
        
        Args:
            board_type: 公告板类型 ("global"/"market"/"system"/"social")
            content: 内容
            **kwargs: 其他参数
            
        Returns:
            Bulletin: 发布的公告
        """
        boards = {
            'global': self.global_board,
            'market': self.market_board,
            'system': self.system_board,
            'social': self.social_board
        }
        
        board = boards.get(board_type)
        if board:
            return board.post(content, **kwargs)
        else:
            logger.error(f"未知的公告板类型: {board_type}")
            return None
    
    def get_bulletins_for_agent(self, agent_subscription: Dict) -> List[Bulletin]:
        """
        根据Agent订阅获取公告
        
        Args:
            agent_subscription: Agent的订阅配置
            
        Returns:
            List[Bulletin]: 公告列表
        """
        bulletins = []
        
        if agent_subscription.get('global', True):
            bulletins.extend(self.global_board.get_recent(hours=24))
        
        if agent_subscription.get('market', True):
            bulletins.extend(self.market_board.get_recent(hours=6))
        
        if agent_subscription.get('system', True):
            bulletins.extend(self.system_board.get_recent(hours=12))
        
        if agent_subscription.get('social', False):
            bulletins.extend(self.social_board.get_recent(hours=1))
        
        return bulletins
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'global': len(self.global_board.bulletins),
            'market': len(self.market_board.bulletins),
            'system': len(self.system_board.bulletins),
            'social': len(self.social_board.bulletins),
            'total': sum([
                len(self.global_board.bulletins),
                len(self.market_board.bulletins),
                len(self.system_board.bulletins),
                len(self.social_board.bulletins)
            ])
        }

