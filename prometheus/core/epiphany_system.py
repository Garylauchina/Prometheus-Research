"""
顿悟系统 - Agent自我进化机制

核心思想：
1. Agent通过经验触发"顿悟"
2. 顿悟导致基因参数即时调整
3. 补充长期进化，实现快速适应
"""

import random
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EpiphanyTrigger:
    """顿悟触发器配置"""
    name: str
    condition_func: callable
    effect: Dict[str, float]  # {param: change_value}
    probability: float
    description: str
    cooldown_hours: int = 24


class EpiphanySystem:
    """
    顿悟系统 - Agent危机学习机制
    
    触发条件：
    1. near_death: 资金亏损>50%但存活
    2. consecutive_losses: 连续亏损>=5次
    3. missed_opportunity: 错过大涨>10%
    4. successful_escape: 成功逃顶>20%利润
    5. sideways_frustration: 震荡市频繁亏损
    """
    
    def __init__(self):
        self.triggers = self._init_triggers()
        self.epiphany_cooldowns: Dict[str, datetime] = {}  # {agent_id: last_epiphany_time}
        self.epiphany_history: List[Dict] = []
    
    def _init_triggers(self) -> List[EpiphanyTrigger]:
        """初始化触发器"""
        return [
            # 1. 死里逃生：大亏后变保守
            EpiphanyTrigger(
                name='near_death',
                condition_func=self._check_near_death,
                effect={'risk_appetite': -0.25, 'stop_loss_discipline': +0.20},
                probability=0.8,
                description='经历大亏后，学会风险控制',
                cooldown_hours=48
            ),
            
            # 2. 连续止损：加强纪律
            EpiphanyTrigger(
                name='consecutive_losses',
                condition_func=self._check_consecutive_losses,
                effect={'stop_loss_discipline': +0.20, 'patience': +0.15},
                probability=0.7,
                description='连续亏损后，加强交易纪律',
                cooldown_hours=24
            ),
            
            # 3. 错过大行情：学会跟随趋势
            EpiphanyTrigger(
                name='missed_opportunity',
                condition_func=self._check_missed_opportunity,
                effect={'trend_pref': +0.20, 'momentum_pref': +0.15},
                probability=0.6,
                description='错过大涨后，学会跟随趋势',
                cooldown_hours=24
            ),
            
            # 4. 成功逃顶：提升择时能力
            EpiphanyTrigger(
                name='successful_escape',
                condition_func=self._check_successful_escape,
                effect={'market_timing': +0.25, 'profit_locking': +0.20},
                probability=0.75,
                description='成功逃顶后，提升择时天赋',
                cooldown_hours=36
            ),
            
            # 5. 震荡市亏损：学会耐心
            EpiphanyTrigger(
                name='sideways_frustration',
                condition_func=self._check_sideways_frustration,
                effect={'patience': +0.25, 'risk_appetite': -0.15},
                probability=0.6,
                description='震荡市亏损后，学会耐心等待',
                cooldown_hours=24
            ),
        ]
    
    def check_and_trigger(self, agent, market_state: Dict, recent_trades: List[Dict]) -> bool:
        """
        检查并触发顿悟
        
        Args:
            agent: Agent对象
            market_state: 市场状态
            recent_trades: 最近交易记录
        
        Returns:
            是否触发了顿悟
        """
        agent_id = agent.agent_id
        
        # 检查冷却期
        if not self._check_cooldown(agent_id):
            return False
        
        # 遍历所有触发器
        for trigger in self.triggers:
            if trigger.condition_func(agent, market_state, recent_trades):
                if random.random() < trigger.probability:
                    self._apply_epiphany(agent, trigger)
                    self._set_cooldown(agent_id, trigger.cooldown_hours)
                    return True
        
        return False
    
    def _check_cooldown(self, agent_id: str) -> bool:
        """检查冷却期"""
        if agent_id not in self.epiphany_cooldowns:
            return True
        
        last_time = self.epiphany_cooldowns[agent_id]
        cooldown_end = last_time + timedelta(hours=24)
        
        return datetime.now() > cooldown_end
    
    def _set_cooldown(self, agent_id: str, hours: int):
        """设置冷却期"""
        self.epiphany_cooldowns[agent_id] = datetime.now()
    
    # ========== 触发条件检查函数 ==========
    
    def _check_near_death(self, agent, market_state, recent_trades) -> bool:
        """检查：死里逃生"""
        # 资金损失>50%，但仍存活
        current_capital = getattr(agent, 'current_capital', None)
        initial_capital = getattr(agent, 'initial_capital', None)
        
        if current_capital is None or initial_capital is None or initial_capital == 0:
            return False
        
        capital_ratio = current_capital / initial_capital
        return 0.3 < capital_ratio < 0.5
    
    def _check_consecutive_losses(self, agent, market_state, recent_trades) -> bool:
        """检查：连续亏损"""
        if not recent_trades or len(recent_trades) < 5:
            return False
        
        # 检查最近5笔交易是否都是亏损
        last_5 = recent_trades[-5:]
        losses = sum(1 for t in last_5 if (t.get('pnl') or 0) < 0)
        
        return losses >= 5
    
    def _check_missed_opportunity(self, agent, market_state, recent_trades) -> bool:
        """检查：错过大行情"""
        # 市场大涨但Agent没有持仓
        market_surge = market_state.get('price_change_pct', 0)
        
        # 检查持仓（处理None情况）
        positions = getattr(agent, 'positions', None)
        if positions is None:
            has_position = False
        elif isinstance(positions, dict):
            has_position = len(positions) > 0
        else:
            has_position = False
        
        return market_surge > 10 and not has_position
    
    def _check_successful_escape(self, agent, market_state, recent_trades) -> bool:
        """检查：成功逃顶"""
        if not recent_trades or len(recent_trades) == 0:
            return False
        
        last_trade = recent_trades[-1]
        
        # 平仓盈利>20%，且之后市场下跌
        profit_pct = last_trade.get('profit_pct') or 0
        market_change = market_state.get('price_change_pct') or 0
        
        # 安全比较
        try:
            market_crash = market_change < -5
            return profit_pct > 20 and market_crash
        except (TypeError, ValueError):
            return False
    
    def _check_sideways_frustration(self, agent, market_state, recent_trades) -> bool:
        """检查：震荡市亏损"""
        # 市场震荡（低波动）+ 最近交易胜率低
        volatility = market_state.get('volatility') or 1.0
        
        # 安全比较
        try:
            low_volatility = volatility < 0.5
        except (TypeError, ValueError):
            low_volatility = False
        
        if not recent_trades or len(recent_trades) < 5:
            return False
        
        recent_5 = recent_trades[-5:]
        wins = sum(1 for t in recent_5 if (t.get('pnl') or 0) > 0)
        win_rate = wins / len(recent_5) if len(recent_5) > 0 else 0
        
        return low_volatility and win_rate < 0.4
    
    # ========== 应用顿悟效果 ==========
    
    def _apply_epiphany(self, agent, trigger: EpiphanyTrigger):
        """
        应用顿悟效果
        
        Args:
            agent: Agent对象
            trigger: 触发器配置
        """
        logger.info(f"💡 {agent.agent_id} 顿悟触发: {trigger.description}")
        
        changes = []
        
        for param, change_value in trigger.effect.items():
            # 获取当前基因
            if not hasattr(agent, 'gene') or not hasattr(agent.gene, 'active_params'):
                logger.warning(f"{agent.agent_id} 没有可进化基因，跳过顿悟")
                return
            
            gene_params = agent.gene.active_params
            
            # 如果参数不存在，先解锁
            if param not in gene_params:
                if self._can_unlock_param(agent.gene, param):
                    gene_params[param] = 0.5  # 初始值
                    logger.info(f"   ✨ 顿悟解锁新参数: {param}")
                else:
                    continue
            
            # 应用变化
            old_value = gene_params[param]
            new_value = old_value + change_value
            new_value = max(0.0, min(1.0, new_value))  # 限制在[0,1]
            
            gene_params[param] = new_value
            
            changes.append({
                'param': param,
                'old_value': old_value,
                'new_value': new_value,
                'delta': change_value
            })
            
            logger.info(f"   {param}: {old_value:.2f} → {new_value:.2f} ({change_value:+.2f})")
        
        # 记录顿悟历史
        epiphany_event = {
            'agent_id': agent.agent_id,
            'time': datetime.now(),
            'trigger': trigger.name,
            'description': trigger.description,
            'changes': changes,
            'generation': getattr(agent.gene, 'generation', 0)
        }
        
        self.epiphany_history.append(epiphany_event)
        
        # 更新Agent的顿悟计数
        if not hasattr(agent, 'epiphany_count'):
            agent.epiphany_count = 0
        agent.epiphany_count += 1
    
    def _can_unlock_param(self, gene, param: str) -> bool:
        """检查是否可以解锁参数"""
        from prometheus.core.evolvable_gene import EvolvableGene
        
        # 检查参数是否在参数池中
        for tier_name, tier_config in EvolvableGene.PARAMETER_TIERS.items():
            if param in tier_config['params']:
                # 检查代数是否满足
                return gene.generation >= tier_config['unlock_generation']
        
        return False
    
    def get_agent_epiphany_stats(self, agent_id: str) -> Dict:
        """获取Agent的顿悟统计"""
        agent_epiphanies = [
            e for e in self.epiphany_history
            if e['agent_id'] == agent_id
        ]
        
        if not agent_epiphanies:
            return {
                'total_count': 0,
                'triggers': {},
                'params_changed': []
            }
        
        # 统计触发器类型
        trigger_counts = {}
        for e in agent_epiphanies:
            trigger = e['trigger']
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        # 统计改变的参数
        params_changed = set()
        for e in agent_epiphanies:
            for change in e['changes']:
                params_changed.add(change['param'])
        
        return {
            'total_count': len(agent_epiphanies),
            'triggers': trigger_counts,
            'params_changed': list(params_changed),
            'last_epiphany': agent_epiphanies[-1]['time'].isoformat()
        }
    
    def get_population_epiphany_stats(self) -> Dict:
        """获取种群的顿悟统计"""
        if not self.epiphany_history:
            return {
                'total_count': 0,
                'avg_per_agent': 0,
                'most_common_trigger': None
            }
        
        # 统计触发器
        trigger_counts = {}
        for e in self.epiphany_history:
            trigger = e['trigger']
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        most_common = max(trigger_counts.items(), key=lambda x: x[1])
        
        # 统计Agent数量
        unique_agents = set(e['agent_id'] for e in self.epiphany_history)
        
        return {
            'total_count': len(self.epiphany_history),
            'unique_agents': len(unique_agents),
            'avg_per_agent': len(self.epiphany_history) / len(unique_agents) if unique_agents else 0,
            'most_common_trigger': most_common[0],
            'trigger_distribution': trigger_counts
        }

