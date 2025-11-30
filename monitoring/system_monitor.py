"""
系统监控模块

负责收集和报告系统性能指标、交易统计和健康状态
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
import psutil

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    系统监控器 - 收集和报告系统性能指标
    """
    
    def __init__(self, config: Dict):
        """
        初始化监控器
        
        Args:
            config: 监控配置
                - report_interval: 报告间隔（秒）
                - alert_thresholds: 警报阈值配置
                - data_retention_hours: 数据保留时间（小时）
                - report_dir: 报告保存目录
        """
        self.config = config
        self.report_interval = config.get('report_interval', 3600)  # 默认1小时
        self.alert_thresholds = config.get('alert_thresholds', {})
        self.data_retention_hours = config.get('data_retention_hours', 24)  # 默认24小时
        self.report_dir = config.get('report_dir', 'reports')
        
        # 确保报告目录存在
        os.makedirs(self.report_dir, exist_ok=True)
        
        # 性能指标数据
        self.performance_metrics = []
        self.trade_statistics = []
        self.agent_metrics = []
        self.error_logs = []
        
        # 系统资源监控
        self.process = psutil.Process()
        
        # 最后一次报告时间
        self.last_report_time = time.time()
        
        # 启动监控线程
        self.running = False
        self.monitor_thread = None
        
        logger.info("系统监控器初始化完成")
    
    def start(self):
        """
        启动监控线程
        """
        if self.running:
            logger.warning("监控器已经在运行中")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"系统监控线程已启动，报告间隔: {self.report_interval}秒")
    
    def stop(self):
        """
        停止监控线程
        """
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("系统监控已停止")
    
    def _monitor_loop(self):
        """
        监控主循环
        """
        while self.running:
            try:
                # 收集系统资源指标
                self._collect_system_metrics()
                
                # 检查是否需要生成报告
                current_time = time.time()
                if current_time - self.last_report_time >= self.report_interval:
                    self.generate_report()
                    self.last_report_time = current_time
                    
                # 清理过期数据
                self._cleanup_old_data()
                
                # 休眠一段时间
                time.sleep(min(60, self.report_interval))  # 最小1分钟检查一次
                
            except Exception as e:
                logger.error(f"监控循环发生错误: {e}")
                time.sleep(60)  # 出错后休眠1分钟再继续
    
    def _collect_system_metrics(self):
        """
        收集系统资源使用指标
        """
        try:
            # 获取CPU使用率
            cpu_percent = self.process.cpu_percent(interval=0.1)
            
            # 获取内存使用情况
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 获取磁盘使用情况
            disk_usage = psutil.disk_usage('.')
            
            # 收集网络统计
            net_io = psutil.net_io_counters()
            
            # 构建指标数据
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_used_mb': memory_info.rss / (1024 * 1024),
                'memory_percent': memory_percent,
                'disk_used_percent': disk_usage.percent,
                'network_bytes_sent': net_io.bytes_sent,
                'network_bytes_recv': net_io.bytes_recv,
                'thread_count': len(self.process.threads()),
                'file_handles': len(self.process.open_files()),
            }
            
            self.performance_metrics.append(metrics)
            
            # 限制存储的数据量
            if len(self.performance_metrics) > 1000:
                self.performance_metrics = self.performance_metrics[-1000:]
                
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def record_trade_statistics(self, trade_stats: Dict):
        """
        记录交易统计数据
        
        Args:
            trade_stats: 交易统计信息
                - total_trades: 总交易次数
                - successful_trades: 成功交易次数
                - failed_trades: 失败交易次数
                - total_pnl: 总盈亏
                - avg_pnl_per_trade: 平均每笔盈亏
                - win_rate: 胜率
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            **trade_stats
        }
        self.trade_statistics.append(stats)
        
        # 限制存储的数据量
        if len(self.trade_statistics) > 500:
            self.trade_statistics = self.trade_statistics[-500:]
    
    def record_agent_metrics(self, agent_id: int, metrics: Dict):
        """
        记录代理性能指标
        
        Args:
            agent_id: 代理ID
            metrics: 代理指标
                - roi: 回报率
                - trade_count: 交易次数
                - win_rate: 胜率
                - max_drawdown: 最大回撤
                - is_alive: 是否存活
        """
        # 确保agent_id始终是可哈希的类型（避免列表作为字典键）
        if isinstance(agent_id, list):
            # 将列表转换为字符串，确保可哈希
            agent_id_str = str(agent_id)
            logger.warning(f"检测到列表类型的agent_id，已转换为字符串: {agent_id_str}")
            agent_id = agent_id_str
        
        agent_data = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            **metrics
        }
        self.agent_metrics.append(agent_data)
        
        # 限制存储的数据量
        if len(self.agent_metrics) > 10000:
            self.agent_metrics = self.agent_metrics[-10000:]
    
    def record_error(self, error_type: str, error_message: str, component: str):
        """
        记录错误日志
        
        Args:
            error_type: 错误类型
            error_message: 错误信息
            component: 出错组件
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': error_message,
            'component': component
        }
        self.error_logs.append(error_entry)
        
        # 检查是否需要触发警报
        self._check_alert_conditions(error_entry)
        
        # 限制存储的数据量
        if len(self.error_logs) > 1000:
            self.error_logs = self.error_logs[-1000:]
    
    def _check_alert_conditions(self, error_entry: Dict):
        """
        检查是否需要触发警报
        
        Args:
            error_entry: 错误条目
        """
        # 实现警报逻辑
        pass
    
    def generate_report(self):
        """
        生成系统报告
        """
        try:
            timestamp = datetime.now()
            report_filename = f"report_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join(self.report_dir, report_filename)
            
            # 准备报告数据
            report_data = {
                'report_time': timestamp.isoformat(),
                'system_metrics': self._aggregate_system_metrics(),
                'trade_statistics': self._aggregate_trade_statistics(),
                'agent_performance': self._aggregate_agent_performance(),
                'error_summary': self._aggregate_error_summary(),
                'health_status': self._calculate_health_status()
            }
            
            # 保存报告到文件
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"系统报告已生成: {report_path}")
            
            # 同时生成简短的文本报告用于日志
            self._generate_text_report(report_data)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
    
    def _aggregate_system_metrics(self) -> Dict:
        """
        聚合系统指标
        
        Returns:
            聚合后的系统指标
        """
        if not self.performance_metrics:
            return {}
        
        # 最近一小时的数据
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        recent_metrics = [m for m in self.performance_metrics if m['timestamp'] >= one_hour_ago]
        
        if not recent_metrics:
            return {}
        
        # 计算平均值
        avg_cpu = sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics)
        
        return {
            'average_cpu_percent': avg_cpu,
            'average_memory_percent': avg_memory,
            'peak_cpu_percent': max(m['cpu_percent'] for m in recent_metrics),
            'peak_memory_percent': max(m['memory_percent'] for m in recent_metrics),
            'disk_usage_percent': recent_metrics[-1]['disk_used_percent'],
            'thread_count': recent_metrics[-1]['thread_count'],
            'data_points': len(recent_metrics)
        }
    
    def _aggregate_trade_statistics(self) -> Dict:
        """
        聚合交易统计
        
        Returns:
            聚合后的交易统计
        """
        if not self.trade_statistics:
            return {}
        
        # 获取最新的统计数据
        latest_stats = self.trade_statistics[-1]
        
        # 计算今日统计
        today = datetime.now().strftime('%Y-%m-%d')
        today_stats = [m for m in self.trade_statistics if m['timestamp'].startswith(today)]
        
        today_trades = sum(s.get('total_trades', 0) for s in today_stats)
        today_successful = sum(s.get('successful_trades', 0) for s in today_stats)
        today_pnl = sum(s.get('total_pnl', 0) for s in today_stats)
        
        return {
            'total_trades': latest_stats.get('total_trades', 0),
            'successful_trades': latest_stats.get('successful_trades', 0),
            'failed_trades': latest_stats.get('failed_trades', 0),
            'total_pnl': latest_stats.get('total_pnl', 0),
            'win_rate': latest_stats.get('win_rate', 0),
            'today_trades': today_trades,
            'today_successful': today_successful,
            'today_pnl': today_pnl,
            'today_win_rate': today_successful / today_trades if today_trades > 0 else 0
        }
    
    def _aggregate_agent_performance(self) -> Dict:
        """
        聚合代理性能
        
        Returns:
            代理性能聚合数据
        """
        if not self.agent_metrics:
            return {}
        
        # 按代理分组
        agent_groups = {}
        for metric in self.agent_metrics:
            agent_id = metric['agent_id']
            # 确保agent_id是可哈希的类型
            if isinstance(agent_id, list):
                agent_id = str(agent_id)
                logger.warning(f"在聚合代理性能时检测到列表类型的agent_id，已转换为字符串")
            
            if agent_id not in agent_groups:
                agent_groups[agent_id] = []
            agent_groups[agent_id].append(metric)
        
        # 获取每个代理的最新状态
        agent_status = {}
        for agent_id, metrics in agent_groups.items():
            # 按时间排序，取最新的
            latest = sorted(metrics, key=lambda x: x['timestamp'])[-1]
            agent_status[agent_id] = {
                'roi': latest.get('roi', 0),
                'trade_count': latest.get('trade_count', 0),
                'win_rate': latest.get('win_rate', 0),
                'is_alive': latest.get('is_alive', False)
            }
        
        # 计算总体统计
        alive_agents = [a for a in agent_status.values() if a['is_alive']]
        dead_agents = [a for a in agent_status.values() if not a['is_alive']]
        
        avg_roi = sum(a['roi'] for a in agent_status.values()) / len(agent_status) if agent_status else 0
        
        return {
            'total_agents': len(agent_status),
            'alive_agents': len(alive_agents),
            'dead_agents': len(dead_agents),
            'average_roi': avg_roi,
            'top_performer': max(agent_status.items(), key=lambda x: x[1]['roi']) if agent_status else None
        }
    
    def _aggregate_error_summary(self) -> Dict:
        """
        聚合错误摘要
        
        Returns:
            错误统计摘要
        """
        if not self.error_logs:
            return {}
        
        # 今日错误
        today = datetime.now().strftime('%Y-%m-%d')
        today_errors = [e for e in self.error_logs if e['timestamp'].startswith(today)]
        
        # 按组件分组
        component_errors = {}
        for error in today_errors:
            component = error['component']
            if component not in component_errors:
                component_errors[component] = 0
            component_errors[component] += 1
        
        # 按类型分组
        type_errors = {}
        for error in today_errors:
            error_type = error['type']
            if error_type not in type_errors:
                type_errors[error_type] = 0
            type_errors[error_type] += 1
        
        return {
            'total_errors_today': len(today_errors),
            'errors_by_component': component_errors,
            'errors_by_type': type_errors,
            'recent_errors': today_errors[-10:] if today_errors else []
        }
    
    def _calculate_health_status(self) -> Dict:
        """
        计算系统健康状态
        
        Returns:
            健康状态信息
        """
        # 根据各种指标计算健康分数（0-100）
        health_score = 100
        
        # 系统资源使用
        system_metrics = self._aggregate_system_metrics()
        if system_metrics:
            if system_metrics.get('average_cpu_percent', 0) > 80:
                health_score -= 20
            if system_metrics.get('average_memory_percent', 0) > 90:
                health_score -= 30
            if system_metrics.get('disk_usage_percent', 0) > 95:
                health_score -= 40
        
        # 交易错误率
        trade_stats = self._aggregate_trade_statistics()
        total_trades = trade_stats.get('total_trades', 0)
        failed_trades = trade_stats.get('failed_trades', 0)
        if total_trades > 0:
            failure_rate = failed_trades / total_trades
            if failure_rate > 0.3:
                health_score -= 30
            elif failure_rate > 0.1:
                health_score -= 10
        
        # 错误数量
        error_summary = self._aggregate_error_summary()
        if error_summary.get('total_errors_today', 0) > 50:
            health_score -= 20
        elif error_summary.get('total_errors_today', 0) > 10:
            health_score -= 10
        
        # 确保分数在0-100之间
        health_score = max(0, min(100, health_score))
        
        # 确定状态
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 60:
            status = 'fair'
        elif health_score >= 40:
            status = 'poor'
        else:
            status = 'critical'
        
        return {
            'health_score': health_score,
            'status': status,
            'last_updated': datetime.now().isoformat()
        }
    
    def _generate_text_report(self, report_data: Dict):
        """
        生成文本格式的报告用于日志
        
        Args:
            report_data: 报告数据
        """
        try:
            health = report_data['health_status']
            trade_stats = report_data['trade_statistics']
            agent_perf = report_data['agent_performance']
            system_metrics = report_data['system_metrics']
            
            report_text = (
                "\n========== 系统状态报告 ==========\n"
                f"时间: {report_data['report_time']}\n"
                f"健康状态: {health['status'].upper()} ({health['health_score']}/100)\n"
                "\n交易统计:\n"
                f"  总交易: {trade_stats.get('total_trades', 0)}\n"
                f"  胜率: {trade_stats.get('win_rate', 0)*100:.1f}%\n"
                f"  总盈亏: {trade_stats.get('total_pnl', 0):.2f}\n"
                f"  今日交易: {trade_stats.get('today_trades', 0)}\n"
                f"  今日盈亏: {trade_stats.get('today_pnl', 0):.2f}\n"
                "\n代理状态:\n"
                f"  总代理数: {agent_perf.get('total_agents', 0)}\n"
                f"  存活代理: {agent_perf.get('alive_agents', 0)}\n"
                f"  平均ROI: {agent_perf.get('average_roi', 0)*100:.2f}%\n"
                "\n系统资源:\n"
                f"  CPU使用率: {system_metrics.get('average_cpu_percent', 0):.1f}%\n"
                f"  内存使用率: {system_metrics.get('average_memory_percent', 0):.1f}%\n"
                f"  磁盘使用率: {system_metrics.get('disk_usage_percent', 0):.1f}%\n"
                "==================================\n"
            )
            
            logger.info(report_text)
            
        except Exception as e:
            logger.error(f"生成文本报告失败: {e}")
    
    def _cleanup_old_data(self):
        """
        清理过期的数据
        """
        try:
            cutoff_time = (datetime.now() - timedelta(hours=self.data_retention_hours)).isoformat()
            
            # 清理性能指标
            self.performance_metrics = [m for m in self.performance_metrics if m['timestamp'] >= cutoff_time]
            
            # 清理交易统计
            self.trade_statistics = [s for s in self.trade_statistics if s['timestamp'] >= cutoff_time]
            
            # 清理代理指标
            self.agent_metrics = [a for a in self.agent_metrics if a['timestamp'] >= cutoff_time]
            
            # 清理错误日志
            self.error_logs = [e for e in self.error_logs if e['timestamp'] >= cutoff_time]
            
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def get_latest_health_status(self) -> Dict:
        """
        获取最新的健康状态
        
        Returns:
            健康状态信息
        """
        return self._calculate_health_status()
    
    def get_performance_summary(self) -> Dict:
        """
        获取性能摘要
        
        Returns:
            性能摘要数据
        """
        return {
            'system_metrics': self._aggregate_system_metrics(),
            'trade_statistics': self._aggregate_trade_statistics(),
            'agent_performance': self._aggregate_agent_performance(),
            'health_status': self._calculate_health_status()
        }
    
    def update_system_metrics(self, *args, **kwargs):
        """
        更新系统指标
        
        收集并更新系统资源使用情况的指标，包括CPU、内存、磁盘和网络使用情况。
        这个方法被外部组件调用以定期更新系统状态。
        
        Args:
            *args: 可变位置参数，用于兼容不同的调用方式
            **kwargs: 可变关键字参数，用于兼容不同的调用方式
        """
        try:
            # 调用现有的收集系统指标方法
            self._collect_system_metrics()
            logger.debug("系统指标已更新")
        except Exception as e:
            logger.error(f"更新系统指标失败: {e}")
    
    def update_trade_statistics(self, *args, **kwargs):
        """
        更新交易统计信息
        
        记录和更新交易统计数据，这个方法被外部组件调用以跟踪交易活动。
        
        Args:
            *args: 可变位置参数，用于兼容不同的调用方式
            **kwargs: 可变关键字参数，包含交易统计信息
        """
        try:
            # 如果提供了交易统计数据，则记录它
            if kwargs:
                self.record_trade_statistics(kwargs)
            logger.debug("交易统计已更新")
        except Exception as e:
            logger.error(f"更新交易统计失败: {e}")
    
    def update_agent_performance(self, *args, **kwargs):
        """
        更新代理性能指标
        
        记录和更新代理的性能指标，这个方法被外部组件调用以跟踪代理活动。
        
        Args:
            *args: 可变位置参数，用于兼容不同的调用方式
            **kwargs: 可变关键字参数，包含代理ID和性能指标
        """
        try:
            # 检查是否提供了代理ID和指标
            if len(args) > 0:
                agent_id = args[0]
                # 尝试从args或kwargs中获取指标
                metrics = args[1] if len(args) > 1 else kwargs
                self.record_agent_metrics(agent_id, metrics)
            logger.debug("代理性能已更新")
        except Exception as e:
            logger.error(f"更新代理性能失败: {e}")
