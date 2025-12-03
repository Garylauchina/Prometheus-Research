"""
可进化基因系统 - Prometheus v4.1

核心思想：
1. 创世时只有3个简单参数
2. 通过进化逐步增加复杂度
3. 市场自然选择有效参数
"""

import random
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class EvolvableGene:
    """
    可进化基因 - 从简单到复杂
    
    核心参数（创世）:
        - risk_appetite: 风险偏好 (0-1)
        - trend_pref: 趋势偏好 (0-1)
        - patience: 耐心程度 (0-1)
    
    可解锁参数（进化获得）:
        第2层: volatility_pref, momentum_pref, stop_loss_discipline
        第3层: bull_skill, bear_skill, position_sizing
        第4层: contrarian_pref, adaptation_rate, greed_control
        稀有层: market_timing, fear_control, profit_locking
    """
    
    # ========== 参数池定义 ==========
    CORE_PARAMS = ['risk_appetite', 'trend_pref', 'patience']
    
    PARAMETER_TIERS = {
        'tier_2': {
            'params': ['volatility_pref', 'momentum_pref', 'stop_loss_discipline'],
            'unlock_generation': 2,
            'unlock_probability': 0.05
        },
        'tier_3': {
            'params': ['bull_skill', 'bear_skill', 'position_sizing'],
            'unlock_generation': 5,
            'unlock_probability': 0.10
        },
        'tier_4': {
            'params': ['contrarian_pref', 'adaptation_rate', 'greed_control'],
            'unlock_generation': 10,
            'unlock_probability': 0.15
        },
        'rare': {
            'params': ['market_timing', 'fear_control', 'profit_locking'],
            'unlock_generation': 15,
            'unlock_probability': 0.02
        }
    }
    
    def __init__(self, 
                 active_params: Optional[Dict[str, float]] = None,
                 generation: int = 0,
                 parent_ids: Optional[List[str]] = None):
        """
        初始化基因
        
        Args:
            active_params: 激活的参数字典 {param_name: value}
            generation: 代数
            parent_ids: 父母ID列表
        """
        self.generation = generation
        self.parent_ids = parent_ids or []
        self.birth_time = datetime.now()
        
        # 激活的参数
        if active_params is None:
            # 创世基因：只有3个核心参数
            self.active_params = self._generate_core_params()
        else:
            # 清理非数值参数（防御性编程）
            self.active_params = {}
            for key, value in active_params.items():
                if isinstance(value, (int, float)):
                    self.active_params[key] = float(value)
                else:
                    logger.warning(f"基因初始化时跳过非数值参数: {key} = {value} (类型: {type(value).__name__})")
        
        # 进化历史
        self.mutation_history: List[Dict] = []
        self.unlocked_params: List[str] = []
    
    def _generate_core_params(self) -> Dict[str, float]:
        """生成核心参数（创世）"""
        return {
            param: random.betavariate(2, 2)  # 集中在0.3-0.7
            for param in self.CORE_PARAMS
        }
    
    @classmethod
    def create_genesis(cls) -> 'EvolvableGene':
        """创建创世基因（只有3个核心参数）"""
        return cls(generation=0)
    
    def mutate(self, mutation_rate: float = 0.15, mutation_strength: float = 0.15,
               environmental_hints: Optional[Dict] = None) -> 'EvolvableGene':
        """
        变异：改变参数值 + 可能解锁新参数
        
        Args:
            mutation_rate: 变异率 (0-1) - 每个参数变异的概率
            mutation_strength: 变异强度 (0-1) - 高斯变异的标准差
            environmental_hints: 环境提示（可选）- 先知提供的进化建议
        
        Returns:
            变异后的新基因
        """
        new_gene = EvolvableGene(
            active_params=self.active_params.copy(),
            generation=self.generation + 1,
            parent_ids=[id(self)]
        )
        
        # 1. 现有参数变异
        for param in list(new_gene.active_params.keys()):
            if random.random() < mutation_rate:
                old_value = new_gene.active_params[param]
                
                # 类型检查：只对数值类型进行变异
                if not isinstance(old_value, (int, float)):
                    logger.warning(f"跳过非数值参数变异: {param} (类型: {type(old_value).__name__})")
                    continue
                
                # 高斯变异（使用可配置的强度）
                mutation = random.gauss(0, mutation_strength)
                new_value = float(old_value) + mutation  # 确保类型转换
                new_value = max(0.0, min(1.0, new_value))
                
                new_gene.active_params[param] = new_value
                
                new_gene.mutation_history.append({
                    'type': 'value_change',
                    'param': param,
                    'old_value': old_value,
                    'new_value': new_value,
                    'time': datetime.now()
                })
        
        # 2. 尝试解锁新参数（自适应或随机）
        if self._should_unlock_param(new_gene):
            # 如果有环境提示，使用自适应解锁；否则随机解锁
            if environmental_hints:
                unlocked = self._unlock_adaptive_param(new_gene, environmental_hints)
            else:
                unlocked = self._unlock_random_param(new_gene)
            
            # 日志已在解锁方法中输出
        
        return new_gene
    
    def _should_unlock_param(self, gene: 'EvolvableGene') -> bool:
        """判断是否应该解锁新参数"""
        # 基于代数的解锁概率
        base_probability = min(0.25, gene.generation * 0.02)
        return random.random() < base_probability
    
    def _unlock_random_param(self, gene: 'EvolvableGene') -> Optional[str]:
        """解锁一个随机参数"""
        # 收集可解锁的参数
        available_params = []
        
        for tier_name, tier_config in self.PARAMETER_TIERS.items():
            if gene.generation >= tier_config['unlock_generation']:
                for param in tier_config['params']:
                    if param not in gene.active_params:
                        available_params.append((param, tier_config['unlock_probability']))
        
        if not available_params:
            return None
        
        # 根据概率加权选择
        params, probs = zip(*available_params)
        total_prob = sum(probs)
        normalized_probs = [p / total_prob for p in probs]
        
        selected_param = np.random.choice(params, p=normalized_probs)
        
        # 解锁参数
        gene.active_params[selected_param] = random.uniform(0.3, 0.7)
        gene.unlocked_params.append(selected_param)
        
        gene.mutation_history.append({
            'type': 'param_unlock',
            'param': selected_param,
            'value': gene.active_params[selected_param],
            'time': datetime.now()
        })
        
        return selected_param
    
    def _unlock_adaptive_param(self, gene: 'EvolvableGene', 
                               environmental_hints: Dict) -> Optional[str]:
        """
        根据环境提示自适应解锁参数（v4.2）
        
        先知提供建议，但Agent保持自主性
        
        Args:
            gene: 要解锁参数的基因
            environmental_hints: 环境提示
                {
                    'suggested_traits': ['param1', 'param2'],
                    'pressure': 0.7,
                    'regime': 'volatile'
                }
        
        Returns:
            解锁的参数名，如果没有则返回None
        """
        # 收集可解锁的参数
        available_params = []
        
        for tier_name, tier_config in self.PARAMETER_TIERS.items():
            if gene.generation >= tier_config['unlock_generation']:
                for param in tier_config['params']:
                    if param not in gene.active_params:
                        base_weight = tier_config['unlock_probability']
                        
                        # 如果是先知建议的参数，权重×3
                        suggested_traits = environmental_hints.get('suggested_traits', [])
                        if param in suggested_traits:
                            weight = base_weight * 3.0
                            logger.debug(f"🔮 先知建议 {param}，权重提升×3")
                        else:
                            weight = base_weight
                        
                        available_params.append((param, weight))
        
        if not available_params:
            return None
        
        # 根据调整后的权重随机选择
        params, weights = zip(*available_params)
        total_weight = sum(weights)
        normalized_probs = [w / total_weight for w in weights]
        
        selected_param = np.random.choice(params, p=normalized_probs)
        
        # 解锁参数
        gene.active_params[selected_param] = random.uniform(0.3, 0.7)
        gene.unlocked_params.append(selected_param)
        
        gene.mutation_history.append({
            'type': 'adaptive_unlock',
            'param': selected_param,
            'value': gene.active_params[selected_param],
            'hint_influenced': selected_param in environmental_hints.get('suggested_traits', []),
            'time': datetime.now()
        })
        
        # 记录是否受先知影响
        if selected_param in environmental_hints.get('suggested_traits', []):
            logger.info(f"🔮 依照先知建议解锁: {selected_param}")
        else:
            logger.info(f"🧬 自主探索解锁: {selected_param}")
        
        return selected_param
    
    def crossover(self, other: 'EvolvableGene', 
                  parent1_agent_id: str = None, 
                  parent2_agent_id: str = None) -> 'EvolvableGene':
        """
        交叉繁殖：从双亲继承基因
        
        Args:
            other: 另一个父母基因
            parent1_agent_id: 父方Agent ID（推荐提供）
            parent2_agent_id: 母方Agent ID（推荐提供）
        
        Returns:
            子代基因
        """
        # 使用Agent ID而非内存地址
        if parent1_agent_id and parent2_agent_id:
            parent_ids = [parent1_agent_id, parent2_agent_id]
        else:
            # 兼容旧代码：如果基因对象有agent_id属性，使用它
            parent_ids = [
                getattr(self, 'agent_id', f"unknown_{id(self)}"),
                getattr(other, 'agent_id', f"unknown_{id(other)}")
            ]
            if "unknown_" in parent_ids[0] or "unknown_" in parent_ids[1]:
                logger.warning(f"⚠️ crossover未提供parent_agent_id，使用临时标识")
        
        child_gene = EvolvableGene(
            generation=max(self.generation, other.generation) + 1,
            parent_ids=parent_ids
        )
        
        # 合并双亲的所有参数
        all_params = set(self.active_params.keys()) | set(other.active_params.keys())
        
        for param in all_params:
            in_self = param in self.active_params
            in_other = param in other.active_params
            
            if in_self and in_other:
                # 双亲都有：70%概率取平均，30%概率随机选择一方
                if random.random() < 0.7:
                    # 平均混合（产生新值，增加多样性）
                    child_gene.active_params[param] = (
                        self.active_params[param] + other.active_params[param]
                    ) / 2.0
                else:
                    # 随机选择一方
                    if random.random() < 0.5:
                        child_gene.active_params[param] = self.active_params[param]
                    else:
                        child_gene.active_params[param] = other.active_params[param]
                    
            elif in_self:
                # 只有父方有：30%概率继承
                if random.random() < 0.3:
                    child_gene.active_params[param] = self.active_params[param]
                    
            elif in_other:
                # 只有母方有：30%概率继承
                if random.random() < 0.3:
                    child_gene.active_params[param] = other.active_params[param]
        
        # 确保至少有核心参数
        for core_param in self.CORE_PARAMS:
            if core_param not in child_gene.active_params:
                if core_param in self.active_params:
                    child_gene.active_params[core_param] = self.active_params[core_param]
                elif core_param in other.active_params:
                    child_gene.active_params[core_param] = other.active_params[core_param]
                else:
                    child_gene.active_params[core_param] = 0.5
        
        return child_gene
    
    def calculate_fitness_score(self, agent_performance: Dict) -> float:
        """
        计算适应度得分（用于自然选择）
        
        Args:
            agent_performance: Agent表现数据
        
        Returns:
            适应度得分 (越高越好)
        """
        # 基于多个指标计算适应度
        total_pnl = agent_performance.get('total_pnl', 0)
        win_rate = agent_performance.get('win_rate', 0)
        trade_count = agent_performance.get('trade_count', 0)
        
        # 综合得分
        fitness = (
            total_pnl * 1.0 +           # 盈亏最重要
            win_rate * 10 +              # 胜率
            min(trade_count, 20) * 0.5  # 交易活跃度（上限20）
        )
        
        return fitness
    
    def get_param_count(self) -> int:
        """获取激活的参数数量"""
        return len(self.active_params)
    
    def get_complexity_level(self) -> str:
        """获取复杂度等级"""
        param_count = self.get_param_count()
        
        if param_count <= 3:
            return "简单"
        elif param_count <= 6:
            return "中等"
        elif param_count <= 9:
            return "复杂"
        else:
            return "高级"
    
    def get_parent_ids(self) -> List[str]:
        """
        获取父母Agent ID
        
        Returns:
            父母ID列表，例如：["Agent_05", "Agent_12"]
        """
        return self.parent_ids if self.parent_ids else []
    
    def get_genealogy_summary(self) -> Dict:
        """
        获取谱系摘要
        
        Returns:
            谱系信息字典
        """
        return {
            'generation': self.generation,
            'parents': self.get_parent_ids(),
            'birth_time': self.birth_time.isoformat() if self.birth_time else None,
            'param_count': len(self.active_params),
            'mutation_count': len(self.mutation_history),
            'unlocked_params': self.unlocked_params.copy()
        }
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'active_params': self.active_params.copy(),
            'generation': self.generation,
            'parent_ids': self.parent_ids.copy(),
            'birth_time': self.birth_time.isoformat(),
            'unlocked_params': self.unlocked_params.copy(),
            'mutation_history': self.mutation_history.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvolvableGene':
        """从字典反序列化"""
        gene = cls(
            active_params=data['active_params'],
            generation=data['generation'],
            parent_ids=data.get('parent_ids', [])
        )
        gene.unlocked_params = data.get('unlocked_params', [])
        gene.mutation_history = data.get('mutation_history', [])
        
        if 'birth_time' in data:
            gene.birth_time = datetime.fromisoformat(data['birth_time'])
        
        return gene
    
    def __repr__(self) -> str:
        params_str = ', '.join([f"{k}={v:.2f}" for k, v in list(self.active_params.items())[:3]])
        return (f"EvolvableGene(gen={self.generation}, "
                f"params={self.get_param_count()}, "
                f"complexity={self.get_complexity_level()}, "
                f"[{params_str}...])")

