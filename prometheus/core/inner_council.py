"""
Daimon (Inner Council) - Agent的守护神决策系统
=============================================

Daimon是Agent的"内在声音"，综合多种因素进行决策。

设计哲学（来自苏格拉底的Daimon）：
- 守护神不是外部神灵，而是内在智慧
- 在关键时刻提供指引
- 理性与直觉的结合

决策机制：五个"声音"投票
1. Instinct Voice（本能声音）：死亡恐惧、损失厌恶等
2. Genome Voice（基因声音）：genome参数偏好
3. Experience Voice（经验声音）：个人记忆中的模式
4. Emotion Voice（情绪声音）：despair/fear/confidence
5. Market Voice（市场声音）：先知预言、技术指标

v5.0版本：无记忆，纯函数式决策
v5.1+：增加记忆和反馈学习
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
import logging
import random  # v5.2: 用于探索性决策

logger = logging.getLogger(__name__)


@dataclass
class Vote:
    """
    单个投票
    
    Attributes:
        action: 建议的行动 (buy/sell/hold/close/short/cover)
        confidence: 信心水平 (0-1)
        voter_category: 投票者类别 (instinct/genome/experience/emotion/market)
        reason: 投票理由
    """
    action: str
    confidence: float
    voter_category: str
    reason: str
    
    def __post_init__(self):
        """验证投票数据"""
        assert self.action in ['buy', 'sell', 'hold', 'close', 'short', 'cover'], \
            f"Invalid action: {self.action}"
        assert 0 <= self.confidence <= 1, f"Confidence must be in [0, 1]: {self.confidence}"


@dataclass
class CouncilDecision:
    """
    议会决策结果
    
    Attributes:
        action: 最终决策的行动
        confidence: 决策信心 (0-1)
        reasoning: 决策推理（自然语言）
        all_votes: 所有投票记录
        weights_used: 使用的权重配置
        context_snapshot: 决策时的上下文快照（用于调试）
    """
    action: str
    confidence: float
    reasoning: str
    all_votes: List[Vote] = field(default_factory=list)
    weights_used: Dict[str, float] = field(default_factory=dict)
    context_snapshot: Dict = field(default_factory=dict)


class Daimon:
    """
    守护神 - Agent的决策中枢
    
    v5.1版本特点：
    - 无记忆（纯函数式）
    - 权重从元基因组读取（可遗传）✨
    - 六个"声音"投票机制
    """
    
    def __init__(self, agent: 'AgentV5'):
        """
        初始化守护神
        
        Args:
            agent: 所属的Agent对象
        """
        self.agent = agent
        
        # v5.1: 权重从元基因组读取（可遗传！）
        if hasattr(agent, 'meta_genome') and agent.meta_genome is not None:
            self.base_weights = agent.meta_genome.get_daimon_weights()
        else:
            # 向后兼容：默认权重
            self.base_weights = {
                'instinct': 1.0,          # 本能权重最高（死亡恐惧）
                'world_signature': 0.8,   # ✨ v5.5+：世界感知（环境认知）
                'experience': 0.7,        # 经验次之（历史教训）
                'prophecy': 0.6,          # 先知预言（战略指导）
                'strategy': 0.5,          # 策略分析（战术分析）
                'genome': 0.5,            # 基因偏好（个性倾向）
                'emotion': 0.3,           # 情绪权重最低（易受干扰）
            }
    
    # ==================== 主决策流程 ====================
    
    def guide(self, context: Dict) -> CouncilDecision:
        """
        守护神的指引 - 核心决策方法
        
        Args:
            context: 决策上下文，包含：
                - market_data: 市场数据
                - bulletins: 公告板信息
                - capital: 当前资金
                - capital_ratio: 资金比率
                - position: 当前持仓
                - recent_pnl: 最近盈亏
                - consecutive_losses: 连续亏损次数
                - personal_stats: 个人统计（如果有PersonalInsights）
                - world_signature: WorldSignature（v5.5+新增）✨
        
        Returns:
            CouncilDecision: 决策结果
        """
        # 收集所有"声音"的投票（v5.5+：7个声音）
        all_votes = []
        all_votes.extend(self._instinct_voice(context))
        all_votes.extend(self._genome_voice(context))
        all_votes.extend(self._experience_voice(context))
        all_votes.extend(self._emotion_voice(context))
        all_votes.extend(self._strategy_voice(context))   # 策略分析（战术）
        all_votes.extend(self._prophecy_voice(context))   # 先知预言（战略）
        all_votes.extend(self._world_signature_voice(context))  # ✨ v5.5+：世界感知！
        
        # 如果没有任何投票，默认hold
        if not all_votes:
            return CouncilDecision(
                action='hold',
                confidence=0.5,
                reasoning="无明确信号，保持观望",
                all_votes=[],
                weights_used=self.base_weights.copy(),
                context_snapshot=context.copy(),
            )
        
        # v5.2：增强可见性 - 显示各个声音的投票
        votes_by_category = {}
        for vote in all_votes:
            cat = vote.voter_category
            if cat not in votes_by_category:
                votes_by_category[cat] = []
            votes_by_category[cat].append(vote)
        
        # 特别记录本能的投票（最重要）
        if 'instinct' in votes_by_category:
            instinct_votes = votes_by_category['instinct']
            logger.debug(
                f"   🧬 本能投票: {len(instinct_votes)}票 | "
                f"数值:[{self.agent.instinct.describe_instinct_values()}] | "
                f"性格:{self.agent.instinct.describe_personality()}"
            )
            for vote in instinct_votes:
                logger.debug(f"      → {vote.action}({vote.confidence:.0%}): {vote.reason}")
        
        # 加权汇总投票
        decision = self._tally_votes(all_votes, context)
        
        # 生成推理
        decision.reasoning = self._generate_reasoning(all_votes, decision.action)
        decision.all_votes = all_votes
        decision.weights_used = self.base_weights.copy()
        decision.context_snapshot = context.copy()
        
        return decision
    
    # ==================== 五个"声音" ====================
    
    def _instinct_voice(self, context: Dict) -> List[Vote]:
        """
        本能声音：基于Agent的本能做出判断
        
        本能影响：
        1. 死亡恐惧：资金低时强烈要求平仓
        2. 损失厌恶：亏损时倾向止损
        3. 风险偏好：影响开仓倾向
        """
        votes = []
        instinct = self.agent.instinct
        
        capital_ratio = context.get('capital_ratio', 1.0)
        recent_pnl = context.get('recent_pnl', 0)
        consecutive_losses = context.get('consecutive_losses', 0)
        position = context.get('position', {})
        has_position = position.get('amount', 0) != 0
        
        # 1. 死亡恐惧（v5.2改进：动态阈值，更激进）
        fear_level = instinct.calculate_death_fear_level(capital_ratio, consecutive_losses)
        # v5.2: 根据fear_of_death动态调整阈值（改进版：差异更大）
        fear_threshold = 3.0 - instinct.fear_of_death * 1.5
        # 高恐惧(1.8): threshold=0.3 → 极易触发（资金<85%就平仓）
        # 低恐惧(0.3): threshold=2.55 → 极难触发（资金<15%才平仓）
        
        if fear_level > fear_threshold and has_position:
            # 高度恐惧 + 持仓 → 强烈要求平仓
            votes.append(Vote(
                action='close',
                confidence=min(fear_level / 3.0, 0.95),
                voter_category='instinct',
                reason=f"死亡恐惧({fear_level:.1f}>阈值{fear_threshold:.1f}): 资金仅剩{capital_ratio:.1%}"
            ))
        elif fear_level > fear_threshold * 0.7 and not has_position:
            # 中度恐惧 + 无仓 → 观望
            votes.append(Vote(
                action='hold',
                confidence=0.7,
                voter_category='instinct',
                reason=f"死亡恐惧({fear_level:.1f}): 谨慎观望"
            ))
        
        # 2. 损失厌恶
        if recent_pnl < -0.05 and has_position:
            # 亏损超过5% → 损失厌恶触发
            loss_aversion_strength = instinct.loss_aversion
            votes.append(Vote(
                action='close',
                confidence=loss_aversion_strength * 0.8,
                voter_category='instinct',
                reason=f"损失厌恶({loss_aversion_strength:.1%}): 及时止损(亏{recent_pnl:.1%})"
            ))
        
        # 3. 风险偏好（v5.2改进：增强探索性开仓）
        if not has_position and capital_ratio > 0.5:  # v5.2: 降低资金门槛到50%
            # 无仓时，风险偏好影响开仓倾向
            if instinct.risk_appetite > 0.6:  # v5.2: 降低门槛到60%
                # 高风险偏好 → 主动探索开仓
                # v5.2: 随机选择方向，增加多样性
                action = random.choice(['buy', 'sell'])
                votes.append(Vote(
                    action=action,
                    confidence=instinct.risk_appetite * 0.7,  # v5.2: 提高confidence到0.7
                    voter_category='instinct',
                    reason=f"风险偏好({instinct.risk_appetite:.1%}): 探索性{action}"
                ))
            elif instinct.risk_appetite < 0.3:
                # 低风险偏好 → 倾向观望
                votes.append(Vote(
                    action='hold',
                    confidence=(1 - instinct.risk_appetite) * 0.6,
                    voter_category='instinct',
                    reason=f"风险偏好({instinct.risk_appetite:.1%}): 保守观望"
                ))
        
        return votes
    
    def _genome_voice(self, context: Dict) -> List[Vote]:
        """
        基因声音：基于Agent的genome参数做出判断
        
        genome影响：
        - trend_pref: 趋势偏好（是否喜欢顺势交易）
        - mean_reversion: 均值回归偏好
        - patience: 耐心（影响持仓时间）
        """
        votes = []
        genome = self.agent.genome
        
        # 获取genome中的关键参数
        active_params = genome.active_params
        
        # 1. 趋势偏好
        trend_pref = active_params.get('trend_pref', 0.5)
        market_trend = context.get('market_data', {}).get('trend', 'neutral')
        
        if trend_pref > 0.6:
            # 高趋势偏好 → 顺势交易
            if market_trend == 'bullish':
                votes.append(Vote(
                    action='buy',
                    confidence=trend_pref * 0.6,
                    voter_category='genome',
                    reason=f"趋势偏好({trend_pref:.1%}): 顺势做多"
                ))
            elif market_trend == 'bearish':
                votes.append(Vote(
                    action='sell',
                    confidence=trend_pref * 0.6,
                    voter_category='genome',
                    reason=f"趋势偏好({trend_pref:.1%}): 顺势做空"
                ))
        
        # 2. 均值回归偏好
        mean_reversion = active_params.get('mean_reversion', 0.5)
        price_deviation = context.get('market_data', {}).get('price_deviation', 0)
        
        if mean_reversion > 0.6 and abs(price_deviation) > 0.05:
            # 高均值回归偏好 + 价格偏离 → 反向交易
            if price_deviation > 0:  # 价格过高
                votes.append(Vote(
                    action='sell',
                    confidence=mean_reversion * 0.5,
                    voter_category='genome',
                    reason=f"均值回归({mean_reversion:.1%}): 价格过高"
                ))
            else:  # 价格过低
                votes.append(Vote(
                    action='buy',
                    confidence=mean_reversion * 0.5,
                    voter_category='genome',
                    reason=f"均值回归({mean_reversion:.1%}): 价格过低"
                ))
        
        # 3. 耐心
        patience = active_params.get('patience', 0.5)
        position = context.get('position', {})
        has_position = position.get('amount', 0) != 0
        holding_periods = context.get('holding_periods', 0)
        
        if patience > 0.7 and has_position and holding_periods < 5:
            # 高耐心 + 持仓时间短 → 建议持有
            votes.append(Vote(
                action='hold',
                confidence=patience * 0.6,
                voter_category='genome',
                reason=f"耐心({patience:.1%}): 等待更好时机"
            ))
        
        return votes
    
    def _experience_voice(self, context: Dict) -> List[Vote]:
        """
        经验声音：基于Agent的历史经验做出判断
        
        经验来源：
        - PersonalInsights（如果实现了）
        - Private Ledger的历史记录
        
        v5.0版本：简化实现，仅基于最近表现
        """
        votes = []
        
        # v5.0: 简化版，仅基于最近的盈亏模式
        recent_pnl = context.get('recent_pnl', 0)
        consecutive_losses = context.get('consecutive_losses', 0)
        consecutive_wins = context.get('consecutive_wins', 0)
        
        # 如果连续亏损，经验建议保守
        if consecutive_losses >= 3:
            votes.append(Vote(
                action='hold',
                confidence=min(consecutive_losses / 10, 0.8),
                voter_category='experience',
                reason=f"经验教训: 连续{consecutive_losses}次亏损，应谨慎"
            ))
        
        # 如果连续盈利，经验建议继续（但降低信心，避免过度自信）
        if consecutive_wins >= 3:
            # 不投票，或低信心投票（避免过度自信）
            pass
        
        # v5.1+: 这里可以添加PersonalInsights的查询
        # personal_stats = context.get('personal_stats', {})
        # if personal_stats:
        #     ...
        
        return votes
    
    def _emotion_voice(self, context: Dict) -> List[Vote]:
        """
        情绪声音：基于Agent的情绪状态做出判断
        
        情绪影响：
        - despair: 绝望 → 倾向放弃/极端行为
        - fear: 恐惧 → 倾向保守
        - confidence: 信心 → 倾向激进
        - stress: 压力 → 影响判断质量
        """
        votes = []
        emotion = self.agent.emotion
        
        position = context.get('position', {})
        has_position = position.get('amount', 0) != 0
        
        # 1. 绝望
        if emotion.despair > 0.7:
            # 高度绝望 → 可能做出极端决策（不建议，降低权重）
            if has_position:
                votes.append(Vote(
                    action='close',
                    confidence=0.5,  # 低信心（情绪化决策）
                    voter_category='emotion',
                    reason=f"绝望({emotion.despair:.1%}): 放弃持仓"
                ))
        
        # 2. 恐惧
        if emotion.fear > 0.6 and has_position:
            # 高度恐惧 + 持仓 → 倾向平仓
            votes.append(Vote(
                action='close',
                confidence=emotion.fear * 0.6,
                voter_category='emotion',
                reason=f"恐惧({emotion.fear:.1%}): 不安全感"
            ))
        
        # 3. 信心
        if emotion.confidence > 0.7 and not has_position:
            # 高信心 + 无仓 → 倾向开仓
            votes.append(Vote(
                action='buy',  # 默认做多
                confidence=emotion.confidence * 0.5,
                voter_category='emotion',
                reason=f"信心({emotion.confidence:.1%}): 感觉良好"
            ))
        
        # 4. 压力
        if emotion.stress > 0.8:
            # 高压力 → 降低所有emotion投票的权重（通过记录）
            # v5.0: 简单处理，不投票或投hold
            votes.append(Vote(
                action='hold',
                confidence=0.4,
                voter_category='emotion',
                reason=f"压力({emotion.stress:.1%}): 无法决策"
            ))
        
        return votes
    
    def _strategy_voice(self, context: Dict) -> List[Vote]:
        """
        策略声音：基于Agent的策略池进行市场分析
        
        策略分析流程：
        1. 遍历Agent激活的策略
        2. 每个策略分析市场，给出评分
        3. 将评分转换为投票
        
        v5.0设计：
        - Strategy不直接决策，只提供"市场评估"
        - 输出：bullish_score/bearish_score（0-1）
        - Daimon综合所有因素后做最终决策
        """
        votes = []
        
        # 获取策略信号
        strategy_signals = context.get('strategy_signals', [])
        
        for signal in strategy_signals:
            strategy_name = signal.get('strategy_name', 'Unknown')
            bullish_score = signal.get('bullish_score', 0)
            bearish_score = signal.get('bearish_score', 0)
            confidence = signal.get('confidence', 0.5)
            reasoning = signal.get('reasoning', '')
            
            # 如果看涨评分高
            if bullish_score > 0.6:
                votes.append(Vote(
                    action='buy',
                    confidence=bullish_score * confidence,
                    voter_category='strategy',
                    reason=f"{strategy_name}: {reasoning} (看涨{bullish_score:.1%})"
                ))
            
            # 如果看跌评分高
            if bearish_score > 0.6:
                votes.append(Vote(
                    action='sell',
                    confidence=bearish_score * confidence,
                    voter_category='strategy',
                    reason=f"{strategy_name}: {reasoning} (看跌{bearish_score:.1%})"
                ))
            
            # 如果都不高，可能建议观望
            if bullish_score < 0.5 and bearish_score < 0.5:
                votes.append(Vote(
                    action='hold',
                    confidence=confidence * 0.6,
                    voter_category='strategy',
                    reason=f"{strategy_name}: {reasoning} (震荡)"
                ))
        
        return votes
    
    def _prophecy_voice(self, context: Dict) -> List[Vote]:
        """
        预言声音：基于Mastermind的预言（战略指导）
        
        预言来源：
        1. Mastermind的小预言（短期趋势）
        2. 环境压力评估
        
        特点：
        - 这是"战略层"的指导
        - 权重较高（0.6），但低于本能（1.0）
        - 可以被本能否决
        """
        votes = []
        
        bulletins = context.get('bulletins', {})
        
        # 1. 先知预言
        prophecy = bulletins.get('minor_prophecy', {})
        if prophecy:
            trend = prophecy.get('trend', 'neutral')
            confidence = prophecy.get('confidence', 0)
            
            if trend == 'bullish' and confidence > 0.6:
                votes.append(Vote(
                    action='buy',
                    confidence=confidence * 0.8,  # 略微折扣
                    voter_category='prophecy',
                    reason=f"先知预言: 看涨(信心{confidence:.1%})"
                ))
            elif trend == 'bearish' and confidence > 0.6:
                votes.append(Vote(
                    action='sell',
                    confidence=confidence * 0.8,
                    voter_category='prophecy',
                    reason=f"先知预言: 看跌(信心{confidence:.1%})"
                ))
            elif trend == 'neutral':
                votes.append(Vote(
                    action='hold',
                    confidence=0.6,
                    voter_category='prophecy',
                    reason="先知预言: 震荡市，观望"
                ))
        
        # 2. 环境压力
        environmental_pressure = prophecy.get('environmental_pressure', 0)
        if environmental_pressure > 0.7:
            # 高压力环境 → 建议观望或平仓
            position = context.get('position', {})
            has_position = position.get('amount', 0) != 0
            
            if has_position:
                votes.append(Vote(
                    action='close',
                    confidence=environmental_pressure * 0.7,
                    voter_category='prophecy',
                    reason=f"环境压力高({environmental_pressure:.1%}): 规避风险"
                ))
            else:
                votes.append(Vote(
                    action='hold',
                    confidence=0.6,
                    voter_category='prophecy',
                    reason=f"环境压力高({environmental_pressure:.1%}): 观望"
                ))
        
        return votes
    
    def _world_signature_voice(self, context: Dict) -> List[Vote]:
        """
        世界签名声音：基于WorldSignature感知市场环境（v5.5+新增）✨
        
        这是朋友指出的关键：让Agent"知道"它在什么世界中！
        
        WorldSignature特征：
        - drift: 漂移率（趋势方向和强度）
        - volatility: 波动率（市场波动程度）
        - trend_strength: 趋势强度（趋势的可靠性）
        - entropy: 熵（市场混乱程度）
        - regime_label: Regime标签（bull/bear/volatile/sideways）
        
        特点：
        - 这是"环境感知"层的指导
        - 权重适中（0.6-0.8），让Agent"看见"世界
        - 与先知预言配合，形成完整的环境认知
        """
        votes = []
        
        # 获取WorldSignature
        signature = context.get('world_signature', None)
        if not signature:
            # 如果没有WorldSignature，不投票
            return votes
        
        # 提取特征（支持两种格式）
        if hasattr(signature, 'drift'):
            # SignatureEnrichedData格式
            drift = signature.drift
            volatility = signature.volatility
            trend_strength = signature.trend_strength
            entropy = signature.entropy
            regime_label = signature.regime_label
        else:
            # 字典格式
            drift = signature.get('drift', 0)
            volatility = signature.get('volatility', 0)
            trend_strength = signature.get('trend_strength', 0)
            entropy = signature.get('entropy', 0)
            regime_label = signature.get('regime_label', 'unknown')
        
        position = context.get('position', {})
        has_position = position.get('amount', 0) != 0
        
        # ==================== Regime感知决策 ====================
        
        # 1. 牛市regime
        if regime_label in ['steady_bull', 'volatile_bull']:
            if drift > 0.01 and trend_strength > 0.5:
                # 强势牛市：建议做多
                if not has_position:
                    votes.append(Vote(
                        action='buy',
                        confidence=min(trend_strength * 0.9, 0.85),
                        voter_category='world_signature',
                        reason=f"牛市环境(drift={drift:+.2%}, 趋势强度={trend_strength:.0%})"
                    ))
                elif has_position:
                    # 持有多单
                    votes.append(Vote(
                        action='hold',
                        confidence=0.7,
                        voter_category='world_signature',
                        reason=f"牛市持续，持有头寸"
                    ))
            elif drift < 0:
                # 牛市转熊？建议警惕
                if has_position:
                    votes.append(Vote(
                        action='close',
                        confidence=0.6,
                        voter_category='world_signature',
                        reason=f"牛市可能反转(drift={drift:+.2%})"
                    ))
        
        # 2. 熊市regime
        elif regime_label in ['crash_bear', 'steady_bear']:
            if drift < -0.01 and trend_strength > 0.5:
                # 强势熊市：建议做空或平多
                if has_position:
                    votes.append(Vote(
                        action='close',
                        confidence=0.8,
                        voter_category='world_signature',
                        reason=f"熊市环境(drift={drift:+.2%})，及时离场"
                    ))
                else:
                    votes.append(Vote(
                        action='sell',
                        confidence=min(trend_strength * 0.8, 0.75),
                        voter_category='world_signature',
                        reason=f"熊市环境，顺势做空"
                    ))
            elif drift > 0:
                # 熊市转牛？谨慎乐观
                votes.append(Vote(
                    action='hold',
                    confidence=0.5,
                    voter_category='world_signature',
                    reason=f"熊市可能反转，观望"
                ))
        
        # 3. 高波震荡
        elif regime_label == 'high_volatility':
            if entropy > 0.7:
                # 高熵高波：市场混乱，建议观望或快速进出
                if has_position:
                    votes.append(Vote(
                        action='close',
                        confidence=0.7,
                        voter_category='world_signature',
                        reason=f"高波震荡(vol={volatility:.0%}, 熵={entropy:.0%})，快速离场"
                    ))
                else:
                    votes.append(Vote(
                        action='hold',
                        confidence=0.6,
                        voter_category='world_signature',
                        reason=f"市场混乱，观望为主"
                    ))
            else:
                # 有序震荡：可以短线交易
                if not has_position and abs(drift) > 0.005:
                    action = 'buy' if drift > 0 else 'sell'
                    votes.append(Vote(
                        action=action,
                        confidence=0.6,
                        voter_category='world_signature',
                        reason=f"有序震荡，短线{action}"
                    ))
        
        # 4. 低波盘整
        elif regime_label == 'low_volatility':
            # 低波动：交易成本高，建议观望
            if has_position and abs(drift) < 0.003:
                # 无明显趋势，平仓
                votes.append(Vote(
                    action='close',
                    confidence=0.5,
                    voter_category='world_signature',
                    reason=f"低波盘整(vol={volatility:.0%})，节省成本"
                ))
            else:
                votes.append(Vote(
                    action='hold',
                    confidence=0.6,
                    voter_category='world_signature',
                    reason=f"低波盘整，等待机会"
                ))
        
        # 5. 未知regime
        else:
            # 侧向观望
            votes.append(Vote(
                action='hold',
                confidence=0.5,
                voter_category='world_signature',
                reason=f"Regime不明({regime_label})，观望"
            ))
        
        # ==================== 危险指数检查（通用）====================
        
        # 如果WorldSignature有danger_index（v2.0格式）
        if hasattr(signature, 'danger_index'):
            danger = signature.danger_index
            if danger > 0.7 and has_position:
                # 高危环境，强烈建议平仓
                votes.append(Vote(
                    action='close',
                    confidence=0.9,
                    voter_category='world_signature',
                    reason=f"高危环境(danger={danger:.0%})，紧急离场！"
                ))
        
        # 如果WorldSignature有opportunity_index（v2.0格式）
        if hasattr(signature, 'opportunity_index'):
            opportunity = signature.opportunity_index
            if opportunity > 0.8 and not has_position:
                # 高机会环境，建议开仓
                action = 'buy' if drift > 0 else 'sell'
                votes.append(Vote(
                    action=action,
                    confidence=0.75,
                    voter_category='world_signature',
                    reason=f"高机会环境(opportunity={opportunity:.0%})！"
                ))
        
        return votes
    
    # ==================== 投票汇总 ====================
    
    def _tally_votes(self, all_votes: List[Vote], context: Dict) -> CouncilDecision:
        """
        汇总所有投票，做出最终决策
        
        汇总规则：
        1. 每个投票的得分 = confidence × category_weight
        2. 按action汇总得分
        3. 选择得分最高的action
        4. 最终信心 = 该action的平均信心
        
        v5.2改进：紧急模式
        - 资金<60%时，本能权重×3
        - 资金<40%时，本能权重×5
        """
        if not all_votes:
            return CouncilDecision(
                action='hold',
                confidence=0.5,
                reasoning="无投票"
            )
        
        # v5.2: 紧急模式 - 危险时提升本能权重
        capital_ratio = context.get('capital_ratio', 1.0)
        instinct_multiplier = 1.0
        if capital_ratio < 0.4:
            instinct_multiplier = 5.0  # 极度危险：本能权重×5
        elif capital_ratio < 0.6:
            instinct_multiplier = 3.0  # 危险：本能权重×3
        
        # 计算每个action的加权得分
        action_scores = defaultdict(float)
        action_vote_counts = defaultdict(int)
        action_confidence_sum = defaultdict(float)
        
        for vote in all_votes:
            weight = self.base_weights.get(vote.voter_category, 0.5)
            # v5.2: 紧急模式下，本能权重动态提升
            if vote.voter_category == 'instinct':
                weight *= instinct_multiplier
            weighted_score = vote.confidence * weight
            
            action_scores[vote.action] += weighted_score
            action_vote_counts[vote.action] += 1
            action_confidence_sum[vote.action] += vote.confidence
        
        # 选择得分最高的action
        primary_action = max(action_scores, key=action_scores.get)
        
        # 计算该action的平均信心
        avg_confidence = action_confidence_sum[primary_action] / action_vote_counts[primary_action]
        
        # 归一化信心（基于得分占比）
        total_score = sum(action_scores.values())
        if total_score > 0:
            confidence = action_scores[primary_action] / total_score
            # 与平均信心结合
            final_confidence = (confidence + avg_confidence) / 2
        else:
            final_confidence = avg_confidence
        
        # 限制在[0, 1]
        final_confidence = min(max(final_confidence, 0), 1)
        
        return CouncilDecision(
            action=primary_action,
            confidence=final_confidence,
            reasoning="",  # 将在guide中生成
        )
    
    def _generate_reasoning(self, all_votes: List[Vote], final_action: str) -> str:
        """
        生成决策推理（自然语言）
        
        规则：
        1. 列出支持final_action的主要投票
        2. 格式："{reason1} + {reason2} + {reason3} → {action}"
        """
        # 筛选支持final_action的投票
        supporting_votes = [v for v in all_votes if v.action == final_action]
        
        if not supporting_votes:
            return f"决策: {final_action}"
        
        # 按信心排序，取前3个
        supporting_votes.sort(key=lambda v: v.confidence, reverse=True)
        top_votes = supporting_votes[:3]
        
        # 生成推理
        reasons = [f"{v.reason}({v.confidence:.1%})" for v in top_votes]
        reasoning = " + ".join(reasons) + f" → {final_action}"
        
        return reasoning


# ==================== 工具函数 ====================

def format_decision_report(decision: CouncilDecision) -> str:
    """
    格式化决策报告（用于日志）
    
    Args:
        decision: CouncilDecision对象
    
    Returns:
        str: 格式化的报告
    """
    lines = []
    lines.append("━" * 60)
    lines.append(f"【守护神决策】{decision.action} (信心{decision.confidence:.1%})")
    lines.append(f"【推理】{decision.reasoning}")
    lines.append("━" * 60)
    lines.append("【投票详情】")
    
    for vote in sorted(decision.all_votes, key=lambda v: -v.confidence):
        weight = decision.weights_used.get(vote.voter_category, 1.0)
        weighted_conf = vote.confidence * weight
        lines.append(
            f"  [{vote.voter_category:10s}] {vote.action:5s} "
            f"{vote.confidence:.1%} (权重{weight:.1f} = {weighted_conf:.1%}) - {vote.reason}"
        )
    
    lines.append("━" * 60)
    
    return "\n".join(lines)

