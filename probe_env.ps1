$ErrorActionPreference = 'Continue'

Write-Output '=== SolidWorks ProgIDs in registry ==='
Get-ChildItem 'HKLM:\SOFTWARE\Classes' -ErrorAction SilentlyContinue |
    Where-Object { $_.PSChildName -like 'SldWorks*' -or $_.PSChildName -like 'SolidWorks*' } |
    Select-Object -ExpandProperty PSChildName

Write-Output '=== ProgID resolution ==='
foreach ($progId in @('SldWorks.Application', 'SwDocumentMgr.SwDMClassFactory')) {
    try {
        $type = [Type]::GetTypeFromProgID($progId)
        if ($type) { Write-Output "$progId -> $($type.GUID)" }
        else { Write-Output "$progId -> not registered" }
    } catch {
        Write-Output "$progId -> error: $($_.Exception.Message)"
    }
}

Write-Output '=== Install dirs ==='
foreach ($dir in @(
    'C:\Program Files\SOLIDWORKS Corp',
    'C:\Program Files\SolidWorks Corp',
    'C:\Program Files\FreeCAD 1.0',
    'C:\Program Files\FreeCAD 1.1',
    'C:\Program Files\FreeCAD'
)) {
    if (Test-Path $dir) { Write-Output "PRESENT $dir" } else { Write-Output "absent  $dir" }
}

Write-Output '=== FreeCAD on PATH ==='
foreach ($exe in @('freecad', 'FreeCAD', 'freecadcmd', 'FreeCADCmd')) {
    $cmd = Get-Command $exe -ErrorAction SilentlyContinue
    if ($cmd) { Write-Output "$exe -> $($cmd.Source)" } else { Write-Output "$exe -> not found" }
}

Write-Output '=== Parashell FreeCAD build ==='
foreach ($candidate in @(
    'C:\Users\odin\Documents\Parashell\Parashell\build\bin\FreeCADCmd.exe',
    'C:\Users\odin\Documents\Parashell\Parashell\build\bin\FreeCAD.exe'
)) {
    if (Test-Path $candidate) { Write-Output "PRESENT $candidate" } else { Write-Output "absent  $candidate" }
}
