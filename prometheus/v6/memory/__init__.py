"""
记忆层（MemoryLayer）

AlphaZero式学习机制:
  - 积累历史经验 (WorldSignature, Genome, Performance)
  - 智能创世（基于历史最优策略）
  - 不断逼近相对最优解

组件:
  - experience_db.py: 经验数据库（存储和查询）
  - intelligent_genesis.py: 智能创世管理器
"""

__all__ = []

