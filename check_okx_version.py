import sys
import importlib

# 打印Python版本信息
print(f"Python版本: {sys.version}")

# 尝试导入okx包
print("\n检查okx包导入:")
try:
    import okx
    print(f"成功导入okx包")
    print(f"okx包版本: {getattr(okx, '__version__', '未知')}")
    
    # 检查okx包的内容
    print("\nokx包内容:")
    print(dir(okx))
    
    # 尝试导入MarketData
    print("\n尝试导入MarketData:")
    try:
        from okx import MarketData
        print("成功导入MarketData")
        print(f"MarketData内容: {dir(MarketData)}")
    except ImportError as e:
        print(f"导入MarketData失败: {e}")
        
    # 尝试直接导入子模块
    print("\n尝试直接导入子模块:")
    try:
        # 检查所有可能的导入方式
        import okx.MarketData
        print("存在okx.MarketData子模块")
    except ImportError:
        print("不存在okx.MarketData子模块")
        
except ImportError as e:
    print(f"导入okx包失败: {e}")

# 检查已安装的包信息
print("\n检查已安装的包:")
try:
    import pkg_resources
    installed_packages = [pkg.key for pkg in pkg_resources.working_set]
    if 'okx' in installed_packages:
        print(f"okx包已安装")
        okx_version = [pkg.version for pkg in pkg_resources.working_set if pkg.key == 'okx'][0]
        print(f"已安装的okx包版本: {okx_version}")
    else:
        print("okx包未安装")
except ImportError:
    print("无法检查已安装的包")
