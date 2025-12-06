"""
WorldSignature v2.0 演示脚本

展示核心功能：
1. 实时生成市场签名
2. 评分指标解读
3. Regime聚类和匹配
4. 完整workflow演示
"""

import numpy as np
import time
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from prometheus.world_signature import (
    StreamingSignatureGenerator,
    RegimeLibrary,
)
from prometheus.world_signature.metrics import interpret_metrics


def demo_basic_usage():
    """基础使用演示"""
    print("\n" + "="*70)
    print("【演示1】基础使用 - 生成市场签名")
    print("="*70)
    
    # 创建生成器
    generator = StreamingSignatureGenerator(
        instrument="BTC-USDT",
        macro_window_hours=4,
        micro_window_minutes=5
    )
    
    # 模拟市场数据
    price = 50000.0
    
    for i in range(5):
        # 模拟价格变化
        price += np.random.randn() * 100
        
        market_data = {
            'price': price,
            'volume': 10.0 + np.random.randn() * 2,
            'orderbook': {
                'bids': [[price - j*10, 1.0 + j*0.1] for j in range(10)],
                'asks': [[price + j*10, 1.0 + j*0.1] for j in range(10)]
            },
            'trades': [
                {'price': price, 'size': 0.1, 'side': 'buy' if np.random.rand() > 0.5 else 'sell'}
                for _ in range(10)
            ]
        }
        
        # 生成签名
        sig = generator.update(
            market_data=market_data,
            funding_rate=0.0003,
            open_interest=1000000
        )
        
        print(f"\n签名 #{i+1}:")
        print(sig.to_human_readable())
        
        print("\n📊 指标解读:")
        metrics = {
            'regime_confidence': sig.regime_confidence,
            'stability_score': sig.stability_score,
            'danger_index': sig.danger_index,
            'opportunity_index': sig.opportunity_index,
            'novelty_score': sig.novelty_score
        }
        print(interpret_metrics(metrics))
        
        time.sleep(0.1)


def demo_regime_clustering():
    """Regime聚类演示"""
    print("\n" + "="*70)
    print("【演示2】Regime聚类 - 识别市场情境模式")
    print("="*70)
    
    # 生成历史数据
    generator = StreamingSignatureGenerator(
        instrument="BTC-USDT",
        macro_window_hours=1,
        micro_window_minutes=5
    )
    
    print("\n🔄 生成历史数据 (100个签名)...")
    
    for i in range(100):
        price = 50000 + i * 20 + np.random.randn() * 200
        
        market_data = {
            'price': price,
            'volume': 10.0 + np.random.randn() * 3,
            'orderbook': {
                'bids': [[price - j*10, 1.0] for j in range(10)],
                'asks': [[price + j*10, 1.0] for j in range(10)]
            }
        }
        
        generator.update(market_data, 0.0003, 1000000)
        
        if (i+1) % 20 == 0:
            print(f"  进度: {i+1}/100")
    
    # 获取历史签名
    historical_sigs = generator.get_historical_signatures()
    print(f"\n✅ 历史数据准备完成: {len(historical_sigs)}个签名")
    
    # 聚类
    print("\n🔍 开始聚类...")
    regime_lib = RegimeLibrary()
    
    try:
        regime_lib.build_from_history(
            historical_sigs,
            min_cluster_size=10,
            min_samples=5
        )
        
        if len(regime_lib.regimes) > 0:
            print(regime_lib.summary())
            
            # 测试匹配
            latest_sig = historical_sigs[-1]
            regime_id, confidence = regime_lib.match_regime(latest_sig)
            
            print(f"\n🎯 最新签名匹配结果:")
            print(f"  Regime: {regime_id}")
            print(f"  置信度: {confidence:.1%}")
            
            regime_info = regime_lib.get_regime_info(regime_id)
            if regime_info:
                print(f"  代表tags: {regime_info['representative_tags']}")
                print(f"  平均危险指数: {regime_info['avg_danger']:.1%}")
                print(f"  平均机会指数: {regime_info['avg_opportunity']:.1%}")
        else:
            print("⚠️  未能聚类出Regime（需要安装sklearn）")
    except Exception as e:
        print(f"⚠️  聚类失败: {e}")
        print("提示: 安装sklearn和hdbscan可以使用完整聚类功能")
        print("  pip install scikit-learn hdbscan")


