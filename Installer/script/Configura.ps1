<#
    Configura il Cruscotto Degenze dopo che il setup ha copiato i file.

    Il setup .exe si limita a mettere i file sul disco: tutto quello che
    serve perché il programma parta davvero — Python, l'ambiente virtuale, le
    librerie, il file .env, il database, il primo amministratore — lo fa
    questo script. È separato dal setup di proposito: così lo si può
    rilanciare a mano se qualcosa va storto, o dopo aver aggiornato i file
    del programma, senza dover reinstallare tutto.

        powershell -ExecutionPolicy Bypass -File installazione\Configura.ps1

    Senza il file delle credenziali (che scrive la procedura guidata) salta
    semplicemente la creazione dell'amministratore.
#>

[CmdletBinding()]
param(
    # Cartella in cui è stato installato il programma. Se non viene passata,
    # la ricava da dove si trova questo script: installazione\ sta dentro.
    [string]$CartellaApp,

    # File scritto dalla procedura guidata con i dati dell'amministratore.
    # Viene cancellato appena letto: contiene una password.
    [string]$FileCredenziali,

    # Versione di Python da installare se sul PC non ce n'è una adatta.
    [string]$VersionePython = '3.12.10',

    # In caso di errore lo script aspetta un tasto, altrimenti la finestra si
    # chiuderebbe portandosi via il messaggio. Chi lo lancia da un altro
    # script, dove non c'è nessuno a premere niente, usa questo interruttore.
    [switch]$SenzaPausa
)

$ErrorActionPreference = 'Stop'

# I valori qui sotto non possono stare fra i valori predefiniti del blocco
# param(): in Windows PowerShell 5.1 $PSScriptRoot là dentro è ancora vuoto,
# e lo script morirebbe prima di cominciare.
$CartellaScript = $PSScriptRoot
if (-not $CartellaScript) { $CartellaScript = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $CartellaApp)     { $CartellaApp     = Split-Path -Parent $CartellaScript }
if (-not $FileCredenziali) { $FileCredenziali = Join-Path $CartellaScript 'amministratore.dati' }

# Le versioni su cui il programma è stato provato. La prima è quella che
# installiamo noi se non troviamo niente; le altre le accettiamo se ci sono
# già, per non mettere sul PC un secondo Python senza motivo.
$VersioniAmmesse = @('3.12', '3.13')

$Passo = 0
$PassiTotali = 7

function Scrivi-Passo {
    param([string]$Testo)
    $script:Passo++
    Write-Host ''
    Write-Host ("[$script:Passo/$PassiTotali] $Testo") -ForegroundColor Cyan
}

function Scrivi-Esito {
    param([string]$Testo)
    Write-Host "      $Testo" -ForegroundColor Green
}

function Scrivi-Avviso {
    param([string]$Testo)
    Write-Host "      $Testo" -ForegroundColor Yellow
}

# --------------------------------------------------------------------------
# Python
# --------------------------------------------------------------------------

function Get-VersionePython {
    <#  Chiede a un eseguibile che versione di Python sia, nella forma "3.12".
        Restituisce $null se non risponde: sul PATH di Windows può esserci il
        finto python.exe del Microsoft Store, che non esegue nulla e serve
        solo ad aprire il negozio. #>
    param([string]$Eseguibile)

    if (-not (Test-Path -LiteralPath $Eseguibile)) { return $null }
    try {
        $versione = & $Eseguibile -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    } catch { return $null }
    if ($LASTEXITCODE -ne 0 -or -not $versione) { return $null }
    return $versione.Trim()
}

function Update-PercorsoDiRicerca {
    <#  Rilegge il PATH dal registro di sistema.

        Serve subito dopo aver installato Python: la variabile PATH di questa
        finestra è stata fotografata quando il processo è partito, e non sa
        nulla delle cartelle aggiunte da allora. #>
    $macchina = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $utente   = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = (@($macchina, $utente) | Where-Object { $_ }) -join ';'
}

