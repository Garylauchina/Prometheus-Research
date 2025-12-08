"""
进化压力调节器

动态调整竞争强度，避免"过度竞争"或"竞争不足"：
  - 多样性高 → 增加压力（加速进化）
  - 多样性低 → 减少压力（保护探索）
  - Fitness高 → 增加难度（防止过拟合）
  - Fitness低 → 降低难度（给喘息时间）

核心理念：
  - 压力是动态的，不是固定的
  - 根据系统状态自适应调整
  - 避免"进化停滞"或"过度淘汰"
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class PressureHistory:
    """
    压力历史记录
    
    属性：
      - generation: 代数
      - pressure: 压力水平
      - diversity: 多样性指数
      - avg_fitness: 平均适应度
      - competition_mode: 竞争模式
    """
    generation: int
    pressure: float
    diversity: float
    avg_fitness: float
    fitness_variance: float
    competition_mode: str
    adversary_ratio: float


class PressureController:
    """
    进化压力调节器
    
    功能：
      1. 动态调整竞争压力
      2. 选择竞争模式（放松/适中/激烈）
      3. 调整对手盘比例
      4. 记录压力历史
    
    压力等级：
      - 0.0-0.3: 放松（自由进化）
      - 0.3-0.7: 适中（正常竞争）
      - 0.7-1.0: 激烈（高压淘汰）
    """
    
    def __init__(self, initial_pressure: float = 0.50):
        """
        初始化压力调节器
        
        参数：
          - initial_pressure: 初始压力（默认0.50）
        """
        self.pressure_level = initial_pressure
        self.history: List[PressureHistory] = []
        
        logger.info(f"压力调节器初始化: initial_pressure={initial_pressure:.2f}")
    
    # ===== 核心方法 =====
    
    def adjust_pressure(
        self,
        generation: int,
        diversity_index: float,
        avg_fitness: float,
        fitness_variance: float
    ) -> Dict:
        """
        调整进化压力
        
        考虑因素：
          1. 多样性（diversity_index）
          2. 平均适应度（avg_fitness）
          3. 适应度方差（fitness_variance）
          4. 代数（generation）
        
        参数：
          - generation: 当前代数
          - diversity_index: 多样性指数（0-1）
          - avg_fitness: 平均适应度
          - fitness_variance: 适应度方差
        
        返回：
          - pressure_config: 压力配置
            {
              'pressure_level': float,
              'adversary_ratio': float,
              'competition_mode': str,
              'elimination_rate': float
            }
        """
        # 1. 基于多样性的调整
        diversity_factor = self._calculate_diversity_factor(diversity_index)
        
        # 2. 基于适应度的调整
        fitness_factor = self._calculate_fitness_factor(avg_fitness)
        
        # 3. 基于方差的调整
        variance_factor = self._calculate_variance_factor(fitness_variance)
        
        # 4. 基于代数的调整（早期宽松，后期严格）
        generation_factor = self._calculate_generation_factor(generation)
        
        # 综合计算新压力
        new_pressure = (
            self.pressure_level * 0.7 +  # 70%保留历史压力（平滑）
            0.3 * (  # 30%新调整
                diversity_factor * 0.4 +
                fitness_factor * 0.3 +
                variance_factor * 0.2 +
                generation_factor * 0.1
            )
        )
        
        # 限制范围
        new_pressure = np.clip(new_pressure, 0.1, 1.0)
        
        # 更新压力
        self.pressure_level = new_pressure
        
        # 选择竞争模式
        competition_mode = self._select_competition_mode(new_pressure)
        
        # 计算对手盘比例（压力越大，对手盘越多）
        adversary_ratio = 0.10 + 0.30 * new_pressure  # 10%-40%
        
        # 计算淘汰率（压力越大，淘汰率越高）
        elimination_rate = 0.10 + 0.20 * new_pressure  # 10%-30%
        
        # 记录历史
        history_record = PressureHistory(
            generation=generation,
            pressure=new_pressure,
            diversity=diversity_index,
            avg_fitness=avg_fitness,
            fitness_variance=fitness_variance,
            competition_mode=competition_mode,
            adversary_ratio=adversary_ratio
        )
        self.history.append(history_record)
        
        logger.info(
            f"   🎚️ 压力调节 Gen{generation}: "
            f"pressure={new_pressure:.2f} "
            f"(diversity={diversity_index:.2f}, "
            f"fitness={avg_fitness:.2f}) → "
            f"mode={competition_mode}, "
            f"adversary={adversary_ratio*100:.0f}%, "
            f"elim={elimination_rate*100:.0f}%"
        )
        
        return {
            'pressure_level': new_pressure,
            'adversary_ratio': adversary_ratio,
            'competition_mode': competition_mode,
            'elimination_rate': elimination_rate
        }
    
    # ===== 因子计算 =====
    
    def _calculate_diversity_factor(self, diversity: float) -> float:
        """
        计算多样性因子
        
        规则：
          - diversity < 0.30 → factor = 0.30（降低压力，保护探索）
          - 0.30 <= diversity < 0.70 → factor = 1.0（正常）
          - diversity >= 0.70 → factor = 1.50（增加压力，加速进化）
        """
        if diversity < 0.30:
            return 0.30
        elif diversity < 0.70:
            return 1.0
        else:
            return 1.50
    
    def _calculate_fitness_factor(self, avg_fitness: float) -> float:
        """
        计算适应度因子
        
        规则：
          - avg_fitness > 0.50 → factor = 1.30（增加难度）
          - avg_fitness < 0.10 → factor = 0.70（降低难度）
          - 其他 → factor = 1.0（正常）
        """
        if avg_fitness > 0.50:
            return 1.30
        elif avg_fitness < 0.10:
            return 0.70
        else:
            return 1.0
    
    def _calculate_variance_factor(self, variance: float) -> float:
        """
        计算方差因子
        
        规则：
          - variance < 0.10 → factor = 1.20（方差小，趋同，增加扰动）
          - 其他 → factor = 1.0（正常）
        """
        if variance < 0.10:
            return 1.20
        else:
            return 1.0
    
    def _calculate_generation_factor(self, generation: int) -> float:
        """
        计算代数因子
        
        规则：
          - generation < 10 → factor = 0.60（早期宽松）
          - generation < 50 → factor = 1.0（正常）
          - generation >= 50 → factor = 1.20（后期严格）
        """
        if generation < 10:
            return 0.60
        elif generation < 50:
            return 1.0
        else:
            return 1.20
    
    def _select_competition_mode(self, pressure: float) -> str:
        """
        选择竞争模式
        
        参数：
          - pressure: 压力水平（0-1）
        
        返回：
          - mode: 竞争模式
            - 'relaxed': 放松（自由进化，无淘汰）
            - 'moderate': 适中（小组赛）
            - 'intense': 激烈（锦标赛）
        """
        if pressure < 0.3:
            return 'relaxed'
        elif pressure < 0.7:
            return 'moderate'
        else:
            return 'intense'
    
    # ===== 查询方法 =====
    
    def get_pressure_history(self, last_n: Optional[int] = None) -> List[PressureHistory]:
        """
        获取压力历史
        
        参数：
          - last_n: 最近N条记录（如果None，返回全部）
        """
        if last_n:
            return self.history[-last_n:]
        else:
            return self.history
    
    def get_current_pressure(self) -> float:
        """获取当前压力"""
        return self.pressure_level
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.history:
            return {
                'current_pressure': self.pressure_level,
                'total_adjustments': 0,
                'avg_pressure': 0.0,
                'pressure_trend': 'stable'
            }
        
        avg_pressure = np.mean([h.pressure for h in self.history])
        
        # 压力趋势
        if len(self.history) >= 5:
            recent_avg = np.mean([h.pressure for h in self.history[-5:]])
            early_avg = np.mean([h.pressure for h in self.history[:5]])
            
            if recent_avg > early_avg * 1.1:
                trend = 'increasing'
            elif recent_avg < early_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'current_pressure': self.pressure_level,
            'total_adjustments': len(self.history),
            'avg_pressure': avg_pressure,
            'pressure_trend': trend,
            'min_pressure': min([h.pressure for h in self.history]) if self.history else 0,
            'max_pressure': max([h.pressure for h in self.history]) if self.history else 0
        }
    
    def reset(self):
        """重置压力调节器"""
        self.pressure_level = 0.50
        self.history.clear()
        logger.info("压力调节器已重置")

