"""
Environmental Pressure System - 环境压力系统

自适应进化的核心机制，根据市场、种群和资金状况动态调整繁殖和死亡策略。

设计理念：
- 繁荣期：鼓励繁殖，宽松淘汰
- 危机期：抑制繁殖，严格淘汰
- 平衡期：正常运作

Author: Prometheus Evolution Team
Version: 2.0
Date: 2025-12-01
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)


class EnvironmentalPressure:
    """
    环境压力系统
    
    压力计算公式:
    pressure = 市场因素(40%) + 种群因素(30%) + 资金池因素(30%)
    
    压力分级:
    - 0.0-0.3: 繁荣期（低压）- 鼓励扩张
    - 0.3-0.7: 平衡期（中压）- 正常运作
    - 0.7-1.0: 危机期（高压）- 优胜劣汰
    """
    
    # 压力阈值
    PROSPERITY_THRESHOLD = 0.3
    CRISIS_THRESHOLD = 0.7
    
    # 平滑系数
    SMOOTHING_OLD = 0.7
    SMOOTHING_NEW = 0.3
    
    def __init__(self, initial_pressure: float = 0.5):
        """
        初始化环境压力系统
        
        Args:
            initial_pressure: 初始压力值（默认0.5，中等压力）
        """
        self.pressure = initial_pressure
        self.history = []
        
        logger.info(f"环境压力系统初始化: 初始压力{initial_pressure:.2%}")
    
    def update(self, 
               market_features: Dict[str, float], 
               agents: List[Any], 
               capital_pool_status: Dict[str, float]) -> float:
        """
        动态更新压力值
        
        Args:
            market_features: 市场特征字典
            agents: Agent列表
            capital_pool_status: 资金池状态
            
        Returns:
            float: 当前压力值（0.0-1.0）
        """
        # 1. 计算市场因素（40%权重）
        market_factor = self._calculate_market_factor(market_features)
        
        # 2. 计算种群因素（30%权重）
        population_factor = self._calculate_population_factor(agents)
        
        # 3. 计算资金池因素（30%权重）
        capital_factor = self._calculate_capital_factor(capital_pool_status)
        
        # 4. 综合计算
        new_pressure = market_factor + population_factor + capital_factor
        
        # 5. 平滑处理（避免剧烈波动）
        self.pressure = self.pressure * self.SMOOTHING_OLD + new_pressure * self.SMOOTHING_NEW
        
        # 6. 限制在0-1范围
        self.pressure = max(0.0, min(1.0, self.pressure))
        
        # 7. 记录历史
        self.history.append(self.pressure)
        if len(self.history) > 20:
            self.history = self.history[-20:]
        
        logger.debug(f"压力更新: 市场{market_factor:.2%} + 种群{population_factor:.2%} + "
                    f"资金{capital_factor:.2%} = {self.pressure:.2%}")
        
        return self.pressure
    
    def _calculate_market_factor(self, market_features: Dict[str, float]) -> float:
        """
        计算市场压力因素（40%权重）
        
        考虑因素:
        - 波动率：高波动增加压力
        - 恐慌指标：恐慌增加压力
        """
        market_volatility = (
            market_features.get('high_vol', 0) + 
            market_features.get('extreme_high_vol', 0) * 0.5
        )
        market_fear = (
            market_features.get('fear', 0) + 
            market_features.get('extreme_fear', 0) * 0.5
        )
        
        market_factor = (market_volatility * 0.6 + market_fear * 0.4) * 0.4
        return market_factor
    
    def _calculate_population_factor(self, agents: List[Any]) -> float:
        """
        计算种群压力因素（30%权重）
        
        考虑因素:
        - 平均ROI：越低压力越大
        - 存活率：越低压力越大
        """
        alive_agents = [a for a in agents if a.is_alive]
        
        if not alive_agents:
            return 0.3  # 无存活Agent，中等压力
        
        # ROI因子
        avg_roi = np.mean([a.roi for a in alive_agents])
        # 将ROI转换为压力（ROI越低压力越大）
        # ROI范围限制在[-1, 1]，然后反转
        roi_factor = (1 - min(max(avg_roi, -1), 1)) * 0.6
        
        # 存活率因子
        survival_rate = len(alive_agents) / len(agents)
        survival_factor = (1 - survival_rate) * 0.4
        
        population_factor = (roi_factor + survival_factor) * 0.3
        return population_factor
    
    def _calculate_capital_factor(self, capital_pool_status: Dict[str, float]) -> float:
        """
        计算资金池压力因素（30%权重）
        
        设计：U型曲线
        - 利用率过高（>90%）：资金紧张，增加压力
        - 利用率过低（<30%）：资金闲置，增加压力
        - 利用率适中（30-90%）：最优状态，无压力
        """
        utilization = capital_pool_status.get('utilization', 0.5)
        
        if utilization > 0.9:
            # 过度利用：压力线性增加
            capital_factor = (utilization - 0.5) * 0.3
        elif utilization < 0.3:
            # 利用不足：压力线性增加
            capital_factor = (0.5 - utilization) * 0.3
        else:
            # 正常范围：无压力
            capital_factor = 0
        
        return capital_factor
    
    def get_phase(self) -> Tuple[str, str]:
        """
        获取当前压力阶段
        
        Returns:
            tuple: (阶段代码, 阶段名称)
        """
        if self.pressure < self.PROSPERITY_THRESHOLD:
            return "prosperity", "🌟 繁荣期"
        elif self.pressure < self.CRISIS_THRESHOLD:
            return "normal", "⚖️ 平衡期"
        else:
            return "crisis", "🔥 危机期"
    
    def adjust_reproduction_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据压力调整繁殖配置
        
        Args:
            config: 原始繁殖配置
            
        Returns:
            dict: 调整后的配置
        """
        adjusted = config.copy()
        
        if self.pressure < self.PROSPERITY_THRESHOLD:
            # 繁荣期 - 鼓励繁殖
            adjusted['min_roi'] *= 0.7          # ROI要求降低30%
            adjusted['min_trades'] = max(1, adjusted.get('min_trades', 2) - 1)
            adjusted['pool_subsidy_ratio'] = adjusted.get('pool_subsidy_ratio', 0.30) * 1.5
            logger.info("繁荣期调整: 降低繁殖门槛，增加资助")
            
        elif self.pressure > self.CRISIS_THRESHOLD:
            # 危机期 - 抑制繁殖
            adjusted['min_roi'] *= 1.3          # ROI要求提高30%
            adjusted['min_trades'] = adjusted.get('min_trades', 2) + 1
            adjusted['pool_subsidy_ratio'] = adjusted.get('pool_subsidy_ratio', 0.30) * 0.5
            logger.info("危机期调整: 提高繁殖门槛，减少资助")
        
        return adjusted
    
    def adjust_death_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据压力调整死亡配置
        
        Args:
            config: 原始死亡配置
            
        Returns:
            dict: 调整后的配置
        """
        adjusted = config.copy()
        
        if self.pressure < self.PROSPERITY_THRESHOLD:
            # 繁荣期 - 宽松淘汰
            adjusted['death_roi_threshold'] *= 1.2  # -35% → -42%
            adjusted['parent_protection_period'] = adjusted.get('parent_protection_period', 3) + 2
            adjusted['elite_roi_threshold'] *= 0.8   # 20% → 16%
            logger.info("繁荣期调整: 放宽死亡标准，增加保护")
            
        elif self.pressure > self.CRISIS_THRESHOLD:
            # 危机期 - 严格淘汰
            adjusted['death_roi_threshold'] *= 0.8  # -35% → -28%
            adjusted['parent_protection_period'] = max(1, adjusted.get('parent_protection_period', 3) - 1)
            adjusted['elite_roi_threshold'] *= 1.2  # 20% → 24%
            adjusted['crisis_mode'] = True
            logger.info("危机期调整: 严格死亡标准，减少保护")
        
        return adjusted
    
    def get_pressure_breakdown(self) -> Dict[str, float]:
        """
        获取压力来源分解（用于调试）
        
        Returns:
            dict: 各因素的压力贡献
        """
        # 这需要保存上次计算的中间值
        # 简化版本，返回当前总压力
        return {
            'total_pressure': self.pressure,
            'phase': self.get_phase()[1],
            'avg_pressure_20cycles': np.mean(self.history) if self.history else self.pressure
        }
    
    def reset(self, initial_pressure: float = 0.5):
        """
        重置压力系统
        
        Args:
            initial_pressure: 重置后的初始压力
        """
        self.pressure = initial_pressure
        self.history = []
        logger.info(f"环境压力系统已重置: {initial_pressure:.2%}")
    
    def __repr__(self) -> str:
        phase_code, phase_name = self.get_phase()
        return f"EnvironmentalPressure({self.pressure:.2%}, {phase_name})"


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    pressure = EnvironmentalPressure()
    print("初始状态:", pressure)
    
    # 模拟不同场景
    # 场景1：平静市场
    market1 = {'high_vol': 0.2, 'extreme_high_vol': 0.0, 'fear': 0.1, 'extreme_fear': 0.0}
    
    class MockAgent:
        def __init__(self, roi, is_alive=True):
            self.roi = roi
            self.is_alive = is_alive
    
    agents1 = [MockAgent(0.08) for _ in range(15)]
    pool1 = {'utilization': 0.65}
    
    p1 = pressure.update(market1, agents1, pool1)
    print(f"\n场景1（平静市场）: 压力={p1:.2%}, {pressure.get_phase()[1]}")
    
    # 场景2：危机市场
    market2 = {'high_vol': 0.7, 'extreme_high_vol': 0.5, 'fear': 0.6, 'extreme_fear': 0.8}
    agents2 = [MockAgent(-0.15, i < 8) for i in range(15)]  # 只有8个存活
    pool2 = {'utilization': 0.95}
    
    p2 = pressure.update(market2, agents2, pool2)
    print(f"场景2（危机市场）: 压力={p2:.2%}, {pressure.get_phase()[1]}")
    
    # 测试配置调整
    base_config = {'min_roi': 0.05, 'min_trades': 2, 'pool_subsidy_ratio': 0.30}
    adjusted = pressure.adjust_reproduction_config(base_config)
    print(f"\n繁殖配置调整:")
    print(f"  原配置: {base_config}")
    print(f"  调整后: {adjusted}")

