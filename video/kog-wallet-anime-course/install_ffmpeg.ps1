# Install ffmpeg for Windows PowerShell using the first available package manager.
# Usage:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\install_ffmpeg.ps1

$ErrorActionPreference = "Stop"

function Test-Ffmpeg {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "ffmpeg found at: $($cmd.Source)"
        ffmpeg -version | Select-Object -First 1
        return $true
    }
    return $false
}

if (Test-Ffmpeg) {
    exit 0
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Installing ffmpeg with winget..."
    winget install --id Gyan.FFmpeg --source winget --accept-package-agreements --accept-source-agreements
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Host "Installing ffmpeg with Chocolatey..."
    choco install ffmpeg -y
} elseif (Get-Command scoop -ErrorAction SilentlyContinue) {
    Write-Host "Installing ffmpeg with Scoop..."
    scoop install ffmpeg
} else {
    Write-Error "No supported Windows package manager found. Install one of: winget, Chocolatey, or Scoop; then rerun this script."
    exit 127
}

# Refresh PATH for the current PowerShell process.
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"

if (-not (Test-Ffmpeg)) {
    Write-Error "ffmpeg installation command finished, but ffmpeg is not visible in PATH. Close and reopen PowerShell, then run: ffmpeg -version"
    exit 127
}
