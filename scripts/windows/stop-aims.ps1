$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$PidFile = Join-Path (Join-Path $Root "runtime") "aims.pid"
$Ports = @(8000, 5173)

function Stop-ProcessId {
    param([int]$ProcessId, [string]$Reason)

    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $Process) {
        return $false
    }

    # Verify this is actually an AIMS-related process before killing
    $IsAims = $false
    try {
        $CmdLine = (Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue).CommandLine
        if ($CmdLine -and ($CmdLine -match "backend\.main" -or $CmdLine -match "uvicorn" -or $CmdLine -match "vite" -or $Process.ProcessName -match "node")) {
            $IsAims = $true
        }
    } catch {
        # If we can't check the command line, assume it's ours if we found it via port or PID file
        $IsAims = $true
    }

    if (-not $IsAims) {
        Write-Host "Skipped process $ProcessId ($($Process.ProcessName)) - not an AIMS process."
        return $false
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped process $ProcessId ($($Process.ProcessName))."
    return $true
}

# --- Method 1: Find by listening port (most reliable) ---
Write-Host "Searching for AIMS processes..."

$PortProcessIds = @{}
foreach ($Port in $Ports) {
    $PortProcessIds[[string]$Port] = $true
}

$FoundIds = @()
$Netstat = netstat -ano
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
    $Port = ($LocalAddress -split ":")[-1]
    if ($PortProcessIds.ContainsKey($Port) -and $PidText -match "^\d+$") {
        $FoundIds += [int]$PidText
    }
}

$FoundIds = $FoundIds | Select-Object -Unique
$Stopped = $false

foreach ($ProcessId in $FoundIds) {
    $Stopped = (Stop-ProcessId -ProcessId $ProcessId -Reason "port") -or $Stopped
}

# --- Method 2: Try PID file (in case port check missed it) ---
if (Test-Path $PidFile) {
    $PidValue = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($PidValue -and $PidValue -match "^\d+$") {
        $pidFromFile = [int]$PidValue
        if ($pidFromFile -notin $FoundIds) {
            $Stopped = (Stop-ProcessId -ProcessId $pidFromFile -Reason "pidfile") -or $Stopped
        }
    }
}

# --- Method 3: Find python/uvicorn processes by command line ---
try {
    $PythonPids = Get-CimInstance -ClassName Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "backend\.main|uvicorn" } |
        Select-Object -ExpandProperty ProcessId
    foreach ($ProcessId in $PythonPids) {
        if ($ProcessId -notin $FoundIds) {
            $Stopped = (Stop-ProcessId -ProcessId $ProcessId -Reason "python") -or $Stopped
            $FoundIds += $ProcessId
        }
    }
} catch {
    # WMI query might fail on some systems; skip gracefully
}

# --- Always clean up PID file ---
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue

if ($Stopped) {
    Write-Host "AIMS stopped."
} else {
    Write-Host "AIMS is not running."
}
