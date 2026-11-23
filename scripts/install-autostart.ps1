# SPDX-License-Identifier: Apache-2.0
# Install or remove the login autostart entry for the Chinese interface watcher.
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\install-autostart.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\install-autostart.ps1 -Uninstall

param([switch]$Uninstall)

$ErrorActionPreference = "Stop"
$name = "HerdrChineseWatcher"
$key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$root = Split-Path -Parent $PSScriptRoot
$watch = Join-Path $root "src\zh_watch.py"

function Find-Pythonw {
    $pw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($pw) { return $pw.Source }
    $py = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($py) {
        $candidate = Join-Path (Split-Path $py.Source) "pythonw.exe"
        if (Test-Path $candidate) { return $candidate }
        return $py.Source
    }
    throw "Python not found. Install Python 3.9+ and add it to PATH."
}

if ($Uninstall) {
    if (Get-ItemProperty -Path $key -Name $name -ErrorAction SilentlyContinue) {
        Remove-ItemProperty -Path $key -Name $name
        Write-Host "Removed autostart entry: $name"
    } else {
        Write-Host "No autostart entry named $name"
    }
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*zh_watch.py*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "Stopped the watcher"
    exit 0
}

if (-not (Test-Path $watch)) { throw "Watcher not found: $watch" }
$pythonw = Find-Pythonw
$cmd = '"' + $pythonw + '" "' + $watch + '"'
New-ItemProperty -Path $key -Name $name -Value $cmd -PropertyType String -Force | Out-Null
Write-Host "Installed autostart entry: $name"
Write-Host "Command: $cmd"
Start-Process -FilePath $pythonw -ArgumentList @("`"$watch`"") -WindowStyle Hidden
Write-Host "Watcher started"
