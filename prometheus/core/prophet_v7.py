"""
Prometheus v7.0 - Prophet核心模块

🎯 Prophet = 气象台，不是指挥官⭐⭐⭐

职责：
  1. 自省（Introspection）：计算S（繁殖指数）
  2. 聆听（Listening）：计算E（趋势值）
  3. 发布2个数字到BulletinBoard

不做的事：
  ❌ 不预测市场方向
  ❌ 不指导交易
  ❌ 不输出买/卖指令

核心哲学：
  Prophet只观测，不指挥
  就像气象台只报告天气，不指挥你穿什么

代码：20行核心代码⭐⭐⭐
"""

import time
import logging
from typing import Dict, List
from prometheus.core.bulletin_board import BulletinBoard

# 使用标准logging
logger = logging.getLogger(__name__)


class ProphetV7:
    """
    Prophet v7.0 - 气象台⭐⭐⭐
    
    只观测，不指挥
    只发布信息，不发布命令
    """
    
    def __init__(self, bulletin_board: BulletinBoard):
        """
        初始化Prophet
        
        Args:
            bulletin_board: 公告板（用于发布信息）
        """
        self.bulletin_board = bulletin_board
        
        logger.info("🧘 Prophet v7.0 已初始化")
        logger.info("   职责：自省 + 聆听")
        logger.info("   输出：繁殖指数 + 压力指数")
    
    def run_decision_cycle(self):
        """
        Prophet的唯一工作⭐⭐⭐
        
        1. 计算两个指数
        2. 发布公告
        
        就这么简单！
        """
        
        # ===== 能力1：自省⭐ =====
        # 向内看：我现在活得好不好？
        S = self._introspection()
        
        # ===== 能力2：聆听⭐ =====
        # 向外听：世界在告诉我什么？
        E = self._listening()
        
        # ===== 发布极简公告⭐⭐⭐ =====
        self.bulletin_board.publish('prophet_announcement', {
            # 核心数据（只有两个数字）⭐⭐⭐
            'reproduction_target': S,      # 繁殖指数目标（0-1）
            'pressure_level': abs(E),      # 压力指数（0-1）
            
            # 原始数据（供参考）
            'S': S,
            'E': E,
            
            # 人话解释
            'message': self._format_message(S, E),
            
            # 时间戳
            'timestamp': time.time(),
        })
        
        logger.info(f"📢 Prophet公告已发布:")
        logger.info(f"   繁殖指数目标: {S:.2f} ({S:.0%})")
        logger.info(f"   压力指数: {abs(E):.2f} ({abs(E):.0%})")
        logger.info(f"   → Moirai和Agent，根据这个信息自主决策！⭐")
    
    def _introspection(self) -> float:
        """
        自省（Introspection）⭐
        
        向内观：我现在和市场匹配吗？
        
        计算繁殖指数（S）：
          S = 系统与市场的当前匹配度
          S高 → Agent活得好 → 系统与市场匹配
          S低 → Agent死得多 → 系统与市场不匹配
        
        Returns:
            S（繁殖指数，0-1）
        """
        
        # ===== 从Moirai获取种群状态 =====
        moirai_report = self.bulletin_board.get('moirai_report')
        
        if not moirai_report:
            # 如果还没有报告，返回中性值
            logger.warning("⚠️ 未找到Moirai报告，使用默认值")
            return 0.5
        
        # ===== 核心指标⭐⭐⭐ =====
        
        # 1. 存活率（Agent活得好不好）
        survival_rate = moirai_report.get('survival_rate', 0.5)
        
        # 2. 平均ROI（Agent赚不赚钱）
        avg_roi = moirai_report.get('avg_roi', 0.0)
        # ROI归一化到0-1（假设ROI范围-100%到+100%）
        avg_roi_normalized = (avg_roi + 1.0) / 2.0
        avg_roi_normalized = max(0, min(1, avg_roi_normalized))
        
        # 3. 基因多样性（种群是否健康）
        diversity = moirai_report.get('diversity', 0.5)
        
        # ===== 计算S（繁殖指数）⭐⭐⭐ =====
        S = (
            survival_rate * 0.4 +          # 存活率权重40%
            avg_roi_normalized * 0.4 +     # ROI权重40%
            diversity * 0.2                # 多样性权重20%
        )
        
        # 确保在0-1范围内
        S = max(0, min(1, S))
        
        logger.debug(f"🧘 自省（Introspection）:")
        logger.debug(f"   存活率: {survival_rate:.2f}")
        logger.debug(f"   平均ROI: {avg_roi:.2%} → {avg_roi_normalized:.2f}")
        logger.debug(f"   多样性: {diversity:.2f}")
        logger.debug(f"   → S（繁殖指数）: {S:.2f}")
        
        return S
    
    def _listening(self) -> float:
        """
        聆听（Listening）⭐
        
        向外听：市场在如何变化？
        
        计算趋势值（E）：
          E = 市场变化对匹配度的影响
          E > 0 → 市场变化有利于当前系统（匹配度上升）
          E < 0 → 市场变化不利于当前系统（匹配度下降）
        
        Returns:
            E（趋势值，-1 to +1）
        """
        
        # ===== 从BulletinBoard获取市场数据 =====
        world_sig = self.bulletin_board.get('world_signature')
        
        if not world_sig:
            logger.warning("⚠️ 未找到WorldSignature，使用默认值")
            return 0.0
        
        # ===== 核心指标⭐⭐⭐ =====
        
        # 1. 价格变化（最重要）
        price_change = world_sig.get('price_change_24h', 0.0)
        # 归一化到-1到+1（假设日变化范围-50%到+50%）
        price_change_normalized = max(-1, min(1, price_change / 0.5))
        
        # 2. 成交量变化（次要）
        volume_ratio = world_sig.get('volume_ratio', 1.0)
        # 归一化（成交量倍数，0.5-2.0 → -1到+1）
        volume_change_normalized = max(-1, min(1, (volume_ratio - 1.0) / 1.0))
        
        # 3. 波动率变化（辅助）
        volatility_24h = world_sig.get('volatility_24h', 0.0)
        volatility_change = world_sig.get('volatility_change', 0.0)
        # 归一化
        volatility_change_normalized = max(-1, min(1, volatility_change / 0.1))
        
        # ===== 计算E（趋势值）⭐⭐⭐ =====
        E = (
            price_change_normalized * 0.5 +      # 价格变化权重50%
            volume_change_normalized * 0.3 +     # 成交量变化权重30%
            volatility_change_normalized * 0.2   # 波动率变化权重20%
        )
        
        # 确保在-1到+1范围内
        E = max(-1, min(1, E))
        
        logger.debug(f"👂 聆听（Listening）:")
        logger.debug(f"   价格变化: {price_change:.2%} → {price_change_normalized:.2f}")
        logger.debug(f"   成交量比: {volume_ratio:.2f} → {volume_change_normalized:.2f}")
        logger.debug(f"   波动率变化: {volatility_change:.2%} → {volatility_change_normalized:.2f}")
        logger.debug(f"   → E（趋势值）: {E:.2f}")
        
        return E
    
    def _format_message(self, S: float, E: float) -> str:
        """
        格式化人话消息⭐
        
        Args:
            S: 繁殖指数
            E: 趋势值
        
        Returns:
            人话解释
        """
        pressure = abs(E)
        
        # 繁殖指数解释
        if S > 0.7:
            repro_msg = "扩张（繁殖指数高）"
            repro_emoji = "🚀"
        elif S > 0.4:
            repro_msg = "维持（繁殖指数中等）"
            repro_emoji = "😐"
        else:
            repro_msg = "收缩（繁殖指数低）"
            repro_emoji = "📉"
        
        # 压力指数解释
        if pressure > 0.4:
            pressure_msg = "高压（快速执行）"
            pressure_emoji = "⚡"
        elif pressure > 0.2:
            pressure_msg = "中压（正常执行）"
            pressure_emoji = "🔄"
        else:
            pressure_msg = "低压（缓慢执行）"
            pressure_emoji = "🐌"
        
        # 市场变化解释
        if E > 0.1:
            market_msg = "市场向好"
        elif E < -0.1:
            market_msg = "市场变坏"
        else:
            market_msg = "市场稳定"
        
        return f"""
{repro_emoji} 繁殖指数目标: {S:.0%} - {repro_msg}
{pressure_emoji} 压力指数: {pressure:.0%} - {pressure_msg}
📊 市场状态: {market_msg} (E = {E:+.2f})

系统应该{'扩张' if S > 0.6 else '维持' if S > 0.4 else '收缩'}到{S:.0%}规模
{'快速' if pressure > 0.4 else '正常' if pressure > 0.2 else '缓慢'}执行

Moirai和Agent们，根据这个信息自主决策！⭐
"""


if __name__ == "__main__":
    """
    简单测试
    """
    from prometheus.core.bulletin_board import BulletinBoard
    
    # 创建BulletinBoard
    bb = BulletinBoard()
    
    # 模拟Moirai报告
    bb.publish('moirai_report', {
        'survival_rate': 0.75,
        'avg_roi': 0.20,
        'diversity': 0.65,
    })
    
    # 模拟WorldSignature
    bb.publish('world_signature', {
        'price_change_24h': 0.08,
        'volume_ratio': 1.5,
        'volatility_24h': 0.05,
        'volatility_change': 0.01,
    })
    
    # 创建Prophet
    prophet = ProphetV7(bb)
    
    # 运行决策周期
    prophet.run_decision_cycle()
    
    # 查看结果
    announcement = bb.get('prophet_announcement')
    print("\n" + "="*50)
    print("📢 Prophet公告:")
    print("="*50)
    print(announcement['message'])
    print("="*50)

