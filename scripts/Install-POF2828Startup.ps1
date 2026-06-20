param(
    [string]$RepoPath = "D:\GitHub\FastAPI-application",
    [string]$ShortcutName = "POF 2828 Dashboard.lnk",
    [string]$PrimaryUrl = ""
)

$ErrorActionPreference = "Stop"

$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder $ShortcutName
$launcherPath = Join-Path $RepoPath "scripts\Start-POF2828.ps1"

if (-not (Test-Path $launcherPath)) {
    throw "Cannot find launcher at $launcherPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
if ($PrimaryUrl) {
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`" -RepoPath `"$RepoPath`" -PrimaryUrl `"$PrimaryUrl`""
}
else {
    $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`" -RepoPath `"$RepoPath`""
}
$shortcut.WorkingDirectory = $RepoPath
$shortcut.WindowStyle = 7
$shortcut.Description = "Start or open the POF 2828 FastAPI dashboard"
$shortcut.Save()

Write-Host "Installed startup shortcut: $shortcutPath"
