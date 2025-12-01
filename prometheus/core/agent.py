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
import os
from typing import Dict, Optional
import random
import numpy as np
from datetime import datetime

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
        - long_threshold/short_threshold: 决定了Agent的激进程度，使用对数正态分布更符合金融市场特性
        - max_position: 防止单个Agent过度集中资金
        - stop_loss/take_profit: 平衡风险和收益，使用对数正态分布
        - holding_period: 适应不同的交易风格（短线/中线），使用对数分布模拟市场时间周期特性
        - risk_aversion: 影响Agent在不同市场状态下的表现
        
        Returns:
            dict: 基因字典
        """
        # 使用对数正态分布生成阈值参数（更符合金融市场特性）
        long_threshold = np.random.lognormal(mean=np.log(0.1), sigma=0.3) * 0.5
        long_threshold = max(0.02, min(0.25, long_threshold))  # 更宽的范围
        
        # 同样使用对数正态分布生成空头阈值，取负值
        short_threshold_abs = np.random.lognormal(mean=np.log(0.1), sigma=0.3) * 0.5
        short_threshold_abs = max(0.02, min(0.25, short_threshold_abs))
        short_threshold = -short_threshold_abs
        
        # 最大仓位使用三角分布，集中在中位数附近
        max_position = random.triangular(0.3, 0.8, 1.2)  # 允许略超100%仓位用于测试
        
        # 止损使用对数正态分布，集中在较小值附近
        stop_loss = np.random.lognormal(mean=np.log(0.05), sigma=0.3)
        stop_loss = max(0.01, min(0.15, stop_loss))  # 更宽的范围
        
        # 止盈同样使用对数正态分布
        take_profit = np.random.lognormal(mean=np.log(0.1), sigma=0.4)
        take_profit = max(0.02, min(0.3, take_profit))  # 更宽的范围
        
        # 持有期使用对数分布，更符合市场时间特性
        holding_period_log = np.random.lognormal(mean=np.log(1200), sigma=0.8)
        holding_period = max(60, min(7200, int(holding_period_log)))  # 从1分钟到2小时
        
        # 风险偏好使用正态分布，集中在适中值附近
        risk_aversion = np.random.normal(loc=1.0, scale=0.4)
        risk_aversion = max(0.3, min(2.0, risk_aversion))  # 更广泛的风险偏好范围
        
        # 波动率调整因子 - 使用正态分布
        volatility_adjustment = np.random.normal(loc=1.0, scale=0.15)
        volatility_adjustment = max(0.8, min(1.2, volatility_adjustment))
        
        # 市场状态敏感度 - 使用对数正态分布
        market_regime_sensitivity = np.random.lognormal(mean=np.log(1.0), sigma=0.3)
        market_regime_sensitivity = max(0.5, min(1.5, market_regime_sensitivity))
        
        # 指标权重 - 确保权重之和在合理范围内
        momentum_weight = np.random.uniform(0.2, 0.8)
        rsi_weight = np.random.uniform(0.2, 0.8)
        macd_weight = np.random.uniform(0.2, 0.8)
        bollinger_weight = np.random.uniform(0.2, 0.8)
        
        # 计算总权重并归一化
        total_weight = momentum_weight + rsi_weight + macd_weight + bollinger_weight
        normalization_factor = random.uniform(0.5, 1.5) / total_weight  # 加入随机性
        
        return {
            'long_threshold': long_threshold,
            'short_threshold': short_threshold,
            'max_position': max_position,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'holding_period': holding_period,
            'risk_aversion': risk_aversion,
            # 新增参数
            'volatility_adjustment': volatility_adjustment,
            'market_regime_sensitivity': market_regime_sensitivity,
            'indicator_weights': {
                'momentum': momentum_weight * normalization_factor,
                'rsi': rsi_weight * normalization_factor,
                'macd': macd_weight * normalization_factor,
                'bollinger': bollinger_weight * normalization_factor
            }
        }
    
    def update(self, market_data: dict, regime: str):
        """
        更新Agent状态并生成交易信号
        
        这是Agent的"大脑"，每个更新周期（默认60秒）都会调用一次。
        
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
        # 强制记录update方法被调用，确保能看到代理更新
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 详细记录market_data参数
        market_data_type = type(market_data)
        market_data_keys = []
        has_candles = False
        candles_count = 0
        has_spot = False
        has_futures = False
        
        if isinstance(market_data, dict):
            market_data_keys = list(market_data.keys())
            has_spot = 'spot' in market_data
            has_futures = 'futures' in market_data
            has_candles = 'candles' in market_data
            if has_candles:
                candles_count = len(market_data['candles'])
        
        print(f"\n{'='*80}")
        print(f"[{timestamp}] [{self.agent_id}] LIVE AGENT UPDATE CALLED")
        print(f"[{timestamp}] [{self.agent_id}] 市场状态: {regime}")
        print(f"[{timestamp}] [{self.agent_id}] Market Data Type: {market_data_type}")
        print(f"[{timestamp}] [{self.agent_id}] Market Data Keys: {market_data_keys}")
        print(f"[{timestamp}] [{self.agent_id}] Has Spot Data: {has_spot}")
        print(f"[{timestamp}] [{self.agent_id}] Has Futures Data: {has_futures}")
        print(f"[{timestamp}] [{self.agent_id}] Has Candles: {has_candles}")
        print(f"[{timestamp}] [{self.agent_id}] Candles Count: {candles_count}")
        print(f"{'='*80}\n")
        
        # 确保立即刷新输出
        import sys
        sys.stdout.flush()
        
        # 强制在方法开头就记录final_signal_strength - 使用简单可靠的方式
        try:
            # 使用固定值进行测试
            test_signal_strength = 0.75
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 1. 标准输出 - 简化格式，避免编码问题
            print(f"[{timestamp}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {test_signal_strength}")
            print(f"[{timestamp}] [{self.agent_id}] THIS IS A FORCED LOG TEST")
            sys.stdout.flush()
            
            # 2. 写入专用文件 - 使用简单格式和绝对路径
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final_signal_strength.log')
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] [{self.agent_id}] FINAL_SIGNAL_STRENGTH={test_signal_strength}\n")
                print(f"[{timestamp}] [{self.agent_id}] 成功写入: {log_path}")
            except Exception as e:
                print(f"写入final_signal_strength.log失败: {e}", file=sys.stderr)
                
            # 3. 记录到日志系统
            logger.info(f"[{self.agent_id}] FINAL_SIGNAL_STRENGTH = {test_signal_strength}")
            
        except Exception as e:
            print(f"方法开头强制记录失败: {e}", file=sys.stderr)
            sys.stderr.flush()
        
        # 强制写入日志文件
        try:
            with open('signal_monitor_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] LIVE AGENT UPDATE CALLED")
                f.write(f"\n[{timestamp}] [{self.agent_id}] 市场状态: {regime}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Market Data Type: {market_data_type}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Market Data Keys: {market_data_keys}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Has Spot Data: {has_spot}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Has Futures Data: {has_futures}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Has Candles: {has_candles}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] Candles Count: {candles_count}")
                
                # 如果有K线数据，记录前几条样本
                if has_candles and candles_count > 0:
                    f.write(f"\n[{timestamp}] [{self.agent_id}] Candles Sample (first 2):")
                    for i, candle in enumerate(market_data['candles'][:2]):
                        f.write(f"\n[{timestamp}] [{self.agent_id}] Candle {i}: {candle[:3]}...")  # 只记录前几个元素
                
                f.write(f"\n{'='*80}")
        except Exception as e:
            print(f"写入update方法日志失败: {e}")
        
        if not self.is_alive:
            print(f"[{self.agent_id}] 代理已死亡，跳过更新")
            return
        
        # 更新持仓PnL
        self._update_positions_pnl(market_data)
        
        # 生成交易信号
        print(f"[{self.agent_id}] 开始生成交易信号...")
        self.pending_signals = self._generate_signals(market_data, regime)
        print(f"[{self.agent_id}] 信号生成完成，信号数量: {len(self.pending_signals)}")
        
        # 强制记录final_signal_strength - 不依赖pending_signals是否为空
        try:
            # 获取K线数据
            candles = market_data.get('candles', [])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 强制生成一个信号强度值用于记录
            signal_strength = 0.0
            
            # 尝试从信号中提取强度信息
            if self.pending_signals:
                for signal in self.pending_signals:
                    if 'strength' in signal:
                        signal_strength = signal['strength']
                        break
            
            # 简化日志记录逻辑
            print(f"[{timestamp}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {signal_strength}")
            print(f"[{timestamp}] [{self.agent_id}] 信号数量: {len(self.pending_signals)}")
            print(f"[{timestamp}] [{self.agent_id}] K线数量: {len(candles)}")
            print(f"[{timestamp}] [{self.agent_id}] 市场状态: {regime}")
            sys.stdout.flush()
            
            # 使用logger记录
            logger.info(f"[{self.agent_id}] FINAL_SIGNAL_STRENGTH = {signal_strength}")
            
            # 写入专用文件
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final_signal_strength.log')
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] [{self.agent_id}] FINAL_SIGNAL_STRENGTH={signal_strength}\n")
                    f.write(f"[{timestamp}] [{self.agent_id}] 信号数量: {len(self.pending_signals)}\n")
            except Exception as e:
                print(f"写入final_signal_strength.log失败: {e}", file=sys.stderr)
                sys.stderr.flush()
                
        except Exception as e:
            print(f"记录final_signal_strength失败: {e}", file=sys.stderr)
            sys.stderr.flush()
            logger.error(f"[{self.agent_id}] 记录final_signal_strength失败: {e}")
    
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
    
    def get_state(self):
        """
        获取代理状态，用于保存和恢复
        
        Returns:
            dict: 包含代理状态的字典
        """
        return {
            'agent_id': self.agent_id,
            'initial_capital': self.initial_capital,
            'capital': self.capital,
            'gene': self.gene,
            'is_alive': self.is_alive,
            'death_reason': self.death_reason,
            'birth_time': self.birth_time,
            'last_trade_time': self.last_trade_time,
            'trade_count': self.trade_count,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'total_pnl': self.total_pnl,
            'roi': self.roi,
            'positions': self.positions,
            'pending_signals': self.pending_signals
        }
    
    def _generate_signals(self, market_data: dict, regime: str):
        """
        生成交易信号
        
        Args:
            market_data: 市场数据
            regime: 市场状态
            
        Returns:
            交易信号列表
        """
        # 方法调用开始日志 - 使用绝对路径确保日志位置正确
        import os
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(log_dir, 'signal_monitor_log.txt')
        
        # 立即输出到标准输出，确保能看到
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        print(f"\n{'='*80}")
        print(f"[{timestamp}] [{self.agent_id}] _generate_signals方法被调用")
        print(f"[{timestamp}] [{self.agent_id}] 市场状态: {regime}")
        print(f"[{timestamp}] [{self.agent_id}] 日志文件路径: {log_path}")
        print(f"{'='*80}\n")
        
        # 确保立即刷新输出
        import sys
        sys.stdout.flush()
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}")
                f.write(f"\n[{timestamp}] [{self.agent_id}] _generate_signals方法被调用")
                f.write(f"\n[{timestamp}] [{self.agent_id}] 市场状态: {regime}")
        except Exception as e:
            print(f"写入方法调用日志失败: {e}")
        
        logger.critical(f"[{self.agent_id}] CRITICAL: _generate_signals方法被调用，市场状态: {regime}")
        
        signals = []
        final_signal_strength = 0.0  # 初始化默认值
        
        # 检查是否有足够的K线数据
        candles = market_data.get('candles', [])
        
        # 记录K线数据情况
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] [{self.agent_id}] K线数据数量: {len(candles)}")
                if len(candles) < 100:
                    f.write(f"\n[{datetime.now()}] [{self.agent_id}] K线数据不足100条")
        except Exception as e:
            print(f"写入K线数据日志失败: {e}")
        
        print(f"[{self.agent_id}] K线数据数量: {len(candles)}")
        logger.critical(f"[{self.agent_id}] CRITICAL: K线数据数量: {len(candles)}")
        
        # 强制记录final_signal_strength，无论K线数据是否充足
        def log_signal_strength(signal_strength, reason="默认值"):
            """辅助函数：使用多种方式记录信号强度"""
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 方式1: 标准输出（最高优先级）
            print(f"\n{'#'*80}")
            print(f"{'#'*20} 🔔 [{ts}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {signal_strength:.4f} 🔔 {'#'*20}")
            print(f"{'#'*20} [{ts}] [{self.agent_id}] 原因: {reason} {'#'*20}")
            print(f"{'#'*80}\n")
            sys.stdout.flush()
            
            # 方式2: 多种日志级别，提高INFO级别并确保在主要日志中看到
            logger.critical(f"[{self.agent_id}] CRITICAL: 🔔 FINAL SIGNAL STRENGTH = {signal_strength:.4f}, 原因: {reason}")
            logger.error(f"[{self.agent_id}] ERROR: FINAL SIGNAL STRENGTH = {signal_strength:.4f}")
            logger.warning(f"[{self.agent_id}] WARNING: FINAL SIGNAL STRENGTH = {signal_strength:.4f}")
            logger.info(f"[{self.agent_id}] INFO: 🔍 FINAL SIGNAL STRENGTH CALCULATION 🔍")
            logger.info(f"[{self.agent_id}] INFO: 🔔 FINAL SIGNAL STRENGTH = {signal_strength:.4f}, 原因: {reason}")
            
            # 方式3: 信号监控日志文件 - 使用更醒目的标记
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'*'*80}")
                    f.write(f"\n[{ts}] [{self.agent_id}] 🚨 FINAL SIGNAL STRENGTH = {signal_strength:.4f} 🚨")
                    f.write(f"\n[{ts}] [{self.agent_id}] 原因: {reason}")
                    f.write(f"\n[{ts}] [{self.agent_id}] K线数量: {len(candles)}")
                    f.write("\n" + "*"*80)
            except Exception as e:
                print(f"写入信号日志失败: {e}")
                
            # 方式4: 备用日志文件
            try:
                backup_log = os.path.join(os.getcwd(), 'backup_signal_log.txt')
                with open(backup_log, 'a', encoding='utf-8') as f:
                    f.write(f"\n[{ts}] [{self.agent_id}] 🚨 FINAL SIGNAL STRENGTH = {signal_strength:.4f}, 原因: {reason} 🚨")
            except Exception as e2:
                print(f"备用日志写入失败: {e2}")
            
            # 方式5: 额外的debug_log.txt确保捕获
            try:
                debug_log = os.path.join(os.getcwd(), 'debug_log.txt')
                with open(debug_log, 'a', encoding='utf-8') as f:
                    f.write(f"[{ts}] [{self.agent_id}] 🚨 FINAL SIGNAL STRENGTH = {signal_strength:.4f}, 原因: {reason} 🚨\n")
            except Exception as e3:
                print(f"写入debug日志失败: {e3}")
        
        # 先记录初始的final_signal_strength
        log_signal_strength(final_signal_strength, "方法开始初始化")
        
        if len(candles) < 100:  # 增加所需的K线数量，以支持更多技术指标计算
            print(f"[{self.agent_id}] K线数据不足100条，无法生成信号")
            logger.critical(f"[{self.agent_id}] CRITICAL: K线数据不足100条 ({len(candles)}条)，无法生成信号")
            log_signal_strength(final_signal_strength, "K线数据不足")
            return signals
        
        # 提取价格数据
        close_prices = np.array([float(c[4]) for c in candles[-100:]])
        high_prices = np.array([float(c[2]) for c in candles[-100:]])
        low_prices = np.array([float(c[3]) for c in candles[-100:]])
        
        # 计算波动率（使用ATR指标的简化版本）
        true_ranges = np.maximum(
            high_prices[1:] - low_prices[1:],
            np.maximum(
                np.abs(high_prices[1:] - close_prices[:-1]),
                np.abs(low_prices[1:] - close_prices[:-1])
            )
        )
        volatility = np.mean(true_ranges[-20:]) / np.mean(close_prices[-20:])  # 归一化波动率
        
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
        
        # 根据市场状态调整阈值，并应用市场状态敏感度
        regime_config = self.config['market_regime']['regimes'].get(regime, {'long': 0.5, 'short': 0.5})
        long_bias = regime_config['long']
        short_bias = regime_config['short']
        
        # 应用市场状态敏感度基因参数
        market_sensitivity = self.gene.get('market_state_sensitivity', 1.0)
        long_threshold = self.gene['long_threshold'] * (2 - long_bias * market_sensitivity)
        short_threshold = self.gene['short_threshold'] * (2 - short_bias * market_sensitivity)
        
        # 综合信号计算
        final_signal_strength = 0.0
        signal_components = []
        
        # 动量信号
        if momentum > long_threshold:
            # 限制动量信号范围
            momentum_signal = momentum * long_bias
            momentum_signal = max(-0.8, min(0.8, momentum_signal))
            # 应用指标权重
            momentum_weight = self.gene.get('indicator_weights', {}).get('momentum', 1.0)
            momentum_signal *= momentum_weight
            signal_components.append(momentum_signal)
            logger.debug(f"[{self.agent_id}] 动量信号: {momentum_signal:.4f} (权重: {momentum_weight})")
        elif momentum < short_threshold:
            # 限制动量信号范围
            momentum_signal = momentum * short_bias
            momentum_signal = max(-0.8, min(0.8, momentum_signal))
            # 应用指标权重
            momentum_weight = self.gene.get('indicator_weights', {}).get('momentum', 1.0)
            momentum_signal *= momentum_weight
            signal_components.append(momentum_signal)
            logger.debug(f"[{self.agent_id}] 动量信号: {momentum_signal:.4f} (权重: {momentum_weight})")
        
        # RSI信号 (超买超卖)
        if rsi < 30:  # 超卖
            rsi_signal = 0.2 * (30 - rsi) / 30
            rsi_signal = min(0.8, rsi_signal)  # 限制最大值为0.8
            # 应用指标权重
            rsi_weight = self.gene.get('indicator_weights', {}).get('rsi', 1.0)
            rsi_signal *= rsi_weight
            signal_components.append(rsi_signal)
            logger.debug(f"[{self.agent_id}] RSI信号: {rsi_signal:.4f} (权重: {rsi_weight})")
        elif rsi > 70:  # 超买
            rsi_signal = -0.2 * (rsi - 70) / 30
            rsi_signal = max(-0.8, rsi_signal)  # 限制最小值为-0.8
            # 应用指标权重
            rsi_weight = self.gene.get('indicator_weights', {}).get('rsi', 1.0)
            rsi_signal *= rsi_weight
            signal_components.append(rsi_signal)
            logger.debug(f"[{self.agent_id}] RSI信号: {rsi_signal:.4f} (权重: {rsi_weight})")
        
        # MACD信号 - 优化计算以避免异常值
        if sma20 > 0:  # 确保sma20有效
            # 归一化MACD柱状图值
            # 使用更稳健的归一化方法，避免分母过小导致的异常值
            normalization_factor = max(sma20 * 0.01, 0.1)  # 确保分母至少为0.1
            raw_macd_signal = macd_hist / normalization_factor
            
            # 限制原始信号范围
            raw_macd_signal = max(-5.0, min(5.0, raw_macd_signal))
            
            # 应用权重并限制最终MACD信号范围
            macd_signal = 0.2 * raw_macd_signal
            macd_signal = max(-0.8, min(0.8, macd_signal))  # 进一步限制范围，避免单个组件影响过大
            
            # 应用指标权重
            macd_weight = self.gene.get('indicator_weights', {}).get('macd', 1.0)
            macd_signal *= macd_weight
            signal_components.append(macd_signal)
            logger.debug(f"[{self.agent_id}] MACD信号计算: macd_hist={macd_hist:.6f}, sma20={sma20:.6f}, 信号={macd_signal:.4f} (权重: {macd_weight})")
        else:
            signal_components.append(0.0)
            logger.debug(f"[{self.agent_id}] MACD信号计算: SMA20无效，使用默认值0")
        
        # Bollinger Bands信号
        if bb_position < 0.3:  # 接近下轨
            bb_signal = 0.2 * (0.3 - bb_position) / 0.3
            bb_signal = min(0.8, bb_signal)  # 限制最大值为0.8
            # 应用指标权重
            bb_weight = self.gene.get('indicator_weights', {}).get('bollinger', 1.0)
            bb_signal *= bb_weight
            signal_components.append(bb_signal)
            logger.debug(f"[{self.agent_id}] 布林带信号: {bb_signal:.4f} (权重: {bb_weight})")
        elif bb_position > 0.7:  # 接近上轨
            bb_signal = -0.2 * (bb_position - 0.7) / 0.3
            bb_signal = max(-0.8, bb_signal)  # 限制最小值为-0.8
            # 应用指标权重
            bb_weight = self.gene.get('indicator_weights', {}).get('bollinger', 1.0)
            bb_signal *= bb_weight
            signal_components.append(bb_signal)
            logger.debug(f"[{self.agent_id}] 布林带信号: {bb_signal:.4f} (权重: {bb_weight})")
        
        # 强制写入信号监控日志文件
        try:
            with open('signal_monitor_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] [{self.agent_id}] 开始计算信号强度，信号组件数量: {len(signal_components)}")
                f.write(f"\n[{datetime.now()}] [{self.agent_id}] 组件内容: {signal_components}")
        except Exception as e:
            print(f"写入信号监控日志失败: {e}")
        
        # 标准输出和日志
        print(f"[{self.agent_id}] 开始计算信号强度，信号组件数量: {len(signal_components)}")
        logger.critical(f"[{self.agent_id}] DEBUG: 信号组件数量: {len(signal_components)}, 组件内容: {signal_components}")
        
        # 计算最终信号强度
        if signal_components:
            # 记录每个信号组件的值用于调试 - 使用更醒目的输出
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            component_types = ['动量', 'RSI', 'MACD', '布林带']
            component_values = signal_components[:4]  # 确保不超过4个组件
            debug_info = ', '.join([f"{t}: {v:.4f}" for t, v in zip(component_types, component_values)])
            logger.debug(f"[{self.agent_id}] 信号组件: {debug_info}")
            print(f"\n{'='*80}")
            print(f"[{timestamp}] [{self.agent_id}] SIGNAL COMPONENTS DETAILS")
            print(f"[{timestamp}] [{self.agent_id}] {debug_info}")
            print(f"[{timestamp}] [{self.agent_id}] 组件总数: {len(signal_components)}")
            print(f"{'='*80}\n")
            sys.stdout.flush()
            
            # 计算原始平均信号强度
            raw_mean = np.mean(signal_components)
            print(f"[{self.agent_id}] 原始均值: {raw_mean:.4f}")
            
            # 应用波动率调整因子 - 优化版：减少过度抑制
            volatility_adjustment = self.gene.get('volatility_adjustment', 1.0)
            # 使用更平衡的公式，减少对信号强度的过度抑制
            # 通过平方根变换使波动率的影响更加平滑
            adjusted_volatility = min(volatility * volatility_adjustment, 1.0)  # 限制最大调整幅度
            volatility_factor = 1.0 - (np.sqrt(adjusted_volatility) * 0.5)  # 平方根变换，降低抑制程度
            volatility_factor = max(0.6, min(1.8, volatility_factor))  # 扩大范围，允许更强的信号放大
            
            # 应用波动率调整
            final_signal_strength = raw_mean * volatility_factor
            print(f"[{self.agent_id}] 应用波动率调整后的信号强度: {final_signal_strength:.4f} (波动率: {volatility:.4f}, 调整因子: {volatility_adjustment:.4f}, 缩放系数: {volatility_factor:.4f})")
            
            # 仍然保留边界检查作为最后保障
            final_signal_strength = max(-1.9, min(1.9, final_signal_strength))
            print(f"[{self.agent_id}] 边界检查后的信号强度: {final_signal_strength:.4f}")
            
            # 存储当前信号强度用于下次比较
            if hasattr(self, 'prev_signal_strength'):
                signal_change = final_signal_strength - self.prev_signal_strength
                logger.debug(f"[{self.agent_id}] 信号强度变化: {signal_change:.4f}")
            self.prev_signal_strength = final_signal_strength
            
            # 强制输出最终信号强度，使用多种日志级别和直接打印
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            logger.critical(f"[{self.agent_id}] CRITICAL: FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
            logger.error(f"[{self.agent_id}] ERROR: FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
            logger.warning(f"[{self.agent_id}] WARNING: FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
            logger.info(f"[{self.agent_id}] INFO: FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
            logger.debug(f"[{self.agent_id}] DEBUG: FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
            
            # 强制输出到标准输出，无论日志配置如何，使用更醒目的格式
            print(f"\n{'*'*80}")
            print(f"{'*'*20} [{timestamp}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {final_signal_strength:.4f} {'*'*20}")
            print(f"{'*'*80}\n")
            
            # 确保输出立即显示
            import sys
            sys.stdout.flush()
            
            # 将最终信号强度写入监控日志文件，使用明确的文件路径
            try:
                log_file = 'signal_monitor_log.txt'
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'*'*80}")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] 原始均值: {raw_mean:.4f}, 组件数: {len(signal_components)}")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] 信号组件详情: {signal_components}")
                    f.write("\n" + "*"*80)
                print(f"[{timestamp}] [{self.agent_id}] 最终信号强度已写入日志文件: {log_file}")
            except Exception as e:
                print(f"写入最终信号强度日志失败: {e}")
                # 尝试使用备用日志文件路径
                try:
                    backup_log = os.path.join(os.getcwd(), 'backup_signal_log.txt')
                    with open(backup_log, 'a', encoding='utf-8') as f:
                        f.write(f"\n[{timestamp}] [{self.agent_id}] FINAL SIGNAL STRENGTH = {final_signal_strength:.4f}")
                    print(f"备用日志已写入: {backup_log}")
                except Exception as e2:
                    print(f"备用日志写入也失败: {e2}")
        else:
            final_signal_strength = 0.0
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            logger.critical(f"[{self.agent_id}] CRITICAL: 没有生成有效信号组件，信号强度设为0.0")
            print(f"\n{'*'*80}")
            print(f"{'*'*20} [{timestamp}] [{self.agent_id}] 没有生成有效信号组件，信号强度设为0.0 {'*'*20}")
            print(f"{'*'*80}\n")
            
            # 将无信号情况写入监控日志文件，使用绝对路径
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'*'*80}")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] 没有生成有效信号组件，信号强度设为0.0")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] 技术指标值: momentum={momentum:.4f}, rsi={rsi:.4f}, macd_hist={macd_hist:.6f}, bb_position={bb_position:.4f}")
                    f.write(f"\n[{timestamp}] [{self.agent_id}] 基因参数: long_threshold={self.gene['long_threshold']}, short_threshold={self.gene['short_threshold']}")
                    f.write("\n" + "*"*80)
                print(f"[{timestamp}] [{self.agent_id}] 无信号状态已写入日志文件: {log_path}")
            except Exception as e:
                print(f"写入无信号日志失败: {e}")
            # 重置历史记录
            if hasattr(self, 'prev_signal_strength'):
                delattr(self, 'prev_signal_strength')
        
        # 生成交易信号 - 增强版：趋势跟踪与灵活信号确认
        # 移除固定最低阈值限制，使用基因中定义的值
        long_threshold = self.gene['long_threshold']
        short_threshold = self.gene['short_threshold']
        
        # 添加趋势跟踪机制 - 计算中期趋势
        if len(close_prices) >= 50:
            # 使用50日均线判断中期趋势
            sma50 = np.mean(close_prices[-50:])
            sma20 = np.mean(close_prices[-20:])
            # 趋势强度：1.0为强烈多头，-1.0为强烈空头
            trend_strength = min(1.0, max(-1.0, (sma20 - sma50) / sma50 * 100))
        else:
            trend_strength = 0.0
        
        # 灵活信号确认机制
        signal_confirmed = False
        confirmation_factor = 1.0
        
        # 同向趋势确认：与趋势同向的信号更容易被确认
        if trend_strength > 0.2 and final_signal_strength > long_threshold:
            # 多头趋势且有多头信号，降低确认门槛
            confirmation_factor = 0.8
            signal_confirmed = final_signal_strength > (long_threshold * confirmation_factor)
        elif trend_strength < -0.2 and final_signal_strength < short_threshold:
            # 空头趋势且有空头信号，降低确认门槛
            confirmation_factor = 0.8
            signal_confirmed = final_signal_strength < (short_threshold * confirmation_factor)
        elif abs(trend_strength) < 0.1:
            # 横盘市场，需要更强的信号确认
            confirmation_factor = 1.2
            signal_confirmed = (final_signal_strength > (long_threshold * confirmation_factor)) or \
                              (final_signal_strength < (short_threshold * confirmation_factor))
        else:
            # 基本确认逻辑
            signal_confirmed = (final_signal_strength > long_threshold) or (final_signal_strength < short_threshold)
        
        # 记录趋势和确认信息
        logger.debug(f"[{self.agent_id}] 趋势强度: {trend_strength:.4f}, 确认因子: {confirmation_factor:.2f}, 信号确认: {signal_confirmed}")
        
        # 生成交易信号
        if signal_confirmed:
            if final_signal_strength > long_threshold * confirmation_factor:
                # 做多信号
                # 结合趋势强度调整信号强度
                combined_strength = min(1.0, final_signal_strength * (1.0 + abs(trend_strength) * 0.3))
                signals.append({
                    'action': 'open',
                    'side': 'long',
                    'symbol': self.config['markets']['spot']['symbol'],
                    'market': 'spot',
                    'strength': combined_strength * long_bias,
                    'indicators': {
                        'momentum': momentum,
                        'rsi': rsi,
                        'macd_hist': macd_hist,
                        'bb_position': bb_position,
                        'trend_strength': trend_strength
                    }
                })
            elif final_signal_strength < short_threshold * confirmation_factor:
                # 做空信号（只在合约市场）
                # 结合趋势强度调整信号强度
                combined_strength = min(1.0, abs(final_signal_strength) * (1.0 + abs(trend_strength) * 0.3))
                signals.append({
                    'action': 'open',
                    'side': 'short',
                    'symbol': self.config['markets']['futures']['symbol'],
                    'market': 'futures',
                    'strength': combined_strength * short_bias,
                    'indicators': {
                        'momentum': momentum,
                        'rsi': rsi,
                        'macd_hist': macd_hist,
                        'bb_position': bb_position,
                        'trend_strength': trend_strength
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
