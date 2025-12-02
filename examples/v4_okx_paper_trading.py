"""
Prometheus v4.0 - OKX模拟盘实盘测试

连接OKX模拟盘进行真实市场环境测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置UTF-8编码（Windows兼容）
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

from prometheus.core import (
    Mastermind, Supervisor, AgentV4,
    BulletinBoardV4, TradingPermissionSystem, PermissionLevel,
    Valhalla, MedalSystem, AgentPersonality, EmotionalState
)


class TeeOutput:
    """同时输出到控制台和文件的包装器"""
    def __init__(self, file_path):
        self.terminal = sys.stdout
        self.log = open(file_path, 'w', encoding='utf-8')
        self.start_time = datetime.now()
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.write(f"\n\n{'='*70}\n")
        self.log.write(f"测试结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        self.log.write(f"总运行时长: {duration:.2f}分钟\n")
        self.log.write(f"{'='*70}\n")
        self.log.close()


class OKXPaperTrading:
    """OKX模拟盘交易接口"""
    
    def __init__(self, api_key: str, api_secret: str, passphrase: str):
        """
        初始化OKX模拟盘连接
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            passphrase: API密码
        """
        print("\n" + "="*70)
        print("  🔗 连接OKX模拟盘")
        print("="*70)
        
        # 初始化交易所（模拟盘模式）
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,
            'enableRateLimit': True,
            'sandbox': True,  # ← 关键配置：启用sandbox模式
            'options': {
                'defaultType': 'swap',  # 永续合约
            }
        })
        
        print("   ✅ 模拟盘模式: Sandbox已启用")
        
        print("✅ OKX模拟盘连接成功")
        
        # 测试连接
        try:
            balance = self.exchange.fetch_balance()
            print(f"   模拟账户余额: {balance['USDT']['free']:.2f} USDT")
        except Exception as e:
            print(f"⚠️  获取余额失败: {e}")
    
    def fetch_current_price(self, symbol='BTC/USDT:USDT'):
        """获取当前价格"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"⚠️  获取价格失败: {e}")
            return None
    
    def fetch_recent_klines(self, symbol='BTC/USDT:USDT', timeframe='1m', limit=100):
        """获取最近K线数据"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"⚠️  获取K线失败: {e}")
            return None
    
    def place_market_order(self, symbol='BTC/USDT:USDT', side='buy', amount=0.001, reduce_only=False, pos_side=None):
        """
        下市价单（OKX永续合约）
        
        Args:
            symbol: 交易对
            side: 'buy' or 'sell'
            amount: 数量（BTC）
            reduce_only: 是否仅平仓（不开新仓）
            pos_side: 持仓方向 ('long' or 'short')，仅平仓时需要
        """
        try:
            # OKX永续合约必需参数
            if reduce_only and pos_side:
                # 平仓模式：明确指定持仓方向
                params = {
                    'tdMode': 'cross',  # 全仓模式
                    'posSide': pos_side,  # 使用传入的持仓方向
                    'reduceOnly': True    # 仅平仓，不开新仓
                }
            else:
                # 开仓模式：根据side推断方向
                params = {
                    'tdMode': 'cross',  # 全仓模式
                    'posSide': 'long' if side == 'buy' else 'short'  # 持仓方向
                }
            
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=amount,
                params=params
            )
            action = "平仓" if reduce_only else "开仓"
            print(f"✅ 订单成功: {action} {side.upper()} {amount} {symbol}")
            return order
        except Exception as e:
            print(f"❌ 订单失败: {e}")
            return None
    
    def place_limit_order(self, symbol='BTC/USDT:USDT', side='buy', 
                         amount=0.001, price=50000):
        """
        下限价单
        
        Args:
            symbol: 交易对
            side: 'buy' or 'sell'
            amount: 数量
            price: 价格
        """
        try:
            order = self.exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=amount,
                price=price
            )
            print(f"✅ 限价单: {side.upper()} {amount} @ ${price}")
            return order
        except Exception as e:
            print(f"❌ 订单失败: {e}")
            return None
    
    def get_positions(self):
        """获取当前持仓"""
        try:
            positions = self.exchange.fetch_positions()
            # 严格过滤：只返回真正有持仓的（contracts > 0.001）
            return [p for p in positions if abs(float(p['contracts'])) > 0.001]
        except Exception as e:
            print(f"⚠️  获取持仓失败: {e}")
            return []
    
    def close_position(self, symbol='BTC/USDT:USDT'):
        """平仓（使用reduceOnly模式）"""
        try:
            positions = self.get_positions()
            for pos in positions:
                if pos['symbol'] == symbol:
                    pos_side = pos['side']  # 持仓方向
                    close_side = 'sell' if pos_side == 'long' else 'buy'
                    amount = abs(float(pos['contracts']))
                    return self.place_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=amount,
                        reduce_only=True,    # 仅平仓
                        pos_side=pos_side    # 明确持仓方向
                    )
            return None
        except Exception as e:
            print(f"❌ 平仓失败: {e}")
            return None
    
    def close_all_positions(self):
        """强制清理所有持仓和挂单"""
        print("\n" + "="*70)
        print("  🔄 全面清理：检查持仓、挂单、历史委托")
        print("="*70)
        
        all_clean = True
        
        try:
            # 1. 检查并取消所有挂单
            print("\n【第1步】检查挂单...")
            try:
                open_orders = self.exchange.fetch_open_orders()
                if open_orders:
                    print(f"⚠️  发现 {len(open_orders)} 个挂单，开始取消...")
                    cancelled_count = 0
                    for order in open_orders:
                        try:
                            self.exchange.cancel_order(order['id'], order['symbol'])
                            print(f"   ✅ 取消挂单: {order['symbol']} | {order['side'].upper()} | {order['amount']}")
                            cancelled_count += 1
                        except Exception as e:
                            print(f"   ❌ 取消失败: {e}")
                            all_clean = False
                    print(f"   取消挂单: {cancelled_count}/{len(open_orders)}")
                else:
                    print("   ✅ 无挂单")
            except Exception as e:
                print(f"   ⚠️  检查挂单失败: {e}")
            
            # 2. 检查当前持仓
            print("\n【第2步】检查持仓...")
            positions = self.get_positions()
            
            if not positions:
                print("   ✅ 无持仓")
            else:
                print(f"⚠️  发现 {len(positions)} 个持仓，开始平仓...")
                
                closed_count = 0
                for pos in positions:
                    symbol = pos['symbol']
                    side = pos['side']
                    contracts = abs(float(pos['contracts']))
                    unrealized_pnl = pos.get('unrealizedPnl', 0)
                    
                    print(f"\n   持仓详情:")
                    print(f"      币种: {symbol}")
                    print(f"      方向: {side.upper()}")
                    print(f"      数量: {contracts} 张")
                    if unrealized_pnl:
                        print(f"      浮盈: ${float(unrealized_pnl):.2f}")
                    
                    # 平仓（使用reduceOnly模式）
                    close_side = 'sell' if side == 'long' else 'buy'
                    order = self.place_market_order(
                        symbol=symbol,
                        side=close_side,
                        amount=contracts,
                        reduce_only=True,      # 仅平仓
                        pos_side=side          # 明确指定持仓方向
                    )
                    
                    if order:
                        closed_count += 1
                        print(f"   ✅ 平仓成功")
                    else:
                        print(f"   ❌ 平仓失败")
                        all_clean = False
                
                print(f"\n   平仓完成: {closed_count}/{len(positions)}")
            
            # 3. 等待订单完成
            if closed_count > 0:
                print("\n   ⏳ 等待3秒，确保平仓完成...")
                import time
                time.sleep(3)
            
            # 4. 再次确认状态
            print("\n【第3步】最终确认...")
            final_positions = self.get_positions()
            final_orders = self.exchange.fetch_open_orders()
            
            if not final_positions and not final_orders:
                print("   ✅ 确认：账户状态干净")
            else:
                if final_positions:
                    print(f"   ⚠️  仍有 {len(final_positions)} 个持仓")
                    all_clean = False
                if final_orders:
                    print(f"   ⚠️  仍有 {len(final_orders)} 个挂单")
                    all_clean = False
            
            print(f"\n{'='*70}")
            if all_clean:
                print("  ✅ 清理完成：账户状态干净")
            else:
                print("  ⚠️  清理完成：部分项目未能清理")
            print("="*70)
            
            return all_clean
            
        except Exception as e:
            print(f"❌ 清理过程失败: {e}")
            print("="*70)
            return False


class PrometheusLiveTrading:
    """Prometheus实盘交易系统"""
    
    def __init__(self, okx_trader: OKXPaperTrading, log_file=None):
        print("\n" + "="*70)
        print("  Prometheus v4.0 - OKX模拟盘实盘测试")
        print("="*70)
        
        if log_file:
            print(f"  📝 日志文件: {log_file}")
            print("="*70)
        
        self.okx = okx_trader
        
        # 初始化前先清理所有持仓
        self.okx.close_all_positions()
        
        # 初始化系统组件
        self.bulletin_board = BulletinBoardV4()
        self.mastermind = Mastermind(
            initial_capital=100000.0,
            decision_mode="human",
            bulletin_board=self.bulletin_board
        )
        self.supervisor = Supervisor(bulletin_board=self.bulletin_board)
        
        # 创建Agent群体
        self.agents = self._create_agent_population(count=10)  # 10个创世Agent
        
        # 系统组件
        self.permission_system = TradingPermissionSystem()
        self.valhalla = Valhalla()
        self.medal_system = MedalSystem()
        
        # 统计数据
        self.stats = {
            'total_signals': 0,
            'executed_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
        }
        
        # 当前持仓
        self.current_position = None
        
        # 当前市场状态（供agents决策使用）
        self.current_market_state = {'trend': '震荡', 'change_pct': 0}
        
        # 完整的交易历史记录
        self.trade_history = []  # 每笔交易的完整信息
        self.signal_history = []  # 每次信号的完整信息
        
        # ===== 架构升级：Supervisor成为完整运营系统 =====
        
        # 1. 注入OKX交易接口到Supervisor
        self.supervisor.set_okx_trading(self.okx)
        
        # 2. 初始化Supervisor的虚拟账户系统
        initial_capital_per_agent = 10000
        self.supervisor.initialize_virtual_accounts(self.agents, initial_capital_per_agent)
        
        # 3. 初始化Supervisor的实际持仓跟踪系统
        self.supervisor.initialize_agent_real_positions(self.agents)
        
        print("✅ Prometheus系统初始化完成")
        print(f"   💼 Supervisor完整运营系统已就绪：")
        print(f"      - 管理{len(self.agents)}个Agent虚拟账户（每个{initial_capital_per_agent} USDT）")
        print(f"      - 跟踪{len(self.agents)}个Agent实际持仓")
        print(f"      - 拥有交易执行权限")
    
    def _create_agent_population(self, count=5):
        """创建Agent群体"""
        agents = []
        
        personality_profiles = [
            {'optimism': 0.8, 'discipline': 0.3, 'adaptability': 0.7, 'risk_tolerance': 0.9},  # 1. 激进型
            {'optimism': 0.4, 'discipline': 0.9, 'adaptability': 0.5, 'risk_tolerance': 0.2},  # 2. 保守型
            {'optimism': 0.6, 'discipline': 0.6, 'adaptability': 0.6, 'risk_tolerance': 0.5},  # 3. 平衡型
            {'optimism': 0.5, 'discipline': 0.5, 'adaptability': 0.9, 'risk_tolerance': 0.6},  # 4. 灵活型
            {'optimism': 0.3, 'discipline': 0.8, 'adaptability': 0.4, 'risk_tolerance': 0.3},  # 5. 谨慎型
            {'optimism': 0.9, 'discipline': 0.4, 'adaptability': 0.8, 'risk_tolerance': 0.95}, # 6. 极端激进
            {'optimism': 0.7, 'discipline': 0.7, 'adaptability': 0.8, 'risk_tolerance': 0.7},  # 7. 积极适应
            {'optimism': 0.2, 'discipline': 0.95, 'adaptability': 0.3, 'risk_tolerance': 0.1}, # 8. 极端保守
            {'optimism': 0.5, 'discipline': 0.4, 'adaptability': 0.95, 'risk_tolerance': 0.8}, # 9. 超级灵活
            {'optimism': 0.6, 'discipline': 0.5, 'adaptability': 0.7, 'risk_tolerance': 0.65}, # 10. 稳健进取
        ]
        
        for i in range(count):
            profile = personality_profiles[i % len(personality_profiles)]
            
            gene = {
                'risk_preference': np.random.uniform(0.3, 0.8),
                'trend_following': np.random.uniform(0.4, 0.9),
                'contrarian': np.random.uniform(0.2, 0.6),
                'patience': np.random.uniform(0.3, 0.8),
                'aggression': np.random.uniform(0.3, 0.7),
                'learning_rate': np.random.uniform(0.4, 0.9),
                'adaptability': np.random.uniform(0.5, 0.9),
                'max_position_size': np.random.uniform(0.2, 0.5),
                'stop_loss': np.random.uniform(0.02, 0.05),
                'take_profit': np.random.uniform(0.03, 0.08)
            }
            
            personality = AgentPersonality(**profile)
            
            agent = AgentV4(
                agent_id=f"LiveAgent_{i+1:02d}",
                gene=gene,
                personality=personality,
                initial_capital=10000,  # 每个Agent 10000 USDT虚拟资金
                bulletin_board=self.bulletin_board
            )
            
            agents.append(agent)
        
        return agents
    
    def run_live_test(self, duration_minutes=None, check_interval=60):
        """
        运行实盘测试
        
        Args:
            duration_minutes: 测试时长（分钟），None表示不限时
            check_interval: 检查间隔（秒）
        """
        start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f'okx_live_test_{start_timestamp}.txt'
        
        print(f"\n📝 日志将保存到: {log_filename}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if duration_minutes is None:
            print(f"测试时长: 不限时 (按Ctrl+C停止)")
        else:
            print(f"测试时长: {duration_minutes}分钟")
        print(f"检查间隔: {check_interval}秒")
        print("\n" + "="*70)
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
        cycle_count = 0
        
        try:
            while True:
                # 检查是否超时（如果有设置时长）
                if end_time and datetime.now() >= end_time:
                    print("\n⏰ 测试时间已到，正常结束")
                    break
                cycle_count += 1
                current_time = datetime.now()
                
                print(f"\n{'='*70}")
                print(f"  🔄 周期 {cycle_count} | {current_time.strftime('%H:%M:%S')}")
                print(f"{'='*70}")
                
                # 1. 获取市场数据
                market_data = self._fetch_market_data()
                if market_data is None or len(market_data) < 25:
                    print("⚠️  市场数据不足，等待下一周期...")
                    time.sleep(check_interval)
                    continue
                
                current_price = market_data['close'].iloc[-1]
                print(f"\n📊 当前价格: ${current_price:.2f}")
                
                # 2. Supervisor分析市场
                market_state = self._supervisor_analysis(market_data)
                
                # 3. Mastermind战略决策（每5个周期）
                if cycle_count % 5 == 0:
                    self._mastermind_strategy(market_data, market_state)
                
                # 4. Agent自主决策并执行（新模式）
                self._agents_autonomous_decide_and_execute(market_data, current_price)
                
                # 5. Supervisor更新虚拟盈亏
                self.supervisor.calculate_unrealized_pnl(current_price)
                
                # 6. Supervisor发布Agent表现报告（每5个周期）
                if cycle_count % 5 == 0:
                    self.supervisor.publish_agent_performance_report()
                    self.supervisor.print_performance_summary()
                
                # 7. 更新统计
                self._update_statistics()
                
                # 8. 显示实时状态
                self._print_status()
                
                # 等待下一周期
                print(f"\n⏸️  等待 {check_interval}秒...")
                time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被用户中断")
        
        # 最终总结
        self._print_final_summary()
    
    def _fetch_market_data(self):
        """获取市场数据"""
        return self.okx.fetch_recent_klines(
            symbol='BTC/USDT:USDT',
            timeframe='1m',
            limit=100
        )
    
    def _supervisor_analysis(self, market_data):
        """Supervisor市场分析"""
        print("\n👁️  【Supervisor】市场分析")
        
        # 简化的市场状态分析
        price_change = (market_data['close'].iloc[-1] - market_data['close'].iloc[0]) / market_data['close'].iloc[0]
        volatility = market_data['close'].pct_change().std()
        
        trend = "上涨" if price_change > 0.01 else ("下跌" if price_change < -0.01 else "震荡")
        
        market_state = {
            'trend': trend,
            'price_change': price_change * 100,
            'change_pct': price_change * 100,  # 添加change_pct字段
            'volatility': volatility,
            'difficulty': min(0.9, 0.5 + volatility * 10),
        }
        
        # 存储当前市场状态供agents使用
        self.current_market_state = market_state
        
        print(f"   趋势: {trend}")
        print(f"   涨跌幅: {price_change*100:.2f}%")
        print(f"   波动率: {volatility:.4f}")
        
        # 发布市场公告
        try:
            self.supervisor.comprehensive_monitoring(market_data)
        except:
            pass
        
        return market_state
    
    def _mastermind_strategy(self, market_data, market_state):
        """Mastermind战略决策"""
        print("\n🧠 【Mastermind】战略决策")
        
        if market_state['trend'] == "上涨":
            strategy = "aggressive"
            message = "市场上涨趋势，可适度做多"
        elif market_state['trend'] == "下跌":
            strategy = "conservative"
            message = "市场下跌，寻找做空或抄底机会"
        else:
            strategy = "balanced"
            # 震荡市场改为鼓励高抛低吸
            volatility = market_state.get('volatility', 0)
            if volatility > 0.001:
                message = "市场震荡但有波动，可以高抛低吸"
            else:
                message = "市场震荡波动小，等待突破机会"
        
        # 发布战略公告
        self.bulletin_board.post(
            publisher="Mastermind",
            tier="strategic",
            title=f"战略调整：{strategy}",
            content=message,
            priority="high"
        )
        
        print(f"   战略: {strategy}")
        print(f"   指导: {message}")
    
    def _agents_decide(self, market_data):
        """Agent自主决策（每个Agent独立判断）"""
        print("\n🤖 【Agents】自主决策")
        
        signals = []
        decisions_detail = []
        
        for agent in self.agents:
            try:
                # Agent读取公告并决策
                decision = agent.process_bulletins_and_decide()
                
                # 记录决策详情（调试用）
                decisions_detail.append({
                    'agent': agent.agent_id,
                    'decision': decision.get('decision', 'unknown'),
                    'action': decision.get('action', 'hold'),
                    'confidence': decision.get('confidence', 0)
                })
                
                if decision.get('decision') == 'bulletin_guided':
                    action = decision.get('action', 'hold')
                    confidence = decision.get('confidence', 0.5)
                    
                    # 根据市场状态和action生成交易信号
                    # 使用当前市场状态
                    trend_str = self.current_market_state.get('trend', '震荡')
                    change_pct = self.current_market_state.get('change_pct', 0)
                    
                    # 转换趋势为英文标识
                    if trend_str == '上涨':
                        market_trend = 'uptrend'
                    elif trend_str == '下跌':
                        market_trend = 'downtrend'
                    else:
                        market_trend = 'sideways'
                    
                    # 买入信号：明确的开多动作 或 在下跌时分析机会
                    if action in ['open_long', 'increase_position']:
                        signals.append({
                            'agent_id': agent.agent_id,
                            'signal': 'buy',
                            'confidence': confidence
                        })
                    # 在下跌趋势中，analyze_opportunity可能是抄底机会
                    elif action == 'analyze_opportunity' and market_trend == 'downtrend' and confidence > 0.6:
                        signals.append({
                            'agent_id': agent.agent_id,
                            'signal': 'buy',
                            'confidence': confidence * 0.8  # 降低信心度
                        })
                    
                    # 卖出信号：明确的开空/平仓动作 或 在上涨时减少风险
                    elif action in ['open_short', 'close_position']:
                        signals.append({
                            'agent_id': agent.agent_id,
                            'signal': 'sell',
                            'confidence': confidence
                        })
                    # 在上涨趋势中，reduce_risk可能是止盈信号
                    elif action == 'reduce_risk' and market_trend == 'uptrend' and confidence > 0.7:
                        signals.append({
                            'agent_id': agent.agent_id,
                            'signal': 'sell',
                            'confidence': confidence * 0.8  # 降低信心度
                        })
                    
                    # adjust_strategy：根据市场趋势调整（更激进）
                    elif action == 'adjust_strategy':
                        if market_trend == 'uptrend' and confidence > 0.6:
                            # 上涨趋势：顺势做多
                            signals.append({
                                'agent_id': agent.agent_id,
                                'signal': 'buy',
                                'confidence': confidence * 0.8  # 提高信心度权重
                            })
                        elif market_trend == 'downtrend' and confidence > 0.6:
                            # 下跌趋势：顺势做空或平仓
                            signals.append({
                                'agent_id': agent.agent_id,
                                'signal': 'sell',
                                'confidence': confidence * 0.8  # 提高信心度权重
                            })
                        elif market_trend == 'sideways':
                            # 震荡市场：优先低吸建仓，再考虑高抛
                            # 策略1：下跌时买入（降低门槛，更容易触发）
                            if change_pct < -0.2 and confidence > 0.6:  # 从-0.5降到-0.2
                                signals.append({
                                    'agent_id': agent.agent_id,
                                    'signal': 'buy',
                                    'confidence': confidence * 0.7  # 提高信心度
                                })
                            # 策略2：横盘也可以买入（极小波动时建仓）
                            elif abs(change_pct) < 0.3 and confidence > 0.75:
                                signals.append({
                                    'agent_id': agent.agent_id,
                                    'signal': 'buy',
                                    'confidence': confidence * 0.6
                                })
                            # 策略3：上涨时考虑卖出（提高门槛，避免无持仓卖出）
                            elif change_pct > 0.8 and confidence > 0.75:  # 从0.5提高到0.8
                                signals.append({
                                    'agent_id': agent.agent_id,
                                    'signal': 'sell',
                                    'confidence': confidence * 0.7  # 提高信心度
                                })
            except Exception as e:
                decisions_detail.append({
                    'agent': agent.agent_id,
                    'error': str(e)
                })
        
        # 显示详细决策（前3个Agent）
        print("   Agent决策详情（示例）:")
        for detail in decisions_detail[:3]:
            if 'error' in detail:
                print(f"      {detail['agent']}: 错误 - {detail['error']}")
            else:
                print(f"      {detail['agent']}: {detail['decision']} → {detail['action']} (信心:{detail['confidence']:.2f})")
        
        if signals:
            buy_signals = [s for s in signals if s['signal'] == 'buy']
            sell_signals = [s for s in signals if s['signal'] == 'sell']
            
            print(f"   信号统计: {len(buy_signals)}买 / {len(sell_signals)}卖")
            
            self.stats['total_signals'] += len(signals)
        else:
            print("   无交易信号")
        
        return signals
    
    def _agents_autonomous_decide_and_execute(self, market_data, current_price):
        """
        Agent自主决策并执行（方案A：简化版）
        
        每个Agent独立决策，虚拟统计表现，实际只执行代表性交易
        """
        print("\n🤖 【Agents】自主决策模式")
        
        # 收集每个Agent的独立决策
        agent_decisions = []
        buy_agents = []
        sell_agents = []
        hold_agents = []
        
        for agent in self.agents:
            try:
                # Agent独立决策
                decision = agent.process_bulletins_and_decide()
                
                if decision.get('decision') == 'bulletin_guided':
                    action = decision.get('action', 'hold')
                    confidence = decision.get('confidence', 0.5)
                    
                    # 判断该Agent是否想交易
                    trend_str = self.current_market_state.get('trend', '震荡')
                    change_pct = self.current_market_state.get('change_pct', 0)
                    
                    if trend_str == '上涨':
                        market_trend = 'uptrend'
                    elif trend_str == '下跌':
                        market_trend = 'downtrend'
                    else:
                        market_trend = 'sideways'
                    
                    # 该Agent的交易意愿
                    trade_signal = None
                    
                    # 判断逻辑（与之前相同）
                    if action in ['open_long', 'increase_position']:
                        trade_signal = 'buy'
                    elif action == 'analyze_opportunity' and market_trend == 'downtrend' and confidence > 0.6:
                        trade_signal = 'buy'
                    elif action in ['open_short', 'close_position']:
                        trade_signal = 'sell'
                    elif action == 'reduce_risk' and market_trend == 'uptrend' and confidence > 0.7:
                        trade_signal = 'sell'
                    elif action == 'adjust_strategy':
                        if market_trend == 'uptrend' and confidence > 0.6:
                            trade_signal = 'buy'
                        elif market_trend == 'downtrend' and confidence > 0.6:
                            trade_signal = 'sell'
                        elif market_trend == 'sideways':
                            if change_pct < -0.2 and confidence > 0.6:
                                trade_signal = 'buy'
                            elif abs(change_pct) < 0.3 and confidence > 0.75:
                                trade_signal = 'buy'
                            elif change_pct > 0.8 and confidence > 0.75:
                                trade_signal = 'sell'
                    
                    # 记录Agent决策
                    agent_decision = {
                        'agent_id': agent.agent_id,
                        'action': action,
                        'confidence': confidence,
                        'signal': trade_signal,
                        'personality': agent.personality
                    }
                    agent_decisions.append(agent_decision)
                    
                    # 分类统计
                    if trade_signal == 'buy':
                        buy_agents.append(agent_decision)
                    elif trade_signal == 'sell':
                        sell_agents.append(agent_decision)
                    else:
                        hold_agents.append(agent_decision)
                        
            except Exception as e:
                print(f"   ⚠️  {agent.agent_id} 决策失败: {e}")
        
        # 显示每个Agent的决策
        print(f"\n   📊 Agent决策分布:")
        print(f"      🟢 做多: {len(buy_agents)}个Agent")
        print(f"      🔴 做空/平仓: {len(sell_agents)}个Agent")
        print(f"      ⚪ 观望: {len(hold_agents)}个Agent")
        
        # 显示代表性决策
        print(f"\n   📋 代表性Agent决策:")
        for i, decision in enumerate(agent_decisions[:5], 1):
            signal_icon = "🟢" if decision['signal'] == 'buy' else ("🔴" if decision['signal'] == 'sell' else "⚪")
            signal_text = decision['signal'] or 'hold'
            print(f"      {signal_icon} {decision['agent_id']}: {decision['action']} → {signal_text} (信心:{decision['confidence']:.2f})")
        
        if len(agent_decisions) > 5:
            print(f"      ... 还有{len(agent_decisions)-5}个Agent")
        
        # ===== 新架构：Agent提交请求给Supervisor =====
        
        print(f"\n💼 【交易执行】Agent → Supervisor模式")
        
        executed_count = 0
        for decision in agent_decisions:
            agent_id = decision['agent_id']
            signal = decision['signal']
            confidence = decision['confidence']
            
            if signal:  # 有交易信号
                # Agent提交交易请求给Supervisor
                success = self.supervisor.receive_trade_request(
                    agent_id=agent_id,
                    signal=signal,
                    confidence=confidence,
                    current_price=current_price
                )
                
                if success:
                    executed_count += 1
        
        if executed_count == 0:
            print(f"   ⏸️  本周期无Agent交易")
        else:
            print(f"   ✅ Supervisor执行了{executed_count}笔交易")
    
    def _execute_virtual_trades(self, agent_decisions, current_price):
        """
        【已废弃】执行虚拟交易
        
        现在虚拟交易由Supervisor.receive_trade_request()统一处理
        保留此方法仅用于向后兼容
        """
        # 已废弃，虚拟交易现在在Supervisor.receive_trade_request中处理
        pass
    
    def _agent_independent_trade(self, agent_id, signal, confidence, current_price):
        """
        【已废弃】单个Agent独立执行实际交易
        
        现在由Supervisor.receive_trade_request()统一处理
        保留此方法仅用于向后兼容
        """
        # 已废弃，现在由Supervisor执行交易
        pass
    
    def _agent_independent_trade_deprecated(self, agent_id, signal, confidence, current_price):
        """【备份】原实现（已废弃）"""
        # 获取该Agent的本地持仓状态
        agent_pos = self.agent_positions.get(agent_id, {'has_position': False})
        
        if signal == 'buy':
            # 检查该Agent是否已有持仓（本地状态）
            if not agent_pos['has_position']:
                # Agent独立开仓
                amount = 0.01  # 每个Agent固定 0.01 BTC（OKX最小精度）
                order = self.okx.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='buy',
                    amount=amount,
                    reduce_only=False,
                    pos_side='long'
                )
                
                if order:
                    # 更新本地持仓状态
                    self.agent_positions[agent_id] = {
                        'has_position': True,
                        'amount': amount,
                        'entry_price': current_price,
                        'entry_time': datetime.now()
                    }
                    print(f"      ✅ {agent_id}: 实际开多 {amount} BTC (信心:{confidence:.2f})")
                    self.stats['executed_trades'] += 1
            else:
                print(f"      ⏸️  {agent_id}: 已有持仓，跳过")
        
        elif signal == 'sell':
            # 检查该Agent是否有持仓（本地状态）
            if agent_pos['has_position']:
                # Agent独立平仓
                amount = agent_pos['amount']
                
                order = self.okx.place_market_order(
                    symbol='BTC/USDT:USDT',
                    side='sell',
                    amount=amount,
                    reduce_only=True,
                    pos_side='long'
                )
                
                if order:
                    # 计算盈亏
                    pnl = (current_price - agent_pos['entry_price']) * amount
                    
                    # 更新本地持仓状态
                    self.agent_positions[agent_id] = {
                        'has_position': False,
                        'amount': 0,
                        'entry_price': 0,
                        'entry_time': None
                    }
                    
                    print(f"      ✅ {agent_id}: 实际平仓 {amount} BTC (信心:{confidence:.2f}, 盈亏:${pnl:.2f})")
                    self.stats['executed_trades'] += 1
                    
                    # 更新系统盈亏统计
                    self.stats['total_pnl'] += pnl
                    if pnl > 0:
                        self.stats['successful_trades'] += 1
                    else:
                        self.stats['failed_trades'] += 1
            else:
                print(f"      ⏸️  {agent_id}: 无持仓，跳过")
    
    def _execute_representative_trade(self, buy_agents, sell_agents, current_price):
        """
        【已废弃】执行代表性交易
        
        此方法已被完全自主模式取代。
        现在每个Agent独立执行实际交易，不再需要"代表性交易"。
        
        保留此方法仅用于向后兼容或紧急回退。
        """
        # 已废弃，不再执行
        pass
    
    def _execute_representative_trade_deprecated(self, buy_agents, sell_agents, current_price):
        """
        【备份】原代表性交易逻辑（已废弃）
        
        如需回退到代表性交易模式，可恢复此逻辑。
        """
        print("\n💼 【代表性交易执行】")
        
        # 检查当前持仓
        positions = self.okx.get_positions()
        has_position = len(positions) > 0
        
        # 统计
        buy_count = len(buy_agents)
        sell_count = len(sell_agents)
        total_agents = len(self.agents)
        
        # 开仓：只要有Agent支持（哪怕1个）
        if buy_count > 0 and not has_position:
            avg_confidence = sum(a['confidence'] for a in buy_agents) / buy_count
            
            print(f"   🟢 {buy_count}/{total_agents}个Agent支持做多")
            print(f"   平均信心: {avg_confidence:.2f}")
            
            # 执行1笔代表性买入
            amount = 0.01
            order = self.okx.place_market_order('BTC/USDT:USDT', 'buy', amount)
            
            if order:
                print(f"   ✅ 代表性订单: BUY {amount} BTC")
                self.stats['executed_trades'] += 1
                self.current_position = {
                    'side': 'long',
                    'entry_price': current_price,
                    'amount': amount,
                    'time': datetime.now()
                }
        
        # 平仓：只要有Agent支持（哪怕1个）
        elif sell_count > 0 and has_position:
            avg_confidence = sum(a['confidence'] for a in sell_agents) / sell_count
            
            print(f"   🔴 {sell_count}/{total_agents}个Agent支持平仓")
            print(f"   平均信心: {avg_confidence:.2f}")
            
            # 执行平仓
            order = self.okx.close_position('BTC/USDT:USDT')
            
            if order and self.current_position:
                pnl = (current_price - self.current_position['entry_price']) * self.current_position['amount']
                self.stats['total_pnl'] += pnl
                
                if pnl > 0:
                    self.stats['successful_trades'] += 1
                    print(f"   ✅ 盈利: ${pnl:.2f}")
                else:
                    self.stats['failed_trades'] += 1
                    print(f"   ❌ 亏损: ${pnl:.2f}")
                
                self.current_position = None
        
        else:
            # 无交易信号
            if has_position:
                print(f"   ⏸️  持仓中，暂无平仓信号 (做多:{buy_count} 平仓:{sell_count})")
            else:
                print(f"   ⏸️  观望中，暂无开仓信号 (做多:{buy_count} 平仓:{sell_count})")
    
    def _execute_consensus_trade(self, signals, current_price):
        """执行共识交易"""
        print("\n💼 【交易执行】")
        
        # 统计买卖信号
        buy_signals = [s for s in signals if s['signal'] == 'buy']
        sell_signals = [s for s in signals if s['signal'] == 'sell']
        
        buy_confidence = sum(s['confidence'] for s in buy_signals) / len(signals) if signals else 0
        sell_confidence = sum(s['confidence'] for s in sell_signals) / len(signals) if signals else 0
        
        # 决策阈值：进一步降低以便测试（生产环境应提高）
        threshold = 0.3        # 降到0.3，更容易触发
        support_ratio = 0.2    # 降到0.2，只需20%支持（1个agent就能触发）
        
        # 检查当前持仓
        positions = self.okx.get_positions()
        has_position = len(positions) > 0
        
        if len(buy_signals) / len(self.agents) > support_ratio and buy_confidence > threshold:
            if not has_position:
                print(f"   🟢 共识：做多 (信心度: {buy_confidence:.2f})")
                print(f"   支持Agent: {len(buy_signals)}/{len(self.agents)}")
                
                # 执行买入
                amount = 0.01  # 0.01 BTC (OKX最小精度要求)
                order = self.okx.place_market_order('BTC/USDT:USDT', 'buy', amount)
                
                if order:
                    self.stats['executed_trades'] += 1
                    trade_time = datetime.now()
                    
                    # 记录持仓信息
                    self.current_position = {
                        'side': 'long',
                        'entry_price': current_price,
                        'amount': amount,
                        'time': trade_time,
                        'trade_id': len(self.trade_history) + 1,
                        'supporting_agents': [s['agent_id'] for s in buy_signals]
                    }
                    
                    # 记录完整的交易历史
                    trade_record = {
                        'trade_id': len(self.trade_history) + 1,
                        'type': 'open_long',
                        'side': 'buy',
                        'price': current_price,
                        'amount': amount,
                        'time': trade_time,
                        'timestamp': trade_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'supporting_agents': [s['agent_id'] for s in buy_signals],
                        'all_signals': buy_signals,  # 完整信号信息
                        'consensus_confidence': buy_confidence,
                        'market_state': self.current_market_state.copy(),
                        'order_info': order
                    }
                    self.trade_history.append(trade_record)
                    print(f"   📝 交易记录ID: #{trade_record['trade_id']}")
            else:
                print("   ⏸️  已有持仓，跳过")
        
        elif len(sell_signals) / len(self.agents) > support_ratio and sell_confidence > threshold:
            if has_position:
                print(f"   🔴 共识：平仓/做空 (信心度: {sell_confidence:.2f})")
                print(f"   支持Agent: {len(sell_signals)}/{len(self.agents)}")
                
                # 平仓
                order = self.okx.close_position('BTC/USDT:USDT')
                
                if order and self.current_position:
                    trade_time = datetime.now()
                    
                    # 计算盈亏
                    pnl = (current_price - self.current_position['entry_price']) * self.current_position['amount']
                    self.stats['total_pnl'] += pnl
                    
                    if pnl > 0:
                        self.stats['successful_trades'] += 1
                        print(f"   ✅ 盈利: ${pnl:.2f}")
                    else:
                        self.stats['failed_trades'] += 1
                        print(f"   ❌ 亏损: ${pnl:.2f}")
                    
                    # 记录平仓交易历史
                    trade_record = {
                        'trade_id': len(self.trade_history) + 1,
                        'type': 'close_position',
                        'side': 'sell',
                        'price': current_price,
                        'amount': self.current_position['amount'],
                        'time': trade_time,
                        'timestamp': trade_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'supporting_agents': [s['agent_id'] for s in sell_signals],
                        'all_signals': sell_signals,
                        'consensus_confidence': sell_confidence,
                        'market_state': self.current_market_state.copy(),
                        'order_info': order,
                        # 关联开仓信息
                        'related_open_trade_id': self.current_position.get('trade_id'),
                        'entry_price': self.current_position['entry_price'],
                        'exit_price': current_price,
                        'pnl': pnl,
                        'holding_time': (trade_time - self.current_position['time']).total_seconds() / 60  # 持仓分钟数
                    }
                    self.trade_history.append(trade_record)
                    print(f"   📝 交易记录ID: #{trade_record['trade_id']}")
                    
                    self.current_position = None
            else:
                print("   ⏸️  无持仓，跳过")
        else:
            print("   ⏸️  未达成共识，观望")
    
    def _update_statistics(self):
        """更新统计数据"""
        # 更新Agent表现
        for agent in self.agents:
            if agent.trade_count > 10:
                win_rate = agent.win_count / agent.trade_count
                
                # 简单的权限更新
                if win_rate > 0.6 and agent.total_pnl > 500:
                    if agent.permission_level == PermissionLevel.NOVICE:
                        agent.permission_level = PermissionLevel.INTERMEDIATE
    
    def _print_status(self):
        """打印实时状态"""
        print(f"\n📊 【系统状态】")
        print(f"   总信号: {self.stats['total_signals']}")
        print(f"   代表性交易: {self.stats['executed_trades']}")
        print(f"   盈利交易: {self.stats['successful_trades']}")
        print(f"   亏损交易: {self.stats['failed_trades']}")
        print(f"   系统盈亏: ${self.stats['total_pnl']:.2f}")
        
        if self.current_position:
            print(f"\n   代表性持仓: {self.current_position['side'].upper()}")
            print(f"   入场价: ${self.current_position['entry_price']:.2f}")
            print(f"   持仓量: {self.current_position['amount']} BTC")
        
        # 显示Agent虚拟表现Top3
        print(f"\n🏆 【Agent虚拟表现 Top3】")
        
        # 使用Supervisor的排名功能
        try:
            rankings = self.supervisor.rank_agent_performance()
            
            # 显示Top3
            for i, (agent_id, perf_data) in enumerate(rankings[:3], 1):
                medal = "🥇" if i == 1 else ("🥈" if i == 2 else "🥉")
                pnl = perf_data['total_pnl']
                trades = perf_data['trade_count']
                win_rate = perf_data['win_rate'] * 100
                portfolio = self.supervisor.get_agent_portfolio(agent_id)
                positions = len(portfolio['virtual_positions']) if portfolio else 0
                
                print(f"   {medal} {agent_id}: ${pnl:.2f} | "
                      f"{trades}笔 | 胜率{win_rate:.0f}% | "
                      f"{'持仓中' if positions > 0 else '空仓'}")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
    
    def save_trade_history(self, filename=None):
        """保存交易历史到文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'trade_history_{timestamp}.json'
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': self.stats,
                'trades': self.trade_history,
                'agent_portfolios': self.supervisor.get_all_portfolios(),  # 从Supervisor获取
                'agent_info': [
                    {
                        'agent_id': agent.agent_id,
                        'personality': {
                            'aggression': agent.personality.aggression,
                            'risk_tolerance': agent.personality.risk_tolerance,
                            'adaptability': agent.personality.adaptability
                        }
                    } for agent in self.agents
                ]
            }, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 交易历史已保存: {filename}")
        return filename
    
    def _print_final_summary(self):
        """打印最终总结"""
        print("\n" + "="*70)
        print("  📊 测试总结")
        print("="*70)
        
        print(f"\n【交易统计】")
        print(f"  总信号数: {self.stats['total_signals']}")
        print(f"  执行交易: {self.stats['executed_trades']}")
        print(f"  盈利交易: {self.stats['successful_trades']}")
        print(f"  亏损交易: {self.stats['failed_trades']}")
        
        if self.stats['executed_trades'] > 0:
            win_rate = self.stats['successful_trades'] / self.stats['executed_trades'] * 100
            print(f"  胜率: {win_rate:.2f}%")
        
        # 保存交易历史
        if self.trade_history:
            self.save_trade_history()
        
        print(f"\n【盈亏统计】")
        print(f"  系统累计盈亏: ${self.stats['total_pnl']:.2f}")
        
        # Agent虚拟表现排名
        print(f"\n🏆【Agent虚拟表现完整排名】")
        agent_performance = []
        
        # 从Supervisor获取虚拟账户数据
        all_portfolios = self.supervisor.get_all_portfolios()
        for agent_id, portfolio in all_portfolios.items():
            if portfolio['trade_count'] > 0:
                pnl_rate = portfolio['total_pnl'] / portfolio['initial_capital'] * 100
                win_rate = portfolio['win_count'] / portfolio['trade_count'] * 100
            else:
                pnl_rate = 0
                win_rate = 0
            
            agent_performance.append({
                'agent_id': agent_id,
                'pnl': portfolio['total_pnl'],
                'pnl_rate': pnl_rate,
                'trades': portfolio['trade_count'],
                'wins': portfolio['win_count'],
                'losses': portfolio['loss_count'],
                'win_rate': win_rate,
                'capital': portfolio['virtual_capital'],
                'personality': portfolio['personality']
            })
        
        # 按盈亏排序
        agent_performance.sort(key=lambda x: x['pnl'], reverse=True)
        
        # 显示完整排名
        print(f"  {'排名':<4} {'Agent ID':<15} {'盈亏':<12} {'收益率':<8} {'交易数':<6} {'胜率':<6}")
        print("  " + "-" * 70)
        
        for i, perf in enumerate(agent_performance, 1):
            medal = "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i:2d}"))
            print(f"  {medal:4} {perf['agent_id']:<15} "
                  f"${perf['pnl']:+7.2f}    {perf['pnl_rate']:+5.1f}%   "
                  f"{perf['trades']:3d}笔   {perf['win_rate']:5.1f}%")
        
        # 显示性格与表现的关系
        print(f"\n📊【性格与表现分析】")
        if agent_performance:
            top_performer = agent_performance[0]
            print(f"  最佳: {top_performer['agent_id']}")
            print(f"    - 激进度: {top_performer['personality']['aggression']:.2f}")
            print(f"    - 风险承受: {top_performer['personality']['risk_tolerance']:.2f}")
            print(f"    - 适应性: {top_performer['personality']['adaptability']:.2f}")


