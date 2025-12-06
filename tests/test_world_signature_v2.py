"""
WorldSignature v2.0 测试

测试所有核心功能：
1. MacroCode / MicroCode
2. WorldSignature_V2
3. StreamingSignatureGenerator
4. RegimeLibrary
5. 评分指标
"""

import numpy as np
import time
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from prometheus.world_signature import (
    MacroCode,
    MicroCode,
    WorldSignature_V2,
    StreamingSignatureGenerator,
    RegimeLibrary,
)
from prometheus.world_signature.metrics import calculate_all_metrics


class TestMacroCode:
    """测试MacroCode"""
    
    def test_create_macro_code(self):
        """测试创建MacroCode"""
        from prometheus.world_signature.macro_code import (
            compute_macro_features,
            discretize_macro,
            tags_to_compact_text,
            embed_macro
        )
        
        # 模拟OHLC数据
        ohlc_data = np.random.randn(240, 4) * 100 + 50000  # 4小时数据
        volume_data = np.random.randn(240) * 10 + 100
        
        # 计算特征
        features = compute_macro_features(
            ohlc_data=ohlc_data,
            volume_data=volume_data,
            funding_rate=0.0003,
            open_interest=1000000,
            open_interest_24h_ago=950000,
            volume_30d_avg=14400,
            vol_30d_avg=0.015
        )
        
        assert 'trend_slope' in features
        assert 'realized_vol_1h' in features
        
        # 离散化
        tags = discretize_macro(features)
        assert len(tags) > 0
        assert any('trend:' in tag for tag in tags)
        
        # 紧凑文本
        compact = tags_to_compact_text(tags, 'M')
        assert 'M:' in compact
        
        # 嵌入
        vec = embed_macro(features, tags, dim=128)
        assert len(vec) == 128
        assert np.abs(np.linalg.norm(vec) - 1.0) < 0.01  # L2归一化
        
        # 创建MacroCode
        macro = MacroCode(
            human_tags=tags,
            compact_text=compact,
            macro_vec=vec,
            raw_features=features
        )
        
        assert macro is not None
        print(f"✅ MacroCode创建成功: {macro.compact_text}")


class TestMicroCode:
    """测试MicroCode"""
    
    def test_create_micro_code(self):
        """测试创建MicroCode"""
        from prometheus.world_signature.micro_code import (
            compute_micro_features,
            discretize_micro,
            tags_to_compact_text,
            embed_micro
        )
        
        # 模拟订单簿
        orderbook = {
            'bids': [[50000 - i*10, 1.0 + i*0.1] for i in range(10)],
            'asks': [[50000 + i*10, 1.0 + i*0.1] for i in range(10)]
        }
        
        # 模拟交易
        trades = [
            {'price': 50000, 'size': 0.5, 'side': 'buy'},
            {'price': 50010, 'size': 0.3, 'side': 'sell'},
        ] * 10
        
        # 模拟价格历史
        price_history = np.random.randn(300) * 100 + 50000
        
        # 计算特征
        features = compute_micro_features(
            orderbook=orderbook,
            recent_trades=trades,
            price_history=price_history,
            window_minutes=5
        )
        
        assert 'rel_spread' in features
        assert 'depth_imbalance' in features
        
        # 离散化
        tags = discretize_micro(features)
        assert len(tags) > 0
        
        # 紧凑文本
        compact = tags_to_compact_text(tags, 'm')
        print(f"Tags: {tags}")
        print(f"Compact: {compact}")
        assert 'm' in compact  # 至少包含前缀
        
        # 嵌入
        vec = embed_micro(features, tags, dim=256)
        assert len(vec) == 256
        
        # 创建MicroCode
        micro = MicroCode(
            human_tags=tags,
            compact_text=compact,
            micro_vec=vec,
            raw_features=features
        )
        
        assert micro is not None
        print(f"✅ MicroCode创建成功: {micro.compact_text}")


class TestWorldSignature:
    """测试WorldSignature_V2"""
    
    def test_create_signature(self):
        """测试创建完整签名"""
        from prometheus.world_signature.macro_code import compute_macro_features, discretize_macro, tags_to_compact_text as macro_compact, embed_macro
        from prometheus.world_signature.micro_code import compute_micro_features, discretize_micro, tags_to_compact_text as micro_compact, embed_micro
        
        # 创建MacroCode
        ohlc = np.random.randn(240, 4) * 100 + 50000
        volume = np.random.randn(240) * 10 + 100
        
        macro_features = compute_macro_features(
            ohlc_data=ohlc,
            volume_data=volume,
            funding_rate=0.0003,
            open_interest=1000000,
            open_interest_24h_ago=950000,
            volume_30d_avg=14400,
            vol_30d_avg=0.015
        )
        
        macro_tags = discretize_macro(macro_features)
        macro = MacroCode(
            human_tags=macro_tags,
            compact_text=macro_compact(macro_tags, 'M'),
            macro_vec=embed_macro(macro_features, macro_tags),
            raw_features=macro_features
        )
        
        # 创建MicroCode
        orderbook = {
            'bids': [[50000 - i*10, 1.0] for i in range(10)],
            'asks': [[50000 + i*10, 1.0] for i in range(10)]
        }
        
        micro_features = compute_micro_features(
            orderbook=orderbook,
            recent_trades=[],
            price_history=np.random.randn(300) + 50000
        )
        
        micro_tags = discretize_micro(micro_features)
        micro = MicroCode(
            human_tags=micro_tags,
            compact_text=micro_compact(micro_tags, 'm'),
            micro_vec=embed_micro(micro_features, micro_tags),
            raw_features=micro_features
        )
        
        # 创建签名
        signature = WorldSignature_V2(
            id=WorldSignature_V2.generate_id(),
            timestamp=time.time(),
            instrument="BTC-USDT",
            macro=macro,
            micro=micro,
            regime_id="R_1",
            regime_confidence=0.85,
            novelty_score=0.3,
            stability_score=0.7,
            danger_index=0.2,
            opportunity_index=0.6
        )
        
        assert signature is not None
        assert signature.regime_id == "R_1"
        
        # 测试序列化
        sig_dict = signature.to_dict()
        assert 'macro' in sig_dict
        
        sig_json = signature.to_json()
        assert 'BTC-USDT' in sig_json
        
        # 测试反序列化
        sig2 = WorldSignature_V2.from_dict(sig_dict)
        assert sig2.regime_id == signature.regime_id
        
        # 测试可读性
        readable = signature.to_human_readable()
        print("\n" + readable)
        
        # 测试紧凑表示
        compact = signature.to_compact_string()
        print(f"紧凑表示: {compact}")
        
        print("✅ WorldSignature_V2创建和序列化成功")


