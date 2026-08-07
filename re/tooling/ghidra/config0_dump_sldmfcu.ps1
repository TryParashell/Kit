$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "12G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\dump_config0_sldmfcu.log"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_sldmfcu") sldmfcu `
    -process sldmfcu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript RenameArchiveApi.java `
    -postScript DumpVtableSlot.java (Join-Path $root "out\sldmfcu_vtslots.txt") 40 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE ELAPSED_SEC $($sw.Elapsed.TotalSeconds)" | Out-File -Encoding utf8 -Append $log
