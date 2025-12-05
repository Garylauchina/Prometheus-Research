"""
Instinct System - Agent的本能系统
=================================

本能是Agent的核心驱动力，全部可进化：
1. 死亡恐惧（fear_of_death）：求生意志，范围0-2
   - 高恐惧(>1.5): 保守，早早平仓，难死但难大赚
   - 中恐惧(0.5-1.5): 平衡，适度冒险
   - 低恐惧(<0.5): 激进，敢于持仓，易死但易暴富

2. 其他本能：繁殖冲动、损失厌恶、风险偏好、好奇心、时间偏好

设计哲学（v5.2实验性改进）：
- **所有本能都可遗传、可变异、可进化**
- 不同的fear_of_death导致不同的生存策略
- 进化压力决定最优的恐惧水平：
  * 温和市场：低恐惧者繁荣（冒险有回报）
  * 残酷市场：高恐惧者生存（保守是王道）
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import random
import numpy as np


@dataclass
class Instinct:
    """
    Agent的本能系统
    
    所有本能都可进化（v5.2实验性改进）：
    1. fear_of_death: 死亡恐惧/求生意志（0-2，集中在1.0附近）
       - 高恐惧(1.5-2.0): 保守派，容易平仓
       - 中恐惧(0.5-1.5): 平衡派
       - 低恐惧(0-0.5): 激进派，敢于冒险
    
    2. 其他本能（0-1）：
       - reproductive_drive: 繁殖欲望
       - loss_aversion: 损失厌恶
       - risk_appetite: 风险偏好
       - curiosity: 好奇心
       - time_preference: 时间偏好（0=短期，1=长期）
    """
    
    # ==================== 核心本能（全部可进化）====================
    fear_of_death: float = 1.0       # 死亡恐惧：范围0-2，可遗传，可变异
    reproductive_drive: float = 0.5  # 繁殖欲望：渴望留下后代
    loss_aversion: float = 0.5       # 损失厌恶：对亏损的敏感度
    risk_appetite: float = 0.5       # 风险偏好：追求高收益的倾向
    curiosity: float = 0.5           # 好奇心：探索新策略的倾向
    time_preference: float = 0.5     # 时间偏好：0=短期主义，1=长期主义
    
    # ==================== 元数据 ====================
    generation: int = 0              # 第几代
    parent_instincts: Tuple = None   # 父母的本能值（用于追溯）
    
    def __post_init__(self):
        """确保所有本能在合理范围内（v5.2: fear_of_death不再固定）"""
        # v5.2实验性改进：fear_of_death可变，范围0-2
        self.fear_of_death = np.clip(self.fear_of_death, 0, 2)
        
        # 其他本能在[0, 1]范围内
        self.reproductive_drive = np.clip(self.reproductive_drive, 0, 1)
        self.loss_aversion = np.clip(self.loss_aversion, 0, 1)
        self.risk_appetite = np.clip(self.risk_appetite, 0, 1)
        self.curiosity = np.clip(self.curiosity, 0, 1)
        self.time_preference = np.clip(self.time_preference, 0, 1)
    
    # ==================== 创世方法 ====================
    
    @classmethod
    def create_genesis(cls) -> 'Instinct':
        """
        创建创世Agent的本能
        
        特点（v5.2实验性改进）：
        - 所有本能都随机生成，确保多样性
        - fear_of_death使用Beta(2,2)×2，范围0-2，集中在1.0附近
        - 其他本能使用Beta(2,2)，范围0-1
        """
        return cls(
            # v5.2: fear_of_death可变，范围0-2，集中在1.0附近
            fear_of_death=np.random.beta(2, 2) * 2,
            
            # 其他本能：使用Beta(2, 2)分布，集中在0.5附近但有多样性
            reproductive_drive=np.random.beta(2, 2),
            loss_aversion=np.random.beta(2, 2),
            risk_appetite=np.random.beta(2, 2),
            curiosity=np.random.beta(2, 2),
            time_preference=np.random.beta(2, 2),
            
            generation=0,
            parent_instincts=None,
        )
    
    # ==================== 遗传方法 ====================
    
    @classmethod
    def inherit_from_parents(
        cls,
        parent1: 'Instinct',
        parent2: 'Instinct',
        generation: int
    ) -> 'Instinct':
        """
        从父母继承本能
        
        规则：
        1. 基本本能（死亡恐惧）：固定1.0，不遗传
        2. 进化本能：平均遗传 + 随机强化/削弱
        
        遗传公式：
        child_value = (parent1_value + parent2_value) / 2 * random_factor
        random_factor ~ N(1.0, 0.15)，即 ±15% 的随机变化
        """
        # 计算父母所有本能的平均值（v5.2: 包括fear_of_death）
        avg_fear = (parent1.fear_of_death + parent2.fear_of_death) / 2
        avg_reproductive = (parent1.reproductive_drive + parent2.reproductive_drive) / 2
        avg_loss_aversion = (parent1.loss_aversion + parent2.loss_aversion) / 2
        avg_risk_appetite = (parent1.risk_appetite + parent2.risk_appetite) / 2
        avg_curiosity = (parent1.curiosity + parent2.curiosity) / 2
        avg_time_preference = (parent1.time_preference + parent2.time_preference) / 2
        
        # 应用随机强化/削弱（正态分布，均值1.0，标准差0.15）
        def apply_variation(value: float, max_value: float = 1.0) -> float:
            """应用 ±15% 的随机变化"""
            factor = np.random.normal(1.0, 0.15)
            factor = np.clip(factor, 0.7, 1.3)  # 限制在 [0.7, 1.3]
            return np.clip(value * factor, 0, max_value)
        
        # 创建子代本能（v5.2: fear_of_death也遗传）
        child = cls(
            fear_of_death=apply_variation(avg_fear, max_value=2.0),  # 范围0-2
            
            reproductive_drive=apply_variation(avg_reproductive),
            loss_aversion=apply_variation(avg_loss_aversion),
            risk_appetite=apply_variation(avg_risk_appetite),
            curiosity=apply_variation(avg_curiosity),
            time_preference=apply_variation(avg_time_preference),
            
            generation=generation,
            parent_instincts=(
                parent1.get_evolved_instincts(),
                parent2.get_evolved_instincts()
            ),
        )
        
        return child
    
    # ==================== 查询方法 ====================
    
    def get_evolved_instincts(self) -> Dict[str, float]:
        """获取所有进化本能（二级本能）的值"""
        return {
            'reproductive_drive': self.reproductive_drive,
            'loss_aversion': self.loss_aversion,
            'risk_appetite': self.risk_appetite,
            'curiosity': self.curiosity,
            'time_preference': self.time_preference,
        }
    
    def get_all_instincts(self) -> Dict[str, float]:
        """获取所有本能（包括基本本能和进化本能）"""
        return {
            'fear_of_death': self.fear_of_death,
            **self.get_evolved_instincts()
        }
    
    def calculate_death_fear_level(self, capital_ratio: float, consecutive_losses: int = 0) -> float:
        """
        计算当前的死亡恐惧水平
        
        Args:
            capital_ratio: 当前资金/初始资金
            consecutive_losses: 连续亏损次数
        
        Returns:
            float: 死亡恐惧水平 (0-1)，越高越恐惧
        
        计算逻辑：
        - capital_ratio < 0.3: 极度恐惧
        - capital_ratio < 0.5: 高度恐惧
        - consecutive_losses: 加剧恐惧
        """
        # 基础恐惧（基于资金比率）
        if capital_ratio >= 0.8:
            base_fear = 0.0
        elif capital_ratio >= 0.5:
            base_fear = (0.8 - capital_ratio) / 0.3  # 0 -> 1
        elif capital_ratio >= 0.3:
            base_fear = 1.0 + (0.5 - capital_ratio) / 0.2  # 1 -> 2
        else:
            base_fear = 2.0 + (0.3 - capital_ratio) / 0.3  # 2 -> 3
        
        # 连续亏损加成（非线性）
        loss_fear = min(consecutive_losses ** 1.5 * 0.1, 1.0)
        
        # 综合恐惧（本能强度 × (基础恐惧 + 亏损恐惧)）
        total_fear = self.fear_of_death * (base_fear + loss_fear)
        
        return min(total_fear, 3.0)  # 最高3.0（极度恐惧）
    
    def should_prioritize_survival(self, capital_ratio: float) -> bool:
        """
        判断是否应该优先考虑生存
        
        Args:
            capital_ratio: 当前资金/初始资金
        
        Returns:
            bool: True表示应该优先生存（保守策略）
        """
        fear_level = self.calculate_death_fear_level(capital_ratio)
        return fear_level > 1.0  # 恐惧超过1.0时优先生存
    
    def apply_instinct_pressure(
        self,
        base_action_score: Dict[str, float],
        context: Dict
    ) -> Dict[str, float]:
        """
        将本能压力应用到行动评分上
        
        Args:
            base_action_score: 基础行动评分 {'buy': 0.6, 'sell': 0.3, 'hold': 0.1}
            context: 决策上下文
        
        Returns:
            Dict[str, float]: 施加本能压力后的行动评分
        
        本能影响规则：
        1. 死亡恐惧：资金低时强烈倾向于'close'/'hold'
        2. 损失厌恶：亏损时倾向于止损
        3. 风险偏好：影响仓位大小倾向
        4. 好奇心：影响新策略尝试倾向
        5. 时间偏好：影响持仓时间倾向
        """
        capital_ratio = context.get('capital_ratio', 1.0)
        recent_pnl = context.get('recent_pnl', 0)
        consecutive_losses = context.get('consecutive_losses', 0)
        
        adjusted_scores = base_action_score.copy()
        
        # 1. 死亡恐惧的影响
        fear_level = self.calculate_death_fear_level(capital_ratio, consecutive_losses)
        if fear_level > 1.0:
            # 濒死时强烈倾向于平仓/持有
            fear_factor = min(fear_level / 3.0, 1.0)
            adjusted_scores['close'] = adjusted_scores.get('close', 0) + fear_factor * 0.5
            adjusted_scores['hold'] = adjusted_scores.get('hold', 0) + fear_factor * 0.3
            adjusted_scores['buy'] = adjusted_scores.get('buy', 0) * (1 - fear_factor * 0.7)
            adjusted_scores['sell'] = adjusted_scores.get('sell', 0) * (1 - fear_factor * 0.7)
        
        # 2. 损失厌恶的影响
        if recent_pnl < 0:
            # 亏损时，损失厌恶高的Agent倾向于尽快止损
            loss_aversion_impact = self.loss_aversion * abs(recent_pnl) * 2
            adjusted_scores['close'] = adjusted_scores.get('close', 0) + loss_aversion_impact
            adjusted_scores['sell'] = adjusted_scores.get('sell', 0) + loss_aversion_impact * 0.5
        
        # 3. 风险偏好的影响
        if self.risk_appetite > 0.7:
            # 高风险偏好：更倾向于开仓
            adjusted_scores['buy'] = adjusted_scores.get('buy', 0) * 1.2
            adjusted_scores['sell'] = adjusted_scores.get('sell', 0) * 1.2
        elif self.risk_appetite < 0.3:
            # 低风险偏好：更倾向于观望
            adjusted_scores['hold'] = adjusted_scores.get('hold', 0) * 1.3
            adjusted_scores['close'] = adjusted_scores.get('close', 0) * 1.2
        
        # 归一化（确保总和为1）
        total = sum(adjusted_scores.values())
        if total > 0:
            adjusted_scores = {k: v / total for k, v in adjusted_scores.items()}
        
        return adjusted_scores
    
    # ==================== 展示方法 ====================
    
    def get_instinct_summary(self) -> str:
        """获取本能总结（用于日志）"""
        summary = [
            f"一级本能: 死亡恐惧={self.fear_of_death:.2f} (固定)",
            f"二级本能: 繁殖={self.reproductive_drive:.2f}, "
            f"损厌={self.loss_aversion:.2f}, "
            f"风偏={self.risk_appetite:.2f}, "
            f"好奇={self.curiosity:.2f}, "
            f"时偏={self.time_preference:.2f}",
        ]
        return " | ".join(summary)
    
    def describe_personality(self) -> str:
        """用自然语言描述本能形成的性格（v5.2: 包括fear_of_death）"""
        descriptions = []
        
        # v5.2实验：死亡恐惧（范围0-2）
        if self.fear_of_death > 1.5:
            descriptions.append("极度恐惧死亡")
        elif self.fear_of_death < 0.5:
            descriptions.append("无畏者")
        
        # 繁殖欲望
        if self.reproductive_drive > 0.7:
            descriptions.append("强烈的繁衍欲望")
        elif self.reproductive_drive < 0.3:
            descriptions.append("淡泊的繁衍欲望")
        
        # 损失厌恶
        if self.loss_aversion > 0.7:
            descriptions.append("极度厌恶损失")
        elif self.loss_aversion < 0.3:
            descriptions.append("对损失麻木")
        
        # 风险偏好
        if self.risk_appetite > 0.7:
            descriptions.append("冒险家")
        elif self.risk_appetite < 0.3:
            descriptions.append("保守派")
        
        # 好奇心
        if self.curiosity > 0.7:
            descriptions.append("极度好奇")
        elif self.curiosity < 0.3:
            descriptions.append("墨守成规")
        
        # 时间偏好
        if self.time_preference > 0.7:
            descriptions.append("长期主义者")
        elif self.time_preference < 0.3:
            descriptions.append("短期主义者")
        
        if not descriptions:
            return "平衡型性格"
        
        return "、".join(descriptions)
    
    def describe_instinct_values(self) -> str:
        """v5.2：显示本能的具体数值（用于调试）"""
        return (
            f"恐惧{self.fear_of_death:.2f} | "  # v5.2实验：fear_of_death现在可变
            f"繁殖{self.reproductive_drive:.2f} | "
            f"厌损{self.loss_aversion:.2f} | "
            f"风险{self.risk_appetite:.2f} | "
            f"好奇{self.curiosity:.2f} | "
            f"时间{self.time_preference:.2f}"
        )
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        return {
            'fear_of_death': self.fear_of_death,
            'reproductive_drive': self.reproductive_drive,
            'loss_aversion': self.loss_aversion,
            'risk_appetite': self.risk_appetite,
            'curiosity': self.curiosity,
            'time_preference': self.time_preference,
            'generation': self.generation,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Instinct':
        """从字典创建（用于反序列化）"""
        return cls(
            fear_of_death=data.get('fear_of_death', 1.0),
            reproductive_drive=data.get('reproductive_drive', 0.5),
            loss_aversion=data.get('loss_aversion', 0.5),
            risk_appetite=data.get('risk_appetite', 0.5),
            curiosity=data.get('curiosity', 0.5),
            time_preference=data.get('time_preference', 0.5),
            generation=data.get('generation', 0),
        )


# ==================== 工具函数 ====================

def calculate_instinct_diversity(instincts: list['Instinct']) -> float:
    """
    计算一组本能的多样性
    
    Args:
        instincts: Instinct对象列表
    
    Returns:
        float: 多样性分数 (0-1)，越高越多样
    """
    if len(instincts) < 2:
        return 0.0
    
    # 提取所有进化本能的值
    evolved_instinct_names = [
        'reproductive_drive', 'loss_aversion', 'risk_appetite',
        'curiosity', 'time_preference'
    ]
    
    diversities = []
    for name in evolved_instinct_names:
        values = [getattr(inst, name) for inst in instincts]
        diversity = np.var(values)  # 方差
        diversities.append(diversity)
    
    # 平均多样性
    avg_diversity = np.mean(diversities)
    
    # 归一化到 [0, 1]（方差最大为0.25，即0和1的方差）
    normalized_diversity = min(avg_diversity / 0.25, 1.0)
    
    return normalized_diversity


def get_dominant_instinct(instinct: Instinct) -> Tuple[str, float]:
    """
    获取Agent的主导本能
    
    Args:
        instinct: Instinct对象
    
    Returns:
        Tuple[str, float]: (主导本能名称, 值)
    """
    evolved = instinct.get_evolved_instincts()
    dominant_name = max(evolved, key=evolved.get)
    dominant_value = evolved[dominant_name]
    
    return (dominant_name, dominant_value)


# ==================== 本能名称映射（中英文）====================

INSTINCT_NAME_MAP = {
    'fear_of_death': '死亡恐惧',
    'reproductive_drive': '繁殖欲望',
    'loss_aversion': '损失厌恶',
    'risk_appetite': '风险偏好',
    'curiosity': '好奇心',
    'time_preference': '时间偏好',
}

def get_instinct_chinese_name(instinct_name: str) -> str:
    """获取本能的中文名称"""
    return INSTINCT_NAME_MAP.get(instinct_name, instinct_name)

