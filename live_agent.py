"""
Prometheus v3.0 - Live Trading Agent

这是实盘交易的Agent实现，每个Agent代表一个独立的交易策略。
Agent拥有自己的"基因"（交易参数），通过遗传算法进化。

设计思路：
1. 每个Agent是一个独立的交易单元，拥有自己的资金和策略
2. Agent通过基因（gene）定义其交易行为（如做多阈值、止损比例等）
3. 表现好的Agent会繁殖（复制基因并轻微变异），表现差的会死亡
4. 通过自然选择，系统会自动筛选出适应当前市场的策略

作者: Manus AI
日期: 2025-11-29
"""

import logging
import time
from typing import Dict, Optional
import random

logger = logging.getLogger(__name__)


class LiveAgent:
    """实盘交易Agent"""
    
    def __init__(self, agent_id: str, initial_capital: float, config: dict, gene: Optional[dict] = None):
        """
        初始化
        
        Args:
            agent_id: Agent ID
            initial_capital: 初始资金
            config: 配置
            gene: 基因（可选，用于繁殖）
        """
        self.agent_id = agent_id
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.config = config
        
        # 基因（策略参数）
        if gene is None:
            self.gene = self._generate_random_gene()
        else:
            self.gene = gene
        
        # 生命周期
        self.is_alive = True
        self.death_reason = None
        self.birth_time = time.time()
        self.last_trade_time = time.time()
        
        # 交易统计
        self.trade_count = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_pnl = 0.0
        
        # 性能指标
        self.roi = 0.0
        self.capital_history = [initial_capital]
        self.roi_history = [0.0]
        
        # 当前持仓
        # 为什么用字典而不是列表？
        # - 因为需要快速查找特定交易对的持仓信息
        # - 字典的查找复杂度是O(1)，列表是O(n)
        self.positions = {}  # {symbol: {'side': 'long/short', 'size': float, 'entry_price': float}}
        
        # 待执行的交易信号
        # 由update()生成，由LiveTradingSystem执行
        self.pending_signals = []
        
        logger.info(f"Created {self.agent_id} with capital ${initial_capital:.2f}")
    
    def _generate_random_gene(self):
        """
        生成随机基因
        
        基因是Agent的DNA，决定了Agent的交易行为。
        每个基因参数都有一个范围，这些范围是经过多次实验调优后确定的。
        
        为什么这样设计？
        - long_threshold/short_threshold: 决定了Agent的激进程度，范围较宽以保证多样性
        - max_position: 防止单个Agent过度集中资金
        - stop_loss/take_profit: 平衡风险和收益
        - holding_period: 适应不同的交易风格（短线/中线）
        - risk_aversion: 影响Agent在不同市场状态下的表现
        
        Returns:
            dict: 基因字典
        """
        return {
            'long_threshold': random.uniform(0.05, 0.15),  # 降低50%
            'short_threshold': random.uniform(-0.15, -0.05),  # 降低50%
            'max_position': random.uniform(0.5, 1.0),
            'stop_loss': random.uniform(0.03, 0.08),
            'take_profit': random.uniform(0.05, 0.15),
            'holding_period': random.randint(300, 3600),  # 5分钟到60分钟
            'risk_aversion': random.uniform(0.5, 1.5)
        }
    
    def update(self, market_data: dict, regime: str):
        """
        更新Agent状态并生成交易信号
        
        这是Agent的“大脑”，每个更新周期（默认60秒）都会调用一次。
        
        工作流程：
        1. 更新持仓盈亏（基于最新市场价格）
        2. 生成交易信号（做多/做空/平仓）
        3. 信号会被存储在pending_signals中，等待LiveTradingSystem执行
        
        为什么不直接执行交易？
        - 需要系统层面的风控检查
        - 需要统一的订单管理
        - 需要处理API调用限制
        
        Args:
            market_data: 市场数据，包含价格、成交量等
            regime: 市场状态 (strong_bull/weak_bull/sideways/weak_bear/strong_bear)
        """
        if not self.is_alive:
            return
        
        # 更新持仓PnL
        self._update_positions_pnl(market_data)
        
        # 生成交易信号
        self.pending_signals = self._generate_signals(market_data, regime)
    
    def _update_positions_pnl(self, market_data: dict):
        """更新持仓盈亏"""
        total_unrealized_pnl = 0.0
        
        for symbol, pos in self.positions.items():
            # 获取当前价格
            if 'SWAP' in symbol:
                current_price = market_data['futures']['price']
            else:
                current_price = market_data['spot']['price']
            
            # 计算未实现盈亏
            if pos['side'] == 'long':
                pnl = (current_price - pos['entry_price']) * pos['size']
            else:
                pnl = (pos['entry_price'] - current_price) * pos['size']
            
            total_unrealized_pnl += pnl
        
        # 更新资金
        self.capital = self.initial_capital + self.total_pnl + total_unrealized_pnl
        self.roi = (self.capital - self.initial_capital) / self.initial_capital
        
        # 更新历史
        self.capital_history.append(self.capital)
        self.roi_history.append(self.roi)
    
    def _generate_signals(self, market_data: dict, regime: str):
        """
        生成交易信号
        
        Args:
            market_data: 市场数据
            regime: 市场状态
            
        Returns:
            交易信号列表
        """
        signals = []
        
        # 简化版信号生成：基于价格动量
        candles = market_data.get('candles', [])
        if len(candles) < 20:
            return signals
        
        # 计算短期和长期均线
        prices = [float(c[4]) for c in candles[-20:]]
        short_ma = sum(prices[-5:]) / 5
        long_ma = sum(prices[-20:]) / 20
        
        # 计算动量
        momentum = (short_ma - long_ma) / long_ma
        
        # 根据市场状态调整阈值
        regime_config = self.config['market_regime']['regimes'].get(regime, {'long': 0.5, 'short': 0.5})
        long_bias = regime_config['long']
        short_bias = regime_config['short']
        
        # 生成信号
        if momentum > self.gene['long_threshold'] * (2 - long_bias):
            # 做多信号
            signals.append({
                'action': 'open',
                'side': 'long',
                'symbol': self.config['markets']['spot']['symbol'],
                'market': 'spot',
                'strength': min(1.0, momentum * long_bias)
            })
        
        elif momentum < self.gene['short_threshold'] * (2 - short_bias):
            # 做空信号（只在合约市场）
            signals.append({
                'action': 'open',
                'side': 'short',
                'symbol': self.config['markets']['futures']['symbol'],
                'market': 'futures',
                'strength': min(1.0, abs(momentum) * short_bias)
            })
        
        # 检查止损/止盈
        for symbol, pos in list(self.positions.items()):
            if 'SWAP' in symbol:
                current_price = market_data['futures']['price']
            else:
                current_price = market_data['spot']['price']
            
            # 计算盈亏比例
            if pos['side'] == 'long':
                pnl_pct = (current_price - pos['entry_price']) / pos['entry_price']
            else:
                pnl_pct = (pos['entry_price'] - current_price) / pos['entry_price']
            
            # 止损
            if pnl_pct < -self.gene['stop_loss']:
                signals.append({
                    'action': 'close',
                    'symbol': symbol,
                    'reason': 'stop_loss'
                })
            
            # 止盈
            elif pnl_pct > self.gene['take_profit']:
                signals.append({
                    'action': 'close',
                    'symbol': symbol,
                    'reason': 'take_profit'
                })
        
        return signals
    
    def should_die(self):
        """判断是否应该死亡"""
        if not self.is_alive:
            return False
        
        # 检查ROI
        if self.roi < self.config['agent_manager']['death']['roi_threshold']:
            self.death_reason = f"ROI too low: {self.roi:.2%}"
            return True
        
        # 检查不活跃时间
        inactive_seconds = time.time() - self.last_trade_time
        max_inactive = self.config['agent_manager']['death']['max_inactive_days'] * 86400
        if inactive_seconds > max_inactive:
            self.death_reason = f"Inactive for {inactive_seconds/86400:.1f} days"
            return True
        
        return False
    
    def can_reproduce(self):
        """判断是否可以繁殖"""
        if not self.is_alive:
            return False
        
        # 检查ROI
        if self.roi < self.config['agent_manager']['reproduction']['min_roi']:
            return False
        
        # 检查交易次数
        if self.trade_count < self.config['agent_manager']['reproduction']['min_trades']:
            return False
        
        return True
    
    def reproduce(self, new_capital: float):
        """
        繁殖新agent
        
        Args:
            new_capital: 新agent的资金
            
        Returns:
            新的agent
        """
        # 变异基因
        new_gene = self._mutate_gene()
        
        # 创建新agent
        new_agent = LiveAgent(
            agent_id=f"{self.agent_id}_child_{int(time.time())}",
            initial_capital=new_capital,
            config=self.config,
            gene=new_gene
        )
        
        # 扣除繁殖成本
        cost = self.capital * self.config['agent_manager']['reproduction']['cost_ratio']
        self.capital -= cost
        self.total_pnl -= cost
        
        logger.info(f"{self.agent_id} reproduced -> {new_agent.agent_id}")
        
        return new_agent
    
    def _mutate_gene(self):
        """变异基因"""
        new_gene = self.gene.copy()
        
        # 随机变异一些参数
        mutation_rate = 0.1
        for key in new_gene:
            if random.random() < mutation_rate:
                if isinstance(new_gene[key], float):
                    # 浮点数：±20%变异
                    new_gene[key] *= random.uniform(0.8, 1.2)
                elif isinstance(new_gene[key], int):
                    # 整数：±20%变异
                    new_gene[key] = int(new_gene[key] * random.uniform(0.8, 1.2))
        
        return new_gene
    
    def __repr__(self):
        return (f"LiveAgent(id={self.agent_id}, capital=${self.capital:.2f}, "
                f"ROI={self.roi:.2%}, trades={self.trade_count})")
