"""
网络延迟模拟器

为Agent交易提供真实的网络延迟模拟：
- 订单提交延迟
- 市场数据延迟  
- 订单确认延迟

Author: Prometheus Team
Version: v5.3
Date: 2025-12-06
"""

import time
import random
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NetworkStats:
    """网络延迟统计"""
    total_delays: int = 0
    total_time_seconds: float = 0.0
    order_delays: int = 0
    market_data_delays: int = 0
    confirmation_delays: int = 0
    
    @property
    def avg_delay_ms(self) -> float:
        """平均延迟（毫秒）"""
        if self.total_delays == 0:
            return 0.0
        return (self.total_time_seconds / self.total_delays) * 1000


class NetworkSimulator:
    """
    简单网络延迟模拟器
    
    用于v5.3阶段2.1-2.2，模拟基础网络延迟
    不包含丢包、重传等复杂逻辑（未来可扩展）
    
    特点：
    - 基础延迟 + 随机抖动
    - 高峰时段倍数
    - 可启用/禁用
    - 统计收集
    """
    
    def __init__(self, 
                 enabled: bool = True,
                 base_latency_ms: float = 30.0,
                 jitter_ms: float = 10.0,
                 peak_hour_multiplier: float = 1.0):
        """
        初始化网络模拟器
        
        Args:
            enabled: 是否启用延迟模拟
            base_latency_ms: 基础延迟（毫秒）
            jitter_ms: 延迟抖动范围（±毫秒）
            peak_hour_multiplier: 高峰时段延迟倍数
        """
        self.enabled = enabled
        self.base_latency = base_latency_ms / 1000  # 转换为秒
        self.jitter = jitter_ms / 1000
        self.peak_multiplier = peak_hour_multiplier
        
        self.stats = NetworkStats()
        
        if enabled:
            logger.info(f"🌐 网络模拟器已启用")
            logger.info(f"   基础延迟: {base_latency_ms:.1f}ms")
            logger.info(f"   延迟抖动: ±{jitter_ms:.1f}ms")
            logger.info(f"   高峰倍数: {peak_hour_multiplier:.1f}x")
        else:
            logger.info(f"🌐 网络模拟器已禁用（零延迟模式）")
    
    def simulate_order_delay(self, execute: bool = True) -> float:
        """
        模拟订单提交延迟
        
        Args:
            execute: 是否实际执行延迟（time.sleep）
            
        Returns:
            延迟时间（秒）
        """
        if not self.enabled:
            return 0.0
        
        # 计算延迟：基础 + 随机抖动 + 高峰倍数
        delay = self.base_latency + random.uniform(-self.jitter, self.jitter)
        delay *= self.peak_multiplier
        delay = max(0.001, delay)  # 至少1ms
        
        # 更新统计
        self.stats.total_delays += 1
        self.stats.order_delays += 1
        self.stats.total_time_seconds += delay
        
        # 执行延迟
        if execute:
            time.sleep(delay)
        
        return delay
    
    def simulate_market_data_delay(self, execute: bool = True) -> float:
        """
        模拟市场数据延迟（通常比订单快）
        
        Args:
            execute: 是否实际执行延迟
            
        Returns:
            延迟时间（秒）
        """
        if not self.enabled:
            return 0.0
        
        # 市场数据延迟约为订单延迟的30%
        delay = (self.base_latency * 0.3) + random.uniform(-self.jitter * 0.3, self.jitter * 0.3)
        delay = max(0.001, delay)
        
        # 更新统计
        self.stats.total_delays += 1
        self.stats.market_data_delays += 1
        self.stats.total_time_seconds += delay
        
        # 执行延迟
        if execute:
            time.sleep(delay)
        
        return delay
    
    def simulate_confirmation_delay(self, execute: bool = True) -> float:
        """
        模拟订单确认延迟（通常比订单慢）
        
        Args:
            execute: 是否实际执行延迟
            
        Returns:
            延迟时间（秒）
        """
        if not self.enabled:
            return 0.0
        
        # 确认延迟约为订单延迟的2倍
        delay = (self.base_latency * 2.0) + random.uniform(-self.jitter, self.jitter)
        delay *= self.peak_multiplier
        delay = max(0.001, delay)
        
        # 更新统计
        self.stats.total_delays += 1
        self.stats.confirmation_delays += 1
        self.stats.total_time_seconds += delay
        
        # 执行延迟
        if execute:
            time.sleep(delay)
        
        return delay
    
    def set_peak_hour(self, is_peak: bool):
        """
        设置是否为高峰时段
        
        Args:
            is_peak: True表示高峰时段，延迟会增加
        """
        old_multiplier = self.peak_multiplier
        self.peak_multiplier = 3.0 if is_peak else 1.0
        
        if old_multiplier != self.peak_multiplier:
            status = "进入" if is_peak else "退出"
            logger.debug(f"🌐 {status}高峰时段 | 延迟倍数: {old_multiplier:.1f}x → {self.peak_multiplier:.1f}x")
    
    def get_stats(self) -> Dict:
        """
        获取网络延迟统计
        
        Returns:
            包含统计信息的字典
        """
        return {
            'enabled': self.enabled,
            'total_delays': self.stats.total_delays,
            'total_time_seconds': self.stats.total_time_seconds,
            'avg_delay_ms': self.stats.avg_delay_ms,
            'order_delays': self.stats.order_delays,
            'market_data_delays': self.stats.market_data_delays,
            'confirmation_delays': self.stats.confirmation_delays,
            'base_latency_ms': self.base_latency * 1000,
            'jitter_ms': self.jitter * 1000,
            'peak_multiplier': self.peak_multiplier
        }
    
    def reset_stats(self):
        """重置统计数据"""
        self.stats = NetworkStats()
        logger.debug("🌐 网络统计已重置")
    
    def __repr__(self) -> str:
        """字符串表示"""
        if not self.enabled:
            return "NetworkSimulator(disabled)"
        
        return (f"NetworkSimulator("
                f"latency={self.base_latency*1000:.1f}ms, "
                f"jitter=±{self.jitter*1000:.1f}ms, "
                f"peak={self.peak_multiplier:.1f}x)")


