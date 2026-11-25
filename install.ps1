# softtarget installer for Windows.
#   irm https://raw.githubusercontent.com/ckarandev010/softtarget/main/install.ps1 | iex
# Installs Python and Ollama with winget if they are missing, installs softtarget into
# %USERPROFILE%\.softtarget\venv, downloads the model and starts the labs.
# Env overrides: SOFTTARGET_MODEL (model), SOFTTARGET_SRC (pip source, for testing).

$ErrorActionPreference = "Stop"
function Say($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Fail($m) { Write-Host "softtarget install failed: $m" -ForegroundColor Red; throw $m }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Find-Python {
    foreach ($c in @("python", "py")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            try {
                $ok = & $c -c "import sys; print(sys.version_info >= (3, 10))" 2>$null
                if ($ok -eq "True") { return $c }
            } catch {}
        }
    }
    return $null
}
function Have-Winget { [bool](Get-Command winget -ErrorAction SilentlyContinue) }

$src = if ($env:SOFTTARGET_SRC) { $env:SOFTTARGET_SRC } else { "https://github.com/ckarandev010/softtarget/archive/refs/heads/main.zip" }
$home_dir = Join-Path $env:USERPROFILE ".softtarget"
$venv = Join-Path $home_dir "venv"

# 1. Python 3.10+
$py = Find-Python
if (-not $py) {
    if (-not (Have-Winget)) { Fail "Python 3.10+ not found. Install it from https://www.python.org/downloads/ and rerun." }
    Say "Installing Python 3.12 (winget)"
    winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements | Out-Host
    Refresh-Path
    $py = Find-Python
    if (-not $py) { Fail "Python installed but not on PATH yet. Open a new PowerShell window and rerun." }
}
Say "Using $(& $py --version)"

# 2. Ollama
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    $local = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
    if (Test-Path (Join-Path $local "ollama.exe")) {
        $env:Path += ";$local"
    } else {
        if (-not (Have-Winget)) { Fail "Ollama not found. Install it from https://ollama.com/download and rerun." }
        Say "Installing Ollama (winget)"
        winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements | Out-Host
        Refresh-Path
        if (Test-Path (Join-Path $local "ollama.exe")) { $env:Path += ";$local" }
        if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) { Fail "Ollama installed but not on PATH yet. Open a new PowerShell window and rerun." }
    }
}
Say "Ollama found: $((Get-Command ollama).Source)"

# 3. softtarget in its own virtual environment
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) {
    Say "Creating $venv"
    New-Item -ItemType Directory -Force $home_dir | Out-Null
    & $py -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail "could not create a virtual environment" }
}
$vpy = Join-Path $venv "Scripts\python.exe"
Say "Installing softtarget"
& $vpy -m pip install --quiet --disable-pip-version-check --upgrade $src
if ($LASTEXITCODE -ne 0) { Fail "pip install failed" }

# 4. Model + first run
$args_ = @()
if ($env:SOFTTARGET_MODEL) { $args_ += @("--model", $env:SOFTTARGET_MODEL) }
& $vpy -m softtarget setup @args_
if ($LASTEXITCODE -ne 0) { Fail "setup did not finish (see above)" }

$exe = Join-Path $venv "Scripts\softtarget.exe"
Say "Installed. Start it any time with:"
Write-Host "    & `"$exe`""
if (-not $env:SOFTTARGET_NO_RUN) { & $exe @args_ }
