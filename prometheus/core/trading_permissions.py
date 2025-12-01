"""
交易权限系统 - Prometheus v4.0

分级授权体系，根据Agent表现逐步开放交易品种和杠杆
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限等级"""
    NOVICE = "novice"               # 新手
    INTERMEDIATE = "intermediate"   # 中级
    ADVANCED = "advanced"           # 高级
    EXPERT = "expert"               # 专家
    MASTER = "master"               # 大师


class TradingProduct(Enum):
    """交易品种"""
    SPOT = "spot"                   # 现货
    MARGIN = "margin"               # 杠杆交易
    PERPETUAL = "perpetual"         # 永续合约
    FUTURES = "futures"             # 交割合约
    OPTIONS = "options"             # 期权


@dataclass
class PermissionConfig:
    """权限配置"""
    level: PermissionLevel
    allowed_products: List[TradingProduct]
    max_leverage: float
    max_position_ratio: float  # 单笔最大仓位比例
    description: str
    
    # 晋升条件
    min_days_alive: int = 0
    min_total_return: float = 0.0
    min_win_rate: float = 0.0
    min_score: int = 0


class TradingPermissionSystem:
    """
    交易权限系统
    
    职责：
    1. 定义各级权限配置
    2. 评估Agent表现
    3. 决定权限升降级
    4. 检查交易是否合规
    """
    
    def __init__(self):
        """初始化权限配置"""
        self.permissions = {
            PermissionLevel.NOVICE: PermissionConfig(
                level=PermissionLevel.NOVICE,
                allowed_products=[TradingProduct.SPOT],
                max_leverage=1.0,
                max_position_ratio=0.1,
                description="新手级：仅现货，无杠杆",
                min_days_alive=0,
                min_total_return=0.0,
                min_win_rate=0.0,
                min_score=0
            ),
            
            PermissionLevel.INTERMEDIATE: PermissionConfig(
                level=PermissionLevel.INTERMEDIATE,
                allowed_products=[TradingProduct.SPOT, TradingProduct.MARGIN],
                max_leverage=3.0,
                max_position_ratio=0.2,
                description="中级：现货+低杠杆",
                min_days_alive=7,
                min_total_return=0.05,
                min_win_rate=0.4,
                min_score=20
            ),
            
            PermissionLevel.ADVANCED: PermissionConfig(
                level=PermissionLevel.ADVANCED,
                allowed_products=[
                    TradingProduct.SPOT,
                    TradingProduct.MARGIN,
                    TradingProduct.PERPETUAL
                ],
                max_leverage=10.0,
                max_position_ratio=0.3,
                description="高级：含永续合约，中等杠杆",
                min_days_alive=14,
                min_total_return=0.15,
                min_win_rate=0.45,
                min_score=40
            ),
            
            PermissionLevel.EXPERT: PermissionConfig(
                level=PermissionLevel.EXPERT,
                allowed_products=[
                    TradingProduct.SPOT,
                    TradingProduct.MARGIN,
                    TradingProduct.PERPETUAL,
                    TradingProduct.FUTURES
                ],
                max_leverage=20.0,
                max_position_ratio=0.5,
                description="专家级：全合约，高杠杆",
                min_days_alive=30,
                min_total_return=0.30,
                min_win_rate=0.5,
                min_score=60
            ),
            
            PermissionLevel.MASTER: PermissionConfig(
                level=PermissionLevel.MASTER,
                allowed_products=[
                    TradingProduct.SPOT,
                    TradingProduct.MARGIN,
                    TradingProduct.PERPETUAL,
                    TradingProduct.FUTURES,
                    TradingProduct.OPTIONS
                ],
                max_leverage=50.0,
                max_position_ratio=0.7,
                description="大师级：全品种含期权",
                min_days_alive=60,
                min_total_return=0.50,
                min_win_rate=0.55,
                min_score=80
            )
        }
        
        logger.info("交易权限系统已初始化（5级）")
    
    def evaluate_agent_level(self, agent_stats: Dict) -> PermissionLevel:
        """
        评估Agent应该处于哪个权限级别
        
        Args:
            agent_stats: Agent统计数据
            
        Returns:
            PermissionLevel: 推荐的权限级别
        """
        score = self._calculate_performance_score(agent_stats)
        
        # 从高到低检查是否满足条件
        for level in [PermissionLevel.MASTER, PermissionLevel.EXPERT, 
                      PermissionLevel.ADVANCED, PermissionLevel.INTERMEDIATE]:
            
            config = self.permissions[level]
            
            if (agent_stats['days_alive'] >= config.min_days_alive and
                agent_stats['total_return'] >= config.min_total_return and
                agent_stats['win_rate'] >= config.min_win_rate and
                score >= config.min_score):
                
                return level
        
        # 默认新手级
        return PermissionLevel.NOVICE
    
    def _calculate_performance_score(self, agent_stats: Dict) -> int:
        """
        计算Agent综合表现分数（0-100）
        
        考虑因素：
        1. 存活时间（30分）
        2. 盈利能力（40分）
        3. 胜率（20分）
        4. 风险控制（10分）
        """
        score = 0
        
        # 1. 存活时间（最高30分）
        days_alive = min(agent_stats.get('days_alive', 0), 60)
        score += int(days_alive / 2)  # 60天 = 30分
        
        # 2. 盈利能力（最高40分）
        total_return = agent_stats.get('total_return', 0.0)
        if total_return >= 1.0:      # 100%+
            score += 40
        elif total_return >= 0.5:    # 50%+
            score += 35
        elif total_return >= 0.3:    # 30%+
            score += 30
        elif total_return >= 0.2:    # 20%+
            score += 25
        elif total_return >= 0.1:    # 10%+
            score += 20
        elif total_return >= 0.05:   # 5%+
            score += 10
        elif total_return > 0:
            score += 5
        
        # 3. 胜率（最高20分）
        win_rate = agent_stats.get('win_rate', 0.0)
        if win_rate >= 0.6:
            score += 20
        elif win_rate >= 0.55:
            score += 18
        elif win_rate >= 0.5:
            score += 15
        elif win_rate >= 0.45:
            score += 12
        elif win_rate >= 0.4:
            score += 10
        elif win_rate >= 0.35:
            score += 5
        
        # 4. 风险控制（最高10分）
        max_drawdown = agent_stats.get('max_drawdown', 1.0)
        if max_drawdown <= 0.05:      # 5%以内
            score += 10
        elif max_drawdown <= 0.10:    # 10%以内
            score += 8
        elif max_drawdown <= 0.15:    # 15%以内
            score += 6
        elif max_drawdown <= 0.20:    # 20%以内
            score += 4
        elif max_drawdown <= 0.30:    # 30%以内
            score += 2
        
        return min(score, 100)
    
    def can_use_product(self, level: PermissionLevel, product: TradingProduct) -> bool:
        """
        检查某级别是否可以使用某个交易品种
        
        Args:
            level: 权限级别
            product: 交易品种
            
        Returns:
            bool: 是否允许
        """
        config = self.permissions[level]
        return product in config.allowed_products
    
    def get_max_leverage(self, level: PermissionLevel) -> float:
        """
        获取某级别允许的最大杠杆
        
        Args:
            level: 权限级别
            
        Returns:
            float: 最大杠杆倍数
        """
        return self.permissions[level].max_leverage
    
    def get_max_position_ratio(self, level: PermissionLevel) -> float:
        """
        获取某级别允许的最大仓位比例
        
        Args:
            level: 权限级别
            
        Returns:
            float: 最大仓位比例
        """
        return self.permissions[level].max_position_ratio
    
    def check_trade_permission(self, 
                               level: PermissionLevel,
                               product: TradingProduct,
                               leverage: float,
                               position_ratio: float) -> Tuple[bool, str]:
        """
        检查交易是否符合权限要求
        
        Args:
            level: Agent权限级别
            product: 交易品种
            leverage: 杠杆倍数
            position_ratio: 仓位比例
            
        Returns:
            Tuple[bool, str]: (是否允许, 原因)
        """
        config = self.permissions[level]
        
        # 检查交易品种
        if product not in config.allowed_products:
            return False, f"权限不足：{level.value}级不允许交易{product.value}"
        
        # 检查杠杆
        if leverage > config.max_leverage:
            return False, f"杠杆过高：最大{config.max_leverage}x，请求{leverage}x"
        
        # 检查仓位
        if position_ratio > config.max_position_ratio:
            return False, f"仓位过大：最大{config.max_position_ratio*100}%，请求{position_ratio*100}%"
        
        return True, "通过"
    
    def get_inherited_level(self, parent_level: PermissionLevel) -> PermissionLevel:
        """
        计算子代继承的权限级别
        
        规则：继承父母级别，但降一级（需要自己证明）
        
        Args:
            parent_level: 父代权限级别
            
        Returns:
            PermissionLevel: 子代初始权限级别
        """
        level_order = [
            PermissionLevel.NOVICE,
            PermissionLevel.INTERMEDIATE,
            PermissionLevel.ADVANCED,
            PermissionLevel.EXPERT,
            PermissionLevel.MASTER
        ]
        
        if parent_level == PermissionLevel.NOVICE:
            return PermissionLevel.NOVICE
        
        parent_idx = level_order.index(parent_level)
        child_idx = max(0, parent_idx - 1)
        
        return level_order[child_idx]
    
    def get_upgrade_bonus(self, old_level: PermissionLevel, new_level: PermissionLevel) -> float:
        """
        计算升级奖励（资金奖励比例）
        
        Args:
            old_level: 旧级别
            new_level: 新级别
            
        Returns:
            float: 奖励比例（0.0-1.0）
        """
        level_order = [
            PermissionLevel.NOVICE,
            PermissionLevel.INTERMEDIATE,
            PermissionLevel.ADVANCED,
            PermissionLevel.EXPERT,
            PermissionLevel.MASTER
        ]
        
        old_idx = level_order.index(old_level)
        new_idx = level_order.index(new_level)
        
        if new_idx > old_idx:  # 升级
            # 升级越高，奖励越多
            upgrade_levels = new_idx - old_idx
            bonus = 0.1 * upgrade_levels  # 每级10%
            return bonus
        else:
            return 0.0
    
    def get_level_statistics(self, agents: List) -> Dict:
        """
        统计各级别Agent数量
        
        Args:
            agents: Agent列表
            
        Returns:
            Dict: 统计结果
        """
        stats = {level: 0 for level in PermissionLevel}
        
        for agent in agents:
            if hasattr(agent, 'permission_level'):
                stats[agent.permission_level] += 1
        
        total = sum(stats.values())
        
        return {
            'counts': stats,
            'total': total,
            'distribution': {
                level: count / total if total > 0 else 0
                for level, count in stats.items()
            }
        }


