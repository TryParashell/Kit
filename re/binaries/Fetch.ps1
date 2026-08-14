# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$InstallRoot,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $here 'Manifest.json'

if (-not (Test-Path -LiteralPath $manifestPath)) {
    throw "Manifest.json not found beside Fetch.ps1 at $here"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json

if (-not $InstallRoot) { $InstallRoot = $manifest.install_root }

if (-not $VerifyOnly -and -not (Test-Path -LiteralPath $InstallRoot)) {
    throw "SOLIDWORKS install not found at '$InstallRoot'. Pass -InstallRoot <path> to point at a licensed install."
}

$failures = 0

foreach ($entry in $manifest.binaries) {
    $target = Join-Path $here $entry.name
    $source = Join-Path $InstallRoot $entry.name

    if (-not $VerifyOnly) {
        if (-not (Test-Path -LiteralPath $source)) {
            Write-Information ("MISSING SOURCE  {0}  {1}" -f $entry.name, $source) -InformationAction Continue
            $failures++
            continue
        }
        Copy-Item -LiteralPath $source -Destination $target -Force
    }

    if (-not (Test-Path -LiteralPath $target)) {
        Write-Information ("ABSENT          {0}" -f $entry.name) -InformationAction Continue
        $failures++
        continue
    }

    $item = Get-Item -LiteralPath $target
    $hash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLower()
    $info = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($target)

    $sizeOk = ($item.Length -eq $entry.bytes)
    $hashOk = ($hash -eq $entry.sha256)
    $versionOk = ($info.FileVersion -eq $entry.version.file_version)

    if ($sizeOk -and $hashOk -and $versionOk) {
        Write-Information ("OK              {0}  {1} bytes  {2}" -f $entry.name, $item.Length, $info.FileVersion) -InformationAction Continue
    }
    else {
        $failures++
        Write-Information ("MISMATCH        {0}" -f $entry.name) -InformationAction Continue
        if (-not $sizeOk) { Write-Information ("  bytes    expected {0} got {1}" -f $entry.bytes, $item.Length) -InformationAction Continue }
        if (-not $hashOk) { Write-Information ("  sha256   expected {0} got {1}" -f $entry.sha256, $hash) -InformationAction Continue }
        if (-not $versionOk) { Write-Information ("  version  expected {0} got {1}" -f $entry.version.file_version, $info.FileVersion) -InformationAction Continue }
    }
}

if ($failures -gt 0) {
    Write-Information "" -InformationAction Continue
    Write-Information ("$failures of " + $manifest.binaries.Count + " binaries did not match the manifest.") -InformationAction Continue
    Write-Information "A version mismatch is expected on a different SOLIDWORKS release. Re-derive the offsets in re/solidworks/ before trusting them against other bytes." -InformationAction Continue
    exit 1
}

Write-Information "" -InformationAction Continue
Write-Information ("All " + $manifest.binaries.Count + " binaries match the manifest (" + $manifest.product + ", " + $manifest.binaries[0].version.file_version + ").") -InformationAction Continue
exit 0
