param(
    [string]$RepoPath = "D:\GitHub\FastAPI-application",
    [string]$PrimaryUrl = "http://127.0.0.1:28280",
    [string]$PythonCommand = "python",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

function Test-PofApi {
    param([string]$BaseUrl)

    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/health" -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    }
    catch {
        return $false
    }
}

function Start-PofApi {
    param([string]$Path, [string]$PythonExe)

    $mainFile = Join-Path $Path "main.py"
    if (-not (Test-Path $mainFile)) {
        throw "Cannot find main.py at $mainFile"
    }

    Start-Process -FilePath $PythonExe -ArgumentList @($mainFile) -WorkingDirectory $Path -WindowStyle Hidden
}

if (-not (Test-PofApi -BaseUrl $PrimaryUrl)) {
    Start-PofApi -Path $RepoPath -PythonExe $PythonCommand

    $deadline = (Get-Date).AddSeconds(20)
    while ((Get-Date) -lt $deadline) {
        if (Test-PofApi -BaseUrl $PrimaryUrl) {
            break
        }
        Start-Sleep -Seconds 1
    }
}

if (-not $NoBrowser) {
    Start-Process "$PrimaryUrl/"
}
