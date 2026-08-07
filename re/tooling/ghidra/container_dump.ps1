$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
$env:GHIDRA_HEADLESS_MAXMEM = "12G"
$root = "C:\Users\odin\kitgh"
$repo = "C:\Users\odin\Documents\Parashell\Kit"
$headless = Join-Path $root "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
$log = Join-Path $root "logs\dump_container.log"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log
& $headless (Join-Path $root "proj_sldmodu") sldmodu `
    -process sldmodu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript RenameArchiveApi.java `
    -postScript DumpFunctions.java (Join-Path $root "out\container_serialize.c") (Join-Path $repo "re\tooling\ghidra\container_spec.txt") 1 300 `
    *>&1 | Out-File -Encoding utf8 -Append $log
"EXIT $LASTEXITCODE ELAPSED_SEC $($sw.Elapsed.TotalSeconds)" | Out-File -Encoding utf8 -Append $log

$sw2 = [System.Diagnostics.Stopwatch]::StartNew()
$log2 = Join-Path $root "logs\dump_container_mfcu.log"
"START $(Get-Date -Format o)" | Out-File -Encoding utf8 $log2
& $headless (Join-Path $root "proj_sldmfcu") sldmfcu `
    -process sldmfcu.dll -noanalysis `
    -scriptPath (Join-Path $root "scripts") `
    -postScript DumpFunctions.java (Join-Path $root "out\container_serialize_mfcu.c") (Join-Path $repo "re\tooling\ghidra\container_spec_mfcu.txt") 1 300 `
    *>&1 | Out-File -Encoding utf8 -Append $log2
"EXIT $LASTEXITCODE ELAPSED_SEC $($sw2.Elapsed.TotalSeconds)" | Out-File -Encoding utf8 -Append $log2
