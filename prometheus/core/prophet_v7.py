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
from typing import Dict, List, Optional
from prometheus.core.bulletin_board import BulletinBoard
from prometheus.core.three_dimension_monitor import ThreeDimensionMonitor
from prometheus.core.experience_db import ExperienceDB

# 使用标准logging
logger = logging.getLogger(__name__)


class ProphetV7:
    """
    Prophet v7.0 - 气象台⭐⭐⭐
    
    只观测，不指挥
    只发布信息，不发布命令
    """
    
    def __init__(
        self, 
        bulletin_board: BulletinBoard,
        experience_db: Optional[ExperienceDB] = None,
        run_id: str = "default"
    ):
        """
        初始化Prophet
        
        Args:
            bulletin_board: 公告板（用于发布信息）
            experience_db: 经验数据库（用于保存系统指标）
            run_id: 运行ID
        """
        self.bulletin_board = bulletin_board
        self.experience_db = experience_db
        self.run_id = run_id
        
        # ===== v7.0核心：三维监控器⭐⭐⭐ =====
        self.three_dim_monitor = ThreeDimensionMonitor(
            window_size=100,
            save_interval=10
        )
        
        # 周期计数器
        self.cycle_count = 0
        
        logger.info("🧘 Prophet v7.0 已初始化")
        logger.info("   职责：自省 + 聆听 + 三维监控")
        logger.info("   输出：繁殖指数 + 压力指数 + 风险等级")
    
    def run_decision_cycle(self):
        """
        Prophet的核心工作⭐⭐⭐
        
        1. 三维异常检测
        2. 计算S（考虑异常）
        3. 计算E
        4. 发布公告
        """
        
        self.cycle_count += 1
        
        # ===== 步骤0：获取必要数据 =====
        world_sig = self.bulletin_board.get('world_signature') or {}
        friction_data = self.bulletin_board.get('friction_data') or {
            'slippage': 0.001,
            'latency_norm': 0.02,
            'fill_rate': 0.98
        }
        death_stats = self.bulletin_board.get('death_stats') or {
            'abnormal_deaths': 0,
            'total_agents': 100
        }
        
        # ===== 步骤1：基础计算 =====
        base_S = self._introspection()
        E = self._listening()
        
        # ===== 步骤2：三维异常检测⭐⭐⭐ =====
        # 先计算Prophet决策（用于保存）
        temp_decision = {
            'S': base_S,
            'E': E,
            'scale': 0.5  # 临时值
        }
        
        anomaly_result = self.three_dim_monitor.monitor_cycle(
            cycle=self.cycle_count,
            run_id=self.run_id,
            world_signature=world_sig,
            friction_data=friction_data,
            death_stats=death_stats,
            prophet_decision=temp_decision,
            experience_db=self.experience_db
        )
        
        # ===== 步骤3：根据异常调整S⭐⭐⭐ =====
        risk_level = anomaly_result['risk_level']
        
        if risk_level == 'safe':
            S = base_S
        elif risk_level == 'warning':
            S = base_S * 0.9  # 一维异常：-10%
        elif risk_level == 'danger':
            S = base_S * 0.7  # 二维异常：-30%
        else:  # critical
            S = 0.2  # 三维异常：强制收缩到20%
        
        # ===== 发布极简公告⭐⭐⭐ =====
        self.bulletin_board.publish('prophet_announcement', {
            # 核心数据（只有两个数字）⭐⭐⭐
            'reproduction_target': S,      # 繁殖指数目标（0-1）
            'pressure_level': abs(E),      # 压力指数（0-1）
            
            # 原始数据（供参考）
            'S': S,
            'E': E,
            
            # v7.0新增：风险等级⭐
            'risk_level': risk_level,
            'anomaly_dims': anomaly_result['total_anomaly_dims'],
            
            # 人话解释
            'message': self._format_message(S, E, risk_level),
            
            # 时间戳
            'timestamp': time.time(),
        })
        
        logger.info(f"📢 Prophet公告已发布:")
        logger.info(f"   繁殖指数目标: {S:.2f} ({S:.0%})")
        logger.info(f"   压力指数: {abs(E):.2f} ({abs(E):.0%})")
        logger.info(f"   风险等级: {risk_level}")
        if anomaly_result['total_anomaly_dims'] > 0:
            logger.warning(f"   ⚠️ 检测到{anomaly_result['total_anomaly_dims']}维异常！")
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
        # 计算各项贡献
        survival_contribution = survival_rate * 0.4
        roi_contribution = avg_roi_normalized * 0.4
        diversity_contribution = diversity * 0.2
        
        S = survival_contribution + roi_contribution + diversity_contribution
        
        # 确保在0-1范围内
        S = max(0, min(1, S))
        
        # ⭐ v7.0增强：详细日志，显示各项贡献
        logger.debug(f"🧘 自省（Introspection）:")
        logger.debug(f"   存活率: {survival_rate:.2%} → 贡献: {survival_contribution:.3f} (40%权重)")
        logger.debug(f"   平均ROI: {avg_roi:.2%} → 贡献: {roi_contribution:.3f} (40%权重)")
        logger.debug(f"   多样性: {diversity:.2%} → 贡献: {diversity_contribution:.3f} (20%权重)")
        logger.debug(f"   → S（繁殖指数）: {S:.2f} = {survival_contribution:.3f} + {roi_contribution:.3f} + {diversity_contribution:.3f}")
        
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
        # 计算各项贡献
        price_contribution = price_change_normalized * 0.5
        volume_contribution = volume_change_normalized * 0.3
        volatility_contribution = volatility_change_normalized * 0.2
        
        E = price_contribution + volume_contribution + volatility_contribution
        
        # 确保在-1到+1范围内
        E = max(-1, min(1, E))
        
        # ⭐ v7.0增强：详细日志，显示各项贡献
        logger.debug(f"👂 聆听（Listening）:")
        logger.debug(f"   价格变化: {price_change:.2%} → 贡献: {price_contribution:+.3f} (50%权重)")
        logger.debug(f"   成交量比: {volume_ratio:.2f} → 贡献: {volume_contribution:+.3f} (30%权重)")
        logger.debug(f"   波动率变化: {volatility_change:.2%} → 贡献: {volatility_contribution:+.3f} (20%权重)")
        logger.debug(f"   → E（趋势值）: {E:+.2f}")
        
        return E
    
    def _format_message(self, S: float, E: float, risk_level: str = 'safe') -> str:
        """
        格式化人话消息⭐
        
        Args:
            S: 繁殖指数
            E: 趋势值
            risk_level: 风险等级
        
        Returns:
            人话解释
        """
        pressure = abs(E)
        
        # 风险等级emoji
        risk_emoji = {
            'safe': '✅',
            'warning': '⚠️',
            'danger': '⚠️⚠️',
            'critical': '🚨🚨🚨'
        }.get(risk_level, '❓')
        
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
        
        # 风险等级说明
        risk_msg = {
            'safe': "正常运行",
            'warning': "一维异常，轻微调整",
            'danger': "二维异常，大幅收缩",
            'critical': "三维异常，紧急逃命！"
        }.get(risk_level, "")
        
        return f"""
{risk_emoji} 风险等级: {risk_level.upper()} - {risk_msg}
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

