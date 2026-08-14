$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "8G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\dump_sldmfcu.log"
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_sldmfcu") sldmfcu `
    -process sldmfcu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript DumpRefs.java (Join-Path $root "out\SldmfcuSigtableRefs.txt") 3cf5a440 3cf5b3f0 240 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE" | Out-File -Encoding utf8 -Append $log
