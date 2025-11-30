"""
交易警报系统

负责监控交易系统的关键指标并在达到阈值时发送警报
"""

import logging
import json
import smtplib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests

logger = logging.getLogger(__name__)


class AlertSystem:
    """
    交易警报系统 - 监控关键指标并在达到阈值时发送警报
    """
    
    def __init__(self, config: Dict):
        """
        初始化警报系统
        
        Args:
            config: 警报配置
                - alert_channels: 警报渠道配置
                    - email: 邮件配置
                    - telegram: Telegram配置
                    - webhook: Webhook配置
                - thresholds: 警报阈值配置
                - cooldown_period: 冷却时间（秒）
        """
        self.config = config
        self.alert_channels = config.get('alert_channels', {})
        self.thresholds = config.get('thresholds', {})
        self.cooldown_period = config.get('cooldown_period', 300)  # 默认5分钟冷却
        
        # 记录最近的警报时间，用于冷却机制
        self.last_alert_time: Dict[str, datetime] = {}
        
        # 警报计数器
        self.alert_counter = 0
        
        logger.info("交易警报系统初始化完成")
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """
        直接发送警报（兼容旧API）
        
        Args:
            alert_type: 警报类型
            message: 警报消息
            severity: 警报严重性 (info, warning, error, critical)
            
        Returns:
            bool: 是否成功发送
        """
        # 调用现有方法
        return self.check_and_send_alert(alert_type, message, severity)
    
    def check_and_send_alert(self, alert_type: str, message: str, 
                           severity: str = 'warning', 
                           data: Optional[Dict] = None, 
                           force_send: bool = False):
        """
        检查并发送警报
        
        Args:
            alert_type: 警报类型
            message: 警报消息
            severity: 严重程度 ('info', 'warning', 'error', 'critical')
            data: 附加数据
            force_send: 是否强制发送（忽略冷却）
            
        Returns:
            是否发送了警报
        """
        # 检查冷却时间
        if not force_send:
            now = datetime.now()
            last_time = self.last_alert_time.get(alert_type)
            if last_time and (now - last_time).total_seconds() < self.cooldown_period:
                logger.debug(f"警报 {alert_type} 处于冷却期，跳过发送")
                return False
        
        # 更新最后警报时间
        self.last_alert_time[alert_type] = datetime.now()
        
        # 生成警报ID
        alert_id = f"ALERT-{self.alert_counter:06d}"
        self.alert_counter += 1
        
        # 构建完整警报数据
        alert_data = {
            'alert_id': alert_id,
            'alert_type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        # 发送警报到所有配置的渠道
        sent = False
        for channel_name, channel_config in self.alert_channels.items():
            if channel_config.get('enabled', False):
                try:
                    if channel_name == 'email':
                        self._send_email_alert(alert_data, channel_config)
                    elif channel_name == 'telegram':
                        self._send_telegram_alert(alert_data, channel_config)
                    elif channel_name == 'webhook':
                        self._send_webhook_alert(alert_data, channel_config)
                    sent = True
                    logger.info(f"警报 {alert_id} 已发送到 {channel_name}")
                except Exception as e:
                    logger.error(f"发送警报到 {channel_name} 失败: {e}")
        
        return sent
    
    def check_daily_loss_limit(self, daily_pnl: float):
        """
        检查每日亏损限制
        
        Args:
            daily_pnl: 当日盈亏
        """
        daily_loss_limit = self.thresholds.get('daily_loss_limit')
        if daily_loss_limit is not None and daily_pnl <= -daily_loss_limit:
            message = f"每日亏损限制被触发！当日亏损: {daily_pnl:.2f}，限制: {daily_loss_limit}"
            self.check_and_send_alert(
                'DAILY_LOSS_LIMIT',
                message,
                severity='critical',
                data={'daily_pnl': daily_pnl, 'limit': daily_loss_limit}
            )
    
    def check_max_drawdown(self, current_drawdown: float):
        """
        检查最大回撤
        
        Args:
            current_drawdown: 当前回撤
        """
        max_drawdown_limit = self.thresholds.get('max_drawdown_limit')
        if max_drawdown_limit is not None and current_drawdown >= max_drawdown_limit:
            message = f"最大回撤限制被触发！当前回撤: {current_drawdown:.2f}%，限制: {max_drawdown_limit:.2f}%"
            self.check_and_send_alert(
                'MAX_DRAWDOWN',
                message,
                severity='critical',
                data={'drawdown': current_drawdown, 'limit': max_drawdown_limit}
            )
    
    def check_api_error_rate(self, error_rate: float):
        """
        检查API错误率
        
        Args:
            error_rate: API错误率（0-1）
        """
        api_error_threshold = self.thresholds.get('api_error_threshold', 0.1)
        if error_rate >= api_error_threshold:
            message = f"API错误率过高！当前错误率: {error_rate:.2%}，阈值: {api_error_threshold:.2%}"
            self.check_and_send_alert(
                'API_ERROR_RATE',
                message,
                severity='warning',
                data={'error_rate': error_rate, 'threshold': api_error_threshold}
            )
    
    def check_account_balance(self, balance: float, min_balance: float):
        """
        检查账户余额
        
        Args:
            balance: 当前账户余额
            min_balance: 最小余额限制
        """
        if balance < min_balance:
            message = f"账户余额过低！当前余额: {balance:.2f}，最小要求: {min_balance:.2f}"
            self.check_and_send_alert(
                'LOW_ACCOUNT_BALANCE',
                message,
                severity='warning',
                data={'balance': balance, 'min_balance': min_balance}
            )
    
    def check_position_size(self, position_size: float, max_position_size: float):
        """
        检查仓位大小
        
        Args:
            position_size: 当前仓位大小
            max_position_size: 最大允许仓位大小
        """
        if position_size > max_position_size:
            message = f"仓位过大！当前仓位: {position_size:.2f}，最大允许: {max_position_size:.2f}"
            self.check_and_send_alert(
                'LARGE_POSITION_SIZE',
                message,
                severity='warning',
                data={'position_size': position_size, 'max_position_size': max_position_size}
            )
    
    def check_system_health(self, health_score: float):
        """
        检查系统健康状态
        
        Args:
            health_score: 健康分数（0-100）
        """
        critical_threshold = self.thresholds.get('health_score_critical', 40)
        warning_threshold = self.thresholds.get('health_score_warning', 60)
        
        if health_score <= critical_threshold:
            message = f"系统健康状态严重！健康分数: {health_score:.1f}/100，严重阈值: {critical_threshold}"
            self.check_and_send_alert(
                'SYSTEM_HEALTH_CRITICAL',
                message,
                severity='critical',
                data={'health_score': health_score, 'threshold': critical_threshold}
            )
        elif health_score <= warning_threshold:
            message = f"系统健康状态警告！健康分数: {health_score:.1f}/100，警告阈值: {warning_threshold}"
            self.check_and_send_alert(
                'SYSTEM_HEALTH_WARNING',
                message,
                severity='warning',
                data={'health_score': health_score, 'threshold': warning_threshold}
            )
    
    def check_trade_execution_error(self, trade_error: str, symbol: str):
        """
        检查交易执行错误
        
        Args:
            trade_error: 错误信息
            symbol: 交易对
        """
        message = f"交易执行失败！交易对: {symbol}，错误: {trade_error}"
        self.check_and_send_alert(
            'TRADE_EXECUTION_ERROR',
            message,
            severity='error',
            data={'error': trade_error, 'symbol': symbol}
        )
    
    def check_exchange_connection(self, is_connected: bool):
        """
        检查交易所连接状态
        
        Args:
            is_connected: 是否连接
        """
        if not is_connected:
            message = "交易所连接断开！请检查网络和API状态"
            self.check_and_send_alert(
                'EXCHANGE_DISCONNECTED',
                message,
                severity='critical'
            )
    
    def _send_email_alert(self, alert_data: Dict, email_config: Dict):
        """
        通过邮件发送警报
        
        Args:
            alert_data: 警报数据
            email_config: 邮件配置
        """
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = email_config['sender']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = f"[{alert_data['severity'].upper()}] {alert_data['alert_type']}: {alert_data['message']}"
            
            # 邮件正文
            body = f"""
            <html>
            <body>
                <h2>交易系统警报</h2>
                <p><strong>警报ID:</strong> {alert_data['alert_id']}</p>
                <p><strong>类型:</strong> {alert_data['alert_type']}</p>
                <p><strong>严重程度:</strong> {alert_data['severity']}</p>
                <p><strong>时间:</strong> {alert_data['timestamp']}</p>
                <p><strong>消息:</strong> {alert_data['message']}</p>
                
                {self._format_data_for_email(alert_data['data'])}                
                
                <p>---<br>此邮件由Prometheus V30交易系统自动发送</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 添加JSON附件
            json_str = json.dumps(alert_data, indent=2)
            attachment = MIMEApplication(json_str)
            attachment.add_header('Content-Disposition', 'attachment', filename=f"alert_{alert_data['alert_id']}.json")
            msg.attach(attachment)
            
            # 发送邮件
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                if 'username' in email_config and 'password' in email_config:
                    server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            logger.debug(f"邮件警报已发送: {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"发送邮件警报失败: {e}")
            raise
    
    def _format_data_for_email(self, data: Dict) -> str:
        """
        格式化数据为HTML表格
        
        Args:
            data: 数据字典
            
        Returns:
            HTML表格
        """
        if not data:
            return ""
        
        html = "<h3>详细信息</h3><table border='1' cellpadding='5' cellspacing='0'>"
        for key, value in data.items():
            html += f"<tr><td><strong>{key}</strong></td><td>{self._format_value_for_html(value)}</td></tr>"
        html += "</table>"
        return html
    
    def _format_value_for_html(self, value) -> str:
        """
        格式化值为HTML友好格式
        
        Args:
            value: 要格式化的值
            
        Returns:
            HTML字符串
        """
        if isinstance(value, dict):
            return f"<pre>{json.dumps(value, indent=2)}</pre>"
        elif isinstance(value, list):
            if len(value) > 10:
                return f"<pre>{json.dumps(value[:10], indent=2)}...</pre><p>还有 {len(value) - 10} 项未显示</p>"
            else:
                return f"<pre>{json.dumps(value, indent=2)}</pre>"
        elif isinstance(value, (float, int)) and isinstance(value, (int, float)):
            # 格式化数字
            if value >= 1000000:
                return f"{value/1000000:.2f}M"
            elif value >= 1000:
                return f"{value/1000:.2f}K"
            else:
                return f"{value:.2f}"
        else:
            return str(value)
    
    def _send_telegram_alert(self, alert_data: Dict, telegram_config: Dict):
        """
        通过Telegram发送警报
        
        Args:
            alert_data: 警报数据
            telegram_config: Telegram配置
        """
        try:
            bot_token = telegram_config['bot_token']
            chat_id = telegram_config['chat_id']
            
            # 构建消息文本
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }.get(alert_data['severity'], '📢')
            
            message = f"{severity_emoji} <b>交易系统警报</b> {severity_emoji}\n\n"
            message += f"<b>警报ID:</b> {alert_data['alert_id']}\n"
            message += f"<b>类型:</b> {alert_data['alert_type']}\n"
            message += f"<b>严重程度:</b> {alert_data['severity']}\n"
            message += f"<b>时间:</b> {alert_data['timestamp']}\n"
            message += f"<b>消息:</b> {alert_data['message']}\n"
            
            # 简洁显示数据
            if alert_data['data']:
                message += "\n<b>详细信息:</b>\n"
                for key, value in alert_data['data'].items():
                    if isinstance(value, (int, float)):
                        if key.lower() in ['pnl', 'profit_loss']:
                            message += f"- {key}: {value:.2f}\n"
                        else:
                            message += f"- {key}: {value}\n"
                    else:
                        message += f"- {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}\n"
            
            # 发送请求
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.debug(f"Telegram警报已发送: {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"发送Telegram警报失败: {e}")
            raise
    
    def _send_webhook_alert(self, alert_data: Dict, webhook_config: Dict):
        """
        通过Webhook发送警报
        
        Args:
            alert_data: 警报数据
            webhook_config: Webhook配置
        """
        try:
            webhook_url = webhook_config['url']
            headers = webhook_config.get('headers', {})
            
            # 发送请求
            response = requests.post(
                webhook_url,
                json=alert_data,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            logger.debug(f"Webhook警报已发送: {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"发送Webhook警报失败: {e}")
            raise
    
    def send_custom_alert(self, title: str, description: str, 
                         severity: str = 'info', 
                         additional_data: Optional[Dict] = None):
        """
        发送自定义警报
        
        Args:
            title: 警报标题
            description: 警报描述
            severity: 严重程度
            additional_data: 附加数据
        """
        self.check_and_send_alert(
            'CUSTOM_ALERT',
            f"{title}: {description}",
            severity=severity,
            data={
                'title': title,
                'description': description,
                **(additional_data or {})
            }
        )
    
    def send_system_startup_alert(self):
        """
        发送系统启动警报
        """
        message = "Prometheus V30交易系统已启动"
        self.check_and_send_alert(
            'SYSTEM_STARTUP',
            message,
            severity='info',
            force_send=True
        )
    
    def send_system_shutdown_alert(self, reason: str = '正常关闭'):
        """
        发送系统关闭警报
        
        Args:
            reason: 关闭原因
        """
        message = f"Prometheus V30交易系统已关闭: {reason}"
        self.check_and_send_alert(
            'SYSTEM_SHUTDOWN',
            message,
            severity='info',
            force_send=True
        )
    
    def send_daily_summary(self, summary_data: Dict):
        """
        发送每日摘要
        
        Args:
            summary_data: 摘要数据
                - total_trades: 总交易次数
                - total_pnl: 总盈亏
                - win_rate: 胜率
                - best_trade: 最佳交易
                - worst_trade: 最差交易
        """
        total_trades = summary_data.get('total_trades', 0)
        total_pnl = summary_data.get('total_pnl', 0)
        win_rate = summary_data.get('win_rate', 0)
        
        # 根据盈亏决定图标
        emoji = '📈' if total_pnl > 0 else '📉' if total_pnl < 0 else '📊'
        
        message = f"{emoji} <b>交易系统每日摘要</b> {emoji}\n\n"
        message += f"<b>交易次数:</b> {total_trades}\n"
        message += f"<b>总盈亏:</b> {total_pnl:.2f}\n"
        message += f"<b>胜率:</b> {win_rate:.2%}\n"
        
        # 添加最佳和最差交易
        best_trade = summary_data.get('best_trade')
        if best_trade:
            message += f"\n<b>最佳交易:</b> {best_trade.get('symbol')} {best_trade.get('side')} {best_trade.get('profit_loss', 0):.2f}\n"
        
        worst_trade = summary_data.get('worst_trade')
        if worst_trade:
            message += f"<b>最差交易:</b> {worst_trade.get('symbol')} {worst_trade.get('side')} {worst_trade.get('profit_loss', 0):.2f}\n"
        
        # 发送到所有启用的渠道
        alert_data = {
            'alert_id': f"SUMMARY-{self.alert_counter:06d}",
            'alert_type': 'DAILY_SUMMARY',
            'message': message,
            'severity': 'info',
            'timestamp': datetime.now().isoformat(),
            'data': summary_data
        }
        
        for channel_name, channel_config in self.alert_channels.items():
            if channel_config.get('enabled', False) and channel_name in ['email', 'telegram']:
                try:
                    if channel_name == 'email':
                        # 为邮件重新格式化消息
                        self._send_email_summary(alert_data, channel_config)
                    elif channel_name == 'telegram':
                        # 使用Telegram格式发送
                        self._send_telegram_alert(alert_data, channel_config)
                    logger.info(f"每日摘要已发送到 {channel_name}")
                except Exception as e:
                    logger.error(f"发送每日摘要到 {channel_name} 失败: {e}")
    
    def _send_email_summary(self, alert_data: Dict, email_config: Dict):
        """
        通过邮件发送每日摘要
        
        Args:
            alert_data: 摘要数据
            email_config: 邮件配置
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['sender']
            msg['To'] = ', '.join(email_config['recipients'])
            msg['Subject'] = "交易系统每日摘要"
            
            # 准备HTML内容
            data = alert_data['data']
            
            body = f"""
            <html>
            <body>
                <h2>交易系统每日摘要</h2>
                <p><strong>生成时间:</strong> {alert_data['timestamp']}</p>
                
                <table border='1' cellpadding='10' cellspacing='0' style='border-collapse: collapse;'>
                    <tr style='background-color: #f2f2f2;'>
                        <th>指标</th>
                        <th>值</th>
                    </tr>
                    <tr>
                        <td>总交易次数</td>
                        <td>{data.get('total_trades', 0)}</td>
                    </tr>
                    <tr>
                        <td>总盈亏</td>
                        <td style='color: {'green' if data.get('total_pnl', 0) > 0 else 'red'};'>
                            {data.get('total_pnl', 0):.2f}
                        </td>
                    </tr>
                    <tr>
                        <td>胜率</td>
                        <td>{data.get('win_rate', 0):.2%}</td>
                    </tr>
                    <tr>
                        <td>平均盈亏</td>
                        <td>{data.get('average_pnl', 0):.2f}</td>
                    </tr>
                    <tr>
                        <td>总交易量</td>
                        <td>{data.get('total_volume', 0):.2f}</td>
                    </tr>
                </table>
                
                <h3>交易详情</h3>
                {self._format_trade_details_for_email(data.get('best_trade'), '最佳交易')}
                {self._format_trade_details_for_email(data.get('worst_trade'), '最差交易')}
                
                <h3>交易对分布</h3>
                {self._format_symbol_distribution(data.get('symbol_distribution', {}))}
                
                <p>---<br>此邮件由Prometheus V30交易系统自动发送</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                if 'username' in email_config and 'password' in email_config:
                    server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"发送邮件摘要失败: {e}")
            raise
    
    def _format_trade_details_for_email(self, trade: Optional[Dict], title: str) -> str:
        """
        格式化交易详情为HTML
        
        Args:
            trade: 交易数据
            title: 标题
            
        Returns:
            HTML字符串
        """
        if not trade:
            return f"<p><strong>{title}:</strong> 无数据</p>"
        
        html = f"<h4>{title}</h4><table border='1' cellpadding='5' cellspacing='0'>"
        for key, value in trade.items():
            if key not in ['data']:  # 排除复杂数据
                html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
        html += "</table><br>"
        return html
    
    def _format_symbol_distribution(self, distribution: Dict) -> str:
        """
        格式化交易对分布为HTML
        
        Args:
            distribution: 分布数据
            
        Returns:
            HTML字符串
        """
        if not distribution:
            return "<p>暂无交易对分布数据</p>"
        
        html = "<table border='1' cellpadding='5' cellspacing='0'>"
        html += "<tr style='background-color: #f2f2f2;'><th>交易对</th><th>交易次数</th></tr>"
        
        # 按交易次数排序
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        
        for symbol, count in sorted_items[:10]:  # 只显示前10个
            html += f"<tr><td>{symbol}</td><td>{count}</td></tr>"
        
        html += "</table>"
        return html
