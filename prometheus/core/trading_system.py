"""
Prometheus v3.0 - Live Trading System

这是实盘交易系统的核心，相当于整个系统的"总指挥"。

架构设计：
1. LiveTradingSystem：总指挥，负责调度所有模块
2. OKXAdapter：与交易所API通信，封装所有外部接口
3. MarketRegimeDetector：判断市场状态（牛市/熊市/震荡）
4. SimpleCapitalManager：管理资金分配
5. LiveAgent[]：多个Agent并行交易，相互竞争

工作流程（每60秒一次循环）：
1. 获取市场数据（价格、K线）
2. 检测市场状态（强牛/弱牛/震荡/弱熊/强熊）
3. 更新所有Agent的状态，生成交易信号
4. 执行交易（经过风控检查）
5. 检查Agent生命周期（繁殖/死亡）
6. 生成交易报告

作者: Manus AI
日期: 2025-11-29
"""

import logging
import time
import signal
import sys
import os
import psutil
import pickle
import traceback
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import threading

from adapters.okx_adapter import OKXTradingAdapter
from live_agent import LiveAgent
from market_regime import MarketRegimeDetector
from simple_capital_manager import SimpleCapitalManager
from backtest_live_bridge import BacktestLiveBridge, create_bridge_adapter
from monitoring.system_monitor import SystemMonitor
from monitoring.trade_reporter import TradeReporter
from monitoring.alert_system import AlertSystem

logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """
    系统健康监控器
    
    负责监控系统各组件的健康状态，检测异常并触发恢复机制。
    """
    
    def __init__(self, config):
        self.config = config
        self.health_check_interval = config.get('health_monitor', {}).get('check_interval', 300)  # 默认5分钟
        self.max_api_response_time = config.get('health_monitor', {}).get('max_api_response_time', 5)  # 最大API响应时间
        self.max_memory_usage = config.get('health_monitor', {}).get('max_memory_usage', 80)  # 最大内存使用率(%)
        self.max_cpu_usage = config.get('health_monitor', {}).get('max_cpu_usage', 90)  # 最大CPU使用率(%)
        
        # 组件健康状态
        self.health_status = {
            'api_connection': True,
            'market_data': True,
            'agents': True,
            'risk_manager': True,
            'last_api_response_time': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'last_health_check': None,
            'consecutive_failures': {
                'api_connection': 0,
                'market_data': 0,
                'agents': 0,
                'risk_manager': 0
            },
            'last_error_time': {
                'api_connection': None,
                'market_data': None,
                'agents': None,
                'risk_manager': None
            }
        }
        
        # 恢复策略配置
        self.recovery_strategies = config.get('health_monitor', {}).get('recovery_strategies', {
            'api_connection': {'max_failures': 3, 'action': 'restart_adapter'},
            'market_data': {'max_failures': 5, 'action': 'wait_retry'},
            'agents': {'max_failures': 3, 'action': 'recreate_failed_agents'},
            'risk_manager': {'max_failures': 2, 'action': 'restart_risk_manager'}
        })
        
        logger.info("系统健康监控器初始化完成")
    
    def update_health_status(self, component, status, error_msg=None):
        """更新组件健康状态"""
        if component in self.health_status:
            self.health_status[component] = status
            self.health_status['last_health_check'] = datetime.now()
            
            if not status:
                self.health_status['consecutive_failures'][component] += 1
                self.health_status['last_error_time'][component] = datetime.now()
                logger.warning(f"组件 {component} 不健康: {error_msg}，连续失败次数: {self.health_status['consecutive_failures'][component]}")
            else:
                self.health_status['consecutive_failures'][component] = 0
    
    def check_system_resources(self):
        """检查系统资源使用情况"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_percent()
        cpu_info = process.cpu_percent(interval=1)
        
        self.health_status['memory_usage'] = memory_info
        self.health_status['cpu_usage'] = cpu_info
        
        # 检查内存和CPU使用情况
        memory_healthy = memory_info < self.max_memory_usage
        cpu_healthy = cpu_info < self.max_cpu_usage
        
        if not memory_healthy:
            logger.warning(f"内存使用率过高: {memory_info:.2f}%")
        if not cpu_healthy:
            logger.warning(f"CPU使用率过高: {cpu_info:.2f}%")
        
        return memory_healthy and cpu_healthy
    
    def check_api_response_time(self, response_time):
        """检查API响应时间"""
        self.health_status['last_api_response_time'] = response_time
        healthy = response_time < self.max_api_response_time
        
        if not healthy:
            logger.warning(f"API响应时间过长: {response_time:.2f}秒")
        
        return healthy
    
    def get_health_status(self):
        """获取当前健康状态摘要"""
        return {
            'overall_status': all(self.health_status[comp] for comp in ['api_connection', 'market_data', 'agents', 'risk_manager']),
            'components': {
                comp: {
                    'status': self.health_status[comp],
                    'consecutive_failures': self.health_status['consecutive_failures'][comp],
                    'last_error': self.health_status['last_error_time'][comp].isoformat() if self.health_status['last_error_time'][comp] else None
                }
                for comp in ['api_connection', 'market_data', 'agents', 'risk_manager']
            },
            'resources': {
                'memory_usage': self.health_status['memory_usage'],
                'cpu_usage': self.health_status['cpu_usage'],
                'api_response_time': self.health_status['last_api_response_time']
            },
            'last_check': self.health_status['last_health_check'].isoformat() if self.health_status['last_health_check'] else None
        }
    
    def should_recover(self, component):
        """检查是否需要触发恢复机制"""
        failures = self.health_status['consecutive_failures'].get(component, 0)
        max_failures = self.recovery_strategies.get(component, {}).get('max_failures', 3)
        return failures >= max_failures
    
    def get_recovery_action(self, component):
        """获取恢复操作"""
        return self.recovery_strategies.get(component, {}).get('action', 'wait_retry')


class LiveTradingSystem:
    """
    实盘交易系统 - 系统的总指挥
    
    负责：
    1. 调度所有模块的运行
    2. 管理Agent的生命周期（创建/繁殖/死亡）
    3. 执行交易并进行风控检查
    4. 生成交易报告和日志
    5. 处理异常和错误
    6. 监控系统健康状态
    7. 实现自动恢复机制
    
    为什么需要这个层？
    - 将业务逻辑（策略、进化）与技术实现（API调用）解耦
    - 统一的风控和错误处理
    - 便于测试和维护
    - 提高系统稳定性和可靠性
    """
    
    def __init__(self, config, okx_config):
        """
        初始化
        
        Args:
            config: Prometheus配置
            okx_config: OKX API配置
        """
        self.config = config
        self.okx_config = okx_config
        
        # 初始化桥接器 - 这是连接回测和实盘的关键组件
        self.bridge = create_bridge_adapter({
            'mode': 'live',
            'backtest': config.get('backtest', {}),
            'live_only': ['exchanges', 'api_keys', 'webhook_urls']
        })
        
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
        
        # 基因种子库 - 预先定义一些表现良好的基因配置
        self.gene_seed_pool = [
            # 趋势跟踪型基因
            {
                'long_threshold': 0.08,
                'short_threshold': -0.08,
                'max_position': 0.8,
                'stop_loss': 0.05,
                'take_profit': 0.12,
                'holding_period': 1800,
                'risk_aversion': 0.8,
                'volatility_adjustment': 0.7,
                'market_state_sensitivity': 1.2,
                'indicator_weights': {
                    'momentum': 1.5,
                    'rsi': 0.8,
                    'macd': 1.2,
                    'bollinger': 0.5
                }
            },
            # 均值回归型基因
            {
                'long_threshold': 0.05,
                'short_threshold': -0.05,
                'max_position': 0.6,
                'stop_loss': 0.04,
                'take_profit': 0.08,
                'holding_period': 600,
                'risk_aversion': 1.2,
                'volatility_adjustment': 1.5,
                'market_state_sensitivity': 0.8,
                'indicator_weights': {
                    'momentum': 0.6,
                    'rsi': 1.5,
                    'macd': 0.8,
                    'bollinger': 1.7
                }
            },
            # 平衡型基因
            {
                'long_threshold': 0.06,
                'short_threshold': -0.06,
                'max_position': 0.7,
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'holding_period': 1200,
                'risk_aversion': 1.0,
                'volatility_adjustment': 1.0,
                'market_state_sensitivity': 1.0,
                'indicator_weights': {
                    'momentum': 1.0,
                    'rsi': 1.0,
                    'macd': 1.0,
                    'bollinger': 1.0
                }
            },
            # 高风险高回报型基因 - 调整后更易触发交易
            {
                'long_threshold': 0.06,
                'short_threshold': -0.06,
                'max_position': 0.9,
                'stop_loss': 0.07,
                'take_profit': 0.15,
                'holding_period': 900,
                'risk_aversion': 0.6,
                'volatility_adjustment': 0.5,
                'market_state_sensitivity': 1.5,
                'indicator_weights': {
                    'momentum': 1.8,
                    'rsi': 0.6,
                    'macd': 1.4,
                    'bollinger': 0.7
                }
            },
            # 保守型基因
            {
                'long_threshold': 0.04,
                'short_threshold': -0.04,
                'max_position': 0.5,
                'stop_loss': 0.03,
                'take_profit': 0.06,
                'holding_period': 2400,
                'risk_aversion': 1.5,
                'volatility_adjustment': 1.8,
                'market_state_sensitivity': 0.6,
                'indicator_weights': {
                    'momentum': 0.8,
                    'rsi': 1.2,
                    'macd': 0.9,
                    'bollinger': 1.1
                }
            }
        ]
        
        # 基因种子使用配置
        self.gene_seed_config = {
            'use_seed_probability': config.get('gene_pool', {}).get('use_seed_probability', 0.3),  # 30%概率使用种子
            'seed_mutation_rate': config.get('gene_pool', {}).get('seed_mutation_rate', 0.2)  # 种子基因变异率
        }
        
        # 基因多样性监测配置
        self.diversity_monitor_config = {
            'monitor_interval': config.get('diversity_monitor', {}).get('interval', 3600),  # 监测间隔（秒）
            'min_diversity_threshold': config.get('diversity_monitor', {}).get('min_threshold', 0.2),  # 最小多样性阈值
            'max_similarity_threshold': config.get('diversity_monitor', {}).get('max_similarity', 0.8),  # 最大相似度阈值
            'diversity_recovery_action': config.get('diversity_monitor', {}).get('recovery_action', 'introduce_random')  # 恢复措施
        }
        
        # 多样性监测状态
        self.diversity_stats = {
            'last_monitor_time': None,
            'average_distance': 0.0,
            'minimum_distance': 0.0,
            'max_similarity': 0.0,
            'diversity_history': [],
            'recovery_actions_taken': 0
        }
        
        # 运行状态
        self.running = False
        self.stop_requested = False
        self.safe_mode = False
        self.safe_mode_entry_time = None
        self.safe_mode_exit_time = None
        
        # 错误计数器
        self.error_counters = {
            'market_data': 0,
            'order_execution': 0,
            'agent_update': 0
        }
        
        # 最后一次成功操作的时间
        self.last_successful_operation = {
            'market_data': None,
            'order_execution': None,
            'agent_update': None
        }
        
        # 状态持久化配置
        self.state_dir = os.path.join(os.getcwd(), 'system_state')
        if not os.path.exists(self.state_dir):
            os.makedirs(self.state_dir)
        
        # 上次持久化状态的时间
        self.last_state_save_time = datetime.now()
        
        # 异常模式检测
        self.abnormal_patterns = {
            'rapid_price_changes': [],
            'failed_orders_sequence': [],
            'api_timeouts': []
        }
        
        # 待恢复的代理信息
        self._pending_agents_to_recreate = []
        
        # 健康监控器
        self.health_monitor = SystemHealthMonitor(config)
        
        # 初始化监控与报告系统
        self.system_monitor = SystemMonitor(config.get('monitoring', {}))
        self.trade_reporter = TradeReporter(config.get('reporting', {}))
        self.alert_system = AlertSystem(config.get('alerts', {}))
        
        # 恢复机制锁
        self.recovery_lock = threading.RLock()
        
        # 系统运行统计
        self.system_stats = {
            'recovery_attempts': 0,
            'component_restarts': {
                'adapter': 0,
                'risk_manager': 0,
                'agents': 0,
                'market_data': 0
            },
            'last_recovery_time': None,
            'crashes': 0,
            'restarts': 0
        }
        
        # 性能优化相关配置
        self.performance = {
            'enable_concurrency': config.get('performance', {}).get('enable_concurrency', True),
            'max_concurrent_agents': config.get('performance', {}).get('max_concurrent_agents', 10),
            'api_rate_limit': config.get('performance', {}).get('api_rate_limit', 60),  # 每分钟请求数
            'market_data_cache_ttl': config.get('performance', {}).get('market_data_cache_ttl', 5),  # 缓存有效期(秒)
            'batch_trade_size': config.get('performance', {}).get('batch_trade_size', 5),  # 批量交易大小
            'agent_update_timeout': config.get('performance', {}).get('agent_update_timeout', 3),  # 代理更新超时(秒)
            'trade_execution_timeout': config.get('performance', {}).get('trade_execution_timeout', 5)  # 交易执行超时(秒)
        }
        
        # 性能统计
        self.performance_stats = {
            'loop_times': [],
            'agent_update_times': [],
            'trade_execution_times': [],
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'throttled_calls': 0
        }
        
        # API调用节流控制
        self.api_call_history = []
        
        # 市场数据缓存
        self._market_data_cache = {
            'data': None,
            'timestamp': 0
        }
        
        # 价格历史缓存
        self._price_history_cache = {
            'data': {},
            'timestamp': {}
        }
        
        # 市场数据缓存时间记录
        self._market_data_cache_times = {}
        
        # 尝试加载之前的状态
        self._load_last_state()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("实盘交易系统初始化完成，回测-实盘桥接器已启用，监控系统已初始化")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备优雅关闭系统")
        self.safe_shutdown()
    
    def safe_shutdown(self):
        """安全关闭系统，包括状态保存和持仓清理"""
        logger.info("开始安全关闭流程...")
        
        # 保存当前状态
        self._save_state()
        
        # 请求停止
        self.stop_requested = True
    
    def _save_state(self):
        """保存系统状态到文件"""
        try:
            state_file = os.path.join(self.state_dir, f"state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl")
            state = {
                'timestamp': datetime.now(),
                'agents': [agent.get_state() for agent in self.agents if agent.is_alive],
                'capital_manager': self.capital_manager.get_state() if hasattr(self.capital_manager, 'get_state') else None,
                'stats': self.stats,
                'system_stats': self.system_stats,
                'error_counters': self.error_counters,
                'market_detector_state': self.market_detector.get_state() if hasattr(self.market_detector, 'get_state') else None
            }
            
            with open(state_file, 'wb') as f:
                pickle.dump(state, f)
            
            # 保留最近5个状态文件
            self._clean_old_state_files()
            
            logger.info(f"系统状态已保存到 {state_file}")
            self.last_state_save_time = datetime.now()
            return True
        except Exception as e:
            logger.error(f"保存系统状态失败: {e}")
            return False
    
    def _clean_old_state_files(self):
        """清理旧的状态文件，只保留最近的几个"""
        try:
            state_files = [f for f in os.listdir(self.state_dir) if f.startswith('state_') and f.endswith('.pkl')]
            state_files.sort()
            
            # 删除最旧的文件，保留最近5个
            files_to_delete = state_files[:-5]
            for file in files_to_delete:
                os.remove(os.path.join(self.state_dir, file))
        except Exception as e:
            logger.error(f"清理旧状态文件失败: {e}")
    
    def _load_last_state(self):
        """加载最近的系统状态"""
        try:
            state_files = [f for f in os.listdir(self.state_dir) if f.startswith('state_') and f.endswith('.pkl')]
            if not state_files:
                logger.info("没有找到可恢复的状态文件")
                return False
            
            # 获取最新的状态文件
            state_files.sort()
            last_state_file = state_files[-1]
            state_file_path = os.path.join(self.state_dir, last_state_file)
            
            with open(state_file_path, 'rb') as f:
                state = pickle.load(f)
            
            logger.info(f"加载状态文件: {last_state_file}，保存时间: {state['timestamp']}")
            
            # 恢复统计数据
            self.stats = state.get('stats', self.stats)
            self.system_stats = state.get('system_stats', self.system_stats)
            self.error_counters = state.get('error_counters', self.error_counters)
            
            # 增加重启计数
            self.system_stats['restarts'] += 1
            
            # 保存代理状态信息，用于可能的重建
            self._pending_agents_to_recreate = state.get('agents', [])
            
            # 发送重启通知
            if hasattr(self, 'alert_system'):
                self.alert_system.send_alert(
                    'system_restart',
                    f"系统从状态文件恢复，上次保存时间: {state['timestamp']}",
                    severity='warning'
                )
            
            return True
        except Exception as e:
            logger.error(f"加载系统状态失败: {e}")
            return False
    
    def initialize_agents(self):
        """初始化交易代理"""
        logger.info(f"正在初始化 {self.config['initial_agents']} 个交易代理...")
        logger.info(f"基因种子配置: 使用概率={self.gene_seed_config['use_seed_probability']}, 变异率={self.gene_seed_config['seed_mutation_rate']}")
        
        import random
        import numpy as np
        
        for i in range(self.config['initial_agents']):
            # 从资金池分配资金
            capital = self.capital_manager.allocate_capital(
                self.config['capital_manager']['min_agent_capital']
            )
            
            if capital > 0:
                # 决定是否使用基因种子
                use_seed = random.random() < self.gene_seed_config['use_seed_probability']
                gene = None
                
                if use_seed and self.gene_seed_pool:
                    # 从种子库中随机选择一个基因
                    gene = random.choice(self.gene_seed_pool).copy()
                    
                    # 应用变异
                    if random.random() < self.gene_seed_config['seed_mutation_rate']:
                        # 对基因参数进行小幅度变异
                        for param in gene:
                            if param == 'indicator_weights':
                                # 处理指标权重的变异
                                for weight_param in gene[param]:
                                    gene[param][weight_param] *= np.random.normal(1.0, 0.1)  # 正态分布变异
                                    gene[param][weight_param] = max(0.1, min(2.0, gene[param][weight_param]))  # 限制范围
                            else:
                                # 对其他参数进行变异
                                gene[param] *= np.random.normal(1.0, 0.1)  # 正态分布变异
                                
                                # 确保参数在合理范围内
                                if param == 'max_position':
                                    gene[param] = max(0.1, min(1.0, gene[param]))
                                elif param in ['long_threshold', 'take_profit']:
                                    gene[param] = max(0.01, min(0.2, gene[param]))
                                elif param in ['short_threshold', 'stop_loss']:
                                    gene[param] = min(-0.01, max(-0.2, gene[param]))
                                elif param == 'holding_period':
                                    gene[param] = max(60, min(7200, gene[param]))
                                elif param in ['risk_aversion', 'volatility_adjustment', 'market_state_sensitivity']:
                                    gene[param] = max(0.1, min(2.0, gene[param]))
                    
                    logger.info(f"代理 {i+1} 使用基因种子（变异: {random.random() < self.gene_seed_config['seed_mutation_rate']}")
                else:
                    logger.info(f"代理 {i+1} 使用随机生成的基因")
                
                agent = LiveAgent(
                    agent_id=f"agent_{i+1}",
                    initial_capital=capital,
                    config=self.config,
                    gene=gene  # 如果gene为None，LiveAgent会生成随机基因
                )
                self.agents.append(agent)
                logger.info(f"创建代理 {agent.agent_id}，分配资金 ${capital:.2f}")
            else:
                logger.warning(f"代理 {i+1} 资金不足")
        
        logger.info(f"初始化完成 {len(self.agents)} 个代理")
    
    def run(self, duration_seconds=3600):
        """
        运行交易系统
        
        Args:
            duration_seconds: 运行时长（秒）
        """
        logger.info(f"开始实盘交易，运行时长 {duration_seconds} 秒...")
        
        self.stats['start_time'] = datetime.now()
        self.running = True
        
        # 初始化交易代理
        self.initialize_agents()
        
        # 启动监控与报告线程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.reporting_thread = threading.Thread(target=self._reporting_loop, daemon=True)
        self.monitoring_thread.start()
        self.reporting_thread.start()
        logger.info("监控与报告线程已启动")
        
        # 获取初始账户状态
        try:
            initial_summary = self.adapter.get_account_summary()
            logger.info(f"初始账户余额: ${initial_summary['total_equity']:.2f}")
        except Exception as e:
            logger.error(f"获取初始账户状态失败: {e}")
            # 尝试恢复适配器连接
            self._recover_adapter()
        
        # 主循环
        end_time = time.time() + duration_seconds
        update_interval = self.config['trading']['update_interval']
        
        # 健康检查计时器
        next_health_check = time.time() + self.health_monitor.health_check_interval
        
        # 性能报告计时器
        next_performance_report = time.time() + 300  # 每5分钟报告一次性能
        
        iteration = 0
        while self.running and time.time() < end_time and not self.stop_requested:
            iteration += 1
            loop_start = time.time()
            
            # 保存当前迭代次数用于暂停交易计算
            self._current_iteration = iteration
            
            try:
                # 定期执行健康检查
                if time.time() >= next_health_check:
                    self._perform_health_check()
                    next_health_check = time.time() + self.health_monitor.health_check_interval
                
                # 定期报告性能统计
                if time.time() >= next_performance_report:
                    self._report_performance_stats()
                    next_performance_report = time.time() + 300
                
                logger.info(f"=== 迭代 {iteration} ===")
                
                # 1. 获取市场数据
                market_data = self._get_market_data()
                
                # 2. 更新市场状态
                regime = self._update_market_regime(market_data)
                logger.info(f"市场状态: {regime}")
                
                # 3. 更新所有交易代理
                self._update_agents(market_data, regime)
                
                # 4. 计算并记录交易信心指数（基于市场数据和技术指标）
                try:
                    # 导入numpy用于计算
                    import numpy as np
                    
                    # 计算基于市场数据的交易信心指数
                    def calculate_market_confidence(market_data):
                        # 检查是否有足够的K线数据
                        candles = market_data.get('candles', [])
                        
                        if len(candles) < 100:
                            logger.warning(f"K线数据不足100条 ({len(candles)}条)，无法计算完整的技术指标")
                            return 0.0, "K线数据不足"
                        
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
                        gain = np.where(delta > 0, delta, 0)
                        loss = np.where(delta < 0, -delta, 0)
                        
                        avg_gain = np.mean(gain[-14:])
                        avg_loss = np.mean(loss[-14:])
                        
                        if np.isnan(avg_gain) or np.isnan(avg_loss) or avg_loss == 0:
                            rsi = 50  # 默认值
                        else:
                            rs = avg_gain / avg_loss
                            rsi = 100 - (100 / (1 + rs))
                        
                        # 3. MACD (Moving Average Convergence Divergence)
                        def exponential_moving_average(data, span):
                            alpha = 2 / (span + 1)
                            weights = (1 - alpha) ** np.arange(len(data)-1, -1, -1)
                            weights /= weights.sum()
                            return np.dot(data, weights)
                        
                        prices_needed = max(12, 26)
                        recent_prices = close_prices[-prices_needed:]
                        
                        ema12 = exponential_moving_average(recent_prices, 12)
                        ema26 = exponential_moving_average(recent_prices, 26)
                        macd_line = ema12 - ema26
                        
                        if len(close_prices) > 34:
                            macd_values = [exponential_moving_average(close_prices[-i-26:-i], 12) - 
                                          exponential_moving_average(close_prices[-i-26:-i], 26) 
                                          for i in range(5)]
                            signal_line = exponential_moving_average(np.array(macd_values), 9)
                            macd_hist = macd_line - signal_line
                        else:
                            macd_hist = macd_line
                        
                        # 4. Bollinger Bands
                        sma20 = np.mean(close_prices[-20:])
                        std20 = np.std(close_prices[-20:])
                        upper_band = sma20 + (2 * std20)
                        lower_band = sma20 - (2 * std20)
                        bb_width = (upper_band - lower_band) / sma20 if sma20 > 0 else 0.01
                        bb_position = (close_prices[-1] - lower_band) / bb_width if bb_width > 0 else 0.5
                        
                        # 综合信号计算 - 使用系统级默认权重
                        signal_components = []
                        
                        # 动量信号
                        if abs(momentum) > 0.01:  # 只有当动量足够显著时才考虑
                            momentum_signal = momentum
                            momentum_signal = max(-0.8, min(0.8, momentum_signal))
                            signal_components.append(momentum_signal)
                        
                        # RSI信号
                        if rsi < 30 or rsi > 70:
                            if rsi < 30:  # 超卖
                                rsi_signal = 0.2 * (30 - rsi) / 30
                            else:  # 超买
                                rsi_signal = -0.2 * (rsi - 70) / 30
                            rsi_signal = max(-0.8, min(0.8, rsi_signal))
                            signal_components.append(rsi_signal)
                        
                        # MACD信号
                        if sma20 > 0:
                            normalization_factor = max(sma20 * 0.01, 0.1)
                            raw_macd_signal = macd_hist / normalization_factor
                            raw_macd_signal = max(-5.0, min(5.0, raw_macd_signal))
                            macd_signal = 0.2 * raw_macd_signal
                            macd_signal = max(-0.8, min(0.8, macd_signal))
                            signal_components.append(macd_signal)
                        
                        # 布林带信号
                        if bb_position < 0.3 or bb_position > 0.7:
                            if bb_position < 0.3:
                                bb_signal = 0.2 * (0.3 - bb_position) / 0.3
                            else:
                                bb_signal = -0.2 * (bb_position - 0.7) / 0.3
                            bb_signal = max(-0.8, min(0.8, bb_signal))
                            signal_components.append(bb_signal)
                        
                        # 计算最终信心指数
                        if signal_components:
                            # 简单平均作为综合指数
                            confidence_index = sum(signal_components) / len(signal_components)
                            # 确保范围在[-1, 1]之间
                            confidence_index = max(-1.0, min(1.0, confidence_index))
                            reason = f"基于{len(signal_components)}个技术指标计算 (动量, RSI, MACD, 布林带)"
                        else:
                            confidence_index = 0.0
                            reason = "无明显技术指标信号"
                        
                        return confidence_index, reason
                    
                    # 调用计算函数
                    trading_confidence, confidence_reason = calculate_market_confidence(market_data)
                    
                    # 记录交易信心指数
                    logger.info(f"交易信心指数: {trading_confidence:.4f} ({confidence_reason})")
                    
                except Exception as e:
                    logger.error(f"计算交易信心指数失败: {e}")
                    logger.info(f"交易信心指数: 0.0 (计算出错)")
                
                # 4. 执行交易
                self._execute_trades()
                
                # 5. 检查繁殖和死亡
                self._check_lifecycle()
                
                # 6. 打印状态
                self._print_status()
                
                # 7. 检查是否需要恢复操作
                self._check_and_recover()
                
                # 8. 等待下一次更新
                elapsed = time.time() - loop_start
                self.performance_stats['loop_times'].append(elapsed)
                
                # 动态调整更新间隔（基于系统负载）
                if len(self.performance_stats['loop_times']) > 10:
                    avg_loop_time = sum(self.performance_stats['loop_times'][-10:]) / 10
                    # 如果平均循环时间超过更新间隔的80%，考虑调整
                    if avg_loop_time > (update_interval * 0.8):
                        # 临时降低并发度以减轻系统负载
                        if self.performance['enable_concurrency']:
                            self.performance['max_concurrent_agents'] = max(3, self.performance['max_concurrent_agents'] - 2)
                            logger.warning(f"系统负载过高，调整最大并发代理数: {self.performance['max_concurrent_agents']}")
                    else:
                        # 系统负载正常，可以逐渐恢复并发度
                        self.performance['max_concurrent_agents'] = min(20, self.performance['max_concurrent_agents'] + 1)
                
                sleep_time = max(0, update_interval - elapsed)
                if sleep_time > 0:
                    logger.debug(f"休眠 {sleep_time:.1f}秒...")
                    time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"交易循环错误: {e}", exc_info=True)
                self.stats['failed_trades'] += 1
                self.error_counters['market_data'] += 1
                self.health_monitor.update_health_status('market_data', False, str(e))
                
                # 尝试执行必要的恢复操作
                self._handle_critical_error(e)
                
                # 错误后等待，时间随错误次数增加
                wait_time = min(30, 5 + (self.error_counters['market_data'] * 2))
                logger.info(f"错误后等待 {wait_time}秒...")
                time.sleep(wait_time)
        
        # 停止交易
        self.stop()
        
        # 输出最终性能报告
        self._report_performance_stats()
        
        logger.info("实盘交易完成")
    
    def _report_performance_stats(self):
        """
        报告系统性能统计
        """
        try:
            # 安全检查
            if not hasattr(self, 'performance_stats') or not self.performance_stats:
                logger.info("性能统计: 配置缺失")
                return
            
            # 处理空数据情况
            if not self.performance_stats.get('loop_times'):
                logger.info("性能统计: 暂无数据")
                return
            
            # 计算性能指标，添加异常处理
            try:
                loop_times = self.performance_stats.get('loop_times', [])
                if loop_times:
                    avg_loop_time = sum(loop_times) / len(loop_times)
                    max_loop_time = max(loop_times)
                    min_loop_time = min(loop_times)
                else:
                    avg_loop_time = max_loop_time = min_loop_time = 0
            except Exception as e:
                logger.error(f"计算循环时间统计失败: {e}")
                avg_loop_time = max_loop_time = min_loop_time = 0
            
            # 计算代理更新性能
            agent_update_stats = "暂无数据"
            try:
                agent_update_times = self.performance_stats.get('agent_update_times', [])
                if agent_update_times:
                    avg_agent_update = sum(agent_update_times) / len(agent_update_times)
                    agent_update_stats = f"平均: {avg_agent_update:.3f}秒"
            except Exception as e:
                logger.error(f"计算代理更新性能失败: {e}")
            
            # 计算交易执行性能
            trade_execution_stats = "暂无数据"
            try:
                trade_execution_times = self.performance_stats.get('trade_execution_times', [])
                if trade_execution_times:
                    avg_trade_execution = sum(trade_execution_times) / len(trade_execution_times)
                    trade_execution_stats = f"平均: {avg_trade_execution:.3f}秒"
            except Exception as e:
                logger.error(f"计算交易执行性能失败: {e}")
            
            # 计算缓存命中率
            cache_hit_rate = "暂无数据"
            try:
                cache_hits = self.performance_stats.get('cache_hits', 0)
                cache_misses = self.performance_stats.get('cache_misses', 0)
                total_cache = cache_hits + cache_misses
                if total_cache > 0:
                    hit_rate = (cache_hits / total_cache) * 100
                    cache_hit_rate = f"{hit_rate:.1f}%"
            except Exception as e:
                logger.error(f"计算缓存命中率失败: {e}")
            
            # 获取并发设置
            concurrent_agents = "未知"
            try:
                if hasattr(self, 'performance'):
                    concurrent_agents = str(self.performance.get('max_concurrent_agents', '未知'))
            except Exception as e:
                logger.error(f"获取并发设置失败: {e}")
            
            # 生成报告
            logger.info("======== 性能统计报告 ========")
            logger.info(f"循环时间: 平均 {avg_loop_time:.3f}秒, 最大 {max_loop_time:.3f}秒, 最小 {min_loop_time:.3f}秒")
            logger.info(f"代理更新性能: {agent_update_stats}")
            logger.info(f"交易执行性能: {trade_execution_stats}")
            logger.info(f"API调用: 总计 {self.performance_stats.get('api_calls', 0)}次")
            logger.info(f"API节流: 总计 {self.performance_stats.get('throttled_calls', 0)}次")
            logger.info(f"缓存命中率: {cache_hit_rate}")
            logger.info(f"当前并发设置: {concurrent_agents}个代理")
            logger.info("==============================")
            
            # 安全地重置部分统计数据
            try:
                # 保留最近的100条循环时间用于动态调整
                if len(loop_times) > 100:
                    self.performance_stats['loop_times'] = loop_times[-100:]
                
                # 重置详细的更新和执行时间，避免内存占用过大
                self.performance_stats['agent_update_times'] = []
                self.performance_stats['trade_execution_times'] = []
            except Exception as e:
                logger.error(f"重置性能统计失败: {e}")
        
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
    
    def _throttle_api_calls(self, required_calls=1):
        """API调用节流控制"""
        try:
            # 参数验证
            if required_calls <= 0:
                return
            
            current_time = time.time()
            
            # 确保api_call_history存在
            if not hasattr(self, 'api_call_history'):
                self.api_call_history = []
            
            # 清理过期的调用记录
            self.api_call_history = [t for t in self.api_call_history if current_time - t < 60]
            
            # 检查是否需要节流
            if len(self.api_call_history) + required_calls > self.performance.get('api_rate_limit', 60):
                # 安全检查：避免空列表导致的错误
                if self.api_call_history:
                    oldest_call = min(self.api_call_history)
                    wait_time = 60 - (current_time - oldest_call) + 0.1  # 加0.1秒确保安全
                    
                    if wait_time > 0 and wait_time < 30:  # 限制最大等待时间，避免死等
                        logger.debug(f"API调用节流，等待 {wait_time:.2f}秒")
                        if hasattr(self.performance_stats, 'throttled_calls'):
                            self.performance_stats['throttled_calls'] += 1
                        time.sleep(wait_time)
                        
                        # 再次清理过期记录
                        self.api_call_history = [t for t in self.api_call_history if current_time - t < 60]
                    else:
                        logger.warning(f"节流等待时间异常 ({wait_time:.2f}秒)，跳过节流")
            
            # 记录新的调用，防止记录过多导致内存问题
            max_history_size = 1000  # 设置最大历史记录数
            for _ in range(required_calls):
                self.api_call_history.append(time.time())
                if hasattr(self.performance_stats, 'api_calls'):
                    self.performance_stats['api_calls'] += 1
            
            # 限制历史记录大小
            if len(self.api_call_history) > max_history_size:
                self.api_call_history = self.api_call_history[-max_history_size:]
        except Exception as e:
            logger.error(f"API节流控制异常: {e}")
            # 出错时不抛出异常，避免影响主流程
    
    def _get_market_data(self):
        """获取市场数据，增强版：增加MarketDataManager健康状态检查和SSL错误处理"""
        import ssl
        import socket
        
        # 检查缓存是否有效
        cache_ttl = self.performance['market_data_cache_ttl']
        
        # 如果发生SSL错误，延长缓存有效期以避免频繁重试
        is_ssl_error = self.health_monitor.get_health_status().get('market_data', {}).get('last_error') and \
                      'SSL' in self.health_monitor.get_health_status().get('market_data', {}).get('last_error', '')
        
        # 根据错误状态动态调整缓存TTL
        adjusted_cache_ttl = cache_ttl * 2 if is_ssl_error else cache_ttl
        
        # 检查缓存有效性
        if (self._market_data_cache['data'] and 
            time.time() - self._market_data_cache['timestamp'] < adjusted_cache_ttl):
            cache_age = time.time() - self._market_data_cache['timestamp']
            logger.debug(f"使用市场数据缓存 (缓存时间: {cache_age:.1f}秒)")
            self.performance_stats['cache_hits'] += 1
            return self._market_data_cache['data']
        
        self.performance_stats['cache_misses'] += 1
        spot_symbol = self.config['markets']['spot']['symbol']
        futures_symbol = self.config['markets']['futures']['symbol']
        
        # 检查MarketDataManager的健康状态
        if hasattr(self.adapter, 'market_data'):
            health_status = self.adapter.market_data.get_health_status() if hasattr(self.adapter.market_data, 'get_health_status') else {'is_healthy': True}
            if hasattr(health_status, 'get') and not health_status.get('is_healthy', True):
                logger.warning(f"组件 market_data 不健康: {health_status.get('last_error', 'unknown')}，连续失败次数: {health_status.get('consecutive_failures', 0)}")
                
                # 如果连续失败次数超过阈值，尝试执行轻量级恢复
                if health_status.get('consecutive_failures', 0) >= 3:
                    logger.warning("检测到市场数据组件连续失败，尝试轻量级恢复...")
                    try:
                        # 重置API连接
                        if hasattr(self.adapter.market_data, 'reset_connection'):
                            self.adapter.market_data.reset_connection()
                            logger.info("成功重置MarketDataManager连接")
                    except Exception as recovery_error:
                        logger.error(f"重置MarketDataManager连接失败: {recovery_error}")
        
        # API调用节流控制
        self._throttle_api_calls(required_calls=3)  # 获取现货价格、合约价格和K线数据
        
        start_time = time.time()
        
        # 设置最大重试次数
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
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
                
                # 计算API响应时间
                response_time = time.time() - start_time
                self.health_monitor.check_api_response_time(response_time)
                
                # 更新健康状态
                self.health_monitor.update_health_status('api_connection', True)
                self.health_monitor.update_health_status('market_data', True)
                self.error_counters['market_data'] = 0
                self.last_successful_operation['market_data'] = datetime.now()
                
                market_data = {
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
                
                # 更新缓存
                self._market_data_cache['data'] = market_data
                self._market_data_cache['timestamp'] = time.time()
                
                # 同时更新_last_market_data用于错误恢复
                self._last_market_data = market_data
                
                return market_data
            
            except (ssl.SSLError, socket.timeout) as e:
                # 特殊处理SSL错误和超时
                error_str = str(e)
                retry_count += 1
                self.error_counters['market_data'] += 1
                
                # 更新健康状态
                self.health_monitor.update_health_status('market_data', False, error_str)
                
                # 记录SSL握手超时错误
                if isinstance(e, ssl.SSLError) and "handshake operation timed out" in error_str:
                    logger.error(f"SSL握手超时错误: {error_str}，重试次数: {retry_count}/{max_retries}")
                    
                    # 立即尝试重置连接
                    if hasattr(self.adapter, 'market_data') and hasattr(self.adapter.market_data, 'reset_connection'):
                        try:
                            logger.warning("尝试重置SSL连接...")
                            self.adapter.market_data.reset_connection()
                        except Exception as reset_error:
                            logger.error(f"重置连接失败: {reset_error}")
                else:
                    logger.error(f"网络错误: {error_str}，重试次数: {retry_count}/{max_retries}")
                
                # 如果不是最后一次重试，等待后重试
                if retry_count <= max_retries:
                    wait_time = 0.5 * (2 ** (retry_count - 1))  # 指数退避
                    logger.info(f"等待 {wait_time:.2f}秒后重试...")
                    time.sleep(wait_time)
                # 如果是最后一次重试且有缓存，使用缓存
                elif self._market_data_cache['data']:
                    logger.warning("达到最大重试次数，使用缓存的市场数据")
                    return self._market_data_cache['data']
            
            except Exception as e:
                # 处理其他错误
                self.error_counters['market_data'] += 1
                self.health_monitor.update_health_status('market_data', False, str(e))
                logger.error(f"获取市场数据失败: {e}")
                
                # 如果有最近的有效数据，尝试使用缓存数据
                if self._market_data_cache['data']:
                    logger.warning("使用缓存的市场数据")
                    return self._market_data_cache['data']
                
                raise
        
        # 所有重试都失败且没有缓存，抛出异常
        raise Exception("获取市场数据失败：所有重试都已耗尽且没有可用缓存")
    
    def _check_and_recover(self, error=None, component='unknown'):
        """
        检查并执行轻量级恢复策略，特别是针对SSL错误，增强版：包含详细诊断日志
        
        Args:
            error: 捕获到的异常
            component: 出错的组件名称
            
        Returns:
            bool: 恢复是否成功
        """
        import ssl
        import socket
        
        # 记录恢复操作的诊断信息
        recovery_context = {
            "component": component,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__ if error else "N/A"
        }
        logger.info(f"开始对组件 {component} 执行轻量级恢复检查: {json.dumps(recovery_context)}")
        
        recovery_success = False
        
        # 1. 分析错误类型
        is_ssl_error = False
        is_timeout_error = False
        is_ssl_handshake_timeout = False
        error_str = str(error) if error else "未知错误"
        
        if isinstance(error, ssl.SSLError):
            is_ssl_error = True
            is_ssl_handshake_timeout = "handshake operation timed out" in error_str
            
            # 记录SSL错误的详细诊断信息
            self._log_ssl_diagnostic_info(error, f"recovery_{component}")
            
            # 记录SSL错误的关键信息
            if is_ssl_handshake_timeout:
                logger.warning(f"检测到SSL握手超时错误: {error_str}")
                # 记录SSL握手超时的详细上下文
                handshake_context = {
                    "error_code": getattr(error, 'errno', 'N/A'),
                    "component": component,
                    "attempt_time": datetime.now().isoformat()
                }
                logger.info(f"SSL握手超时上下文: {json.dumps(handshake_context)}")
            else:
                logger.warning(f"检测到其他SSL错误: {error_str}")
        elif isinstance(error, socket.timeout):
            is_timeout_error = True
            logger.warning(f"检测到超时错误: {error_str}")
        
        # 2. 根据组件和错误类型执行不同的恢复策略
        if component == 'market_data' or component == 'unknown':
            if is_ssl_error or is_timeout_error:
                logger.info("执行市场数据组件的轻量级恢复...")
                recovery_success = self._recover_market_data()
        
        # 3. 全局连接清理（如果需要）
        if not recovery_success and (is_ssl_error or is_timeout_error):
            logger.info("执行全局连接清理...")
            recovery_success = self._cleanup_connections()
        
        # 4. 如果恢复成功，更新健康状态
        if recovery_success:
            logger.info(f"组件 {component} 的轻量级恢复成功")
            self.health_monitor.update_health_status(component, True)
            self.error_counters[component] = 0 if component in self.error_counters else 0
            self.last_successful_operation[component] = datetime.now()
        else:
            logger.warning(f"组件 {component} 的轻量级恢复失败")
        
        return recovery_success
    
    def _recover_market_data(self):
        """
        恢复市场数据组件的轻量级策略
        
        Returns:
            bool: 恢复是否成功
        """
        success = False
        
        try:
            # 步骤1: 检查并重置MarketDataManager连接
            if hasattr(self.adapter, 'market_data_manager'):
                # 重置连接
                if hasattr(self.adapter.market_data_manager, 'reset_connection'):
                    logger.info("重置MarketDataManager连接...")
                    self.adapter.market_data_manager.reset_connection()
                
                # 清理缓存
                if hasattr(self.adapter.market_data_manager, 'clear_cache'):
                    logger.info("清理MarketDataManager缓存...")
                    self.adapter.market_data_manager.clear_cache()
                
                # 验证连接
                logger.info("验证MarketDataManager连接...")
                # 使用一个简单的价格查询来验证连接是否恢复
                test_symbol = self.config['markets']['spot']['symbol']
                
                # 验证连接时使用较短的超时
                old_timeout = None
                if hasattr(self.adapter.market_data_manager, 'timeout'):
                    old_timeout = self.adapter.market_data_manager.timeout
                    self.adapter.market_data_manager.timeout = 3  # 3秒超时
                
                try:
                    # 尝试获取一个简单的价格
                    test_price = self.adapter.market_data_manager.get_ticker(test_symbol)
                    if test_price:
                        logger.info(f"MarketDataManager连接验证成功，获取到价格: {test_price}")
                        success = True
                    else:
                        logger.warning("MarketDataManager连接验证失败：无法获取价格")
                except Exception as verify_error:
                    logger.error(f"MarketDataManager连接验证失败: {verify_error}")
                finally:
                    # 恢复原始超时设置
                    if old_timeout is not None:
                        self.adapter.market_data_manager.timeout = old_timeout
            
            # 步骤2: 如果MarketDataManager恢复失败，尝试清理本地缓存和状态
            if not success:
                logger.info("清理本地市场数据缓存...")
                # 延长缓存有效期，避免频繁重试
                if hasattr(self, 'performance'):
                    original_ttl = self.performance.get('market_data_cache_ttl', 10)
                    self.performance['market_data_cache_ttl'] = original_ttl * 3
                    logger.info(f"临时延长市场数据缓存有效期至 {original_ttl * 3}秒")
        
        except Exception as recovery_error:
            logger.error(f"市场数据组件恢复过程中出错: {recovery_error}")
        
        return success
    
    def _cleanup_connections(self):
        """
        执行全局连接清理，关闭可能损坏的连接
        
        Returns:
            bool: 清理是否成功
        """
        try:
            logger.info("执行全局网络连接清理...")
            
            # 尝试强制关闭可能的连接
            # 注意：这是一个安全的清理尝试，不应该直接访问底层连接对象
            
            # 重置会话对象（如果存在）
            if hasattr(self.adapter, '_session') and self.adapter._session:
                try:
                    logger.info("重置适配器会话...")
                    self.adapter._session.close()
                    # 通常会话会在下次请求时自动重新创建
                except Exception as session_error:
                    logger.warning(f"重置会话时出错: {session_error}")
            
            # 释放可能的连接池资源
            logger.info("清理完成，等待连接池资源释放...")
            time.sleep(1)  # 短暂暂停，给系统时间释放资源
            
            return True
        except Exception as cleanup_error:
            logger.error(f"全局连接清理失败: {cleanup_error}")
            return False
    
    def _recover_adapter(self, adapter_type='market_data'):
        """
        恢复适配器连接，执行深度清理和重试验证
        
        Args:
            adapter_type: 适配器类型 ('market_data', 'trade', 等)
            
        Returns:
            bool: 恢复是否成功
        """
        import ssl
        import socket
        
        logger.info(f"开始恢复 {adapter_type} 适配器连接")
        
        # 1. 深度连接清理
        logger.info("执行适配器深度连接清理...")
        
        try:
            # 获取对应的适配器
            adapter = None
            if adapter_type == 'market_data':
                adapter = self.adapter.market_data_manager if hasattr(self.adapter, 'market_data_manager') else None
            else:
                adapter = self.adapter
            
            if not adapter:
                logger.warning(f"未找到 {adapter_type} 适配器")
                return False
            
            # 2. 执行连接重置和资源释放
            cleanup_steps = []
            
            # 重置会话/连接池
            if hasattr(adapter, '_session'):
                cleanup_steps.append("重置会话")
                try:
                    if adapter._session:
                        adapter._session.close()
                        # 置为None以便下次使用时重新创建
                        adapter._session = None
                        logger.info("成功重置并关闭会话")
                except Exception as session_error:
                    logger.error(f"重置会话失败: {session_error}")
            
            # 重置HTTP连接
            if hasattr(adapter, 'reset_connection'):
                cleanup_steps.append("重置连接")
                try:
                    adapter.reset_connection()
                    logger.info("成功重置适配器连接")
                except Exception as reset_error:
                    logger.error(f"重置连接失败: {reset_error}")
            
            # 清理缓存
            if hasattr(adapter, 'clear_cache'):
                cleanup_steps.append("清理缓存")
                try:
                    adapter.clear_cache()
                    logger.info("成功清理适配器缓存")
                except Exception as cache_error:
                    logger.error(f"清理缓存失败: {cache_error}")
            
            # 重置任何可能的连接状态标志
            if hasattr(adapter, '_connection_healthy'):
                adapter._connection_healthy = False
            
            # 等待资源释放
            if cleanup_steps:
                logger.info(f"完成清理步骤: {', '.join(cleanup_steps)}，等待资源释放...")
                time.sleep(1.5)  # 稍长的等待时间确保资源完全释放
            
            # 3. 重试验证
            logger.info("开始适配器连接重试验证...")
            
            # 保存原始超时设置
            original_timeout = None
            if hasattr(adapter, 'timeout'):
                original_timeout = adapter.timeout
                # 设置较短的验证超时
                adapter.timeout = 5
            
            # 保存原始重试设置
            original_retries = None
            if hasattr(adapter, 'max_retries'):
                original_retries = adapter.max_retries
                adapter.max_retries = 1  # 验证时只重试一次
            
            verification_success = False
            verification_attempts = 3
            
            for attempt in range(1, verification_attempts + 1):
                try:
                    logger.info(f"验证尝试 {attempt}/{verification_attempts}")
                    
                    # 根据适配器类型选择验证方法
                    if adapter_type == 'market_data':
                        # 市场数据适配器：尝试获取简单的价格数据
                        test_symbol = self.config['markets']['spot']['symbol']
                        if hasattr(adapter, 'get_ticker'):
                            test_data = adapter.get_ticker(test_symbol)
                            if test_data:
                                logger.info(f"市场数据适配器验证成功，获取到数据: {test_data}")
                                verification_success = True
                                break
                    elif adapter_type == 'trade':
                        # 交易适配器：可以尝试获取账户信息或订单状态（只读操作）
                        if hasattr(adapter, 'get_account'):
                            test_data = adapter.get_account()
                            if test_data:
                                logger.info("交易适配器验证成功，获取到账户信息")
                                verification_success = True
                                break
                    else:
                        # 通用验证：检查是否能进行基本连接
                        if hasattr(adapter, '_ping'):
                            ping_result = adapter._ping()
                            if ping_result:
                                logger.info(f"通用适配器验证成功: {ping_result}")
                                verification_success = True
                                break
                    
                    if not verification_success:
                        logger.warning(f"验证尝试 {attempt} 失败，等待后重试...")
                        time.sleep(1)
                        
                except (ssl.SSLError, socket.timeout) as connection_error:
                    logger.error(f"验证尝试 {attempt} 遇到连接错误: {connection_error}")
                    # SSL错误时可以尝试再次清理
                    if isinstance(connection_error, ssl.SSLError) and hasattr(adapter, 'reset_connection'):
                        try:
                            adapter.reset_connection()
                        except Exception:
                            pass
                    if attempt < verification_attempts:
                        time.sleep(2)  # SSL错误等待更长时间
                except Exception as verify_error:
                    logger.error(f"验证尝试 {attempt} 失败: {verify_error}")
                    if attempt < verification_attempts:
                        time.sleep(1)
            
            # 恢复原始设置
            if original_timeout is not None:
                adapter.timeout = original_timeout
            if original_retries is not None:
                adapter.max_retries = original_retries
            
            # 4. 更新健康状态
            if verification_success:
                logger.info(f"{adapter_type} 适配器恢复成功")
                # 更新适配器内部健康状态（如果有）
                if hasattr(adapter, '_connection_healthy'):
                    adapter._connection_healthy = True
                if hasattr(adapter, '_health_status'):
                    adapter._health_status['is_healthy'] = True
                    adapter._health_status['consecutive_failures'] = 0
                    adapter._health_status['last_error'] = None
                return True
            else:
                logger.error(f"{adapter_type} 适配器恢复失败：所有验证尝试都失败")
                return False
                
        except Exception as recovery_error:
            logger.error(f"适配器恢复过程中发生异常: {recovery_error}")
            return False
    
    def _perform_health_check(self):
        """执行系统健康检查"""
        logger.info("执行系统健康检查...")
        
        # 检查系统资源
        resources_healthy = self.health_monitor.check_system_resources()
        
        # 检查API连接
        api_healthy = self._check_api_connection()
        
        # 检查代理状态
        agents_healthy = self._check_agents_health()
        
        # 检查风控管理器
        risk_manager_healthy = self._check_risk_manager()
        
        # 记录健康状态
        health_status = self.health_monitor.get_health_status()
        logger.info(f"健康检查结果: {json.dumps(health_status, indent=2)}")
        
        # 如果资源使用过高，尝试执行资源清理
        if not resources_healthy:
            self._cleanup_resources()
        
        return health_status['overall_status']
    
    def _check_api_connection(self):
        """检查API连接状态"""
        try:
            start_time = time.time()
            self.adapter.get_price(self.config['markets']['spot']['symbol'])
            response_time = time.time() - start_time
            
            healthy = self.health_monitor.check_api_response_time(response_time)
            self.health_monitor.update_health_status('api_connection', healthy)
            return healthy
        except Exception as e:
            self.health_monitor.update_health_status('api_connection', False, str(e))
            logger.warning(f"API连接检查失败: {e}")
            return False
    
    def _check_agents_health(self):
        """检查代理健康状态"""
        try:
            active_agents = [a for a in self.agents if a.is_alive]
            
            # 检查代理是否有异常
            for agent in active_agents:
                if hasattr(agent, 'last_update_time') and agent.last_update_time:
                    # 检查是否长时间未更新
                    time_since_update = (datetime.now() - agent.last_update_time).total_seconds()
                    if time_since_update > 300:  # 5分钟
                        logger.warning(f"代理 {agent.agent_id} 长时间未更新: {time_since_update:.0f}秒")
            
            # 如果活跃代理数量少于最小阈值，认为不健康
            min_active_agents = max(1, self.config['initial_agents'] // 2)
            healthy = len(active_agents) >= min_active_agents
            self.health_monitor.update_health_status('agents', healthy)
            return healthy
        except Exception as e:
            self.health_monitor.update_health_status('agents', False, str(e))
            logger.error(f"代理健康检查失败: {e}")
            return False
    
    def _check_risk_manager(self):
        """检查风控管理器状态"""
        try:
            # 尝试获取风控指标，验证风控管理器是否正常工作
            metrics = self.adapter.risk_manager.get_risk_metrics()
            healthy = True
            self.health_monitor.update_health_status('risk_manager', healthy)
            return healthy
        except Exception as e:
            self.health_monitor.update_health_status('risk_manager', False, str(e))
            logger.error(f"风控管理器检查失败: {e}")
            return False
    
    def _cleanup_resources(self):
        """清理系统资源"""
        logger.info("执行资源清理...")
        
        # 清理内存中不再需要的数据
        if hasattr(self, '_historical_data') and len(self._historical_data) > 10000:
            self._historical_data = self._historical_data[-5000:]
            logger.info("清理历史数据")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        logger.info("触发垃圾回收")
    
    def _check_and_recover(self):
        """检查是否需要恢复并执行恢复操作"""
        with self.recovery_lock:
            # 检测异常模式
            abnormal_detected = self._detect_abnormal_patterns()
            
            if abnormal_detected and not self.safe_mode:
                self._enter_safe_mode()
            
            # 检查各个组件是否需要恢复
            for component in ['api_connection', 'market_data', 'agents', 'risk_manager']:
                if hasattr(self.health_monitor, 'should_recover') and self.health_monitor.should_recover(component):
                    # 获取失败次数
                    failure_count = 0
                    if hasattr(self.health_monitor, 'health_status') and 'consecutive_failures' in self.health_monitor.health_status:
                        failure_count = self.health_monitor.health_status['consecutive_failures'].get(component, 0)
                    
                    # 使用自适应恢复策略
                    action = self._adaptive_recovery_strategy(component, failure_count)
                    logger.warning(f"组件 {component} 需要恢复，执行操作: {action} (失败次数: {failure_count})")
                    
                    self.system_stats['recovery_attempts'] += 1
                    self.system_stats['last_recovery_time'] = datetime.now()
                    
                    # 保存当前状态
                    self._save_state()
                    
                    # 执行恢复操作
                    if action == 'full_restart':
                        self._full_restart()
                    elif action == 'restart_adapter':
                        self._recover_adapter()
                    elif action == 'recreate_failed_agents':
                        self._recreate_failed_agents()
                    elif action == 'restart_risk_manager':
                        self._restart_risk_manager()
                    elif action == 'wait_retry':
                        logger.info("等待并重试...")
                        time.sleep(5)
            
            # 定期保存状态（每10分钟）
            if (datetime.now() - self.last_state_save_time).total_seconds() > 600:
                self._save_state()
            
            # 检查是否需要从安全模式退出
            if self.safe_mode:
                safe_mode_duration = (datetime.now() - self.safe_mode_entry_time).total_seconds()
                if safe_mode_duration > 1800:  # 30分钟
                    # 检查系统是否恢复正常
                    all_healthy = True
                    for component in ['api_connection', 'market_data']:
                        if hasattr(self.health_monitor, 'is_healthy') and not self.health_monitor.is_healthy(component):
                            all_healthy = False
                            break
                    
                    if all_healthy:
                        logger.info("系统已恢复正常，退出安全模式")
                        self._exit_safe_mode()
    
    def _recover_adapter(self):
        """恢复OKX适配器连接"""
        logger.info("尝试恢复适配器连接...")
        
        try:
            # 关闭旧连接
            if hasattr(self.adapter, 'close'):
                self.adapter.close()
            
            # 创建新的适配器实例
            self.adapter = OKXTradingAdapter(self.okx_config)
            
            # 验证连接
            test_price = self.adapter.get_price(self.config['markets']['spot']['symbol'])
            logger.info(f"适配器连接恢复成功，测试价格: {test_price}")
            
            # 更新统计
            self.system_stats['component_restarts']['adapter'] += 1
            
            # 重置健康状态
            self.health_monitor.update_health_status('api_connection', True)
            self.error_counters['market_data'] = 0
            
            return True
        except Exception as e:
            logger.error(f"适配器恢复失败: {e}")
            self.health_monitor.update_health_status('api_connection', False, str(e))
            return False
    
    def _recreate_failed_agents(self):
        """重新创建失败的代理"""
        logger.info("尝试重新创建失败的代理...")
        
        try:
            active_agents = [a for a in self.agents if a.is_alive]
            min_active_agents = max(1, self.config['initial_agents'] // 2)
            
            # 如果活跃代理数量不足，创建新代理
            agents_to_create = min_active_agents - len(active_agents)
            if agents_to_create > 0:
                logger.info(f"需要创建 {agents_to_create} 个新代理")
                
                for i in range(agents_to_create):
                    # 从资金池分配资金
                    capital = self.capital_manager.allocate_capital(
                        self.config['capital_manager']['min_agent_capital']
                    )
                    
                    if capital > 0:
                        agent = LiveAgent(
                            agent_id=f"recovered_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                            initial_capital=capital,
                            config=self.config
                        )
                        self.agents.append(agent)
                        logger.info(f"创建恢复代理 {agent.agent_id}，分配资金 ${capital:.2f}")
            
            # 更新统计
            self.system_stats['component_restarts']['agents'] += 1
            
            # 重置健康状态
            self.health_monitor.update_health_status('agents', True)
            
            return True
        except Exception as e:
            logger.error(f"代理恢复失败: {e}")
            self.health_monitor.update_health_status('agents', False, str(e))
            return False
    
    def _restart_risk_manager(self):
        """重启风控管理器"""
        logger.info("尝试重启风控管理器...")
        
        try:
            # 重新初始化风控管理器
            if hasattr(self.adapter, 'restart_risk_manager'):
                self.adapter.restart_risk_manager()
                logger.info("风控管理器重启成功")
                
                # 更新统计
                self.system_stats['component_restarts']['risk_manager'] += 1
                
                # 重置健康状态
                self.health_monitor.update_health_status('risk_manager', True)
                
                return True
            else:
                logger.warning("适配器不支持风控管理器重启")
                return False
        except Exception as e:
            logger.error(f"风控管理器重启失败: {e}")
            self.health_monitor.update_health_status('risk_manager', False, str(e))
            return False
    
    def _handle_critical_error(self, error):
        """处理关键错误，增强版：优化SSL握手超时检测和恢复机制"""
        logger.info("处理关键错误...")
        
        # 记录错误信息
        error_type = type(error).__name__
        error_str = str(error)
        
        # 检查是否是SSL握手超时错误
        is_ssl_handshake_timeout = 'ssl' in error_type.lower() and ('handshake' in error_str.lower() and 'timeout' in error_str.lower())
        
        # 记录SSL错误的详细诊断信息
        if 'ssl' in error_type.lower():
            self._log_ssl_diagnostic_info(error, "critical_error_handling")
        
        # 更新错误计数器
        self._update_error_counters(error_type, error_str)
        
        # 根据错误类型执行不同的恢复操作
        if is_ssl_handshake_timeout:
            # 专门处理SSL握手超时错误，优先级最高
            logger.info("检测到SSL握手超时错误，启动专门的恢复流程")
            # 1. 立即检查并恢复市场数据适配器
            recovery_success = self._check_and_recover('market_data', error)
            
            if not recovery_success:
                logger.warning("市场数据适配器恢复失败，尝试深度恢复...")
                # 2. 尝试全面清理连接
                self._cleanup_connections()
                # 3. 执行更彻底的适配器恢复
                self._recover_adapter('market_data')
                
        elif error_type in ['NetworkError', 'TimeoutError', 'ConnectionError']:
            # 网络错误，尝试恢复适配器
            logger.info("检测到网络错误，尝试恢复适配器")
            recovery_success = self._check_and_recover('market_data', error)
            if not recovery_success:
                self._recover_adapter()
                
        elif 'API' in error_type:
            # API错误，检查是否需要重启适配器
            if self.health_monitor.should_recover('api_connection'):
                logger.info("API错误累积过多，尝试恢复适配器")
                self._check_and_recover('market_data', error)
                self._recover_adapter()
                
        elif 'Agent' in error_type or 'LiveAgent' in str(error):
            # 代理相关错误
            self._recreate_failed_agents()
        
        # 检查系统是否需要进入安全模式
        if self.error_counters['market_data'] >= 10 or \
           self.error_counters['order_execution'] >= 10:
            logger.warning("错误过多，考虑进入安全模式")
            # 安全模式：关闭所有持仓并暂停交易
            if hasattr(self, '_enter_safe_mode'):
                self._enter_safe_mode()
            
        # 记录错误恢复操作完成
        logger.info("关键错误恢复操作完成")
        
    def _log_ssl_diagnostic_info(self, error, context="unknown"):
        """
        记录详细的SSL错误诊断信息，便于问题排查
        
        Args:
            error: SSL错误对象
            context: 错误发生的上下文信息
        """
        try:
            # 收集基本错误信息
            error_type = type(error).__name__
            error_str = str(error)
            
            # 诊断信息字典
            diagnostic = {
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "error_type": error_type,
                "error_message": error_str,
                "system_info": {
                    "python_version": platform.python_version(),
                    "system": platform.system(),
                    "release": platform.release(),
                    "machine": platform.machine()
                }
            }
            
            # 收集更多SSL错误相关信息
            if hasattr(error, 'errno'):
                diagnostic["errno"] = error.errno
            if hasattr(error, 'ssl_reason'):
                diagnostic["ssl_reason"] = error.ssl_reason
            if hasattr(error, 'reason'):
                diagnostic["reason"] = error.reason
            
            # 记录详细的诊断日志
            logger.info(f"SSL错误诊断信息: {json.dumps(diagnostic, ensure_ascii=False, indent=2)}")
            
            # 记录摘要信息便于快速查看
            logger.error(
                f"SSL错误摘要 | "
                f"上下文: {context} | "
                f"类型: {error_type} | "
                f"消息: {error_str[:100]}..."
            )
            
        except Exception as log_error:
            logger.error(f"记录SSL诊断信息时发生错误: {log_error}")
            
    def _update_error_counters(self, error_type, error_str):
        """更新错误计数器，针对SSL错误进行特殊处理"""
        # 更新通用错误计数器
        if 'market_data' in self.error_counters:
            self.error_counters['market_data'] += 1
        
        # 针对SSL握手超时增加专门的计数器
        is_ssl_handshake_timeout = 'ssl' in error_type.lower() and ('handshake' in error_str.lower() and 'timeout' in error_str.lower())
        if is_ssl_handshake_timeout:
            # 初始化SSL错误计数器（如果不存在）
            if 'ssl_handshake_errors' not in self.error_counters:
                self.error_counters['ssl_handshake_errors'] = 0
            
            # 增加SSL握手错误计数
            self.error_counters['ssl_handshake_errors'] += 1
            logger.warning(f"SSL握手超时错误计数: {self.error_counters['ssl_handshake_errors']}")
            
            # 记录SSL握手超时的诊断信息
            logger.warning(f"SSL握手超时累积状态: 当前 {self.error_counters['ssl_handshake_errors']}次，" 
                          f"市场数据错误总计 {self.error_counters.get('market_data', 0)}次")
            
            # 如果SSL握手错误过多，可以考虑更激进的措施
            if self.error_counters['ssl_handshake_errors'] > 15:
                logger.error("SSL握手超时错误过多，重置SSL错误计数器")
                self.error_counters['ssl_handshake_errors'] = 0
    
    def _update_market_regime(self, market_data):
        """更新市场状态"""
        candles = market_data['candles']
        if len(candles) > 0:
            prices = [float(c[4]) for c in candles]  # 收盘价
            regime = self.market_detector.detect_regime(prices)
            return regime
        return 'sideways'
    
    def _update_agents(self, market_data, regime):
        """
        更新所有agents（通过桥接器）
        使用并发更新提升性能
        """
        update_start_time = time.time()
        
        # 安全检查
        if not hasattr(self, 'agents') or not self.agents:
            logger.warning("代理列表为空，跳过更新")
            return
        
        active_agents = [agent for agent in self.agents if hasattr(agent, 'is_alive') and agent.is_alive]
        
        # 数据准备阶段的异常处理
        try:
            # 使用桥接器格式化市场数据（只需一次）
            formatted_market_data = self.bridge.format_market_data(market_data)
            
            # 获取价格历史（只需一次）
            symbol = self.config.get('markets', {}).get('spot', {}).get('symbol', '')
            if not symbol:
                logger.error("无法获取交易对信息，使用串行更新模式")
                raise ValueError("交易对信息缺失")
            
            price_history = self._get_price_history(symbol, 100)
            
            # 使用桥接器构建标准化的市场特征（只需一次）
            market_features = self.bridge.build_market_features(
                price_history, 
                -1  # 使用最新数据点
            )
            
        except Exception as e:
            logger.error(f"准备代理更新数据失败: {e}")
            # 数据准备失败时，降级到基本串行更新模式
            for agent in active_agents:
                try:
                    # 使用有限的市场数据进行更新，保持正确的参数顺序
                    basic_price = market_data.get('spot', {}).get('price', 0)
                    if basic_price > 0:
                        basic_market_data = {'spot': {'price': basic_price}, 'futures': {'price': basic_price}}
                        agent.update(basic_market_data, regime)
                        agent.last_update_time = datetime.now()
                except Exception as inner_e:
                    logger.error(f"基本更新代理 {getattr(agent, 'agent_id', 'unknown')} 失败: {inner_e}")
            return
        
        # 检查是否启用并发
        enable_concurrency = self.performance.get('enable_concurrency', True)
        max_concurrent_agents = self.performance.get('max_concurrent_agents', 10)
        
        if enable_concurrency and len(active_agents) > 3:
            # 使用线程池进行并发更新
            try:
                from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
                
                # 计算批处理大小，增加安全限制
                batch_size = min(max(1, max_concurrent_agents), len(active_agents), 20)  # 最多20个并发
                
                logger.debug(f"使用并发更新代理，批量大小: {batch_size}")
                
                def update_agent_wrapper(agent):
                    try:
                        # 超时控制
                        update_timeout = self.performance.get('agent_update_timeout', 3)
                        import threading
                        
                        # 使用共享变量来获取线程执行结果
                        result_data = {'success': False, 'execution_time': None, 'error': None}
                        
                        def update_with_timeout():
                            try:
                                start_time = time.time()
                                # 整合市场数据为一个字典，符合LiveAgent.update()方法的参数要求
                                # 添加candles数据，确保LiveAgent能够计算技术指标和信号强度
                                candles = []
                                try:
                                    # 尝试从适配器获取K线数据
                                    if hasattr(self.adapter, 'market_data') and hasattr(self.adapter.market_data, 'get_candles'):
                                        symbol = self.config['markets']['spot']['symbol']
                                        candles = self.adapter.market_data.get_candles(symbol, '1m', 100)
                                        logger.debug(f"获取到 {len(candles)} 条K线数据用于代理更新")
                                    else:
                                        logger.warning("无法获取K线数据，使用空列表")
                                except Exception as e:
                                    logger.error(f"获取K线数据失败: {e}")
                                     
                                market_data = {
                                    'spot': {'price': formatted_market_data['price']},
                                    'futures': {'price': formatted_market_data['price']},
                                    'features': market_features,
                                    'candles': candles  # 添加candles键，确保信号计算
                                }
                                
                                # 添加Agent更新日志
                                logger.info(f">>> 更新 {agent.agent_id}")
                                logger.info(f"    资金: ${agent.capital:.2f}")
                                logger.info(f"    持仓: {len(agent.positions)}个")
                                
                                agent.update(market_data, regime)
                                
                                logger.info(f"    信号数: {len(agent.pending_signals)}")
                                if agent.pending_signals:
                                    for sig in agent.pending_signals:
                                        logger.info(f"    信号: {sig}")
                                        
                                agent.last_update_time = datetime.now()
                                result_data['execution_time'] = time.time() - start_time
                                result_data['success'] = True
                            except Exception as e:
                                result_data['error'] = str(e)
                                result_data['success'] = False
                        
                        # 使用线程执行带超时的更新
                        update_thread = threading.Thread(target=update_with_timeout)
                        update_thread.daemon = True
                        update_thread.start()
                        update_thread.join(update_timeout)
                        
                        if update_thread.is_alive():
                            raise TimeoutError(f"代理更新超时 (> {update_timeout}秒)")
                            
                        if result_data['success']:
                            return (getattr(agent, 'agent_id', 'unknown'), True, result_data['execution_time'])
                        else:
                            raise Exception(result_data['error'] if result_data['error'] else "代理更新失败")
                    except Exception as e:
                        return (getattr(agent, 'agent_id', 'unknown'), False, str(e))
                
                # 添加更新前的日志
                logger.info(f"=" * 80)
                logger.info(f"开始更新 {len(active_agents)} 个Agent")
                logger.info(f"市场数据: candles={len(formatted_market_data.get('candles', []))}根")
                logger.info(f"=" * 80)
                
                # 执行并发更新
                update_failures = 0
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = {executor.submit(update_agent_wrapper, agent): agent for agent in active_agents}
                    
                    # 总体超时控制
                    total_timeout = min(len(active_agents) * 2, 60)  # 最多等待60秒
                    
                    for future in as_completed(futures, timeout=total_timeout):
                        try:
                            agent_id, success, result = future.result(timeout=5)  # 单个future结果也设置超时
                            
                            if success:
                                # 记录更新时间
                                if hasattr(self, 'performance_stats') and hasattr(self.performance_stats, 'agent_update_times'):
                                    self.performance_stats['agent_update_times'].append(result)
                            else:
                                # 处理更新失败
                                update_failures += 1
                                logger.error(f"并发更新代理 {agent_id} 失败: {result}")
                                
                                agent = futures.get(future)
                                if agent:
                                    if hasattr(agent, 'update_failures'):
                                        agent.update_failures += 1
                                    else:
                                        agent.update_failures = 1
                                    
                                    if agent.update_failures >= 5:
                                        logger.warning(f"代理 {agent_id} 多次更新失败，标记为不活跃")
                                        agent.is_alive = False
                        except TimeoutError:
                            logger.warning(f"获取代理更新结果超时")
                            update_failures += 1
                
                # 更新错误计数，确保属性存在
                if not hasattr(self, 'error_counters'):
                    self.error_counters = {'agent_update': 0}
                
                if update_failures > 0:
                    self.error_counters['agent_update'] = update_failures
                else:
                    self.error_counters['agent_update'] = 0
                    if hasattr(self, 'last_successful_operation'):
                        self.last_successful_operation['agent_update'] = datetime.now()
            except Exception as e:
                logger.error(f"并发更新代理异常: {e}")
                # 并发失败时降级到串行模式
                enable_concurrency = False
        
        if not enable_concurrency:
            # 添加更新前的日志
            logger.info(f"=" * 80)
            logger.info(f"开始更新 {len(active_agents)} 个Agent")
            logger.info(f"市场数据: candles={len(formatted_market_data.get('candles', []))}根")
            logger.info(f"=" * 80)
            
            # 串行更新（适用于少量代理或并发失败时）
            for agent in active_agents:
                try:
                    start_time = time.time()
                    # 串行更新也添加超时保护
                    update_timeout = self.performance.get('agent_update_timeout', 3)
                    import signal
                    
                    def update_with_timeout_serial():
                        # 使用与并发模式相同的市场数据格式，包含完整的K线数据
                        market_data = {
                            'spot': {'price': formatted_market_data['price']},
                            'futures': {'price': formatted_market_data['price']},
                            'features': market_features,
                            'candles': formatted_market_data.get('candles', [])  # 确保包含K线数据
                        }
                        # 添加详细日志记录market_data内容
                        logger.debug(f"串行模式 - 准备更新代理 {getattr(agent, 'agent_id', 'unknown')} 的市场数据: ")
                        logger.debug(f"  - 蜡烛图数据数量: {len(market_data.get('candles', []))}")
                        logger.debug(f"  - 价格: {market_data.get('spot', {}).get('price')}")
                        
                        # 添加Agent更新日志
                        logger.info(f">>> 更新 {agent.agent_id}")
                        logger.info(f"    资金: ${agent.capital:.2f}")
                        logger.info(f"    持仓: {len(agent.positions)}个")
                        
                        agent.update(market_data, regime)
                        
                        logger.info(f"    信号数: {len(agent.pending_signals)}")
                        if agent.pending_signals:
                            for sig in agent.pending_signals:
                                logger.info(f"    信号: {sig}")
                                
                        agent.last_update_time = datetime.now()
                    
                    # 简单的超时控制（不使用signal，以兼容Windows）
                    import threading
                    update_thread = threading.Thread(target=update_with_timeout_serial)
                    update_thread.daemon = True
                    update_thread.start()
                    update_thread.join(update_timeout)
                    
                    if update_thread.is_alive():
                        raise TimeoutError(f"代理更新超时 (> {update_timeout}秒)")
                        
                    # 记录性能指标
                    update_time = time.time() - start_time
                    if hasattr(self, 'performance_stats') and hasattr(self.performance_stats, 'agent_update_times'):
                        self.performance_stats['agent_update_times'].append(update_time)
                    
                except Exception as e:
                    if not hasattr(self, 'error_counters'):
                        self.error_counters = {'agent_update': 0}
                    self.error_counters['agent_update'] += 1
                    agent_id = getattr(agent, 'agent_id', 'unknown')
                    logger.error(f"更新代理 {agent_id} 失败: {e}")
                    
                    # 对多次失败的代理标记为不活跃
                    if hasattr(agent, 'update_failures'):
                        agent.update_failures += 1
                    else:
                        agent.update_failures = 1
                    
                    if agent.update_failures >= 5:
                        logger.warning(f"代理 {agent_id} 多次更新失败，标记为不活跃")
                        agent.is_alive = False
            
            # 所有代理更新成功
            if hasattr(self, 'error_counters') and hasattr(self, 'last_successful_operation'):
                if not self.error_counters.get('agent_update', 0):
                    self.last_successful_operation['agent_update'] = datetime.now()
        
        # 记录总体更新时间
        total_update_time = time.time() - update_start_time
        logger.debug(f"代理更新完成，耗时: {total_update_time:.2f}秒，活跃代理数: {len(active_agents)}")
                        
    def _get_price_history(self, symbol: str, window: int = 100) -> List[Dict]:
        """
        获取价格历史数据
        
        Args:
            symbol: 交易对
            window: 窗口大小
            
        Returns:
            价格历史列表
        """
        try:
            # 获取K线数据
            klines = self.adapter.get_candles(symbol, bar='1m', limit=window)
            
            # 转换为标准格式
            price_history = []
            for kline in klines:
                entry = self.bridge.format_market_data({
                    'timestamp': kline[0],  # 假设第一个字段是时间戳
                    'open': kline[1],      # 第二个字段是开盘价
                    'high': kline[2],      # 第三个字段是最高价
                    'low': kline[3],       # 第四个字段是最低价
                    'close': kline[4],     # 第五个字段是收盘价
                    'volume': kline[5]     # 第六个字段是成交量
                })
                price_history.append(entry)
            
            return price_history
        except Exception as e:
            logger.error(f"获取价格历史失败: {e}")
            return []
    
    def _execute_trades(self):
        """
        执行交易（通过桥接器）
        使用批量处理提升性能
        """
        execution_start_time = time.time()
        
        # 安全检查
        if not hasattr(self, 'agents') or not self.agents:
            logger.warning("代理列表为空，跳过交易执行")
            return
        
        # 确保必要属性存在
        if not hasattr(self, 'error_counters'):
            self.error_counters = {'order_execution': 0}
        if not hasattr(self, 'stats'):
            self.stats = {'total_trades': 0, 'successful_trades': 0, 'failed_trades': 0}
        if not hasattr(self, 'last_successful_operation'):
            self.last_successful_operation = {'order_execution': None}
        
        # 收集所有待执行的交易信号
        pending_trades = []
        for agent in self.agents:
            if not hasattr(agent, 'is_alive') or not agent.is_alive:
                continue
            
            if hasattr(agent, 'pause_trading') and agent.pause_trading:
                continue
            
            if not hasattr(agent, 'pending_signals') or not agent.pending_signals:
                continue
            
            # 收集该代理的所有信号，添加基本验证
            for signal in agent.pending_signals:
                if isinstance(signal, dict) and 'action' in signal and 'symbol' in signal:
                    pending_trades.append((agent, signal))
                else:
                    logger.warning(f"忽略无效信号: {signal}")
        
        logger.debug(f"准备执行 {len(pending_trades)} 笔交易")
        
        # 批量处理交易
        batch_size = self.performance.get('batch_trade_size', 5)
        batch_size = max(1, min(batch_size, 20))  # 限制批量大小范围
        
        # 按照交易对分组，减少重复的市场数据请求
        trades_by_symbol = {}
        for agent, signal in pending_trades:
            symbol = signal.get('symbol', 'unknown')
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = []
            trades_by_symbol[symbol].append((agent, signal))
        
        # 为每个交易对处理批量交易
        for symbol, symbol_trades in trades_by_symbol.items():
            # 尝试获取该交易对的市场数据（每个交易对只获取一次）
            symbol_market_data = None
            try:
                symbol_market_data = self._get_market_data_for_signal(symbol)
            except Exception as e:
                logger.error(f"获取交易对 {symbol} 的市场数据失败: {e}")
                continue  # 跳过该交易对的所有交易
            
            # 分批处理该交易对的交易
            for i in range(0, len(symbol_trades), batch_size):
                batch = symbol_trades[i:i+batch_size]
                
                # API调用节流控制
                try:
                    self._throttle_api_calls(required_calls=len(batch))
                except Exception as e:
                    logger.warning(f"API节流控制异常: {e}，继续执行")
                
                # 执行批量交易
                for agent, signal in batch:
                    try:
                        start_time = time.time()
                        
                        # 获取市场信息
                        market = signal.get('market', 'spot')
                        
                        # 使用已获取的市场数据（优化）
                        raw_market_data = symbol_market_data
                        
                        # 使用桥接器格式化市场数据
                        formatted_market_data = self.bridge.format_market_data(raw_market_data)
                        current_price = formatted_market_data.get('price', 0)
                        
                        if current_price <= 0:
                            logger.warning(f"无效价格数据: {current_price}，跳过交易")
                            continue
                        
                        # 转换信号为标准化交易指令
                        trade_instruction = self.bridge.convert_strategy_signal(
                            signal.get('strength', 0), 
                            signal.get('market_regime', 'sideways')
                        )
                        
                        # 只有非持有的信号才执行
                        if trade_instruction.get('side') == 'hold':
                            continue
                        
                        # 转换信号为订单请求
                        order_request = self._signal_to_order(signal, agent)
                        
                        if order_request is None:
                            continue
                        
                        # 添加置信度信息
                        order_request['confidence'] = trade_instruction.get('confidence', 0)
                        order_request['timestamp'] = trade_instruction.get('timestamp', int(time.time()))
                        
                        # 交易安全检查
                        if order_request.get('size', 0) <= 0:
                            logger.warning(f"无效订单大小: {order_request.get('size')}")
                            continue
                        
                        if order_request.get('price', 0) <= 0 and order_request.get('order_type') == 'limit':
                            logger.warning(f"无效限价: {order_request.get('price')}")
                            continue
                        
                        # 执行订单，添加超时控制
                        agent_id = getattr(agent, 'agent_id', 'unknown')
                        logger.info(f"{agent_id} 下单: {signal.get('action')} {signal.get('side', 'close')} {symbol} (置信度: {order_request['confidence']:.2f})")
                        
                        # 交易执行超时控制
                        import threading
                        execution_result = {'order': None, 'exception': None}
                        
                        def execute_order_thread():
                            try:
                                if hasattr(self.bridge, 'mode') and self.bridge.mode == 'live':
                                    execution_result['order'] = self.adapter.place_order(order_request)
                                else:
                                    # 回测模式下，通过桥接器模拟执行
                                    execution_result['order'] = self.bridge.execute_order(order_request, current_price)
                            except Exception as e:
                                execution_result['exception'] = e
                        
                        # 启动交易执行线程
                        execution_timeout = self.performance.get('trade_execution_timeout', 5)
                        exec_thread = threading.Thread(target=execute_order_thread)
                        exec_thread.daemon = True
                        exec_thread.start()
                        exec_thread.join(execution_timeout)
                        
                        # 检查执行结果和超时
                        if exec_thread.is_alive():
                            raise TimeoutError(f"订单执行超时 (> {execution_timeout}秒)")
                        
                        if execution_result['exception']:
                            raise execution_result['exception']
                        
                        order = execution_result['order']
                        
                        # 处理订单结果
                        if hasattr(self.bridge, 'mode') and self.bridge.mode == 'live':
                            # 检查order是对象还是字典，并相应地访问其属性
                            if isinstance(order, dict):
                                normalized_result = {
                                    'order_id': order.get('order_id', order.get('ordId', f"manual_{int(time.time())}")),
                                    'status': self._map_order_status(order.get('state', order.get('status', 'filled'))),
                                    'side': order_request.get('side'),
                                    'price': order.get('price_avg', order.get('avgPx', current_price)),
                                    'quantity': order.get('size', order_request.get('size', 0)),
                                    'timestamp': int(time.time()),
                                    'type': order_request.get('order_type', 'market'),
                                    'filled_amount': order.get('filled_size', order.get('accFillSz', order_request.get('size', 0))),
                                    'fee': order.get('fee', 0)
                                }
                            else:
                                # 处理Order对象
                                normalized_result = {
                                    'order_id': getattr(order, 'order_id', getattr(order, 'ordId', f"manual_{int(time.time())}")),
                                    'status': self._map_order_status(getattr(order, 'state', getattr(order, 'status', 'filled'))),
                                    'side': order_request.get('side'),
                                    'price': getattr(order, 'price_avg', getattr(order, 'avgPx', current_price)),
                                    'quantity': getattr(order, 'size', order_request.get('size', 0)),
                                    'timestamp': int(time.time()),
                                    'type': order_request.get('order_type', 'market'),
                                    'filled_amount': getattr(order, 'filled_size', getattr(order, 'accFillSz', order_request.get('size', 0))),
                                    'fee': getattr(order, 'fee', 0)
                                }
                        else:
                            # 回测模式下，直接使用桥接器结果
                            normalized_result = order
                        
                        # 更新统计
                        self.stats['total_trades'] = self.stats.get('total_trades', 0) + 1
                        if normalized_result.get('status') in ['filled', 'partially_filled']:
                            self.stats['successful_trades'] = self.stats.get('successful_trades', 0) + 1
                        else:
                            self.stats['failed_trades'] = self.stats.get('failed_trades', 0) + 1
                        
                        # 记录交易到报告系统（添加异常处理）
                        try:
                            trade_record = {
                                'trade_id': normalized_result.get('order_id', 'unknown'),
                                'agent_id': agent_id,
                                'symbol': order_request.get('symbol', symbol),
                                'market': order_request.get('market', market),
                                'side': order_request.get('side'),
                                'action': signal.get('action'),
                                'price': normalized_result.get('price', 0),
                                'quantity': normalized_result.get('quantity', 0),
                                'filled_amount': normalized_result.get('filled_amount', 0),
                                'fee': normalized_result.get('fee', 0),
                                'status': normalized_result.get('status'),
                                'timestamp': datetime.now(),
                                'confidence': order_request.get('confidence', 0),
                                'signal_strength': signal.get('strength', 0),
                                'market_regime': signal.get('market_regime', 'sideways')
                            }
                            if hasattr(self, 'trade_reporter'):
                                self.trade_reporter.record_trade(trade_record)
                        except Exception as report_e:
                            logger.error(f"记录交易报告失败: {report_e}")
                        
                        # 更新交易代理状态
                        agent.last_trade_time = time.time()
                        agent.trade_count = getattr(agent, 'trade_count', 0) + 1
                        
                        # 更新性能统计
                        execution_time = time.time() - start_time
                        if hasattr(self, 'performance_stats') and hasattr(self.performance_stats, 'trade_execution_times'):
                            self.performance_stats['trade_execution_times'].append(execution_time)
                        
                        logger.info(f"{agent_id} 订单执行成功: {normalized_result.get('order_id')} (耗时: {execution_time:.2f}秒)")
                        
                    except Exception as e:
                        self.error_counters['order_execution'] = self.error_counters.get('order_execution', 0) + 1
                        agent_id = getattr(agent, 'agent_id', 'unknown')
                        logger.error(f"代理 {agent_id} 交易执行失败: {e}")
                        self.stats['failed_trades'] = self.stats.get('failed_trades', 0) + 1
                        
                        # 连续失败多次，考虑暂停该代理交易
                        if hasattr(agent, 'trade_failures'):
                            agent.trade_failures += 1
                        else:
                            agent.trade_failures = 1
                        
                        if agent.trade_failures >= 3:
                            logger.warning(f"代理 {agent_id} 交易连续失败，暂停交易5次迭代")
                            agent.pause_trading = True
                            agent.pause_until_iteration = hasattr(self, '_current_iteration') and self._current_iteration + 5 or 5
        
        # 处理暂停交易的代理
        for agent in self.agents:
            if hasattr(agent, 'pause_trading') and agent.pause_trading:
                if hasattr(agent, 'pause_until_iteration') and hasattr(self, '_current_iteration'):
                    if self._current_iteration >= agent.pause_until_iteration:
                        agent.pause_trading = False
                        agent.trade_failures = 0
                        agent_id = getattr(agent, 'agent_id', 'unknown')
                        logger.info(f"代理 {agent_id} 恢复交易")
                    else:
                        agent_id = getattr(agent, 'agent_id', 'unknown')
                        logger.debug(f"代理 {agent_id} 仍在交易暂停期内")
            
            # 安全地清空已处理的信号
            if hasattr(agent, 'pending_signals'):
                try:
                    agent.pending_signals = []
                except Exception as e:
                    logger.warning(f"清空代理信号失败: {e}")
        
        # 重置错误计数（如果有成功交易）
        if self.stats.get('successful_trades', 0) > 0:
            self.last_successful_operation['order_execution'] = datetime.now()
            self.error_counters['order_execution'] = 0
            
        # 记录总体执行时间
        total_execution_time = time.time() - execution_start_time
        logger.debug(f"交易执行完成，耗时: {total_execution_time:.2f}秒，处理交易: {len(pending_trades)}笔")
            
    def _get_market_data_for_signal(self, symbol):
        """
        获取用于信号处理的市场数据
        增强版：添加缓存、重试机制和错误处理
        
        Args:
            symbol: 交易对
            
        Returns:
            市场数据字典
        """
        try:
            # 参数验证
            if not symbol or not isinstance(symbol, str):
                logger.warning(f"无效的交易对: {symbol}")
                return {'price': 0, 'candles': [], 'timestamp': time.time(), 'error': 'invalid_symbol'}
            
            # 初始化缓存（如果不存在）
            if not hasattr(self, '_market_data_cache'):
                self._market_data_cache = {}
                self._market_data_cache_times = {}
            
            # 缓存设置
            cache_ttl = 1.0  # 缓存1秒
            current_time = time.time()
            
            # 检查缓存是否有效
            if symbol in self._market_data_cache and \
               symbol in self._market_data_cache_times and \
               current_time - self._market_data_cache_times[symbol] < cache_ttl:
                # 缓存命中，更新统计
                if hasattr(self, 'performance_stats'):
                    self.performance_stats['cache_hits'] = self.performance_stats.get('cache_hits', 0) + 1
                return self._market_data_cache[symbol]
            
            # 缓存未命中，更新统计
            if hasattr(self, 'performance_stats'):
                self.performance_stats['cache_misses'] = self.performance_stats.get('cache_misses', 0) + 1
            
            # 结果初始化为默认值
            result = {
                'price': 0,
                'candles': [],
                'timestamp': current_time,
                'success': False
            }
            
            # 获取价格数据（添加重试机制）
            max_retries = 2
            price_success = False
            
            for attempt in range(max_retries + 1):
                try:
                    # API调用节流控制
                    if hasattr(self, '_throttle_api_calls'):
                        try:
                            self._throttle_api_calls(required_calls=1)
                        except Exception as e:
                            logger.warning(f"API节流控制异常: {e}")
                    
                    # 获取价格
                    price = self.adapter.get_price(symbol)
                    
                    # 验证价格有效性
                    try:
                        price_value = float(price)
                        if price_value > 0:
                            result['price'] = price_value
                            price_success = True
                            break
                        else:
                            logger.warning(f"获取到无效价格: {price}")
                    except (ValueError, TypeError):
                        logger.warning(f"价格数据类型错误: {price}")
                        
                except Exception as e:
                    logger.warning(f"获取价格失败 (尝试 {attempt+1}/{max_retries+1}): {e}")
                    
                # 退避重试
                if attempt < max_retries:
                    backoff_time = 0.1 * (2 ** attempt)
                    time.sleep(backoff_time)
            
            # 获取K线数据（添加重试机制）
            candles_success = False
            
            for attempt in range(max_retries + 1):
                try:
                    # API调用节流控制
                    if hasattr(self, '_throttle_api_calls'):
                        try:
                            self._throttle_api_calls(required_calls=1)
                        except Exception as e:
                            logger.warning(f"API节流控制异常: {e}")
                    
                    # 获取K线数据
                    candles = self.adapter.get_candles(symbol, bar='1m', limit=10)
                    
                    # 验证K线数据有效性
                    if isinstance(candles, list) and len(candles) > 0:
                        # 验证第一根K线的数据格式
                        first_candle = candles[0]
                        if isinstance(first_candle, (list, tuple)) and len(first_candle) >= 6:  # 至少需要包含基本OHLCV数据
                            result['candles'] = candles
                            candles_success = True
                            break
                        else:
                            logger.warning(f"K线数据格式错误: {first_candle}")
                    else:
                        logger.warning(f"获取到空的K线数据")
                        
                except Exception as e:
                    logger.warning(f"获取K线数据失败 (尝试 {attempt+1}/{max_retries+1}): {e}")
                    
                # 退避重试
                if attempt < max_retries:
                    backoff_time = 0.1 * (2 ** attempt)
                    time.sleep(backoff_time)
            
            # 判断是否成功获取任何数据
            result['success'] = price_success or candles_success
            
            # 更新结果时间戳
            result['timestamp'] = time.time()
            
            # 更新错误计数器
            if not result['success']:
                if hasattr(self, 'error_counters'):
                    self.error_counters['market_data'] = self.error_counters.get('market_data', 0) + 1
                result['error'] = 'data_retrieval_failed'
            else:
                # 清除错误计数器
                if hasattr(self, 'error_counters'):
                    self.error_counters['market_data'] = 0
                if hasattr(self, 'last_successful_operation'):
                    self.last_successful_operation['market_data'] = datetime.now()
            
            # 更新缓存（只缓存成功的数据）
            if result['success']:
                self._market_data_cache[symbol] = result.copy()
                self._market_data_cache_times[symbol] = time.time()
                
                # 清理过期缓存，避免内存泄漏
                self._clean_cache()
            
            return result
            
        except Exception as e:
            logger.error(f"获取信号市场数据异常: {e}")
            # 记录错误
            if hasattr(self, 'error_counters'):
                self.error_counters['market_data'] = self.error_counters.get('market_data', 0) + 1
            return {'price': 0, 'candles': [], 'timestamp': time.time(), 'error': str(e), 'success': False}
            
    def _clean_cache(self):
        """
        清理过期缓存，防止内存泄漏
        """
        try:
            # 缓存大小限制
            max_cache_size = 500
            if hasattr(self, '_market_data_cache') and len(self._market_data_cache) > max_cache_size:
                # 移除最旧的缓存项
                oldest_key = min(self._market_data_cache_times.items(), key=lambda x: x[1])[0]
                if oldest_key in self._market_data_cache:
                    del self._market_data_cache[oldest_key]
                if oldest_key in self._market_data_cache_times:
                    del self._market_data_cache_times[oldest_key]
                
                logger.debug(f"清理市场数据缓存，当前大小: {len(self._market_data_cache)}")
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
            # 静默处理缓存清理错误，不影响主流程
            
    def _map_order_status(self, status):
        """
        映射订单状态到标准状态
        
        Args:
            status: 原始订单状态
            
        Returns:
            标准订单状态
        """
        status_map = {
            'live': 'submitted',
            'partially_filled': 'partially_filled',
            'filled': 'filled',
            'cancelled': 'cancelled',
            'rejected': 'failed'
        }
        return status_map.get(status, 'unknown')
    
    def _enter_safe_mode(self):
        """进入安全模式：关闭所有持仓，暂停新开仓"""
        logger.warning("===== 进入安全模式 =====")
        
        # 关闭所有持仓
        self._close_all_positions()
        
        # 暂停所有代理交易
        for agent in self.agents:
            if agent.is_alive:
                agent.pause_trading = True
                logger.info(f"代理 {agent.agent_id} 已暂停交易")
        
        # 记录安全模式状态
        self.safe_mode = True
        self.safe_mode_entry_time = datetime.now()
        
        # 等待一段时间后自动退出安全模式
        # 注意：这会在主循环中检查，不会阻塞此处执行
    
    def _exit_safe_mode(self):
        """退出安全模式"""
        logger.warning("===== 退出安全模式 =====")
        
        # 恢复代理交易
        for agent in self.agents:
            if agent.is_alive:
                agent.pause_trading = False
                logger.info(f"代理 {agent.agent_id} 交易恢复")
        
        # 更新状态
        self.safe_mode = False
        self.safe_mode_exit_time = datetime.now()
    
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
            # 参数验证
            if not isinstance(signal, dict):
                logger.warning(f"无效的信号类型: {type(signal).__name__}")
                return None
            
            # 必需字段检查
            required_fields = ['symbol']
            for field in required_fields:
                if field not in signal:
                    logger.warning(f"信号缺少必需字段: {field}")
                    return None
            
            # action字段检查
            action = signal.get('action', '').lower()
            if action not in ['close', 'open']:
                logger.warning(f"无效的action类型: {action}")
                return None
            
            # 代理状态检查
            if not agent or not hasattr(agent, 'is_alive') or not agent.is_alive:
                logger.warning(f"尝试使用不活跃代理生成订单")
                return None
            
            # 安全检查：获取代理ID
            agent_id = getattr(agent, 'agent_id', 'unknown')
            
            # 平仓信号处理
            if action == 'close':
                try:
                    symbol = signal['symbol']
                    
                    # 检查持仓是否存在
                    if not hasattr(agent, 'positions') or not isinstance(agent.positions, dict):
                        logger.warning(f"代理没有有效的持仓信息")
                        return None
                    
                    if symbol not in agent.positions:
                        logger.warning(f"代理没有 {symbol} 的持仓")
                        return None
                    
                    pos = agent.positions[symbol]
                    
                    # 检查持仓数据完整性
                    if not isinstance(pos, dict) or 'side' not in pos or 'size' not in pos:
                        logger.warning(f"持仓数据不完整: {pos}")
                        return None
                    
                    # 确定平仓方向
                    if pos['side'] == 'long':
                        side = 'sell'
                        pos_side = 'long'
                    else:
                        side = 'buy'
                        pos_side = 'short'
                    
                    # 确定市场类型
                    market = 'futures' if 'SWAP' in symbol else 'spot'
                    
                    # 构建平仓订单
                    order_request = {
                        'market': market,
                        'symbol': symbol,
                        'side': side,
                        'order_type': 'market',
                        'size': abs(float(pos['size'])),  # 确保是浮点数
                        'reduce_only': True,
                        'agent_id': agent_id,
                        'timestamp': int(time.time())
                    }
                    
                    # 合约添加pos_side
                    if market == 'futures':
                        order_request['pos_side'] = pos_side
                    
                    logger.debug(f"生成平仓订单: {order_request}")
                    return order_request
                    
                except KeyError as e:
                    logger.error(f"平仓信号缺少关键字段: {e}")
                    return None
                except (ValueError, TypeError) as e:
                    logger.error(f"平仓数据类型错误: {e}")
                    return None
            
            # 开仓信号处理
            elif action == 'open':
                try:
                    # 验证必要字段
                    required_open_fields = ['market', 'symbol', 'side']
                    for field in required_open_fields:
                        if field not in signal:
                            logger.warning(f"开仓信号缺少必需字段: {field}")
                            return None
                    
                    market = signal['market']
                    symbol = signal['symbol']
                    side = signal['side']
                    strength = min(max(float(signal.get('strength', 0.5)), 0), 1)  # 归一化到0-1范围
                    
                    # 验证参数值
                    if market not in ['spot', 'futures', 'linear', 'inverse']:
                        logger.warning(f"无效的市场类型: {market}")
                        return None
                    
                    if side not in ['long', 'short', 'buy', 'sell']:
                        logger.warning(f"无效的交易方向: {side}")
                        return None
                    
                    # 确保代理有资金
                    if not hasattr(agent, 'capital') or float(agent.capital) <= 0:
                        logger.warning(f"代理资金不足: {getattr(agent, 'capital', '未知')}")
                        return None
                    
                    # 获取风险配置，提供合理默认值
                    max_order_value = self.config.get('risk', {}).get('max_order_value', 500)
                    position_percent = 0.3  # 默认使用30%资金
                    
                    # 计算订单价值
                    try:
                        value = float(agent.capital) * strength * position_percent
                        value = min(value, float(max_order_value))  # 限制最大订单价值
                        
                        # 确保价值有最小值，防止生成过小的订单
                        # 根据市场类型设置不同的最小订单价值
                        if market == 'contract':
                            min_value = 50.0  # 合约市场保留较高的最小价值
                        else:
                            min_value = 30.0  # 现货市场允许较小的订单价值
                        
                        # 只有当订单价值严格小于最小值时才返回警告
                        if value < min_value:
                            logger.warning(f"计算的订单价值过小: {value}，需要至少{min_value}")
                            return None
                    except (ValueError, TypeError) as e:
                        logger.error(f"计算订单价值失败: {e}")
                        return None
                    
                    # 现货市场处理
                    if market == 'spot':
                        try:
                            # 获取当前价格，添加错误处理和超时
                            current_price = None
                            for attempt in range(3):  # 最多尝试3次
                                try:
                                    current_price = self.adapter.get_price(symbol)
                                    if float(current_price) > 0:
                                        break
                                except Exception as e:
                                    logger.warning(f"获取价格失败 (尝试 {attempt+1}/3): {e}")
                                    time.sleep(0.1 * (attempt + 1))  # 指数退避
                            
                            if current_price is None or float(current_price) <= 0:
                                logger.error(f"无法获取有效价格: {current_price}")
                                return None
                            
                            # 计算数量
                            current_price = float(current_price)
                            size = value / current_price
                            
                            # 数量限制检查
                            min_size = 0.0001  # 现货最小0.0001
                            if size < min_size:
                                logger.warning(f"订单数量小于最小限制: {size} < {min_size}")
                                return None
                            
                            # 舍入到合理精度
                            size = round(size, 4)
                            
                            # 现货订单始终是买入
                            return {
                                'market': 'spot',
                                'symbol': symbol,
                                'side': 'buy',
                                'order_type': 'market',
                                'size': size,
                                'agent_id': agent_id,
                                'timestamp': int(time.time()),
                                'signal_strength': strength
                            }
                            
                        except Exception as e:
                            logger.error(f"现货订单生成失败: {e}")
                            return None
                    
                    # 合约市场处理
                    else:
                        try:
                            # 合约价值估算（每张合约约100 USDT）
                            contract_value = 100.0
                            
                            # 计算并确保至少有1张合约
                            size = max(1, int(value / contract_value))
                            
                            # 验证大小合理性
                            if size > 100:  # 防止异常大的订单
                                logger.warning(f"订单数量异常大: {size}")
                                size = 100
                            
                            logger.info(f"生成合约订单数量: {size} 张")
                            
                            # 确定订单方向
                            if side == 'long' or side == 'buy':
                                order_side = 'buy'
                                pos_side = 'long'
                            else:
                                order_side = 'sell'
                                pos_side = 'short'
                            
                            # 获取杠杆配置，限制在合理范围内
                            leverage = int(self.config.get('markets', {}).get('futures', {}).get('max_leverage', 2))
                            leverage = max(1, min(leverage, 100))  # 限制杠杆在1-100倍
                            
                            return {
                                'market': 'futures',
                                'symbol': symbol,
                                'side': order_side,
                                'pos_side': pos_side,
                                'order_type': 'market',
                                'size': size,
                                'leverage': leverage,
                                'agent_id': agent_id,
                                'timestamp': int(time.time()),
                                'signal_strength': strength
                            }
                            
                        except Exception as e:
                            logger.error(f"合约订单生成失败: {e}")
                            return None
                except Exception as e:
                    logger.error(f"开仓信号处理异常: {e}")
                    return None
        except Exception as e:
            logger.error(f"信号转换为订单失败: {e}")
            # 记录错误统计
            if hasattr(self, 'error_counters'):
                self.error_counters['signal_to_order'] = self.error_counters.get('signal_to_order', 0) + 1
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
        
        logger.info(f"活跃代理数量: {len(active_agents)}/{len(self.agents)}")
        logger.info(f"总权益: ${summary['total_equity']:.2f}")
        logger.info(f"未实现盈亏: ${summary['total_unrealized_pnl']:.2f}")
        logger.info(f"总交易次数: {self.stats['total_trades']}")
        logger.info(f"代理出生数: {self.stats['births']}, 代理死亡数: {self.stats['deaths']}")
    
    def _calculate_gene_distance(self, gene1, gene2):
        """
        计算两个基因之间的欧氏距离
        
        Args:
            gene1: 第一个基因字典
            gene2: 第二个基因字典
            
        Returns:
            float: 归一化的欧氏距离（0表示完全相同，1表示完全不同）
        """
        import numpy as np
        
        # 提取主要参数作为特征向量
        features1 = []
        features2 = []
        
        # 主要参数
        main_params = ['long_threshold', 'short_threshold', 'max_position', 
                       'stop_loss', 'take_profit', 'holding_period', 'risk_aversion',
                       'volatility_adjustment', 'market_state_sensitivity']
        
        for param in main_params:
            if param in gene1 and param in gene2:
                val1 = gene1[param]
                val2 = gene2[param]
                
                # 对于不同参数进行适当的归一化
                if param == 'holding_period':
                    # 对时间参数进行对数归一化
                    val1 = np.log(val1 + 1)
                    val2 = np.log(val2 + 1)
                elif param in ['long_threshold', 'short_threshold', 'stop_loss', 'take_profit']:
                    # 对阈值参数进行缩放
                    val1 *= 10
                    val2 *= 10
                
                features1.append(val1)
                features2.append(val2)
        
        # 处理指标权重
        if 'indicator_weights' in gene1 and 'indicator_weights' in gene2:
            weights1 = gene1['indicator_weights']
            weights2 = gene2['indicator_weights']
            
            # 确保使用相同的顺序
            weight_keys = sorted(set(weights1.keys()).intersection(weights2.keys()))
            for key in weight_keys:
                features1.append(weights1[key])
                features2.append(weights2[key])
        
        if not features1 or not features2:
            return 0.0  # 无法计算距离
        
        # 转换为numpy数组
        vec1 = np.array(features1)
        vec2 = np.array(features2)
        
        # 计算欧氏距离
        distance = np.linalg.norm(vec1 - vec2)
        
        # 归一化距离（考虑特征向量的最大可能距离）
        max_possible_distance = np.linalg.norm(np.ones_like(vec1) * 10)  # 估计的最大可能距离
        normalized_distance = min(1.0, distance / (max_possible_distance + 1e-10))
        
        return normalized_distance
    
    def _monitor_gene_diversity(self):
        """
        监测基因多样性，计算代理之间的相似度
        
        Returns:
            dict: 多样性统计信息
        """
        if len(self.agents) < 2:
            return {
                'average_distance': 1.0,
                'minimum_distance': 1.0,
                'max_similarity': 0.0,
                'message': '代理数量不足，无法计算多样性'
            }
        
        import numpy as np
        
        distances = []
        similarities = []
        
        # 计算所有代理对之间的距离
        for i in range(len(self.agents)):
            for j in range(i + 1, len(self.agents)):
                distance = self._calculate_gene_distance(
                    self.agents[i].gene, 
                    self.agents[j].gene
                )
                distances.append(distance)
                similarities.append(1.0 - distance)  # 相似度 = 1 - 距离
        
        # 计算统计信息
        avg_distance = np.mean(distances) if distances else 0.0
        min_distance = np.min(distances) if distances else 0.0
        max_similarity = np.max(similarities) if similarities else 0.0
        
        # 更新历史记录
        self.diversity_stats['average_distance'] = avg_distance
        self.diversity_stats['minimum_distance'] = min_distance
        self.diversity_stats['max_similarity'] = max_similarity
        self.diversity_stats['last_monitor_time'] = datetime.now()
        
        # 保存历史数据（限制长度）
        self.diversity_stats['diversity_history'].append({
            'timestamp': datetime.now(),
            'average_distance': avg_distance,
            'minimum_distance': min_distance,
            'max_similarity': max_similarity,
            'agent_count': len(self.agents)
        })
        
        # 保持历史记录不超过100条
        if len(self.diversity_stats['diversity_history']) > 100:
            self.diversity_stats['diversity_history'] = self.diversity_stats['diversity_history'][-100:]
        
        # 记录日志
        logger.info(f"基因多样性监测: 平均距离={avg_distance:.4f}, 最小距离={min_distance:.4f}, 最大相似度={max_similarity:.4f}")
        
        # 检查是否需要采取恢复措施
        if avg_distance < self.diversity_monitor_config['min_diversity_threshold'] or \
           max_similarity > self.diversity_monitor_config['max_similarity_threshold']:
            self._take_diversity_recovery_action()
        
        return {
            'average_distance': avg_distance,
            'minimum_distance': min_distance,
            'max_similarity': max_similarity
        }
    
    def _take_diversity_recovery_action(self):
        """
        当基因多样性不足时采取恢复措施
        """
        action = self.diversity_monitor_config['diversity_recovery_action']
        logger.warning(f"基因多样性不足，采取恢复措施: {action}")
        
        self.diversity_stats['recovery_actions_taken'] += 1
        
        if action == 'introduce_random':
            # 引入新的随机代理
            new_agent_count = max(2, len(self.agents) // 10)  # 引入代理总数的10%，最少2个
            logger.info(f"引入 {new_agent_count} 个新的随机代理以增加多样性")
            
            for i in range(new_agent_count):
                capital = self.capital_manager.allocate_capital(
                    self.config['capital_manager']['min_agent_capital']
                )
                
                if capital > 0:
                    # 创建新代理，不使用种子基因
                    agent = LiveAgent(
                        agent_id=f"diversity_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                        initial_capital=capital,
                        config=self.config,
                        gene=None  # 强制生成随机基因
                    )
                    self.agents.append(agent)
                    logger.info(f"创建多样性恢复代理 {agent.agent_id}，分配资金 ${capital:.2f}")
        
        elif action == 'cull_similar':
            # 淘汰最相似的代理
            if len(self.agents) > 3:  # 确保至少保留3个代理
                similar_pairs = []
                
                # 找出所有相似的代理对
                for i in range(len(self.agents)):
                    for j in range(i + 1, len(self.agents)):
                        similarity = 1.0 - self._calculate_gene_distance(
                            self.agents[i].gene,
                            self.agents[j].gene
                        )
                        similar_pairs.append((similarity, i, j))
                
                # 按相似度排序
                similar_pairs.sort(reverse=True)
                
                # 标记要淘汰的代理（保留表现较好的那个）
                to_remove = set()
                for similarity, i, j in similar_pairs:
                    if i not in to_remove and j not in to_remove and similarity > 0.8:
                        # 比较两个代理的表现，移除表现较差的
                        agent_i = self.agents[i]
                        agent_j = self.agents[j]
                        
                        # 简化的表现评估：比较ROI
                        if hasattr(agent_i, 'roi') and hasattr(agent_j, 'roi'):
                            if agent_i.roi < agent_j.roi:
                                to_remove.add(i)
                            else:
                                to_remove.add(j)
                
                # 移除标记的代理
                for idx in sorted(to_remove, reverse=True):
                    agent = self.agents[idx]
                    logger.info(f"移除相似代理 {agent.agent_id} 以增加多样性")
                    # 释放资金
                    self.capital_manager.release_capital(agent.capital)
                    del self.agents[idx]
        
        # 发送多样性警告
        self.alert_system.send_alert(
            level='WARNING',
            title='基因多样性警告',
            message=f"系统基因多样性低于阈值，已采取恢复措施: {action}",
            details={
                'average_distance': self.diversity_stats['average_distance'],
                'minimum_distance': self.diversity_stats['minimum_distance'],
                'max_similarity': self.diversity_stats['max_similarity'],
                'recovery_actions_taken': self.diversity_stats['recovery_actions_taken']
            }
        )
    
    def _monitoring_loop(self):
        """监控系统循环"""
        logger.info("监控循环已启动")
        monitoring_interval = self.config.get('monitoring', {}).get('interval', 60)  # 默认60秒
        # 初始化最后多样性监测时间
        self.diversity_stats['last_monitor_time'] = datetime.now()
        
        while self.running:
            try:
                # 收集系统指标
                system_metrics = {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('.').percent,
                    'network_io': psutil.net_io_counters(),
                    'process_count': len(psutil.pids())
                }
                
                # 更新系统监控器
                self.system_monitor.update_system_metrics(system_metrics)
                
                # 收集交易统计
                trade_statistics = {
                    'total_trades': self.stats['total_trades'],
                    'successful_trades': self.stats['successful_trades'],
                    'failed_trades': self.stats['failed_trades'],
                    'error_counters': self.error_counters.copy()
                }
                self.system_monitor.update_trade_statistics(trade_statistics)
                
                # 收集代理性能
                agent_performance = []
                for agent in self.agents:
                    if agent.is_alive:
                        agent_performance.append({
                            'agent_id': agent.agent_id,
                            'capital': agent.capital,
                            'roi': agent.roi,
                            'trade_count': agent.trade_count,
                            'last_trade_time': agent.last_trade_time
                        })
                self.system_monitor.update_agent_performance(agent_performance)
                
                # 检查健康状态
                health_status = self.system_monitor.get_latest_health_status()
                
                # 如果健康分数过低，发送警报
                if health_status.get('health_score', 100) < 60:
                    self.alert_system.send_alert(
                        'system_health',
                        f'系统健康分数过低: {health_status.get("health_score", 100)}/100',
                        health_status
                    )
                    
                # 检查错误率
                total_errors = sum(self.error_counters.values())
                if total_errors > 10:
                    self.alert_system.send_alert(
                        'error_rate',
                        f'系统错误数量过多: {total_errors}',
                        self.error_counters.copy()
                    )
                    
                # 检查API连接状态
                if not self.health_monitor.health_status['api_connection']:
                    self.alert_system.send_alert(
                        'api_connection',
                        'API连接异常',
                        self.health_monitor.get_health_status()
                    )
                
                # 检查基因多样性（根据配置的间隔）
                if self.diversity_stats['last_monitor_time'] and \
                   (datetime.now() - self.diversity_stats['last_monitor_time']).total_seconds() > \
                   self.diversity_monitor_config['monitor_interval']:
                    self._monitor_gene_diversity()
                    
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
            
            time.sleep(monitoring_interval)
    
    def _reporting_loop(self):
        """报告系统循环"""
        logger.info("报告循环已启动")
        daily_report_time = self.config.get('reporting', {}).get('daily_time', '23:59')  # 默认每日23:59生成报告
        
        while self.running:
            try:
                # 检查是否到达每日报告时间
                now = datetime.now()
                current_time = now.strftime('%H:%M')
                
                if current_time == daily_report_time:
                    # 生成每日报告
                    daily_report = self.trade_reporter.generate_daily_report()
                    if daily_report:
                        report_file = self.trade_reporter.save_report(daily_report, 'daily')
                        logger.info(f"每日报告已生成: {report_file}")
                        
                        # 发送报告摘要
                        self.alert_system.send_daily_summary(daily_report)
                    
                    # 等待1分钟，避免重复生成
                    time.sleep(60)
                
                # 每小时生成性能摘要
                elif now.minute == 0 and now.second < 10:  # 每小时整点，给10秒容错
                    # 获取系统性能摘要
                    performance_summary = self.system_monitor.get_performance_summary()
                    
                    # 生成文本报告并记录到日志
                    self.system_monitor._generate_text_report(performance_summary)
                    
                    # 等待10秒，避免重复生成
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"报告循环错误: {e}")
            
            time.sleep(10)  # 每10秒检查一次时间
    
    def _enter_safe_mode(self):
        """进入安全模式：关闭所有持仓，暂停新开仓"""
        logger.warning("===== 进入安全模式 =====")
        
        # 关闭所有持仓
        self._close_all_positions()
        
        # 暂停所有代理交易
        for agent in self.agents:
            if hasattr(agent, 'pause_trading'):
                agent.pause_trading = True
                logger.info(f"代理 {agent.agent_id} 已暂停交易")
        
        # 记录安全模式状态
        self.safe_mode = True
        self.safe_mode_entry_time = datetime.now()
        
        # 发送警报
        self.alert_system.send_alert(
            'safe_mode_activated',
            "系统已进入安全模式，所有持仓已关闭",
            severity='warning'
        )
    
    def _exit_safe_mode(self):
        """退出安全模式"""
        logger.warning("===== 退出安全模式 =====")
        
        # 恢复代理交易
        for agent in self.agents:
            if hasattr(agent, 'pause_trading'):
                agent.pause_trading = False
                logger.info(f"代理 {agent.agent_id} 交易恢复")
        
        # 更新状态
        self.safe_mode = False
        self.safe_mode_exit_time = datetime.now()
        
        # 发送警报
        self.alert_system.send_alert(
            'safe_mode_deactivated',
            "系统已退出安全模式，交易恢复",
            severity='info'
        )
    
    def _detect_abnormal_patterns(self):
        """检测异常交易模式"""
        # 快速价格变动检测
        current_time = datetime.now()
        
        # 记录并分析价格变动速率
        for symbol in self.config['markets']['futures'].get('symbols', []):
            try:
                price = self.adapter.get_price(symbol)
                self.abnormal_patterns['rapid_price_changes'].append((current_time, symbol, price))
                
                # 只保留最近的10个价格点
                if len(self.abnormal_patterns['rapid_price_changes']) > 10:
                    self.abnormal_patterns['rapid_price_changes'] = self.abnormal_patterns['rapid_price_changes'][-10:]
                
                # 检查是否有超过5%的急剧价格变动
                if len(self.abnormal_patterns['rapid_price_changes']) >= 5:
                    prices = [x[2] for x in self.abnormal_patterns['rapid_price_changes']]
                    if max(prices) / min(prices) > 1.05:
                        logger.warning(f"检测到快速价格波动: {symbol}")
                        self.alert_system.send_alert(
                            'abnormal_price_movement',
                            f"符号 {symbol} 在短时间内出现超过5%的价格波动",
                            severity='warning'
                        )
                        return True
            except Exception:
                pass
        
        # 检查失败订单序列
        if len(self.abnormal_patterns['failed_orders_sequence']) >= 5:
            # 最近5个订单都失败了
            logger.warning("检测到连续失败订单模式")
            self.alert_system.send_alert(
                'consecutive_failed_orders',
                "检测到连续5个订单失败，可能存在系统问题",
                severity='warning'
            )
            return True
        
        return False
    
    def _adaptive_recovery_strategy(self, component, failure_count):
        """根据失败次数和类型采用自适应恢复策略"""
        if failure_count >= 5:
            # 多次失败，采用更激进的恢复策略
            if component == 'api_connection':
                # 尝试更换API端点或代理
                if hasattr(self.adapter, 'switch_endpoint'):
                    self.adapter.switch_endpoint()
            return 'full_restart'  # 多次失败，建议完全重启
        elif failure_count >= 3:
            # 中度失败，进入安全模式并重启组件
            self._enter_safe_mode()
            return self.health_monitor.get_recovery_action(component)
        else:
            # 轻度失败，使用常规恢复策略
            return self.health_monitor.get_recovery_action(component)
    
    def _full_restart(self):
        """完全重启系统"""
        logger.warning("执行系统完全重启...")
        
        try:
            # 保存当前状态
            self._save_state()
            
            # 关闭所有持仓
            self._close_all_positions()
            
            # 重置所有组件
            if hasattr(self.adapter, 'close'):
                self.adapter.close()
            
            # 重新初始化适配器
            self.adapter = OKXTradingAdapter(self.okx_config)
            
            # 重置健康状态
            for component in ['api_connection', 'market_data', 'agents', 'risk_manager']:
                if hasattr(self.health_monitor, 'update_health_status'):
                    self.health_monitor.update_health_status(component, True)
            
            # 重置错误计数器
            self.error_counters = {
                'market_data': 0,
                'order_execution': 0,
                'agent_update': 0
            }
            
            logger.info("系统完全重启成功")
            
            # 通知警报系统
            self.alert_system.send_alert(
                'system_restart',
                "系统已完全重启并重置",
                severity='info'
            )
            
            return True
        except Exception as e:
            logger.error(f"系统完全重启失败: {e}")
            self.alert_system.send_alert(
                'system_error',
                f"系统重启失败: {str(e)}",
                severity='critical'
            )
            return False
    
    def stop(self):
        """停止交易系统"""
        if not self.running:
            return
        
        logger.info("Stopping live trading system...")
        self.running = False
        self.stats['end_time'] = datetime.now()
        
        # 关闭所有持仓
        self._close_all_positions()
        
        # 保存最终状态
        self._save_state()
        
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
        logger.info("生成交易报告...")
        
        # 获取最终账户状态
        try:
            final_summary = self.adapter.get_account_summary()
        except Exception as e:
            logger.error(f"获取最终账户状态失败: {e}")
            # 使用默认值
            final_summary = {'total_equity': self.config['initial_capital']}
        
        # 计算ROI
        initial_capital = self.config['initial_capital']
        final_capital = final_summary['total_equity']
        roi = (final_capital - initial_capital) / initial_capital * 100
        
        # 计算运行时长
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # 获取健康状态摘要
        health_summary = self.health_monitor.get_health_status()
        
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
            },
            'system_health': {
                'health_summary': health_summary,
                'recovery_attempts': self.system_stats['recovery_attempts'],
                'component_restarts': self.system_stats['component_restarts'],
                'last_recovery_time': self.system_stats['last_recovery_time'].isoformat() if self.system_stats['last_recovery_time'] else None,
                'error_counters': self.error_counters
            }
        }
        
        # 确保报告目录存在
        report_dir = os.path.join(os.getcwd(), 'trading_logs')
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        # 保存报告
        report_file = os.path.join(report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"报告已保存到 {report_file}")
            logger.info(f"最终ROI: {roi:.2f}%")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
        
        return report
