#!/usr/bin/env python3
"""
系统监控
========

功能：
1. 实时日志
2. 性能监控
3. 告警机制
4. 报告生成
"""

import logging
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        初始化监控器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        self.trade_log = []
        self.pnl_log = []
        self.agent_log = []
        
        logger.info(f"✅ 监控器初始化完成 - 日志目录: {log_dir}")
    
    def log_trade(self, trade: Dict):
        """记录交易"""
        trade['timestamp'] = datetime.now().isoformat()
        self.trade_log.append(trade)
        
        # 每100笔保存一次
        if len(self.trade_log) % 100 == 0:
            self.save_trade_log()
    
    def log_pnl(self, pnl: Dict):
        """记录盈亏"""
        pnl['timestamp'] = datetime.now().isoformat()
        self.pnl_log.append(pnl)
        
        # 每天保存一次
        self.save_pnl_log()
    
    def log_agent_status(self, agents: List):
        """记录Agent状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'total_count': len(agents),
            'alive_count': sum(1 for a in agents if a.current_capital > 0),
            'total_capital': sum(a.current_capital for a in agents),
            'avg_capital': sum(a.current_capital for a in agents) / len(agents) if agents else 0,
        }
        self.agent_log.append(status)
    
    def save_trade_log(self):
        """保存交易日志"""
        filename = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.trade_log, f, indent=2, ensure_ascii=False)
    
    def save_pnl_log(self):
        """保存盈亏日志"""
        filename = self.log_dir / f"pnl_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.pnl_log, f, indent=2, ensure_ascii=False)
    
    def send_alert(self, message: str, level: str = "INFO"):
        """发送告警"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        
        logger.warning(f"🚨 告警: {message}")
        
        # TODO: 可以集成企业微信、钉钉、Telegram等
        # 目前只记录日志
    
    def generate_daily_report(self) -> Dict:
        """生成每日报告"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'total_trades': len(self.trade_log),
            'total_pnl': sum(p.get('pnl', 0) for p in self.pnl_log),
            'agent_status': self.agent_log[-1] if self.agent_log else {}
        }
        
        # 保存报告
        filename = self.log_dir / f"report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 每日报告已生成: {filename}")
        
        return report

