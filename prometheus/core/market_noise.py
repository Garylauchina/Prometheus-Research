"""
市场噪声层 - v5.2新增模块

真实市场中的随机事件与异常：
1. 流动性突变 (Liquidity Shock)
2. 滑点尖峰 (Slippage Spike)
3. 资金费率跳跃 (Funding Rate Jump)
4. 订单簿断层 (Order Book Gap)

这些噪声事件会随机发生，模拟真实市场的不可预测性。

Author: Prometheus Team
Version: v5.2
Date: 2025-12-05
"""

import random
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NoiseEvent:
    """噪声事件"""
    event_type: str       # 事件类型
    magnitude: float      # 影响强度
    description: str      # 事件描述
    timestamp: int        # 发生时间（周期）


class MarketNoiseLayer:
    """
    市场噪声层
    
    模拟真实市场中的突发事件和异常：
    - 流动性突然枯竭
    - 滑点突然暴涨
    - 资金费率突变
    - 订单簿出现断层
    
    这些事件会随机发生，为Agent提供更真实的市场环境。
    """
    
    def __init__(self,
                 liquidity_shock_prob: float = 0.05,    # 5%概率
                 slippage_spike_prob: float = 0.10,     # 10%概率
                 funding_jump_prob: float = 0.03,       # 3%概率
                 orderbook_gap_prob: float = 0.08,      # 8%概率
                 enable_extreme_events: bool = False):   # 极端事件（更低概率，更大影响）
        """
        初始化市场噪声层
        
        Args:
            liquidity_shock_prob: 流动性冲击概率（每轮）
            slippage_spike_prob: 滑点尖峰概率（每轮）
            funding_jump_prob: 资金费率跳跃概率（每轮）
            orderbook_gap_prob: 订单簿断层概率（每轮）
            enable_extreme_events: 是否启用极端事件（黑天鹅）
        """
        self.liquidity_shock_prob = liquidity_shock_prob
        self.slippage_spike_prob = slippage_spike_prob
        self.funding_jump_prob = funding_jump_prob
        self.orderbook_gap_prob = orderbook_gap_prob
        self.enable_extreme_events = enable_extreme_events
        
        # 统计
        self.total_events = 0
        self.event_history: List[NoiseEvent] = []
        
        logger.info(f"🌪️ 市场噪声层已初始化")
        logger.info(f"   流动性冲击: {liquidity_shock_prob:.1%}")
        logger.info(f"   滑点尖峰: {slippage_spike_prob:.1%}")
        logger.info(f"   资金费率跳跃: {funding_jump_prob:.1%}")
        logger.info(f"   订单簿断层: {orderbook_gap_prob:.1%}")
        if enable_extreme_events:
            logger.info(f"   ⚠️ 极端事件已启用")
    
    def apply_noise(self,
                   base_liquidity: float,
                   base_slippage: float,
                   base_funding: float,
                   current_cycle: int = 0) -> Dict:
        """
        对市场参数应用噪声
        
        Args:
            base_liquidity: 基础流动性倍数（1.0=正常）
            base_slippage: 基础滑点率（如0.005=0.5%）
            base_funding: 基础资金费率（如0.0001=0.01%）
            current_cycle: 当前周期（用于记录）
        
        Returns:
            {
                'liquidity': float,      # 调整后的流动性
                'slippage': float,       # 调整后的滑点
                'funding': float,        # 调整后的资金费率
                'events': List[str],     # 发生的事件
                'event_objects': List[NoiseEvent]  # 事件对象（用于统计）
            }
        """
        result = {
            'liquidity': base_liquidity,
            'slippage': base_slippage,
            'funding': base_funding,
            'events': [],
            'event_objects': []
        }
        
        # 1. 流动性冲击
        if random.random() < self.liquidity_shock_prob:
            shock_magnitude = random.uniform(-0.50, -0.20)  # 降低20-50%
            result['liquidity'] *= (1 + shock_magnitude)
            
            event_desc = f"流动性冲击{shock_magnitude:.1%}"
            result['events'].append(event_desc)
            
            event = NoiseEvent(
                event_type='liquidity_shock',
                magnitude=shock_magnitude,
                description=event_desc,
                timestamp=current_cycle
            )
            result['event_objects'].append(event)
            self.event_history.append(event)
            self.total_events += 1
            
            logger.warning(f"   ⚠️ {event_desc}")
        
        # 2. 滑点尖峰
        if random.random() < self.slippage_spike_prob:
            spike_magnitude = random.uniform(2.0, 5.0)  # 2-5倍
            result['slippage'] *= spike_magnitude
            
            event_desc = f"滑点尖峰×{spike_magnitude:.1f}"
            result['events'].append(event_desc)
            
            event = NoiseEvent(
                event_type='slippage_spike',
                magnitude=spike_magnitude,
                description=event_desc,
                timestamp=current_cycle
            )
            result['event_objects'].append(event)
            self.event_history.append(event)
            self.total_events += 1
            
            logger.warning(f"   ⚠️ {event_desc}")
        
        # 3. 资金费率跳跃
        if random.random() < self.funding_jump_prob:
            jump_magnitude = random.uniform(-0.003, 0.003)  # ±0.3%
            result['funding'] += jump_magnitude
            
            event_desc = f"资金费率跳跃{jump_magnitude:+.3%}"
            result['events'].append(event_desc)
            
            event = NoiseEvent(
                event_type='funding_jump',
                magnitude=jump_magnitude,
                description=event_desc,
                timestamp=current_cycle
            )
            result['event_objects'].append(event)
            self.event_history.append(event)
            self.total_events += 1
            
            logger.warning(f"   ⚠️ {event_desc}")
        
        # 4. 订单簿断层
        if random.random() < self.orderbook_gap_prob:
            gap_magnitude = random.uniform(1.5, 3.0)  # 1.5-3倍滑点
            result['slippage'] *= gap_magnitude
            
            event_desc = f"订单簿断层×{gap_magnitude:.1f}"
            result['events'].append(event_desc)
            
            event = NoiseEvent(
                event_type='orderbook_gap',
                magnitude=gap_magnitude,
                description=event_desc,
                timestamp=current_cycle
            )
            result['event_objects'].append(event)
            self.event_history.append(event)
            self.total_events += 1
            
            logger.warning(f"   ⚠️ {event_desc}")
        
        # 5. 极端事件（黑天鹅）
        if self.enable_extreme_events:
            extreme_prob = 0.01  # 1%概率
            if random.random() < extreme_prob:
                # 黑天鹅：所有指标恶化
                result['liquidity'] *= 0.3   # 流动性暴跌70%
                result['slippage'] *= 10.0   # 滑点×10
                result['funding'] += random.choice([-0.01, 0.01])  # ±1%
                
                event_desc = "⚡黑天鹅事件⚡"
                result['events'].append(event_desc)
                
                event = NoiseEvent(
                    event_type='black_swan',
                    magnitude=10.0,
                    description=event_desc,
                    timestamp=current_cycle
                )
                result['event_objects'].append(event)
                self.event_history.append(event)
                self.total_events += 1
                
                logger.error(f"   💀 {event_desc}")
        
        return result
    
    def get_statistics(self) -> Dict:
        """
        获取噪声事件统计
        
        Returns:
            {
                'total_events': int,
                'liquidity_shocks': int,
                'slippage_spikes': int,
                'funding_jumps': int,
                'orderbook_gaps': int,
                'black_swans': int,
                'event_history': List[NoiseEvent]
            }
        """
        stats = {
            'total_events': self.total_events,
            'liquidity_shocks': 0,
            'slippage_spikes': 0,
            'funding_jumps': 0,
            'orderbook_gaps': 0,
            'black_swans': 0,
            'event_history': self.event_history
        }
        
        for event in self.event_history:
            if event.event_type == 'liquidity_shock':
                stats['liquidity_shocks'] += 1
            elif event.event_type == 'slippage_spike':
                stats['slippage_spikes'] += 1
            elif event.event_type == 'funding_jump':
                stats['funding_jumps'] += 1
            elif event.event_type == 'orderbook_gap':
                stats['orderbook_gaps'] += 1
            elif event.event_type == 'black_swan':
                stats['black_swans'] += 1
        
        return stats
    
    def reset_statistics(self):
        """重置统计数据"""
        self.total_events = 0
        self.event_history.clear()
        logger.info("🔄 市场噪声统计已重置")


