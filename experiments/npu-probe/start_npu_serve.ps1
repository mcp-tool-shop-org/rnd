# DRAFT — not registered, not scheduled. Reviewed as a draft only.
# Starts npu-serve on loopback (default port 11491) with a pid file and a log under results/.
param(
    [int]$Port = 11491,
    [string]$Models = "bge-base-en-v1.5,nomic-embed-text",
    [switch]$Nli
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = "E:/AI/envs/npu-openvino/Scripts/python.exe"
$pidFile = Join-Path $here "results/npu-serve.pid"
$logFile = Join-Path $here "results/npu-serve.log"

if (Test-Path $pidFile) {
    $old = Get-Content $pidFile
    if (Get-Process -Id $old -ErrorAction SilentlyContinue) {
        throw "npu-serve already running (pid $old)"
    }
    Remove-Item $pidFile
}

$argList = @("-X", "utf8", (Join-Path $here "npu_serve.py"), "--port", "$Port", "--models", $Models)
if ($Nli) { $argList += "--nli" }

$p = Start-Process -FilePath $python -ArgumentList $argList -WorkingDirectory $here `
    -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" -PassThru -WindowStyle Hidden
Set-Content $pidFile $p.Id
Write-Host "npu-serve starting (pid $($p.Id)) on http://127.0.0.1:$Port; log $logFile"
Write-Host "Reminder: the NPU is one exclusive device — log this session with the Publisher before load."
