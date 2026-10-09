# DRAFT — not registered, not scheduled. Reviewed as a draft only.
# Stops the npu-serve started by start_npu_serve.ps1 (via its pid file) and frees the NPU.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $here "results/npu-serve.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "no pid file; nothing to stop"
    exit 0
}
$pid = Get-Content $pidFile
if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
    Stop-Process -Id $pid -Force
    Write-Host "stopped npu-serve (pid $pid); the NPU is free — say so for the Publisher's ledger"
} else {
    Write-Host "pid $pid is not running; cleaning up the pid file"
}
Remove-Item $pidFile