# ============================================
# 测试代码
# ============================================

def test_network_simulator():
    """测试网络模拟器"""
    print("="*70)
    print("🧪 网络延迟模拟器测试")
    print("="*70)
    
    # 创建模拟器
    network = NetworkSimulator(
        enabled=True,
        base_latency_ms=30,
        jitter_ms=10,
        peak_hour_multiplier=1.0
    )
    
    print(f"\n📊 配置: {network}")
    
    # 测试订单延迟
    print(f"\n1️⃣ 测试订单延迟（10次）")
    order_delays = []
    for i in range(10):
        start = time.time()
        delay = network.simulate_order_delay(execute=True)
        actual = time.time() - start
        order_delays.append(delay * 1000)
        print(f"   第{i+1}次: {delay*1000:.2f}ms (实际: {actual*1000:.2f}ms)")
    
    print(f"   平均: {sum(order_delays)/len(order_delays):.2f}ms")
    print(f"   范围: {min(order_delays):.2f}ms - {max(order_delays):.2f}ms")
    
    # 测试市场数据延迟
    print(f"\n2️⃣ 测试市场数据延迟（10次）")
    data_delays = []
    for i in range(10):
        delay = network.simulate_market_data_delay(execute=False)
        data_delays.append(delay * 1000)
        print(f"   第{i+1}次: {delay*1000:.2f}ms")
    
    print(f"   平均: {sum(data_delays)/len(data_delays):.2f}ms")
    
    # 测试确认延迟
    print(f"\n3️⃣ 测试确认延迟（10次）")
    confirm_delays = []
    for i in range(10):
        delay = network.simulate_confirmation_delay(execute=False)
        confirm_delays.append(delay * 1000)
        print(f"   第{i+1}次: {delay*1000:.2f}ms")
    
    print(f"   平均: {sum(confirm_delays)/len(confirm_delays):.2f}ms")
    
    # 测试高峰时段
    print(f"\n4️⃣ 测试高峰时段（延迟×3）")
    network.set_peak_hour(True)
    peak_delays = []
    for i in range(5):
        delay = network.simulate_order_delay(execute=False)
        peak_delays.append(delay * 1000)
        print(f"   第{i+1}次: {delay*1000:.2f}ms")
    
    print(f"   平均: {sum(peak_delays)/len(peak_delays):.2f}ms")
    
    # 退出高峰
    network.set_peak_hour(False)
    
    # 统计
    print(f"\n📊 统计信息:")
    stats = network.get_stats()
    print(f"   总延迟次数: {stats['total_delays']}")
    print(f"   总延迟时间: {stats['total_time_seconds']:.3f}秒")
    print(f"   平均延迟: {stats['avg_delay_ms']:.2f}ms")
    print(f"   订单延迟: {stats['order_delays']}次")
    print(f"   市场数据延迟: {stats['market_data_delays']}次")
    print(f"   确认延迟: {stats['confirmation_delays']}次")
    
    print(f"\n✅ 测试完成！")
    print("="*70)


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    test_network_simulator()

