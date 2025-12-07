#!/usr/bin/env python3
"""
交易行为深度诊断
==================

诊断为什么系统收益(152%)远低于BTC(536%)

✅ 数据封装原则：
- 使用facade统一入口
- 通过account/ledger访问数据
- 不直接访问私有属性
"""

import pandas as pd
import json
from pathlib import Path
import sys


def load_data():
    """加载价格数据和测试结果"""
    # 价格数据
    df = pd.read_csv('data/okx/BTC_USDT_1d_20251206.csv')
    prices = df['close'].tolist()
    
    # Phase 1结果
    result_file = Path("results/phase1_training_20251208_041431.json")
    with open(result_file, 'r') as f:
        result = json.load(f)
    
    return prices, result


def diagnose_from_logs():
    """从日志中诊断交易行为"""
    
    print("=" * 80)
    print("🔬 Phase 1 交易行为深度诊断")
    print("=" * 80)
    print()
    
    prices, result = load_data()
    
    # 基准信息
    start_price = prices[0]
    end_price = prices[min(499, len(prices) - 1)]
    btc_return = (end_price - start_price) / start_price * 100
    system_return = result['result']['system_return']
    
    print("📊 基准对比:")
    print(f"   BTC收益: {btc_return:+.2f}%")
    print(f"   系统收益: {system_return:+.2f}%")
    print(f"   差距: {system_return - btc_return:+.2f}%")
    print()
    
    # 从日志提取交易信息
    log_file = Path("results/phase1_COMPLIANT.log")
    
    if not log_file.exists():
        print("❌ 找不到日志文件")
        return
    
    print("=" * 80)
    print("🔍 分析日志中的交易记录...")
    print("=" * 80)
    print()
    
    with open(log_file, 'r') as f:
        log_content = f.read()
    
    # 统计交易类型
    buy_count = log_content.count("✅ 交易执行成功") + log_content.count("开多")
    sell_count = log_content.count("平多") + log_content.count("sell")
    short_count = log_content.count("开空") + log_content.count("short")
    cover_count = log_content.count("平空") + log_content.count("cover")
    
    # 统计持仓相关
    has_position_count = log_content.count("has_position=True")
    no_position_count = log_content.count("has_position=False")
    
    print("📈 交易类型统计:")
    print(f"   开多(buy): ~{buy_count}次")
    print(f"   平多(sell): ~{sell_count}次")
    print(f"   开空(short): ~{short_count}次")
    print(f"   平空(cover): ~{cover_count}次")
    print()
    
    print("💼 持仓状态:")
    print(f"   有持仓: ~{has_position_count}次")
    print(f"   无持仓: ~{no_position_count}次")
    print()
    
    # 分析可能的问题
    print("=" * 80)
    print("💡 问题诊断")
    print("=" * 80)
    print()
    
    total_trades = result['result']['total_trades']
    
    # 诊断1: 交易太少
    if total_trades < 50:
        print("🔴 问题1: 交易次数过少 ({total_trades}笔)")
        print(f"   50个Agent，500周期，只有{total_trades}笔交易")
        print(f"   → 大部分Agent没有交易！")
        print(f"   → 可能原因: Daimon决策过于保守")
        print()
    
    # 诊断2: 持仓率低
    if total_trades > 0 and total_trades < 100:
        estimated_position_rate = (total_trades / 2) / 50 * 100  # 估算持仓率
        print(f"🔴 问题2: 估算持仓率过低 (~{estimated_position_rate:.1f}%)")
        print(f"   理论上50个Agent应该有40+个持仓")
        print(f"   → 实际可能只有{total_trades // 2}个Agent持仓")
        print(f"   → 大量资金闲置！")
        print()
    
    # 诊断3: 杠杆为1
    print("🔴 问题3: 杠杆固定为1.0x（无杠杆）")
    print("   系统硬编码 leverage = 1.0")
    print("   → 相当于现货交易")
    print("   → 如果用3x杠杆，收益可达 ~456%")
    print()
    
    # 诊断4: 资金利用率
    avg_trades_per_agent = result['result']['avg_trades_per_agent']
    if avg_trades_per_agent < 1:
        print(f"🔴 问题4: 人均交易过少 ({avg_trades_per_agent}笔/agent)")
        print(f"   说明大部分Agent一次都没交易")
        print(f"   → 资金完全闲置！")
        print()
    
    # 综合诊断
    print("=" * 80)
    print("🎯 根本原因分析")
    print("=" * 80)
    print()
    
    print("系统收益远低于BTC的原因：")
    print()
    print("1. **大量Agent没有参与交易** (推测)")
    print(f"   - 总交易: {total_trades}笔")
    print(f"   - 人均交易: {avg_trades_per_agent:.1f}笔")
    print(f"   - 如果每个Agent买入+持有，至少应该有50笔买入交易")
    print(f"   - 实际可能只有 ~{total_trades // 2} 个Agent交易")
    print()
    
    print("2. **Daimon决策过于保守** (推测)")
    print("   - Daimon可能大部分时间选择'hold'（不交易）")
    print("   - confidence可能过低，导致仓位过小")
    print("   - 需要检查Daimon的决策逻辑")
    print()
    
    print("3. **杠杆为1.0x**")
    print("   - 如果其他问题解决，1x杠杆应该也能获得~536%收益")
    print("   - 但目前只有152%，说明持仓严重不足")
    print()
    
    # 建议
    print("=" * 80)
    print("💡 自由演化方案（不手动调参）")
    print("=" * 80)
    print()
    
    print("❌ 不做：手动增加杠杆、手动调整Daimon逻辑")
    print("✅ 应做：让进化机制自然解决问题")
    print()
    
    print("方案1: 增加训练周期")
    print("   - 从500周期 → 2000周期")
    print("   - 让系统有更多时间发现'持有'策略的优势")
    print()
    
    print("方案2: 调整Fitness函数")
    print("   - 当前只看绝对收益")
    print("   - 可能需要考虑'参与度'")
    print("   - 不交易的Agent不应该被复制")
    print()
    
    print("方案3: 增加种群多样性")
    print("   - 当前50个Agent可能太相似")
    print("   - 增加Agent数量或初始多样性")
    print("   - 让更多策略有机会被尝试")
    print()
    
    print("方案4: 解锁更多基因参数")
    print("   - 检查是否有控制'交易倾向'的基因")
    print("   - 确保基因空间足够大")
    print()
    
    # 保存诊断结果
    diagnosis = {
        "total_trades": total_trades,
        "avg_trades_per_agent": avg_trades_per_agent,
        "estimated_active_agents": total_trades // 2 if total_trades > 0 else 0,
        "estimated_position_rate": (total_trades / 2) / 50 * 100 if total_trades > 0 else 0,
        "leverage": 1.0,
        "problems": [
            "交易次数过少",
            "大量Agent未参与交易",
            "Daimon决策过于保守",
            "杠杆为1.0（但不是主要问题）"
        ],
        "root_cause": "大量资金闲置，未实现真正的'买入持有'",
        "recommendation": "让进化机制自然解决，不手动调参"
    }
    
    output_file = Path("results/trading_behavior_diagnosis.json")
    with open(output_file, 'w') as f:
        json.dump(diagnosis, f, indent=2, ensure_ascii=False)
    
    print(f"💾 诊断结果已保存: {output_file}")
    print()


if __name__ == "__main__":
    diagnose_from_logs()

