"""
核心模块（私有）

警告：
  ⚠️ 此目录下的所有模块都是私有的（Private）
  ⚠️ 文件名前缀 _ 表示不应直接导入
  ⚠️ 所有功能必须通过 prometheus.v6.facade 访问
  ⚠️ 违反将导致架构混乱和难以维护

核心模块:
  - _agent.py: Agent定义（StrategyParams取代Instinct）
  - _moirai.py: Agent生命周期管理（创建、淘汰、交易撮合）
  - _evolution.py: 进化管理（选择、繁殖、变异、淘汰）
  - _capital_pool.py: 资金池管理（统一资金分配和回收）
"""

# 不导出任何内容
__all__ = []

