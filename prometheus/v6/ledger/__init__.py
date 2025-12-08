"""
账簿系统

核心特性:
  - 双账簿（PrivateLedger + PublicLedger）
  - 自动对账（每笔交易自动验证一致性）
  - 原子操作（私账先记，公账后记，不可分割）

组件:
  - private_ledger.py: 私有账簿（Agent视角）
  - public_ledger.py: 公共账簿（系统视角）
  - account_system.py: 账户系统（自动对账）
"""

__all__ = []

