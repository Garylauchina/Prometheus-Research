@echo off
echo ========================================
echo   Prometheus v4.0 - 6小时测试启动器
echo ========================================
echo.
echo 测试配置：
echo   时长: 6小时 (360分钟)
echo   间隔: 2分钟 (120秒)
echo   日志: 自动保存
echo.
echo 按任意键开始测试...
pause > nul

python run_okx_paper_test.py

echo.
echo ========================================
echo   测试已完成或中断
echo ========================================
pause

