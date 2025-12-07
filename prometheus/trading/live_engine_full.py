#!/usr/bin/env python3
"""
实盘交易引擎 - 完整版（真实下单）
==================================

重要修改：
1. ✅ 真实下单到OKX（已取消注释）
2. ✅ 持仓跟踪系统
3. ✅ 真实盈亏计算
4. ✅ 风控机制
5. ✅ 异常处理
"""

import logging
import time
from typing import List, Dict, Optional
from datetime import datetime
from prometheus.exchange.okx_api import OKXExchange
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

logger = logging.getLogger(__name__)


class LiveTradingEngine:
    """实盘交易引擎 - 完整版"""
    
    def __init__(
        self,
        exchange: OKXExchange,
        moirai: Moirai,
        evolution_manager: EvolutionManagerV5,
        symbol: str = 'BTC/USDT',
        interval: int = 60,
        evolution_interval: int = 86400,
        max_position_size: float = 0.01,
        max_leverage: float = 10.0,
        enable_real_trading: bool = True,  # 是否启用真实交易
    ):
        """初始化交易引擎"""
        self.exchange = exchange
        self.moirai = moirai
        self.evolution_manager = evolution_manager
        self.symbol = symbol
        self.interval = interval
        self.evolution_interval = evolution_interval
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        self.enable_real_trading = enable_real_trading
        
        self.running = False
        self.cycle_count = 0
        self.last_evolution_time = time.time()
        self.last_price = None
        
        # 持仓跟踪
        self.positions = {}  # {agent_id: {'side': 'long/short', 'size': 0.001, 'entry_price': 89500, 'leverage': 5}}
        
        # 统计
        self.total_orders = 0
        self.successful_orders = 0
        self.failed_orders = 0
        
        logger.info(f"✅ 实盘交易引擎初始化完成")
        logger.info(f"   交易对: {symbol}")
        logger.info(f"   交易周期: {interval}秒")
        logger.info(f"   真实交易: {'启用' if enable_real_trading else '禁用（仅模拟）'}")
        logger.info(f"   最大持仓: {max_position_size} BTC")
        logger.info(f"   最大杠杆: {max_leverage}x")
    
    def start(self):
        """启动交易引擎"""
        self.running = True
        logger.info("🚀 交易引擎启动")
        
        if self.enable_real_trading:
            logger.warning("⚠️  真实交易模式已启用 - 将会在OKX下单！")
        else:
            logger.info("ℹ️  模拟模式 - 不会真实下单")
        
        try:
            while self.running:
                self.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("⏹️  收到停止信号")
            self.stop()
        except Exception as e:
            logger.error(f"❌ 交易引擎异常: {e}")
            import traceback
            traceback.print_exc()
            self.stop()
    
    def stop(self):
        """停止交易引擎"""
        self.running = False
        logger.info("⏹️  交易引擎已停止")
        
        # 显示最终统计
        logger.info(f"\n📊 最终统计:")
        logger.info(f"   总订单数: {self.total_orders}")
        logger.info(f"   成功: {self.successful_orders}")
        logger.info(f"   失败: {self.failed_orders}")
        logger.info(f"   成功率: {self.successful_orders / self.total_orders * 100 if self.total_orders > 0 else 0:.1f}%")
    
    def run_cycle(self):
        """运行一个交易周期"""
        try:
            self.cycle_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 交易周期 #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 获取市场数据
            ticker = self.exchange.get_ticker(self.symbol)
            if not ticker:
                logger.error("❌ 无法获取行情数据")
                return
            
            current_price = ticker['last']
            logger.info(f"📊 当前价格: ${current_price:,.2f}")
            
            # 2. 计算价格变化
            price_change = 0.0
            if self.last_price:
                price_change = (current_price - self.last_price) / self.last_price
                logger.info(f"📈 价格变化: {price_change:+.2%}")
            
            self.last_price = current_price
            
            # 3. 更新所有持仓的盈亏
            self.update_all_positions_pnl(current_price)
            
            # 4. 每个Agent做决策
            agents = self.moirai.agents
            logger.info(f"👥 活跃Agent数量: {len(agents)}")
            
            decision_count = 0
            buy_count = 0
            sell_count = 0
            hold_count = 0
            close_count = 0
            
            for agent in agents:
                if agent.current_capital <= 0:
                    continue
                
                # Agent决策
                decision = self.agent_make_decision(agent, price_change, current_price)
                
                # 执行决策
                if decision:
                    success = self.execute_decision(agent, decision, current_price)
                    if success:
                        decision_count += 1
                        
                        if decision['action'] == 'buy':
                            buy_count += 1
                        elif decision['action'] == 'sell':
                            sell_count += 1
                        elif decision['action'] == 'close':
                            close_count += 1
                else:
                    hold_count += 1
            
            # 显示决策统计
            logger.info(f"📊 决策统计: {buy_count}开多 / {sell_count}开空 / {close_count}平仓 / {hold_count}持有")
            if decision_count > 0:
                logger.info(f"✅ 本周期有 {decision_count} 个交易决策")
            
            # 5. 检查是否需要进化
            if time.time() - self.last_evolution_time >= self.evolution_interval:
                self.run_evolution()
                self.last_evolution_time = time.time()
            
            # 6. 显示状态
            self.log_status()
            
        except Exception as e:
            logger.error(f"❌ 交易周期异常: {e}")
            import traceback
            traceback.print_exc()
    
    def agent_make_decision(self, agent, price_change: float, current_price: float) -> Optional[Dict]:
        """Agent做决策"""
        try:
            risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
            agent_id = agent.agent_id
            
            # 检查是否已有持仓
            has_position = agent_id in self.positions
            
            # 如果有持仓，先考虑是否平仓
            if has_position:
                position = self.positions[agent_id]
                pnl_ratio = position.get('pnl_ratio', 0)
                
                # 止盈：盈利超过5%
                if pnl_ratio > 0.05:
                    return {
                        'action': 'close',
                        'reason': f'止盈 (PnL: {pnl_ratio:+.2%})'
                    }
                
                # 止损：亏损超过3%
                if pnl_ratio < -0.03:
                    return {
                        'action': 'close',
                        'reason': f'止损 (PnL: {pnl_ratio:+.2%})'
                    }
                
                # 其他情况继续持有
                return None
            
            # 没有持仓，考虑开仓
            # 降低决策阈值
            if abs(price_change) < 0.0001:  # 0.01%
                return None
            
            # 决定开多还是开空
            if price_change > 0:
                action = 'buy'  # 开多
                position = risk_tolerance * 0.8
            else:
                action = 'sell'  # 开空
                position = risk_tolerance * 0.8
            
            # 计算交易数量
            account_value = self.exchange.get_account_value()
            agent_capital_ratio = agent.current_capital / (account_value if account_value > 0 else 1.0)
            
            size = min(
                position * agent_capital_ratio * self.max_position_size,
                self.max_position_size * 0.1
            )
            
            # 降低最小交易量阈值
            if size < 0.0001:
                return None
            
            # 杠杆选择
            leverage = min(1.0 + risk_tolerance * 9.0, self.max_leverage)
            
            return {
                'action': action,
                'size': size,
                'leverage': leverage,
                'reason': f'价格变化{price_change:+.2%}'
            }
        
        except Exception as e:
            logger.error(f"Agent决策异常: {e}")
            return None
    
    def execute_decision(self, agent, decision: Dict, current_price: float) -> bool:
        """执行Agent决策 - 真实下单"""
        try:
            action = decision['action']
            reason = decision.get('reason', '')
            agent_id = agent.agent_id
            
            # 记录决策
            logger.info(
                f"📝 Agent[{agent_id[:8]}] 决策: {action.upper()} "
                f"(资金: ${agent.current_capital:,.2f}) {reason}"
            )
            
            # 如果是平仓
            if action == 'close':
                return self.close_position(agent, current_price)
            
            # 如果是开仓
            size = decision['size']
            leverage = decision['leverage']
            
            if not self.enable_real_trading:
                # 模拟模式：只记录，不真实下单
                logger.info(f"   [模拟] {action.upper()} {size:.4f} BTC @ {leverage:.1f}x")
                # 记录虚拟持仓
                self.positions[agent_id] = {
                    'side': 'long' if action == 'buy' else 'short',
                    'size': size,
                    'entry_price': current_price,
                    'leverage': leverage,
                    'pnl': 0,
                    'pnl_ratio': 0
                }
                return True
            
            # 真实交易模式
            self.total_orders += 1
            
            try:
                # 设置杠杆（如果exchange支持）
                if hasattr(self.exchange, 'set_leverage'):
                    self.exchange.set_leverage(self.symbol, leverage)
                
                # 下单
                side = 'buy' if action == 'buy' else 'sell'
                order = self.exchange.place_order(
                    symbol=self.symbol,
                    side=side,
                    size=size,  # 修复：参数名是size不是amount
                    order_type='market',
                    leverage=leverage
                )
                
                if order:
                    logger.info(f"   ✅ 订单成功: {order.get('id', 'N/A')}")
                    self.successful_orders += 1
                    
                    # 记录持仓
                    self.positions[agent_id] = {
                        'side': 'long' if action == 'buy' else 'short',
                        'size': size,
                        'entry_price': current_price,
                        'leverage': leverage,
                        'order_id': order.get('id'),
                        'pnl': 0,
                        'pnl_ratio': 0
                    }
                    return True
                else:
                    logger.error(f"   ❌ 订单失败：未返回订单信息")
                    self.failed_orders += 1
                    return False
                    
            except Exception as e:
                logger.error(f"   ❌ 下单异常: {e}")
                self.failed_orders += 1
                return False
                
        except Exception as e:
            logger.error(f"执行决策异常: {e}")
            return False
    
    def close_position(self, agent, current_price: float) -> bool:
        """平仓"""
        try:
            agent_id = agent.agent_id
            
            if agent_id not in self.positions:
                return False
            
            position = self.positions[agent_id]
            size = position['size']
            pnl_ratio = position.get('pnl_ratio', 0)
            
            if not self.enable_real_trading:
                # 模拟模式
                logger.info(f"   [模拟] 平仓 {size:.4f} BTC (PnL: {pnl_ratio:+.2%})")
                
                # 更新Agent资金（模拟盈亏）
                pnl_amount = agent.current_capital * pnl_ratio
                agent.current_capital += pnl_amount
                
                # 移除持仓
                del self.positions[agent_id]
                return True
            
            # 真实交易模式
            self.total_orders += 1
            
            try:
                # 平仓：如果是多仓就卖出，如果是空仓就买入
                side = 'sell' if position['side'] == 'long' else 'buy'
                
                order = self.exchange.place_order(
                    symbol=self.symbol,
                    side=side,
                    size=size,  # 修复：参数名是size不是amount
                    order_type='market'
                )
                
                if order:
                    logger.info(f"   ✅ 平仓成功 (PnL: {pnl_ratio:+.2%})")
                    self.successful_orders += 1
                    
                    # 更新Agent资金
                    pnl_amount = agent.current_capital * pnl_ratio
                    agent.current_capital += pnl_amount
                    
                    # 移除持仓
                    del self.positions[agent_id]
                    return True
                else:
                    logger.error(f"   ❌ 平仓失败")
                    self.failed_orders += 1
                    return False
                    
            except Exception as e:
                logger.error(f"   ❌ 平仓异常: {e}")
                self.failed_orders += 1
                return False
                
        except Exception as e:
            logger.error(f"平仓处理异常: {e}")
            return False
    
    def update_all_positions_pnl(self, current_price: float):
        """更新所有持仓的盈亏"""
        for agent_id, position in list(self.positions.items()):
            try:
                entry_price = position['entry_price']
                leverage = position['leverage']
                side = position['side']
                
                # 计算价格变化
                price_change = (current_price - entry_price) / entry_price
                
                # 计算盈亏（考虑杠杆和方向）
                if side == 'long':
                    pnl_ratio = price_change * leverage
                else:  # short
                    pnl_ratio = -price_change * leverage
                
                # 更新持仓信息
                position['pnl_ratio'] = pnl_ratio
                position['current_price'] = current_price
                
            except Exception as e:
                logger.error(f"更新持仓盈亏异常 {agent_id[:8]}: {e}")
    
    def run_evolution(self):
        """运行进化"""
        try:
            logger.info("🧬 开始进化...")
            
            # 淘汰资金为0的Agent
            self.moirai.agents = [
                a for a in self.moirai.agents 
                if a.current_capital > 0
            ]
            
            if len(self.moirai.agents) > 0:
                self.evolution_manager.run_evolution_cycle()
                logger.info(f"✅ 进化完成 - 当前种群: {len(self.moirai.agents)}个Agent")
            else:
                logger.warning("⚠️  没有存活的Agent，无法进化")
        
        except Exception as e:
            logger.error(f"进化异常: {e}")
    
    def log_status(self):
        """记录状态"""
        try:
            # 账户总价值
            account_value = self.exchange.get_account_value()
            
            # Agent统计
            agents = self.moirai.agents
            alive_count = sum(1 for a in agents if a.current_capital > 0)
            avg_capital = sum(a.current_capital for a in agents) / len(agents) if agents else 0
            
            # 持仓统计
            position_count = len(self.positions)
            
            logger.info(f"💰 账户总价值: ${account_value:,.2f}")
            logger.info(f"👥 存活Agent: {alive_count}/{len(agents)}")
            logger.info(f"📊 平均资金: ${avg_capital:,.2f}")
            logger.info(f"📈 当前持仓: {position_count}个")
            
        except Exception as e:
            logger.error(f"状态记录异常: {e}")