def main():
    """主函数"""
    # 设置日志输出
    start_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f'okx_live_test_{start_timestamp}.txt'
    tee = TeeOutput(log_filename)
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        print("\n" + "="*70)
        print("  Prometheus v4.0 - OKX模拟盘实盘测试")
        print("="*70)
        print(f"  📝 日志文件: {log_filename}")
        print("="*70)
        print("\n⚠️  使用说明：")
        print("  1. 需要OKX模拟盘API密钥")
        print("  2. 确保模拟账户有足够余额")
        print("  3. 建议先短时间测试（如5-10分钟）")
        print("  4. 测试过程将同时输出到终端和日志文件")
        print("="*70)
        
        # 请输入您的OKX模拟盘API信息
        sys.stdout = original_stdout  # 临时恢复stdout以便input
        print("\n请输入OKX模拟盘API信息：")
        api_key = input("API Key: ").strip()
        api_secret = input("API Secret: ").strip()
        passphrase = input("Passphrase: ").strip()
        sys.stdout = tee  # 恢复tee输出
        
        if not all([api_key, api_secret, passphrase]):
            print("\n❌ API信息不完整，退出")
            return
        
        # 连接OKX模拟盘
        okx_trader = OKXPaperTrading(api_key, api_secret, passphrase)
        
        # 创建Prometheus交易系统
        prometheus = PrometheusLiveTrading(okx_trader, log_file=log_filename)
        
        # 运行实盘测试
        sys.stdout = original_stdout  # 临时恢复stdout
        duration = int(input("\n测试时长（分钟，建议5-60）: ") or "10")
        interval = int(input("检查间隔（秒，建议30-120）: ") or "60")
        sys.stdout = tee  # 恢复tee输出
        
        prometheus.run_live_test(duration_minutes=duration, check_interval=interval)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复stdout并关闭日志文件
        sys.stdout = original_stdout
        tee.close()
        print(f"\n✅ 日志已保存到: {log_filename}")


if __name__ == '__main__':
    main()

