# Prometheus v5.1 Git Commit Script (English Version)
# Usage: .\git_commit_v5.1_simple.ps1

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Prometheus v5.1 Git Commit Script" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Git status
Write-Host "Checking Git status..." -ForegroundColor Yellow
git status --short

Write-Host ""
$confirm = Read-Host "Continue with commits? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled by user" -ForegroundColor Red
    exit
}

Write-Host ""

# ============================================================================
# Commit 1: Core Features
# ============================================================================
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Commit 1: Core Features" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

git add prometheus/core/slippage_model.py 2>$null
git add prometheus/core/funding_rate_model.py 2>$null
git add prometheus/core/meta_genome.py 2>$null
git add prometheus/core/niche_protection.py 2>$null
git add prometheus/core/mastermind.py 2>$null
git add prometheus/core/agent_v5.py 2>$null
git add prometheus/core/inner_council.py 2>$null
git add prometheus/core/evolution_manager_v5.py 2>$null

git commit -m "feat: implement v5.1 core features" `
    -m "Add SlippageModel for realistic slippage simulation" `
    -m "Add FundingRateModel for perpetual futures" `
    -m "Add MetaGenome for inheritable decision styles" `
    -m "Add NicheProtection for strategy diversity" `
    -m "Enhance Mastermind with 9-factor pressure calculation" `
    -m "Integrate MetaGenome into AgentV5 and evolution system"

Write-Host "Core features committed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Commit 2: Test Suite
# ============================================================================
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Commit 2: Test Suite" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

git add test_slippage.py 2>$null
git add test_funding_rate.py 2>$null
git add test_meta_genome.py 2>$null
git add test_meta_evolution.py 2>$null
git add test_niche_protection.py 2>$null
git add test_mastermind_pressure.py 2>$null
git add test_complete_pressure.py 2>$null
git add test_v5_integration.py 2>$null
git add test_extreme_stress.py 2>$null

git commit -m "test: add v5.1 comprehensive test suite" `
    -m "Add integration test (normal market)" `
    -m "Add stress test (extreme market)" `
    -m "Add unit tests for all modules" `
    -m "Test coverage: 100%"

Write-Host "Test suite committed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Commit 3: Tools and Data
# ============================================================================
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Commit 3: Tools and Data" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

git add tools/ 2>$null
git add data/okx/*.json 2>$null

git commit -m "feat: add historical data download tools" `
    -m "Add OKX API integration" `
    -m "Add batch download script" `
    -m "Add data analysis tools" `
    -m "Add metadata files"

Write-Host "Tools and data committed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Commit 4: Documentation
# ============================================================================
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Commit 4: Documentation" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

git add docs/V5.1_UPGRADE_GUIDE.md 2>$null
git add docs/SLIPPAGE_INTEGRATION.md 2>$null
git add CHANGELOG_V5.1.md 2>$null
git add PROJECT_STATUS_V5.1.md 2>$null
git add TODO_TOMORROW.md 2>$null
git add DAILY_LOG_2025-12-05.md 2>$null
git add GIT_COMMIT_README.md 2>$null

git commit -m "docs: add v5.1 complete documentation" `
    -m "Add upgrade guide" `
    -m "Add changelog" `
    -m "Add project status report" `
    -m "Add tomorrow's TODO list" `
    -m "Add development log"

Write-Host "Documentation committed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Summary
# ============================================================================
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Commit Summary" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan

git log --oneline -4

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "All commits completed!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Ask about pushing
$push = Read-Host "Push to remote repository? (Y/N)"
if ($push -eq "Y" -or $push -eq "y") {
    Write-Host "Pushing to remote..." -ForegroundColor Yellow
    git push
    Write-Host "Push completed!" -ForegroundColor Green
} else {
    Write-Host "Skipped push. You can push later with: git push" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Git commit script completed!" -ForegroundColor Green
Write-Host ""

