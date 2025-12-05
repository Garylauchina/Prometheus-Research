@echo off
chcp 65001 >nul
echo ================================================================================
echo Git Commit - Prometheus v5.1.3 Parameter Optimization
echo ================================================================================
echo.

echo [1/4] Adding modified core files...
git add prometheus/core/evolution_manager_v5.py
git add prometheus/core/niche_protection.py
echo   - evolution_manager_v5.py (dynamic mutation + forced breeding)
echo   - niche_protection.py (parameter optimization)
echo.

echo [2/4] Adding test files...
git add test_extreme_stress.py
git add test_extreme_stress_batch.py
echo   - test_extreme_stress.py (auto cleanup)
echo   - test_extreme_stress_batch.py (batch testing)
echo.

echo [3/4] Adding documentation...
git add OPTIMIZATION_SUMMARY_V5.1.3.md
echo   - OPTIMIZATION_SUMMARY_V5.1.3.md (complete summary)
echo.

echo [4/4] Committing...
git commit -m "feat(v5.1.3): parameter optimization complete - diversity protection and stability guarantee" ^
           -m "" ^
           -m "Core Improvements:" ^
           -m "- Dynamic mutation rate (10%% -> 60%% based on gene entropy)" ^
           -m "- Similarity-based mating control (prevent inbreeding)" ^
           -m "- Progressive threshold relaxation (85%% -> 50%%)" ^
           -m "- Forced breeding mechanism (guarantee population stability)" ^
           -m "- Enhanced niche protection (stronger minority protection)" ^
           -m "" ^
           -m "Test Results:" ^
           -m "- Gene entropy: 0.057 -> 0.099 (+73.7%%)" ^
           -m "- Population stability: 100%% (3/3 tests)" ^
           -m "- System robustness: Extreme pressure test passed" ^
           -m "" ^
           -m "Files Changed:" ^
           -m "- prometheus/core/evolution_manager_v5.py" ^
           -m "- prometheus/core/niche_protection.py" ^
           -m "- test_extreme_stress.py" ^
           -m "- test_extreme_stress_batch.py (new)" ^
           -m "- OPTIMIZATION_SUMMARY_V5.1.3.md (new)"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo Commit successful!
    echo ================================================================================
    echo.
    
    set /p push="Push to remote repository? (Y/N): "
    if /i "%push%"=="Y" (
        echo.
        echo Pushing to origin/develop/v5.0...
        git push
        echo.
        echo Done!
    ) else (
        echo.
        echo Commit saved locally. You can push later with: git push
    )
) else (
    echo.
    echo Commit failed! Please check the error messages above.
)

echo.
pause

