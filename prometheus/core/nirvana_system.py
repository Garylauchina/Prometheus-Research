"""
涅槃系统 - Prometheus v4.0
在极端市场情况下快速复活大量Agent进行套利
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np

logger = logging.getLogger(__name__)


class NirvanaReason(Enum):
    """涅槃触发原因"""
    MASS_EXTINCTION = "mass_extinction"       # 大量Agent死亡
    MARKET_CRASH = "market_crash"             # 市场崩盘
    MARKET_SURGE = "market_surge"             # 市场暴涨
    EXTREME_VOLATILITY = "extreme_volatility" # 极端波动
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"  # 套利机会
    MANUAL_TRIGGER = "manual_trigger"         # 人工触发


@dataclass
class NirvanaEvent:
    """涅槃事件"""
    event_id: str
    trigger_time: datetime
    reason: NirvanaReason
    market_context: Dict
    
    # 复活参数
    target_agent_count: int
    initial_capital_per_agent: float
    gene_selection_strategy: str
    
    # 结果
    agents_revived: int = 0
    success_rate: float = 0.0
    avg_profit: float = 0.0
    
    end_time: Optional[datetime] = None
    is_active: bool = True


class NirvanaSystem:
    """
    涅槃系统 - 凤凰涅槃，浴火重生
    
    职责：
    1. 监测极端市场情况
    2. 评估是否需要触发涅槃
    3. 快速批量复活Agent
    4. 使用最优基因进行套利
    5. 统计涅槃效果
    
    设计理念：
    - 平时系统缓慢进化
    - 极端情况下快速响应
    - 利用积累的优秀基因
    - 抓住市场短暂机会
    """
    
    def __init__(self,
                 gene_pool,
                 mass_extinction_threshold: float = 0.7,
                 market_crash_threshold: float = -0.15,
                 market_surge_threshold: float = 0.20,
                 volatility_threshold: float = 0.05):
        """
        初始化涅槃系统
        
        Args:
            gene_pool: 基因库实例
            mass_extinction_threshold: 大灭绝阈值（死亡比例）
            market_crash_threshold: 市场崩盘阈值（跌幅）
            market_surge_threshold: 市场暴涨阈值（涨幅）
            volatility_threshold: 极端波动阈值
        """
        self.gene_pool = gene_pool
        
        # 触发阈值
        self.mass_extinction_threshold = mass_extinction_threshold
        self.market_crash_threshold = market_crash_threshold
        self.market_surge_threshold = market_surge_threshold
        self.volatility_threshold = volatility_threshold
        
        # 涅槃历史
        self.nirvana_events: List[NirvanaEvent] = []
        self.event_counter = 0
        
        # 冷却期（避免频繁触发）
        self.cooldown_hours = 24
        self.last_nirvana_time: Optional[datetime] = None
        
        logger.info("涅槃系统已初始化")
    
    def evaluate_nirvana_trigger(self,
                                 agent_statistics: Dict,
                                 market_data: Dict,
                                 system_metrics: Dict) -> Optional[NirvanaReason]:
        """
        评估是否应该触发涅槃
        
        Args:
            agent_statistics: Agent群体统计
            market_data: 市场数据
            system_metrics: 系统指标
            
        Returns:
            Optional[NirvanaReason]: 触发原因，None表示不触发
        """
        # 检查冷却期
        if self._is_in_cooldown():
            logger.debug("涅槃系统在冷却期")
            return None
        
        # 1. 检查大灭绝
        if self._check_mass_extinction(agent_statistics):
            logger.warning("检测到大灭绝事件！")
            return NirvanaReason.MASS_EXTINCTION
        
        # 2. 检查市场崩盘
        if self._check_market_crash(market_data):
            logger.warning("检测到市场崩盘！")
            return NirvanaReason.MARKET_CRASH
        
        # 3. 检查市场暴涨
        if self._check_market_surge(market_data):
            logger.warning("检测到市场暴涨！")
            return NirvanaReason.MARKET_SURGE
        
        # 4. 检查极端波动
        if self._check_extreme_volatility(market_data):
            logger.warning("检测到极端波动！")
            return NirvanaReason.EXTREME_VOLATILITY
        
        # 5. 检查套利机会
        if self._check_arbitrage_opportunity(market_data):
            logger.info("检测到套利机会！")
            return NirvanaReason.ARBITRAGE_OPPORTUNITY
        
        return None
    
    def _is_in_cooldown(self) -> bool:
        """检查是否在冷却期"""
        if not self.last_nirvana_time:
            return False
        
        elapsed = datetime.now() - self.last_nirvana_time
        return elapsed < timedelta(hours=self.cooldown_hours)
    
    def _check_mass_extinction(self, agent_stats: Dict) -> bool:
        """
        检查大灭绝
        
        条件：短时间内大量Agent死亡
        """
        total_agents = agent_stats.get('total_agents', 0)
        if total_agents == 0:
            return True  # 没有Agent了，肯定需要涅槃
        
        # 检查死亡比例
        recent_deaths = agent_stats.get('recent_deaths_24h', 0)
        death_ratio = recent_deaths / max(total_agents + recent_deaths, 1)
        
        return death_ratio > self.mass_extinction_threshold
    
    def _check_market_crash(self, market_data: Dict) -> bool:
        """
        检查市场崩盘
        
        条件：短时间内大幅下跌
        """
        # 检查1小时跌幅
        price_change_1h = market_data.get('price_change_1h', 0)
        if price_change_1h < self.market_crash_threshold:
            return True
        
        # 检查24小时跌幅
        price_change_24h = market_data.get('price_change_24h', 0)
        if price_change_24h < self.market_crash_threshold * 2:
            return True
        
        return False
    
    def _check_market_surge(self, market_data: Dict) -> bool:
        """
        检查市场暴涨
        
        条件：短时间内大幅上涨
        """
        # 检查1小时涨幅
        price_change_1h = market_data.get('price_change_1h', 0)
        if price_change_1h > self.market_surge_threshold:
            return True
        
        # 检查24小时涨幅
        price_change_24h = market_data.get('price_change_24h', 0)
        if price_change_24h > self.market_surge_threshold * 2:
            return True
        
        return False
    
    def _check_extreme_volatility(self, market_data: Dict) -> bool:
        """
        检查极端波动
        
        条件：短时间内剧烈波动
        """
        volatility_1h = market_data.get('volatility_1h', 0)
        return volatility_1h > self.volatility_threshold
    
    def _check_arbitrage_opportunity(self, market_data: Dict) -> bool:
        """
        检查套利机会
        
        条件：市场出现明显的价格偏差
        """
        # 这里可以实现具体的套利机会识别逻辑
        # 例如：跨交易所价差、期现价差等
        
        arbitrage_score = market_data.get('arbitrage_score', 0)
        return arbitrage_score > 0.8
    
    def trigger_nirvana(self,
                       reason: NirvanaReason,
                       market_context: Dict,
                       available_capital: float,
                       current_agent_count: int) -> NirvanaEvent:
        """
        触发涅槃
        
        Args:
            reason: 触发原因
            market_context: 市场环境
            available_capital: 可用资金
            current_agent_count: 当前Agent数量
            
        Returns:
            NirvanaEvent: 涅槃事件
        """
        self.event_counter += 1
        
        # 计算复活参数
        revival_params = self._calculate_revival_parameters(
            reason, market_context, available_capital, current_agent_count
        )
        
        # 创建涅槃事件
        event = NirvanaEvent(
            event_id=f"NIRVANA-{self.event_counter:04d}",
            trigger_time=datetime.now(),
            reason=reason,
            market_context=market_context.copy(),
            target_agent_count=revival_params['target_count'],
            initial_capital_per_agent=revival_params['capital_per_agent'],
            gene_selection_strategy=revival_params['gene_strategy']
        )
        
        self.nirvana_events.append(event)
        self.last_nirvana_time = datetime.now()
        
        logger.warning(f"🔥 涅槃触发！原因: {reason.value}")
        logger.info(f"   计划复活 {event.target_agent_count} 个Agent")
        logger.info(f"   每个Agent资金: ${event.initial_capital_per_agent:.2f}")
        logger.info(f"   基因策略: {event.gene_selection_strategy}")
        
        return event
    
    def _calculate_revival_parameters(self,
                                     reason: NirvanaReason,
                                     market_context: Dict,
                                     available_capital: float,
                                     current_agent_count: int) -> Dict:
        """
        计算复活参数
        
        Args:
            reason: 触发原因
            market_context: 市场环境
            available_capital: 可用资金
            current_agent_count: 当前Agent数量
            
        Returns:
            Dict: 复活参数
        """
        # 根据不同原因设置不同的复活策略
        if reason == NirvanaReason.MASS_EXTINCTION:
            # 大灭绝：大量复活，重建生态
            target_count = max(20, current_agent_count * 3)
            gene_strategy = "diverse"  # 多样化基因
            capital_multiplier = 0.8   # 正常资金
            
        elif reason == NirvanaReason.MARKET_CRASH:
            # 市场崩盘：抄底策略
            target_count = 15
            gene_strategy = "contrarian"  # 逆向基因
            capital_multiplier = 1.2      # 增加资金（抄底）
            
        elif reason == NirvanaReason.MARKET_SURGE:
            # 市场暴涨：追涨策略
            target_count = 12
            gene_strategy = "momentum"  # 动量基因
            capital_multiplier = 1.0
            
        elif reason == NirvanaReason.EXTREME_VOLATILITY:
            # 极端波动：短线策略
            target_count = 10
            gene_strategy = "scalping"  # 短线基因
            capital_multiplier = 0.9
            
        elif reason == NirvanaReason.ARBITRAGE_OPPORTUNITY:
            # 套利机会：精准套利
            target_count = 8
            gene_strategy = "arbitrage"  # 套利基因
            capital_multiplier = 1.5      # 更多资金
            
        else:  # MANUAL_TRIGGER
            target_count = 10
            gene_strategy = "best"
            capital_multiplier = 1.0
        
        # 计算每个Agent资金
        capital_per_agent = (available_capital * 0.7) / target_count * capital_multiplier
        
        return {
            'target_count': target_count,
            'capital_per_agent': capital_per_agent,
            'gene_strategy': gene_strategy
        }
    
    def generate_revival_agents(self, event: NirvanaEvent) -> List[Dict]:
        """
        生成复活Agent的配置
        
        Args:
            event: 涅槃事件
            
        Returns:
            List[Dict]: Agent配置列表
        """
        revival_configs = []
        market_regime = event.market_context.get('regime', 'unknown')
        
        for i in range(event.target_agent_count):
            # 从基因库选择基因
            gene, personality = self._select_gene_for_revival(
                event.gene_selection_strategy,
                market_regime
            )
            
            # 创建Agent配置
            config = {
                'agent_id': f"Nirvana-{event.event_id}-{i+1:03d}",
                'initial_capital': event.initial_capital_per_agent,
                'gene': gene,
                'personality': personality,
                'nirvana_event_id': event.event_id,
                'revival_time': datetime.now(),
                'special_mission': self._get_special_mission(event.reason)
            }
            
            revival_configs.append(config)
        
        event.agents_revived = len(revival_configs)
        
        logger.info(f"✨ 生成了 {len(revival_configs)} 个涅槃Agent配置")
        
        return revival_configs
    
    def _select_gene_for_revival(self, strategy: str, market_regime: str) -> Tuple[Dict, Dict]:
        """
        为复活选择基因
        
        Args:
            strategy: 基因选择策略
            market_regime: 市场状态
            
        Returns:
            Tuple[Dict, Dict]: (基因, 性格)
        """
        if strategy == "diverse":
            # 多样化：随机选择不同的基因
            best_genes = self.gene_pool.get_best_genes(market_regime, count=20)
            if best_genes:
                gene_record = np.random.choice(best_genes)
                return gene_record.gene, gene_record.personality
                
        elif strategy == "contrarian":
            # 逆向：选择均值回归倾向高的基因
            best_genes = self.gene_pool.get_best_genes(market_regime, count=50)
            contrarian_genes = [
                g for g in best_genes
                if g.personality.get('mean_reversion', 0) > 0.6
            ]
            if contrarian_genes:
                gene_record = np.random.choice(contrarian_genes)
                return gene_record.gene, gene_record.personality
                
        elif strategy == "momentum":
            # 动量：选择趋势跟随倾向高的基因
            best_genes = self.gene_pool.get_best_genes(market_regime, count=50)
            momentum_genes = [
                g for g in best_genes
                if g.personality.get('trend_following', 0) > 0.6
            ]
            if momentum_genes:
                gene_record = np.random.choice(momentum_genes)
                return gene_record.gene, gene_record.personality
        
        elif strategy == "best":
            # 最优：直接选择最好的基因
            best_genes = self.gene_pool.get_best_genes(market_regime, count=5)
            if best_genes:
                gene_record = best_genes[0]
                return gene_record.gene, gene_record.personality
        
        # 如果基因库为空或没找到，返回None（调用方需要生成随机基因）
        return None, None
    
    def _get_special_mission(self, reason: NirvanaReason) -> str:
        """获取特殊任务描述"""
        missions = {
            NirvanaReason.MASS_EXTINCTION: "重建生态系统",
            NirvanaReason.MARKET_CRASH: "抄底反弹",
            NirvanaReason.MARKET_SURGE: "追涨获利",
            NirvanaReason.EXTREME_VOLATILITY: "短线套利",
            NirvanaReason.ARBITRAGE_OPPORTUNITY: "套利获利"
        }
        return missions.get(reason, "正常交易")
    
    def update_nirvana_results(self,
                              event_id: str,
                              success_count: int,
                              failure_count: int,
                              avg_profit: float):
        """
        更新涅槃结果
        
        Args:
            event_id: 事件ID
            success_count: 成功数量
            failure_count: 失败数量
            avg_profit: 平均盈利
        """
        for event in self.nirvana_events:
            if event.event_id == event_id and event.is_active:
                event.success_rate = success_count / max(event.agents_revived, 1)
                event.avg_profit = avg_profit
                event.end_time = datetime.now()
                event.is_active = False
                
                logger.info(f"涅槃事件 {event_id} 结束")
                logger.info(f"  成功率: {event.success_rate:.1%}")
                logger.info(f"  平均盈利: {avg_profit:.2%}")
                
                break
    
    def get_active_nirvana_event(self) -> Optional[NirvanaEvent]:
        """获取当前活跃的涅槃事件"""
        for event in reversed(self.nirvana_events):
            if event.is_active:
                return event
        return None
    
    def get_statistics(self) -> Dict:
        """
        获取涅槃系统统计
        
        Returns:
            Dict: 统计信息
        """
        if not self.nirvana_events:
            return {
                'total_events': 0,
                'total_agents_revived': 0,
                'avg_success_rate': 0
            }
        
        total_revived = sum(e.agents_revived for e in self.nirvana_events)
        completed_events = [e for e in self.nirvana_events if not e.is_active]
        
        avg_success_rate = 0
        if completed_events:
            avg_success_rate = np.mean([e.success_rate for e in completed_events])
        
        # 按原因分类统计
        reason_counts = {}
        for event in self.nirvana_events:
            reason = event.reason.value
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return {
            'total_events': len(self.nirvana_events),
            'active_events': sum(1 for e in self.nirvana_events if e.is_active),
            'total_agents_revived': total_revived,
            'avg_success_rate': avg_success_rate,
            'reason_distribution': reason_counts,
            'last_nirvana_time': self.last_nirvana_time
        }

