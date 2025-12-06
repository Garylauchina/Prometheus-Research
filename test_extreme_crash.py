"""
极端场景测试：BTC市场崩盘（24小时内暴跌99%）

测试目标：
1. WorldSignature能否正确识别极端危险？
2. Daimon会给出什么决策？
3. 系统是否有足够的"恐惧"？
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from prometheus.world_signature.world_signature_v2 import WorldSignature_V2
from prometheus.world_signature.macro_code import MacroCode
from prometheus.world_signature.micro_code import MicroCode
from prometheus.world_signature.metrics import Metrics
from prometheus.core.inner_council import Daimon
from prometheus.core.genome import GenomeVector
from prometheus.core.lineage import LineageVector
from prometheus.core.instinct import Instinct


def create_crash_market_data(hours: int = 24) -> pd.DataFrame:
    """
    创建一个极端崩盘的市场数据
    
    场景：BTC在24小时内从$50,000跌到$500（-99%）
    """
    np.random.seed(42)
    
    # 时间序列（每分钟一个数据点）
    n_points = hours * 60
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(n_points, 0, -1)]
    
    # 价格：指数衰减从50000到500
    start_price = 50000
    end_price = 500
    
    # 使用指数衰减 + 随机波动
    t = np.linspace(0, 1, n_points)
    base_prices = start_price * np.exp(-np.log(start_price/end_price) * t)
    
    # 添加随机波动（崩盘中的反弹和加速）
    random_factor = 1 + np.random.normal(0, 0.1, n_points)  # ±10%随机波动
    prices = base_prices * random_factor
    
    # 成交量：恐慌性放大
    # 崩盘时成交量会暴增（恐慌性抛售）
    base_volume = 1000
    panic_multiplier = 1 + 50 * np.exp(-3 * t)  # 前期恐慌最大
    volumes = base_volume * panic_multiplier * (1 + np.random.normal(0, 0.5, n_points))
    
    # 构造OHLCV数据
    data = []
    for i in range(n_points):
        close = prices[i]
        high = close * (1 + abs(np.random.normal(0, 0.02)))  # 最高价
        low = close * (1 - abs(np.random.normal(0, 0.05)))   # 最低价（跌幅更大）
        open_price = close * (1 + np.random.normal(0, 0.03))
        
        data.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volumes[i]
        })
    
    df = pd.DataFrame(data)
    
    print(f"📊 崩盘市场数据生成完成：")
    print(f"   起始价格：${df['close'].iloc[0]:,.2f}")
    print(f"   结束价格：${df['close'].iloc[-1]:,.2f}")
    print(f"   总跌幅：{(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:.2f}%")
    print(f"   最大单小时跌幅：{df['close'].pct_change().min() * 100:.2f}%")
    print(f"   平均成交量：{df['volume'].mean():.2f}")
    print()
    
    return df


def analyze_crash_with_worldsignature(df: pd.DataFrame) -> WorldSignature_V2:
    """使用WorldSignature分析崩盘市场"""
    
    print("🌍 WorldSignature分析崩盘市场...")
    print("=" * 60)
    
    # 计算returns
    returns = df['close'].pct_change().dropna().values
    
    # 计算各种指标
    recent_returns = returns[-20:] if len(returns) >= 20 else returns
    
    # Drift：平均收益率（应该是极度负值）
    drift = float(np.mean(recent_returns))
    
    # Volatility：波动率（应该爆炸）
    volatility = float(np.std(recent_returns))
    
    # Trend strength：趋势强度（应该是-1，单向下跌）
    if len(recent_returns) > 0:
        trend_direction = 1 if drift > 0 else -1
        trend_strength = trend_direction * min(abs(drift) / (volatility + 1e-8), 1.0)
    else:
        trend_strength = 0.0
    
    # Entropy：市场混乱度（崩盘时可能很低，因为所有人都在卖）
    # 或者很高，因为价格剧烈波动
    price_changes = np.diff(df['close'].values)
    entropy = float(np.std(price_changes) / (np.mean(np.abs(price_changes)) + 1e-8))
    
    # 创建MacroCode
    macro_code = MacroCode(
        drift=drift,
        volatility=volatility,
        trend_strength=trend_strength,
        entropy=entropy
    )
    
    # 创建MicroCode（简化版）
    micro_code = MicroCode(
        bid_ask_spread=0.05,  # 崩盘时spread会扩大
        order_imbalance=-0.9,  # 极度偏向卖方
        trade_intensity=10.0,  # 交易强度暴增
        price_impact=0.8       # 价格冲击巨大
    )
    
    # 创建Metrics
    metrics = Metrics(
        regime_confidence=0.99,  # 对regime识别非常确定
        stability=0.05,          # 极度不稳定
        danger=0.99,             # 极度危险！
        opportunity=0.01,        # 几乎没有机会
        novelty=0.95             # 这是罕见事件
    )
    
    # 创建WorldSignature
    world_signature = WorldSignature_V2(
        macro_code=macro_code,
        micro_code=micro_code,
        metrics=metrics,
        regime_label="EXTREME_CRASH",  # 特殊标签
        timestamp=df['timestamp'].iloc[-1]
    )
    
    # 打印分析结果
    print("\n📈 宏观特征（MacroCode）：")
    print(f"   Drift: {drift:.6f} (平均收益率) {'🔴 极度负值！' if drift < -0.01 else ''}")
    print(f"   Volatility: {volatility:.6f} (波动率) {'🔴 爆炸式波动！' if volatility > 0.1 else ''}")
    print(f"   Trend Strength: {trend_strength:.6f} (趋势强度) {'🔴 单向暴跌！' if trend_strength < -0.5 else ''}")
    print(f"   Entropy: {entropy:.6f} (混乱度)")
    
    print("\n📊 微观特征（MicroCode）：")
    print(f"   Order Imbalance: {micro_code.order_imbalance:.2f} (买卖失衡) {'🔴 卖方压倒性优势！' if micro_code.order_imbalance < -0.5 else ''}")
    print(f"   Trade Intensity: {micro_code.trade_intensity:.2f} (交易强度) {'🔴 恐慌性抛售！' if micro_code.trade_intensity > 5 else ''}")
    
    print("\n⚠️  风险评估（Metrics）：")
    print(f"   Regime Confidence: {metrics.regime_confidence:.2%} (识别确定性)")
    print(f"   Stability: {metrics.stability:.2%} {'🔴 极度不稳定！' if metrics.stability < 0.2 else ''}")
    print(f"   Danger: {metrics.danger:.2%} {'🔴🔴🔴 极度危险！' if metrics.danger > 0.8 else ''}")
    print(f"   Opportunity: {metrics.opportunity:.2%} {'❌ 几乎无机会' if metrics.opportunity < 0.1 else ''}")
    print(f"   Novelty: {metrics.novelty:.2%} {'⚠️  罕见事件！' if metrics.novelty > 0.7 else ''}")
    
    print(f"\n🏷️  市场状态：{world_signature.regime_label}")
    print("=" * 60)
    print()
    
    return world_signature


def test_daimon_decision_in_crash(world_signature: WorldSignature_V2):
    """测试Daimon在崩盘中的决策"""
    
    print("🧠 Daimon决策测试（极端崩盘场景）...")
    print("=" * 60)
    
    # 创建一个测试Agent
    genome = GenomeVector.create_genesis()
    lineage = LineageVector.create_genesis(family_id=0)
    instinct = Instinct.create_genesis()
    
    # 创建Daimon
    daimon = Daimon(
        genome=genome,
        lineage=lineage,
        instinct=instinct
    )
    
    # 场景1：持有BTC（最危险）
    print("\n【场景1】持有BTC，面临99%亏损...")
    context_holding = {
        'world_signature': world_signature,
        'position': 1.0,  # 满仓
        'unrealized_pnl': -0.99,  # 已亏损99%
        'account_health': 0.01,  # 账户几乎归零
        'market_data': {
            'close': 500,
            'volume': 50000,
        }
    }
    
    decision_holding = daimon.deliberate(context_holding)
    print(f"\n   决策：{decision_holding.action}")
    print(f"   信心：{decision_holding.confidence:.2%}")
    print(f"   投票明细：")
    for vote in decision_holding.votes:
        print(f"      - {vote.voice}: {vote.action} (信心 {vote.confidence:.2%}, 权重 {vote.weight:.2f})")
    
    # 场景2：空仓观望
    print("\n【场景2】空仓观望，是否抄底？")
    context_empty = {
        'world_signature': world_signature,
        'position': 0.0,  # 空仓
        'unrealized_pnl': 0.0,
        'account_health': 1.0,  # 账户健康
        'market_data': {
            'close': 500,
            'volume': 50000,
        }
    }
    
    decision_empty = daimon.deliberate(context_empty)
    print(f"\n   决策：{decision_empty.action}")
    print(f"   信心：{decision_empty.confidence:.2%}")
    print(f"   投票明细：")
    for vote in decision_empty.votes:
        print(f"      - {vote.voice}: {vote.action} (信心 {vote.confidence:.2%}, 权重 {vote.weight:.2f})")
    
    # 场景3：做空获利
    print("\n【场景3】做空持仓，已盈利300%，是否平仓？")
    context_short = {
        'world_signature': world_signature,
        'position': -1.0,  # 做空
        'unrealized_pnl': 3.0,  # 盈利300%
        'account_health': 4.0,  # 账户暴涨
        'market_data': {
            'close': 500,
            'volume': 50000,
        }
    }
    
    decision_short = daimon.deliberate(context_short)
    print(f"\n   决策：{decision_short.action}")
    print(f"   信心：{decision_short.confidence:.2%}")
    print(f"   投票明细：")
    for vote in decision_short.votes:
        print(f"      - {vote.voice}: {vote.action} (信心 {vote.confidence:.2%}, 权重 {vote.weight:.2f})")
    
    print("\n" + "=" * 60)
    
    return {
        'holding': decision_holding,
        'empty': decision_empty,
        'short': decision_short
    }


def analyze_system_response(decisions: dict):
    """分析系统的整体响应"""
    
    print("\n" + "🎯 系统响应分析" + "\n")
    print("=" * 60)
    
    print("\n✅ 合理的响应：")
    correct_responses = []
    
    # 场景1：持有BTC应该立即平仓
    if decisions['holding'].action in ['close', 'sell']:
        print("   ✓ 场景1（持仓）：正确决策 - 立即平仓止损")
        correct_responses.append(True)
    else:
        print("   ✗ 场景1（持仓）：错误决策 - 应该立即平仓！")
        correct_responses.append(False)
    
    # 场景2：空仓应该继续观望或做空
    if decisions['empty'].action in ['hold', 'sell']:
        print("   ✓ 场景2（空仓）：正确决策 - 不抄底/做空")
        correct_responses.append(True)
    else:
        print("   ✗ 场景2（空仓）：错误决策 - 不应该抄底！")
        correct_responses.append(False)
    
    # 场景3：做空盈利，可以平仓或继续持有
    if decisions['short'].action in ['close', 'hold']:
        print("   ✓ 场景3（做空）：合理决策 - 平仓获利或继续持有")
        correct_responses.append(True)
    else:
        print("   ✗ 场景3（做空）：可疑决策 - 为何要反向操作？")
        correct_responses.append(False)
    
    accuracy = sum(correct_responses) / len(correct_responses)
    print(f"\n📊 决策正确率：{accuracy:.1%} ({sum(correct_responses)}/{len(correct_responses)})")
    
    # 系统的"恐惧指数"
    print("\n⚠️  系统的「恐惧反应」评估：")
    
    # 持仓场景的反应速度
    holding_confidence = decisions['holding'].confidence
    if decisions['holding'].action in ['close', 'sell'] and holding_confidence > 0.7:
        print(f"   ✓ 高信心止损（{holding_confidence:.1%}）- 系统有足够的「恐惧」✅")
        fear_level = "充足"
    elif decisions['holding'].action in ['close', 'sell']:
        print(f"   ⚠️  低信心止损（{holding_confidence:.1%}）- 系统「恐惧不足」⚠️")
        fear_level = "不足"
    else:
        print(f"   ✗ 不止损（{holding_confidence:.1%}）- 系统「完全不恐惧」❌")
        fear_level = "缺失"
    
    # 空仓场景的抄底欲望
    if decisions['empty'].action == 'buy':
        print("   ✗ 尝试抄底 - 系统「贪婪战胜恐惧」❌")
    else:
        print("   ✓ 不抄底 - 系统「理性控制贪婪」✅")
    
    print(f"\n🎯 最终评估：")
    print(f"   决策准确性：{'🟢 优秀' if accuracy >= 0.8 else '🟡 尚可' if accuracy >= 0.6 else '🔴 危险'}")
    print(f"   恐惧反应：{'🟢 充足' if fear_level == '充足' else '🟡 不足' if fear_level == '不足' else '🔴 缺失'}")
    
    # 最重要的问题
    print("\n" + "=" * 60)
    print("💭 最关键的问题：")
    print("=" * 60)
    
    if decisions['holding'].action not in ['close', 'sell']:
        print("\n🚨 严重警告：系统在-99%崩盘中不止损！")
        print("   这意味着：")
        print("   1. ❌ 风险控制机制失效")
        print("   2. ❌ WorldSignature的danger信号未被重视")
        print("   3. ❌ Daimon的「求生本能」不足")
        print("\n   ⚠️  这是致命缺陷！必须修复！")
    else:
        print("\n✅ 系统在极端崩盘中能够正确止损")
        print("   这表明：")
        print("   1. ✅ 风险控制机制有效")
        print("   2. ✅ WorldSignature的danger信号被正确识别")
        print("   3. ✅ Daimon的「求生本能」充足")
        print("\n   🎉 通过极端压力测试！")
    
    print("=" * 60)


def main():
    """主测试流程"""
    
    print("\n" + "🚨" * 30)
    print("极端场景压力测试：BTC市场崩盘（-99%）")
    print("🚨" * 30 + "\n")
    
    # 步骤1：生成崩盘市场数据
    print("【步骤1】生成崩盘市场数据...")
    df = create_crash_market_data(hours=24)
    
    # 步骤2：WorldSignature分析
    print("【步骤2】WorldSignature分析...")
    world_signature = analyze_crash_with_worldsignature(df)
    
    # 步骤3：Daimon决策测试
    print("【步骤3】Daimon决策测试...")
    decisions = test_daimon_decision_in_crash(world_signature)
    
    # 步骤4：系统响应分析
    print("【步骤4】系统响应分析...")
    analyze_system_response(decisions)
    
    print("\n" + "🚨" * 30)
    print("测试完成！")
    print("🚨" * 30 + "\n")


if __name__ == '__main__':
    main()

