"""
System - 主系统模块

职责: 协调所有模块，运行模拟
"""

from typing import Dict, List
from .capital_pool import CapitalPool
from .agent_manager import AgentManager
from .capital_manager import CapitalManager
from .market_analyzer import MarketAnalyzer


class PrometheusV3:
    """普罗米修斯系统 v3.0 - 带资金池"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 系统配置
        """
        self.config = config
        
        # 创建资金池
        self.capital_pool = CapitalPool(config['initial_capital'])
        
        # 创建管理器（传入资金池）
        self.agent_manager = AgentManager(config['agent_manager'], self.capital_pool)
        self.capital_manager = CapitalManager(config['capital_manager'], self.capital_pool)
        self.market_analyzer = MarketAnalyzer(config['market_analyzer'])
        
        # 初始化智能体（从资金池获取资金）
        if config['initial_agents'] > 0:
            self.agent_manager.initialize(
                num_agents=config['initial_agents'],
                capital_per_agent=config['initial_capital'] / config['initial_agents']
            )
        
        # 运行统计
        self.current_day = 0
    
    def add_capital(self, amount: float):
        """
        管理者追加资金
        
        Args:
            amount: 追加金额
        """
        self.capital_pool.deposit(amount, 'manager')
    
    def run_day(self, price_history: List[float], day: int):
        """
        运行一天
        
        Args:
            price_history: 价格历史
            day: 当前天数
        """
        if day == 0 or day >= len(price_history):
            return
        
        self.current_day = day
        
        # 1. 计算市场特征
        # 支持两种格式: list[float] 或 list[dict]
        if isinstance(price_history[day], dict):
            current_price = price_history[day]['price']
            prev_price = price_history[day-1]['price']
        else:
            current_price = price_history[day]
            prev_price = price_history[day-1]
        
        price_change = (current_price - prev_price) / prev_price
        market_features = self.market_analyzer.analyze(price_history, day)
        
        # 2. 更新所有智能体
        self.agent_manager.update_all(market_features, price_change)
        
        # 3. 检查死亡（资金自动返回资金池）
        self.agent_manager.check_death()
        
        # 4. 检查繁殖（可从资金池获取额外资金）
        self.agent_manager.check_reproduction()
        
        # 5. 资金重新分配（使用资金池）
        if self.capital_manager.enabled:
            if day % self.config['capital_manager']['reallocation_period'] == 0:
                self.capital_manager.reallocate(self.agent_manager.agents)
    
    def run(self, price_history: List[float], start_day: int = 1, end_day: int = None):
        """
        运行模拟
        
        Args:
            price_history: 价格历史
            start_day: 开始天数
            end_day: 结束天数（None表示到最后）
        """
        if end_day is None:
            end_day = len(price_history) - 1
        
        for day in range(start_day, end_day + 1):
            self.run_day(price_history, day)
    
    def get_report(self) -> Dict:
        """获取报告"""
        agent_report = self.agent_manager.get_report()
        pool_report = self.capital_pool.get_report()
        capital_manager_report = self.capital_manager.get_report()
        
        initial_capital = self.config['initial_capital']
        
        # 系统总资金 = 智能体资金 + 资金池余额
        system_total_capital = self.agent_manager.get_system_total_capital()
        system_roi = (system_total_capital - initial_capital) / initial_capital
        
        # 资金池利用率
        pool_utilization = self.capital_pool.get_utilization_rate(system_total_capital)
        
        return {
            'system': {
                'current_day': self.current_day,
                'system_roi': system_roi,
                'initial_capital': initial_capital,
                'final_capital': system_total_capital,
                'agent_capital': agent_report['total_capital'],
                'pool_capital': pool_report['balance'],
                'pool_utilization': pool_utilization,
            },
            'agent_manager': agent_report,
            'capital_pool': pool_report,
            'capital_manager': capital_manager_report,
        }
    
    def get_summary(self) -> str:
        """获取简要报告"""
        report = self.get_report()
        system = report['system']
        agents = report['agent_manager']
        pool = report['capital_pool']
        
        summary = f"""
=== Prometheus v3.0 Summary ===
Day: {system['current_day']}
System ROI: {system['system_roi']:.2%}
Initial Capital: ${system['initial_capital']:,.2f}
Final Capital: ${system['final_capital']:,.2f}

Agents: {agents['total_agents']} (Active: {agents['active_agents']}, Inactive: {agents['inactive_agents']})
Total Births: {agents['stats']['total_births']}
Total Deaths: {agents['stats']['total_deaths']} (ROI: {agents['stats']['roi_deaths']}, Inactive: {agents['stats']['inactive_deaths']})
Total Trades: {agents['stats']['total_trades']}

Capital Pool Balance: ${pool['balance']:,.2f}
Pool Utilization: {system['pool_utilization']:.1%}
Death Deposits: ${pool['stats']['death_deposits']:,.2f}
Manager Deposits: ${pool['stats']['manager_deposits']:,.2f}
Reproduction Withdrawals: ${pool['stats']['reproduction_withdrawals']:,.2f}
"""
        return summary.strip()
    
    def __repr__(self) -> str:
        return f"PrometheusV3(day={self.current_day}, agents={len(self.agent_manager.agents)})"

    def generate_report(self) -> Dict:
        """
        生成系统报告
        
        Returns:
            报告字典
        """
        active_agents = [a for a in self.agent_manager.agents if a.is_alive]
        
        # 计算总资金
        total_capital = sum(a.capital for a in active_agents) + self.capital_pool.balance
        
        # 计算系统ROI
        system_roi = (total_capital - self.config['initial_capital']) / self.config['initial_capital']
        
        return {
            'system_roi': system_roi,
            'initial_capital': self.config['initial_capital'],
            'final_capital': total_capital,
            'pool_balance': self.capital_pool.balance,
            'total_agents': len(self.agent_manager.agents),
            'active_agents': len(active_agents),
            'dead_agents': len(self.agent_manager.agents) - len(active_agents),
            'total_births': self.agent_manager.stats['total_births'],
            'total_deaths': self.agent_manager.stats['total_deaths'],
            'death_reasons': self.agent_manager.stats.get('death_reasons', {}).copy(),
            'agents': [
                {
                    'id': a.id,
                    'roi': a.roi,
                    'capital': a.capital,
                    'trades': a.trade_count,
                    'age': a.age,
                    'is_alive': a.is_alive,
                    'species': a.gene.generate_species_name()
                }
                for a in self.agent_manager.agents
            ]
        }
