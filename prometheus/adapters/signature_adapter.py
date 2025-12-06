"""
WorldSignature适配器

将市场数据转换为WorldSignature，供Agent使用
"""

import numpy as np
from typing import Dict, List, Optional
from collections import deque
import logging

from prometheus.world_signature import (
    MacroCode,
    MicroCode,
    WorldSignature_V2,
    StreamingSignatureGenerator
)
from prometheus.world_signature.macro_code import (
    compute_macro_features,
    discretize_macro,
    tags_to_compact_text as macro_compact,
    embed_macro
)
from prometheus.world_signature.micro_code import (
    compute_micro_features,
    discretize_micro,
    tags_to_compact_text as micro_compact,
    embed_micro
)

logger = logging.getLogger(__name__)


class SignatureAdapter:
    """
    WorldSignature适配器
    
    将回测中的市场数据转换为WorldSignature
    """
    
    def __init__(self, instrument: str = "BTC-USDT"):
        """初始化"""
        self.instrument = instrument
        
        # 使用StreamingSignatureGenerator
        self.generator = StreamingSignatureGenerator(
            instrument=instrument,
            macro_window_hours=1,  # 简化：1小时宏观窗口
            micro_window_minutes=5
        )
        
        logger.info(f"✅ SignatureAdapter初始化完成: {instrument}")
    
    def generate_signature_from_price(
        self,
        current_price: float,
        timestamp: float,
        volume: float = 10.0,
        funding_rate: float = 0.0003,
        open_interest: float = 1000000
    ) -> WorldSignature_V2:
        """
        从价格数据生成WorldSignature
        
        这是简化版本，用于回测中只有价格数据的情况
        """
        # 构造market_data
        spread = current_price * 0.001  # 0.1%价差
        
        market_data = {
            'price': current_price,
            'volume': volume,
            'orderbook': {
                'bids': [[current_price - spread/2, 1.0 + i*0.1] for i in range(10)],
                'asks': [[current_price + spread/2, 1.0 + i*0.1] for i in range(10)]
            },
            'trades': []  # 简化：无交易数据
        }
        
        # 使用generator生成signature
        signature = self.generator.update(
            market_data=market_data,
            funding_rate=funding_rate,
            open_interest=open_interest
        )
        
        return signature
    
    def get_regime_suggestion(self, signature: WorldSignature_V2) -> Dict:
        """
        基于signature提供策略建议
        
        Returns:
            {
                'regime': str,  # regime名称
                'confidence': float,  # 置信度
                'danger': float,  # 危险指数
                'opportunity': float,  # 机会指数
                'suggestion': str  # 策略建议
            }
        """
        # 分析signature
        macro_tags = signature.macro.human_tags
        danger = signature.danger_index
        opportunity = signature.opportunity_index
        novelty = signature.novelty_score
        
        # 判断regime类型（基于macro tags）
        regime = self._infer_regime(macro_tags)
        
        # 生成建议
        if danger > 0.7:
            suggestion = "defensive"  # 防守
        elif opportunity > 0.7:
            suggestion = "aggressive"  # 进攻
        elif novelty > 0.8:
            suggestion = "cautious"  # 谨慎
        else:
            suggestion = "balanced"  # 平衡
        
        return {
            'regime': regime,
            'confidence': signature.regime_confidence,
            'danger': danger,
            'opportunity': opportunity,
            'novelty': novelty,
            'suggestion': suggestion,
            'macro_tags': macro_tags
        }
    
    def _infer_regime(self, macro_tags: List[str]) -> str:
        """根据macro tags推断regime"""
        tags_str = ' '.join(macro_tags)
        
        # 检查趋势
        if 'STRONG_UP' in tags_str or 'trend:UP' in tags_str:
            if 'vol:HIGH' in tags_str:
                return "volatile_bull"  # 高波牛市
            else:
                return "steady_bull"  # 稳定牛市
        elif 'STRONG_DOWN' in tags_str or 'trend:DOWN' in tags_str:
            if 'vol:HIGH' in tags_str:
                return "crash_bear"  # 暴跌熊市
            else:
                return "steady_bear"  # 稳定熊市
        elif 'vol:HIGH' in tags_str:
            return "high_volatility"  # 高波震荡
        elif 'vol:LOW' in tags_str:
            return "low_volatility"  # 低波盘整
        else:
            return "sideways"  # 震荡
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.generator.statistics()


