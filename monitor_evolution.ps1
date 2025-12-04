# Prometheus v4.1 - 进化系统实时监控
# 监控：排名报告、顿悟事件、进化周期

$terminalFile = "c:\Users\garyl\.cursor\projects\e-Cursor-store-prometheus-v30\terminals\54.txt"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Prometheus v4.1 进化系统监控" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 退出" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$lastCycle = 0
$epiphanyCount = 0
$evolutionCount = 0

while ($true) {
    Start-Sleep -Seconds 10
    
    if (-not (Test-Path $terminalFile)) {
        Write-Host "⚠️  终端文件不存在" -ForegroundColor Red
        continue
    }
    
    $content = Get-Content $terminalFile -ErrorAction SilentlyContinue
    
    # 获取当前周期
    $cycles = $content | Select-String "周期 \d+"
    $currentCycle = 0
    if ($cycles) {
        $lastCycleLine = $cycles | Select-Object -Last 1
        if ($lastCycleLine -match "周期 (\d+)") {
            $currentCycle = [int]$matches[1]
        }
    }
    
    if ($currentCycle -ne $lastCycle) {
        $lastCycle = $currentCycle
        Write-Host "`n📊 周期 $currentCycle" -ForegroundColor Yellow
        
        # 获取当前价格
        $priceLines = $content | Select-String "当前价格:" | Select-Object -Last 1
        if ($priceLines) {
            Write-Host "   $priceLines" -ForegroundColor Green
        }
    }
    
    # 检查顿悟事件
    $epiphanies = $content | Select-String "💡.*顿悟"
    if ($epiphanies -and $epiphanies.Count -gt $epiphanyCount) {
        $newEpiphanies = $epiphanies | Select-Object -Last ($epiphanies.Count - $epiphanyCount)
        foreach ($ep in $newEpiphanies) {
            Write-Host "`n💡 顿悟事件:" -ForegroundColor Magenta
            Write-Host "   $ep" -ForegroundColor White
        }
        $epiphanyCount = $epiphanies.Count
    }
    
    # 检查进化周期
    $evolutions = $content | Select-String "🧬 开始进化周期"
    if ($evolutions -and $evolutions.Count -gt $evolutionCount) {
        $newEvolutions = $evolutions | Select-Object -Last ($evolutions.Count - $evolutionCount)
        foreach ($evo in $newEvolutions) {
            Write-Host "`n🧬 进化周期:" -ForegroundColor Cyan
            Write-Host "   $evo" -ForegroundColor White
            
            # 显示进化详情
            $evoDetails = $content | Select-String "淘汰|繁殖|新Agent诞生" -Context 0,1 | Select-Object -Last 10
            foreach ($detail in $evoDetails) {
                Write-Host "   $detail" -ForegroundColor Gray
            }
        }
        $evolutionCount = $evolutions.Count
    }
    
    # 检查排名报告
    if ($currentCycle % 5 -eq 0 -and $currentCycle -gt 0) {
        $rankings = $content | Select-String "Agent表现排名" -Context 0,15 | Select-Object -Last 1
        if ($rankings) {
            Write-Host "`n📊 最新排名 (周期 $currentCycle):" -ForegroundColor Yellow
            $rankings.Context.PostContext | Select-Object -First 10 | ForEach-Object {
                if ($_ -match "Agent_\d+") {
                    Write-Host "   $_" -ForegroundColor White
                }
            }
        }
    }
    
    # 状态栏
    Write-Host "`r⏰ 监控中... 周期:$currentCycle | 顿悟:$epiphanyCount次 | 进化:$evolutionCount代" -NoNewline -ForegroundColor Gray
}

