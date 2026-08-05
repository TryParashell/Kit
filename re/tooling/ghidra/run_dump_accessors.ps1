$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "12G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\dump_accessors.log"
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_sldmodu") sldmodu `
    -process sldmodu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript DumpFunctions.java (Join-Path $root "out\sldmodu_accessors.c") (Join-Path $root "spec_accessors.txt") 0 120 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE" | Out-File -Encoding utf8 -Append $log
