param([int]$TimeoutSeconds = 240)

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = Join-Path $root ".venv\Scripts\python.exe"
$files = Get-ChildItem -Path (Join-Path $root "tests") -Recurse -Filter "test_*.py" | Sort-Object FullName

foreach ($file in $files) {
    $relative = $file.FullName.Substring($root.Length + 1)
    $out = Join-Path $root ".rescratch\tests_$($file.BaseName).txt"
    $process = Start-Process -FilePath $python `
        -ArgumentList @("-m", "pytest", $relative, "-q", "--tb=no", "-rf", "-p", "no:cacheprovider") `
        -WorkingDirectory $root -RedirectStandardOutput $out -RedirectStandardError "$out.err" `
        -PassThru -NoNewWindow
    if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
        try { $process.Kill($true) } catch { }
        Write-Output "$relative :: TIMEOUT after ${TimeoutSeconds}s"
        continue
    }
    $summary = (Get-Content $out -ErrorAction SilentlyContinue | Where-Object { $_ -match "passed|failed|error|no tests" } | Select-Object -Last 1)
    Write-Output "$relative :: exit=$($process.ExitCode) :: $summary"
}
