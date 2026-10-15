# The capped cu134 build, as approved (2026-10-15): start /AFFINITY 3FC /BELOWNORMAL (E-cores 2-9) with -j 8,
# typeperf every 5 s, a stop if total CPU holds above 50% for 30 s, the build's own processes watched.
$ErrorActionPreference = 'Stop'
$Dir = $PSScriptRoot
$Result = [ordered]@{ started_utc = (Get-Date).ToUniversalTime().ToString('o'); mask = '0x3FC (logical 2-9, E-cores)'; jobs = 8 }
$Work = 'nvcc', 'cl', 'cicc', 'ptxas', 'cudafe++', 'fatbinary', 'nvlink', 'link', 'ninja', 'cmake'

$tp = Start-Process typeperf -ArgumentList '"\Processor(_Total)\% Processor Time"', '-si', '5', '-f', 'CSV', '-o', (Join-Path $Dir 'typeperf.csv'), '-y' -PassThru -WindowStyle Hidden
$cmd = "start `"`" /B /WAIT /AFFINITY 3FC /BELOWNORMAL cmd /c `"$Dir\build.cmd`" > `"$Dir\build.log`" 2>&1"
$t0 = Get-Date
$launcher = Start-Process cmd.exe -ArgumentList '/c', $cmd -PassThru -WindowStyle Hidden
$Result.launcher_pid = $launcher.Id

$mon = Join-Path $Dir 'monitor.csv'
'utc,total_cpu_pct,build_cpu_pct,build_procs,affinity_seen' | Set-Content $mon
$last = @{}; $over = 0; $affSeen = @{}
while (-not $launcher.HasExited) {
  Start-Sleep 5
  $total = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue, 1)
  $procs = @(Get-Process -Name $Work -ErrorAction SilentlyContinue)
  $cpu = 0.0; $now = @{}
  foreach ($p in $procs) {
    try { $now[$p.Id] = $p.TotalProcessorTime.TotalSeconds; if ($last.ContainsKey($p.Id)) { $cpu += $now[$p.Id] - $last[$p.Id] }; $affSeen['0x{0:X}' -f [int64]$p.ProcessorAffinity] = $true } catch {}
  }
  $last = $now
  $buildPct = [math]::Round(100 * $cpu / (5 * [Environment]::ProcessorCount), 1)
  "$((Get-Date).ToUniversalTime().ToString('HH:mm:ss')),$total,$buildPct,$($procs.Count),$(($affSeen.Keys) -join '|')" | Add-Content $mon
  if ($total -gt 50) { $over += 1 } else { $over = 0 }
  if ($over -ge 6) {
    & taskkill /PID $launcher.Id /T /F | Out-Null
    $Result.stopped = "total CPU above 50% for 30 s ($total% at the stop)"
    break
  }
}
$Result.wall_seconds = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
Stop-Process -Id $tp.Id -Force -ErrorAction SilentlyContinue
$Result.build_ok = [bool](Select-String -Path (Join-Path $Dir 'build.log') -Pattern '^BUILD_OK' -Quiet)
$Result.affinity_seen = @($affSeen.Keys)
$rows = Import-Csv $mon
$Result.total_cpu_pct = [ordered]@{ peak = ($rows | ForEach-Object { [double]$_.total_cpu_pct } | Measure-Object -Maximum).Maximum; average = [math]::Round(($rows | ForEach-Object { [double]$_.total_cpu_pct } | Measure-Object -Average).Average, 1) }
$Result.build_cpu_pct = [ordered]@{ peak = ($rows | ForEach-Object { [double]$_.build_cpu_pct } | Measure-Object -Maximum).Maximum; average = [math]::Round(($rows | ForEach-Object { [double]$_.build_cpu_pct } | Measure-Object -Average).Average, 1) }
$Result.finished_utc = (Get-Date).ToUniversalTime().ToString('o')
$Result | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $Dir 'build-result.json')
Get-Content (Join-Path $Dir 'build-result.json')
