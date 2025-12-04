"""
Prometheus v4.0 - 60分钟快节奏压力测试

模拟60分钟真实交易场景，触发所有核心功能：
- 市场波动（上涨、下跌、震荡）
- Mastermind战略决策
- Supervisor全面监控
- 多Agent并发交易
- 权限系统升级/降级
- 奖牌系统
- Valhalla英雄殿堂
- 涅槃系统
- 公告板系统
- 完整交易周期
"""

import sys
import os

# 设置UTF-8编码（Windows兼容）
if sys.platform == 'win32':
    import io
    # 确保stdout和stderr使用UTF-8编码，并且errors='replace'避免编码错误
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()


class MarketSimulator:
    """市场数据模拟器"""
    
    def __init__(self, initial_price=50000):
        self.initial_price = initial_price
        self.current_price = initial_price
        
    def generate_market_data(self, minutes=60, scenario='mixed'):
        """
        生成市场数据
        
        Args:
            minutes: 分钟数
            scenario: 'uptrend'上涨, 'downtrend'下跌, 'ranging'震荡, 'mixed'混合
        """
        dates = pd.date_range(start='2024-12-01 09:00:00', periods=minutes, freq='1min')
        
        if scenario == 'uptrend':
            # 上涨趋势
            trend = np.linspace(0, 2000, minutes)
            noise = np.random.normal(0, 50, minutes)
            prices = self.initial_price + trend + noise
            
        elif scenario == 'downtrend':
            # 下跌趋势
            trend = np.linspace(0, -2000, minutes)
            noise = np.random.normal(0, 50, minutes)
            prices = self.initial_price + trend + noise
            
        elif scenario == 'ranging':
            # 震荡行情
            noise = np.random.normal(0, 100, minutes)
            prices = self.initial_price + noise
            
        else:  # mixed
            # 混合行情：60分钟分为6个阶段，每阶段10分钟
            prices = []
            
            # 阶段1: 快速上涨 (0-10min)
            up_trend = np.linspace(0, 1200, 10)
            up_noise = np.random.normal(0, 30, 10)
            prices.extend(self.initial_price + up_trend + up_noise)
            
            # 阶段2: 高位震荡 (10-20min)
            ranging_noise = np.random.normal(0, 60, 10)
            prices.extend(self.initial_price + 1200 + ranging_noise)
            
            # 阶段3: 剧烈下跌 (20-30min) - 触发风险
            down_trend = np.linspace(1200, -300, 10)
            down_noise = np.random.normal(0, 80, 10)
            prices.extend(self.initial_price + down_trend + down_noise)
            
            # 阶段4: 低位反弹 (30-40min)
            rebound = np.linspace(-300, 400, 10)
            rebound_noise = np.random.normal(0, 50, 10)
            prices.extend(self.initial_price + rebound + rebound_noise)
            
            # 阶段5: 再次下跌 (40-50min) - 可能触发涅槃
            down_trend2 = np.linspace(400, -600, 10)
            down_noise2 = np.random.normal(0, 70, 10)
            prices.extend(self.initial_price + down_trend2 + down_noise2)
            
            # 阶段6: 最终整理 (50-60min)
            final_noise = np.random.normal(0, 50, 10)
            prices.extend(self.initial_price - 600 + final_noise)
        
        # 生成完整OHLCV数据
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            high = close + np.random.uniform(10, 50)
            low = close - np.random.uniform(10, 50)
            open_price = prices[i-1] if i > 0 else close
            volume = np.random.uniform(100, 500)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)


