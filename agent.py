"""
Agent - 智能体模块

职责: 管理单个智能体的状态和行为
"""

from typing import Dict, Optional
from .gene import Gene
from .strategy import Strategy
from .capital_pool import CapitalPool


class Agent:
    """智能体 - 独立的交易实体"""
    
    def __init__(self, 
                 agent_id: int,
                 gene: Gene,
                 initial_capital: float,
                 strategy: Strategy):
        """
        Args:
            agent_id: 智能体ID
            gene: 基因
            initial_capital: 初始资金
            strategy: 策略
        """
        # 基本信息
        self.id = agent_id
        self.gene = gene
        self.strategy = strategy
        
        # 资金状态
        self.capital = initial_capital
        self.initial_capital = initial_capital
        
        # 仓位状态
        self.long_ratio = 0.0
        self.short_ratio = 0.0
        
        # 交易统计
        self.trade_count = 0
        self.age = 0  # 存活天数
        self.days_since_last_trade = 0
        
        # 性能指标
        self.roi = 0.0
        
        # 生命周期
        self.is_alive = True
        self.death_reason = None
    
    def update(self, market_features: Dict[str, float], price_change: float):
        """
        更新智能体状态
        
        Args:
            market_features: 市场特征
            price_change: 价格变化率
        """
        if not self.is_alive:
            return
        
        # 1. 计算盈亏
        long_pnl = self.capital * self.long_ratio * price_change
        short_pnl = self.capital * self.short_ratio * (-price_change)
        total_pnl = long_pnl + short_pnl
        
        self.capital += total_pnl
        
        # 2. 计算新仓位
        target_long, target_short = self.strategy.calculate_position(market_features)
        
        # 3. 计算交易金额和手续费
        trade_value = self.strategy.calculate_trade_value(
            self.long_ratio, self.short_ratio,
            target_long, target_short,
            self.capital
        )
        
        if trade_value > 0:
            # 发生了交易
            trading_cost = trade_value * 0.001  # Round 10: OKX 0.1%手续费 (taker)
            self.capital -= trading_cost
            
            self.trade_count += 1
            self.days_since_last_trade = 0
        else:
            self.days_since_last_trade += 1
        
        # 4. 更新仓位
        self.long_ratio = target_long
        self.short_ratio = target_short
        
        # 5. 更新ROI
        self.roi = (self.capital - self.initial_capital) / self.initial_capital
        
        # 6. 更新年龄
        self.age += 1
    
    def should_die(self, death_config: Dict) -> bool:
        """
        判断是否应该死亡
        
        Args:
            death_config: 死亡配置
        
        Returns:
            是否应该死亡
        """
        if not self.is_alive:
            return False
        
        # 条件1: ROI过低
        if self.roi < death_config['death_roi_threshold']:
            self.death_reason = 'low_roi'
            return True
        
        # 条件2: 长期不交易
        if self.days_since_last_trade >= death_config['max_inactive_days']:
            self.death_reason = 'inactive'
            return True
        
        return False
    
    def can_reproduce(self, reproduction_config: Dict) -> bool:
        """
        判断是否可以繁殖
        
        Args:
            reproduction_config: 繁殖配置
        
        Returns:
            是否可以繁殖
        """
        if not self.is_alive:
            return False
        
        # 条件1: ROI达标
        if self.roi < reproduction_config['min_roi']:
            return False
        
        # 条件2: 交易次数达标
        if self.trade_count < reproduction_config['min_trades']:
            return False
        
        # 条件3: 资金充足
        child_capital = self.capital * reproduction_config['child_capital_ratio']
        if child_capital < reproduction_config['min_child_capital']:
            return False
        
        return True
    
    def reproduce(self, 
                  reproduction_config: Dict,
                  capital_pool: Optional[CapitalPool] = None,
                  child_id: int = 0) -> 'Agent':
        """
        繁殖子代
        
        Args:
            reproduction_config: 繁殖配置
            capital_pool: 资金池（可选）
            child_id: 子代ID
        
        Returns:
            子代智能体
        """
        # 1. 从父代继承资金
        child_capital_from_parent = self.capital * reproduction_config['child_capital_ratio']
        self.capital -= child_capital_from_parent
        
        # 2. 从资金池获取额外资金（如果启用且可用）
        child_capital_from_pool = 0.0
        if (capital_pool and 
            reproduction_config.get('pool_capital_enabled', False) and
            reproduction_config.get('pool_capital_ratio', 0) > 0):
            
            requested_amount = child_capital_from_parent * reproduction_config['pool_capital_ratio']
            child_capital_from_pool = capital_pool.withdraw(requested_amount, 'reproduction')
        
        # 3. 子代总资金
        child_total_capital = child_capital_from_parent + child_capital_from_pool
        
        # 4. 更新父代初始资金（用于ROI计算）
        self.initial_capital = self.capital
        
        # 5. 创建变异基因
        child_gene = self.gene.mutate(reproduction_config['mutation_rate'])
        
        # 6. 创建子代策略
        child_strategy = Strategy(child_gene, self.strategy.config)
        
        # 7. 创建子代
        child = Agent(
            agent_id=child_id,
            gene=child_gene,
            initial_capital=child_total_capital,
            strategy=child_strategy
        )
        
        return child
    
    def die(self):
        """标记为死亡"""
        self.is_alive = False
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'id': self.id,
            'gene': self.gene.to_dict(),
            'capital': self.capital,
            'initial_capital': self.initial_capital,
            'long_ratio': self.long_ratio,
            'short_ratio': self.short_ratio,
            'trade_count': self.trade_count,
            'age': self.age,
            'days_since_last_trade': self.days_since_last_trade,
            'roi': self.roi,
            'is_alive': self.is_alive,
            'death_reason': self.death_reason,
            'species': self.gene.generate_species_name()
        }
    
    def __repr__(self) -> str:
        return (f"Agent(id={self.id}, species={self.gene.generate_species_name()}, "
                f"capital=${self.capital:.2f}, roi={self.roi:.2%})")
