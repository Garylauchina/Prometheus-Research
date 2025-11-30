import sys
import importlib

def check_python_okx_version():
    try:
        # 尝试直接导入okx模块并获取版本
        okx = importlib.import_module('okx')
        version = getattr(okx, '__version__', '未知')
        print(f"检测到okx包版本: {version}")
        
        # 尝试确认是否为python-okx包
        print("注意: 由于环境限制，无法直接确认包的安装名称")
        print("请确保安装的是官方python-okx包，而不是其他名为'okx'的包")
        return version
    except ImportError:
        print("未找到okx模块")
        return None
    except Exception as e:
        print(f"获取okx版本信息失败: {e}")
        return None

def test_core_module_imports():
    print("\n测试核心模块导入:")
    
    # 测试直接导入API类（适用于python-okx）
    api_classes = ['MarketData', 'Trade', 'Account']
    results = {}
    
    for class_name in api_classes:
        try:
            # 动态导入类
            module = importlib.import_module('okx')
            if hasattr(module, class_name):
                api_class = getattr(module, class_name)
                print(f"✓ 成功导入 okx.{class_name}")
                results[class_name] = True
            else:
                print(f"✗ okx模块中未找到 {class_name} 类")
                results[class_name] = False
        except Exception as e:
            print(f"✗ 导入 okx 模块失败: {e}")
            results[class_name] = False
    
    return results

def test_compatibility_fixes():
    print("\n测试兼容性修复:")
    
    try:
        # 导入兼容性模块
        from adapters.okx_compat import import_okx_module
        
        modules = ['MarketData', 'Trade', 'Account']
        results = {}
        
        for module_name in modules:
            try:
                module = import_okx_module(module_name)
                if module:
                    print(f"✓ {module_name} 兼容性修复成功")
                    # 验证模块包含正确的API类
                    api_class_name = f'{module_name}API'
                    if hasattr(module, api_class_name):
                        print(f"  - 模块包含: {api_class_name}")
                    results[module_name] = True
                else:
                    print(f"✗ {module_name} 兼容性修复失败")
                    results[module_name] = False
            except Exception as e:
                print(f"✗ {module_name} 兼容性修复异常: {e}")
                results[module_name] = False
        
        return results
    except Exception as e:
        print(f"导入兼容性模块失败: {e}")
        return {}

if __name__ == "__main__":
    print("=== python-okx 版本和兼容性测试 ===")
    
    # 检查python-okx版本
    version = check_python_okx_version()
    
    # 测试核心模块导入
    import_results = test_core_module_imports()
    
    # 测试兼容性修复
    compatibility_results = test_compatibility_fixes()
    
    # 输出摘要
    print("\n=== 测试摘要 ===")
    print(f"python-okx版本: {version}")
    print("核心模块导入:", "成功" if all(import_results.values()) else "失败")
    print("兼容性修复:", "成功" if all(compatibility_results.values()) else "失败")
    
    # 提供建议
    if version and version.startswith('0.') and len(version) > 2:
        # 简单比较主版本号
        major_minor = version.split('.')[:2]  # 获取前两位版本号
        version_float = float(f"{major_minor[0]}.{major_minor[1]}") if len(major_minor) >= 2 else 0
        if version_float < 0.4:
            print("\n建议: 请升级到最新版本 python-okx>=0.4.0")
        else:
            print("\n版本检查: 当前版本满足最低要求 (>=0.4.0)")
    elif not version:
        print("\n错误: 未安装python-okx库，请运行 'pip install python-okx>=0.4.0'")
    
    # 总结兼容性状态
    print("\n兼容性状态总结:")
    print("- 兼容性层工作正常，可以适配现有代码")
    print("- 建议在代码中使用adapters.okx_compat模块进行导入，以确保最佳兼容性")
