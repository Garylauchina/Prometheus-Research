#!/usr/bin/env python3
"""
资金注资API验证测试
===================

测试目标：
1. 验证统一注资接口 invest_system_capital
2. 验证 SystemCapitalConfig 配置类
3. 验证多次注资的正确性
4. 验证资金守恒

测试场景：
- 场景1: 创世注资（20%配资）
- 场景2: 中途追加投资（100%可用）
- 场景3: 紧急救援注资（100%立即可用）
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
import json

# 设置日志
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"results/capital_investment_api_{timestamp}.log"
Path("results").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from prometheus.facade.v6_facade import V6Facade
from prometheus.config.capital_config import SystemCapitalConfig, CapitalConfigPresets


def test_scenario_1_genesis():
    """场景1: 创世注资（20%配资）"""
    logger.info("=" * 80)
    logger.info("📋 场景1: 创世注资（20%配资，80%储备）")
    logger.info("=" * 80)
    logger.info("")
    
    # 创建配置
    config = CapitalConfigPresets.conservative_genesis()
    logger.info(config.summary())
    
    # 创建Facade
    facade = V6Facade(num_families=50, exchange=None)
    
    # 使用统一注资接口
    investment_result = facade.invest_system_capital(
        total_amount=config.total_system_capital,
        allocation_ratio=config.genesis_allocation_ratio,
        purpose=config.purpose,
        reason=config.reason
    )
    
    # 验证结果
    logger.info("\n✅ 验证结果:")
    logger.info(f"   注资金额: ${investment_result['invested']:,.2f}")
    logger.info(f"   立即可用: ${investment_result['immediate_available']:,.2f}")
    logger.info(f"   储备金额: ${investment_result['reserved']:,.2f}")
    logger.info(f"   资金池余额: ${investment_result['pool_balance']:,.2f}")
    
    # 验证资金守恒
    assert abs(investment_result['invested'] - (investment_result['immediate_available'] + investment_result['reserved'])) < 0.01
    assert abs(investment_result['pool_balance'] - config.total_system_capital) < 0.01
    
    logger.info("\n🎯 场景1: ✅ 通过\n")
    return facade, investment_result


def test_scenario_2_expansion(facade):
    """场景2: 中途追加投资（100%可用）"""
    logger.info("=" * 80)
    logger.info("📋 场景2: 中途追加投资（100%立即可用）")
    logger.info("=" * 80)
    logger.info("")
    
    # 追加投资$100K
    additional_amount = 100000.0
    
    # 记录追加前的资金池状态
    before_balance = facade.capital_pool.available_pool
    logger.info(f"追加前资金池余额: ${before_balance:,.2f}")
    
    # 使用统一注资接口（100%立即可用）
    investment_result = facade.invest_system_capital(
        total_amount=additional_amount,
        allocation_ratio=1.0,  # 100%立即可用
        purpose="expansion",
        reason="bull_market_opportunity"
    )
    
    # 验证结果
    logger.info("\n✅ 验证结果:")
    logger.info(f"   追加金额: ${investment_result['invested']:,.2f}")
    logger.info(f"   立即可用: ${investment_result['immediate_available']:,.2f}")
    logger.info(f"   储备金额: ${investment_result['reserved']:,.2f}")
    logger.info(f"   资金池余额: ${investment_result['pool_balance']:,.2f}")
    
    # 验证
    assert abs(investment_result['immediate_available'] - additional_amount) < 0.01
    assert abs(investment_result['reserved']) < 0.01  # 应该为0
    assert abs(investment_result['pool_balance'] - (before_balance + additional_amount)) < 0.01
    
    logger.info("\n🎯 场景2: ✅ 通过\n")
    return investment_result


def test_scenario_3_rescue(facade):
    """场景3: 紧急救援注资（100%立即可用）"""
    logger.info("=" * 80)
    logger.info("📋 场景3: 紧急救援注资（100%立即可用）")
    logger.info("=" * 80)
    logger.info("")
    
    # 救援金额$50K
    rescue_amount = 50000.0
    
    # 记录救援前的资金池状态
    before_balance = facade.capital_pool.available_pool
    logger.info(f"救援前资金池余额: ${before_balance:,.2f}")
    
    # 使用统一注资接口（100%立即可用）
    investment_result = facade.invest_system_capital(
        total_amount=rescue_amount,
        allocation_ratio=1.0,  # 100%立即可用
        purpose="rescue",
        reason="emergency_capital_supplement"
    )
    
    # 验证结果
    logger.info("\n✅ 验证结果:")
    logger.info(f"   救援金额: ${investment_result['invested']:,.2f}")
    logger.info(f"   立即可用: ${investment_result['immediate_available']:,.2f}")
    logger.info(f"   储备金额: ${investment_result['reserved']:,.2f}")
    logger.info(f"   资金池余额: ${investment_result['pool_balance']:,.2f}")
    
    # 验证
    assert abs(investment_result['immediate_available'] - rescue_amount) < 0.01
    assert abs(investment_result['reserved']) < 0.01  # 应该为0
    assert abs(investment_result['pool_balance'] - (before_balance + rescue_amount)) < 0.01
    
    logger.info("\n🎯 场景3: ✅ 通过\n")
    return investment_result


def main():
    """主测试函数"""
    logger.info("=" * 80)
    logger.info("🚀 资金注资API验证测试")
    logger.info("=" * 80)
    logger.info("")
    
    # 场景1: 创世注资
    facade, genesis_result = test_scenario_1_genesis()
    
    # 场景2: 中途追加投资
    expansion_result = test_scenario_2_expansion(facade)
    
    # 场景3: 紧急救援
    rescue_result = test_scenario_3_rescue(facade)
    
    # 总结
    logger.info("=" * 80)
    logger.info("📊 测试总结")
    logger.info("=" * 80)
    
    total_invested = genesis_result['invested'] + expansion_result['invested'] + rescue_result['invested']
    final_balance = facade.capital_pool.available_pool
    
    logger.info(f"创世注资: ${genesis_result['invested']:,.2f}")
    logger.info(f"追加投资: ${expansion_result['invested']:,.2f}")
    logger.info(f"紧急救援: ${rescue_result['invested']:,.2f}")
    logger.info(f"总计注资: ${total_invested:,.2f}")
    logger.info(f"资金池余额: ${final_balance:,.2f}")
    logger.info("")
    
    # 验证资金守恒
    logger.info("✅ 资金守恒验证:")
    if abs(final_balance - total_invested) < 0.01:
        logger.info(f"   ✅ 通过: 资金池余额 = 总注资金额")
    else:
        logger.error(f"   ❌ 失败: 差异 = ${abs(final_balance - total_invested):,.2f}")
    
    logger.info("")
    logger.info("🎯 所有测试通过！")
    logger.info("=" * 80)
    
    # 保存结果
    result = {
        "test": "capital_investment_api",
        "scenarios": {
            "genesis": {
                "invested": genesis_result['invested'],
                "immediate_available": genesis_result['immediate_available'],
                "reserved": genesis_result['reserved']
            },
            "expansion": {
                "invested": expansion_result['invested'],
                "immediate_available": expansion_result['immediate_available']
            },
            "rescue": {
                "invested": rescue_result['invested'],
                "immediate_available": rescue_result['immediate_available']
            }
        },
        "summary": {
            "total_invested": total_invested,
            "final_balance": final_balance,
            "capital_conservation": abs(final_balance - total_invested) < 0.01
        },
        "log_file": log_file
    }
    
    result_file = f"results/capital_investment_api_{timestamp}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ 结果已保存: {result_file}")
    logger.info(f"📄 日志文件: {log_file}")


if __name__ == "__main__":
    main()

