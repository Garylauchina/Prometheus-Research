"""
市场数据生成器 - Stage 1.1
符合10条黄金规则的结构切换市场生成器

创建日期: 2025-12-09
核心功能: 生成固定ATR、固定蜡烛大小、无gap的结构切换市场
"""

import numpy as np
import pandas as pd
from typing import List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketStructureGenerator:
    """
    生成符合Stage 1黄金规则的结构切换市场
    
    核心原则：
    1. 固定ATR（每个结构内波动率相同）
    2. 固定蜡烛大小（high-low基本一致）
    3. 无gap（连续价格）
    4. 无极端事件
    5. 每个结构明确可区分
    """
    
    def __init__(
        self,
        base_price: float = 40000.0,
        base_volatility: float = 0.003,  # 0.3% ATR
        candle_body_ratio: float = 0.6,  # 实体占比
        random_seed: int = None
    ):
        """
        初始化市场生成器
        
        Args:
            base_price: 起始价格
            base_volatility: 基础波动率（固定ATR）
            candle_body_ratio: 实体占比（0-1）
            random_seed: 随机种子（用于复现）
        """
        self.base_price = base_price
        self.base_volatility = base_volatility
        self.candle_body_ratio = candle_body_ratio
        
        if random_seed is not None:
            np.random.seed(random_seed)
        
        logger.info(f"MarketStructureGenerator initialized: "
                   f"base_price={base_price}, volatility={base_volatility}")
    
    def generate_switching_market(
        self,
        structures: List[str] = None,
        bars_per_structure: int = 300,
        total_bars: int = 5000,
        structure_cycle: bool = True
    ) -> pd.DataFrame:
        """
        生成结构切换市场
        
        Args:
            structures: 结构序列 ['trend_up', 'range', 'trend_down', 'fake_breakout']
            bars_per_structure: 每个结构的bars数
            total_bars: 总bars数
            structure_cycle: 是否循环结构序列
            
        Returns:
            DataFrame with ['timestamp', 'open', 'high', 'low', 'close', 
                           'volume', 'structure_type']
        """
        if structures is None:
            structures = ['trend_up', 'range', 'trend_down', 'fake_breakout']
        
        logger.info(f"Generating switching market: {total_bars} bars, "
                   f"structures={structures}, bars_per_structure={bars_per_structure}")
        
        all_candles = []
        current_price = self.base_price
        structure_index = 0
        bars_generated = 0
        
        start_time = datetime(2024, 1, 1, 0, 0, 0)
        
        while bars_generated < total_bars:
            # 确定当前结构
            if structure_cycle:
                current_structure = structures[structure_index % len(structures)]
            else:
                current_structure = structures[min(structure_index, len(structures) - 1)]
            
            # 生成当前结构的bars
            bars_to_generate = min(bars_per_structure, total_bars - bars_generated)
            
            logger.info(f"Generating structure '{current_structure}': "
                       f"{bars_to_generate} bars starting at price {current_price:.2f}")
            
            # 根据结构类型生成数据
            if current_structure == 'trend_up':
                candles, end_price = self._generate_trend_up(
                    bars_to_generate, current_price
                )
            elif current_structure == 'trend_down':
                candles, end_price = self._generate_trend_down(
                    bars_to_generate, current_price
                )
            elif current_structure == 'range':
                candles, end_price = self._generate_range(
                    bars_to_generate, current_price
                )
            elif current_structure == 'fake_breakout':
                candles, end_price = self._generate_fake_breakout(
                    bars_to_generate, current_price
                )
            else:
                raise ValueError(f"Unknown structure type: {current_structure}")
            
            # 添加时间戳和结构标签
            for i, candle in enumerate(candles):
                timestamp = start_time + timedelta(minutes=bars_generated + i)
                all_candles.append({
                    'timestamp': timestamp,
                    'open': candle[0],
                    'high': candle[1],
                    'low': candle[2],
                    'close': candle[3],
                    'volume': candle[4],
                    'structure_type': current_structure
                })
            
            current_price = end_price
            bars_generated += bars_to_generate
            structure_index += 1
        
        df = pd.DataFrame(all_candles)
        
        # 验证数据质量
        self._validate_market_data(df)
        
        logger.info(f"Market generation complete: {len(df)} bars, "
                   f"price range [{df['low'].min():.2f}, {df['high'].max():.2f}]")
        
        return df
    
    def _generate_trend_up(
        self,
        bars: int,
        start_price: float
    ) -> Tuple[List[Tuple[float, float, float, float, float]], float]:
        """
        生成上涨趋势
        
        特征：
        - 稳定上涨，每bar +0.1-0.2%
        - 固定ATR
        - 偶尔小幅回调（20%概率）
        
        Returns:
            (candles, end_price)
        """
        candles = []
        current_price = start_price
        trend_strength = 0.0015  # 0.15% per bar
        
        for i in range(bars):
            # 偶尔小幅回调
            if np.random.random() < 0.2:
                direction = -1
                trend_move = trend_strength * 0.5
            else:
                direction = 1
                trend_move = trend_strength
            
            # 生成蜡烛
            candle = self._generate_candle(
                current_price,
                direction=direction,
                trend_move=trend_move
            )
            candles.append(candle)
            current_price = candle[3]  # close
        
        return candles, current_price
    
    def _generate_trend_down(
        self,
        bars: int,
        start_price: float
    ) -> Tuple[List[Tuple[float, float, float, float, float]], float]:
        """
        生成下跌趋势
        
        特征：
        - 稳定下跌，每bar -0.1-0.2%
        - 固定ATR
        - 偶尔小幅反弹（20%概率）
        
        Returns:
            (candles, end_price)
        """
        candles = []
        current_price = start_price
        trend_strength = 0.0015  # 0.15% per bar
        
        for i in range(bars):
            # 偶尔小幅反弹
            if np.random.random() < 0.2:
                direction = 1
                trend_move = trend_strength * 0.5
            else:
                direction = -1
                trend_move = trend_strength
            
            # 生成蜡烛
            candle = self._generate_candle(
                current_price,
                direction=direction,
                trend_move=trend_move
            )
            candles.append(candle)
            current_price = candle[3]  # close
        
        return candles, current_price
    
    def _generate_range(
        self,
        bars: int,
        start_price: float
    ) -> Tuple[List[Tuple[float, float, float, float, float]], float]:
        """
        生成震荡区间
        
        特征：
        - 在 ±2% 范围内震荡
        - 无明显方向性
        - 周期性上下波动
        - 长期回归均值
        
        Returns:
            (candles, end_price)
        """
        candles = []
        center_price = start_price
        range_width = 0.02  # ±2%
        current_price = start_price
        
        # 生成正弦波形的震荡
        phase = np.random.random() * 2 * np.pi
        frequency = 2 * np.pi / 50  # 50 bars一个周期
        
        for i in range(bars):
            # 目标价格（正弦波）
            target_offset = np.sin(phase + i * frequency) * range_width
            target_price = center_price * (1 + target_offset)
            
            # 向目标价格移动
            if current_price < target_price:
                direction = 1
            else:
                direction = -1
            
            # 移动幅度较小（为了保持震荡）
            trend_move = abs(target_price - current_price) / current_price * 0.3
            
            # 生成蜡烛
            candle = self._generate_candle(
                current_price,
                direction=direction,
                trend_move=trend_move
            )
            candles.append(candle)
            current_price = candle[3]  # close
        
        return candles, current_price
    
    def _generate_fake_breakout(
        self,
        bars: int,
        start_price: float
    ) -> Tuple[List[Tuple[float, float, float, float, float]], float]:
        """
        生成假突破
        
        特征：
        - 前30%：快速上涨（诱多）
        - 中20%：横盘整理
        - 后50%：快速反转下跌
        - 最终价格低于起点
        
        Returns:
            (candles, end_price)
        """
        candles = []
        current_price = start_price
        
        # 阶段1：快速上涨（诱多）
        stage1_bars = int(bars * 0.3)
        stage1_trend = 0.003  # 0.3% per bar
        
        for i in range(stage1_bars):
            candle = self._generate_candle(
                current_price,
                direction=1,
                trend_move=stage1_trend
            )
            candles.append(candle)
            current_price = candle[3]
        
        # 阶段2：横盘整理
        stage2_bars = int(bars * 0.2)
        
        for i in range(stage2_bars):
            direction = 1 if np.random.random() < 0.5 else -1
            candle = self._generate_candle(
                current_price,
                direction=direction,
                trend_move=0.0005  # 小幅波动
            )
            candles.append(candle)
            current_price = candle[3]
        
        # 阶段3：快速反转下跌
        stage3_bars = bars - stage1_bars - stage2_bars
        # 计算需要的下跌幅度（回到起点以下5%）
        target_price = start_price * 0.95
        total_drop = (current_price - target_price) / current_price
        stage3_trend = total_drop / stage3_bars
        
        for i in range(stage3_bars):
            candle = self._generate_candle(
                current_price,
                direction=-1,
                trend_move=stage3_trend
            )
            candles.append(candle)
            current_price = candle[3]
        
        return candles, current_price
    
    def _generate_candle(
        self,
        start_price: float,
        direction: int,  # 1 for up, -1 for down
        trend_move: float = 0.0
    ) -> Tuple[float, float, float, float, float]:
        """
        生成单根蜡烛
        
        Args:
            start_price: 开盘价
            direction: 方向（1 上涨, -1 下跌）
            trend_move: 趋势移动幅度（比例）
            
        Returns:
            (open, high, low, close, volume)
        """
        open_price = start_price
        
        # 计算close（基于趋势）
        trend_change = start_price * trend_move * direction
        # 添加小幅随机波动（±0.1%）
        random_change = start_price * np.random.uniform(-0.001, 0.001)
        close_price = start_price + trend_change + random_change
        
        # 计算ATR范围
        atr = start_price * self.base_volatility
        
        # 实体大小
        body_size = abs(close_price - open_price)
        
        # 上下影线（保证总高度接近ATR）
        remaining_range = atr - body_size
        upper_wick = remaining_range * np.random.uniform(0.3, 0.7)
        lower_wick = remaining_range - upper_wick
        
        # 计算high和low
        if close_price > open_price:  # 阳线
            high = close_price + upper_wick
            low = open_price - lower_wick
        else:  # 阴线
            high = open_price + upper_wick
            low = close_price - lower_wick
        
        # 确保价格非负
        low = max(low, start_price * 0.5)
        
        # 生成volume（固定范围，添加随机性）
        volume = np.random.uniform(1000, 2000)
        
        return (open_price, high, low, close_price, volume)
    
    def _validate_market_data(self, df: pd.DataFrame):
        """
        验证生成的市场数据质量
        
        检查项：
        1. 固定ATR（标准差 < 0.0005）
        2. 无price gap
        3. 价格连续性
        """
        # 计算ATR
        df['atr'] = (df['high'] - df['low']) / df['close']
        atr_mean = df['atr'].mean()
        atr_std = df['atr'].std()
        
        logger.info(f"ATR validation: mean={atr_mean:.6f}, std={atr_std:.6f}")
        
        if atr_std > 0.001:
            logger.warning(f"ATR标准差较大: {atr_std:.6f} (目标 < 0.001)")
        
        # 检查price gap
        df['price_gap'] = abs(df['open'] - df['close'].shift(1))
        max_gap = df['price_gap'].max()
        
        logger.info(f"Price gap validation: max_gap={max_gap:.2f}")
        
        # 检查价格连续性
        gaps = df[df['price_gap'] > df['close'] * 0.001]  # gap > 0.1%
        if len(gaps) > 0:
            logger.warning(f"发现 {len(gaps)} 处较大gap (> 0.1%)")
        
        # 统计结构分布
        structure_counts = df['structure_type'].value_counts()
        logger.info(f"Structure distribution:\n{structure_counts}")


