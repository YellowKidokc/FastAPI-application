param(
    [string]$RepoPath = "D:\GitHub\FastAPI-application",
    [string]$PrimaryUrl = "",
    [string]$PythonCommand = "python",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

function Get-PofEnv {
    param([string]$Path)

    $envPath = Join-Path $Path ".env"
    $values = @{}
    if (-not (Test-Path $envPath)) {
        return $values
    }

    foreach ($line in Get-Content $envPath) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
    }
    return $values
}

function Get-PofLanAddress {
    $preferred = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -like "192.168.1.*" -and
            $_.IPAddress -ne "192.168.1.254" -and
            $_.PrefixOrigin -ne "WellKnown"
        } |
        Select-Object -First 1

    if ($preferred) {
        return $preferred.IPAddress
    }

    $fallback = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -like "192.168.*" -and
            $_.PrefixOrigin -ne "WellKnown"
        } |
        Select-Object -First 1

    if ($fallback) {
        return $fallback.IPAddress
    }

    return "192.168.1.76"
}

function Resolve-PofUrl {
    param([string]$Path, [string]$RequestedUrl)

    if ($RequestedUrl) {
        return $RequestedUrl.TrimEnd("/")
    }

    $envValues = Get-PofEnv -Path $Path
    if ($envValues["POF_DASHBOARD_URL"]) {
        return $envValues["POF_DASHBOARD_URL"].TrimEnd("/")
    }

    $hostName = $envValues["POF_DASHBOARD_HOST"]
    if (-not $hostName) {
        $hostName = $envValues["POF_LAPTOP_LAN"]
    }
    if (-not $hostName) {
        $hostName = Get-PofLanAddress
    }

    $port = $envValues["POF_APP_PORT"]
    if (-not $port) {
        $port = "28280"
    }

    return "http://${hostName}:${port}"
}

function Test-PofApi {
    param([string]$BaseUrl)

    try {
        $response = Invoke-WebRequest -Uri "$BaseUrl/ready" -UseBasicParsing -TimeoutSec 3
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500)
    }
    catch {
        return $false
    }
}

function Start-PofApi {
    param([string]$Path, [string]$PythonExe, [string]$BaseUrl)

    $mainFile = Join-Path $Path "main.py"
    if (-not (Test-Path $mainFile)) {
        throw "Cannot find main.py at $mainFile"
    }

    $uri = [Uri]$BaseUrl
    $port = $uri.Port
    if ($port -le 0) {
        $port = 28280
    }

    Start-Process -FilePath $PythonExe -ArgumentList @("-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$port") -WorkingDirectory $Path -WindowStyle Hidden
}

$ResolvedUrl = Resolve-PofUrl -Path $RepoPath -RequestedUrl $PrimaryUrl

if (-not (Test-PofApi -BaseUrl $ResolvedUrl)) {
    Start-PofApi -Path $RepoPath -PythonExe $PythonCommand -BaseUrl $ResolvedUrl

    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if (Test-PofApi -BaseUrl $ResolvedUrl) {
            break
        }
        Start-Sleep -Seconds 1
    }
}

if (-not $NoBrowser) {
    Start-Process "$ResolvedUrl/"
}
