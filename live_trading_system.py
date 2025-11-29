"""
Live Trading System for Prometheus v3.0
"""

import logging
import time
import signal
import sys
from datetime import datetime
from typing import Dict, List
import json

from prometheus_v30.adapters.okx_adapter import OKXTradingAdapter
from prometheus_v30.live_agent import LiveAgent
from prometheus_v30.market_regime import MarketRegimeDetector
from prometheus_v30.simple_capital_manager import SimpleCapitalManager

logger = logging.getLogger(__name__)


class LiveTradingSystem:
    """实盘交易系统"""
    
    def __init__(self, config, okx_config):
        """
        初始化
        
        Args:
            config: Prometheus配置
            okx_config: OKX API配置
        """
        self.config = config
        self.okx_config = okx_config
        
        # 初始化OKX适配器
        self.adapter = OKXTradingAdapter(okx_config)
        
        # 初始化市场状态检测器
        self.market_detector = MarketRegimeDetector(
            config['market_regime']['regimes']
        )
        
        # 初始化资金管理器
        self.capital_manager = SimpleCapitalManager(
            total_capital=config['initial_capital'],
            pool_ratio=config['capital_manager']['pool_ratio']
        )
        
        # Agent列表
        self.agents: List[LiveAgent] = []
        
        # 交易统计
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'births': 0,
            'deaths': 0
        }
        
        # 运行状态
        self.running = False
        self.stop_requested = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("LiveTradingSystem initialized")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"Received signal {signum}, stopping...")
        self.stop_requested = True
    
    def initialize_agents(self):
        """初始化agents"""
        logger.info(f"Initializing {self.config['initial_agents']} agents...")
        
        for i in range(self.config['initial_agents']):
            # 从资金池分配资金
            capital = self.capital_manager.allocate_capital(
                self.config['capital_manager']['min_agent_capital']
            )
            
            if capital > 0:
                agent = LiveAgent(
                    agent_id=f"agent_{i+1}",
                    initial_capital=capital,
                    config=self.config
                )
                self.agents.append(agent)
                logger.info(f"Created {agent.agent_id} with capital ${capital:.2f}")
            else:
                logger.warning(f"Insufficient capital for agent {i+1}")
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    def run(self, duration_seconds=3600):
        """
        运行交易系统
        
        Args:
            duration_seconds: 运行时长（秒）
        """
        logger.info(f"Starting live trading for {duration_seconds} seconds...")
        
        self.stats['start_time'] = datetime.now()
        self.running = True
        
        # 初始化agents
        self.initialize_agents()
        
        # 获取初始账户状态
        initial_summary = self.adapter.get_account_summary()
        logger.info(f"Initial account: ${initial_summary['total_equity']:.2f}")
        
        # 主循环
        end_time = time.time() + duration_seconds
        update_interval = self.config['trading']['update_interval']
        
        iteration = 0
        while self.running and time.time() < end_time and not self.stop_requested:
            iteration += 1
            loop_start = time.time()
            
            try:
                logger.info(f"=== Iteration {iteration} ===")
                
                # 1. 获取市场数据
                market_data = self._get_market_data()
                
                # 2. 更新市场状态
                regime = self._update_market_regime(market_data)
                logger.info(f"Market regime: {regime}")
                
                # 3. 更新所有agents
                self._update_agents(market_data, regime)
                
                # 4. 执行交易
                self._execute_trades()
                
                # 5. 检查繁殖和死亡
                self._check_lifecycle()
                
                # 6. 打印状态
                self._print_status()
                
                # 7. 等待下一次更新
                elapsed = time.time() - loop_start
                sleep_time = max(0, update_interval - elapsed)
                if sleep_time > 0:
                    logger.debug(f"Sleeping for {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                self.stats['failed_trades'] += 1
                time.sleep(5)  # 错误后等待5秒
        
        # 停止交易
        self.stop()
        
        logger.info("Live trading completed")
    
    def _get_market_data(self):
        """获取市场数据"""
        spot_symbol = self.config['markets']['spot']['symbol']
        futures_symbol = self.config['markets']['futures']['symbol']
        
        # 获取现货价格
        spot_price = self.adapter.get_price(spot_symbol)
        
        # 获取合约价格
        futures_price = self.adapter.get_price(futures_symbol)
        
        # 获取K线数据（用于市场状态检测）
        candles = self.adapter.get_candles(
            spot_symbol,
            bar='1H',
            limit=100
        )
        
        return {
            'spot': {
                'symbol': spot_symbol,
                'price': spot_price,
                'timestamp': time.time()
            },
            'futures': {
                'symbol': futures_symbol,
                'price': futures_price,
                'timestamp': time.time()
            },
            'candles': candles
        }
    
    def _update_market_regime(self, market_data):
        """更新市场状态"""
        candles = market_data['candles']
        if len(candles) > 0:
            prices = [float(c[4]) for c in candles]  # 收盘价
            regime = self.market_detector.detect_regime(prices)
            return regime
        return 'sideways'
    
    def _update_agents(self, market_data, regime):
        """更新所有agents"""
        for agent in self.agents:
            if agent.is_alive:
                try:
                    # 更新agent状态
                    agent.update(market_data, regime)
                except Exception as e:
                    logger.error(f"Error updating {agent.agent_id}: {e}")
    
    def _execute_trades(self):
        """执行交易"""
        for agent in self.agents:
            if not agent.is_alive:
                continue
            
            # 检查是否有待执行的信号
            if not hasattr(agent, 'pending_signals') or not agent.pending_signals:
                continue
            
            # 执行每个信号
            for signal in agent.pending_signals:
                try:
                    # 转换信号为订单请求
                    order_request = self._signal_to_order(signal, agent)
                    
                    if order_request is None:
                        continue
                    
                    # 执行订单
                    logger.info(f"{agent.agent_id} placing order: {signal['action']} {signal.get('side', 'close')} {signal['symbol']}")
                    order = self.adapter.place_order(order_request)
                    
                    # 更新统计
                    self.stats['total_trades'] += 1
                    self.stats['successful_trades'] += 1
                    
                    # 更新agent状态
                    agent.last_trade_time = time.time()
                    agent.trade_count += 1
                    
                    logger.info(f"{agent.agent_id} order executed: {order.order_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to execute trade for {agent.agent_id}: {e}")
                    self.stats['failed_trades'] += 1
            
            # 清空已处理的信号
            agent.pending_signals = []
    
    def _signal_to_order(self, signal, agent):
        """
        将信号转换为订单请求
        
        Args:
            signal: 交易信号
            agent: Agent对象
            
        Returns:
            订单请求字典，或None
        """
        try:
            if signal['action'] == 'close':
                # 平仓信号
                if signal['symbol'] not in agent.positions:
                    return None
                
                pos = agent.positions[signal['symbol']]
                
                # 确定平仓方向
                if pos['side'] == 'long':
                    side = 'sell'
                    pos_side = 'long'
                else:
                    side = 'buy'
                    pos_side = 'short'
                
                # 构建平仓订单
                market = 'futures' if 'SWAP' in signal['symbol'] else 'spot'
                return {
                    'market': market,
                    'symbol': signal['symbol'],
                    'side': side,
                    'pos_side': pos_side,
                    'order_type': 'market',
                    'size': abs(pos['size']),
                    'reduce_only': True
                }
            
            elif signal['action'] == 'open':
                # 开仓信号
                market = signal['market']
                symbol = signal['symbol']
                side = signal['side']
                strength = signal.get('strength', 0.5)
                
                # 计算订单数量
                if market == 'spot':
                    # 现货：使用agent资金的一定比例
                    value = agent.capital * strength * 0.3  # 最多30%资金
                    # 限制单笔订单最大$500
                    value = min(value, self.config['risk']['max_order_value'])
                    
                    # 获取当前价格
                    current_price = self.adapter.get_price(symbol)
                    size = value / current_price
                    
                    # 现货最小0.0001 BTC
                    if size < 0.0001:
                        return None
                    
                    return {
                        'market': 'spot',
                        'symbol': symbol,
                        'side': 'buy',  # 现货只能做多
                        'order_type': 'market',
                        'size': round(size, 4)
                    }
                
                else:
                    # 合约：计算合约张数
                    value = agent.capital * strength * 0.3  # 最多30%资金
                    value = min(value, self.config['risk']['max_order_value'])
                    
                    # 每张合约约100 USDT
                    size = int(value / 100)
                    
                    # 最少1张
                    if size < 1:
                        return None
                    
                    # 确定方向
                    if side == 'long':
                        order_side = 'buy'
                        pos_side = 'long'
                    else:
                        order_side = 'sell'
                        pos_side = 'short'
                    
                    return {
                        'market': 'futures',
                        'symbol': symbol,
                        'side': order_side,
                        'pos_side': pos_side,
                        'order_type': 'market',
                        'size': size,
                        'leverage': self.config['markets']['futures']['max_leverage']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error converting signal to order: {e}")
            return None
    
    def _check_lifecycle(self):
        """检查繁殖和死亡"""
        # 检查死亡
        for agent in self.agents:
            if agent.is_alive and agent.should_die():
                agent.is_alive = False
                self.stats['deaths'] += 1
                # 回收资金到资金池
                self.capital_manager.return_capital(agent.capital)
                logger.info(f"{agent.agent_id} died, capital returned: ${agent.capital:.2f}")
        
        # 检查繁殖
        if len([a for a in self.agents if a.is_alive]) < self.config['max_agents']:
            for agent in self.agents:
                if agent.is_alive and agent.can_reproduce():
                    # 尝试繁殖
                    cost = agent.capital * self.config['agent_manager']['reproduction']['cost_ratio']
                    new_capital = self.capital_manager.allocate_capital(cost)
                    
                    if new_capital > 0:
                        new_agent = agent.reproduce(new_capital)
                        self.agents.append(new_agent)
                        self.stats['births'] += 1
                        logger.info(f"{agent.agent_id} reproduced -> {new_agent.agent_id}")
                        break
    
    def _print_status(self):
        """打印当前状态"""
        active_agents = [a for a in self.agents if a.is_alive]
        
        # 获取账户摘要
        summary = self.adapter.get_account_summary()
        
        logger.info(f"Active agents: {len(active_agents)}/{len(self.agents)}")
        logger.info(f"Total equity: ${summary['total_equity']:.2f}")
        logger.info(f"Unrealized PnL: ${summary['total_unrealized_pnl']:.2f}")
        logger.info(f"Total trades: {self.stats['total_trades']}")
        logger.info(f"Births: {self.stats['births']}, Deaths: {self.stats['deaths']}")
    
    def stop(self):
        """停止交易系统"""
        if not self.running:
            return
        
        logger.info("Stopping live trading system...")
        self.running = False
        self.stats['end_time'] = datetime.now()
        
        # 关闭所有持仓
        self._close_all_positions()
        
        # 生成最终报告
        self._generate_report()
        
        logger.info("Live trading system stopped")
    
    def _close_all_positions(self):
        """关闭所有持仓"""
        logger.info("Closing all positions...")
        
        positions = self.adapter.get_positions()
        for inst_id, pos in positions.items():
            if pos['size'] != 0:
                try:
                    # 平仓
                    side = 'sell' if pos['size'] > 0 else 'buy'
                    order_request = {
                        'market': 'futures' if 'SWAP' in inst_id else 'spot',
                        'symbol': inst_id,
                        'side': side,
                        'order_type': 'market',
                        'size': abs(pos['size'])
                    }
                    self.adapter.place_order(order_request)
                    logger.info(f"Closed position: {inst_id}")
                except Exception as e:
                    logger.error(f"Failed to close position {inst_id}: {e}")
    
    def _generate_report(self):
        """生成交易报告"""
        logger.info("Generating trading report...")
        
        # 获取最终账户状态
        final_summary = self.adapter.get_account_summary()
        
        # 计算ROI
        initial_capital = self.config['initial_capital']
        final_capital = final_summary['total_equity']
        roi = (final_capital - initial_capital) / initial_capital * 100
        
        # 计算运行时长
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        report = {
            'summary': {
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': self.stats['end_time'].isoformat(),
                'duration_seconds': duration,
                'initial_capital': initial_capital,
                'final_capital': final_capital,
                'roi_pct': roi
            },
            'trading': {
                'total_trades': self.stats['total_trades'],
                'successful_trades': self.stats['successful_trades'],
                'failed_trades': self.stats['failed_trades'],
                'success_rate': self.stats['successful_trades'] / max(1, self.stats['total_trades']) * 100
            },
            'agents': {
                'total_agents': len(self.agents),
                'active_agents': len([a for a in self.agents if a.is_alive]),
                'births': self.stats['births'],
                'deaths': self.stats['deaths']
            }
        }
        
        # 保存报告
        report_file = f"/home/ubuntu/trading_logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_file}")
        logger.info(f"Final ROI: {roi:.2f}%")
        
        return report
