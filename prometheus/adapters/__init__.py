"""
Adapters模块

提供各种适配器，连接不同组件
"""

from .signature_adapter import SignatureAdapter, RegimeAwareAgent, create_regime_aware_backtest

__all__ = [
    'SignatureAdapter',
    'RegimeAwareAgent',
    'create_regime_aware_backtest'
]

