<#.SYNOPSIS
Sync Python dependencies.#>
Param(
    # Python version.
    [string]$Version,
    # Sync to highest dependencies.
    [switch]$High,
    # Recompile dependencies.
    [switch]$Compile,
    # Add all local dependency compilations to the lock.
    [switch]$Lock,
    # Don't run pre-sync actions.
    [switch]$NoPreSync,
    # Don't run post-sync actions.
    [switch]$NoPostSync
)

# ? Fail early
. 'scripts/Set-StrictErrors.ps1'
# ? Allow disabling CI when in CI, in order to test local dev workflows
$Env:CI = $Env:SYNC_PY_DISABLE_CI ? $null : $Env:CI
# ? Don't pre-sync or post-sync in CI
$NoPreSync = $NoPreSync ? $NoPreSync : $Env:CI
$NoPostSync = $NoPostSync ? $NoPostSync : $Env:CI
# ? Core dependencies needed for syncing
$PRE_SYNC_DEPENDENCIES = 'requirements/sync.in'

function Sync-Py {
    <#.SYNOPSIS
    Sync Python dependencies.#>

    '***SYNCING' | Write-PyProgress
    $py = $Env:CI ? (Get-PySystem $Version) : (Get-Py $Version)
    # ? Install directly to system if in CI, breaking system packages if needed
    $uvPip = "$py -m uv pip"
    $System = $Env:CI ? '--system --break-system-packages' : ''
    $install = "$uvPip install $System"
    $sync = "$uvPip sync $System"
    # ? Python scripts for utilities not invoked with e.g. `python -m` (e.g. pre-commit)
    $scripts = $(Split-Path $py)

    'INSTALLING DEPENDENCIES FOR SYNCING' | Write-PyProgress
    Invoke-Expression "$py -m pip install $(Get-Content $PRE_SYNC_DEPENDENCIES)"

    'INSTALLING TOOLS' | Write-PyProgress
    # ? Install the `boilercv_tools` Python module
    Invoke-Expression "$install --editable scripts/."

    if (!$NoPreSync) {
        'RUNNING PRE-SYNC TASKS' | Write-PyProgress

        'SYNCING SUBMODULES' | Write-PyProgress
        git submodule update --init --merge
        'SUBMODULES SYNCED' | Write-PyProgress -Done

        if ($Env:CI) {
        'SYNCING PROJECT WITH TEMPLATE' | Write-PyProgress
        $head = git rev-parse HEAD:submodules/template
        Invoke-Expression "$py -m copier update --defaults --vcs-ref $head"
        }

        'PRE-SYNC DONE' | Write-PyProgress -Done
    }

    'SYNCING DEPENDENCIES' | Write-PyProgress
    $High = $High ? '--high' : ''
    # ? Compile or retrieve compiled dependencies
    if ($Compile) { $comp = Invoke-Expression "$py -m boilercv_tools compile $High" }
    else { $comp = Invoke-Expression "$py -m boilercv_tools get-comp $High" }
    # ? Lock
    if ($Lock) { Invoke-Expression "$py -m boilercv_tools lock" }
    # ? Sync
    if (!$NoPreSync -and (Test-FileLock "$scripts/dvc$($IsWindows ? '.exe': '')")) {
        'The DVC VSCode extension is locking `dvc.exe`. INSTALLING INSTEAD OF SYNCING' |
            Write-PyProgress
        $compNoDvc = $comp | Get-Item | Get-Content | Select-String -Pattern '^(?!dvc[^-])'
        $compNoDvc | Set-Content $comp
        Invoke-Expression "$install --requirement $comp"
        'DEPENDENCIES INSTALLED (Disable the VSCode DVC extension or close VSCode and sync in an external terminal to perform a full sync)' |
            Write-PyProgress -Done
    }
    else {
        Invoke-Expression "$sync $comp"
        'DEPENDENCIES SYNCED' | Write-PyProgress -Done
    }

    if (!$NoPostSync) {
        'RUNNING POST-SYNC TASKS' | Write-PyProgress

        'SYNCING LOCAL DEV CONFIGS' | Write-PyProgress
        Invoke-Expression "$py -m boilercv_tools sync-local-dev-configs"
        'LOCAL DEV CONFIGS SYNCED' | Write-PyProgress -Done

        'INSTALLING MISSING PRE-COMMIT HOOKS' | Write-PyProgress
        Invoke-Expression "$scripts/pre-commit install"

        'POST-SYNC TASKS COMPLETE' | Write-PyProgress -Done
    }

    Write-Host ''
    '...DONE ***' | Write-PyProgress -Done
}

