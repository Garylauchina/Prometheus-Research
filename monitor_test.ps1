# Prometheus v4.0 实时监控脚本
# 监控小预言、排名、进化等关键信息

Write-Host "=" 60 -ForegroundColor Cyan
Write-Host "📊 Prometheus v4.0 实时监控" -ForegroundColor Yellow
Write-Host "=" 60 -ForegroundColor Cyan
Write-Host ""

$terminalFile = "c:\Users\garyl\.cursor\projects\e-Cursor-store-prometheus-v30\terminals\75.txt"

Write-Host "监控文件: $terminalFile" -ForegroundColor Gray
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Gray
Write-Host ""

$lastSize = 0
$cycleCount = 0

while ($true) {
    Start-Sleep -Seconds 3
    
    if (Test-Path $terminalFile) {
        $currentSize = (Get-Item $terminalFile).Length
        
        if ($currentSize -gt $lastSize) {
            Clear-Host
            Write-Host "=" 60 -ForegroundColor Cyan
            Write-Host "📊 Prometheus v4.0 实时监控 (更新时间: $(Get-Date -Format 'HH:mm:ss'))" -ForegroundColor Yellow
            Write-Host "=" 60 -ForegroundColor Cyan
            Write-Host ""
            
            # 显示最新50行
            $content = Get-Content $terminalFile -Tail 50
            
            # 统计信息
            $prophecies = $content | Select-String "小预言:|创世大预言:"
            $cycles = $content | Select-String "周期 \d+ \|"
            $trades = $content | Select-String "执行了\d+笔交易"
            $rankings = $content | Select-String "Agent表现排名"
            
            Write-Host "📈 统计信息:" -ForegroundColor Green
            Write-Host "   预言次数: $($prophecies.Count)" -ForegroundColor White
            Write-Host "   周期数: $($cycles.Count)" -ForegroundColor White
            Write-Host "   交易记录: $($trades.Count)" -ForegroundColor White
            Write-Host "   排名报告: $($rankings.Count)" -ForegroundColor White
            Write-Host ""
            Write-Host "-" 60 -ForegroundColor Gray
            Write-Host ""
            
            # 显示最新内容
            $content | ForEach-Object {
                if ($_ -match "小预言:|创世大预言:") {
                    Write-Host $_ -ForegroundColor Yellow
                } elseif ($_ -match "周期 \d+") {
                    Write-Host $_ -ForegroundColor Cyan
                } elseif ($_ -match "Agent表现排名") {
                    Write-Host $_ -ForegroundColor Green
                } elseif ($_ -match "ERROR|错误|失败") {
                    Write-Host $_ -ForegroundColor Red
                } elseif ($_ -match "WARNING|警告") {
                    Write-Host $_ -ForegroundColor Yellow
                } else {
                    Write-Host $_
                }
            }
            
            $lastSize = $currentSize
        }
    } else {
        Write-Host "⚠️  等待系统启动..." -ForegroundColor Yellow
    }
}