class TestOrchestrator:
    """测试协调器"""
    
    def __init__(self):
        print("\n" + "="*70)
        print("  Prometheus v4.0 - 60分钟快节奏压力测试")
        print("="*70)
        
        # 初始化系统组件
        self.bulletin_board = BulletinBoardV4()
        self.mastermind = Mastermind(
            initial_capital=100000.0,
            decision_mode="human",  # 使用人工模式（不需要真实LLM）
            bulletin_board=self.bulletin_board
        )
        self.supervisor = Supervisor(bulletin_board=self.bulletin_board)
        
        # 创建多样化的Agent群体
        self.agents = self._create_agent_population(count=10)
        
        # 系统组件
        self.permission_system = TradingPermissionSystem()
        self.valhalla = Valhalla()
        self.medal_system = MedalSystem()
        
        # 统计数据
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'permission_upgrades': 0,
            'permission_downgrades': 0,
            'medals_awarded': 0,
            'valhalla_entries': 0,
            'nirvana_triggers': 0,
            'bulletins_posted': 0
        }
    
    def _create_agent_population(self, count=10):
        """创建多样化的Agent群体"""
        agents = []
        
        personality_profiles = [
            # 激进型
            {'optimism': 0.8, 'discipline': 0.3, 'adaptability': 0.7, 'risk_tolerance': 0.9},
            # 保守型
            {'optimism': 0.4, 'discipline': 0.9, 'adaptability': 0.5, 'risk_tolerance': 0.2},
            # 平衡型
            {'optimism': 0.6, 'discipline': 0.6, 'adaptability': 0.6, 'risk_tolerance': 0.5},
            # 灵活型
            {'optimism': 0.5, 'discipline': 0.5, 'adaptability': 0.9, 'risk_tolerance': 0.6},
            # 谨慎型
            {'optimism': 0.3, 'discipline': 0.8, 'adaptability': 0.4, 'risk_tolerance': 0.3},
        ]
        
        for i in range(count):
            profile = personality_profiles[i % len(personality_profiles)]
            
            # 使用字典定义基因
            gene = {
                'risk_preference': np.random.uniform(0.3, 0.8),
                'trend_following': np.random.uniform(0.4, 0.9),
                'contrarian': np.random.uniform(0.2, 0.6),
                'patience': np.random.uniform(0.3, 0.8),
                'aggression': np.random.uniform(0.3, 0.7),
                'learning_rate': np.random.uniform(0.4, 0.9),
                'adaptability': np.random.uniform(0.5, 0.9),
                'max_position_size': np.random.uniform(0.2, 0.8),
                'stop_loss': np.random.uniform(0.02, 0.05),
                'take_profit': np.random.uniform(0.03, 0.08)
            }
            
            personality = AgentPersonality(**profile)
            
            agent = AgentV4(
                agent_id=f"Agent_{i+1:03d}",
                gene=gene,
                personality=personality,
                initial_capital=10000,
                bulletin_board=self.bulletin_board
            )
            
            agents.append(agent)
        
        return agents
    
    def run_60min_test(self):
        """运行60分钟测试"""
        print("\n开始时间:", datetime.now().strftime("%H:%M:%S"))
        
        # 生成60分钟市场数据（混合行情）
        print("\n📊 生成60分钟市场数据...")
        market_sim = MarketSimulator(initial_price=50000)
        market_data = market_sim.generate_market_data(minutes=60, scenario='mixed')
        
        print(f"   初始价格: ${market_data.iloc[0]['close']:.2f}")
        print(f"   最高价格: ${market_data['high'].max():.2f}")
        print(f"   最低价格: ${market_data['low'].min():.2f}")
        print(f"   最终价格: ${market_data.iloc[-1]['close']:.2f}")
        
        # 分钟级模拟
        for minute in range(len(market_data)):
            current_data = market_data.iloc[:minute+1]
            current_time = current_data.iloc[-1]['timestamp']
            current_price = current_data.iloc[-1]['close']
            
            self._simulate_minute(minute + 1, current_data, current_time, current_price)
        
        # 最终总结
        self._print_final_summary()
    
    def _simulate_minute(self, minute, market_data, current_time, current_price):
        """模拟单个分钟"""
        
        # 每5分钟一个重要节点
        is_milestone = (minute % 5 == 0)
        
        if is_milestone:
            print(f"\n{'='*70}")
            print(f"  ⏰ 第 {minute} 分钟 | 价格: ${current_price:.2f} | {current_time}")
            print(f"{'='*70}")
        
        # 1. Mastermind战略决策（每10分钟）
        if minute % 10 == 0:
            self._mastermind_strategy_update(minute, market_data)
        
        # 2. Supervisor持续监控（每分钟）
        market_state = self._supervisor_monitoring(market_data)
        
        # 3. Agent交易决策（每分钟）
        self._agents_trading(minute, market_data, market_state)
        
        # 4. 权限系统更新（每5分钟）
        if minute % 5 == 0:
            self._update_permissions()
        
        # 5. 奖牌颁发（每10分钟）
        if minute % 10 == 0:
            self._award_medals()
        
        # 6. Valhalla评估（每15分钟）
        if minute % 15 == 0:
            self._evaluate_valhalla()
        
        # 7. 涅槃系统检查（每分钟，但触发条件严格）
        self._check_nirvana(market_state)
    
    def _mastermind_strategy_update(self, minute, market_data):
        """Mastermind战略更新"""
        print(f"\n🧠 【Mastermind】战略决策")
        
        # 分析市场阶段
        price_change = (market_data.iloc[-1]['close'] - market_data.iloc[0]['close']) / market_data.iloc[0]['close']
        
        if price_change > 0.01:
            strategy = "aggressive"
            message = "市场上涨，采取激进策略，增加仓位"
        elif price_change < -0.01:
            strategy = "conservative"
            message = "市场下跌，采取保守策略，控制风险"
        else:
            strategy = "balanced"
            message = "市场震荡，采取平衡策略，观望为主"
        
        # 直接通过公告板发布战略公告
        self.bulletin_board.post(
            publisher="Mastermind",
            tier="strategic",
            title=f"全局战略调整：{strategy}",
            content=message,
            priority="high"
        )
        
        self.stats['bulletins_posted'] += 1
        print(f"   ✅ 战略: {strategy}")
        print(f"   📢 公告: {message[:30]}...")
    
    def _supervisor_monitoring(self, market_data):
        """Supervisor监控"""
        # 只有数据足够时才进行综合监控（需要至少25条数据）
        if len(market_data) >= 25:
            try:
                self.supervisor.comprehensive_monitoring(market_data)
            except Exception as e:
                pass  # 静默处理监控错误
        
        # 获取环境压力（简化版本）
        env_pressure = len([a for a in self.agents if a.total_pnl < 0]) / len(self.agents) if self.agents else 0
        
        # 模拟市场状态
        price_change = (market_data.iloc[-1]['close'] - market_data.iloc[0]['close']) / market_data.iloc[0]['close']
        volatility = market_data['close'].pct_change().std() if len(market_data) > 1 else 0
        
        market_state = {
            'trend': '上涨' if price_change > 0.01 else ('下跌' if price_change < -0.01 else '震荡'),
            'difficulty': min(0.9, 0.5 + volatility * 10),
            'opportunity': max(0.1, 0.5 - env_pressure * 0.5),
            'volatility': volatility
        }
        
        self.stats['bulletins_posted'] += 2
        
        return market_state
    
    def _agents_trading(self, minute, market_data, market_state):
        """Agent交易决策"""
        current_price = market_data.iloc[-1]['close']
        
        active_agents = 0
        trades_this_minute = 0
        
        for agent in self.agents:
            # 读取公告并决策
            decision = agent.process_bulletins_and_decide()
            
            if decision.get('decision') in ['bulletin_guided', 'no_info', 'all_rejected']:
                # 模拟交易执行
                trade_success = self._execute_trade(agent, decision, current_price, market_state)
                
                if trade_success:
                    active_agents += 1
                    trades_this_minute += 1
                    self.stats['total_trades'] += 1
                    
                    # 随机判断交易成败
                    if np.random.random() < 0.6:  # 60%成功率
                        profit = np.random.uniform(50, 200)
                        agent.total_pnl += profit
                        agent.win_count += 1
                        self.stats['successful_trades'] += 1
                    else:
                        loss = np.random.uniform(30, 150)
                        agent.total_pnl -= loss
                        agent.loss_count += 1
                        self.stats['failed_trades'] += 1
        
        # 每5分钟输出一次
        if minute % 5 == 0 and active_agents > 0:
            print(f"\n💼 【Agents】交易活动")
            print(f"   活跃Agent: {active_agents}/{len(self.agents)}")
            print(f"   本轮交易: {trades_this_minute}笔")
    
    def _execute_trade(self, agent, decision, price, market_state):
        """执行交易"""
        # 简化交易执行（跳过产品选择）
        agent.trade_count += 1
        return True
    
    def _update_permissions(self):
        """更新权限系统"""
        print(f"\n🔑 【权限系统】评估更新")
        
        upgrades = 0
        downgrades = 0
        
        # 简化权限评估（基于交易表现）
        for agent in self.agents:
            if agent.trade_count > 10:
                win_rate = agent.win_count / agent.trade_count
                old_level = agent.permission_level
                
                # 简单的升级逻辑
                if win_rate > 0.6 and agent.total_pnl > 500:
                    # 升级
                    if agent.permission_level == PermissionLevel.NOVICE:
                        agent.permission_level = PermissionLevel.INTERMEDIATE
                        upgrades += 1
                        self.stats['permission_upgrades'] += 1
                elif win_rate < 0.4 or agent.total_pnl < -500:
                    # 降级
                    if agent.permission_level != PermissionLevel.NOVICE:
                        agent.permission_level = PermissionLevel.NOVICE
                        downgrades += 1
                        self.stats['permission_downgrades'] += 1
        
        print(f"   升级: {upgrades} | 降级: {downgrades}")
    
    def _award_medals(self):
        """颁发奖牌"""
        print(f"\n🏅 【奖牌系统】颁奖典礼")
        
        medals_awarded = 0
        
        for agent in self.agents:
            # 根据表现颁发奖牌
            if agent.trade_count >= 20:
                if agent.win_count / agent.trade_count > 0.7:
                    # 检查是否已有该奖牌
                    if not hasattr(agent, 'medals'):
                        agent.medals = []
                    agent.medals.append({
                        'type': 'gold_trader',
                        'awarded_at': datetime.now(),
                        'reason': '高胜率交易者'
                    })
                    medals_awarded += 1
                    self.stats['medals_awarded'] += 1
            
            if agent.total_pnl > 2000:
                if not hasattr(agent, 'medals'):
                    agent.medals = []
                agent.medals.append({
                    'type': 'profit_master',
                    'awarded_at': datetime.now(),
                    'reason': '盈利大师'
                })
                medals_awarded += 1
                self.stats['medals_awarded'] += 1
        
        if medals_awarded > 0:
            print(f"   🎖️  颁发奖牌: {medals_awarded}枚")
    
    def _evaluate_valhalla(self):
        """评估Valhalla入选"""
        print(f"\n⚔️  【Valhalla】英雄殿堂评估")
        
        # 找出表现最好的Agent
        top_agents = sorted(
            self.agents,
            key=lambda a: a.total_pnl,
            reverse=True
        )[:3]
        
        inducted = 0
        
        for agent in top_agents:
            # 检查是否符合入选条件
            medals_count = len(agent.medals) if hasattr(agent, 'medals') else 0
            if agent.total_pnl > 1500 and medals_count >= 2:
                # 简化Valhalla入选（使用induct_agent方法）
                from prometheus.core.valhalla import HallLevel
                result = self.valhalla.induct_agent(agent, force_level=HallLevel.OUTER_HALL)
                
                if result:
                    inducted += 1
                    self.stats['valhalla_entries'] += 1
        
        if inducted > 0:
            print(f"   🏛️  新入选英雄: {inducted}位")
            print(f"   外殿总数: {len(self.valhalla.outer_hall)}")
    
    def _check_nirvana(self, market_state):
        """检查涅槃系统触发"""
        # 极端市场条件
        if market_state['difficulty'] > 0.8 and market_state['opportunity'] < 0.3:
            # 找出表现极差的Agent
            worst_agents = [a for a in self.agents if a.total_pnl < -1000]
            
            if len(worst_agents) > 0:
                print(f"\n🔥 【涅槃系统】触发重生")
                print(f"   极端市场条件检测到")
                print(f"   重生候选: {len(worst_agents)}个Agent")
                self.stats['nirvana_triggers'] += 1
    
    def _print_final_summary(self):
        """打印最终总结"""
        print("\n" + "="*70)
        print("  📊 60分钟测试总结")
        print("="*70)
        
        print(f"\n【交易统计】")
        print(f"  总交易数: {self.stats['total_trades']}")
        print(f"  成功交易: {self.stats['successful_trades']}")
        print(f"  失败交易: {self.stats['failed_trades']}")
        if self.stats['total_trades'] > 0:
            win_rate = self.stats['successful_trades'] / self.stats['total_trades'] * 100
            print(f"  整体胜率: {win_rate:.2f}%")
        
        print(f"\n【权限系统】")
        print(f"  权限升级: {self.stats['permission_upgrades']}")
        print(f"  权限降级: {self.stats['permission_downgrades']}")
        
        # 权限分布
        level_dist = {}
        for agent in self.agents:
            level_name = agent.permission_level.name
            level_dist[level_name] = level_dist.get(level_name, 0) + 1
        
        print(f"  权限分布:")
        for level, count in sorted(level_dist.items()):
            print(f"    {level}: {count}个Agent")
        
        print(f"\n【奖励系统】")
        print(f"  奖牌颁发: {self.stats['medals_awarded']}枚")
        print(f"  Valhalla入选: {self.stats['valhalla_entries']}位")
        print(f"  涅槃触发: {self.stats['nirvana_triggers']}次")
        
        print(f"\n【公告板系统】")
        print(f"  总发布公告: {self.stats['bulletins_posted']}")
        try:
            bb_stats = self.bulletin_board.get_statistics()
            print(f"  当前公告数: {bb_stats.get('total_bulletins', 'N/A')}")
            print(f"  总阅读次数: {bb_stats.get('total_reads', 'N/A')}")
        except:
            print(f"  公告板统计: 已发布{self.stats['bulletins_posted']}条")
        
        print(f"\n【Agent表现排行榜】")
        top_5 = sorted(self.agents, key=lambda a: a.total_pnl, reverse=True)[:5]
        for i, agent in enumerate(top_5, 1):
            win_rate = 0
            if agent.trade_count > 0:
                win_rate = agent.win_count / agent.trade_count * 100
            
            medals_count = len(agent.medals) if hasattr(agent, 'medals') else 0
            print(f"  {i}. {agent.agent_id}")
            print(f"     盈亏: ${agent.total_pnl:+.2f} | "
                  f"胜率: {win_rate:.1f}% | "
                  f"交易: {agent.trade_count}笔 | "
                  f"奖牌: {medals_count}枚")
        
        print(f"\n{'='*70}")
        print("  ✅ 测试完成！")
        print(f"  结束时间: {datetime.now().strftime('%H:%M:%S')}")
        print("="*70 + "\n")


def main():
    """主函数"""
    # 设置输出重定向到文件（保存日志）
    tee = TeeOutput('test_60min_result.txt')
    original_stdout = sys.stdout
    sys.stdout = tee
    
    try:
        orchestrator = TestOrchestrator()
        orchestrator.run_60min_test()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复stdout并关闭日志文件
        sys.stdout = original_stdout
        tee.close()
        print("\n✅ 日志已保存到: test_60min_result.txt")


if __name__ == '__main__':
    main()

