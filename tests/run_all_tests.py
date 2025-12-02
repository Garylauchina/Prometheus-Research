"""
运行所有测试 - Prometheus v4.0

按顺序运行：
1. 单元测试（技术指标、市场状态、公告板）
2. 集成测试（三层架构联动）
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_test_module(module_name):
    """运行单个测试模块"""
    print(f"\n运行: {module_name}")
    print("-" * 70)
    
    try:
        # 动态导入测试模块
        test_module = __import__(module_name, fromlist=['run_tests'])
        
        # 运行测试
        if hasattr(test_module, 'run_tests'):
            success = test_module.run_tests()
        else:
            # 如果没有run_tests函数，使用unittest.main
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            success = result.wasSuccessful()
        
        return success
    except Exception as e:
        print(f"\n❌ 测试模块 {module_name} 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    start_time = datetime.now()
    
    print_header("Prometheus v4.0 - 完整测试套件")
    print(f"\n开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试模块列表（按执行顺序）
    test_modules = [
        # 单元测试
        ('test_indicator_calculator', '技术指标计算器测试'),
        ('test_market_state_analyzer', '市场状态分析器测试'),
        ('test_bulletin_board', '公告板系统测试'),
        
        # 集成测试
        ('test_integration_v4', '三层架构集成测试'),
    ]
    
    results = {}
    
    # 运行每个测试模块
    for module_name, description in test_modules:
        print_header(description)
        success = run_test_module(module_name)
        results[description] = success
    
    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_header("测试总结")
    
    print(f"\n完成时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration:.2f}秒")
    
    print("\n各模块测试结果:")
    print("-" * 70)
    
    all_passed = True
    for description, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{description:.<50} {status}")
        if not success:
            all_passed = False
    
    print("-" * 70)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        print("\n✅ Prometheus v4.0 核心功能验证成功！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

