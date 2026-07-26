param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RuntimeDir = Join-Path $Root "runtime"
$LogsDir = Join-Path $Root "logs"
$PidFile = Join-Path $RuntimeDir "aims.pid"

New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogsDir | Out-Null

foreach ($ProxyName in @("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")) {
    Remove-Item -LiteralPath "Env:$ProxyName" -ErrorAction SilentlyContinue
}

function Get-ListeningProcessIds {
    param([int[]]$TargetPorts)

    $PortSet = @{}
    foreach ($TargetPort in $TargetPorts) {
        $PortSet[[string]$TargetPort] = $true
    }

    $Ids = @()
    $Netstat = netstat -ano -p tcp
    foreach ($Line in $Netstat) {
        if ($Line -notmatch "LISTENING") {
            continue
        }

        $Columns = $Line.Trim() -split "\s+"
        if ($Columns.Count -lt 5) {
            continue
        }

        $LocalAddress = $Columns[1]
        $PidText = $Columns[4]
        $ListeningPort = ($LocalAddress -split ":")[-1]
        if ($PortSet.ContainsKey($ListeningPort) -and $PidText -match "^\d+$") {
            $Ids += [int]$PidText
        }
    }

    return $Ids | Select-Object -Unique
}

if (Test-Path $PidFile) {
    $ExistingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($ExistingPid -and (Get-Process -Id $ExistingPid -ErrorAction SilentlyContinue)) {
        Write-Host "AIMS is already running. Opening browser..."
        Start-Process "http://127.0.0.1:$Port/"
        exit 0
    }
}

$PortProcessIds = Get-ListeningProcessIds -TargetPorts @($Port)
if ($PortProcessIds.Count -gt 0) {
    Set-Content -Path $PidFile -Value $PortProcessIds[0]
    Write-Host "AIMS is already running on port $Port. Opening browser..."
    Start-Process "http://127.0.0.1:$Port/"
    exit 0
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}

if (-not $Python) {
    Write-Host "Python was not found. Please install Python 3.11+ or use a package that includes .venv."
    Read-Host "Press Enter to exit"
    exit 1
}

Push-Location $Root
try {
    & $Python -c "from backend.storage.database import init_database; init_database()"

    $Stdout = Join-Path $LogsDir "aims.stdout.log"
    $Stderr = Join-Path $LogsDir "aims.stderr.log"
    $AimsLog = Join-Path $LogsDir "aims.log"
    $Args = @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$Port")
    # Python writes its own UTF-8 log to aims.log (avoids PowerShell redirect encoding issues)
    $env:AIMS_LOG_FILE = $AimsLog
    $Process = Start-Process -FilePath $Python -ArgumentList $Args -WorkingDirectory $Root -WindowStyle Hidden -PassThru -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr
    Set-Content -Path $PidFile -Value $Process.Id

    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:$Port/"
    Write-Host "AIMS started at http://127.0.0.1:$Port/"
    Write-Host "Logs: $LogsDir"
} finally {
    Pop-Location
}
