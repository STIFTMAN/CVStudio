# start.ps1
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$venvActivate = Join-Path $ScriptDir ".venv\Scripts\Activate.ps1"
$setupScript  = Join-Path $ScriptDir "setup.ps1"

function Activate-Venv {
    if (Test-Path $venvActivate) {
        & $venvActivate
    } else {
        throw "'.venv' nicht gefunden. Erwartet: $venvActivate"
    }
}

try {
    if (Test-Path $venvActivate) {
        Activate-Venv
    } else {
        if (-not (Test-Path $setupScript)) { throw "setup.ps1 fehlt: $setupScript" }
        & $setupScript
        Activate-Venv
    }
}
catch {
    # Policy-Fehler erkennen und mit Bypass neu starten
    if ($_.FullyQualifiedErrorId -like "*UnauthorizedAccess*") {
        Write-Host "Execution Policy blockiert Skripte. Starte mich selbst mit Bypass neu..."
        $ps = Join-Path $PSHOME "powershell.exe"
        & $ps -ExecutionPolicy Bypass -NoProfile -File $MyInvocation.MyCommand.Path
        exit $LASTEXITCODE
    }
    throw
}

# Im (neu) aktivierten venv starten
& python "main.py"
exit