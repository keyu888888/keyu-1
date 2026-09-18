[CmdletBinding()]
param()

$ErrorActionPreference = 'SilentlyContinue'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Get-CommandCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string[]]$VersionArgs = @('--version')
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        return [ordered]@{
            available = $false
            path = $null
            version = $null
        }
    }

    $versionText = $null
    try {
        $versionText = (& $command.Source @VersionArgs 2>&1 | Select-Object -First 1).ToString()
    } catch {
        $versionText = 'installed; version query failed'
    }

    return [ordered]@{
        available = $true
        path = $command.Source
        version = $versionText
    }
}

function Get-BinaryCheck {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [string[]]$VersionArgs = @('--version'),
        [string]$PortableRoot,
        [string]$PortableFilter
    )

    $normal = Get-CommandCheck -Name $Name -VersionArgs $VersionArgs
    if ($normal.available) {
        return $normal
    }

    if ($PortableRoot -and (Test-Path $PortableRoot)) {
        $portable = Get-ChildItem $PortableRoot -Recurse -File -Filter $PortableFilter -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($portable) {
            $versionText = (& $portable.FullName @VersionArgs 2>&1 | Select-Object -First 1).ToString()
            return [ordered]@{
                available = $true
                path = $portable.FullName
                version = $versionText
            }
        }
    }

    return $normal
}

function Get-BlenderCheck {
    $command = Get-Command blender -ErrorAction SilentlyContinue
    if (-not $command) {
        $portable = Get-ChildItem (Join-Path $projectRoot 'tools\blender') -Recurse -Filter blender.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($portable) {
            $command = $portable
        }
    }
    if (-not $command) {
        $common = Get-ChildItem 'C:\Program Files\Blender Foundation' -Recurse -Filter blender.exe -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($common) {
            $command = $common
        }
    }

    if (-not $command) {
        return [ordered]@{ available = $false; path = $null; version = $null; background_test = $false }
    }

    $path = if ($command.Source) { $command.Source } else { $command.FullName }
    $version = (& $path --version 2>&1 | Select-Object -First 1).ToString()
    $backgroundOutput = & $path -b --python-expr "print('REDREAM_BLENDER_OK')" 2>&1
    $backgroundOk = [bool]($backgroundOutput -match 'REDREAM_BLENDER_OK')
    return [ordered]@{ available = $true; path = $path; version = $version; background_test = $backgroundOk }
}

$python = Get-BinaryCheck -Name 'python' -VersionArgs @('--version') -PortableRoot (Join-Path $projectRoot 'tools\python311') -PortableFilter 'python.exe'
if (-not $python.available) {
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        $installed = & $launcher.Source -0p 2>&1
        if ($LASTEXITCODE -eq 0 -and $installed -notmatch 'No installed Pythons') {
            $python = [ordered]@{ available = $true; path = $launcher.Source; version = ($installed -join '; ') }
        }
    }
}

$nvidia = Get-CommandCheck -Name 'nvidia-smi' -VersionArgs @('--query-gpu=name,memory.total,driver_version', '--format=csv,noheader')
$report = [ordered]@{
    checked_at = (Get-Date).ToString('o')
    platform = [System.Environment]::OSVersion.VersionString
    git = Get-CommandCheck -Name 'git' -VersionArgs @('--version')
    python = $python
    conda = Get-CommandCheck -Name 'conda' -VersionArgs @('--version')
    mamba = Get-CommandCheck -Name 'mamba' -VersionArgs @('--version')
    ffmpeg = Get-BinaryCheck -Name 'ffmpeg' -VersionArgs @('-version') -PortableRoot (Join-Path $projectRoot 'tools\ffmpeg') -PortableFilter 'ffmpeg.exe'
    ffprobe = Get-BinaryCheck -Name 'ffprobe' -VersionArgs @('-version') -PortableRoot (Join-Path $projectRoot 'tools\ffmpeg') -PortableFilter 'ffprobe.exe'
    blender = Get-BlenderCheck
    nvidia = $nvidia
    wsl = Get-CommandCheck -Name 'wsl' -VersionArgs @('--status')
    docker = Get-CommandCheck -Name 'docker' -VersionArgs @('--version')
}

$report | ConvertTo-Json -Depth 6
