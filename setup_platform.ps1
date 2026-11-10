param([switch]$NonInteractive, [switch]$SkipServerCheck)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONNOUSERSITE = '1'
Remove-Item Env:PYTHONHOME,Env:PYTHONPATH -ErrorAction SilentlyContinue
$env:PYTHONUTF8 = '1'
$toolsRoot = Join-Path $PSScriptRoot '.tools'
$runtime = Join-Path $toolsRoot 'web-python'
$portablePython = Join-Path $runtime 'python.exe'
$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$requirements = Join-Path $PSScriptRoot 'requirements-web.txt'

function Test-Python([string]$Exe, [string]$Code) {
    if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { return $false }
    $ErrorActionPreference = 'SilentlyContinue'
    try {
        & $Exe -s -X utf8 -c $Code 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Install-WebPackages([string]$Exe) {
    Write-Host '正在安装网页所需的音频库…'
    if (-not (Test-Python $Exe 'import pip')) {
        & $Exe -m ensurepip
        if ($LASTEXITCODE) { throw '无法初始化 pip。' }
    }
    & $Exe -m pip --disable-pip-version-check install --no-warn-script-location --only-binary=:all: --index-url https://pypi.org/simple -r $requirements
    if ($LASTEXITCODE) { throw '音频库安装失败。请检查能否连接 PyPI，然后重新运行配置。' }
}

function Get-PackageHash([string]$Path) {
    $hash = [Security.Cryptography.SHA256]::Create()
    $file = [IO.File]::OpenRead($Path)
    try { return [BitConverter]::ToString($hash.ComputeHash($file)).Replace('-', '') }
    finally { $file.Dispose(); $hash.Dispose() }
}

function Install-PortablePython {
    # The PSF's Windows x64 NuGet distribution includes pip, venv and the VC runtime.
    $version = '3.13.17'
    $sha256 = 'DCE409744B088F94C6E37BA41F8100C384C27E029E843237364C602D30D475E5'
    $package = Join-Path $toolsRoot "python.$version.nupkg"
    $url = "https://api.nuget.org/v3-flatcontainer/python/$version/python.$version.nupkg"
    $stage = Join-Path $toolsRoot ('web-setup-' + [Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($stage) | Out-Null
    try {
        if (-not (Test-Path -LiteralPath $package -PathType Leaf) -or
            (Get-PackageHash $package) -ne $sha256) {
            Write-Host "正在下载项目专用的 Python $version（Windows x64）…"
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            $ProgressPreference = 'SilentlyContinue'
            $download = Join-Path $stage 'python.nupkg'
            Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $download -TimeoutSec 180
            if ((Get-PackageHash $download) -ne $sha256) {
                throw 'Python 下载文件校验失败，请重试。'
            }
            Copy-Item -LiteralPath $download -Destination $package -Force
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($package, $stage)
        $payload = Join-Path $stage 'tools'
        $exe = Join-Path $payload 'python.exe'
        Install-WebPackages $exe
        if (-not (Test-Python $exe $audioCheck)) { throw '便携环境的音频自检失败。' }
        # Preserve a broken installation until its replacement is fully prepared.
        $previous = $null
        if (Test-Path -LiteralPath $runtime) {
            $item = Get-Item -LiteralPath $runtime
            if ($item.Parent.FullName -ne $toolsRoot -or $item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw '便携环境目录指向其他位置，请检查 .tools\web-python。'
            }
            $previous = Join-Path $toolsRoot ('web-python-backup-' + [Guid]::NewGuid().ToString('N'))
            [IO.Directory]::Move($runtime, $previous)
            Write-Host "旧网页环境已保存在 $previous"
        }
        try { [IO.Directory]::Move($payload, $runtime) }
        catch {
            if ($previous -and -not (Test-Path -LiteralPath $runtime)) { [IO.Directory]::Move($previous, $runtime) }
            throw
        }
    } finally {
        $stageItem = Get-Item -LiteralPath $stage
        if ($stageItem.Parent.FullName -eq $toolsRoot -and $stageItem.Name -match '^web-setup-[0-9a-f]{32}$' -and
            -not ($stageItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Remove-Item -LiteralPath $stageItem.FullName -Recurse -Force
        }
    }
}

$lock = $null
try {
    [IO.Directory]::CreateDirectory($toolsRoot) | Out-Null
    try {
        $lock = [IO.File]::Open((Join-Path $toolsRoot 'web-setup.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    } catch [IO.IOException] { throw '无法锁定配置目录。请关闭另一个配置窗口，并确认项目目录可写。' }

    $versionCheck = 'import sys, struct; assert (3,10) <= sys.version_info[:2] <= (3,13) and struct.calcsize(''P'') == 8'
    $audioCheck = 'import io, numpy as np, soundfile as sf; b=io.BytesIO(); sf.write(b,np.zeros(16),16000,format=''WAV''); b.seek(0); assert sf.info(b).frames == 16'
    Write-Host "项目目录：$PSScriptRoot"
    if (Test-Python $portablePython $versionCheck) {
        $python = $portablePython
    } elseif (-not (Test-Path -LiteralPath $portablePython) -and
              (Test-Python $venvPython ($versionCheck + '; assert sys.prefix != sys.base_prefix'))) {
        $python = $venvPython
    } else {
        Install-PortablePython
        $python = $portablePython
    }
    if (-not (Test-Python $python $audioCheck)) { Install-WebPackages $python }
    if (-not (Test-Python $python $audioCheck)) { throw '无法正常读写 WAV，请检查上方安装信息。' }
    Write-Host "本地网页环境就绪：$python"
    $options = @()
    if ($NonInteractive) { $options += '--non-interactive' }
    if ($SkipServerCheck) { $options += '--skip-server-check' }
    & $python -X utf8 -m scripts.check_platform_setup @options
    if ($LASTEXITCODE) { throw '配置检查未完成，请按上方提示修正后重试。' }
} catch {
    Write-Host ("配置失败：" + $_.Exception.Message) -ForegroundColor Red
    exit 1
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
}
