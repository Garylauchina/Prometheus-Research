"""
交易报告生成器

负责生成详细的交易记录和性能分析报告
"""

import logging
import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)


class TradeReporter:
    """
    交易报告生成器 - 生成各类交易报告和性能分析
    """
    
    def __init__(self, config: Dict):
        """
        初始化报告生成器
        
        Args:
            config: 报告配置
                - report_dir: 报告保存目录
                - generate_charts: 是否生成图表
                - report_formats: 报告格式列表 ['json', 'csv', 'pdf']
        """
        self.config = config
        self.report_dir = config.get('report_dir', 'reports')
        self.generate_charts = config.get('generate_charts', True)
        self.report_formats = config.get('report_formats', ['json', 'csv'])
        
        # 确保报告目录存在
        os.makedirs(self.report_dir, exist_ok=True)
        
        # 图表保存目录
        self.chart_dir = os.path.join(self.report_dir, 'charts')
        os.makedirs(self.chart_dir, exist_ok=True)
        
        # 交易记录
        self.trades = []
        
        logger.info(f"交易报告生成器初始化完成，报告目录: {self.report_dir}")
    
    def record_trade(self, trade_data: Dict):
        """
        记录一笔交易
        
        Args:
            trade_data: 交易数据
                - trade_id: 交易ID
                - agent_id: 代理ID
                - symbol: 交易对
                - side: 方向 (buy/sell)
                - type: 订单类型
                - price: 价格
                - quantity: 数量
                - amount: 金额
                - fee: 手续费
                - timestamp: 时间戳
                - status: 状态
                - profit_loss: 盈亏（平仓时）
                - holding_time: 持仓时间（平仓时）
        """
        # 确保必要字段存在
        required_fields = ['trade_id', 'agent_id', 'symbol', 'side', 'price', 'quantity', 'timestamp']
        for field in required_fields:
            if field not in trade_data:
                logger.warning(f"交易记录缺少必要字段: {field}")
                trade_data[field] = None
        
        # 添加交易到记录
        self.trades.append(trade_data)
        
        logger.debug(f"记录交易: {trade_data['trade_id']} - {trade_data['side']} {trade_data['symbol']}")
    
    def generate_daily_report(self, date: Optional[datetime] = None):
        """
        生成每日报告
        
        Args:
            date: 报告日期，默认今天
            
        Returns:
            报告文件路径列表
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y-%m-%d')
        logger.info(f"生成{date_str}的每日交易报告")
        
        # 过滤当天的交易
        day_start = datetime.combine(date.date(), datetime.min.time())
        day_end = datetime.combine(date.date(), datetime.max.time())
        
        day_trades = []
        for trade in self.trades:
            trade_time = trade.get('timestamp')
            if isinstance(trade_time, str):
                trade_time = datetime.fromisoformat(trade_time)
            elif isinstance(trade_time, (int, float)):
                trade_time = datetime.fromtimestamp(trade_time)
            
            if trade_time >= day_start and trade_time <= day_end:
                day_trades.append(trade)
        
        # 分析当天交易
        analysis = self._analyze_trades(day_trades)
        
        # 准备报告数据
        report_data = {
            'report_date': date_str,
            'report_type': 'daily',
            'generated_at': datetime.now().isoformat(),
            'total_trades': len(day_trades),
            'analysis': analysis,
            'trades': day_trades
        }
        
        # 生成报告文件
        file_paths = self._save_report(report_data, f"daily_{date_str}")
        
        # 生成图表
        if self.generate_charts and day_trades:
            self._generate_trade_charts(day_trades, analysis, f"daily_{date_str}")
        
        return file_paths
    
    def generate_weekly_report(self, start_date: Optional[datetime] = None):
        """
        生成每周报告
        
        Args:
            start_date: 周开始日期，默认本周一
            
        Returns:
            报告文件路径列表
        """
        if start_date is None:
            # 获取本周一
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        logger.info(f"生成{start_date_str}至{end_date_str}的每周交易报告")
        
        # 过滤本周的交易
        week_trades = []
        for trade in self.trades:
            trade_time = trade.get('timestamp')
            if isinstance(trade_time, str):
                trade_time = datetime.fromisoformat(trade_time)
            elif isinstance(trade_time, (int, float)):
                trade_time = datetime.fromtimestamp(trade_time)
            
            if trade_time >= start_date and trade_time <= end_date:
                week_trades.append(trade)
        
        # 分析本周交易
        analysis = self._analyze_trades(week_trades)
        
        # 准备报告数据
        report_data = {
            'report_period': f"{start_date_str} to {end_date_str}",
            'report_type': 'weekly',
            'generated_at': datetime.now().isoformat(),
            'total_trades': len(week_trades),
            'analysis': analysis,
            'trades': week_trades
        }
        
        # 生成报告文件
        file_paths = self._save_report(report_data, f"weekly_{start_date_str}_{end_date_str}")
        
        # 生成图表
        if self.generate_charts and week_trades:
            self._generate_trade_charts(week_trades, analysis, f"weekly_{start_date_str}_{end_date_str}")
        
        return file_paths
    
    def generate_monthly_report(self, year: int = None, month: int = None):
        """
        生成月度报告
        
        Args:
            year: 年份
            month: 月份
            
        Returns:
            报告文件路径列表
        """
        if year is None or month is None:
            today = datetime.now()
            year = today.year
            month = today.month
        
        # 获取月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        period_str = f"{year}-{month:02d}"
        logger.info(f"生成{period_str}的月度交易报告")
        
        # 过滤本月的交易
        month_trades = []
        for trade in self.trades:
            trade_time = trade.get('timestamp')
            if isinstance(trade_time, str):
                trade_time = datetime.fromisoformat(trade_time)
            elif isinstance(trade_time, (int, float)):
                trade_time = datetime.fromtimestamp(trade_time)
            
            if trade_time >= start_date and trade_time <= end_date:
                month_trades.append(trade)
        
        # 分析本月交易
        analysis = self._analyze_trades(month_trades)
        
        # 准备报告数据
        report_data = {
            'report_period': period_str,
            'report_type': 'monthly',
            'generated_at': datetime.now().isoformat(),
            'total_trades': len(month_trades),
            'analysis': analysis,
            'trades': month_trades
        }
        
        # 生成报告文件
        file_paths = self._save_report(report_data, f"monthly_{period_str}")
        
        # 生成图表
        if self.generate_charts and month_trades:
            self._generate_trade_charts(month_trades, analysis, f"monthly_{period_str}")
        
        return file_paths
    
    def generate_agent_report(self, agent_id: int):
        """
        生成特定代理的报告
        
        Args:
            agent_id: 代理ID
            
        Returns:
            报告文件路径列表
        """
        logger.info(f"生成代理 {agent_id} 的交易报告")
        
        # 过滤该代理的交易
        agent_trades = [t for t in self.trades if t.get('agent_id') == agent_id]
        
        # 分析代理交易
        analysis = self._analyze_trades(agent_trades)
        
        # 准备报告数据
        report_data = {
            'agent_id': agent_id,
            'report_type': 'agent',
            'generated_at': datetime.now().isoformat(),
            'total_trades': len(agent_trades),
            'analysis': analysis,
            'trades': agent_trades
        }
        
        # 生成报告文件
        file_paths = self._save_report(report_data, f"agent_{agent_id}")
        
        # 生成图表
        if self.generate_charts and agent_trades:
            self._generate_trade_charts(agent_trades, analysis, f"agent_{agent_id}")
        
        return file_paths
    
    def generate_performance_summary(self) -> Dict:
        """
        生成性能摘要
        
        Returns:
            性能摘要数据
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'total_profit_loss': 0,
                'win_rate': 0,
                'average_profit_loss': 0,
                'best_trade': None,
                'worst_trade': None
            }
        
        # 分析所有交易
        analysis = self._analyze_trades(self.trades)
        
        return {
            'total_trades': len(self.trades),
            'total_profit_loss': analysis.get('total_profit_loss', 0),
            'win_rate': analysis.get('win_rate', 0),
            'average_profit_loss': analysis.get('average_profit_loss', 0),
            'best_trade': analysis.get('best_trade', None),
            'worst_trade': analysis.get('worst_trade', None),
            'profit_factor': analysis.get('profit_factor', 0)
        }
    
    def _analyze_trades(self, trades: List[Dict]) -> Dict:
        """
        分析交易数据
        
        Args:
            trades: 交易列表
            
        Returns:
            分析结果
        """
        if not trades:
            return {
                'total_profit_loss': 0,
                'win_rate': 0,
                'average_profit_loss': 0,
                'total_volume': 0,
                'total_fees': 0,
                'trades_by_symbol': {},
                'trades_by_side': {},
                'trades_by_hour': {},
                'best_trade': None,
                'worst_trade': None,
                'profit_factor': 0
            }
        
        # 计算总盈亏
        total_profit_loss = sum(t.get('profit_loss', 0) for t in trades)
        
        # 计算胜率
        profitable_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
        win_rate = len(profitable_trades) / len(trades) if trades else 0
        
        # 平均盈亏
        average_profit_loss = total_profit_loss / len(trades) if trades else 0
        
        # 总交易量
        total_volume = sum(t.get('amount', 0) for t in trades)
        
        # 总手续费
        total_fees = sum(t.get('fee', 0) for t in trades)
        
        # 按交易对统计
        trades_by_symbol = {}
        for trade in trades:
            symbol = trade.get('symbol', 'unknown')
            if symbol not in trades_by_symbol:
                trades_by_symbol[symbol] = 0
            trades_by_symbol[symbol] += 1
        
        # 按方向统计
        trades_by_side = {'buy': 0, 'sell': 0}
        for trade in trades:
            side = trade.get('side', 'unknown')
            if side in trades_by_side:
                trades_by_side[side] += 1
        
        # 按小时统计交易分布
        trades_by_hour = {}
        for trade in trades:
            trade_time = trade.get('timestamp')
            if isinstance(trade_time, str):
                trade_time = datetime.fromisoformat(trade_time)
            elif isinstance(trade_time, (int, float)):
                trade_time = datetime.fromtimestamp(trade_time)
            
            hour = trade_time.hour
            if hour not in trades_by_hour:
                trades_by_hour[hour] = 0
            trades_by_hour[hour] += 1
        
        # 找出最佳和最差交易
        best_trade = None
        worst_trade = None
        max_profit = float('-inf')
        max_loss = float('inf')
        
        for trade in trades:
            pl = trade.get('profit_loss', 0)
            if pl > max_profit:
                max_profit = pl
                best_trade = trade
            if pl < max_loss:
                max_loss = pl
                worst_trade = trade
        
        # 计算盈利因子
        profits = sum(t.get('profit_loss', 0) for t in trades if t.get('profit_loss', 0) > 0)
        losses = sum(abs(t.get('profit_loss', 0)) for t in trades if t.get('profit_loss', 0) < 0)
        profit_factor = profits / losses if losses > 0 else float('inf')
        
        return {
            'total_profit_loss': total_profit_loss,
            'win_rate': win_rate,
            'average_profit_loss': average_profit_loss,
            'total_volume': total_volume,
            'total_fees': total_fees,
            'trades_by_symbol': trades_by_symbol,
            'trades_by_side': trades_by_side,
            'trades_by_hour': trades_by_hour,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'profit_factor': profit_factor
        }
    
    def _save_report(self, report_data: Dict, filename_base: str) -> List[str]:
        """
        保存报告到文件
        
        Args:
            report_data: 报告数据
            filename_base: 文件名基础
            
        Returns:
            保存的文件路径列表
        """
        file_paths = []
        
        # 保存为JSON
        if 'json' in self.report_formats:
            json_path = os.path.join(self.report_dir, f"{filename_base}.json")
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
                file_paths.append(json_path)
                logger.debug(f"JSON报告已保存: {json_path}")
            except Exception as e:
                logger.error(f"保存JSON报告失败: {e}")
        
        # 保存为CSV（只保存交易记录）
        if 'csv' in self.report_formats and 'trades' in report_data:
            csv_path = os.path.join(self.report_dir, f"{filename_base}.csv")
            try:
                if report_data['trades']:
                    # 获取所有可能的字段名
                    fieldnames = set()
                    for trade in report_data['trades']:
                        fieldnames.update(trade.keys())
                    
                    # 确保时间戳在前面
                    ordered_fields = ['timestamp', 'trade_id', 'agent_id', 'symbol', 'side', 'price', 'quantity', 'amount', 'fee', 'profit_loss']
                    # 添加剩余字段
                    for field in sorted(fieldnames):
                        if field not in ordered_fields:
                            ordered_fields.append(field)
                    
                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=ordered_fields)
                        writer.writeheader()
                        for trade in report_data['trades']:
                            writer.writerow(trade)
                    file_paths.append(csv_path)
                    logger.debug(f"CSV报告已保存: {csv_path}")
            except Exception as e:
                logger.error(f"保存CSV报告失败: {e}")
        
        return file_paths
    
    def _generate_trade_charts(self, trades: List[Dict], analysis: Dict, filename_base: str):
        """
        生成交易相关图表
        
        Args:
            trades: 交易列表
            analysis: 分析结果
            filename_base: 文件名基础
        """
        try:
            # 创建交易时间序列数据
            timestamps = []
            cumulative_pnl = []
            current_pnl = 0
            
            # 按时间排序交易
            sorted_trades = sorted(trades, key=lambda x: x.get('timestamp', 0))
            
            for trade in sorted_trades:
                # 处理时间戳
                ts = trade.get('timestamp')
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                elif isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts)
                
                timestamps.append(ts)
                
                # 累计盈亏
                pl = trade.get('profit_loss', 0)
                current_pnl += pl
                cumulative_pnl.append(current_pnl)
            
            # 图表1: 累计盈亏曲线
            plt.figure(figsize=(12, 6))
            plt.plot(timestamps, cumulative_pnl, marker='o', linestyle='-', markersize=3)
            plt.title('累计盈亏曲线')
            plt.xlabel('时间')
            plt.ylabel('累计盈亏')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            chart_path = os.path.join(self.chart_dir, f"{filename_base}_cumulative_pnl.png")
            plt.savefig(chart_path)
            plt.close()
            
            # 图表2: 交易方向分布
            plt.figure(figsize=(10, 6))
            side_data = analysis.get('trades_by_side', {})
            if side_data:
                plt.bar(side_data.keys(), side_data.values(), color=['green', 'red'])
                plt.title('交易方向分布')
                plt.xlabel('方向')
                plt.ylabel('交易次数')
                plt.tight_layout()
                
                chart_path = os.path.join(self.chart_dir, f"{filename_base}_side_distribution.png")
                plt.savefig(chart_path)
                plt.close()
            
            # 图表3: 交易时间分布（按小时）
            plt.figure(figsize=(12, 6))
            hour_data = analysis.get('trades_by_hour', {})
            if hour_data:
                hours = list(range(24))
                counts = [hour_data.get(h, 0) for h in hours]
                
                plt.bar(hours, counts, color='blue')
                plt.title('交易时间分布（按小时）')
                plt.xlabel('小时')
                plt.ylabel('交易次数')
                plt.xticks(hours)
                plt.tight_layout()
                
                chart_path = os.path.join(self.chart_dir, f"{filename_base}_hourly_distribution.png")
                plt.savefig(chart_path)
                plt.close()
            
            # 图表4: 交易对分布
            plt.figure(figsize=(12, 6))
            symbol_data = analysis.get('trades_by_symbol', {})
            if symbol_data:
                # 只显示前10个交易对
                top_symbols = dict(sorted(symbol_data.items(), key=lambda x: x[1], reverse=True)[:10])
                plt.bar(top_symbols.keys(), top_symbols.values(), color='orange')
                plt.title('交易对分布（Top 10）')
                plt.xlabel('交易对')
                plt.ylabel('交易次数')
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                chart_path = os.path.join(self.chart_dir, f"{filename_base}_symbol_distribution.png")
                plt.savefig(chart_path)
                plt.close()
            
            logger.debug(f"交易图表已生成，基础文件名: {filename_base}")
            
        except Exception as e:
            logger.error(f"生成交易图表失败: {e}")
    
    def get_trade_history(self, limit: int = None) -> List[Dict]:
        """
        获取交易历史
        
        Args:
            limit: 返回交易数量限制
            
        Returns:
            交易历史列表
        """
        if limit is not None:
            return self.trades[-limit:]
        return self.trades
    
    def clear_trade_history(self):
        """
        清空交易历史
        """
        self.trades = []
        logger.info("交易历史已清空")
    
    def export_trades(self, filename: str, format: str = 'json') -> bool:
        """
        导出交易记录
        
        Args:
            filename: 文件名
            format: 格式 ('json' 或 'csv')
            
        Returns:
            是否成功
        """
        try:
            full_path = os.path.join(self.report_dir, filename)
            
            if format == 'json':
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(self.trades, f, indent=2, ensure_ascii=False, default=str)
                logger.info(f"交易记录已导出为JSON: {full_path}")
                return True
            
            elif format == 'csv':
                if not self.trades:
                    logger.warning("没有交易记录可导出")
                    return False
                
                # 获取所有字段
                fieldnames = set()
                for trade in self.trades:
                    fieldnames.update(trade.keys())
                
                # 确保时间戳在前面
                ordered_fields = ['timestamp', 'trade_id', 'agent_id', 'symbol', 'side', 'price', 'quantity', 'amount', 'fee', 'profit_loss']
                for field in sorted(fieldnames):
                    if field not in ordered_fields:
                        ordered_fields.append(field)
                
                with open(full_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=ordered_fields)
                    writer.writeheader()
                    for trade in self.trades:
                        writer.writerow(trade)
                
                logger.info(f"交易记录已导出为CSV: {full_path}")
                return True
            
            else:
                logger.error(f"不支持的导出格式: {format}")
                return False
                
        except Exception as e:
            logger.error(f"导出交易记录失败: {e}")
            return False
