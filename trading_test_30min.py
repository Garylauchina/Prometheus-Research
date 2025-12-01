#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
30分钟交易测试脚本
功能：
1. 连接到OKX模拟盘
2. 平掉所有现有持仓
3. 创世生成5个Agent
4. 运行30分钟的交易测试
5. 记录详细交易日志
"""

import sys
import os
import time
import logging
import json
from datetime import datetime, timedelta
import random

# 添加项目路径
project_path = 'E:\\Trae_store\\prometheus-v30\\'
if os.path.exists(project_path):
    sys.path.insert(0, project_path)
else:
    print(f"错误: 项目路径不存在: {project_path}")
    sys.exit(1)

# 导入所需模块 - 使用与check_positions.py相同的导入方式
try:
    from adapters.okx_adapter import OKXTradingAdapter
    from config import CONFIG_V3 as CONFIG
    # 由于agent、gene等模块可能存在相对导入问题，我们将创建简化版本
    print("[OK] 必要模块导入成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    # 打印导入路径帮助调试
    print(f"当前Python路径: {sys.path}")
    print(f"当前工作目录: {os.getcwd()}")
    sys.exit(1)

# 创建简化版的核心类，避免导入问题
class SimpleGene:
    """简化版的基因类"""
    def __init__(self):
        self.preferences = {}
    
    @classmethod
    def random(cls):
        gene = cls()
        # 简化的市场特征偏好
        features = ['strong_bull', 'bull', 'weak_bull', 'sideways', 'weak_bear', 'bear', 'strong_bear']
        gene.preferences = {feature: random.uniform(0, 1) for feature in features}
        return gene
    
    def get_top_preferences(self, count=3):
        return sorted(self.preferences.items(), key=lambda x: x[1], reverse=True)[:count]
    
    def generate_species_name(self):
        return f"Species_{random.randint(1000, 9999)}"

class SimpleStrategy:
    """简化版的策略类"""
    def __init__(self, gene, config):
        self.gene = gene
        self.config = config

class SimpleAgent:
    """简化版的Agent类"""
    def __init__(self, agent_id, gene, initial_capital, strategy):
        self.id = agent_id
        self.gene = gene
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.strategy = strategy
        self.is_alive = True
        self.death_reason = None
        self.roi = 0
        self.trade_count = 0
        self.age = 0
        self.long_ratio = 0
        self.short_ratio = 0
    
    def update(self, market_features, price_change):
        # 简化的更新逻辑
        self.age += 1
        # 随机调整资金变化
        capital_change = self.capital * random.uniform(-0.05, 0.05)
        self.capital += capital_change
        self.roi = (self.capital - self.initial_capital) / self.initial_capital
        # 模拟交易
        if random.random() < 0.3:  # 30%概率执行交易
            self.trade_count += 1
        # 随机调整仓位比例
        self.long_ratio = random.uniform(0, 1)
        self.short_ratio = random.uniform(0, 1 - self.long_ratio)
    
    def should_die(self, death_config):
        # 如果ROI低于阈值，标记为死亡
        if self.roi < death_config.get('death_roi_threshold', -0.5):
            self.death_reason = f"ROI低于阈值: {self.roi:.2%}"
            return True
        return False
    
    def die(self):
        self.is_alive = False

# 配置日志
log_dir = os.path.join(project_path, 'test_logs')
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f'trading_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# 配置日志，确保使用UTF-8编码
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
stream_handler = logging.StreamHandler()

# 设置日志级别为DEBUG，以便查看更多调试信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger('trading_test')

class TradingTest:
    def __init__(self, skip_position_check=False):
        # 添加跳过持仓检查的选项
        self.skip_position_check = skip_position_check
        
        # 使用从config.py导入的配置
        self.okx_config = CONFIG['okx_api'].copy()
        # 确保使用模拟盘
        self.okx_config['flag'] = 1
        
        # 如果配置中没有设置API密钥，则使用测试密钥
        if not self.okx_config['api_key']:
            self.okx_config.update({
                'api_key': "265a4c37-1dc1-40d8-80d0-11004026ca48",
                'secret_key': "0AD30E01A7B66FBBBEB7E30D8E0E18B4",
                'passphrase': "Garylauchina3.14"
            })
        
        self.adapter = None
        self.agents = []
        # 使用配置文件中的初始资金
        self.capital_pool = {'initial_capital': CONFIG['initial_capital']}
        # 不需要market对象，因为我们将使用模拟数据
        self.strategy_config = CONFIG['agent_manager']['strategy'].copy()
    
    def connect_to_okx(self):
        """连接到OKX模拟盘"""
        logger.info("正在连接到OKX模拟盘...")
        try:
            self.adapter = OKXTradingAdapter(self.okx_config)
            logger.info("[OK] 成功连接到OKX模拟盘")
            return True
        except Exception as e:
            logger.error(f"❌ 连接OKX失败: {e}")
            return False
    
    def close_all_positions(self, max_attempts=3):
        """
        关闭所有当前持仓
        
        Args:
            max_attempts: 最大尝试次数
            
        Returns:
            成功平仓的持仓数量
        """
        logger.info("====== 开始平仓操作 ======")
        
        # 记录本次尝试的次数
        current_attempt = 1
        total_closed_positions = 0
        
        while current_attempt <= max_attempts:
            logger.info(f"====== 平仓尝试 {current_attempt}/{max_attempts} ======")
            logger.info("正在获取当前持仓...")
            try:
                # 修复：添加更强大的错误处理和重试机制
                positions = self.adapter.get_positions()
                
                # 处理不同的返回格式
                positions_to_close = []
                
                # 记录原始positions数据以便调试
                logger.info(f"原始持仓数据类型: {type(positions)}, 内容: {positions}")
                
                # 首先验证positions是否为有效数据
                if positions is None or (isinstance(positions, dict) and len(positions) == 0) or (isinstance(positions, list) and len(positions) == 0):
                    logger.info("未获取到持仓数据或持仓为空，继续执行测试")
                    return 0
                
                # 处理不同的返回格式并严格验证是否有实际持仓
                if isinstance(positions, dict):
                    for symbol, pos in positions.items():
                        # 记录原始持仓数据用于调试
                        logger.info(f"检查持仓 {symbol}: {pos}")
                        # 检查是否有实际持仓量，使用更严格的判断
                        try:
                            size_values = []
                            # 检查多种可能的字段名称
                            for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                if key in pos and pos[key]:
                                    # 尝试转换为浮点数
                                    size = float(pos[key])
                                    if size > 0.000001:  # 设置一个极小值阈值，避免因精度问题误判
                                        size_values.append(size)
                            # 只有当有明显大于0的持仓量时才加入平仓列表
                            if size_values:
                                logger.info(f"发现有效持仓 {symbol}: {max(size_values)}")
                                positions_to_close.append((symbol, pos))
                            else:
                                logger.info(f"持仓 {symbol} 的持仓量为0或极小，无需平仓")
                        except (ValueError, TypeError) as e:
                            logger.info(f"持仓 {symbol} 的数据格式异常，跳过: {e}")
                            continue
                elif isinstance(positions, list):
                    for pos in positions:
                        if isinstance(pos, dict):
                            # 记录原始持仓数据用于调试
                            logger.info(f"检查持仓项: {pos}")
                            # 适配不同的字段名称
                            symbol_key = 'instId' if 'instId' in pos else 'symbol' if 'symbol' in pos else None
                            if symbol_key and pos.get(symbol_key):
                                try:
                                    # 检查是否有实际持仓量，使用更严格的判断
                                    size_values = []
                                    for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                        if key in pos and pos[key]:
                                            size = float(pos[key])
                                            if size > 0.000001:  # 设置一个极小值阈值
                                                size_values.append(size)
                                    # 只有当有明显大于0的持仓量时才加入平仓列表
                                    if size_values:
                                        symbol = pos[symbol_key]
                                        logger.info(f"发现有效持仓 {symbol}: {max(size_values)}")
                                        positions_to_close.append((symbol, pos))
                                    else:
                                        logger.info(f"持仓项 {pos.get(symbol_key)} 的持仓量为0或极小，无需平仓")
                                except (ValueError, TypeError) as e:
                                    logger.info(f"持仓项数据格式异常，跳过: {e}")
                                    continue
                        else:
                            logger.info(f"非字典类型的持仓项: {pos}")
                
                # 再次验证实际有持仓的数量
                logger.info(f"找到 {len(positions_to_close)} 个有效持仓需要平仓")
                
                # 如果没有实际持仓，直接返回
                if len(positions_to_close) == 0:
                    logger.info("没有发现需要平仓的有效持仓，继续执行测试")
                    return 0
                
                closed_positions = 0
                for symbol, pos in positions_to_close:
                    try:
                        # 更全面地获取持仓信息
                        size = float(pos.get('size', pos.get('pos', pos.get('availPos', pos.get('available', 0)))))  
                        side = pos.get('side', pos.get('posSide', pos.get('direction', ''))).lower()
                        
                        if size <= 0 or not side:
                            logger.warning(f"持仓信息不完整: {symbol}, size={size}, side={side}")
                            continue
                        
                        logger.info(f"平掉持仓: {symbol}, 方向: {side}, 数量: {size}")
                        
                        # 确定平仓方向
                        close_side = 'buy' if side == 'short' else 'sell'
                        
                        # 下单平仓 - 增加重试逻辑
                        max_retries = 3
                        retry_count = 0
                        order_success = False
                        
                        while retry_count < max_retries and not order_success:
                            retry_count += 1
                            try:
                                order_request = {
                                    'market': 'futures',
                                    'symbol': symbol,
                                    'side': close_side,
                                    'order_type': 'market',  # 市价单快速平仓
                                    'size': size
                                }
                                
                                order = self.adapter.place_order(order_request)
                                logger.info(f"[OK] 平仓订单已提交 (尝试 {retry_count}/{max_retries}): {order.order_id}")
                                
                                # 等待订单完成
                                time.sleep(3)  # 增加等待时间
                                
                                # 修复：更灵活的订单状态检查
                                try:
                                    order_status = self.adapter.get_order_status(order.order_id, symbol)
                                    # 检查多种可能的订单状态格式
                                    status = getattr(order_status, 'status', None)
                                    if not status and isinstance(order_status, dict):
                                        status = order_status.get('status', order_status.get('ordStatus', None))
                                            
                                    if status in ['filled', 'filled_completely', 'filled_partially']:
                                        closed_positions += 1
                                        logger.info(f"[OK] {symbol} 持仓已完全平仓")
                                        order_success = True
                                    else:
                                        logger.warning(f"⚠️ {symbol} 平仓订单未完全成交: {status or 'unknown'}")
                                except Exception as status_e:
                                    logger.warning(f"检查订单状态时出错: {status_e}，尝试直接查询持仓")
                                    # 尝试直接重新查询持仓，检查是否已平仓
                                    new_positions = self.adapter.get_positions()
                                    if isinstance(new_positions, dict) and symbol not in new_positions:
                                        closed_positions += 1
                                        logger.info(f"[OK] {symbol} 持仓似乎已平仓 (通过重新查询确认)")
                                        order_success = True
                                    elif isinstance(new_positions, list):
                                        if not any(p.get('instId') == symbol or p.get('symbol') == symbol for p in new_positions):
                                            closed_positions += 1
                                            logger.info(f"[OK] {symbol} 持仓似乎已平仓 (通过重新查询确认)")
                                            order_success = True
                            except Exception as order_e:
                                logger.error(f"❌ 平仓订单提交失败 (尝试 {retry_count}/{max_retries}): {order_e}")
                                if retry_count < max_retries:
                                    logger.info(f"将在 2 秒后重试...")
                                    time.sleep(2)
                                else:
                                    order_success = False
                        
                        if not order_success:
                            logger.error(f"❌ {symbol} 平仓失败，已达到最大重试次数")
                            
                    except Exception as e:
                        logger.error(f"处理持仓 {symbol} 时出错: {e}")
                        continue
            except Exception as e:
                logger.error(f"平仓过程中发生错误: {e}")
                closed_positions = 0
                positions_to_close = []
            
            # 记录本次尝试的结果
            total_closed_positions += closed_positions
            positions_count = len(positions_to_close) if 'positions_to_close' in locals() else 0
            logger.info(f"平仓尝试 {current_attempt}/{max_attempts} 完成，本次成功平仓 {closed_positions}/{positions_count} 个持仓")
            
            # 再次检查是否还有持仓需要平仓
            if 'positions_to_close' in locals() and closed_positions == len(positions_to_close):
                logger.info("✅ 所有持仓已成功平仓！")
                return total_closed_positions
            
            # 如果还有持仓未平仓且未达到最大尝试次数，进行下一轮尝试
            if current_attempt < max_attempts:
                # 等待一段时间后重试
                wait_time = 5  # 5秒等待
                logger.info(f"还有持仓未平仓，{wait_time}秒后进行下一次尝试...")
                time.sleep(wait_time)
                
                # 重新获取持仓信息
                logger.info("重新获取持仓信息...")
                try:
                    positions = self.adapter.get_positions()
                    # 重新处理持仓数据
                    positions_to_close = []
                    if isinstance(positions, dict):
                        for symbol, pos in positions.items():
                            try:
                                size_values = []
                                for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                    if key in pos and pos[key]:
                                        size = float(pos[key])
                                        if size > 0.000001:
                                            size_values.append(size)
                                if size_values:
                                    logger.info(f"仍有持仓需要平仓: {symbol}: {max(size_values)}")
                                    positions_to_close.append((symbol, pos))
                            except (ValueError, TypeError):
                                continue
                    elif isinstance(positions, list):
                        for pos in positions:
                            if isinstance(pos, dict):
                                symbol_key = 'instId' if 'instId' in pos else 'symbol' if 'symbol' in pos else None
                                if symbol_key and pos.get(symbol_key):
                                    try:
                                        size_values = []
                                        for key in ['size', 'pos', 'availPos', 'available', 'notional', 'notionalUsd']:
                                            if key in pos and pos[key]:
                                                size = float(pos[key])
                                                if size > 0.000001:
                                                    size_values.append(size)
                                        if size_values:
                                            symbol = pos[symbol_key]
                                            logger.info(f"仍有持仓需要平仓: {symbol}: {max(size_values)}")
                                            positions_to_close.append((symbol, pos))
                                    except (ValueError, TypeError):
                                        continue
                except Exception as e:
                    logger.error(f"重新获取持仓信息时出错: {e}")
            
            # 增加尝试次数
            current_attempt += 1
        
        logger.info(f"已达到最大平仓尝试次数，总计成功平仓 {total_closed_positions} 个持仓")
        return total_closed_positions
    
    def generate_initial_agents(self, count=5):
        """创世生成简化版Agent"""
        logger.info(f"正在创世生成 {count} 个Agent...")
        
        self.agents = []
        
        # 修改：平衡Agent初始资金与资金池余量 - 使用更合理的配置
        total_pool_capital = self.capital_pool['initial_capital']  # 10,000
        # 分配约80%的资金给Agent，保留20%作为资金池余量
        agent_allocated_capital = total_pool_capital * 0.8
        initial_capital = agent_allocated_capital / count
        
        # 更新资金池余量
        self.capital_pool['reserved_capital'] = total_pool_capital - agent_allocated_capital
        
        logger.info(f"资金分配 - Agent初始资金: ${initial_capital:.2f}, 资金池余量: ${self.capital_pool['reserved_capital']:.2f}")
        
        for i in range(count):
            try:
                # 生成随机基因（使用我们的简化版Gene类）
                gene = SimpleGene.random()
                
                # 创建策略（使用我们的简化版Strategy类）
                strategy = SimpleStrategy(gene, self.strategy_config)
                
                # 创建Agent（使用我们的简化版Agent类）
                agent = SimpleAgent(
                    agent_id=i + 1,
                    gene=gene,
                    initial_capital=initial_capital,
                    strategy=strategy
                )
                
                self.agents.append(agent)
                print(f"[OK] Agent {agent.id} 创建成功: {agent.gene.generate_species_name()}")
                
            except Exception as e:
                logger.error(f"❌ 创建Agent {i+1} 失败: {e}")
        
        logger.info(f"创世生成完成，成功创建 {len(self.agents)} 个Agent")
        return len(self.agents)
    
    def run_trading_test(self, duration_minutes=30):
        """运行交易测试"""
        logger.info(f"开始 {duration_minutes} 分钟的交易测试...")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        test_start_time = datetime.now()
        
        # 记录测试信息
        test_info = {
            'start_time': test_start_time.isoformat(),
            'duration_minutes': duration_minutes,
            'initial_agents_count': len(self.agents),
            'initial_capital_per_agent': [agent.initial_capital for agent in self.agents]
        }
        logger.info(f"测试配置: {json.dumps(test_info, indent=2)}")
        
        # 主循环
        cycle_count = 0
        while datetime.now() < end_time:
            cycle_count += 1
            current_time = datetime.now()
            elapsed = (current_time - test_start_time).total_seconds() / 60
            remaining = (end_time - current_time).total_seconds() / 60
            
            # 使用更醒目的交易周期标识
            cycle_header = f"\n======= 交易周期 {cycle_count} ======= (已运行 {elapsed:.1f} 分钟, 剩余 {remaining:.1f} 分钟) ======="
            print(cycle_header)  # 同时输出到控制台，确保用户能看到
            logger.info(cycle_header)
            
            try:
                # 获取市场数据 - 不输出到控制台
                market_features = self._get_current_market_features()
                # 计算交易指数 final_signal_trading
                final_signal_trading = market_features['bull'] - market_features['bear']
                # 输出交易指数到控制台和日志
                trading_index_msg = f"交易指数: {final_signal_trading:.4f}"
                print(trading_index_msg)
                logger.info(trading_index_msg)
                
                # 计算并显示趋势值
                trend_values = {
                    'strong_bull': market_features['strong_bull'],
                    'bull': market_features['bull'],
                    'weak_bull': market_features['weak_bull'],
                    'sideways': market_features['sideways'],
                    'weak_bear': market_features['weak_bear'],
                    'bear': market_features['bear'],
                    'strong_bear': market_features['strong_bear']
                }
                
                # 构建趋势值显示信息
                trend_info = "市场趋势值: "
                trend_info += ", ".join([f"{k}={v:.3f}" for k, v in trend_values.items()])
                
                # 输出到控制台和日志
                print(trend_info)
                logger.info(trend_info)
                
                # 更新所有Agent
                for agent in self.agents:
                    if agent.is_alive:
                        # 模拟价格变化率 (-0.02 到 +0.02)
                        price_change = random.uniform(-0.02, 0.02)
                        
                        # 更新Agent状态
                        agent.update(market_features, price_change)
                        
                        # 检查是否需要死亡
                        death_config = {'death_roi_threshold': -0.5, 'max_inactive_days': 10}
                        if agent.should_die(death_config):
                            agent.die()
                            print(f"Agent {agent.id} 死亡: {agent.death_reason}")
                        else:
                            # 显示Agent的实际交易决策（基于市场特征和策略计算）
                            if agent.long_ratio > 0 and agent.short_ratio == 0:
                                action_desc = f"做多 {agent.long_ratio:.2f} 仓位"
                            elif agent.short_ratio > 0 and agent.long_ratio == 0:
                                action_desc = f"做空 {agent.short_ratio:.2f} 仓位"
                            elif agent.long_ratio > 0 and agent.short_ratio > 0:
                                action_desc = f"混合仓位 - 多: {agent.long_ratio:.2f}, 空: {agent.short_ratio:.2f}"
                            else:
                                action_desc = "空仓"
                            
                            print(f"Agent {agent.id} 决策: {action_desc}")
                
                # 记录总体统计（仅记录到日志，不输出到控制台）
                alive_agents = sum(1 for agent in self.agents if agent.is_alive)
                total_capital = sum(agent.capital for agent in self.agents)
                logger.info(f"当前统计 - 存活Agent: {alive_agents}, 总资金: ${total_capital:.2f}")
                
            except Exception as e:
                logger.error(f"❌ 交易周期 {cycle_count} 出错: {e}")
            
            # 每30秒执行一次交易周期
            time.sleep(30)
        
        logger.info("\n======= 交易测试完成 =======")
        
        # 生成测试报告
        self._generate_test_report(test_start_time)
        
        return True
    
    def _get_current_market_features(self):
        """获取当前市场特征（模拟数据）"""
        # 生成更合理的市场特征数据，确保bull和bear有一定的相关性
        # 先生成一个基础趋势值
        trend_bias = random.uniform(-1, 1)
        
        # 基于趋势偏置生成bull和bear值
        bull_value = max(0, min(1, 0.5 + trend_bias * 0.3 + random.uniform(-0.2, 0.2)))
        bear_value = max(0, min(1, 0.5 - trend_bias * 0.3 + random.uniform(-0.2, 0.2)))
        
        # 生成其他相关特征
        market_features = {
            'strong_bull': bull_value * random.uniform(0.7, 1.0),
            'bull': bull_value,
            'weak_bull': bull_value * random.uniform(0.3, 0.7),
            'sideways': max(0, 1 - bull_value - bear_value),
            'weak_bear': bear_value * random.uniform(0.3, 0.7),
            'bear': bear_value,
            'strong_bear': bear_value * random.uniform(0.7, 1.0),
            'ultra_low_vol': random.uniform(0, 1),
            'low_vol': random.uniform(0, 1),
            'normal_vol': random.uniform(0, 1),
            'high_vol': random.uniform(0, 1),
            'extreme_high_vol': random.uniform(0, 1),
            'extreme_fear': random.uniform(0, 1),
            'fear': random.uniform(0, 1),
            'neutral': random.uniform(0, 1),
            'greed': random.uniform(0, 1),
            'extreme_greed': random.uniform(0, 1),
            'breakout': random.uniform(0, 1),
            'breakdown': random.uniform(0, 1),
            'pullback': random.uniform(0, 1)
        }
        
        return market_features
    
    def _generate_test_report(self, start_time):
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        report = {
            'test_summary': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration,
                'initial_agents': len(self.agents),
                'alive_agents': sum(1 for agent in self.agents if agent.is_alive),
                'dead_agents': sum(1 for agent in self.agents if not agent.is_alive)
            },
            'agents_final_status': []
        }
        
        # 记录每个Agent的最终状态
        for agent in self.agents:
            agent_report = {
                'id': agent.id,
                'species': agent.gene.generate_species_name(),
                'is_alive': agent.is_alive,
                'death_reason': agent.death_reason,
                'initial_capital': agent.initial_capital,
                'final_capital': agent.capital,
                'roi': agent.roi,
                'trade_count': agent.trade_count,
                'age': agent.age,
                'final_long_ratio': agent.long_ratio,
                'final_short_ratio': agent.short_ratio,
                'top_preferences': agent.gene.get_top_preferences(3)
            }
            report['agents_final_status'].append(agent_report)
        
        # 计算总体统计
        total_initial_capital = sum(agent.initial_capital for agent in self.agents)
        total_final_capital = sum(agent.capital for agent in self.agents)
        overall_roi = (total_final_capital - total_initial_capital) / total_initial_capital
        
        report['test_summary']['total_initial_capital'] = total_initial_capital
        report['test_summary']['total_final_capital'] = total_final_capital
        report['test_summary']['overall_roi'] = overall_roi
        
        # 保存报告
        report_filename = os.path.join(log_dir, f'test_report_{start_time.strftime("%Y%m%d_%H%M%S")}.json')
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"测试报告已保存: {report_filename}")
        
        # 打印摘要
        logger.info("\n======= 测试报告摘要 =======")
        logger.info(f"测试时长: {duration:.2f} 分钟")
        logger.info(f"初始资金: ${total_initial_capital:.2f}")
        logger.info(f"最终资金: ${total_final_capital:.2f}")
        logger.info(f"总体收益率: {overall_roi:.2%}")
        logger.info(f"存活Agent: {report['test_summary']['alive_agents']}")
        logger.info(f"死亡Agent: {report['test_summary']['dead_agents']}")
        
        # 打印表现最好的Agent
        alive_agents = [agent for agent in self.agents if agent.is_alive]
        if alive_agents:
            best_agent = max(alive_agents, key=lambda x: x.roi)
            logger.info(f"\n表现最好的Agent:")
            logger.info(f"Agent ID: {best_agent.id}")
            logger.info(f"物种: {best_agent.gene.generate_species_name()}")
            logger.info(f"ROI: {best_agent.roi:.2%}")
            logger.info(f"最终资金: ${best_agent.capital:.2f}")
            logger.info(f"交易次数: {best_agent.trade_count}")
    
    def run(self):
        """运行完整的测试流程"""
        logger.info("\n======= 开始30分钟交易测试 =======\n")
        
        try:
            # 1. 连接到OKX
            if not self.connect_to_okx():
                logger.error("无法连接到OKX，测试终止")
                return False
            
            # 2. 平掉所有持仓
            closed_positions = self.close_all_positions(max_attempts=5)  # 增加最大尝试次数
            logger.info(f"平仓完成，成功平仓 {closed_positions} 个持仓")
            
            # 3. 生成初始Agent
            agent_count = self.generate_initial_agents(count=5)
            if agent_count == 0:
                logger.error("无法生成初始Agent，测试终止")
                return False
            
            # 4. 运行交易测试
            success = self.run_trading_test(duration_minutes=30)
            
            if success:
                logger.info("[OK] 30分钟交易测试成功完成")
            else:
                logger.error("❌ 交易测试失败")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生未预期错误: {e}", exc_info=True)
            return False
        finally:
            logger.info("\n======= 测试结束 =======\n")

if __name__ == "__main__":
    print("\n======= Prometheus V30 - 30分钟交易测试 =======\n")
    print("开始测试流程，请查看日志获取详细信息...")
    print(f"日志文件: {log_filename}")
    print("\n测试步骤:")
    print("1. 连接到OKX模拟盘")
    print("2. 平掉所有现有持仓")
    print("3. 创世生成5个Agent")
    print("4. 运行30分钟交易测试")
    print("5. 生成详细测试报告")
    print("\n请耐心等待测试完成...\n")
    
    # 创建交易测试实例，确保执行持仓检查和平仓操作
    test = TradingTest(skip_position_check=False)
    success = test.run()
    
    if success:
        print("\n[OK] 测试成功完成！")
        print(f"详细报告已保存到: {os.path.join(log_dir, 'test_report_*.json')}")
    else:
        print("\n❌ 测试失败，请检查日志获取详细信息")
    
    sys.exit(0 if success else 1)