# ============================================================================
# 辅助函数
# ============================================================================

def create_noise_layer(preset: str = "moderate") -> MarketNoiseLayer:
    """
    创建预设的噪声层
    
    Args:
        preset: 预设类型
            - 'low': 低噪声（适合正常测试）
            - 'moderate': 中等噪声（适合压力测试）
            - 'high': 高噪声（适合极端测试）
            - 'extreme': 极端噪声（包含黑天鹅事件）
    
    Returns:
        MarketNoiseLayer实例
    """
    presets = {
        'low': {
            'liquidity_shock_prob': 0.02,
            'slippage_spike_prob': 0.05,
            'funding_jump_prob': 0.01,
            'orderbook_gap_prob': 0.03,
            'enable_extreme_events': False
        },
        'moderate': {
            'liquidity_shock_prob': 0.05,
            'slippage_spike_prob': 0.10,
            'funding_jump_prob': 0.03,
            'orderbook_gap_prob': 0.08,
            'enable_extreme_events': False
        },
        'high': {
            'liquidity_shock_prob': 0.10,
            'slippage_spike_prob': 0.20,
            'funding_jump_prob': 0.05,
            'orderbook_gap_prob': 0.15,
            'enable_extreme_events': False
        },
        'extreme': {
            'liquidity_shock_prob': 0.15,
            'slippage_spike_prob': 0.25,
            'funding_jump_prob': 0.10,
            'orderbook_gap_prob': 0.20,
            'enable_extreme_events': True
        }
    }
    
    if preset not in presets:
        logger.warning(f"未知预设 '{preset}'，使用 'moderate'")
        preset = 'moderate'
    
    logger.info(f"📦 创建市场噪声层：{preset}模式")
    return MarketNoiseLayer(**presets[preset])

