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
import numpy as np

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
        
        logger.info(f"创建 {self.agent_id} 代理，初始资金 ${initial_capital:.2f}")
    
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
        
        # 检查是否有足够的K线数据
        candles = market_data.get('candles', [])
        if len(candles) < 100:  # 增加所需的K线数量，以支持更多技术指标计算
            return signals
        
        # 提取价格数据
        close_prices = np.array([float(c[4]) for c in candles[-100:]])
        high_prices = np.array([float(c[2]) for c in candles[-100:]])
        low_prices = np.array([float(c[3]) for c in candles[-100:]])
        
        # 计算技术指标
        # 1. 均线动量
        short_ma = np.mean(close_prices[-5:])
        long_ma = np.mean(close_prices[-20:])
        momentum = (short_ma - long_ma) / long_ma
        
        # 2. RSI (Relative Strength Index)
        delta = np.diff(close_prices)
        # 计算gain和loss
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        # 使用简单移动平均计算RSI
        avg_gain = np.mean(gain[-14:])
        avg_loss = np.mean(loss[-14:])
        
        # 处理可能的空值
        if np.isnan(avg_gain) or np.isnan(avg_loss) or avg_loss == 0:
            rsi = 50  # 默认值
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 3. MACD (Moving Average Convergence Divergence)
        # 使用numpy实现指数加权移动平均
        def exponential_moving_average(data, span):
            alpha = 2 / (span + 1)
            weights = (1 - alpha) ** np.arange(len(data)-1, -1, -1)
            weights /= weights.sum()
            return np.dot(data, weights)
        
        # 计算MACD
        prices_needed = max(12, 26)
        recent_prices = close_prices[-prices_needed:]
        
        ema12 = exponential_moving_average(recent_prices, 12)
        ema26 = exponential_moving_average(recent_prices, 26)
        macd_line = ema12 - ema26
        
        # 简化版MACD柱状图计算
        # 使用最后5个MACD值计算信号线
        if len(close_prices) > 34:  # 确保有足够的数据计算信号线
            macd_values = [exponential_moving_average(close_prices[-i-26:-i], 12) - 
                          exponential_moving_average(close_prices[-i-26:-i], 26) 
                          for i in range(5)]
            signal_line = exponential_moving_average(np.array(macd_values), 9)
            macd_hist = macd_line - signal_line
        else:
            macd_hist = macd_line  # 简化处理
        
        # 4. Bollinger Bands
        sma20 = np.mean(close_prices[-20:])
        std20 = np.std(close_prices[-20:])
        upper_band = sma20 + (2 * std20)
        lower_band = sma20 - (2 * std20)
        bb_width = (upper_band - lower_band) / sma20
        bb_position = (close_prices[-1] - lower_band) / bb_width
        
        # 根据市场状态调整阈值
        regime_config = self.config['market_regime']['regimes'].get(regime, {'long': 0.5, 'short': 0.5})
        long_bias = regime_config['long']
        short_bias = regime_config['short']
        
        # 综合信号计算
        final_signal_strength = 0.0
        signal_components = []
        
        # 动量信号
        if momentum > self.gene['long_threshold'] * (2 - long_bias):
            signal_components.append(momentum * long_bias)
        elif momentum < self.gene['short_threshold'] * (2 - short_bias):
            signal_components.append(momentum * short_bias)
        
        # RSI信号 (超买超卖)
        if rsi < 30:  # 超卖
            signal_components.append(0.2 * (30 - rsi) / 30)
        elif rsi > 70:  # 超买
            signal_components.append(-0.2 * (rsi - 70) / 30)
        
        # MACD信号
        signal_components.append(0.2 * macd_hist / (sma20 * 0.01) if macd_hist != 0 else 0)
        
        # Bollinger Bands信号
        if bb_position < 0.3:  # 接近下轨
            signal_components.append(0.2 * (0.3 - bb_position) / 0.3)
        elif bb_position > 0.7:  # 接近上轨
            signal_components.append(-0.2 * (bb_position - 0.7) / 0.3)
        
        # 计算最终信号强度
        if signal_components:
            final_signal_strength = np.mean(signal_components)
        
        # 生成交易信号
        if final_signal_strength > 0.15:  # 提高做多阈值的稳定性
            # 做多信号
            signals.append({
                'action': 'open',
                'side': 'long',
                'symbol': self.config['markets']['spot']['symbol'],
                'market': 'spot',
                'strength': min(1.0, final_signal_strength * long_bias),
                'indicators': {
                    'momentum': momentum,
                    'rsi': rsi,
                    'macd_hist': macd_hist,
                    'bb_position': bb_position
                }
            })
        
        elif final_signal_strength < -0.15:  # 提高做空阈值的稳定性
            # 做空信号（只在合约市场）
            signals.append({
                'action': 'open',
                'side': 'short',
                'symbol': self.config['markets']['futures']['symbol'],
                'market': 'futures',
                'strength': min(1.0, abs(final_signal_strength) * short_bias),
                'indicators': {
                    'momentum': momentum,
                    'rsi': rsi,
                    'macd_hist': macd_hist,
                    'bb_position': bb_position
                }
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
        """
        高级基因变异机制
        
        特性：
        1. 自适应变异率：根据ROI和年龄调整变异强度
        2. 精英保护：表现好的参数变异率降低
        3. 增强参数相关性：更复杂的参数关联调整
        4. 多样性保护：避免过早收敛到局部最优
        5. 策略风格一致性：确保参数组合形成连贯的交易风格
        """
        import numpy as np
        
        new_gene = self.gene.copy()
        
        # 参数范围约束
        param_ranges = {
            'long_threshold': (0.01, 0.3),
            'short_threshold': (-0.3, -0.01),
            'max_position': (0.1, 1.0),
            'stop_loss': (0.01, 0.15),
            'take_profit': (0.02, 0.3),
            'holding_period': (60, 7200),  # 1分钟到2小时
            'risk_aversion': (0.1, 3.0),
            'rsi_oversold': (20, 40),     # 新增RSI参数范围
            'rsi_overbought': (60, 80),   # 新增RSI参数范围
            'macd_signal_length': (9, 21), # 新增MACD参数范围
            'bb_std_dev': (1.5, 3.0)      # 新增布林带参数范围
        }
        
        # 确保所有参数都在范围内
        for key in new_gene:
            if key in param_ranges:
                if isinstance(new_gene[key], (int, float)):
                    new_gene[key] = max(param_ranges[key][0], min(param_ranges[key][1], new_gene[key]))
        
        # 1. 计算自适应变异率
        # 基于ROI的变异率调整：表现越好，变异率越低
        roi_factor = max(0.5, min(1.5, 1.0 - self.roi * 5))  # ROI越高，变异率越低
        
        # 基于交易次数的经验调整
        experience_factor = max(0.8, min(1.2, 1.0 + (self.trade_count / 1000) * 0.2))
        
        # 基础变异率
        base_mutation_rate = 0.25
        mutation_rate = base_mutation_rate * roi_factor * experience_factor
        
        # 2. 为每个参数设置变异概率和强度
        # 表现好的参数变异率降低（精英保护）
        param_weights = {
            'long_threshold': max(0.7, min(1.3, 1.0 + (self.roi * 2) if self.roi > 0 else 1.0)),
            'short_threshold': max(0.7, min(1.3, 1.0 + (self.roi * 2) if self.roi > 0 else 1.0)),
            'stop_loss': max(0.8, min(1.2, 1.0 + (self.roi * 1) if self.roi > 0 else 1.0)),
            'take_profit': max(0.8, min(1.2, 1.0 + (self.roi * 1) if self.roi > 0 else 1.0)),
            'max_position': max(0.8, min(1.2, 1.0 + (self.roi * 1) if self.roi > 0 else 1.0)),
            'holding_period': max(0.9, min(1.1, 1.0 + (self.roi * 0.5) if self.roi > 0 else 1.0)),
            'risk_aversion': max(0.9, min(1.1, 1.0 + (self.roi * 0.5) if self.roi > 0 else 1.0))
        }
        
        # 3. 执行参数变异
        for key in new_gene:
            # 个性化变异概率
            p = mutation_rate * param_weights.get(key, 1.0)
            
            if random.random() < p:
                # 变异强度根据参数重要性调整
                if isinstance(new_gene[key], float):
                    # 动态调整变异强度
                    if key in ['long_threshold', 'short_threshold']:
                        # 阈值参数使用较小的变异强度
                        std_dev = abs(new_gene[key] * 0.08) or 0.01
                    elif key in ['stop_loss', 'take_profit']:
                        # 风险参数使用中等变异强度
                        std_dev = abs(new_gene[key] * 0.12) or 0.01
                    else:
                        # 其他参数使用默认变异强度
                        std_dev = abs(new_gene[key] * 0.10) or 0.01
                        
                    # 应用变异
                    mutation = np.random.normal(0, std_dev)
                    new_value = new_gene[key] + mutation
                    
                    # 确保在有效范围内
                    if key in param_ranges:
                        new_value = max(param_ranges[key][0], min(param_ranges[key][1], new_value))
                    
                    new_gene[key] = new_value
                
                elif isinstance(new_gene[key], int):
                    # 整数参数的变异
                    std_dev = max(1, int(new_gene[key] * 0.1))
                    mutation = np.random.normal(0, std_dev)
                    new_value = int(new_gene[key] + mutation)
                    
                    if key in param_ranges:
                        new_value = max(int(param_ranges[key][0]), min(int(param_ranges[key][1]), new_value))
                    
                    new_gene[key] = new_value
        
        # 4. 增强的参数相关性调整
        
        # a. 风险偏好一致性：止损、止盈、仓位大小的协调
        if random.random() < 0.3:  # 增加调整概率
            risk_profile = random.choice(['conservative', 'balanced', 'aggressive'])  # 随机选择风险偏好
            
            if risk_profile == 'conservative':
                # 保守型：小止损、小止盈、小仓位
                scale_factor = random.uniform(0.8, 0.95)
                new_gene['stop_loss'] = max(param_ranges['stop_loss'][0], new_gene['stop_loss'] * scale_factor)
                new_gene['take_profit'] = max(param_ranges['take_profit'][0], new_gene['take_profit'] * scale_factor)
                new_gene['max_position'] = max(param_ranges['max_position'][0], new_gene['max_position'] * scale_factor)
                new_gene['risk_aversion'] = min(param_ranges['risk_aversion'][1], new_gene['risk_aversion'] * 1.1)
                
            elif risk_profile == 'aggressive':
                # 激进型：大止损、大止盈、大仓位
                scale_factor = random.uniform(1.05, 1.2)
                new_gene['stop_loss'] = min(param_ranges['stop_loss'][1], new_gene['stop_loss'] * scale_factor)
                new_gene['take_profit'] = min(param_ranges['take_profit'][1], new_gene['take_profit'] * scale_factor)
                new_gene['max_position'] = min(param_ranges['max_position'][1], new_gene['max_position'] * scale_factor)
                new_gene['risk_aversion'] = max(param_ranges['risk_aversion'][0], new_gene['risk_aversion'] * 0.9)
        
        # b. 交易频率与持仓周期的协调
        if random.random() < 0.25:
            if random.random() < 0.5:
                # 高频交易：小阈值、短持仓周期
                new_gene['long_threshold'] = min(param_ranges['long_threshold'][1], 
                                               new_gene['long_threshold'] * random.uniform(0.8, 0.95))
                new_gene['short_threshold'] = max(param_ranges['short_threshold'][0], 
                                                new_gene['short_threshold'] * random.uniform(1.05, 1.2))
                new_gene['holding_period'] = max(param_ranges['holding_period'][0], 
                                               int(new_gene['holding_period'] * random.uniform(0.7, 0.9)))
            else:
                # 低频交易：大阈值、长持仓周期
                new_gene['long_threshold'] = max(param_ranges['long_threshold'][0], 
                                               new_gene['long_threshold'] * random.uniform(1.05, 1.2))
                new_gene['short_threshold'] = min(param_ranges['short_threshold'][1], 
                                                new_gene['short_threshold'] * random.uniform(0.8, 0.95))
                new_gene['holding_period'] = min(param_ranges['holding_period'][1], 
                                               int(new_gene['holding_period'] * random.uniform(1.1, 1.3)))
        
        # c. 风险规避与技术指标敏感度的协调
        if random.random() < 0.2:
            # 高风险规避的Agent应该使用更保守的技术指标参数
            if new_gene['risk_aversion'] > 1.5:  # 高风险规避
                # 更保守的RSI设置
                if 'rsi_oversold' in new_gene:
                    new_gene['rsi_oversold'] = min(param_ranges['rsi_oversold'][1], 
                                                 new_gene['rsi_oversold'] * random.uniform(1.05, 1.15))
                if 'rsi_overbought' in new_gene:
                    new_gene['rsi_overbought'] = max(param_ranges['rsi_overbought'][0], 
                                                   new_gene['rsi_overbought'] * random.uniform(0.85, 0.95))
                # 更宽的布林带
                if 'bb_std_dev' in new_gene:
                    new_gene['bb_std_dev'] = min(param_ranges['bb_std_dev'][1], 
                                              new_gene['bb_std_dev'] * random.uniform(1.1, 1.2))
        
        # 5. 多样性保护：变异方向多样化
        if random.random() < 0.15:  # 15%的概率执行多样性保护
            # 随机选择一个参数，强制向相反方向变异
            param_to_diversify = random.choice(['long_threshold', 'short_threshold', 'max_position', 'stop_loss'])
            if param_to_diversify in new_gene and param_to_diversify in param_ranges:
                # 如果参数接近范围上限，则向减小方向变异
                range_size = param_ranges[param_to_diversify][1] - param_ranges[param_to_diversify][0]
                normalized_value = (new_gene[param_to_diversify] - param_ranges[param_to_diversify][0]) / range_size
                
                if normalized_value > 0.7:  # 接近上限
                    new_gene[param_to_diversify] *= random.uniform(0.8, 0.9)
                elif normalized_value < 0.3:  # 接近下限
                    new_gene[param_to_diversify] *= random.uniform(1.1, 1.2)
        
        # 确保所有参数最终都在有效范围内
        for key in new_gene:
            if key in param_ranges:
                if isinstance(new_gene[key], (int, float)):
                    new_gene[key] = max(param_ranges[key][0], min(param_ranges[key][1], new_gene[key]))
        
        return new_gene
    
    def __repr__(self):
        return (f"LiveAgent(id={self.agent_id}, capital=${self.capital:.2f}, "
                f"ROI={self.roi:.2%}, trades={self.trade_count})")
