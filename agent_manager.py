"""
AgentManager - 智能体管理器模块

职责: 管理所有智能体的生命周期
"""

from typing import List, Dict
from .agent import Agent
from .gene import Gene
from .strategy import Strategy
from .capital_pool import CapitalPool


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, config: Dict, capital_pool: CapitalPool):
        """
        Args:
            config: 管理器配置
            capital_pool: 资金池
        """
        self.config = config
        self.capital_pool = capital_pool
        self.agents: List[Agent] = []
        self.next_agent_id = 1
        
        # 统计
        self.stats = {
            'total_births': 0,
            'total_deaths': 0,
            'roi_deaths': 0,
            'inactive_deaths': 0,
            'eliminations': 0,
            'blocked_reproductions': 0,
            'total_trades': 0
        }
    
    def initialize(self, num_agents: int, capital_per_agent: float):
        """
        初始化智能体（从资金池获取资金）
        
        Args:
            num_agents: 智能体数量
            capital_per_agent: 每个智能体的资金
        """
        total_needed = num_agents * capital_per_agent
        
        # 从资金池取出资金
        total_withdrawn = self.capital_pool.withdraw(total_needed, 'initialization')
        
        if total_withdrawn < total_needed:
            # 资金不足，调整每个智能体的资金
            capital_per_agent = total_withdrawn / num_agents
        
        for _ in range(num_agents):
            gene = Gene.random()
            strategy = Strategy(gene, self.config['strategy'])
            agent = Agent(
                agent_id=self.next_agent_id,
                gene=gene,
                initial_capital=capital_per_agent,
                strategy=strategy
            )
            self.agents.append(agent)
            self.next_agent_id += 1
            self.stats['total_births'] += 1
    
    def update_all(self, market_features: Dict[str, float], price_change: float):
        """
        更新所有智能体
        
        Args:
            market_features: 市场特征
            price_change: 价格变化率
        """
        for agent in self.agents:
            if agent.is_alive:
                agent.update(market_features, price_change)
        
        # 更新交易统计
        self.stats['total_trades'] = sum(a.trade_count for a in self.agents)
    
    def check_death(self) -> int:
        """
        检查并移除死亡智能体（资金返回资金池）
        
        Returns:
            死亡数量
        """
        to_remove = []
        
        for agent in self.agents:
            if agent.should_die(self.config['death']):
                agent.die()
                to_remove.append(agent)
                self.stats['total_deaths'] += 1
                
                # 统计死亡原因
                if agent.death_reason == 'low_roi':
                    self.stats['roi_deaths'] += 1
                elif agent.death_reason == 'inactive':
                    self.stats['inactive_deaths'] += 1
                
                # 将死亡智能体的资金返回资金池
                if agent.capital > 0:
                    self.capital_pool.deposit(agent.capital, 'death')
        
        for agent in to_remove:
            self.agents.remove(agent)
        
        return len(to_remove)
    
    def check_reproduction(self) -> int:
        """
        检查并执行繁殖（从资金池获取额外资金）
        
        Returns:
            新生数量
        """
        new_agents = []
        
        for agent in self.agents:
            if agent.can_reproduce(self.config['reproduction']):
                # 繁殖时可以从资金池获取额外资金
                child = agent.reproduce(
                    self.config['reproduction'],
                    self.capital_pool,
                    self.next_agent_id
                )
                new_agents.append(child)
                self.next_agent_id += 1
                self.stats['total_births'] += 1
            elif agent.roi > self.config['reproduction']['min_roi']:
                # ROI达标但交易次数不足
                if agent.trade_count < self.config['reproduction']['min_trades']:
                    self.stats['blocked_reproductions'] += 1
        
        self.agents.extend(new_agents)
        
        # 限制数量
        if len(self.agents) > self.config['max_agents']:
            # 淘汰最差的智能体，资金返回资金池
            self.agents.sort(key=lambda a: a.roi, reverse=True)
            eliminated = self.agents[self.config['max_agents']:]
            
            for agent in eliminated:
                if agent.capital > 0:
                    self.capital_pool.deposit(agent.capital, 'elimination')
                self.stats['eliminations'] += 1
            
            self.agents = self.agents[:self.config['max_agents']]
        
        return len(new_agents)
    
    def get_total_capital(self) -> float:
        """获取智能体持有的总资金（不包括资金池）"""
        return sum(a.capital for a in self.agents if a.is_alive)
    
    def get_system_total_capital(self) -> float:
        """获取系统总资金（智能体 + 资金池）"""
        return self.get_total_capital() + self.capital_pool.get_available_capital()
    
    def get_active_agents(self) -> List[Agent]:
        """获取活跃智能体（有交易的）"""
        return [a for a in self.agents if a.is_alive and a.trade_count > 0]
    
    def get_inactive_agents(self) -> List[Agent]:
        """获取不活跃智能体（没有交易的）"""
        return [a for a in self.agents if a.is_alive and a.trade_count == 0]
    
    def get_report(self) -> Dict:
        """获取报告"""
        active_agents = self.get_active_agents()
        inactive_agents = self.get_inactive_agents()
        
        return {
            'total_agents': len(self.agents),
            'active_agents': len(active_agents),
            'inactive_agents': len(inactive_agents),
            'total_capital': self.get_total_capital(),
            'stats': self.stats.copy(),
            'agents': [a.to_dict() for a in self.agents]
        }
    
    def __repr__(self) -> str:
        return f"AgentManager(agents={len(self.agents)}, active={len(self.get_active_agents())})"
