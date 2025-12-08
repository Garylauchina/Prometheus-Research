"""
PressureController测试套件

测试内容：
  1. 压力调节逻辑
  2. 动态调整机制
  3. 竞争模式选择
  4. 历史记录
"""

import pytest
from prometheus.v6.self_play import PressureController, PressureHistory


# ===== 初始化测试 =====

def test_pressure_controller_initialization():
    """测试压力调节器初始化"""
    controller = PressureController(initial_pressure=0.50)
    assert controller.pressure_level == 0.50
    assert len(controller.history) == 0


def test_pressure_controller_custom_initial():
    """测试自定义初始压力"""
    controller = PressureController(initial_pressure=0.80)
    assert controller.pressure_level == 0.80


# ===== 压力调节测试 =====

def test_adjust_pressure_basic():
    """测试基本压力调节"""
    controller = PressureController(initial_pressure=0.50)
    
    # 调整压力
    config = controller.adjust_pressure(
        generation=1,
        diversity_index=0.50,
        avg_fitness=0.30,
        fitness_variance=0.20
    )
    
    # 检查返回配置
    assert 'pressure_level' in config
    assert 'adversary_ratio' in config
    assert 'competition_mode' in config
    assert 'elimination_rate' in config
    
    # 检查压力范围
    assert 0.1 <= config['pressure_level'] <= 1.0


def test_adjust_pressure_low_diversity():
    """测试低多样性情况"""
    controller = PressureController(initial_pressure=0.50)
    
    # 低多样性（应该降低压力）
    config = controller.adjust_pressure(
        generation=10,
        diversity_index=0.20,  # 低多样性
        avg_fitness=0.30,
        fitness_variance=0.20
    )
    
    # 压力应该降低
    assert config['pressure_level'] < 0.50
    assert config['competition_mode'] in ['relaxed', 'moderate']


def test_adjust_pressure_high_diversity():
    """测试高多样性情况"""
    controller = PressureController(initial_pressure=0.50)
    
    # 高多样性（应该增加压力）
    config = controller.adjust_pressure(
        generation=10,
        diversity_index=0.80,  # 高多样性
        avg_fitness=0.30,
        fitness_variance=0.20
    )
    
    # 压力应该增加
    assert config['pressure_level'] > 0.50


def test_adjust_pressure_high_fitness():
    """测试高适应度情况"""
    controller = PressureController(initial_pressure=0.50)
    
    # 高适应度（应该增加压力）
    config = controller.adjust_pressure(
        generation=10,
        diversity_index=0.50,
        avg_fitness=0.80,  # 高适应度
        fitness_variance=0.20
    )
    
    # 压力应该增加
    assert config['pressure_level'] > 0.50


def test_adjust_pressure_low_variance():
    """测试低方差情况"""
    controller = PressureController(initial_pressure=0.50)
    
    # 低方差（趋同，应该增加扰动）
    config = controller.adjust_pressure(
        generation=10,
        diversity_index=0.50,
        avg_fitness=0.30,
        fitness_variance=0.05  # 低方差
    )
    
    # 应该有一定压力增加（扰动）
    assert config['pressure_level'] >= 0.40


# ===== 竞争模式测试 =====

def test_competition_mode_relaxed():
    """测试放松模式"""
    controller = PressureController(initial_pressure=0.20)
    
    config = controller.adjust_pressure(
        generation=1,
        diversity_index=0.20,  # 低多样性
        avg_fitness=0.05,      # 低适应度
        fitness_variance=0.20
    )
    
    assert config['competition_mode'] == 'relaxed'


def test_competition_mode_moderate():
    """测试适中模式"""
    controller = PressureController(initial_pressure=0.50)
    
    config = controller.adjust_pressure(
        generation=20,
        diversity_index=0.50,
        avg_fitness=0.30,
        fitness_variance=0.20
    )
    
    assert config['competition_mode'] in ['moderate', 'relaxed', 'intense']


def test_competition_mode_intense():
    """测试激烈模式"""
    controller = PressureController(initial_pressure=0.80)
    
    config = controller.adjust_pressure(
        generation=100,
        diversity_index=0.80,  # 高多样性
        avg_fitness=0.60,      # 高适应度
        fitness_variance=0.20
    )
    
    assert config['competition_mode'] in ['moderate', 'intense']


# ===== 历史记录测试 =====

