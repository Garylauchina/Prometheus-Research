"""
TrainingInterface - v8.0对抗训练接口⭐⭐⭐

职责：
  • 生成各种对抗性市场场景
  • 测试v7.0系统的鲁棒性
  • 发现系统弱点

设计理念：
  • v8.0是独立的训练工具
  • 通过标准接口与v7.0交互
  • 不侵入v7.0代码

Created: 2025-12-11
Author: Prometheus Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """训练场景类型"""
    # 趋势场景
    BULL_MARKET = "bull_market"          # 牛市
    BEAR_MARKET = "bear_market"          # 熊市
    SIDEWAYS = "sideways"                # 震荡
    
    # 极端场景
    BLACK_SWAN = "black_swan"            # 黑天鹅（突然暴跌）
    FLASH_CRASH = "flash_crash"          # 闪崩
    LIQUIDITY_CRISIS = "liquidity_crisis"  # 流动性枯竭
    PUMP_AND_DUMP = "pump_and_dump"      # 拉高出货
    
    # 复杂场景
    REGIME_CHANGE = "regime_change"      # 市场regime转换
    HIGH_VOLATILITY = "high_volatility"  # 高波动
    WHIPSAW = "whipsaw"                  # 来回打脸
    
    # 对抗场景
    ADVERSARIAL = "adversarial"          # 纯对抗（针对性攻击）
    RANDOM_WALK = "random_walk"          # 随机游走
    WORST_CASE = "worst_case"            # 最坏情况


@dataclass
class TrainingScenario:
    """
    训练场景配置⭐
    """
    scenario_type: ScenarioType
    name: str
    description: str
    
    # 时间参数
    duration_cycles: int  # 持续周期数
    
    # 市场参数
    initial_price: float
    volatility: float     # 波动率
    trend: float          # 趋势强度（-1到+1）
    
    # 特殊事件
    events: List[Dict[str, Any]] = None
    
    # 难度等级
    difficulty: int = 1  # 1-10
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'scenario_type': self.scenario_type.value,
            'name': self.name,
            'description': self.description,
            'duration_cycles': self.duration_cycles,
            'initial_price': self.initial_price,
            'volatility': self.volatility,
            'trend': self.trend,
            'difficulty': self.difficulty
        }


@dataclass
class TrainingResult:
    """
    训练结果⭐
    """
    scenario: TrainingScenario
    
    # 性能指标
    final_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    
    # 生存指标
    survival_rate: float       # Agent存活率
    avg_lifespan: float        # 平均寿命
    total_deaths: int          # 总死亡数
    abnormal_deaths: int       # 非正常死亡数
    
    # 适应指标
    adaptation_time: int       # 适应时间（周期数）
    recovery_rate: float       # 恢复速度
    
    # 详细数据
    cycle_data: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'scenario': self.scenario.to_dict(),
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'survival_rate': self.survival_rate,
            'avg_lifespan': self.avg_lifespan,
            'total_deaths': self.total_deaths,
            'abnormal_deaths': self.abnormal_deaths,
            'adaptation_time': self.adaptation_time,
            'recovery_rate': self.recovery_rate
        }


class TrainingInterface(ABC):
    """
    训练接口（抽象基类）⭐⭐⭐
    
    v8.0对抗训练工具通过这个接口生成场景
    """
    
    @abstractmethod
    def create_scenario(self, scenario_type: ScenarioType, **kwargs) -> TrainingScenario:
        """
        创建训练场景⭐
        
        Args:
            scenario_type: 场景类型
            **kwargs: 场景特定参数
        
        Returns:
            TrainingScenario: 场景配置
        """
        pass
    
    @abstractmethod
    def run_scenario(
        self,
        scenario: TrainingScenario,
        system_under_test: Any  # v7.0系统实例
    ) -> TrainingResult:
        """
        运行训练场景⭐⭐⭐
        
        Args:
            scenario: 场景配置
            system_under_test: 被测试的v7.0系统
        
        Returns:
            TrainingResult: 训练结果
        """
        pass
    
    @abstractmethod
    def run_stress_test(
        self,
        scenarios: List[TrainingScenario],
        system_under_test: Any
    ) -> Dict[str, TrainingResult]:
        """
        压力测试：运行多个场景⭐
        
        Args:
            scenarios: 场景列表
            system_under_test: 被测试的v7.0系统
        
        Returns:
            Dict[str, TrainingResult]: 场景名称->结果
        """
        pass


class AdversarialTraining(TrainingInterface):
    """
    对抗训练实现⭐⭐⭐
    
    生成各种对抗性场景来测试系统
    """
    
    def __init__(self):
        """初始化对抗训练器"""
        logger.info(f"🎯 AdversarialTraining已初始化")
    
    def create_scenario(self, scenario_type: ScenarioType, **kwargs) -> TrainingScenario:
        """创建训练场景"""
        
        # 预定义场景配置
        scenario_configs = {
            ScenarioType.BULL_MARKET: {
                'name': '牛市场景',
                'description': '持续上涨，测试盈利能力',
                'duration_cycles': 100,
                'initial_price': 50000.0,
                'volatility': 0.02,
                'trend': 0.8,
                'difficulty': 2
            },
            ScenarioType.BEAR_MARKET: {
                'name': '熊市场景',
                'description': '持续下跌，测试做空和防御能力',
                'duration_cycles': 100,
                'initial_price': 50000.0,
                'volatility': 0.03,
                'trend': -0.8,
                'difficulty': 4
            },
            ScenarioType.BLACK_SWAN: {
                'name': '黑天鹅场景',
                'description': '突然暴跌15%，测试风险控制',
                'duration_cycles': 50,
                'initial_price': 50000.0,
                'volatility': 0.05,
                'trend': -0.3,
                'difficulty': 8,
                'events': [
                    {'cycle': 25, 'type': 'crash', 'magnitude': -0.15}
                ]
            },
            ScenarioType.FLASH_CRASH: {
                'name': '闪崩场景',
                'description': '瞬间暴跌后快速恢复',
                'duration_cycles': 30,
                'initial_price': 50000.0,
                'volatility': 0.08,
                'trend': 0.0,
                'difficulty': 9,
                'events': [
                    {'cycle': 15, 'type': 'crash', 'magnitude': -0.20},
                    {'cycle': 18, 'type': 'recovery', 'magnitude': 0.15}
                ]
            },
            ScenarioType.LIQUIDITY_CRISIS: {
                'name': '流动性枯竭',
                'description': '成交量骤降，滑点激增',
                'duration_cycles': 50,
                'initial_price': 50000.0,
                'volatility': 0.04,
                'trend': -0.2,
                'difficulty': 7,
                'events': [
                    {'cycle': 20, 'type': 'liquidity_drop', 'fill_rate': 0.3}
                ]
            },
            ScenarioType.WHIPSAW: {
                'name': '来回打脸',
                'description': '价格剧烈来回震荡',
                'duration_cycles': 100,
                'initial_price': 50000.0,
                'volatility': 0.06,
                'trend': 0.0,
                'difficulty': 6,
                'events': [
                    {'cycle': i*10, 'type': 'reverse', 'magnitude': 0.05 if i%2==0 else -0.05}
                    for i in range(10)
                ]
            },
            ScenarioType.WORST_CASE: {
                'name': '最坏情况',
                'description': '组合所有不利因素',
                'duration_cycles': 200,
                'initial_price': 50000.0,
                'volatility': 0.10,
                'trend': -0.5,
                'difficulty': 10,
                'events': [
                    {'cycle': 50, 'type': 'crash', 'magnitude': -0.15},
                    {'cycle': 100, 'type': 'liquidity_drop', 'fill_rate': 0.2},
                    {'cycle': 150, 'type': 'crash', 'magnitude': -0.20}
                ]
            }
        }
        
        # 获取配置
        config = scenario_configs.get(scenario_type, {
            'name': scenario_type.value,
            'description': 'Custom scenario',
            'duration_cycles': 100,
            'initial_price': 50000.0,
            'volatility': 0.02,
            'trend': 0.0,
            'difficulty': 5
        })
        
        # 合并kwargs
        config.update(kwargs)
        
        # 创建场景
        scenario = TrainingScenario(
            scenario_type=scenario_type,
            name=config['name'],
            description=config['description'],
            duration_cycles=config['duration_cycles'],
            initial_price=config['initial_price'],
            volatility=config['volatility'],
            trend=config['trend'],
            events=config.get('events'),
            difficulty=config['difficulty']
        )
        
        logger.info(f"📋 场景已创建: {scenario.name} (难度={scenario.difficulty}/10)")
        
        return scenario
    
    def run_scenario(
        self,
        scenario: TrainingScenario,
        system_under_test: Any
    ) -> TrainingResult:
        """
        运行单个训练场景
        
        TODO: 实现完整的场景运行逻辑
        需要：
        1. 根据场景配置生成市场数据
        2. 将系统连接到模拟数据源
        3. 运行系统
        4. 收集性能指标
        5. 生成报告
        """
        logger.info(f"🏃 开始运行场景: {scenario.name}")
        
        # TODO: 实际实现
        raise NotImplementedError("run_scenario() 待实现")
    
    def run_stress_test(
        self,
        scenarios: List[TrainingScenario],
        system_under_test: Any
    ) -> Dict[str, TrainingResult]:
        """
        运行压力测试
        """
        logger.info(f"💪 开始压力测试: {len(scenarios)}个场景")
        
        results = {}
        for scenario in scenarios:
            try:
                result = self.run_scenario(scenario, system_under_test)
                results[scenario.name] = result
                logger.info(f"✅ 场景完成: {scenario.name}")
            except Exception as e:
                logger.error(f"❌ 场景失败: {scenario.name}, {e}")
        
        logger.info(f"📊 压力测试完成: {len(results)}/{len(scenarios)}个场景成功")
        
        return results


# ========== 预定义场景集合 ==========

def get_standard_test_suite() -> List[TrainingScenario]:
    """
    获取标准测试套件⭐
    
    包含所有基础场景，用于全面测试系统
    
    Returns:
        List[TrainingScenario]: 标准场景列表
    """
    trainer = AdversarialTraining()
    
    scenarios = [
        # 基础场景
        trainer.create_scenario(ScenarioType.BULL_MARKET),
        trainer.create_scenario(ScenarioType.BEAR_MARKET),
        trainer.create_scenario(ScenarioType.SIDEWAYS),
        
        # 极端场景
        trainer.create_scenario(ScenarioType.BLACK_SWAN),
        trainer.create_scenario(ScenarioType.FLASH_CRASH),
        
        # 对抗场景
        trainer.create_scenario(ScenarioType.LIQUIDITY_CRISIS),
        trainer.create_scenario(ScenarioType.WHIPSAW),
    ]
    
    return scenarios


def get_extreme_test_suite() -> List[TrainingScenario]:
    """
    获取极限测试套件⭐⭐⭐
    
    包含所有极端场景，测试系统极限
    
    Returns:
        List[TrainingScenario]: 极限场景列表
    """
    trainer = AdversarialTraining()
    
    scenarios = [
        trainer.create_scenario(ScenarioType.BLACK_SWAN),
        trainer.create_scenario(ScenarioType.FLASH_CRASH),
        trainer.create_scenario(ScenarioType.LIQUIDITY_CRISIS),
        trainer.create_scenario(ScenarioType.WHIPSAW),
        trainer.create_scenario(ScenarioType.WORST_CASE),
    ]
    
    return scenarios


if __name__ == "__main__":
    # 测试代码
    print("测试AdversarialTraining...")
    trainer = AdversarialTraining()
    
    # 创建几个场景
    bull = trainer.create_scenario(ScenarioType.BULL_MARKET)
    print(f"\n场景1: {bull.name}")
    print(f"  描述: {bull.description}")
    print(f"  难度: {bull.difficulty}/10")
    
    black_swan = trainer.create_scenario(ScenarioType.BLACK_SWAN)
    print(f"\n场景2: {black_swan.name}")
    print(f"  描述: {black_swan.description}")
    print(f"  难度: {black_swan.difficulty}/10")
    print(f"  事件: {len(black_swan.events)}个")
    
    # 获取标准测试套件
    standard_suite = get_standard_test_suite()
    print(f"\n标准测试套件: {len(standard_suite)}个场景")
    for i, scenario in enumerate(standard_suite, 1):
        print(f"  {i}. {scenario.name} (难度={scenario.difficulty})")
    
    print("\n✅ TrainingInterface设计完成！")