function Find-Python {
    <#  Cerca un Python adatto e restituisce il percorso del suo python.exe. #>
    $candidati = New-Object System.Collections.Generic.List[string]

    # 1. Il "py launcher", che sa elencare tutti i Python installati.
    $lanciatore = Get-Command py -ErrorAction SilentlyContinue
    if ($lanciatore) {
        foreach ($v in $VersioniAmmesse) {
            try {
                $trovato = & $lanciatore.Source "-$v" -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $trovato) { $candidati.Add($trovato.Trim()) }
            } catch { }
        }
    }

    # 2. Quello che risponde al comando "python".
    $sulPercorso = Get-Command python -ErrorAction SilentlyContinue
    if ($sulPercorso) { $candidati.Add($sulPercorso.Source) }

    # 3. Le cartelle in cui Python si installa di solito, se il PATH non è
    #    ancora aggiornato.
    foreach ($v in $VersioniAmmesse) {
        $senzaPunto = $v.Replace('.', '')
        $candidati.Add("$env:LOCALAPPDATA\Programs\Python\Python$senzaPunto\python.exe")
        $candidati.Add("$env:ProgramFiles\Python$senzaPunto\python.exe")
    }

    foreach ($c in ($candidati | Select-Object -Unique)) {
        $versione = Get-VersionePython -Eseguibile $c
        if ($versione -and ($VersioniAmmesse -contains $versione)) {
            return [pscustomobject]@{ Eseguibile = $c; Versione = $versione }
        }
    }
    return $null
}

function Install-Python {
    <#  Installa Python solo per l'utente corrente: così non servono i
        permessi di amministratore e l'installazione del Cruscotto resta
        una cosa che si fa con un doppio clic. #>

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host '      Installo Python con winget (qualche minuto)...'
        $ramo = ($VersionePython -split '\.')[0..1] -join '.'
        & $winget.Source install --id "Python.Python.$ramo" --source winget `
            --scope user --silent --accept-package-agreements `
            --accept-source-agreements --disable-interactivity
        Update-PercorsoDiRicerca
        $trovato = Find-Python
        if ($trovato) { return $trovato }
        Scrivi-Avviso 'winget non è bastato: provo a scaricare Python da python.org.'
    } else {
        Write-Host '      winget non è disponibile: scarico Python da python.org.'
    }

    $indirizzo = "https://www.python.org/ftp/python/$VersionePython/python-$VersionePython-amd64.exe"
    $scaricato = Join-Path $env:TEMP "python-$VersionePython-amd64.exe"

    Write-Host "      Scarico $indirizzo"
    # Senza questa riga Invoke-WebRequest disegna una barra di avanzamento che
    # su alcuni PC rallenta il download di parecchio.
    $vecchiaPreferenza = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'
    try {
        Invoke-WebRequest -Uri $indirizzo -OutFile $scaricato -UseBasicParsing
    } finally { $ProgressPreference = $vecchiaPreferenza }

    Write-Host '      Installo Python...'
    $argomenti = @(
        '/quiet',
        'InstallAllUsers=0',      # solo per me: niente richiesta di amministratore
        'PrependPath=1',          # aggiunge python al PATH
        'Include_launcher=1',     # installa anche il comando "py"
        'Include_test=0',         # i test di Python stesso non servono
        'Include_doc=0',
        'AssociateFiles=0',
        'Shortcuts=0'             # niente voci nel menu Start: non è un programma per l'utente
    )
    $processo = Start-Process -FilePath $scaricato -ArgumentList $argomenti -Wait -PassThru
    Remove-Item -LiteralPath $scaricato -Force -ErrorAction SilentlyContinue

    if ($processo.ExitCode -ne 0) {
        throw "L'installazione di Python è terminata con codice $($processo.ExitCode)."
    }

    Update-PercorsoDiRicerca
    return (Find-Python)
}

# --------------------------------------------------------------------------
# Inizio
# --------------------------------------------------------------------------

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor White
Write-Host '   Cruscotto Degenze - preparazione del programma' -ForegroundColor White
Write-Host '  ============================================================' -ForegroundColor White
Write-Host "   Cartella: $CartellaApp"