class RiskController:
    """
    风险控制器
    
    即使Agent有权限，也需要通过风控检查
    """
    
    def __init__(self):
        """初始化风控参数"""
        self.max_single_loss_ratio = 0.3      # 单笔最大亏损30%
        self.max_total_exposure_ratio = 3.0   # 总杠杆暴露不超过3倍资金
        self.min_option_seller_capital = 50000  # 期权卖方最小资金
        self.high_volatility_threshold = 0.1   # 高波动阈值
        self.high_volatility_max_leverage = 5  # 高波动时最大杠杆
        
        logger.info("风险控制器已初始化")
    
    def check_trade_risk(self, agent, trade_signal: Dict, market_data: Dict) -> Tuple[bool, str]:
        """
        检查交易风险
        
        Args:
            agent: Agent实例
            trade_signal: 交易信号
            market_data: 市场数据
            
        Returns:
            Tuple[bool, str]: (是否通过, 原因)
        """
        # 1. 单笔最大亏损检查
        position_size = trade_signal.get('position_size', 0)
        leverage = trade_signal.get('leverage', 1.0)
        potential_loss = position_size * leverage
        
        if potential_loss > self.max_single_loss_ratio:
            return False, f"单笔风险过大：{potential_loss*100:.1f}% > {self.max_single_loss_ratio*100}%"
        
        # 2. 总杠杆暴露检查
        current_exposure = self._calculate_total_exposure(agent)
        new_exposure = current_exposure + position_size * leverage
        
        if new_exposure > self.max_total_exposure_ratio:
            return False, f"总杠杆暴露过大：{new_exposure:.1f}x > {self.max_total_exposure_ratio}x"
        
        # 3. 期权卖方资金检查
        product = trade_signal.get('product')
        if product == TradingProduct.OPTIONS and trade_signal.get('side') == 'SELL':
            if agent.current_capital < self.min_option_seller_capital:
                return False, f"期权卖方需要至少 {self.min_option_seller_capital} 资金"
        
        # 4. 市场极端情况检查
        volatility = market_data.get('volatility', 0.03)
        if volatility > self.high_volatility_threshold:
            if leverage > self.high_volatility_max_leverage:
                return False, f"市场波动过大({volatility*100:.1f}%)，限制杠杆至{self.high_volatility_max_leverage}x"
        
        return True, "通过风控"
    
    def _calculate_total_exposure(self, agent) -> float:
        """
        计算Agent的总杠杆暴露
        
        Args:
            agent: Agent实例
            
        Returns:
            float: 总暴露倍数
        """
        if not hasattr(agent, 'positions') or not agent.positions:
            return 0.0
        
        total_exposure = 0.0
        for position in agent.positions.values():
            size = position.get('size', 0)
            leverage = position.get('leverage', 1.0)
            total_exposure += size * leverage
        
        return total_exposure / max(agent.current_capital, 1.0)

