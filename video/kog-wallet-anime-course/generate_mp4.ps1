# KOG Wallet anime preview MP4 generator for Windows PowerShell.
# Usage from repository root:
#   Set-Location .\video\kog-wallet-anime-course
#   .\generate_mp4.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$OutputFile = "kog-wallet-anime-course-preview.mp4"
$BashScript = Join-Path $ScriptDir "generate_mp4.sh"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Error "ffmpeg is required to generate $OutputFile. Install ffmpeg and add it to PATH, then run this script again."
    exit 127
}

if (-not (Get-Command python3 -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python is required to generate SVG frames. Install Python 3 and add it to PATH, then run this script again."
    exit 127
}

if (Get-Command bash -ErrorAction SilentlyContinue) {
    bash $BashScript
    exit $LASTEXITCODE
}

Write-Error "bash is required for this wrapper because the MP4 renderer is implemented in generate_mp4.sh. Install Git for Windows or WSL, then run .\generate_mp4.ps1 again."
exit 127
