param([ValidateSet('ZH-Alto-1','ZH-Tenor-1')][string]$Speaker = 'ZH-Alto-1')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$env:HF_HUB_DISABLE_XET = '1'
$env:HF_HUB_DOWNLOAD_TIMEOUT = '120'
$env:PYTHONUTF8 = '1'
$env:TEMP = Join-Path $projectRoot 'reports\.tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
$stdout = Join-Path $projectRoot 'reports\download.stdout.log'
$stderr = Join-Path $projectRoot 'reports\download.stderr.log'
$downloadScript = Join-Path $projectRoot 'scripts\download_gtsinger.py'
$arguments = '-u "' + $downloadScript + '" --speaker ' + $Speaker
$process = Start-Process -FilePath $pythonPath -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
@{ pid=$process.Id; speaker=$Speaker; started_at=(Get-Date).ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath 'reports/download_process.json' -Encoding utf8
Write-Output "Download started. PID=$($process.Id). Logs: reports/download.stdout.log and download.stderr.log"
