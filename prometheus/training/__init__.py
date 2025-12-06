"""
Training模块

多情境训练系统 - Mock训练学校
"""

from .regime_generators import (
    RegimeGenerator,
    BullMarketGenerator,
    BearMarketGenerator,
    VolatilityGenerator,
    SidewaysGenerator,
    MultiRegimeGenerator,
    create_regime_generator,
    create_standard_multi_regime
)

from .training_school import (
    MockTrainingSchool,
    TrainingCurriculum,
    TrainingSession
)

# from .adaptive_evolution import (
#     AdaptiveEvolutionEngine,
#     RegimeAwareEvolution
# )

__all__ = [
    'RegimeGenerator',
    'BullMarketGenerator',
    'BearMarketGenerator',
    'VolatilityGenerator',
    'SidewaysGenerator',
    'MultiRegimeGenerator',
    'create_regime_generator',
    'create_standard_multi_regime',
    'MockTrainingSchool',
    'TrainingCurriculum',
    'TrainingSession',
    # 'AdaptiveEvolutionEngine',
    # 'RegimeAwareEvolution'
]

