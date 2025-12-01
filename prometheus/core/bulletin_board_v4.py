"""
Prometheus v4.0 - 公告板系统（三层架构）

简化版设计：
- 只有三层：战略、市场、系统
- 只有Mastermind和Supervisor可以发布
- Agent只能阅读
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BulletinTier(Enum):
    """公告板层级（三层）"""
    STRATEGIC = "strategic"  # 战略层（Mastermind发布）
    MARKET = "market"        # 市场层（Supervisor发布）
    SYSTEM = "system"        # 系统层（Supervisor发布）


class Priority(Enum):
    """优先级"""
    URGENT = "urgent"      # 紧急
    HIGH = "high"          # 高
    NORMAL = "normal"      # 正常
    LOW = "low"            # 低


@dataclass
class Bulletin:
    """公告"""
    bulletin_id: str
    tier: BulletinTier
    title: str
    content: Dict[str, Any]  # 结构化内容
    publisher: str  # 'Mastermind' or 'Supervisor'
    priority: Priority
    timestamp: datetime
    expires: datetime
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    
    # 统计
    view_count: int = 0
    
    def is_expired(self) -> bool:
        """是否过期"""
        return datetime.now() > self.expires
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'bulletin_id': self.bulletin_id,
            'tier': self.tier.value,
            'title': self.title,
            'content': self.content,
            'publisher': self.publisher,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'expires': self.expires.isoformat(),
            'tags': self.tags,
            'view_count': self.view_count
        }


class BulletinBoardPermissions:
    """
    公告板权限管理
    
    严格控制：
    - Mastermind可发布战略公告
    - Supervisor可发布市场和系统公告
    - Agent只能阅读
    """
    
    ALLOWED_PUBLISHERS = ['Mastermind', 'Supervisor']
    
    TIER_PERMISSIONS = {
        'Mastermind': [BulletinTier.STRATEGIC],
        'Supervisor': [BulletinTier.MARKET, BulletinTier.SYSTEM]
    }
    
    @classmethod
    def can_publish(cls, publisher: str, tier: BulletinTier) -> bool:
        """
        检查是否有发布权限
        
        Args:
            publisher: 发布者
            tier: 公告层级
        
        Returns:
            bool: 是否有权限
        """
        if publisher not in cls.ALLOWED_PUBLISHERS:
            return False
        
        allowed_tiers = cls.TIER_PERMISSIONS.get(publisher, [])
        return tier in allowed_tiers


class BulletinBoardV4:
    """
    公告板系统 v4.0（简化版）
    
    特点：
    - 三层架构（战略/市场/系统）
    - 严格权限控制
    - Agent只读
    """
    
    def __init__(self, max_bulletins_per_tier: int = 50):
        """
        初始化公告板
        
        Args:
            max_bulletins_per_tier: 每层最大公告数
        """
        self.max_bulletins_per_tier = max_bulletins_per_tier
        
        # 三层公告板
        self.bulletins: Dict[BulletinTier, List[Bulletin]] = {
            BulletinTier.STRATEGIC: [],
            BulletinTier.MARKET: [],
            BulletinTier.SYSTEM: []
        }
        
        # 计数器
        self.bulletin_counter = 0
        
        # 统计
        self.total_posts = 0
        self.total_views = 0
        
        logger.info("公告板系统v4.0已初始化（三层架构 + 严格权限）")
    
    def post(self,
             tier: str,
             title: str,
             content: Dict[str, Any],
             publisher: str,
             priority: str = 'normal',
             tags: Optional[List[str]] = None,
             expires_hours: int = 24) -> Optional[Bulletin]:
        """
        发布公告
        
        Args:
            tier: 层级 ('strategic', 'market', 'system')
            title: 标题
            content: 内容（结构化数据）
            publisher: 发布者 ('Mastermind', 'Supervisor')
            priority: 优先级 ('urgent', 'high', 'normal', 'low')
            tags: 标签
            expires_hours: 过期时间（小时）
        
        Returns:
            Bulletin or None
        """
        # 转换枚举
        try:
            tier_enum = BulletinTier(tier)
            priority_enum = Priority(priority)
        except ValueError as e:
            logger.error(f"无效的参数: {e}")
            return None
        
        # 权限检查
        if not BulletinBoardPermissions.can_publish(publisher, tier_enum):
            logger.error(f"❌ {publisher} 无权在 {tier} 层发布公告")
            return None
        
        # 创建公告
        self.bulletin_counter += 1
        bulletin = Bulletin(
            bulletin_id=f"B{self.bulletin_counter:06d}",
            tier=tier_enum,
            title=title,
            content=content,
            publisher=publisher,
            priority=priority_enum,
            timestamp=datetime.now(),
            expires=datetime.now() + timedelta(hours=expires_hours),
            tags=tags or []
        )
        
        # 添加到对应层级
        self.bulletins[tier_enum].append(bulletin)
        
        # 限制数量（保留最新的）
        if len(self.bulletins[tier_enum]) > self.max_bulletins_per_tier:
            removed = self.bulletins[tier_enum].pop(0)
            logger.debug(f"移除旧公告: {removed.bulletin_id}")
        
        # 统计
        self.total_posts += 1
        
        logger.info(f"📢 [{tier_enum.value}] {publisher}发布: {title} (#{bulletin.bulletin_id})")
        return bulletin
    
    def read(self,
             agent_id: str,
             tier: Optional[str] = None,
             limit: int = 10,
             only_unread: bool = False) -> List[Bulletin]:
        """
        读取公告（Agent调用）
        
        Args:
            agent_id: Agent ID
            tier: 层级过滤（None = 所有层级）
            limit: 最大数量
            only_unread: 只读未读
        
        Returns:
            List[Bulletin]: 公告列表
        """
        bulletins = []
        
        # 确定要读取的层级
        if tier:
            try:
                tier_enum = BulletinTier(tier)
                tiers_to_read = [tier_enum]
            except ValueError:
                logger.error(f"无效的层级: {tier}")
                return []
        else:
            # 读取所有层级（按优先级：战略 > 系统 > 市场）
            tiers_to_read = [
                BulletinTier.STRATEGIC,
                BulletinTier.SYSTEM,
                BulletinTier.MARKET
            ]
        
        # 收集公告
        for tier_enum in tiers_to_read:
            for bulletin in reversed(self.bulletins[tier_enum]):  # 最新的在前
                if bulletin.is_expired():
                    continue
                bulletins.append(bulletin)
                
                # 统计阅读
                bulletin.view_count += 1
                self.total_views += 1
                
                if len(bulletins) >= limit:
                    break
            
            if len(bulletins) >= limit:
                break
        
        logger.debug(f"Agent {agent_id} 读取了 {len(bulletins)} 条公告")
        return bulletins[:limit]
    
    def get_latest(self, tier: str, count: int = 1) -> List[Bulletin]:
        """
        获取最新公告
        
        Args:
            tier: 层级
            count: 数量
        
        Returns:
            List[Bulletin]
        """
        try:
            tier_enum = BulletinTier(tier)
        except ValueError:
            return []
        
        valid_bulletins = [b for b in self.bulletins[tier_enum] if not b.is_expired()]
        return list(reversed(valid_bulletins))[:count]
    
    def get_by_priority(self, priority: str, tier: Optional[str] = None) -> List[Bulletin]:
        """
        按优先级获取公告
        
        Args:
            priority: 优先级
            tier: 层级（可选）
        
        Returns:
            List[Bulletin]
        """
        try:
            priority_enum = Priority(priority)
        except ValueError:
            return []
        
        # 确定层级
        if tier:
            try:
                tier_enum = BulletinTier(tier)
                tiers = [tier_enum]
            except ValueError:
                return []
        else:
            tiers = list(BulletinTier)
        
        # 收集
        results = []
        for tier_enum in tiers:
            for bulletin in self.bulletins[tier_enum]:
                if bulletin.priority == priority_enum and not bulletin.is_expired():
                    results.append(bulletin)
        
        return sorted(results, key=lambda b: b.timestamp, reverse=True)
    
    def cleanup_expired(self):
        """清理过期公告"""
        removed_count = 0
        for tier in BulletinTier:
            before = len(self.bulletins[tier])
            self.bulletins[tier] = [b for b in self.bulletins[tier] if not b.is_expired()]
            after = len(self.bulletins[tier])
            removed_count += (before - after)
        
        if removed_count > 0:
            logger.info(f"清理了 {removed_count} 条过期公告")
        
        return removed_count
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计数据
        """
        stats = {
            'total_posts': self.total_posts,
            'total_views': self.total_views,
            'by_tier': {}
        }
        
        for tier in BulletinTier:
            valid = [b for b in self.bulletins[tier] if not b.is_expired()]
            stats['by_tier'][tier.value] = {
                'count': len(valid),
                'total_views': sum(b.view_count for b in valid)
            }
        
        return stats
    
    def __repr__(self) -> str:
        return (f"BulletinBoardV4("
                f"strategic={len(self.bulletins[BulletinTier.STRATEGIC])}, "
                f"market={len(self.bulletins[BulletinTier.MARKET])}, "
                f"system={len(self.bulletins[BulletinTier.SYSTEM])})")


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    board = BulletinBoardV4()
    
    # Mastermind发布战略公告
    print("\n=== Mastermind发布战略公告 ===")
    board.post(
        tier='strategic',
        title='全局策略调整',
        content={
            'strategy': '保守',
            'reason': '市场波动加剧',
            'parameters': {'max_leverage': 2, 'max_position': 0.3}
        },
        publisher='Mastermind',
        priority='high'
    )
    
    # Supervisor发布市场公告
    print("\n=== Supervisor发布市场公告 ===")
    board.post(
        tier='market',
        title='市场技术指标',
        content={
            'RSI': 75,
            'ADX': 35,
            'trend': '强上升',
            'recommendation': '顺势做多'
        },
        publisher='Supervisor',
        priority='normal'
    )
    
    # Supervisor发布系统公告
    print("\n=== Supervisor发布系统公告 ===")
    board.post(
        tier='system',
        title='环境压力报告',
        content={
            'pressure': 0.65,
            'level': '高压力',
            'recommendation': '谨慎交易'
        },
        publisher='Supervisor',
        priority='high'
    )
    
    # Agent尝试发布（应该失败）
    print("\n=== Agent尝试发布（应该失败）===")
    board.post(
        tier='market',
        title='我的信号',
        content={'signal': 'buy'},
        publisher='Agent001',
        priority='normal'
    )
    
    # Agent读取公告
    print("\n=== Agent读取公告 ===")
    bulletins = board.read('Agent001', limit=5)
    for b in bulletins:
        print(f"[{b.tier.value}] {b.title} ({b.publisher}, {b.priority.value})")
    
    # 统计
    print("\n=== 统计信息 ===")
    stats = board.get_statistics()
    print(f"总发布: {stats['total_posts']}")
    print(f"总阅读: {stats['total_views']}")
    for tier, data in stats['by_tier'].items():
        print(f"  {tier}: {data['count']}条公告, {data['total_views']}次阅读")

