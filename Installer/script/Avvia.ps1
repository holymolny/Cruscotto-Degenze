<#
    Accende il Cruscotto Degenze e apre il browser sulla pagina di accesso.

    Il programma è un sito web che gira sul tuo stesso computer: per usarlo
    deve esserci un server acceso, ed è quello che parte in questa finestra.
    Finché la finestra resta aperta il Cruscotto funziona; chiudendola si
    spegne, come si spegne un programma qualsiasi.
#>

[CmdletBinding()]
param(
    [string]$CartellaApp,
    [string]$Indirizzo = '127.0.0.1',
    [int]$Porta = 8000
)

$ErrorActionPreference = 'Stop'

# Non fra i valori predefiniti del blocco param(): in Windows PowerShell 5.1
# $PSScriptRoot là dentro è ancora vuoto.
$CartellaScript = $PSScriptRoot
if (-not $CartellaScript) { $CartellaScript = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $CartellaApp)    { $CartellaApp    = Split-Path -Parent $CartellaScript }

function Test-Risponde {
    param([string]$Macchina, [int]$Porta, [int]$MilliSecondi = 400)

    $cliente = New-Object System.Net.Sockets.TcpClient
    try {
        $tentativo = $cliente.BeginConnect($Macchina, $Porta, $null, $null)
        if (-not $tentativo.AsyncWaitHandle.WaitOne($MilliSecondi)) { return $false }
        $cliente.EndConnect($tentativo)
        return $true
    } catch {
        return $false
    } finally {
        $cliente.Close()
    }
}

function Esci-ConErrore {
    param([string[]]$Righe)

    Write-Host ''
    foreach ($r in $Righe) { Write-Host "   $r" -ForegroundColor Red }
    Write-Host ''
    exit 1
}

$pythonVenv = Join-Path $CartellaApp '.venv\Scripts\python.exe'
$server     = Join-Path $CartellaScript 'server.py'
$configura  = Join-Path $CartellaScript 'Configura.ps1'

if (-not (Test-Path -LiteralPath $pythonVenv)) {
    Esci-ConErrore @(
        'Il Cruscotto non risulta configurato: manca la cartella .venv.',
        '',
        'Succede se l''installazione si è interrotta a metà. Per riprenderla:',
        '',
        "  powershell -ExecutionPolicy Bypass -File `"$configura`""
    )
}

# Il Cruscotto è già acceso? Capita facilmente: si chiude la finestra del
# browser credendo di aver chiuso il programma, e poi si clicca di nuovo
# sull'icona. Invece di lasciar partire un secondo server che troverebbe la
# porta occupata, riportiamo la persona sulla pagina che sta già girando.
if (Test-Risponde -Macchina $Indirizzo -Porta $Porta) {
    Write-Host ''
    Write-Host '   Il Cruscotto Degenze è già acceso: riapro la pagina.' -ForegroundColor Yellow
    Write-Host '   (il server gira in un''altra finestra: è quella da chiudere per spegnerlo)'
    Write-Host ''
    Start-Process "http://${Indirizzo}:${Porta}/"
    Start-Sleep -Seconds 3
    exit 0
}

Set-Location -LiteralPath $CartellaApp

# Il browser lo apre uno script a parte, in una finestra nascosta: deve
# aspettare che il server sia pronto, e noi qui stiamo per farlo partire.
Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', "`"$(Join-Path $CartellaScript 'ApriBrowser.ps1')`"",
    '-Indirizzo', $Indirizzo, '-Porta', $Porta
) | Out-Null

& $pythonVenv $server
$codice = $LASTEXITCODE

if ($codice -ne 0) {
    Esci-ConErrore @(
        "Il Cruscotto si è fermato con un errore (codice $codice).",
        'Il messaggio con la causa è qui sopra.'
    )
}

exit 0
