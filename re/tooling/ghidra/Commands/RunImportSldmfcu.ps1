$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "8G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\import_sldmfcu.log"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
Copy-Item "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\sldmfcu.dll" (Join-Path $root "bin\") -Force
& $headless (Join-Path $root "proj_sldmfcu") sldmfcu `
    -import (Join-Path $root "bin\sldmfcu.dll") `
    -scriptPath (Join-Path $root "scripts") `
    -analysisTimeoutPerFile 7200 *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE ELAPSED_SEC $($sw.Elapsed.TotalSeconds)" | Out-File -Encoding utf8 -Append $log