try {
    # Dentro il try, non prima: fuori di qui un errore uscirebbe come muro di
    # testo rosso di PowerShell invece che come messaggio leggibile.
    if (-not (Test-Path -LiteralPath (Join-Path $CartellaApp 'wsgi.py'))) {
        throw "In «$CartellaApp» non c'è wsgi.py: non sembra la cartella del programma."
    }
    Set-Location -LiteralPath $CartellaApp

    # ---------------------------------------------------------------- 1/7 --
    Scrivi-Passo 'Controllo Python'
    $python = Find-Python
    if ($python) {
        Scrivi-Esito "Python $($python.Versione) già presente: $($python.Eseguibile)"
    } else {
        Write-Host '      Nessun Python adatto sul PC.'
        $python = Install-Python
        if (-not $python) {
            throw @'
Python è stato installato ma non riesco a trovarlo.
Prova a riavviare il PC e a rilanciare:
  powershell -ExecutionPolicy Bypass -File installazione\Configura.ps1
'@
        }
        Scrivi-Esito "Python $($python.Versione) installato: $($python.Eseguibile)"
    }

    # ---------------------------------------------------------------- 2/7 --
    Scrivi-Passo 'Ambiente virtuale'
    # Un "ambiente virtuale" è una copia isolata di Python con dentro solo le
    # librerie di questo programma: aggiornare qualcosa qui non tocca nessun
    # altro programma del PC, e disinstallare il Cruscotto non lascia in giro
    # librerie orfane.
    $cartellaVenv = Join-Path $CartellaApp '.venv'
    $pythonVenv   = Join-Path $cartellaVenv 'Scripts\python.exe'

    $versioneVenv = Get-VersionePython -Eseguibile $pythonVenv
    if ($versioneVenv -and ($VersioniAmmesse -contains $versioneVenv)) {
        Scrivi-Esito "Ambiente virtuale già pronto (Python $versioneVenv)."
    } else {
        if (Test-Path -LiteralPath $cartellaVenv) {
            Scrivi-Avviso 'Ambiente virtuale inutilizzabile: lo rifaccio da zero.'
            Remove-Item -LiteralPath $cartellaVenv -Recurse -Force
        }
        & $python.Eseguibile -m venv $cartellaVenv
        if ($LASTEXITCODE -ne 0) { throw "Creazione dell'ambiente virtuale fallita (codice $LASTEXITCODE)." }
        Scrivi-Esito 'Ambiente virtuale creato in .venv'
    }

    # ---------------------------------------------------------------- 3/7 --
    Scrivi-Passo 'Librerie (può richiedere qualche minuto)'
    # L'aggiornamento di pip è una comodità, non un requisito: le librerie si
    # installano anche con la versione che arriva insieme a Python. Se fallisce
    # tiriamo dritto, invece di far naufragare l'installazione per un di più.
    & $pythonVenv -m pip install --upgrade pip --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Scrivi-Avviso 'Non sono riuscito ad aggiornare pip: proseguo con quello che c''è.' }

    & $pythonVenv -m pip install -r (Join-Path $CartellaApp 'requirements.txt') --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        throw @"
Installazione delle librerie fallita (codice $LASTEXITCODE).
La causa più comune è la mancanza di connessione a internet: le librerie si
scaricano da pypi.org. Controlla la connessione e rilancia
  powershell -ExecutionPolicy Bypass -File installazione\Configura.ps1
