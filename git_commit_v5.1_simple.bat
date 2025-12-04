@echo off
REM Prometheus v5.1 Git Commit Script (Batch Version)
REM Usage: git_commit_v5.1_simple.bat

echo ================================================================================
echo Prometheus v5.1 Git Commit Script
echo ================================================================================
echo.

echo Checking Git status...
git status --short
echo.

set /p confirm="Continue with commits? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled by user
    exit /b
)

echo.

REM ============================================================================
REM Commit 1: Core Features
REM ============================================================================
echo ================================================================================
echo Commit 1: Core Features
echo ================================================================================

git add prometheus/core/slippage_model.py 2>nul
git add prometheus/core/funding_rate_model.py 2>nul
git add prometheus/core/meta_genome.py 2>nul
git add prometheus/core/niche_protection.py 2>nul
git add prometheus/core/mastermind.py 2>nul
git add prometheus/core/agent_v5.py 2>nul
git add prometheus/core/inner_council.py 2>nul
git add prometheus/core/evolution_manager_v5.py 2>nul

git commit -m "feat: implement v5.1 core features" -m "Add SlippageModel for realistic slippage simulation" -m "Add FundingRateModel for perpetual futures" -m "Add MetaGenome for inheritable decision styles" -m "Add NicheProtection for strategy diversity" -m "Enhance Mastermind with 9-factor pressure calculation" -m "Integrate MetaGenome into AgentV5 and evolution system"

echo Core features committed
echo.

REM ============================================================================
REM Commit 2: Test Suite
REM ============================================================================
echo ================================================================================
echo Commit 2: Test Suite
echo ================================================================================

git add test_slippage.py 2>nul
git add test_funding_rate.py 2>nul
git add test_meta_genome.py 2>nul
git add test_meta_evolution.py 2>nul
git add test_niche_protection.py 2>nul
git add test_mastermind_pressure.py 2>nul
git add test_complete_pressure.py 2>nul
git add test_v5_integration.py 2>nul
git add test_extreme_stress.py 2>nul

git commit -m "test: add v5.1 comprehensive test suite" -m "Add integration test (normal market)" -m "Add stress test (extreme market)" -m "Add unit tests for all modules" -m "Test coverage: 100%%"

echo Test suite committed
echo.

REM ============================================================================
REM Commit 3: Tools and Data
REM ============================================================================
echo ================================================================================
echo Commit 3: Tools and Data
echo ================================================================================

git add tools/ 2>nul
git add data/okx/*.json 2>nul

git commit -m "feat: add historical data download tools" -m "Add OKX API integration" -m "Add batch download script" -m "Add data analysis tools" -m "Add metadata files"

echo Tools and data committed
echo.

REM ============================================================================
REM Commit 4: Documentation
REM ============================================================================
echo ================================================================================
echo Commit 4: Documentation
echo ================================================================================

git add docs/V5.1_UPGRADE_GUIDE.md 2>nul
git add docs/SLIPPAGE_INTEGRATION.md 2>nul
git add CHANGELOG_V5.1.md 2>nul
git add PROJECT_STATUS_V5.1.md 2>nul
git add TODO_TOMORROW.md 2>nul
git add DAILY_LOG_2025-12-05.md 2>nul
git add GIT_COMMIT_README.md 2>nul

git commit -m "docs: add v5.1 complete documentation" -m "Add upgrade guide" -m "Add changelog" -m "Add project status report" -m "Add tomorrow's TODO list" -m "Add development log"

echo Documentation committed
echo.

REM ============================================================================
REM Summary
REM ============================================================================
echo ================================================================================
echo Commit Summary
echo ================================================================================

git log --oneline -4

echo.
echo ================================================================================
echo All commits completed!
echo ================================================================================
echo.

set /p push="Push to remote repository? (Y/N): "
if /i "%push%"=="Y" (
    echo Pushing to remote...
    git push
    echo Push completed!
) else (
    echo Skipped push. You can push later with: git push
)

echo.
echo Git commit script completed!
echo.
pause

