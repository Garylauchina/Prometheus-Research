"""
多市场交易系统
"""

from .market import Market
from .multi_market_agent import MultiMarketAgent
from .agent_manager import AgentManager
from .capital_manager import CapitalManager
from .lifecycle_manager import LifecycleManager
from .config_multi_market import CONFIG_MULTI_MARKET, generate_multi_market_gene
import pandas as pd
from typing import Dict, List

class PrometheusV3MultiMarket:
    """Prometheus v3.0 多市场交易系统"""
    
    def __init__(self, config: dict = None):
        """
        初始化多市场系统
        
        Args:
            config: 配置字典，默认使用CONFIG_MULTI_MARKET
        """
        self.config = config or CONFIG_MULTI_MARKET
        
        # 创建市场
        self.spot_market = Market(**self.config['markets']['spot'])
        self.futures_market = Market(**self.config['markets']['futures'])
        
        # 创建资金管理器
        self.capital_manager = CapitalManager(
            self.config['initial_capital'],
            self.config['capital_manager']
        )
        
        # 创建智能体管理器（需要capital_pool）
        # 注意：AgentManager需要CapitalPool，但我们使用的是CapitalManager
        # 暂时创建一个简单的列表来管理agents
        self.agents = []
        self.next_agent_id = 1
        self.agent_stats = {
            'total_births': 0,
            'total_deaths': 0
        }
        self.lifecycle_manager = LifecycleManager(self.config['lifecycle'])
        
        # 初始化智能体
        self._initialize_agents()
        
        # 统计数据
        self.stats = {
            'total_days': 0,
            'total_trades': 0,
            'total_fees': 0.0,
            'spot_trades': 0,
            'futures_trades': 0,
            'spot_fees': 0.0,
            'futures_fees': 0.0
        }
        
    def _initialize_agents(self):
        """初始化智能体"""
        for i in range(self.config['initial_agents']):
            # 生成基因
            gene = generate_multi_market_gene()
            
            # 从资金池获取资金
            total_capital = self.capital_manager.allocate_capital()
            
            # 根据基因分配现货和期货资金
            spot_ratio = gene['market_allocation']['spot_ratio']
            spot_capital = total_capital * spot_ratio
            futures_capital = total_capital * (1 - spot_ratio)
            
            # 创建多市场智能体
            agent = MultiMarketAgent(
                agent_id=i,
                gene=gene,
                spot_market=self.spot_market,
                futures_market=self.futures_market,
                spot_capital=spot_capital,
                futures_capital=futures_capital
            )
            
            # 添加到管理器
            self.agent_manager.add_agent(agent)
    
    def run(self, data: pd.DataFrame) -> Dict:
        """
        运行回测
        
        Args:
            data: 价格数据DataFrame，需要包含'close'列
            
        Returns:
            回测结果字典
        """
        print(f"🚀 开始多市场回测...")
        print(f"📊 数据: {len(data)}天")
        print(f"💰 初始资金: ${self.config['initial_capital']:,.2f}")
        print(f"🏪 现货市场: {self.spot_market}")
        print(f"📈 期货市场: {self.futures_market}")
        print(f"🤖 初始智能体: {len(self.agent_manager.agents)}")
        print()
        
        for day in range(len(data)):
            price = data.iloc[day]['close']
            
            # 准备市场数据
            start_idx = max(0, day - 30)
            market_data = {
                'prices': data.iloc[start_idx:day+1]['close'].values,
                'volumes': data.iloc[start_idx:day+1].get('volume', 
                    pd.Series([0]*(day+1-start_idx))).values
            }
            
            # 更新所有智能体
            for agent in self.agent_manager.agents[:]:  # 复制列表避免迭代时修改
                if agent.is_alive:
                    agent.update(day, price, market_data)
            
            # 检查死亡
            self.agent_manager.check_deaths(day)
            
            # 检查繁殖
            new_agents = self.agent_manager.check_reproduction(day)
            for new_gene in new_agents:
                # 从资金池获取资金
                total_capital = self.capital_manager.allocate_capital()
                
                if total_capital > 0:
                    # 根据基因分配资金
                    spot_ratio = new_gene['market_allocation']['spot_ratio']
                    spot_capital = total_capital * spot_ratio
                    futures_capital = total_capital * (1 - spot_ratio)
                    
                    # 创建新智能体
                    agent = MultiMarketAgent(
                        agent_id=self.agent_manager.next_agent_id,
                        gene=new_gene,
                        spot_market=self.spot_market,
                        futures_market=self.futures_market,
                        spot_capital=spot_capital,
                        futures_capital=futures_capital
                    )
                    
                    self.agent_manager.add_agent(agent)
            
            # 回收死亡智能体的资金
            for agent in self.agent_manager.agents:
                if not agent.is_alive and agent.capital > 0:
                    self.capital_manager.return_capital(agent.capital)
                    agent.capital = 0
            
            # 生命周期管理
            self.lifecycle_manager.manage(
                self.agent_manager.agents,
                self.capital_manager,
                day
            )
            
            # 每100天打印进度
            if (day + 1) % 100 == 0:
                active_agents = len([a for a in self.agent_manager.agents if a.is_alive])
                system_roi = self.get_system_roi()
                print(f"Day {day+1}/{len(data)}: "
                      f"Active={active_agents}, "
                      f"ROI={system_roi:.2%}, "
                      f"Pool=${self.capital_manager.pool_balance:,.2f}")
        
        # 收集结果
        results = self._collect_results()
        
        print()
        print("=" * 80)
        print("🎉 回测完成!")
        print(f"📊 System ROI: {results['system_roi']:.2%}")
        print(f"💰 Final Capital: ${results['final_capital']:,.2f}")
        print(f"🤖 Active Agents: {results['active_agents']}")
        print(f"📈 Total Trades: {results['total_trades']:,}")
        print(f"💸 Total Fees: ${results['total_fees']:,.2f}")
        print("=" * 80)
        
        return results
    
    def get_system_roi(self) -> float:
        """计算系统总ROI"""
        total_capital = sum(a.capital for a in self.agent_manager.agents if a.is_alive)
        total_capital += self.capital_manager.pool_balance
        
        return (total_capital - self.config['initial_capital']) / self.config['initial_capital']
    
    def _collect_results(self) -> Dict:
        """收集回测结果"""
        active_agents = [a for a in self.agent_manager.agents if a.is_alive]
        
        # 计算总资本
        total_capital = sum(a.capital for a in active_agents)
        total_capital += self.capital_manager.pool_balance
        
        # 计算总交易和费用
        total_spot_trades = sum(a.spot_account.trades for a in self.agent_manager.agents)
        total_futures_trades = sum(a.futures_account.trades for a in self.agent_manager.agents)
        total_spot_fees = sum(a.spot_account.total_fees for a in self.agent_manager.agents)
        total_futures_fees = sum(a.futures_account.total_fees for a in self.agent_manager.agents)
        
        results = {
            'system_roi': self.get_system_roi(),
            'initial_capital': self.config['initial_capital'],
            'final_capital': total_capital,
            'active_agents': len(active_agents),
            'total_agents': len(self.agent_manager.agents),
            'total_trades': total_spot_trades + total_futures_trades,
            'total_fees': total_spot_fees + total_futures_fees,
            
            # 分市场统计
            'spot': {
                'trades': total_spot_trades,
                'fees': total_spot_fees,
                'fee_rate': self.spot_market.fee_rate
            },
            'futures': {
                'trades': total_futures_trades,
                'fees': total_futures_fees,
                'fee_rate': self.futures_market.fee_rate,
                'max_leverage': self.futures_market.leverage
            },
            
            # Agent管理器统计
            'agent_manager': {
                'stats': self.agent_manager.stats,
                'active_agents': len(active_agents),
                'pool_balance': self.capital_manager.pool_balance,
                'pool_utilization': self.capital_manager.get_utilization()
            },
            
            # 生命周期统计
            'lifecycle': self.lifecycle_manager.get_stats(),
            
            # Agent详情
            'agents': [a.get_account_summary() for a in active_agents]
        }
        
        return results
