"""
Mock训练配置 - v6.0
==================

完全封装的Mock训练配置，严格遵守"统一封装，严禁旁路"原则。
"""

from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class MockTrainingConfig:
    """
    Mock训练配置（v6.0极简版）
    
    设计原则：
    1. 完全自由：用户可配置所有进化参数
    2. 极简税率：Moirai自动保证20%资金池生死线（不可配置）
    3. 严格封装：底层模块完全隐藏
    """
    
    # ========== 核心参数（必须） ==========
    cycles: int                              # 训练周期数
    total_system_capital: float              # 系统初始资金
    
    # ========== 进化参数（完全自由） ==========
    agent_count: int = 50                    # 创世Agent个数
    genesis_allocation_ratio: float = 0.2    # 创世配资比例（0.2=20%给Agent，80%资金池）
    evolution_interval: int = 10             # 进化周期（每N周期进化一次）
    elimination_rate: float = 0.3            # 淘汰率（0.3=淘汰30%）
    elite_ratio: float = 0.2                 # 精英比例（0.2=保留20%精英）
    fitness_mode: str = 'profit_factor'      # ✅ Stage 1.1: Fitness计算模式（profit_factor/absolute_return）
    
    # ========== v4新增：退休机制（可选） ==========
    retirement_enabled: bool = False         # 🎖️ 是否启用退休机制（光荣退休+寿终正寝）
    medal_system_enabled: bool = False       # 🏅 是否启用奖章系统（Top5颁发奖章）
    
    # ========== 创世参数（完全自由） ==========
    genesis_strategy: str = 'adaptive'       # 创世策略: 'pure_random', 'adaptive', 'hybrid'
    genesis_seed: Optional[int] = None       # 创世随机种子（None=真随机）
    full_genome_unlock: bool = False         # 是否解锁所有基因（False=渐进式，True=激进式）
    
    # ========== 交易参数（完全自由） ==========
    max_leverage: float = 100.0              # 最大杠杆倍数（OKX最高100x）
    max_position_pct: float = 0.8            # 单次开仓上限（占Agent总资金的%）
    enable_short: bool = True                # 是否允许做空
    fee_rate: float = 0.0005                 # 手续费率（0.05% taker）
    
    # ========== 市场参数 ==========
    market_type: str = 'unknown'             # 市场类型（用于ExperienceDB分类）
    ws_window_size: int = 100                # WorldSignature计算窗口
    
    # ========== 经验库参数（可选） ==========
    experience_db_path: Optional[str] = None  # 数据库路径（None=从0开始）
    top_k_to_save: int = 10                  # 保存最佳Agent数量
    save_experience_interval: int = 50       # 保存经验间隔
    
    # ========== 验证参数 ==========
    validation_data: Optional[pd.DataFrame] = None  # 验证集数据（None=不验证）
    validation_cycles: int = 1000            # 验证周期数
    auto_validate: bool = False              # 是否训练后自动验证
    
    # ========== 日志参数 ==========
    log_dir: str = 'mock_training_logs'      # 日志目录
    log_interval: int = 100                  # 进度日志间隔
    enable_debug_log: bool = False           # 是否启用详细调试日志
    
    # ========== 硬约束（系统保证，不可配置） ==========
    # CAPITAL_POOL_RESERVE_RATIO = 0.20  # 20%流动资金生死线（Moirai自动保证）
    # FIXED_TAX_RATE = 0.10              # 固定税率10%（Moirai自动计算）
    
    def __post_init__(self):
        """参数验证"""
        assert self.cycles > 0, "cycles必须>0"
        assert self.total_system_capital > 0, "total_system_capital必须>0"
        assert self.agent_count > 0, "agent_count必须>0"
        assert 0 < self.genesis_allocation_ratio <= 1, "genesis_allocation_ratio必须在(0, 1]"
        assert 0 <= self.elimination_rate < 1, "elimination_rate必须在[0, 1)"
        assert 0 < self.elite_ratio < 1, "elite_ratio必须在(0, 1)"
        assert self.max_leverage >= 1, "max_leverage必须>=1"
        assert 0 < self.max_position_pct <= 1, "max_position_pct必须在(0, 1]"
        assert self.validation_cycles > 0, "validation_cycles必须>0"
        if self.auto_validate and self.validation_data is None:
            raise ValueError("auto_validate=True时必须提供validation_data")


@dataclass
class MockTrainingResult:
    """
    Mock训练结果（完全封装）
    """
    
    # ========== 基本信息 ==========
    run_id: str                              # 运行ID（时间戳）
    actual_cycles: int                       # 实际运行周期数
    
    # ========== 系统级指标 ==========
    system_roi: float                        # 系统ROI
    system_total_capital: float              # 系统最终总资金
    btc_benchmark_roi: float                 # BTC基准ROI
    outperformance: float                    # 超越BTC的幅度
    
    # ========== Agent统计 ==========
    agent_count_final: int                   # 最终Agent数量
    agent_avg_roi: float                     # Agent平均ROI
    agent_median_roi: float                  # Agent中位数ROI
    agent_best_roi: float                    # 最佳Agent ROI
    agent_avg_trade_count: float             # 平均交易次数
    
    # ========== 资金池状态 ==========
    capital_pool_balance: float              # 资金池余额
    capital_utilization: float               # 资金利用率（Agent资金/总资金）
    
    # ========== 最佳Agent（用于智能创世） ==========
    best_agents: list                        # Top K最佳Agent
    
    # ========== 经验库统计 ==========
    experience_db_records: int               # ExperienceDB总记录数
    experience_saved: bool                   # 本次是否保存了经验
    
    # ========== 日志路径 ==========
    log_file: str                            # 详细日志文件路径
    report_file: str                         # 报告文件路径
    
    # ========== 对账验证 ==========
    reconciliation_passed: bool              # 对账是否通过
    reconciliation_details: dict             # 对账详情
    
    # ========== 验证结果（如果有） ==========
    validation_result: Optional[dict] = None  # 验证集结果

