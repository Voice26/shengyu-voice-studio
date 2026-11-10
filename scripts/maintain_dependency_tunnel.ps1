$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path $PSScriptRoot -Parent
$stopFile = Join-Path $projectRoot 'reports\.tmp\dependency-tunnel.stop'
$deadline = (Get-Date).AddHours(4)
while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $stopFile)) {
    & ssh -N -o BatchMode=yes -o ConnectTimeout=12 -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -R 127.0.0.1:18791:127.0.0.1:18791 voice-gpu
    if (-not (Test-Path -LiteralPath $stopFile)) { Start-Sleep -Seconds 3 }
}
