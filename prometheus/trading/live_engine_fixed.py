#!/usr/bin/env python3
"""
实盘交易引擎 - 修复版
============

修复内容：
1. 降低决策阈值：0.1% → 0.01%
2. 启用决策日志（INFO级别）
3. 添加详细的决策过程记录
"""

import logging
import time
from typing import List, Dict
from datetime import datetime
from prometheus.exchange.okx_api import OKXExchange
from prometheus.core.moirai import Moirai
from prometheus.core.evolution_manager_v5 import EvolutionManagerV5

logger = logging.getLogger(__name__)


class LiveTradingEngine:
    """实盘交易引擎"""
    
    def __init__(
        self,
        exchange: OKXExchange,
        moirai: Moirai,
        evolution_manager: EvolutionManagerV5,
        symbol: str = 'BTC/USDT',
        interval: int = 60,  # 交易周期（秒）
        evolution_interval: int = 86400,  # 进化周期（秒），默认1天
        max_position_size: float = 0.01,  # 最大持仓（BTC）
        max_leverage: float = 10.0,  # 最大杠杆
    ):
        """
        初始化交易引擎
        
        Args:
            exchange: 交易所接口
            moirai: Moirai实例
            evolution_manager: 进化管理器
            symbol: 交易对
            interval: 交易周期（秒）
            evolution_interval: 进化周期（秒）
            max_position_size: 最大持仓
            max_leverage: 最大杠杆
        """
        self.exchange = exchange
        self.moirai = moirai
        self.evolution_manager = evolution_manager
        self.symbol = symbol
        self.interval = interval
        self.evolution_interval = evolution_interval
        self.max_position_size = max_position_size
        self.max_leverage = max_leverage
        
        self.running = False
        self.cycle_count = 0
        self.last_evolution_time = time.time()
        self.last_price = None
        
        logger.info(f"✅ 实盘交易引擎初始化完成")
        logger.info(f"   交易对: {symbol}")
        logger.info(f"   交易周期: {interval}秒")
        logger.info(f"   进化周期: {evolution_interval}秒 ({evolution_interval/3600:.1f}小时)")
        logger.info(f"   最大持仓: {max_position_size} BTC")
        logger.info(f"   最大杠杆: {max_leverage}x")
    
    def start(self):
        """启动交易引擎"""
        self.running = True
        logger.info("🚀 交易引擎启动")
        
        try:
            while self.running:
                self.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("⏹️  收到停止信号")
            self.stop()
        except Exception as e:
            logger.error(f"❌ 交易引擎异常: {e}")
            self.stop()
    
    def stop(self):
        """停止交易引擎"""
        self.running = False
        logger.info("⏹️  交易引擎已停止")
        
        # 平掉所有持仓（可选）
        # self.close_all_positions()
    
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
            
            # 3. 每个Agent做决策
            agents = self.moirai.agents
            logger.info(f"👥 活跃Agent数量: {len(agents)}")
            
            decision_count = 0
            buy_count = 0
            sell_count = 0
            hold_count = 0
            
            for agent in agents:
                if agent.current_capital <= 0:
                    continue
                
                # Agent决策
                decision = self.agent_make_decision(agent, price_change, current_price)
                
                # 执行决策
                if decision:
                    self.execute_decision(agent, decision, current_price)
                    decision_count += 1
                    
                    if decision['action'] == 'buy':
                        buy_count += 1
                    elif decision['action'] == 'sell':
                        sell_count += 1
                else:
                    hold_count += 1
            
            # FIX: 显示决策统计
            logger.info(f"📊 决策统计: {buy_count}买 / {sell_count}卖 / {hold_count}持有")
            if decision_count > 0:
                logger.info(f"✅ 本周期有 {decision_count} 个Agent做出交易决策！")
            
            # 4. 更新Agent资金（根据持仓盈亏）
            self.update_agent_capital(price_change)
            
            # 5. 检查是否需要进化
            if time.time() - self.last_evolution_time >= self.evolution_interval:
                self.run_evolution()
                self.last_evolution_time = time.time()
            
            # 6. 显示状态
            self.log_status()
            
        except Exception as e:
            logger.error(f"❌ 交易周期异常: {e}")
    
    def agent_make_decision(self, agent, price_change: float, current_price: float) -> Dict:
        """
        Agent做决策
        
        Returns:
            {
                'action': 'buy' / 'sell' / 'hold',
                'size': 0.01,  # BTC数量
                'leverage': 5.0
            }
        """
        try:
            risk_tolerance = getattr(agent.instinct, 'risk_tolerance', 0.5)
            
            # FIX: 降低决策阈值从0.1%到0.01%
            # 原来: if abs(price_change) < 0.001:
            # 现在: if abs(price_change) < 0.0001:
            if abs(price_change) < 0.0001:  # 0.01%
                action = 'hold'
                position = 0.0
            elif price_change > 0:
                action = 'buy'
                position = risk_tolerance * 0.8
            else:
                action = 'sell'
                position = risk_tolerance * 0.8
            
            if action == 'hold':
                return None
            
            # 计算交易数量
            # 根据Agent的资金比例计算
            account_value = self.exchange.get_account_value()
            agent_capital_ratio = agent.current_capital / (account_value if account_value > 0 else 1.0)
            
            # Agent应该持有的BTC数量
            size = min(
                position * agent_capital_ratio * self.max_position_size,
                self.max_position_size * 0.1  # 单次最多10%的最大持仓
            )
            
            if size < 0.0001:  # FIX: 降低最小交易量阈值
                return None
            
            # 杠杆选择
            leverage = min(1.0 + risk_tolerance * 9.0, self.max_leverage)
            
            return {
                'action': action,
                'size': size,
                'leverage': leverage
            }
        
        except Exception as e:
            logger.error(f"Agent决策异常: {e}")
            return None
    
    def execute_decision(self, agent, decision: Dict, current_price: float):
        """执行Agent决策"""
        try:
            action = decision['action']
            size = decision['size']
            leverage = decision['leverage']
            
            # FIX: 改为INFO级别，并添加更详细的信息
            logger.info(
                f"📝 Agent [{agent.agent_id[:8]}] 决策: "
                f"{action.upper()} {size:.4f} BTC @ {leverage:.1f}x "
                f"(资金: ${agent.current_capital:,.2f})"
            )
            
            # TODO: 实际下单（当前仅记录）
            # 如果要真实下单，取消注释以下代码：
            # order = self.exchange.place_order(
            #     symbol=self.symbol,
            #     side=action,
            #     size=size,
            #     leverage=leverage
            # )
            # logger.info(f"✅ 订单已提交: {order}")
            
        except Exception as e:
            logger.error(f"执行决策异常: {e}")
    
    def update_agent_capital(self, price_change: float):
        """根据价格变化更新Agent资金"""
        # 简化：假设所有Agent按比例持仓
        # 实际应该根据真实持仓计算
        for agent in self.moirai.agents:
            if agent.current_capital > 0:
                # 简化：假设10%资金持仓，10x杠杆
                exposure = 0.1
                leverage = 10.0
                return_rate = price_change * exposure * leverage
                
                # 限制单次最大盈亏
                return_rate = max(-0.5, min(0.5, return_rate))
                
                agent.current_capital *= (1 + return_rate)
    
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
            
            logger.info(f"💰 账户总价值: ${account_value:,.2f}")
            logger.info(f"👥 存活Agent: {alive_count}/{len(agents)}")
            logger.info(f"📊 平均资金: ${avg_capital:,.2f}")
            
        except Exception as e:
            logger.error(f"状态记录异常: {e}")
    
    def close_all_positions(self):
        """平掉所有持仓"""
        try:
            logger.info("📴 平掉所有持仓...")
            self.exchange.close_position(self.symbol)
        except Exception as e:
            logger.error(f"平仓异常: {e}")


def main():
    """测试实盘交易引擎"""
    import sys
    sys.path.insert(0, '.')
    
    # 初始化组件
    exchange = OKXExchange(paper_trading=True)
    moirai = Moirai()
    evolution_manager = EvolutionManagerV5(moirai=moirai)
    evolution_manager.immigration_enabled = False
    
    # 创建初始Agent
    agents = moirai._genesis_create_agents(
        agent_count=10,
        gene_pool=[],
        capital_per_agent=10000.0
    )
    for agent in agents:
        agent.fitness = 1.0
    moirai.agents = agents
    
    # 创建交易引擎
    engine = LiveTradingEngine(
        exchange=exchange,
        moirai=moirai,
        evolution_manager=evolution_manager,
        symbol='BTC/USDT',
        interval=10,  # 10秒一个周期（测试用）
        evolution_interval=60,  # 1分钟进化一次（测试用）
    )
    
    # 启动
    print("\n启动测试（按Ctrl+C停止）...\n")
    engine.start()


if __name__ == "__main__":
    main()

