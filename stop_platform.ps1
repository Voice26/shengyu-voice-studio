$ErrorActionPreference = 'Stop'
$taskStateFile = Join-Path $PSScriptRoot '.platform\server.json'
if (-not (Test-Path -LiteralPath $taskStateFile)) {
    Write-Host 'Voice Studio is not running from the launcher.'
    exit 0
}
$taskState = Get-Content -LiteralPath $taskStateFile -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskState.root -ne $PSScriptRoot) { throw 'The server record belongs to a different project.' }
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($taskState.pid)" -ErrorAction SilentlyContinue
if (-not $taskProcess) { Write-Host 'Voice Studio is already stopped.'; exit 0 }
if ($taskProcess.CommandLine -notmatch '(^|\s)platform_app\.server(\s|$)') {
    throw 'The saved PID does not belong to Voice Studio. No process was stopped.'
}
$taskStatusUrl = "http://127.0.0.1:$($taskState.port)/api/jobs"
try {
    $taskJobs = Invoke-RestMethod -Uri $taskStatusUrl -TimeoutSec 3
    if ($taskJobs.jobs | Where-Object { $_.status -in @('queued','uploading','separating','analyzing','converting','mixing','downloading') }) {
        throw 'Conversions are still running. Wait for them to finish before stopping the platform.'
    }
} catch {
    if ($_.Exception.Message -like 'Conversions are still running*') { throw }
}
Stop-Process -Id $taskState.pid -ErrorAction Stop
Write-Host 'Voice Studio stopped.'