def generate_stage1_market(
    total_bars: int = 5000,
    save_path: str = None,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    快捷函数：生成Stage 1标准市场数据
    
    Args:
        total_bars: 总bars数
        save_path: 保存路径（可选）
        random_seed: 随机种子
        
    Returns:
        DataFrame
    """
    generator = MarketStructureGenerator(
        base_price=40000.0,
        base_volatility=0.003,  # 0.3% ATR
        random_seed=random_seed
    )
    
    df = generator.generate_switching_market(
        structures=['trend_up', 'range', 'trend_down', 'fake_breakout'],
        bars_per_structure=300,
        total_bars=total_bars,
        structure_cycle=True
    )
    
    if save_path:
        df.to_csv(save_path, index=False)
        logger.info(f"Market data saved to: {save_path}")
    
    return df


if __name__ == "__main__":
    # 测试生成
    import matplotlib.pyplot as plt
    
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 生成Stage 1测试市场数据...")
    df = generate_stage1_market(
        total_bars=5000,
        save_path="data/stage1_market_test.csv",
        random_seed=42
    )
    
    print(f"\n✅ 生成完成: {len(df)} bars")
    print(f"   价格范围: [{df['low'].min():.2f}, {df['high'].max():.2f}]")
    print(f"   ATR均值: {((df['high'] - df['low']) / df['close']).mean():.6f}")
    print(f"   ATR标准差: {((df['high'] - df['low']) / df['close']).std():.6f}")
    
    # 可视化
    print("\n📊 生成可视化图表...")
    fig, axes = plt.subplots(2, 1, figsize=(15, 10))
    
    # 价格图
    ax1 = axes[0]
    colors = {'trend_up': 'green', 'trend_down': 'red', 
              'range': 'blue', 'fake_breakout': 'orange'}
    
    for structure in df['structure_type'].unique():
        mask = df['structure_type'] == structure
        subset = df[mask]
        ax1.plot(subset.index, subset['close'], 
                color=colors.get(structure, 'gray'),
                label=structure, linewidth=1)
    
    ax1.set_title('Stage 1 Market - Price Action', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Bar Index')
    ax1.set_ylabel('Price')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # ATR图
    ax2 = axes[1]
    df['atr_pct'] = (df['high'] - df['low']) / df['close'] * 100
    ax2.plot(df.index, df['atr_pct'], color='purple', linewidth=0.5, alpha=0.7)
    ax2.axhline(y=df['atr_pct'].mean(), color='red', linestyle='--', 
               label=f'Mean ATR: {df["atr_pct"].mean():.3f}%')
    ax2.set_title('ATR Consistency', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Bar Index')
    ax2.set_ylabel('ATR (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data/stage1_market_visualization.png', dpi=150)
    print(f"   可视化已保存: data/stage1_market_visualization.png")
    
    print("\n✅ Task 1.1 完成！")

