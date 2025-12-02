"""
快速测试 - 实时输出版本

逐个运行测试，实时显示进度
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from datetime import datetime


def run_single_test_file(test_file, description):
    """运行单个测试文件"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}\n")
    
    try:
        # 导入测试模块
        test_module = __import__(test_file, fromlist=[''])
        
        # 加载测试
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # 运行测试（高详细度）
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # 返回结果
        return result.wasSuccessful(), result.testsRun, len(result.failures), len(result.errors)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0, 1


def main():
    """主函数"""
    print("\n" + "="*70)
    print("  Prometheus v4.0 - 快速测试套件")
    print("="*70)
    
    start_time = datetime.now()
    print(f"\n开始时间: {start_time.strftime('%H:%M:%S')}\n")
    
    # 测试列表
    tests = [
        ("test_indicator_calculator", "1. 技术指标计算器测试"),
        ("test_market_state_analyzer", "2. 市场状态分析器测试"),
        ("test_bulletin_board", "3. 公告板系统测试"),
        ("test_integration_v4", "4. 三层架构集成测试"),
    ]
    
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    # 逐个运行
    for i, (test_file, description) in enumerate(tests, 1):
        print(f"\n>>> 正在运行 [{i}/{len(tests)}]: {description}")
        success, tests_run, failures, errors = run_single_test_file(test_file, description)
        
        results.append({
            'name': description,
            'success': success,
            'tests': tests_run,
            'failures': failures,
            'errors': errors
        })
        
        total_tests += tests_run
        total_failures += failures
        total_errors += errors
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"\n{status} - {tests_run}个测试, {failures}个失败, {errors}个错误")
    
    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)
    
    print(f"\n完成时间: {end_time.strftime('%H:%M:%S')}")
    print(f"总耗时: {duration:.2f}秒")
    
    print(f"\n总计:")
    print(f"  运行测试: {total_tests}")
    print(f"  成功: {total_tests - total_failures - total_errors}")
    print(f"  失败: {total_failures}")
    print(f"  错误: {total_errors}")
    
    print(f"\n各模块详情:")
    print("-"*70)
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['name']:.<50} {r['tests']}个测试")
        if r['failures'] > 0:
            print(f"    失败: {r['failures']}")
        if r['errors'] > 0:
            print(f"    错误: {r['errors']}")
    print("-"*70)
    
    all_passed = all(r['success'] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败")
        return 1


if __name__ == '__main__':
    exit_code = main()
    print(f"\n退出代码: {exit_code}\n")
    sys.exit(exit_code)