# * -------------------------------------------------------------------------------- * #
# * CUSTOM FUNCTIONS

function Get-PyDevVersion {
    <#.SYNOPSIS
    Get the expected version of Python for development, from '.copier-answers.yml'.#>
    $ver_pattern = '^python_version:\s?["'']([^"'']+)["'']$'
    $re = Get-Content '.copier-answers.yml' | Select-String -Pattern $ver_pattern
    return $re.Matches.Groups[1].value
}

function Write-PyProgress {
    <#.SYNOPSIS
    Write progress and completion messages.#>
    Param([Parameter(Mandatory, ValueFromPipeline)][string]$Message,
        [switch]$Done)
    begin { $Color = $Done ? 'Green' : 'Yellow' }
    process {
        if (!$Done) { Write-Host }
        Write-Host "$Message$($Done ? '' : '...')" -ForegroundColor $Color
    }
}

function Test-FileLock {
    <#.SYNOPSIS
    Test whether a file handle is locked.#>
    Param ([parameter(Mandatory, ValueFromPipeline)][string]$Path)
    process {
        if ( !(Test-Path $Path) ) { return $false }
        try {
            if ($handle = (
                    New-Object 'System.IO.FileInfo' $Path).Open([System.IO.FileMode]::Open,
                    [System.IO.FileAccess]::ReadWrite,
                    [System.IO.FileShare]::None)
            ) { $handle.Close() }
            return $false
        }
        catch [System.IO.IOException], [System.UnauthorizedAccessException] { return $true }
    }
}

# * -------------------------------------------------------------------------------- * #
# * BASIC FUNCTIONS

function Get-Py {
    <#.SYNOPSIS
    Get Python interpreter, global in CI, or activated virtual environment locally.#>
    Param([Parameter(ValueFromPipeline)][string]$Version)
    begin { $venvPath = '.venv' }
    process {
        $Version = $Version ? $Version : (Get-PyDevVersion)
        $SysPy = Get-PySystem $Version
        if (!(Test-Path $venvPath)) {
            "CREATING VIRTUAL ENVIRONMENT: $venvPath" | Write-PyProgress
            Invoke-Expression "$SysPy -m venv $venvPath"
        }
        $VenvPy = Start-PyEnv $venvPath
        $foundVersion = Invoke-Expression "$VenvPy --version"
        if ($foundVersion |
                Select-String -Pattern "^Python $([Regex]::Escape($Version))\.\d+$") {
            "SYNCING VIRTUAL ENVIRONMENT: $(Resolve-Path $VenvPy -Relative)" |
                Write-PyProgress
            return $VenvPy
        }
        "REMOVING VIRTUAL ENVIRONMENT WITH INCORRECT PYTHON: $Env:VIRTUAL_ENV" |
            Write-PyProgress -Done
        Remove-Item -Recurse -Force $Env:VIRTUAL_ENV
        return Get-Py $Version
    }
}

function Get-PySystem {
    <#.SYNOPSIS
    Get system Python interpreter.#>
    Param([Parameter(Mandatory, ValueFromPipeline)][string]$Version)
    process {
        if ((Test-Command 'py') -and
        (py '--list' | Select-String -Pattern "^\s?-V:$([Regex]::Escape($Version))")) {
            return "py -$Version"
        }
        elseif (Test-Command "python$Version") { return "python$Version" }
        elseif (Test-Command 'python') { return 'python' }
        throw "Expected Python $Version, which does not appear to be installed. Ensure it is installed (e.g. from https://www.python.org/downloads/) and run this script again."
    }
}

function Start-PyEnv {
    <#.SYNOPSIS
    Activate and get the Python interpreter for the virtual environment.#>
    Param([Parameter(Mandatory, ValueFromPipeline)][string]$venvPath)
    process {
        if ($IsWindows) { $bin = 'Scripts'; $py = 'python.exe' }
        else { $bin = 'bin'; $py = 'python' }
        Invoke-Expression "$venvPath/$bin/Activate.ps1"
        return "$Env:VIRTUAL_ENV/$bin/$py"
    }
}

function Test-Command {
    <#.SYNOPSIS
    Like `Get-Command` but errors are ignored.#>
    return Get-Command @args -ErrorAction 'Ignore'
}

Sync-Py