"@
    }
    Scrivi-Esito 'Librerie installate.'

    # ---------------------------------------------------------------- 4/7 --
    Scrivi-Passo 'Configurazione (.env)'
    $fileEnv = Join-Path $CartellaApp '.env'
    if (Test-Path -LiteralPath $fileEnv) {
        # Non lo tocchiamo: dentro c'è la chiave con cui sono firmate le
        # sessioni già aperte, e riscriverla scollegherebbe tutti.
        Scrivi-Esito 'Il file .env esiste già: lo lascio com è.'
    } else {
        $byte = New-Object byte[] 32
        $generatore = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        try { $generatore.GetBytes($byte) } finally { $generatore.Dispose() }
        $chiave = -join ($byte | ForEach-Object { $_.ToString('x2') })

        # Configurazione «sviluppo» e non «produzione»: qui il programma gira
        # su http://127.0.0.1, mentre la configurazione di produzione pretende
        # che il cookie di sessione viaggi solo su HTTPS — dietro IIS, sulla
        # macchina virtuale. Usarla qui impedirebbe l'accesso.
        $contenuto = @"
# File scritto dall'installer il $(Get-Date -Format 'dd/MM/yyyy HH:mm').
# Configurazione dell'installazione locale su questo PC.

# Chiave con cui vengono firmati i cookie di sessione: generata a caso qui,
# diversa su ogni PC. Se la cambi, chi è collegato deve rifare l'accesso.
SECRET_KEY=$chiave

# Il programma gira in locale su http://127.0.0.1:8000, non dietro IIS.
FLASK_CONFIG=sviluppo

# Vuoto: viene usato il file cruscotto.db qui nella cartella del programma.
DATABASE_URL=

# Minuti di inattività dopo i quali l'utente viene disconnesso.
MINUTI_INATTIVITA=15

# Dice al comando "flask" quale file contiene l'applicazione.
FLASK_APP=wsgi.py
"@
        # Senza BOM: python-dotenv leggerebbe i primi caratteri invisibili
        # come parte del nome della prima variabile.
        [System.IO.File]::WriteAllText($fileEnv, $contenuto, (New-Object System.Text.UTF8Encoding($false)))
        Scrivi-Esito 'Scritto .env con una chiave di sessione nuova.'
    }

    # ---------------------------------------------------------------- 5/7 --
    Scrivi-Passo 'Database'
    $env:FLASK_APP = 'wsgi.py'
    & $pythonVenv -m flask db upgrade
    if ($LASTEXITCODE -ne 0) { throw "Creazione del database fallita (codice $LASTEXITCODE)." }
    Scrivi-Esito 'Database aggiornato all ultima versione.'

    # ---------------------------------------------------------------- 6/7 --
    Scrivi-Passo 'Amministratore'
    # Quattro righe: nome, cognome, nome utente, password. Il file lo scrive
    # la procedura guidata; se manca (installazione silenziosa, oppure
    # Configura.ps1 rilanciato a mano) semplicemente saltiamo il passo.
    $credenziali = $null
    if (Test-Path -LiteralPath $FileCredenziali) {
        try {
            $righe = @(Get-Content -LiteralPath $FileCredenziali -Encoding UTF8)
            if ($righe.Count -ge 4 -and -not ($righe[0..3] | Where-Object { -not $_ })) {
                $credenziali = $righe
            }
        } finally {
            # La password non deve restare sul disco un minuto più del
            # necessario: prima ci scriviamo sopra, poi cancelliamo.
            Set-Content -LiteralPath $FileCredenziali -Value ('x' * 512) -Force -ErrorAction SilentlyContinue
            Remove-Item -LiteralPath $FileCredenziali -Force -ErrorAction SilentlyContinue
        }
    }

    if ($credenziali) {
        # Passiamo i dati come variabili d'ambiente e non come argomenti: gli
        # argomenti di un processo sono leggibili da chiunque guardi l'elenco
        # dei processi, le variabili d'ambiente no.
        $env:CRUSCOTTO_ADMIN_NOME     = $credenziali[0]
        $env:CRUSCOTTO_ADMIN_COGNOME  = $credenziali[1]
        $env:CRUSCOTTO_ADMIN_USERNAME = $credenziali[2]
        $env:CRUSCOTTO_ADMIN_PASSWORD = $credenziali[3]
        try {
            & $pythonVenv (Join-Path $CartellaScript 'crea_admin_auto.py')
            if ($LASTEXITCODE -ne 0) {
                throw @"
Creazione dell'amministratore fallita (codice $LASTEXITCODE).
Il resto dell'installazione è a posto: puoi crearlo a mano con
  .venv\Scripts\flask.exe crea-admin
"@
            }
        } finally {
            Remove-Item Env:\CRUSCOTTO_ADMIN_NOME, Env:\CRUSCOTTO_ADMIN_COGNOME,
                        Env:\CRUSCOTTO_ADMIN_USERNAME, Env:\CRUSCOTTO_ADMIN_PASSWORD `
                        -ErrorAction SilentlyContinue
        }
    } else {
        Scrivi-Avviso 'Nessuna credenziale da usare: salto questo passo.'
        Scrivi-Avviso 'Per creare un amministratore a mano: .venv\Scripts\flask.exe crea-admin'
    }

    # ---------------------------------------------------------------- 7/7 --
    Scrivi-Passo 'Verifica finale'
    & $pythonVenv -m flask controlla-dati-fissi
    if ($LASTEXITCODE -ne 0) { throw 'I dati fissi (reparti e checklist) non risultano completi.' }

    Write-Host ''
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host '   Tutto pronto.' -ForegroundColor Green
    Write-Host '  ============================================================' -ForegroundColor Green
    Write-Host ''
    exit 0

} catch {
    Write-Host ''
    Write-Host '  ------------------------------------------------------------' -ForegroundColor Red
    Write-Host '   Installazione interrotta' -ForegroundColor Red
    Write-Host '  ------------------------------------------------------------' -ForegroundColor Red
    Write-Host ''
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ''
    Write-Host '   I file del programma restano dove sono: puoi correggere il'
    Write-Host '   problema e rilanciare solo questa parte, senza reinstallare:'
    Write-Host ''
    Write-Host "     powershell -ExecutionPolicy Bypass -File `"$CartellaScript\Configura.ps1`""
    Write-Host ''
    if (-not $SenzaPausa) { Read-Host '   Premi Invio per chiudere' }
    exit 1
}
