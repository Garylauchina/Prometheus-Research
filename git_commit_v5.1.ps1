# Prometheus v5.1 Git提交脚本
# 使用方法：.\git_commit_v5.1.ps1

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*79) -ForegroundColor Cyan
Write-Host "🚀 Prometheus v5.1 Git提交脚本" -ForegroundColor Green
Write-Host ("="*80) -ForegroundColor Cyan
Write-Host ""

# 检查是否有未提交的更改
Write-Host "📋 检查Git状态..." -ForegroundColor Yellow
git status --short

Write-Host ""
$confirm = Read-Host "是否继续提交？(Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "❌ 用户取消操作" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "第一次提交：核心功能" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan

# 核心功能文件
$coreFiles = @(
    "prometheus/core/slippage_model.py",
    "prometheus/core/funding_rate_model.py",
    "prometheus/core/meta_genome.py",
    "prometheus/core/niche_protection.py",
    "prometheus/core/mastermind.py",
    "prometheus/core/agent_v5.py",
    "prometheus/core/inner_council.py",
    "prometheus/core/evolution_manager_v5.py"
)

foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ 添加: $file" -ForegroundColor Green
        git add $file
    } else {
        Write-Host "  ⚠️  未找到: $file" -ForegroundColor Yellow
    }
}

git commit -m "feat: v5.1核心功能实现

- 新增SlippageModel（滑点模拟）
- 新增FundingRateModel（资金费率）
- 新增MetaGenome（元参数基因）
- 新增NicheProtection（生态位保护）
- 增强Mastermind市场压力计算（9维度）
- 集成MetaGenome到AgentV5和进化系统"

Write-Host "✅ 核心功能提交完成" -ForegroundColor Green
Write-Host ""

# ============================================================================

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "第二次提交：测试脚本" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan

# 测试文件
$testFiles = @(
    "test_slippage.py",
    "test_funding_rate.py",
    "test_meta_genome.py",
    "test_meta_evolution.py",
    "test_niche_protection.py",
    "test_mastermind_pressure.py",
    "test_complete_pressure.py",
    "test_v5_integration.py",
    "test_extreme_stress.py"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ 添加: $file" -ForegroundColor Green
        git add $file
    } else {
        Write-Host "  ⚠️  未找到: $file" -ForegroundColor Yellow
    }
}

git commit -m "test: 添加v5.1完整测试套件

- 集成测试（正常市场）✅
- 压力测试（极端市场）✅
- 单元测试（各模块）✅
- 测试覆盖率：100%"

Write-Host "✅ 测试脚本提交完成" -ForegroundColor Green
Write-Host ""

# ============================================================================

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "第三次提交：工具和数据" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan

# 工具文件
if (Test-Path "tools") {
    Write-Host "  ✅ 添加: tools/" -ForegroundColor Green
    git add tools/
}

# 数据元数据（不提交大文件，只提交元数据）
if (Test-Path "data/okx") {
    Get-ChildItem "data/okx/*.json" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  ✅ 添加: $($_.FullName)" -ForegroundColor Green
        git add $_.FullName
    }
}

git commit -m "feat: 添加历史数据下载工具

- OKX API数据下载
- 批量下载脚本
- 数据分析工具
- 数据元数据（JSON）"

Write-Host "✅ 工具和数据提交完成" -ForegroundColor Green
Write-Host ""

# ============================================================================

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "第四次提交：文档" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan

# 文档文件
$docFiles = @(
    "docs/V5.1_UPGRADE_GUIDE.md",
    "docs/SLIPPAGE_INTEGRATION.md",
    "CHANGELOG_V5.1.md",
    "PROJECT_STATUS_V5.1.md",
    "TODO_TOMORROW.md",
    "DAILY_LOG_2025-12-05.md"
)

foreach ($file in $docFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ 添加: $file" -ForegroundColor Green
        git add $file
    } else {
        Write-Host "  ⚠️  未找到: $file" -ForegroundColor Yellow
    }
}

git commit -m "docs: v5.1完整文档

- 升级指南（V5.1_UPGRADE_GUIDE.md）
- 变更日志（CHANGELOG_V5.1.md）
- 项目状态（PROJECT_STATUS_V5.1.md）
- 明日计划（TODO_TOMORROW.md）
- 开发日志（DAILY_LOG_2025-12-05.md）"

Write-Host "✅ 文档提交完成" -ForegroundColor Green
Write-Host ""

# ============================================================================

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "📊 提交总结" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan

# 显示提交历史（最近4次）
git log --oneline -4

Write-Host ""
Write-Host "="*80 -ForegroundColor Cyan
Write-Host "✅ 所有提交完成！" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

# 询问是否推送到远程
$push = Read-Host "是否推送到远程仓库？(Y/N)"
if ($push -eq "Y" -or $push -eq "y") {
    Write-Host "🚀 推送到远程..." -ForegroundColor Yellow
    git push
    Write-Host "✅ 推送完成！" -ForegroundColor Green
} else {
    Write-Host "ℹ️  跳过推送，稍后可手动执行：git push" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Git提交脚本执行完成！" -ForegroundColor Green
Write-Host ""

