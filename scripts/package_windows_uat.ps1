param(
    [string]$Version = "0.1.0-uat",
    [switch]$IncludeVenv,
    [switch]$IncludeEnv,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PackageName = "AIMS-Windows-$Version"
$ReleaseRoot = Join-Path $Root "dist\windows-uat"
$PackageDir = Join-Path $ReleaseRoot $PackageName
$ZipPath = Join-Path $ReleaseRoot "$PackageName.zip"

Push-Location $Root
try {
    if (-not $SkipBuild) {
        if (-not (Test-Path "frontend\node_modules")) {
            throw "frontend\node_modules not found. Run npm install in frontend first."
        }

        Push-Location "frontend"
        try {
            npm run build
            if ($LASTEXITCODE -ne 0) {
                throw "frontend build failed with exit code $LASTEXITCODE."
            }
        } finally {
            Pop-Location
        }
    }

    if (-not (Test-Path "frontend\dist\index.html")) {
        throw "frontend\dist\index.html not found. Run frontend build or remove -SkipBuild."
    }

    if (Test-Path $PackageDir) {
        Remove-Item -LiteralPath $PackageDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

    Copy-Item -Recurse -Path "backend" -Destination $PackageDir
    New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "frontend") | Out-Null
    Copy-Item -Recurse -Path "frontend\dist" -Destination (Join-Path $PackageDir "frontend")
    Copy-Item -Recurse -Path "storage" -Destination $PackageDir
    New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "scripts") | Out-Null
    Copy-Item -Recurse -Path "scripts\windows" -Destination (Join-Path $PackageDir "scripts")
    Copy-Item -Path "requirements.txt", "start.bat", "stop.bat", "README-UAT.txt" -Destination $PackageDir

    if ($IncludeEnv -and (Test-Path ".env")) {
        Copy-Item -Path ".env" -Destination $PackageDir
    } else {
        Copy-Item -Path ".env.example" -Destination (Join-Path $PackageDir ".env")
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "logs") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $PackageDir "runtime") | Out-Null

    if ($IncludeVenv) {
        if (-not (Test-Path ".venv")) {
            throw ".venv not found. Create the virtual environment before using -IncludeVenv."
        }
        Copy-Item -Recurse -Path ".venv" -Destination $PackageDir
    }

    Get-ChildItem -Path $PackageDir -Directory -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $PackageDir -File -Recurse -Include "*.pyc", "*.pyo" | Remove-Item -Force

    if (Test-Path $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Compress-Archive -Path (Join-Path $PackageDir "*") -DestinationPath $ZipPath -Force

    Write-Host "Created package: $ZipPath"
} finally {
    Pop-Location
}
