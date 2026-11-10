param([int]$Port = 7866, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Missing .venv. Create the project data environment first.' }
$taskUrl = "http://127.0.0.1:$Port"
try {
    $taskExisting = Invoke-RestMethod -Uri "$taskUrl/api/bootstrap" -TimeoutSec 2
    if ($taskExisting.model.id -eq 'gtsinger_zh_alto') {
        Write-Host "Voice Studio is already running: $taskUrl"
        if (-not $NoBrowser) { Start-Process $taskUrl }
        exit 0
    }
} catch { }
$env:PYTHONUTF8 = '1'
$taskArgs = @('-m', 'platform_app.server', '--port', "$Port")
if (-not $NoBrowser) { $taskArgs += '--open' }
& $taskPython @taskArgs
exit $LASTEXITCODE
