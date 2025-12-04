# 等待排名报告出现
$terminalFile = "c:\Users\garyl\.cursor\projects\e-Cursor-store-prometheus-v30\terminals\52.txt"
$maxWait = 300  # 最多等待5分钟

Write-Host "⏳ 等待排名报告..." -ForegroundColor Yellow
Write-Host "   文件: $terminalFile" -ForegroundColor Gray

$elapsed = 0
while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds 10
    $elapsed += 10
    
    # 检查是否有排名报告
    $content = Get-Content $terminalFile -ErrorAction SilentlyContinue
    $ranking = $content | Select-String "Agent表现排名"
    
    if ($ranking) {
        Write-Host "`n✅ 发现排名报告！" -ForegroundColor Green
        Write-Host "`n" -NoNewline
        
        # 显示排名报告及其后25行
        $startLine = ($content | Select-String -Pattern "Agent表现排名" -SimpleMatch).LineNumber | Select-Object -Last 1
        if ($startLine) {
            $content[($startLine-1)..($startLine+24)] | ForEach-Object { Write-Host $_ }
        }
        break
    }
    
    # 显示当前周期
    $lastCycle = $content | Select-String "周期 \d+" | Select-Object -Last 1
    Write-Host "`r⏳ 等待中... $lastCycle (已等待 ${elapsed}秒)" -NoNewline -ForegroundColor Yellow
}

if ($elapsed -ge $maxWait) {
    Write-Host "`n⚠️ 超时！未发现排名报告。" -ForegroundColor Red
}

