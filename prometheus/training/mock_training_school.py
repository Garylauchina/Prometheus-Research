"""
MockTrainingSchool - Mock训练学校

功能：
  1. 使用真实历史K线数据
  2. 快速训练环境（简化交易执行）
  3. 集成ExperienceDB（经验积累）
  4. 智能创世（基于历史经验）
  5. 完整的训练→验证→报告流程

这是对测试接口的系统化封装，符合三大铁律：统一封装，统一调用
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import logging
import json

from prometheus.core.world_signature_simple import WorldSignatureSimple
from prometheus.core.experience_db import ExperienceDB
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5
from prometheus.core.capital_pool import CapitalPool
from prometheus.core.agent_v5 import AgentV5, AgentState
from prometheus.core.genome import GenomeVector
from prometheus.core.ledger_system import PublicLedger, AgentAccountSystem

logger = logging.getLogger(__name__)


class MockMarketExecutor:
    """
    Mock市场执行器（Phase 1：极简版）
    
    特点：
      - 100%成交
      - 无滑点
      - 只考虑手续费
    """
    
    FEE_RATE = 0.0005  # 0.05% taker
    
    def __init__(self, market_data: pd.DataFrame):
        self.market_data = market_data
        self.current_cycle = 0
    
    def get_current_price(self) -> float:
        """获取当前K线的收盘价"""
        return float(self.market_data.iloc[self.current_cycle]['close'])
    
    def get_current_kline(self) -> Dict:
        """获取当前K线"""
        kline = self.market_data.iloc[self.current_cycle]
        return {
            'open': float(kline['open']),
            'high': float(kline['high']),
            'low': float(kline['low']),
            'close': float(kline['close']),
            'volume': float(kline['volume']),
            'timestamp': kline['timestamp'] if 'timestamp' in kline else self.current_cycle
        }
    
    def execute_trade(self, agent: AgentV5, action: Dict) -> Dict:
        """
        执行交易（100%成交，无滑点）
        
        参数：
          - agent: Agent对象
          - action: {'type': 'buy'/'sell'/'close', 'amount': 0.1}
        
        返回：
          - {'success': True/False, 'price': 50000, 'amount': 0.1, 'fee': 25}
        """
        current_price = self.get_current_price()
        action_type = action.get('type')
        amount = action.get('amount', 0)
        
        if amount <= 0:
            return {'success': False, 'reason': 'invalid_amount'}
        
        fee = current_price * amount * self.FEE_RATE
        
        # 检查资金
        if action_type in ['buy', 'sell']:
            cost = current_price * amount + fee
            if agent.account.private_ledger.virtual_capital < cost:
                return {'success': False, 'reason': 'insufficient_capital'}
        
        # 执行交易（通过Agent的account）
        try:
            if action_type == 'buy':
                # 开多
                agent.account.record_trade(
                    trade_type='buy',
                    price=current_price,
                    amount=amount,
                    confidence=0.5
                )
                return {'success': True, 'price': current_price, 'amount': amount, 'fee': fee}
            
            elif action_type == 'sell':
                # 开空
                agent.account.record_trade(
                    trade_type='sell',
                    price=current_price,
                    amount=amount,
                    confidence=0.5
                )
                return {'success': True, 'price': current_price, 'amount': amount, 'fee': fee}
            
            elif action_type == 'close':
                # 平仓
                if abs(agent.account.private_ledger.long_position + agent.account.private_ledger.short_position) > 0:
                    close_type = 'cover' if agent.account.private_ledger.short_position < 0 else 'sell'
                    agent.account.record_trade(
                        trade_type=close_type,
                        price=current_price,
                        amount=abs(agent.account.private_ledger.long_position + agent.account.private_ledger.short_position),
                        confidence=0.5
                    )
                    return {'success': True, 'price': current_price, 'pnl': 0, 'fee': fee}
                else:
                    return {'success': False, 'reason': 'no_position'}
        
        except Exception as e:
            logger.error(f"交易执行失败: {e}")
            return {'success': False, 'reason': str(e)}
    
    def next_cycle(self):
        """进入下一个周期"""
        self.current_cycle += 1
        return self.current_cycle < len(self.market_data)


class MockTrainingSchool:
    """
    Mock训练学校
    
    提供完整的训练流程：
      1. 智能创世（基于ExperienceDB）
      2. 训练循环（Agent决策 + 进化）
      3. 结果记录（保存最佳基因）
      4. 验证测试（在测试集上验证）
      5. 报告生成（HTML报告）
    """
    
    def __init__(
        self,
        market_data: pd.DataFrame,
        config: Dict,
        experience_db: ExperienceDB
    ):
        """
        初始化Mock训练学校
        
        参数：
          - market_data: 市场K线数据
          - config: 配置字典
          - experience_db: 经验数据库
        """
        self.market_data = market_data
        self.config = config
        self.experience_db = experience_db
        
        # 组件
        self.executor = MockMarketExecutor(market_data)
        self.moirai = None
        self.evolution = None
        self.capital_pool = None
        
        # 训练状态
        self.agents: List[AgentV5] = []
        self.current_cycle = 0
        self.training_history = []
        
        logger.info(f"MockTrainingSchool初始化: {len(market_data)}根K线")
    
    def train(
        self,
        cycles: int = 1000,
        run_id: Optional[str] = None
    ) -> List[AgentV5]:
        """
        训练循环
        
        参数：
          - cycles: 训练周期数
          - run_id: 训练ID
        
        返回：
          - 最佳Agent列表
        """
        if run_id is None:
            run_id = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"=" * 80)
        logger.info(f"开始训练: {run_id}")
        logger.info(f"  周期数: {cycles}")
        logger.info(f"  Agent数: {self.config.get('agent_count', 50)}")
        logger.info(f"=" * 80)
        
        # 1. 创世
        self._genesis()
        
        # 2. 训练循环
        for cycle in range(min(cycles, len(self.market_data))):
            self.current_cycle = cycle
            self.executor.current_cycle = cycle
            
            # 运行一个周期
            self._run_cycle(cycle)
            
            # 进化
            if cycle > 0 and cycle % 10 == 0:
                self._evolve(cycle)
            
            # 日志
            if cycle % 100 == 0:
                self._log_progress(cycle)
        
        # 3. 计算最终结果
        self._calculate_final_metrics()
        
        # 4. 保存到ExperienceDB
        self._save_to_experience_db(run_id)
        
        # 5. 返回最佳Agent
        self.agents.sort(key=lambda a: getattr(a, 'roi', 0), reverse=True)
        return self.agents[:10]
    
    def _genesis(self):
        """创世"""
        logger.info("🌱 创世开始...")
        
        # 计算当前市场的WorldSignature
        current_ws = WorldSignatureSimple.from_market_data(self.market_data.head(100))
        logger.info(f"当前市场状态:\n{current_ws.to_human_readable()}")
        
        # 智能创世（基于ExperienceDB）
        genesis_strategy = self.config.get('genesis_strategy', 'adaptive')
        genomes_data = self.experience_db.smart_genesis(
            current_ws=current_ws,
            count=self.config.get('agent_count', 50),
            strategy=genesis_strategy
        )
        
        # 初始化资金池
        total_capital = self.config.get('total_capital', 100000)
        capital_per_agent = total_capital / len(genomes_data)
        
        self.capital_pool = CapitalPool()
        self.capital_pool.invest(amount=total_capital, source="genesis")
        
        # 创建Agent
        self.agents = []
        for i, genome_data in enumerate(genomes_data):
            # 创建Agent（先用随机genome）
            agent = AgentV5.create_genesis(
                agent_id=f"Agent{i:03d}",
                initial_capital=capital_per_agent,
                family_id=i % 10,  # 10个家族
                num_families=10,
                full_genome_unlock=True
            )
            
            # 根据genome_data类型设置genome
            if genome_data.get('random'):
                # 随机基因（已在create_genesis中创建）
                pass
            elif genome_data.get('mutated'):
                # 变异基因：加载历史基因并变异
                genome = GenomeVector.from_dict(genome_data)
                genome.mutate(mutation_rate=0.30)
                agent.genome = genome
            else:
                # 历史基因：直接加载
                genome = GenomeVector.from_dict(genome_data)
                agent.genome = genome
            
            self.agents.append(agent)
        
        # 初始化公共账簿（双账簿系统核心）
        self.public_ledger = PublicLedger()
        
        # 为每个Agent创建账户系统（标准流程！）
        logger.info(f"💰 为{len(self.agents)}个Agent初始化账户系统...")
        for agent in self.agents:
            account_system = AgentAccountSystem(
                agent_id=agent.agent_id,
                initial_capital=capital_per_agent,
                public_ledger=self.public_ledger
            )
            agent.account = account_system  # ✅ 挂载到Agent对象
        logger.info("✅ 账户系统初始化完成（双账簿系统）")
        
        # 初始化Moirai和EvolutionManager
        self.moirai = Moirai(capital_pool=self.capital_pool)
        self.moirai.agents = self.agents  # 手动设置agents
        
        self.evolution = EvolutionManagerV5(
            moirai=self.moirai,
            capital_pool=self.capital_pool
        )
        
        logger.info(f"✅ 创世完成: {len(self.agents)}个Agent")
    
    def _run_cycle(self, cycle: int):
        """运行一个周期"""
        kline = self.executor.get_current_kline()
        
        for agent in self.agents:
            if agent.state == AgentState.DEAD:
                continue
            
            # Agent决策（简化版，直接用genome参数）
            # TODO: 集成完整的Daimon决策
            action = self._simple_decide(agent, kline)
            
            # 执行交易
            if action:
                result = self.executor.execute_trade(agent, action)
                if result['success']:
                    # 记录已在execute_trade中完成
                    pass
    
    def _simple_decide(self, agent: AgentV5, kline: Dict) -> Optional[Dict]:
        """
        简单决策（占位符，未来集成Daimon）
        
        当前：基于随机+基因参数的简单策略
        """
        # 基于基因的简单决策
        # TODO: 集成Daimon
        
        # 随机决策（占位符）
        if np.random.random() < 0.01:  # 1%概率交易
            action_types = ['buy', 'sell', 'close']
            return {
                'type': np.random.choice(action_types),
                'amount': 0.1
            }
        return None
    
    def _evolve(self, cycle: int):
        """进化"""
        logger.info(f"  🧬 进化 (cycle {cycle})")
        
        # 调用EvolutionManager
        current_price = self.executor.get_current_price()
        self.evolution.run_evolution_cycle(
            current_price=current_price
        )
    
    def _log_progress(self, cycle: int):
        """记录进度"""
        alive_count = sum(1 for a in self.agents if a.state != AgentState.DEAD)
        avg_capital = np.mean([a.account.private_ledger.virtual_capital for a in self.agents if a.state != AgentState.DEAD])
        
        logger.info(
            f"Cycle {cycle:4d}: "
            f"Alive={alive_count:2d}, "
            f"Avg Capital=${avg_capital:,.0f}"
        )
    
    def _calculate_final_metrics(self):
        """计算最终指标"""
        logger.info("📊 计算最终指标...")
        
        current_price = self.executor.get_current_price()
        
        for agent in self.agents:
            # 计算ROI
            initial_capital = getattr(agent, 'initial_capital', 10000)
            final_capital = agent.account.private_ledger.virtual_capital
            unrealized_pnl = agent.calculate_unrealized_pnl(current_price)
            total_capital = final_capital + unrealized_pnl
            
            agent.roi = (total_capital / initial_capital - 1) if initial_capital > 0 else 0
            agent.sharpe = 0.0  # TODO: 计算夏普比率
            agent.max_drawdown = 0.0  # TODO: 计算最大回撤
            agent.trade_count = len(agent.account.private_ledger.trade_history)
    
    def _save_to_experience_db(self, run_id: str):
        """保存到ExperienceDB"""
        logger.info("💾 保存经验到数据库...")
        
        # 计算WorldSignature（训练期间的平均状态）
        ws = WorldSignatureSimple.from_market_data(self.market_data)
        
        # 保存最佳Agent
        market_type = self.config.get('market_type', 'unknown')
        self.experience_db.save_best_genomes(
            run_id=run_id,
            market_type=market_type,
            world_signature=ws,
            agents=sorted(self.agents, key=lambda a: getattr(a, 'roi', 0), reverse=True),
            top_k=10
        )
    
    def validate(
        self,
        agents: List[AgentV5],
        test_data: pd.DataFrame
    ) -> Dict:
        """
        验证Agent在测试集上的表现
        
        参数：
          - agents: Agent列表
          - test_data: 测试数据
        
        返回：
          - 验证结果字典
        """
        logger.info(f"🧪 验证测试: {len(agents)}个Agent, {len(test_data)}根K线")
        
        # TODO: 实现验证逻辑
        # 当前返回占位符
        return {
            'system_roi': 0.0,
            'agent_roi': [0.0] * len(agents)
        }
    
    def generate_report(
        self,
        run_id: str,
        btc_roi: float = 0.0
    ) -> str:
        """
        生成HTML报告
        
        参数：
          - run_id: 训练ID
          - btc_roi: BTC基准ROI
        
        返回：
          - HTML文件路径
        """
        # TODO: 实现报告生成
        logger.info(f"📄 生成报告: {run_id}")
        return f"reports/{run_id}.html"

