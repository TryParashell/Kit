$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "12G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\dump_accessors3.log"
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_sldmodu") sldmodu `
    -process sldmodu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript DumpFunctions.java (Join-Path $root "out\sldmodu_accessors3.c") (Join-Path $root "spec_accessors3.txt") 0 180 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE" | Out-File -Encoding utf8 -Append $log