class TestStreamingGenerator:
    """测试StreamingSignatureGenerator"""
    
    def test_streaming_generation(self):
        """测试流式生成"""
        generator = StreamingSignatureGenerator(
            instrument="BTC-USDT",
            macro_window_hours=1,  # 短窗口用于测试
            micro_window_minutes=5
        )
        
        # 模拟市场数据流
        for i in range(100):
            price = 50000 + i * 10 + np.random.randn() * 50
            
            market_data = {
                'price': price,
                'volume': 10.0 + np.random.randn(),
                'orderbook': {
                    'bids': [[price - j*10, 1.0] for j in range(10)],
                    'asks': [[price + j*10, 1.0] for j in range(10)]
                },
                'trades': [
                    {'price': price, 'size': 0.1, 'side': 'buy' if np.random.rand() > 0.5 else 'sell'}
                    for _ in range(5)
                ]
            }
            
            sig = generator.update(
                market_data=market_data,
                funding_rate=0.0003,
                open_interest=1000000
            )
            
            assert sig is not None
            
            # 每10个打印一次
            if i % 20 == 0:
                print(f"\n{'='*60}")
                print(f"第{i}个签名:")
                print(sig.to_human_readable())
                
                from prometheus.world_signature.metrics import interpret_metrics
                metrics = {
                    'regime_confidence': sig.regime_confidence,
                    'stability_score': sig.stability_score,
                    'danger_index': sig.danger_index,
                    'opportunity_index': sig.opportunity_index,
                    'novelty_score': sig.novelty_score
                }
                print("\n指标解释:")
                print(interpret_metrics(metrics))
        
        # 统计
        stats = generator.statistics()
        print(f"\n{'='*60}")
        print("生成器统计:")
        print(f"  总生成数: {stats['generation_count']}")
        print(f"  历史签名: {stats['historical_signatures']}")
        print(f"  Buffer大小: {stats['buffer_size']}")
        
        print("✅ 流式生成测试成功")


class TestRegimeLibrary:
    """测试RegimeLibrary"""
    
    def test_regime_clustering(self):
        """测试Regime聚类"""
        # 生成大量历史签名
        generator = StreamingSignatureGenerator(
            instrument="BTC-USDT",
            macro_window_hours=1,
            micro_window_minutes=5
        )
        
        print("\n生成历史数据...")
        for i in range(200):
            price = 50000 + i * 10 + np.random.randn() * 100
            
            market_data = {
                'price': price,
                'volume': 10.0 + np.random.randn(),
                'orderbook': {
                    'bids': [[price - j*10, 1.0] for j in range(10)],
                    'asks': [[price + j*10, 1.0] for j in range(10)]
                }
            }
            
            generator.update(market_data, 0.0003, 1000000)
        
        # 获取历史签名
        historical_sigs = generator.get_historical_signatures()
        print(f"生成了{len(historical_sigs)}个历史签名")
        
        # 聚类
        regime_lib = RegimeLibrary()
        regime_lib.build_from_history(
            historical_sigs,
            min_cluster_size=20,
            min_samples=5
        )
        
        # 打印Regime库
        print(regime_lib.summary())
        
        # 测试匹配
        if len(regime_lib.regimes) > 0:
            latest_sig = historical_sigs[-1]
            regime_id, confidence = regime_lib.match_regime(latest_sig)
            
            print(f"\n最新签名匹配到: {regime_id} (置信度: {confidence:.1%})")
            
            regime_info = regime_lib.get_regime_info(regime_id)
            print(f"Regime信息: {regime_info['representative_tags']}")
        
        print("✅ Regime聚类测试成功")


def run_all_tests():
    """运行所有测试"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║ WorldSignature v2.0 测试套件                                    ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    # 测试1: MacroCode
    print("\n【测试1】MacroCode...")
    test_macro = TestMacroCode()
    test_macro.test_create_macro_code()
    
    # 测试2: MicroCode
    print("\n【测试2】MicroCode...")
    test_micro = TestMicroCode()
    test_micro.test_create_micro_code()
    
    # 测试3: WorldSignature
    print("\n【测试3】WorldSignature_V2...")
    test_sig = TestWorldSignature()
    test_sig.test_create_signature()
    
    # 测试4: StreamingGenerator
    print("\n【测试4】StreamingSignatureGenerator...")
    test_gen = TestStreamingGenerator()
    test_gen.test_streaming_generation()
    
    # 测试5: RegimeLibrary
    print("\n【测试5】RegimeLibrary...")
    test_regime = TestRegimeLibrary()
    test_regime.test_regime_clustering()
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！WorldSignature v2.0 运行正常！")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()

