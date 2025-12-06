"""
WorldSignature v2.0 - 市场情境编码系统

核心模块：
- MacroCode: 宏观编码（长时间窗口）
- MicroCode: 微观编码（短时间窗口）
- WorldSignature_V2: 完整市场签名
- StreamingSignatureGenerator: 流式签名生成器
"""

from .macro_code import MacroCode
from .micro_code import MicroCode
from .signature import WorldSignature_V2
from .generator import StreamingSignatureGenerator
from .regime import RegimeLibrary
from .metrics import (
    calculate_regime_confidence,
    calculate_stability_score,
    calculate_danger_index,
    calculate_opportunity_index,
    calculate_novelty_score,
)

__version__ = "2.0.0"

__all__ = [
    "MacroCode",
    "MicroCode",
    "WorldSignature_V2",
    "StreamingSignatureGenerator",
    "RegimeLibrary",
    "calculate_regime_confidence",
    "calculate_stability_score",
    "calculate_danger_index",
    "calculate_opportunity_index",
    "calculate_novelty_score",
]

