param([int]$Port, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $PSBoundParameters.ContainsKey('Port')) {
    $config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'configs\platform.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $Port = [int]$config.port
}
$taskPython = Join-Path $PSScriptRoot '.tools\web-python\python.exe'
if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) {
    $taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $taskPython -PathType Leaf)) { throw '请先双击项目目录中的「配置换声环境.bat」。' }
$taskUrl = "http://127.0.0.1:$Port"
try {
    $taskExisting = Invoke-RestMethod -Uri "$taskUrl/api/bootstrap" -TimeoutSec 2
    if ($taskExisting.default_model_id -eq 'gtsinger_zh_alto') {
        Write-Host "Voice Studio is already running: $taskUrl"
        if (-not $NoBrowser) { Start-Process $taskUrl }
        exit 0
    }
} catch { }
$env:PYTHONUTF8 = '1'
$env:PYTHONNOUSERSITE = '1'
Remove-Item Env:PYTHONHOME,Env:PYTHONPATH -ErrorAction SilentlyContinue
$taskArgs = @('-m', 'platform_app.server', '--port', "$Port")
if (-not $NoBrowser) { $taskArgs += '--open' }
& $taskPython @taskArgs
exit $LASTEXITCODE
