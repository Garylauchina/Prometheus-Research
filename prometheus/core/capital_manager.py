"""
CapitalManager - 资金管理器模块

职责: 负责动态资金分配
"""

from typing import List, Dict
from .agent import Agent
from .capital_pool import CapitalPool


class CapitalManager:
    """资金管理器 - 负责动态资金分配"""
    
    def __init__(self, config: Dict, capital_pool: CapitalPool):
        """
        Args:
            config: 资金管理配置
            capital_pool: 资金池
        """
        self.config = config
        self.capital_pool = capital_pool
        self.enabled = config.get('enabled', False)
        self.stats = {
            'reallocations': 0
        }
    
    def reallocate(self, agents: List[Agent]):
        """
        重新分配资金（使用资金池）
        
        策略:
        1. 收集所有智能体的资金到资金池
        2. 根据得分重新分配
        3. 优秀智能体获得更多资金
        4. 剩余资金留在资金池
        
        Args:
            agents: 智能体列表
        """
        if not self.enabled or not agents:
            return
        
        # 1. 收集所有资金到资金池
        total_agent_capital = 0.0
        for agent in agents:
            if agent.is_alive:
                total_agent_capital += agent.capital
                agent.capital = 0.0
        
        # 暂时存入资金池
        self.capital_pool.deposit(total_agent_capital, 'other')
        
        # 2. 计算每个智能体的得分
        scores = []
        for agent in agents:
            if not agent.is_alive:
                continue
            
            # 得分 = ROI权重 + 交易频率权重
            roi_score = max(0, agent.roi) * self.config['roi_weight']
            
            if agent.age > 0:
                trade_frequency = agent.trade_count / agent.age
                freq_score = min(1.0, trade_frequency * 10) * self.config['frequency_weight']
            else:
                freq_score = 0
            
            total_score = roi_score + freq_score
            scores.append((agent, total_score))
        
        if not scores:
            return
        
        # 3. 计算总得分
        total_score = sum(s[1] for s in scores)
        
        if total_score == 0:
            # 如果所有得分都是0，平均分配
            equal_share = total_agent_capital / len(scores)
            for agent, _ in scores:
                amount = self.capital_pool.withdraw(equal_share, 'reallocation')
                agent.capital = amount
                agent.initial_capital = amount
            return
        
        # 4. 根据得分从资金池分配资金
        min_capital = total_agent_capital * self.config['min_capital_ratio']
        
        for agent, score in scores:
            # 分配金额 = 总资金 × (得分 / 总得分)
            allocated_amount = max(min_capital, total_agent_capital * (score / total_score))
            
            # 从资金池取出
            actual_amount = self.capital_pool.withdraw(allocated_amount, 'reallocation')
            
            agent.capital = actual_amount
            agent.initial_capital = actual_amount  # 更新初始资金用于ROI计算
        
        self.stats['reallocations'] += 1
        
        # 注意: 如果资金池中还有剩余（由于min_capital限制），会留在资金池中
    
    def get_report(self) -> Dict:
        """获取报告"""
        return {
            'enabled': self.enabled,
            'stats': self.stats.copy()
        }
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"CapitalManager({status}, reallocations={self.stats['reallocations']})"
