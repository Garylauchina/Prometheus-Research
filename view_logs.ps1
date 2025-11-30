# 查看最新的日志文件
Write-Host "最新的日志文件列表："
Get-ChildItem -Path "e:\Trae_store\prometheus-v30\logs" -Filter "*.log" | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 5

# 提示用户选择要查看的日志文件
Write-Host "
请输入要查看的日志文件名（例如：prometheus_20251201_003303.log）："
$logFileName = Read-Host

$logPath = "e:\Trae_store\prometheus-v30\logs\$logFileName"

if (Test-Path $logPath) {
    Write-Host "\n查看日志文件内容：$logPath"
    Get-Content -Path $logPath
} else {
    Write-Host "错误：找不到日志文件 $logPath"
}