def test_pressure_history_recording():
    """测试压力历史记录"""
    controller = PressureController()
    
    # 调整多次
    for gen in range(5):
        controller.adjust_pressure(
            generation=gen,
            diversity_index=0.50,
            avg_fitness=0.30,
            fitness_variance=0.20
        )
    
    # 检查历史
    history = controller.get_pressure_history()
    assert len(history) == 5
    assert all(isinstance(h, PressureHistory) for h in history)


def test_get_pressure_history_last_n():
    """测试获取最近N条记录"""
    controller = PressureController()
    
    # 调整10次
    for gen in range(10):
        controller.adjust_pressure(
            generation=gen,
            diversity_index=0.50,
            avg_fitness=0.30,
            fitness_variance=0.20
        )
    
    # 获取最近3条
    last_3 = controller.get_pressure_history(last_n=3)
    assert len(last_3) == 3
    assert last_3[-1].generation == 9


# ===== 统计信息测试 =====

def test_get_statistics():
    """测试获取统计信息"""
    controller = PressureController(initial_pressure=0.50)
    
    # 调整多次
    for gen in range(10):
        controller.adjust_pressure(
            generation=gen,
            diversity_index=0.50 + gen * 0.01,
            avg_fitness=0.30,
            fitness_variance=0.20
        )
    
    # 获取统计
    stats = controller.get_statistics()
    
    assert 'current_pressure' in stats
    assert 'total_adjustments' in stats
    assert 'avg_pressure' in stats
    assert 'pressure_trend' in stats
    assert stats['total_adjustments'] == 10


def test_get_current_pressure():
    """测试获取当前压力"""
    controller = PressureController(initial_pressure=0.50)
    
    assert controller.get_current_pressure() == 0.50
    
    controller.adjust_pressure(
        generation=1,
        diversity_index=0.50,
        avg_fitness=0.30,
        fitness_variance=0.20
    )
    
    current = controller.get_current_pressure()
    assert 0.1 <= current <= 1.0


# ===== 重置测试 =====

def test_reset():
    """测试重置功能"""
    controller = PressureController(initial_pressure=0.50)
    
    # 调整几次
    for gen in range(5):
        controller.adjust_pressure(
            generation=gen,
            diversity_index=0.50,
            avg_fitness=0.30,
            fitness_variance=0.20
        )
    
    # 重置
    controller.reset()
    
    assert controller.pressure_level == 0.50
    assert len(controller.history) == 0


# ===== 边界测试 =====

def test_pressure_bounds():
    """测试压力边界"""
    controller = PressureController(initial_pressure=0.95)
    
    # 极高的多样性和适应度（应该增加压力，但不能超过1.0）
    config = controller.adjust_pressure(
        generation=100,
        diversity_index=0.99,
        avg_fitness=0.99,
        fitness_variance=0.30
    )
    
    assert config['pressure_level'] <= 1.0


def test_pressure_lower_bound():
    """测试压力下界"""
    controller = PressureController(initial_pressure=0.15)
    
    # 极低的多样性和适应度（应该降低压力，但不能低于0.1）
    config = controller.adjust_pressure(
        generation=1,
        diversity_index=0.05,
        avg_fitness=0.01,
        fitness_variance=0.05
    )
    
    assert config['pressure_level'] >= 0.1


# ===== 集成测试 =====

def test_pressure_controller_full_workflow():
    """测试完整工作流"""
    controller = PressureController(initial_pressure=0.50)
    
    # 模拟10代进化
    for gen in range(10):
        config = controller.adjust_pressure(
            generation=gen,
            diversity_index=0.50 + gen * 0.02,  # 逐渐增加多样性
            avg_fitness=0.30 + gen * 0.03,      # 逐渐增加适应度
            fitness_variance=0.20 - gen * 0.01  # 逐渐降低方差
        )
        
        # 检查配置合理性
        assert 0.1 <= config['pressure_level'] <= 1.0
        assert 0.0 <= config['adversary_ratio'] <= 1.0
        assert 0.0 <= config['elimination_rate'] <= 1.0
        assert config['competition_mode'] in ['relaxed', 'moderate', 'intense']
    
    # 检查历史
    history = controller.get_pressure_history()
    assert len(history) == 10
    
    # 检查统计
    stats = controller.get_statistics()
    assert stats['total_adjustments'] == 10
    assert stats['pressure_trend'] in ['increasing', 'decreasing', 'stable']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

