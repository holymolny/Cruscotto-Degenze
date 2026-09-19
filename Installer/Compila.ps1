<#
    Costruisce CruscottoDegenze-Setup.exe a partire da CruscottoDegenze.iss.

        powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1

    Va rilanciato ogni volta che si modifica il programma: il setup contiene
    una copia dei file, quindi finché non si ricompila continua a installare
    la versione vecchia.

    Serve Inno Setup 6. Se manca, questo script lo installa con winget.
#>

[CmdletBinding()]
param(
    # Sovrascrive il numero di versione scritto nel .iss. Comodo per marcare
    # una copia di prova senza toccare il file versionato.
    [string]$Versione,

    # Compila senza chiedere nulla, anche se Inno Setup va installato.
    [switch]$Automatico
)

$ErrorActionPreference = 'Stop'

$Cartella = $PSScriptRoot
$Script   = Join-Path $Cartella 'CruscottoDegenze.iss'
$Uscita   = Join-Path $Cartella 'Output'

if (-not (Test-Path -LiteralPath $Script)) { throw "Non trovo $Script" }

function Find-Iscc {
    $candidati = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($c in $candidati) { if (Test-Path -LiteralPath $c) { return $c } }

    # Inno Setup si registra fra i programmi installati: se l'utente l'ha
    # messo altrove, lo troviamo comunque.
    $chiavi = @(
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    $voce = Get-ItemProperty $chiavi -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like '*Inno Setup*' } |
            Select-Object -First 1
    if ($voce -and $voce.InstallLocation) {
        $c = Join-Path $voce.InstallLocation 'ISCC.exe'
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return $null
}

$iscc = Find-Iscc
if (-not $iscc) {
    Write-Host 'Inno Setup non è installato su questo PC.' -ForegroundColor Yellow
    if (-not $Automatico) {
        $risposta = Read-Host 'Lo installo adesso con winget? [S/n]'
        if ($risposta -and $risposta.ToLower() -notin @('s', 'si', 'sì', 'y')) {
            throw 'Compilazione annullata: senza Inno Setup non si può costruire il setup.'
        }
    }
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw 'winget non è disponibile: scarica Inno Setup da https://jrsoftware.org/isdl.php'
    }
    & $winget.Source install --id JRSoftware.InnoSetup --source winget --silent `
        --accept-package-agreements --accept-source-agreements --disable-interactivity
    $iscc = Find-Iscc
    if (-not $iscc) { throw 'Inno Setup risulta installato ma non trovo ISCC.exe.' }
}

Write-Host "Compilatore: $iscc"

# Le immagini sono prodotte da uno script a parte: se qualcuno ha cancellato
# la cartella Output o i file generati, li rifacciamo ora invece di fallire.
$icona = Join-Path $Cartella 'risorse\cruscotto.ico'
if (-not (Test-Path -LiteralPath $icona)) {
    Write-Host 'Mancano le immagini: le rigenero dal logo.'
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Cartella 'risorse\PreparaImmagini.ps1')
}

New-Item -ItemType Directory -Path $Uscita -Force | Out-Null

$argomenti = @("/Q", "`"$Script`"")
if ($Versione) { $argomenti = @("/DVersioneApp=$Versione") + $argomenti }

Write-Host 'Compilazione in corso...'
& $iscc @argomenti
if ($LASTEXITCODE -ne 0) { throw "Compilazione fallita (codice $LASTEXITCODE)." }

$setup = Get-Item (Join-Path $Uscita 'CruscottoDegenze-Setup.exe')
Write-Host ''
Write-Host 'Fatto.' -ForegroundColor Green
Write-Host ("  {0}" -f $setup.FullName)
Write-Host ("  {0:N1} MB" -f ($setup.Length / 1MB))
