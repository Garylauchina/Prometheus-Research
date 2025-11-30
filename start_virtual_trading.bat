@echo off
REM Prometheus v3.0 虚拟交易启动脚本 (Windows版本)
REM 提供简化的部署和运行界面，支持性能测试选项

echo ==========================================
echo Prometheus v3.0 虚拟交易启动脚本
==========================================

REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: Python 未安装
    pause
    exit /b 1
)

REM 检查项目目录结构
if not exist "run_virtual_trading.py" ( 
    echo 错误: 请在Prometheus项目根目录下运行此脚本
    pause
    exit /b 1
)

REM 解析命令行参数
set "PERFORMANCE_TEST=false"
set "DURATION=3600"
set "LOG_LEVEL=INFO"

:parse_args
if "%~1"=="--performance" (
    set "PERFORMANCE_TEST=true"
    shift
    goto parse_args
)
if "%~1"=="--duration" (
    set "DURATION=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--log-level" (
    set "LOG_LEVEL=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo 使用方法: %0 [选项]
    echo 选项:
    echo   --performance      运行性能测试模式
    echo   --duration ^<秒数^>   设置运行时长（默认: 3600秒=1小时）
    echo   --log-level ^<级别^>  设置日志级别 (DEBUG, INFO, WARNING, ERROR)
    echo   --help             显示此帮助信息
    pause
    exit /b 0
)
if not "%~1"=="" (
    echo 警告: 未知参数 %1
    shift
    goto parse_args
)

REM 检查配置文件
if not exist "config_virtual.py" (
    echo 警告: 未找到config_virtual.py文件
    echo 正在创建默认配置文件...
    
    (echo """
    echo Prometheus v3.0 虚拟交易配置文件
    echo """"
    echo.
    echo CONFIG_VIRTUAL_TRADING = {
    echo     'initial_capital': 10000.0,
    echo     'initial_agents': 10,
    echo     'max_agents': 50,
    echo     'trading_interval_seconds': 5,
    echo     'max_daily_loss_pct': 10.0,  # 每日最大亏损百分比
    echo     'max_drawdown_pct': 20.0,    # 最大回撤百分比
    echo     'performance_test': False,
    echo     'performance_metrics_enabled': True,
    echo     'api_call_limit_per_minute': 600,
    echo     'cache_ttl_seconds': 10,
    echo     'concurrent_agents_threshold': 15,
    echo     
    echo     'logging': {
    echo         'dir': 'logs',
    echo         'file_prefix': 'prometheus_virtual',
    echo         'level': 'INFO',
    echo         'max_size_mb': 100,
    echo         'backup_count': 10
    echo     },
    echo     
    echo     'risk': {
    echo         'max_position_size_pct': 5.0,  # 最大仓位百分比
    echo         'max_leverage': 1.0,          # 最大杠杆倍数
    echo         'stop_loss_pct': 2.0,         # 止损百分比
    echo         'take_profit_pct': 5.0,       # 止盈百分比
    echo         'max_open_trades': 5          # 最大开仓数量
    echo     },
    echo     
    echo     'okx_api': {
    echo         'api_key': 'your_api_key',
    echo         'secret_key': 'your_secret_key',
    echo         'passphrase': 'your_passphrase',
    echo         'use_testnet': True
    echo     }
    echo }
    ) > config_virtual.py
    
    echo ✓ 已创建默认config_virtual.py
    echo 请编辑config_virtual.py，添加您的OKX API凭证
    pause
    exit /b 0
)

REM 检查虚拟环境
if not exist "venv" (
    echo 警告: 未找到虚拟环境venv
    echo 正在创建虚拟环境...
    
    python -m venv venv
    
    if %errorlevel% equ 0 (
        echo ✓ 已创建虚拟环境
        echo 正在安装依赖...
        
        REM 激活虚拟环境并安装依赖
        if exist "venv\Scripts\activate" (
            call venv\Scripts\activate
        )
        
        REM 升级pip
        python -m pip install --upgrade pip
        
        REM 安装依赖
        if exist "requirements.txt" (
            python -m pip install -r requirements.txt
        ) else (
            echo 警告: 未找到requirements.txt，安装基本依赖
            python -m pip install okx pandas numpy matplotlib seaborn colorlog
        )
        
        echo ✓ 依赖安装完成
    ) else (
        echo 错误: 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 正在激活虚拟环境...
if exist "venv\Scripts\activate" (
    call venv\Scripts\activate
) else (
    echo 警告: 无法找到激活脚本，请手动激活虚拟环境
)

REM 检查API凭证（简化检查）
echo 正在检查配置...
finderstr /C:"your_api_key" config_virtual.py >nul
if %errorlevel% equ 0 (
    echo 错误: config_virtual.py中的API凭证未设置
    echo 请编辑config_virtual.py，添加您的OKX API凭证
    pause
    exit /b 1
)

REM 开始运行
echo ✓ 所有检查通过
==========================================

if "%PERFORMANCE_TEST%"=="true" (
    echo 启动性能测试模式...
    echo 持续时间: %DURATION%秒
    echo 日志级别: %LOG_LEVEL%
    echo ==========================================
    
    python test_performance.py --duration %DURATION% --log-level %LOG_LEVEL%
) else (
    echo 启动虚拟交易模式...
    echo 持续时间: %DURATION%秒 (%DURATION%/3600小时)
    echo 日志级别: %LOG_LEVEL%
    echo ==========================================
    echo 按 Ctrl+C 停止交易
    echo ==========================================
    
    python run_virtual_trading.py --duration %DURATION% --log-level %LOG_LEVEL%
)

set exit_code=%errorlevel%

if %exit_code% equ 0 (
    echo.
    echo ✓ 程序正常退出
) else (
    echo.
    echo ✗ 程序异常退出 (退出码: %exit_code%)
)

REM 显示运行建议
echo.
echo 运行建议:
echo 1. 查看logs目录下的交易日志了解详情
echo 2. 对于性能测试，检查performance_charts目录下的性能报告
echo 3. 如需系统级服务，使用systemd服务配置文件

echo.
echo ==========================================
echo 谢谢使用Prometheus v3.0
echo ==========================================

pause