class RegimeAwareAgent:
    """
    Regime感知Agent
    
    能够根据WorldSignature调整策略的Agent
    """
    
    def __init__(self, agent_id: str, capital: float, signature_adapter: SignatureAdapter):
        """初始化"""
        self.agent_id = agent_id
        self.capital = capital
        self.position = 0.0
        self.entry_price = 0.0
        self.is_alive = True
        self.signature_adapter = signature_adapter
        
        # Agent特性（基因）
        self.risk_tolerance = np.random.uniform(0.3, 0.9)  # 风险承受度
        self.trend_following = np.random.uniform(0.0, 1.0)  # 趋势跟随倾向
        self.contrarian = 1.0 - self.trend_following  # 逆向交易倾向
    
    def make_decision(
        self,
        current_price: float,
        signature: WorldSignature_V2
    ) -> str:
        """
        基于WorldSignature做决策（优化版）
        
        Returns:
            'hold', 'long', 'short', 'close'
        """
        # 获取regime建议
        suggestion = self.signature_adapter.get_regime_suggestion(signature)
        
        regime = suggestion['regime']
        danger = suggestion['danger']
        opportunity = suggestion['opportunity']
        
        # 个性化danger阈值（基于风险承受度）
        danger_threshold = 0.7 + (1.0 - self.risk_tolerance) * 0.2  # 0.7-0.9
        
        # 极端危险才强制平仓
        if danger > danger_threshold:
            if self.position != 0:
                return 'close'  # 平仓
            else:
                return 'hold'  # 持币观望
        
        # 根据regime和Agent特性决策
        if regime in ['steady_bull', 'volatile_bull']:
            # 牛市
            if self.trend_following > 0.5:
                # 趋势跟随者：做多并持有
                if self.position == 0:
                    return 'long'
                elif self.position > 0:
                    return 'hold'  # 持有多单
                else:
                    return 'close'  # 平空单
            else:
                # 逆向交易者：谨慎
                if self.position < 0:
                    return 'close'  # 平空
                return 'hold'
        
        elif regime in ['crash_bear', 'steady_bear']:
            # 熊市
            if self.trend_following > 0.5:
                # 趋势跟随者：做空并持有
                if self.position == 0:
                    return 'short'
                elif self.position < 0:
                    return 'hold'  # 持有空单
                else:
                    return 'close'  # 平多单
            else:
                # 逆向交易者：谨慎
                if self.position > 0:
                    return 'close'  # 平多
                return 'hold'
        
        elif regime == 'high_volatility':
            # 高波震荡：看机会
            if opportunity > 0.6:
                if self.position == 0:
                    # 根据Agent特性选择方向
                    if self.trend_following > 0.5:
                        return 'long'  # 偏多
                    else:
                        return 'short'  # 偏空
                else:
                    return 'hold'  # 持仓等待
            elif opportunity < 0.3:
                # 机会不足，平仓
                if self.position != 0:
                    return 'close'
                return 'hold'
            else:
                return 'hold'
        
        else:
            # 其他情况：中性策略
            if opportunity > 0.7:
                # 高机会，开仓
                if self.position == 0:
                    return 'long' if np.random.rand() > 0.5 else 'short'
            elif danger < 0.3 and self.position == 0:
                # 低危险，可以尝试
                return 'long' if self.trend_following > 0.5 else 'short'
            
            return 'hold'
    
    def update_pnl(self, current_price: float, prev_price: float):
        """更新盈亏"""
        if self.position != 0:
            pnl = self.position * (current_price - prev_price)
            self.capital += pnl
            
            # 爆仓检查
            if self.capital < 100:  # 最小资金
                self.is_alive = False


def create_regime_aware_backtest(
    prices: np.ndarray,
    num_agents: int = 50,
    initial_capital: float = 500000
) -> Dict:
    """
    运行Regime感知回测
    
    Args:
        prices: 价格序列
        num_agents: Agent数量
        initial_capital: 初始资金
    
    Returns:
        回测结果
    """
    # 创建adapter
    adapter = SignatureAdapter()
    
    # 创建Agents
    agents = [
        RegimeAwareAgent(
            agent_id=f"agent_{i}",
            capital=initial_capital / num_agents,
            signature_adapter=adapter
        )
        for i in range(num_agents)
    ]
    
    # 逐日回测
    for day, price in enumerate(prices[1:], 1):
        prev_price = prices[day - 1]
        
        # 生成signature
        signature = adapter.generate_signature_from_price(
            current_price=price,
            timestamp=day * 86400.0,
            volume=10.0
        )
        
        # 每个Agent决策
        for agent in agents:
            if not agent.is_alive:
                continue
            
            # 做决策
            decision = agent.make_decision(price, signature)
            
            # 执行决策
            if decision == 'long' and agent.position == 0:
                # 开多
                agent.position = agent.capital * 0.1 / price
                agent.entry_price = price
            
            elif decision == 'short' and agent.position == 0:
                # 开空
                agent.position = -agent.capital * 0.1 / price
                agent.entry_price = price
            
            elif decision == 'close' and agent.position != 0:
                # 平仓
                pnl = agent.position * (price - agent.entry_price)
                agent.capital += pnl
                agent.position = 0
                agent.entry_price = 0
            
            # 更新盈亏
            agent.update_pnl(price, prev_price)
    
    # 统计结果
    survivors = [a for a in agents if a.is_alive]
    total_capital = sum(a.capital for a in survivors)
    
    roi = (total_capital / initial_capital - 1) * 100
    market_roi = (prices[-1] / prices[0] - 1) * 100
    
    return {
        'survivors': len(survivors),
        'total_capital': total_capital,
        'roi': roi,
        'market_roi': market_roi,
        'agents': agents
    }

