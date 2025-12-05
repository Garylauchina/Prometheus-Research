@echo off
REM Prometheus v5.1 Additional Commits
REM Commit remaining files

echo ================================================================================
echo Prometheus v5.1 - Additional Commits
echo ================================================================================
echo.

REM Commit 1: Test scripts and logs
echo Adding test scripts and logs...
git add test_v5_integration.py 2>nul
git add test_extreme_stress.py 2>nul
git add PROJECT_STATUS_V5.1.md 2>nul
git add TODO_TOMORROW.md 2>nul
git add DAILY_LOG_2025-12-05.md 2>nul
git add extreme_stress_test_results.csv 2>nul

git commit -m "test: add integration and stress tests" -m "Add complete system integration test" -m "Add extreme market stress test" -m "Add project status and daily log"

echo Test scripts committed
echo.

REM Commit 2: Git automation scripts
echo Adding git automation scripts...
git add git_commit_v5.1_simple.bat 2>nul
git add git_commit_v5.1_simple.ps1 2>nul
git add GIT_COMMIT_README.md 2>nul

git commit -m "chore: add git commit automation scripts"

echo Git scripts committed
echo.

REM Summary
echo ================================================================================
echo Recent commits:
echo ================================================================================
git log --oneline -3

echo.
set /p push="Push to remote? (Y/N): "
if /i "%push%"=="Y" (
    echo Pushing to remote...
    git push
    echo Push completed!
) else (
    echo Skipped push
)

echo.
echo All done!
pause

