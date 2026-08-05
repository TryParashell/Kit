$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "6G"
$root = "C:\Users\odin\kitgh"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\test_rename.log"
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_swccu") swccu `
    -process sldarchiveu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript RenameArchiveApi.java `
    -postScript DumpFunctions.java (Join-Path $root "out\sldarchiveu_named.c") (Join-Path $root "spec_sldarchiveu.txt") 0 240 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE" | Out-File -Encoding utf8 -Append $log
