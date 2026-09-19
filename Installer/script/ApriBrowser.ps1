<#
    Aspetta che il Cruscotto risponda, poi apre il browser.

    Gira in una finestra nascosta, in parallelo al server: non possiamo
    aprire il browser prima di far partire il server (troverebbe la pagina
    vuota) né dopo (il server non "finisce", resta in ascolto finché non lo
    si spegne). Quindi qualcuno deve stare a guardare, ed è questo script.
#>

[CmdletBinding()]
param(
    [string]$Indirizzo = '127.0.0.1',
    [int]$Porta = 8000,
    [int]$SecondiDiAttesa = 90
)

$ErrorActionPreference = 'SilentlyContinue'

function Test-Risponde {
    param([string]$Macchina, [int]$Porta, [int]$MilliSecondi = 300)

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

$scadenza = (Get-Date).AddSeconds($SecondiDiAttesa)
while ((Get-Date) -lt $scadenza) {
    if (Test-Risponde -Macchina $Indirizzo -Porta $Porta) {
        Start-Process "http://${Indirizzo}:${Porta}/"
        exit 0
    }
    Start-Sleep -Milliseconds 400
}

# Scaduto il tempo: il server non è partito. Non apriamo niente, perché il
# messaggio d'errore è già nella finestra del server, dove la persona lo vede.
exit 1
