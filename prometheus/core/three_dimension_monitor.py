"""
Prometheus v7.0 - 三维异常检测器⭐⭐⭐

核心功能：
  监控三个关键维度：
    1. WorldSignature（市场状态）
    2. 摩擦系数（交易环境）
    3. 非正常死亡率（Agent健康）
  
  检测逻辑：
    一维震荡 → 轻微调整（warning）
    二维震荡 → 大幅调整（danger）
    三维震荡 → 紧急逃命（critical）⭐⭐⭐

算法：Z-score（2σ原则）
内存：最近100周期
保存：每10周期到数据库
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus.core.experience_db import ExperienceDB

logger = logging.getLogger(__name__)


class ThreeDimensionMonitor:
    """
    三维异常监测器⭐⭐⭐
    
    Prophet的核心能力：
      不预测市场，只检测异常
    """
    
    def __init__(self, window_size: int = 100, save_interval: int = 10):
        """
        初始化监测器
        
        Args:
            window_size: 历史窗口大小（默认100周期）
            save_interval: 数据库保存间隔（默认每10周期）
        """
        self.window_size = window_size
        self.save_interval = save_interval
        
        # 内存历史窗口（最近N周期）
        self.history = {
            'ws_scores': [],
            'friction_indices': [],
            'death_rates': []
        }
        
        logger.info("🔍 ThreeDimensionMonitor已初始化")
        logger.info(f"   历史窗口: {window_size}周期")
        logger.info(f"   保存间隔: {save_interval}周期")
    
    def monitor_cycle(
        self,
        cycle: int,
        run_id: str,
        world_signature: Dict,
        friction_data: Dict,
        death_stats: Dict,
        prophet_decision: Dict,
        experience_db: Optional[object] = None
    ) -> Dict:
        """
        监测一个周期⭐⭐⭐
        
        每个交易周期都调用此方法
        
        Args:
            cycle: 当前周期编号
            run_id: 运行ID
            world_signature: 市场状态
            friction_data: 摩擦数据
            death_stats: 死亡统计
            prophet_decision: Prophet决策（S, E, scale）
            experience_db: 数据库（用于保存）
        
        Returns:
            {
                'ws_anomaly': bool,
                'friction_anomaly': bool,
                'death_anomaly': bool,
                'total_anomaly_dims': int,  # 0-3
                'risk_level': str,
                'details': {...}
            }
        """
        
        # ===== 1. 计算三维得分 =====
        ws_score = self._calculate_ws_score(world_signature)
        friction_index = self._calculate_friction_index(friction_data)
        death_rate = self._calculate_death_rate(death_stats)
        
        # ===== 2. 异常检测（基于内存历史）⭐⭐⭐ =====
        ws_anomaly, ws_z = self._detect_anomaly(ws_score, self.history['ws_scores'])
        friction_anomaly, friction_z = self._detect_anomaly(
            friction_index, 
            self.history['friction_indices']
        )
        death_anomaly, death_z = self._detect_anomaly(
            death_rate, 
            self.history['death_rates']
        )
        
        # ===== 3. 综合判断 =====
        total_anomaly_dims = sum([ws_anomaly, friction_anomaly, death_anomaly])
        risk_level = self._get_risk_level(total_anomaly_dims)
        
        # ===== 4. 更新内存历史 =====
        self.history['ws_scores'].append(ws_score)
        self.history['friction_indices'].append(friction_index)
        self.history['death_rates'].append(death_rate)
        
        # 保持窗口大小
        if len(self.history['ws_scores']) > self.window_size:
            self.history['ws_scores'].pop(0)
            self.history['friction_indices'].pop(0)
            self.history['death_rates'].pop(0)
        
        # ===== 5. 定期保存到数据库 =====
        if experience_db and cycle % self.save_interval == 0:
            experience_db.save_system_metrics(
                run_id=run_id,
                cycle=cycle,
                ws_score=ws_score,
                friction_index=friction_index,
                death_rate=death_rate,
                ws_anomaly=ws_anomaly,
                friction_anomaly=friction_anomaly,
                death_anomaly=death_anomaly,
                total_anomaly_dims=total_anomaly_dims,
                risk_level=risk_level,
                prophet_S=prophet_decision.get('S', 0.5),
                prophet_E=prophet_decision.get('E', 0.0),
                system_scale=prophet_decision.get('scale', 0.5)
            )
            logger.info(f"💾 系统指标已保存: cycle={cycle}, risk={risk_level}")
        
        # ===== 6. 返回结果 =====
        result = {
            'ws_anomaly': ws_anomaly,
            'friction_anomaly': friction_anomaly,
            'death_anomaly': death_anomaly,
            'total_anomaly_dims': total_anomaly_dims,
            'risk_level': risk_level,
            'details': {
                'ws_score': ws_score,
                'ws_z_score': ws_z,
                'friction_index': friction_index,
                'friction_z_score': friction_z,
                'death_rate': death_rate,
                'death_z_score': death_z,
            }
        }
        
        # 日志
        if total_anomaly_dims > 0:
            emoji = ['✅', '⚠️', '⚠️⚠️', '🚨🚨🚨'][total_anomaly_dims]
            logger.warning(f"{emoji} 异常检测: {total_anomaly_dims}维震荡 ({risk_level})")
            if ws_anomaly:
                logger.warning(f"   • WorldSig异常: {ws_score:.3f} (Z={ws_z:.2f})")
            if friction_anomaly:
                logger.warning(f"   • 摩擦异常: {friction_index:.3f} (Z={friction_z:.2f})")
            if death_anomaly:
                logger.warning(f"   • 死亡率异常: {death_rate:.2%} (Z={death_z:.2f})")
        
        return result
    
    def _calculate_ws_score(self, world_signature: Dict) -> float:
        """
        计算WorldSignature综合得分⭐
        
        Args:
            world_signature: 市场状态
        
        Returns:
            综合得分（0-1，越高越震荡）
        """
        volatility = world_signature.get('volatility_24h', 0.0)
        price_change = abs(world_signature.get('price_change_24h', 0.0))
        
        # 综合得分（波动率和价格变化的加权平均）
        score = volatility * 0.5 + price_change * 0.5
        
        return score
    
    def _calculate_friction_index(self, friction_data: Dict) -> float:
        """
        计算摩擦综合指数⭐
        
        Args:
            friction_data: 摩擦数据
        
        Returns:
            综合指数（0-1，越高越摩擦大）
        """
        slippage = friction_data.get('slippage', 0.0)
        latency_norm = friction_data.get('latency_norm', 0.0)  # 归一化的延迟
        fill_rate = friction_data.get('fill_rate', 1.0)
        
        # 综合指数
        index = (
            slippage * 0.4 +
            latency_norm * 0.3 +
            (1 - fill_rate) * 0.3
        )
        
        return index
    
    def _calculate_death_rate(self, death_stats: Dict) -> float:
        """
        计算非正常死亡率⭐
        
        Args:
            death_stats: 死亡统计
        
        Returns:
            非正常死亡率（0-1）
        """
        abnormal_deaths = death_stats.get('abnormal_deaths', 0)
        total_agents = death_stats.get('total_agents', 1)
        
        if total_agents == 0:
            return 0.0
        
        return abnormal_deaths / total_agents
    
    def _detect_anomaly(
        self, 
        current_value: float, 
        history: List[float]
    ) -> Tuple[bool, float]:
        """
        检测是否异常（Z-score方法）⭐⭐⭐
        
        Args:
            current_value: 当前值
            history: 历史数据列表
        
        Returns:
            (is_anomaly, z_score)
        """
        # 历史数据不足，无法判断
        if len(history) < 10:
            return False, 0.0
        
        # 计算均值和标准差
        mean = np.mean(history)
        std = np.std(history)
        
        # 如果标准差为0（所有值都相同），无法判断异常
        if std == 0 or std < 1e-6:
            return False, 0.0
        
        # 计算Z-score
        z_score = abs(current_value - mean) / std
        
        # 异常判断（2σ原则）
        is_anomaly = z_score > 2.0
        
        return is_anomaly, z_score
    
    def _get_risk_level(self, anomaly_dims: int) -> str:
        """
        根据异常维度数判断风险等级⭐⭐⭐
        
        Args:
            anomaly_dims: 异常维度数（0-3）
        
        Returns:
            风险等级字符串
        """
        levels = ['safe', 'warning', 'danger', 'critical']
        return levels[min(anomaly_dims, 3)]


if __name__ == "__main__":
    """
    简单测试
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # 配置logging
    logging.basicConfig(level=logging.INFO)
    
    monitor = ThreeDimensionMonitor(window_size=100, save_interval=10)
    
    # 模拟100个周期的正常数据
    print("\n" + "="*60)
    print("🧪 测试：正常市场（100周期）")
    print("="*60)
    
    for cycle in range(1, 101):
        result = monitor.monitor_cycle(
            cycle=cycle,
            run_id="test_001",
            world_signature={'volatility_24h': 0.03, 'price_change_24h': 0.02},
            friction_data={'slippage': 0.001, 'latency_norm': 0.02, 'fill_rate': 0.98},
            death_stats={'abnormal_deaths': 5, 'total_agents': 100},
            prophet_decision={'S': 0.6, 'E': 0.1, 'scale': 0.6},
            experience_db=None
        )
        
        if cycle % 20 == 0:
            print(f"周期{cycle}: risk={result['risk_level']}, anomaly_dims={result['total_anomaly_dims']}")
    
    # 模拟突然的异常
    print("\n" + "="*60)
    print("🧪 测试：突然出现三维异常")
    print("="*60)
    
    result = monitor.monitor_cycle(
        cycle=101,
        run_id="test_001",
        world_signature={'volatility_24h': 0.15, 'price_change_24h': 0.20},  # 暴涨
        friction_data={'slippage': 0.05, 'latency_norm': 0.20, 'fill_rate': 0.50},  # 摩擦激增
        death_stats={'abnormal_deaths': 60, 'total_agents': 100},  # 大量死亡
        prophet_decision={'S': 0.2, 'E': -0.5, 'scale': 0.2},
        experience_db=None
    )
    
    print(f"周期101: risk={result['risk_level']}, anomaly_dims={result['total_anomaly_dims']}")
    print(f"  WS异常: {result['ws_anomaly']}")
    print(f"  摩擦异常: {result['friction_anomaly']}")
    print(f"  死亡异常: {result['death_anomaly']}")
    print(f"  → {result['risk_level'].upper()}!")
    
    print("\n✅ 测试完成！")

