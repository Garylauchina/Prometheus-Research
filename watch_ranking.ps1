# Prometheus v4.0 - 实时监控排名脚本
# 用法: .\watch_ranking.ps1

$terminalFile = "c:\Users\garyl\.cursor\projects\e-Cursor-store-prometheus-v30\terminals\51.txt"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Prometheus v4.0 实时监控" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 退出" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Prometheus v4.0 实时监控" -ForegroundColor Cyan
    Write-Host "  $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # 获取最新周期
    $latestCycle = Get-Content $terminalFile | Select-String "周期 \d+" | Select-Object -Last 1
    if ($latestCycle) {
        Write-Host "📊 $latestCycle" -ForegroundColor Yellow
    }
    
    # 获取最新价格
    $latestPrice = Get-Content $terminalFile | Select-String "当前价格:" | Select-Object -Last 1
    if ($latestPrice) {
        Write-Host "$latestPrice" -ForegroundColor Green
    }
    
    # 查找排名报告
    $rankingStart = Get-Content $terminalFile | Select-String -Pattern "Agent表现排名" -Context 0,30 | Select-Object -Last 1
    
    if ($rankingStart) {
        Write-Host "`n" -NoNewline
        $rankingStart.Context.PostContext | ForEach-Object { 
            if ($_ -match "^\s*\d+\.") {
                Write-Host $_ -ForegroundColor White
            } elseif ($_ -match "=====") {
                Write-Host $_ -ForegroundColor Cyan
            } else {
                Write-Host $_ -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "`n⏳ 等待第10周期排名报告..." -ForegroundColor Yellow
    }
    
    # 获取最新决策分布
    $latestDecision = Get-Content $terminalFile | Select-String "Agent决策分布:" -Context 0,3 | Select-Object -Last 1
    if ($latestDecision) {
        Write-Host "`n📊 最新决策分布:" -ForegroundColor Yellow
        $latestDecision.Context.PostContext | ForEach-Object { Write-Host "  $_" }
    }
    
    Start-Sleep -Seconds 10
}

