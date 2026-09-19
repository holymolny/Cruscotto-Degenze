# Installer del Cruscotto Degenze

Questa cartella non fa parte del programma: serve a **costruire** il file
`CruscottoDegenze-Setup.exe`, cioè l'installazione con doppio clic da usare
su un PC Windows dove il Cruscotto non c'è ancora.

## Per chi vuole solo installare il programma

Apri `Output\CruscottoDegenze-Setup.exe` e segui la procedura. Non serve
altro, nemmeno Python: se manca, lo installa il setup.

Durante l'installazione serve la **connessione a internet**, perché Python e
le librerie si scaricano al momento. Una volta installato, il Cruscotto
funziona anche scollegato dalla rete.

> **Windows mostrerà «Windows ha protetto il PC».** È normale e non indica
> un problema: succede a ogni programma privo di firma digitale, e una firma
> si compra da un'autorità di certificazione. Clicca su **Ulteriori
> informazioni** e poi su **Esegui comunque**.

## Cosa fa il setup, in ordine

| # | Passo | Dove |
|--:|-------|------|
| 1 | Chiede dove installare e i dati del primo amministratore | procedura guidata |
| 2 | Copia i file del programma | procedura guidata |
| 3 | Installa Python 3.12 se non c'è | `Configura.ps1` |
| 4 | Crea l'ambiente virtuale `.venv` | `Configura.ps1` |
| 5 | Scarica le librerie di `requirements.txt` | `Configura.ps1` |
| 6 | Scrive `.env` con una chiave di sessione casuale | `Configura.ps1` |
| 7 | Crea il database con `flask db upgrade` | `Configura.ps1` |
| 8 | Crea l'amministratore | `crea_admin_auto.py` |
| 9 | Mette i collegamenti su Desktop e menu Start | procedura guidata |

Il programma finisce in `%LOCALAPPDATA%\Programs\CruscottoDegenze`, **non**
in `C:\Programmi`. Non è una svista: il Cruscotto scrive il proprio database
(`cruscotto.db`) nella cartella in cui è installato, e dentro `Programmi`
Windows non glielo lascerebbe fare senza permessi di amministratore. Così
invece l'installazione non chiede nulla a nessuno.

## Come si usa il programma installato

Il collegamento **Cruscotto Degenze** apre una finestra nera e poi il
browser. La finestra nera *è* il programma: finché resta aperta il Cruscotto
funziona, chiudendola si spegne. L'indirizzo è <http://127.0.0.1:8000> e
risponde solo su questo computer: nessun altro sulla rete può collegarsi.

## Aggiornare un'installazione esistente

Si rilancia lo stesso setup sulla **stessa cartella**. Non serve disinstallare
prima, e i dati non si toccano:

- il database `cruscotto.db` resta dov'è, con dentro pazienti, note e utenti;
- il file `.env` non viene riscritto, quindi chi è collegato non viene buttato
  fuori (dentro c'è la chiave con cui sono firmate le sessioni);
- la pagina che chiede il primo amministratore **viene saltata**: il setup si
  accorge che il database c'è già e non rifà domande a cui il programma sa
  già rispondere;
- `flask db upgrade` porta il database all'ultima versione, se nel frattempo
  sono cambiate le tabelle.

## Come si ricostruisce il setup

Il `.exe` contiene una **copia** dei file del programma. Dopo ogni modifica
al codice va quindi ricompilato, altrimenti continua a installare la
versione vecchia:

```powershell
powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1
```

Serve [Inno Setup 6](https://jrsoftware.org/isdl.php); se manca, `Compila.ps1`
propone di installarlo con winget.

Per marcare una copia di prova senza toccare il file versionato:

```powershell
powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1 -Versione 2.1
```

## I file

```
Installer\
  CruscottoDegenze.iss      descrizione del setup (Inno Setup)
  Compila.ps1               costruisce il .exe
  LEGGIMI.md                questo file
  Output\
    CruscottoDegenze-Setup.exe
  risorse\
    PreparaImmagini.ps1     ricava icona e banner dal logo della struttura
    cruscotto.ico           icona del setup e dei collegamenti
    wizard-grande.bmp       banner laterale della procedura guidata
    wizard-piccolo.bmp      logo delle pagine intermedie
  script\                   finiscono in «installazione» dentro il programma
    Configura.ps1           Python, librerie, .env, database, amministratore
    crea_admin_auto.py      crea l'amministratore senza fare domande
    server.py               avvia Waitress
    Avvia.ps1               accende il programma e apre il browser
    ApriBrowser.ps1         aspetta che il server risponda, poi apre la pagina
    Avvia.cmd               il file a cui puntano i collegamenti
```

`risorse\PreparaImmagini.ps1` va rilanciato solo se cambia il logo in
`app\static\img`: i file che produce sono versionati insieme al resto.

## Se l'installazione si interrompe

Il setup divide il lavoro in due proprio per questo: la copia dei file (che
non fallisce quasi mai) e la configurazione (che dipende da internet). Se si
rompe la seconda, i file sono già al loro posto e **non serve reinstallare**.
Apri la cartella del programma e rilancia solo quel pezzo:

```powershell
powershell -ExecutionPolicy Bypass -File installazione\Configura.ps1
```

Lo script è fatto per essere rieseguito quante volte si vuole: salta i passi
già fatti, non ricrea il `.env` (dentro c'è la chiave delle sessioni già
aperte) e non tocca l'amministratore se ce n'è già uno.

Casi frequenti:

| Sintomo | Causa | Rimedio |
|---|---|---|
| Si ferma sulle librerie | Niente internet | Collega e rilancia `Configura.ps1` |
| «Il Cruscotto è acceso» | Server in funzione | Chiudi la finestra nera e riprova |
| Il browser non si apre | Server partito più lento del solito | Vai a mano su <http://127.0.0.1:8000> |
| Non ricordi la password | — | `.venv\Scripts\flask.exe crea-admin` per un secondo account |

## Differenze rispetto alla macchina virtuale

Questa installazione è la **Fase 1** del progetto, quella locale:

- database **SQLite** in un file, non SQL Server;
- configurazione `sviluppo`, non `produzione`. La configurazione di
  produzione pretende che il cookie di sessione viaggi solo su HTTPS, cosa
  giusta dietro IIS ma che qui, su `http://127.0.0.1`, impedirebbe
  l'accesso;
- Waitress in primo piano in una finestra, non un servizio dietro IIS.

L'installazione sulla macchina virtuale resta una cosa a parte: là il
database è SQL Server, il `.env` lo scrive l'IT e l'amministratore si crea
con una password vera.
