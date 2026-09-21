# Cruscotto Degenze

Applicazione web interna della **Casa di Cura Misericordia Navacchio** per
seguire i pazienti ricoverati nei tre reparti (AOUP, Setting 1 — Low Care 1,
Setting 2 — Low Care 2).

Il Cruscotto **non è una cartella clinica**: i dati clinici restano in
ResMedica. Qui si registrano solo i dati minimi necessari a organizzare la
degenza e la dimissione.

- Specifica completa: [`PromptIA/Prompt_Cruscotto_Degenze.pdf`](PromptIA/Prompt_Cruscotto_Degenze.pdf)
- Riferimento grafico: [`PromptIA/PrototipoCruscotto_Degenze_v5.html`](PromptIA/PrototipoCruscotto_Degenze_v5.html)

## Stato di avanzamento

| Passo | Cosa | Stato |
|------:|------|-------|
| 1 | Impalcatura, ambiente virtuale, configurazione | ✅ fatto |
| 2 | Database: modelli, migrazione, `crea-admin`, `dati-demo` | ✅ fatto |
| 3 | Accesso: login, logout, cambio password, blocco | ✅ fatto |
| 4 | Home "Pazienti ricoverati" | ✅ fatto |
| 5 | Agenda delle note | ✅ fatto |
| 6 | Checklist di dimissione | ✅ fatto |
| 7 | PDF del paziente | ✅ fatto |
| 8 | Gestione utenti | ✅ fatto |
| 8b | Registro accessi (consultazione) | da fare |
| 9 | Test automatici e rifinitura grafica | da fare |

Gli eventi del registro accessi vengono **già scritti** da ogni operazione
(vedi [`app/audit.py`](app/audit.py)): manca solo la pagina per consultarli.

## Installazione (Windows)

### Con l'installer, se il PC deve solo usare il programma

`Installer\Output\CruscottoDegenze-Setup.exe` installa tutto con un doppio
clic: Python compreso, se non c'è. Chiede dove installare e i dati del primo
amministratore, poi lascia un collegamento sul Desktop che accende il
Cruscotto e apre il browser. Serve la connessione a internet solo durante
l'installazione.

Dettagli, ricompilazione del setup e cosa fare se si interrompe:
[`Installer/LEGGIMI.md`](Installer/LEGGIMI.md).

### A mano, per sviluppare

Richiede **Python 3.12** e **Git**. Dalla cartella del progetto:

```powershell
# 1. Crea l'ambiente virtuale (una volta sola)
py -m venv .venv

# 2. Attivalo (a ogni nuova finestra del terminale)
.\.venv\Scripts\Activate.ps1

# 3. Installa le librerie
pip install -r requirements.txt

# 4. Crea il file di configurazione e mettici una chiave casuale
copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Se PowerShell rifiuta di eseguire `Activate.ps1`, sbloccalo una volta sola con:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## Avvio

```powershell
# Sviluppo: si riavvia da solo a ogni modifica del codice
flask run

# Prove con gli utenti: stesso server della produzione
waitress-serve --listen=127.0.0.1:8000 wsgi:app
```

Poi apri <http://127.0.0.1:5000> (oppure la porta 8000 con Waitress).

## Comandi utili

```powershell
pytest                        # esegue i test automatici
pytest -v                     # come sopra, ma elenca ogni test
python docs/genera_diario.py  # rigenera il PDF del diario di sviluppo
python docs/genera_guida.py   # rigenera la guida tecnica (docs/Guida_Tecnica_...pdf)
python docs/prepara_logo.py   # ricava i loghi web da PromptIA/LOGO CASA verticale.jpg

flask db upgrade              # porta il database all'ultima versione
flask db migrate -m "..."     # scrive una nuova migrazione dopo aver
                              # modificato i modelli (poi rileggila!)
flask crea-admin              # crea il primo amministratore
flask dati-demo               # carica i dati di prova (solo in sviluppo)
flask dati-demo --azzera      # come sopra, ma riparte da zero
flask controlla-dati-fissi    # verifica reparti e voci della checklist
```

## Primo avvio del database

```powershell
flask db upgrade
flask crea-admin       # chiede nome, cognome, nome utente e password
flask dati-demo        # facoltativo: sei pazienti e sette note di esempio
```

### Credenziali locali

| Nome utente | Password | Ruolo |
|---|---|---|
| `administrator` | `administrator` | Amministratore |
| `mrossi` | `prova2026` | Medico |
| `cbianchi` | `prova2026` | Infermiere |
| `gverdi` | `prova2026` | OSS |
| `ufficioit` | `prova2026` | Amministrazione / IT |

Valgono **solo per le prove in locale**. Sulla macchina virtuale l'amministratore
va creato con una password vera e gli utenti di prova non vanno caricati.

## Diario di sviluppo

[`docs/Diario_Cruscotto_Degenze.pdf`](docs/Diario_Cruscotto_Degenze.pdf) racconta
passo per passo cosa è stato fatto e perché, con la spiegazione dei concetti
nuovi via via incontrati. Il testo sta in `docs/contenuto_diario.py`,
l'impaginazione in `docs/genera_diario.py`: si aggiorna il primo e si rilancia
il comando qui sopra.

## Struttura

```
app/
  __init__.py     create_app(): costruisce l'applicazione
  config.py       configurazioni Sviluppo / Test / Produzione
  estensioni.py   db, migrate, login_manager, csrf
  templates/      pagine HTML (Jinja2)
  static/         CSS, JavaScript, font
tests/            test automatici
Installer/        costruzione del setup .exe per Windows
PromptIA/         specifica e prototipo di riferimento
.env              configurazione locale — NON va su Git
.env.example      modello del .env, senza valori
wsgi.py           punto di ingresso per Waitress
```

## Note

- Il programma funziona **senza connessione a internet**: nessuna risorsa
  viene caricata da CDN o servizi esterni.
- Il file `.env` contiene la chiave di firma delle sessioni e non deve mai
  finire su Git: è escluso da `.gitignore`.