def demo_real_time_monitoring():
    """实时监控演示"""
    print("\n" + "="*70)
    print("【演示3】实时监控 - 市场状态追踪")
    print("="*70)
    
    generator = StreamingSignatureGenerator(
        instrument="BTC-USDT",
        macro_window_hours=1,
        micro_window_minutes=5
    )
    
    print("\n📡 实时监控启动...\n")
    
    base_price = 50000.0
    
    for cycle in range(20):
        # 模拟不同市场状态
        if cycle < 5:
            # 平稳期
            price = base_price + np.random.randn() * 50
            vol_mult = 1.0
            print(f"  [{cycle+1:2d}] 市场状态: 平稳期", end="")
        elif cycle < 10:
            # 上涨期
            price = base_price + (cycle - 5) * 200 + np.random.randn() * 100
            vol_mult = 1.5
            print(f"  [{cycle+1:2d}] 市场状态: 上涨期", end="")
        elif cycle < 15:
            # 剧烈波动期
            price = base_price + 1000 + np.random.randn() * 500
            vol_mult = 3.0
            print(f"  [{cycle+1:2d}] 市场状态: 波动期", end="")
        else:
            # 下跌期
            price = base_price + 1000 - (cycle - 15) * 150 + np.random.randn() * 80
            vol_mult = 1.2
            print(f"  [{cycle+1:2d}] 市场状态: 下跌期", end="")
        
        market_data = {
            'price': price,
            'volume': 10.0 * vol_mult + np.random.randn() * 2,
            'orderbook': {
                'bids': [[price - j*10, 1.0] for j in range(10)],
                'asks': [[price + j*10, 1.0] for j in range(10)]
            },
            'trades': [
                {'price': price, 'size': 0.1, 'side': 'buy' if np.random.rand() > 0.5 else 'sell'}
                for _ in range(10)
            ]
        }
        
        sig = generator.update(market_data, 0.0003, 1000000)
        
        # 显示关键指标
        print(f" | 价格: ${price:.0f} | 新颖度: {sig.novelty_score:.1%} | 危险: {sig.danger_index:.1%} | 机会: {sig.opportunity_index:.1%}")
        
        # 告警检测
        if sig.danger_index > 0.6:
            print(f"    🚨 高危险告警！")
        if sig.novelty_score > 0.85:
            print(f"    🆕 新颖情境告警！")
        if sig.opportunity_index > 0.7:
            print(f"    🎯 高机会提示！")
        
        time.sleep(0.05)
    
    print("\n✅ 实时监控演示完成")


def demo_signature_comparison():
    """签名比较演示"""
    print("\n" + "="*70)
    print("【演示4】签名比较 - 相似度计算")
    print("="*70)
    
    generator = StreamingSignatureGenerator(instrument="BTC-USDT")
    
    # 生成两个签名
    print("\n生成签名1 (平稳市场)...")
    sig1 = generator.update({
        'price': 50000,
        'volume': 10,
        'orderbook': {
            'bids': [[50000 - j*10, 1.0] for j in range(10)],
            'asks': [[50000 + j*10, 1.0] for j in range(10)]
        }
    }, 0.0003, 1000000)
    
    print("\n生成签名2 (相似市场)...")
    sig2 = generator.update({
        'price': 50010,  # 小幅变化
        'volume': 10.5,
        'orderbook': {
            'bids': [[50010 - j*10, 1.0] for j in range(10)],
            'asks': [[50010 + j*10, 1.0] for j in range(10)]
        }
    }, 0.0003, 1000000)
    
    print("\n生成签名3 (不同市场)...")
    sig3 = generator.update({
        'price': 52000,  # 大幅变化
        'volume': 30,     # 成交量激增
        'orderbook': {
            'bids': [[52000 - j*20, 0.5] for j in range(10)],  # 深度下降
            'asks': [[52000 + j*20, 0.5] for j in range(10)]
        }
    }, 0.0008, 1200000)  # 资金费率上升
    
    # 计算相似度
    from prometheus.world_signature.signature import calculate_similarity
    
    sim_12 = calculate_similarity(sig1, sig2)
    sim_13 = calculate_similarity(sig1, sig3)
    sim_23 = calculate_similarity(sig2, sig3)
    
    print(f"\n📊 相似度分析:")
    print(f"\n  签名1 vs 签名2 (相似市场):")
    print(f"    综合相似度: {sim_12['overall']:.1%}")
    print(f"    向量相似度: {sim_12['vec_sim']:.1%}")
    print(f"    标签相似度: {sim_12['tag_sim']:.1%}")
    
    print(f"\n  签名1 vs 签名3 (不同市场):")
    print(f"    综合相似度: {sim_13['overall']:.1%}")
    print(f"    向量相似度: {sim_13['vec_sim']:.1%}")
    print(f"    标签相似度: {sim_13['tag_sim']:.1%}")
    
    print(f"\n  签名2 vs 签名3:")
    print(f"    综合相似度: {sim_23['overall']:.1%}")
    
    print("\n✅ 相似度计算演示完成")


def main():
    """主函数"""
    print("\n╔════════════════════════════════════════════════════════════════╗")
    print("║         WorldSignature v2.0 - 完整功能演示                      ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    try:
        # 演示1: 基础使用
        demo_basic_usage()
        
        # 演示2: Regime聚类
        demo_regime_clustering()
        
        # 演示3: 实时监控
        demo_real_time_monitoring()
        
        # 演示4: 签名比较
        demo_signature_comparison()
        
        print("\n" + "="*70)
        print("✅ 所有演示完成！")
        print("="*70)
        
        print("\n💡 下一步:")
        print("  1. 安装sklearn和hdbscan以使用完整聚类功能")
        print("     pip install scikit-learn hdbscan")
        print("  2. 集成到Prometheus系统:")
        print("     - Prophet: 使用评分指标做战略决策")
        print("     - Moirai: 使用danger_index做风控")
        print("     - Memory Layer: 存储签名和关联经验")
        print("  3. 运行回测验证签名的预测能力")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
    except Exception as e:
        print(f"\n\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

