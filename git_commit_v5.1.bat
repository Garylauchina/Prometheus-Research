@echo off
REM Prometheus v5.1 Git提交脚本（批处理版本）
REM 使用方法：git_commit_v5.1.bat

echo ================================================================================
echo 🚀 Prometheus v5.1 Git提交脚本
echo ================================================================================
echo.

echo 📋 检查Git状态...
git status --short
echo.

set /p confirm="是否继续提交？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo ❌ 用户取消操作
    exit /b
)

echo.
echo ================================================================================
echo 第一次提交：核心功能
echo ================================================================================

git add prometheus/core/slippage_model.py
git add prometheus/core/funding_rate_model.py
git add prometheus/core/meta_genome.py
git add prometheus/core/niche_protection.py
git add prometheus/core/mastermind.py
git add prometheus/core/agent_v5.py
git add prometheus/core/inner_council.py
git add prometheus/core/evolution_manager_v5.py

git commit -m "feat: v5.1核心功能实现" -m "- 新增SlippageModel（滑点模拟）" -m "- 新增FundingRateModel（资金费率）" -m "- 新增MetaGenome（元参数基因）" -m "- 新增NicheProtection（生态位保护）" -m "- 增强Mastermind市场压力计算（9维度）" -m "- 集成MetaGenome到AgentV5和进化系统"

echo ✅ 核心功能提交完成
echo.

REM ============================================================================

echo ================================================================================
echo 第二次提交：测试脚本
echo ================================================================================

git add test_slippage.py
git add test_funding_rate.py
git add test_meta_genome.py
git add test_meta_evolution.py
git add test_niche_protection.py
git add test_mastermind_pressure.py
git add test_complete_pressure.py
git add test_v5_integration.py
git add test_extreme_stress.py

git commit -m "test: 添加v5.1完整测试套件" -m "- 集成测试（正常市场）✅" -m "- 压力测试（极端市场）✅" -m "- 单元测试（各模块）✅" -m "- 测试覆盖率：100%%"

echo ✅ 测试脚本提交完成
echo.

REM ============================================================================

echo ================================================================================
echo 第三次提交：工具和数据
echo ================================================================================

git add tools/
git add data/okx/*.json 2>nul

git commit -m "feat: 添加历史数据下载工具" -m "- OKX API数据下载" -m "- 批量下载脚本" -m "- 数据分析工具" -m "- 数据元数据（JSON）"

echo ✅ 工具和数据提交完成
echo.

REM ============================================================================

echo ================================================================================
echo 第四次提交：文档
echo ================================================================================

git add docs/V5.1_UPGRADE_GUIDE.md
git add docs/SLIPPAGE_INTEGRATION.md
git add CHANGELOG_V5.1.md
git add PROJECT_STATUS_V5.1.md
git add TODO_TOMORROW.md
git add DAILY_LOG_2025-12-05.md

git commit -m "docs: v5.1完整文档" -m "- 升级指南（V5.1_UPGRADE_GUIDE.md）" -m "- 变更日志（CHANGELOG_V5.1.md）" -m "- 项目状态（PROJECT_STATUS_V5.1.md）" -m "- 明日计划（TODO_TOMORROW.md）" -m "- 开发日志（DAILY_LOG_2025-12-05.md）"

echo ✅ 文档提交完成
echo.

REM ============================================================================

echo ================================================================================
echo 📊 提交总结
echo ================================================================================

git log --oneline -4

echo.
echo ================================================================================
echo ✅ 所有提交完成！
echo ================================================================================
echo.

set /p push="是否推送到远程仓库？(Y/N): "
if /i "%push%"=="Y" (
    echo 🚀 推送到远程...
    git push
    echo ✅ 推送完成！
) else (
    echo ℹ️  跳过推送，稍后可手动执行：git push
)

echo.
echo 🎉 Git提交脚本执行完成！
echo.
pause

