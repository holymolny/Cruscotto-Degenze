"""Contenuto del diario di sviluppo.

Questo file contiene SOLO il testo. La parte che disegna il PDF sta in
genera_diario.py: tenere separati contenuto e impaginazione vuol dire che per
aggiungere il passo 2 basta scrivere qui, senza toccare una riga di grafica.

Formato: una lista di coppie (tipo, contenuto). I tipi riconosciuti sono
elencati in genera_diario.py, nella funzione costruisci_storia().

Nei paragrafi si può usare <b>grassetto</b> e <i>corsivo</i>.
Attenzione: il carattere & va scritto &amp;, perché ReportLab legge i
paragrafi come se fossero HTML.
"""

# Compare in copertina e nel piè di pagina.
VERSIONE = "1.5"
SOTTOTITOLO = "Diario di sviluppo"

CONTENUTO = [
    # ------------------------------------------------------------------
    ("titolo1", "A cosa serve questo documento"),
    (
        "paragrafo",
        "Questo diario racconta come è stato costruito il <b>Cruscotto Degenze</b>, "
        "passo per passo. Non è la specifica del progetto — quella è il documento "
        "<i>Prompt_Cruscotto_Degenze.pdf</i> — ma il resoconto di cosa è stato fatto "
        "davvero, perché è stato fatto così, e quali concetti nuovi sono comparsi "
        "lungo la strada.",
    ),
    (
        "paragrafo",
        "Viene rigenerato a ogni passo completato. La data in copertina dice a quale "
        "momento corrisponde la versione che stai leggendo.",
    ),
    (
        "riquadro",
        (
            "Come si rigenera",
            "Dal terminale, nella cartella del progetto, con l'ambiente virtuale attivo:\n"
            "python docs/genera_diario.py",
        ),
    ),

    # ------------------------------------------------------------------
    ("titolo1", "Il progetto in breve"),
    (
        "paragrafo",
        "Il Cruscotto Degenze è un'applicazione web interna della Casa di Cura "
        "Misericordia Navacchio, raggiungibile solo dalla rete aziendale. Serve a "
        "vedere i pazienti ricoverati nei tre reparti ordinati per data presunta di "
        "dimissione, tenere per ognuno un'Agenda di note organizzative, seguire una "
        "checklist di dimissione di 20 voci e stampare un foglio riepilogativo.",
    ),
    (
        "paragrafo",
        "<b>Non è una cartella clinica.</b> I dati clinici restano in ResMedica. Qui "
        "si registrano solo i dati minimi necessari a organizzare la degenza: nome, "
        "cognome, posto letto, date, gravità e note organizzative.",
    ),
    (
        "tabella",
        {
            "intestazioni": ["", ""],
            "righe": [
                ["Linguaggio", "Python 3.12"],
                ["Applicazione web", "Flask 3 con Flask-SQLAlchemy, Flask-Login, Flask-WTF"],
                ["Database — Fase 1", "SQLite, in un file sul PC"],
                ["Database — Fase 2", "Microsoft SQL Server sull'istanza sql-misnav"],
                ["PDF", "ReportLab, generato dal server"],
                ["Server di produzione", "Waitress, dietro IIS come reverse proxy HTTPS"],
                ["Indirizzo finale", "https://degenze.cdcmisnav.local"],
            ],
            "larghezze": [140, 330],
            "intestazione_visibile": False,
        },
    ),

    # ------------------------------------------------------------------
    ("titolo1", "Stato di avanzamento"),
    (
        "tabella",
        {
            "intestazioni": ["Passo", "Contenuto", "Stato"],
            "righe": [
                ["1", "Impalcatura, ambiente virtuale, configurazione", "FATTO"],
                ["2", "Database: modelli, migrazione, crea-admin", "FATTO"],
                ["3", "Accesso: login, logout, cambio password, blocco", "FATTO"],
                ["4", "Home «Pazienti ricoverati»", "FATTO"],
                ["5", "Agenda delle note", "FATTO"],
                ["6", "Checklist di dimissione", "FATTO"],
                ["7", "PDF del paziente", "FATTO"],
                ["8", "Gestione utenti e registro accessi", "da fare"],
                ["9", "Test automatici e rifinitura grafica", "da fare"],
            ],
            "larghezze": [45, 320, 105],
        },
    ),

    # ------------------------------------------------------------------
    ("titolo1", "Decisioni prese"),
    (
        "paragrafo",
        "Le scelte concordate che si discostano dalla specifica iniziale, o che la "
        "specifica lasciava aperte. Sono annotate qui perché fra sei mesi nessuno si "
        "ricorderà il perché.",
    ),
    (
        "tabella",
        {
            "intestazioni": ["Argomento", "Decisione"],
            "righe": [
                [
                    "Chi dimette un paziente",
                    "ADMIN, MEDICO e INFERMIERE. La specifica diceva solo ADMIN: "
                    "cambiato perché in reparto l'infermiere deve poter liberare il "
                    "letto senza chiamare l'IT.",
                ],
                [
                    "Messaggio di conferma",
                    "«Sei sicuro di voler eliminare il paziente? Una volta eliminato "
                    "non sarà più possibile recuperare i dati. Ricordati di stampare "
                    "il foglio paziente prima.»",
                ],
                [
                    "Cancellazione dei dati",
                    "Per l'utente il paziente sparisce e non c'è modo di riportarlo "
                    "indietro. Nel database la riga resta: le note devono poter "
                    "risalire a chi le ha scritte, e l'amministratore di sistema può "
                    "recuperare un'eliminazione sbagliata.",
                ],
                [
                    "Utenti iniziali",
                    "Un solo account creato da terminale: administrator. Tutti gli "
                    "altri vengono creati dalla pagina Gestione utenti.",
                ],
                [
                    "Utenti di prova",
                    "Il comando flask dati-demo aggiunge quattro utenti finti, uno "
                    "per ruolo. Servono perché le note di esempio devono risultare "
                    "firmate da un medico e da un infermiere. È un comando "
                    "facoltativo e funziona solo in sviluppo.",
                ],
                [
                    "Password del primo admin",
                    "administrator non è obbligato a cambiare la password al primo "
                    "accesso: se l'ha scelta lui stesso da terminale, il cambio "
                    "forzato non protegge da nulla. L'obbligo resta per tutti gli "
                    "account creati da qualcun altro.",
                ],
                [
                    "Logout automatico",
                    "Dopo 15 minuti di inattività, controllato dal server. Nessun "
                    "avviso in anticipo.",
                ],
                [
                    "Cambio di reparto",
                    "Realizzato al passo 4 come proposto: un pulsante «Sposta» che "
                    "chiede reparto e nuovo letto, con lo stesso controllo di letto "
                    "occupato dell'inserimento. Note, checklist e date restano "
                    "attaccate al paziente.",
                ],
                [
                    "Nome utente",
                    "Salvato sempre in minuscolo. SQLite e SQL Server trattano le "
                    "maiuscole in modo diverso: normalizzando si ottiene lo stesso "
                    "risultato su entrambi.",
                ],
            ],
            "larghezze": [120, 350],
        },
    ),

    ("pagina_nuova", None),

    # ==================================================================
    ("titolo1", "Passo 1 — L'impalcatura"),
    (
        "paragrafo",
        "Obiettivo del passo: avere un'applicazione Flask che parte, risponde a una "
        "pagina e ha già al posto giusto tutto ciò che servirà dopo. Nessuna funzione "
        "vera, solo le fondamenta.",
    ),

    ("titolo2", "I file creati"),
    (
        "albero",
        """Cruscotto-Degenze/
  app/
    __init__.py        create_app(): costruisce l'applicazione
    config.py          configurazioni Sviluppo / Test / Produzione
    estensioni.py      db, migrate, login_manager, csrf
    templates/
      base.html        impalcatura HTML comune a tutte le pagine
      prova.html       pagina temporanea del passo 1
    static/css/
      stile.css        i colori del prototipo
  tests/
    conftest.py        attrezzatura comune ai test
    test_impalcatura.py
  .venv/               ambiente virtuale (escluso da Git)
  .env                 configurazione locale con la chiave (esclusa da Git)
  .env.example         il modello vuoto, questo sì su Git
  .gitignore
  requirements.txt     librerie con versione esatta
  wsgi.py              punto di ingresso per Waitress
  README.md
  docs/                questo diario
  PromptIA/            specifica e prototipo di riferimento""",
    ),

    ("titolo2", "I concetti nuovi"),

    ("titolo3", "1. L'ambiente virtuale"),
    (
        "paragrafo",
        "La cartella <b>.venv</b> contiene una copia isolata di Python con soltanto le "
        "librerie di questo progetto. Serve a non farsi male: se domani un altro "
        "programma sullo stesso PC pretende una versione diversa di Flask, il "
        "Cruscotto non se ne accorge nemmeno.",
    ),
    (
        "paragrafo",
        "L'ambiente virtuale <b>non va su Git</b>: si ricrea in un minuto a partire da "
        "requirements.txt, che elenca le librerie con la versione esatta. È così che "
        "sulla macchina virtuale finiranno le stesse identiche versioni che girano "
        "qui, senza sorprese.",
    ),

    ("titolo3", "2. La fabbrica create_app()"),
    (
        "paragrafo",
        "Invece di creare l'applicazione una volta sola come variabile globale, la "
        "costruiamo dentro una funzione: <b>create_app()</b>. Si chiama <i>application "
        "factory</i>, fabbrica di applicazioni, ed è il modo consigliato da Flask.",
    ),
    (
        "paragrafo",
        "Il vantaggio è concreto. I test chiamano create_app(\"test\") e ottengono "
        "un'applicazione con un database in memoria, che nasce e muore con il singolo "
        "test. Il comando flask run chiama create_app(\"sviluppo\") e ottiene quella "
        "con il file SQLite. Sulla macchina virtuale sarà create_app(\"produzione\"), "
        "con SQL Server. <b>Stesso codice, tre applicazioni diverse.</b>",
    ),

    ("titolo3", "3. Le estensioni in un file separato"),
    (
        "paragrafo",
        "In <b>app/estensioni.py</b> gli oggetti db, migrate, login_manager e csrf "
        "nascono vuoti, e vengono collegati all'applicazione più tardi con init_app(). "
        "Sembra un giro inutile, ma evita un problema reale.",
    ),
    (
        "paragrafo",
        "Il futuro models.py avrà bisogno di <b>db</b> per definire le tabelle. Se db "
        "nascesse dentro create_app(), models.py dovrebbe importare l'applicazione per "
        "averlo — ma l'applicazione, a sua volta, importa models.py. I due file si "
        "aspetterebbero a vicenda e Python si fermerebbe con un errore. Si chiama "
        "<b>import circolare</b>, e questo è il modo standard di evitarlo.",
    ),

    ("titolo3", "4. Il file .env e i segreti"),
    (
        "paragrafo",
        "Il file <b>.env</b> contiene la SECRET_KEY, cioè la chiave con cui vengono "
        "firmati i cookie di sessione. Chi la conosce può fabbricarsi un cookie e "
        "farsi passare per l'amministratore senza sapere nessuna password.",
    ),
    (
        "paragrafo",
        "Per questo il .env è <b>escluso da .gitignore</b> e non finisce mai su Git. Su "
        "Git va soltanto <b>.env.example</b>, che ha i nomi delle variabili e i "
        "commenti, ma nessun valore. Chi installa il programma altrove lo copia, lo "
        "rinomina in .env e ci mette i propri valori.",
    ),
    (
        "riquadro",
        (
            "Da fare prima della produzione",
            "In sviluppo, se la SECRET_KEY manca, il programma usa una chiave di "
            "ripiego per non bloccare il lavoro. In produzione invece si rifiuta di "
            "partire: meglio un errore chiaro all'avvio che scoprire in reparto che "
            "le sessioni sono firmate con una chiave nota.",
        ),
    ),

    ("titolo2", "Le intestazioni di sicurezza"),
    (
        "paragrafo",
        "Ogni risposta del server porta con sé quattro intestazioni HTTP, aggiunte in "
        "un punto solo dentro create_app():",
    ),
    (
        "tabella",
        {
            "intestazioni": ["Intestazione", "A cosa serve"],
            "righe": [
                [
                    "X-Content-Type-Options",
                    "Il browser non deve indovinare il tipo di un file: se diciamo "
                    "che è testo, lo tratta come testo e non come programma.",
                ],
                [
                    "X-Frame-Options",
                    "Nessun altro sito può incorniciare il Cruscotto dentro una "
                    "propria pagina per ingannare l'utente.",
                ],
                [
                    "Referrer-Policy",
                    "L'indirizzo delle pagine interne non viene comunicato a siti "
                    "esterni.",
                ],
                [
                    "Content-Security-Policy",
                    "Consente solo risorse servite da questo stesso sito. Vale anche "
                    "come rete di protezione: se per distrazione qualcuno aggiungesse "
                    "un riferimento a una CDN, smetterebbe di funzionare subito qui, "
                    "invece che in reparto dove non c'è internet.",
                ],
            ],
            "larghezze": [150, 320],
        },
    ),

    ("titolo2", "Un imprevisto e come è stato risolto"),
    (
        "paragrafo",
        "Al primo giro dei test, Flask-Login si è fermato con l'errore <i>Missing "
        "user_loader</i>. Il motivo: appena viene attivato, Flask-Login pretende una "
        "funzione che sappia ricaricare l'utente dalla sessione a ogni richiesta — e "
        "quella funzione ha bisogno del modello Utente, che nascerà al passo 2.",
    ),
    (
        "paragrafo",
        "Soluzione: login_manager resta dichiarato in estensioni.py, ma viene "
        "collegato all'applicazione al passo 3, quando avrà di che lavorare. In "
        "app/__init__.py c'è un commento che lo spiega, così fra un mese il motivo è "
        "ancora lì.",
    ),

    ("titolo2", "Come si verifica che funzioni"),
    (
        "codice",
        ".\\.venv\\Scripts\\Activate.ps1\n"
        "flask run",
    ),
    (
        "paragrafo",
        "Poi si apre <b>http://127.0.0.1:5000</b>: deve comparire un riquadro bianco su "
        "sfondo grigio chiaro con scritto «Il Cruscotto funziona» nel verde del "
        "prototipo. Per fermare il server: Ctrl+C.",
    ),
    (
        "paragrafo",
        "Se PowerShell rifiuta di eseguire Activate.ps1, va sbloccato una volta sola "
        "con: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned",
    ),
    ("paragrafo", "I test automatici si lanciano con:"),
    ("codice", "pytest -v"),
    (
        "paragrafo",
        "Al passo 1 sono due: uno controlla che la pagina risponda con il testo "
        "giusto, l'altro che le quattro intestazioni di sicurezza ci siano davvero. "
        "Il secondo sembra eccessivo adesso, ma serve fra sei mesi: se qualcuno le "
        "togliesse per sbaglio, il test lo direbbe subito.",
    ),

    ("titolo2", "Esito"),
    (
        "elenco",
        [
            "pytest: 2 test su 2 passati.",
            "La pagina risponde con codice 200 e contiene il testo atteso.",
            "Il foglio di stile viene servito correttamente.",
            "git status non vede né .env né .venv: i segreti restano fuori dal "
            "controllo versione.",
        ],
    ),

    ("pagina_nuova", None),

    # ==================================================================
    ("titolo1", "Passo 2 — Il database"),
    (
        "paragrafo",
        "Obiettivo del passo: le otto tabelle esistono davvero, contengono già i dati "
        "che non cambiano mai (i tre reparti e le 20 voci della checklist), e c'è un "
        "amministratore con cui poter entrare al passo 3.",
    ),

    ("titolo2", "I file creati"),
    (
        "albero",
        """app/
  models.py          le otto tabelle, descritte come classi Python
  dati_fissi.py      i tre reparti e le 20 voci della checklist
  comandi.py         flask crea-admin, flask dati-demo
  formati.py         conversioni fra UTC e ora italiana
migrations/
  versions/          la prima migrazione, generata e poi completata a mano
tests/
  test_modelli.py    20 test sulle regole del database""",
    ),

    ("titolo2", "Le otto tabelle"),
    (
        "tabella",
        {
            "intestazioni": ["Tabella", "Cosa contiene"],
            "righe": [
                ["reparto", "I tre reparti. Tabella fissa, tre righe."],
                [
                    "utente",
                    "Chi usa il programma. Gli utenti non si cancellano mai: per "
                    "togliere l'accesso si usa attivo = falso.",
                ],
                [
                    "paziente",
                    "Nome, cognome, letto, date, gravità, stato. Nessun dato "
                    "clinico.",
                ],
                [
                    "nota",
                    "Le note dell'Agenda, con la firma dell'autore copiata dentro.",
                ],
                [
                    "nota_versione",
                    "Il testo precedente di una nota modificata.",
                ],
                ["voce_checklist", "Le 20 voci, con codice fisso."],
                [
                    "checklist_spunta",
                    "Una riga per ogni voce spuntata di ogni paziente.",
                ],
                [
                    "evento_audit",
                    "Il registro accessi. Ci si scrive soltanto, non si modifica "
                    "e non si cancella.",
                ],
            ],
            "larghezze": [110, 360],
        },
    ),

    ("titolo2", "I concetti nuovi"),

    ("titolo3", "1. Il modello e l'ORM"),
    (
        "paragrafo",
        "Un <b>modello</b> è una classe Python che rappresenta una tabella: ogni "
        "attributo è una colonna, ogni oggetto della classe è una riga. Lo strumento "
        "che fa da traduttore si chiama <b>ORM</b> — <i>Object-Relational Mapper</i> — "
        "e nel nostro caso è SQLAlchemy.",
    ),
    (
        "paragrafo",
        "Concretamente: scriviamo paziente.cognome = \"Rossi\" seguito da "
        "db.session.commit(), e SQLAlchemy genera l'istruzione SQL UPDATE "
        "corrispondente. Il guadagno non è solo la comodità. È che <b>lo stesso "
        "codice funziona su SQLite e su SQL Server</b>: le differenze fra i due le "
        "conosce lui. Ed è impossibile sbagliare in modo pericoloso, perché non "
        "costruiamo mai un'istruzione SQL incollando pezzi di testo — il modo in cui "
        "nascono le vulnerabilità chiamate SQL injection.",
    ),
    (
        "riquadro",
        (
            "Un dettaglio che conta: Unicode invece di String",
            "Nei modelli usiamo db.Unicode e db.UnicodeText invece di db.String e "
            "db.Text. Su SQLite è identico, ma su SQL Server significa colonne "
            "NVARCHAR invece di VARCHAR — cioè lettere accentate salvate come si "
            "deve. In una colonna VARCHAR «Continuità» diventerebbe «Continuit?». "
            "C'è un test apposta che lo controlla.",
        ),
    ),

    ("titolo3", "2. La migrazione"),
    (
        "paragrafo",
        "Una <b>migrazione</b> è un file che descrive una modifica alla struttura del "
        "database: crea questa tabella, aggiungi quella colonna. Si conserva insieme "
        "al codice, e i file si applicano in ordine.",
    ),
    (
        "paragrafo",
        "Perché non creare le tabelle a mano? Perché i database saranno almeno tre: "
        "quello sul PC di sviluppo, quello della VM di prova, quello di produzione. "
        "Se ognuno venisse costruito a mano, prima o poi sarebbero diversi, e un "
        "programma che funziona qui darebbe errore in reparto. Con le migrazioni la "
        "struttura del database <b>è</b> il codice: si aggiorna con un comando e non "
        "si discute.",
    ),
    (
        "paragrafo",
        "Lo strumento è Alembic, che Flask-Migrate rende comodo. Il comando flask db "
        "migrate confronta i modelli con il database e <b>scrive lui</b> il file. Ha "
        "riconosciuto da solo le otto tabelle, i due indici sul paziente e il vincolo "
        "sulle date. Ma va sempre riletto prima di applicarlo: è un'ottima bozza, non "
        "un oracolo.",
    ),
    (
        "paragrafo",
        "Alla migrazione generata abbiamo aggiunto a mano l'inserimento dei dati "
        "fissi. La specifica lo chiede, e il motivo è pratico: se fossero un comando "
        "a parte, prima o poi qualcuno installerebbe il programma dimenticandosi di "
        "lanciarlo, e si ritroverebbe un cruscotto senza reparti.",
    ),

    ("titolo3", "3. L'hash della password"),
    (
        "paragrafo",
        "Nel database non c'è nessuna password. C'è la sua <b>impronta</b>, in inglese "
        "<i>hash</i>: il risultato di un calcolo che trasforma la password in una "
        "stringa illeggibile e <b>da cui non si può tornare indietro</b>. L'algoritmo "
        "si chiama scrypt.",
    ),
    (
        "paragrafo",
        "Quando qualcuno accede, rifacciamo lo stesso calcolo sulla password digitata "
        "e confrontiamo le due impronte. Se coincidono, la password era giusta. "
        "Nemmeno noi, che abbiamo il database in mano, possiamo sapere qual è la "
        "password di un utente: si può solo reimpostarla.",
    ),
    (
        "paragrafo",
        "C'è un secondo accorgimento, il <b>sale</b>: a ogni password viene aggiunto "
        "un pezzetto casuale prima del calcolo. Per questo due utenti con la stessa "
        "identica password hanno impronte diverse. Senza il sale, chi rubasse il "
        "database vedrebbe a colpo d'occhio quali account condividono la password, e "
        "una sola indovinata ne aprirebbe parecchi.",
    ),
    (
        "codice",
        "administrator -> scrypt:32768:8:1$4n810EGBDjtn0REm$1631b3...\n"
        "                 |      |         |               |\n"
        "                 |      parametri sale            impronta vera\n"
        "                 algoritmo",
    ),

    ("titolo3", "4. L'indice parziale sul letto"),
    (
        "paragrafo",
        "Due pazienti non possono stare nello stesso letto: lo garantisce un indice "
        "univoco su reparto e posto letto. Ma se valesse per tutte le righe, un letto "
        "usato da un paziente dimesso sei mesi fa resterebbe bloccato per sempre.",
    ),
    (
        "paragrafo",
        "La soluzione è un <b>indice parziale</b>: l'unicità vale solo dove lo stato è "
        "RICOVERATO. Gli eliminati non contano, e il letto torna libero. SQLite e SQL "
        "Server lo supportano entrambi, con sintassi diverse, e SQLAlchemy sceglie "
        "quella giusta a seconda del database.",
    ),
    (
        "paragrafo",
        "Accanto c'è un <b>vincolo CHECK</b> che impedisce una dimissione precedente "
        "all'arrivo. Il controllo lo farà anche l'applicazione, con un messaggio "
        "gentile in italiano; ma averlo anche nel database significa che nessun bug "
        "futuro potrà aggirarlo. Le regole importanti vanno scritte due volte.",
    ),

    ("titolo3", "5. La firma fotografata nella nota"),
    (
        "paragrafo",
        "La tabella nota ha tre colonne che sembrano un doppione: autore_id, "
        "autore_nome e autore_ruolo. Perché salvare nome e ruolo, se dall'id si "
        "risalirebbe all'utente?",
    ),
    (
        "paragrafo",
        "Perché una firma deve raccontare com'erano le cose <b>quel giorno</b>. Se "
        "Carlo Bianchi passasse da infermiere a medico, le note che ha scritto da "
        "infermiere devono restare firmate «Infermiere: Carlo Bianchi». Con il solo "
        "id, cambiando il suo ruolo cambierebbero retroattivamente anche tutte le sue "
        "note vecchie.",
    ),

    ("titolo3", "6. UTC nel database, ora italiana a schermo"),
    (
        "paragrafo",
        "Tutti gli orari si salvano in UTC e si convertono in ora italiana solo al "
        "momento di mostrarli. Il motivo è l'ora legale: nella notte in cui le "
        "lancette tornano indietro, le 02:30 italiane esistono <b>due volte</b>. Se "
        "salvassimo l'ora locale, due note scritte a un'ora di distanza risulterebbero "
        "scritte nello stesso istante e non ci sarebbe modo di sapere quale è venuta "
        "prima. In UTC il tempo scorre sempre dritto.",
    ),
    (
        "paragrafo",
        "Fa eccezione data_nota, che è la data <i>italiana</i> del giorno in cui la "
        "nota è stata scritta: una nota battuta all'una di notte del 17 deve comparire "
        "sotto il 17, non sotto il 16.",
    ),

    ("titolo2", "I comandi nuovi"),
    (
        "tabella",
        {
            "intestazioni": ["Comando", "Cosa fa"],
            "righe": [
                [
                    "flask db upgrade",
                    "Porta il database all'ultima versione applicando le migrazioni "
                    "che mancano. È il comando che si lancia dopo ogni aggiornamento.",
                ],
                [
                    "flask db migrate -m \"...\"",
                    "Confronta i modelli con il database e scrive una nuova "
                    "migrazione. Va sempre riletta prima di applicarla.",
                ],
                [
                    "flask crea-admin",
                    "Crea il primo amministratore. Si lancia una volta sola, "
                    "subito dopo l'installazione.",
                ],
                [
                    "flask dati-demo",
                    "Carica sei pazienti, sette note e quattro utenti di prova. "
                    "Solo in sviluppo. Con --azzera riparte da zero.",
                ],
                [
                    "flask controlla-dati-fissi",
                    "Verifica che i tre reparti e le 20 voci ci siano. Utile dopo "
                    "un aggiornamento sulla macchina virtuale.",
                ],
            ],
            "larghezze": [150, 320],
        },
    ),

    ("titolo2", "Un imprevisto e come è stato risolto"),
    (
        "paragrafo",
        "Il comando flask dati-demo si rifiutava di partire dicendo di essere in "
        "produzione, pur girando in sviluppo. Il controllo leggeva la variabile DEBUG "
        "— che la configurazione imposta a vero.",
    ),
    (
        "paragrafo",
        "Causa: il comando flask, mentre carica l'applicazione, <b>riscrive DEBUG a "
        "falso</b> se non trova la variabile d'ambiente FLASK_DEBUG. Quindi DEBUG vale "
        "vero quando l'applicazione viene avviata normalmente, ma falso dentro i "
        "comandi da terminale: non è un indicatore affidabile di dove stiamo girando.",
    ),
    (
        "paragrafo",
        "Soluzione: una variabile nostra, <b>AMBIENTE</b>, che vale «sviluppo», «test» "
        "o «produzione» e che nessuno tocca alle nostre spalle. Lezione generale: "
        "quando una decisione importante dipende da un valore, conviene che quel "
        "valore sia nostro.",
    ),

    ("titolo2", "I test"),
    (
        "paragrafo",
        "Da 2 test siamo passati a <b>22</b>. Non provano Python: provano le regole che "
        "abbiamo chiesto al database di far rispettare. I più significativi:",
    ),
    (
        "elenco",
        [
            "la password non compare mai in chiaro nell'impronta salvata;",
            "due utenti con la stessa password hanno impronte diverse (il sale);",
            "un letto occupato non si può riassegnare;",
            "lo stesso numero di letto in due reparti diversi è ammesso;",
            "il letto di un paziente eliminato torna libero;",
            "una dimissione precedente all'arrivo viene rifiutata;",
            "una dimissione nello stesso giorno dell'arrivo è ammessa;",
            "«Continuità» e «Setting 1 — Low Care 1» tornano dal database intatti.",
        ],
    ),
    (
        "paragrafo",
        "I test girano su un database <b>in memoria</b>, che nasce e muore con il "
        "singolo test: non possono sporcarsi a vicenda e non toccano mai il "
        "cruscotto.db vero.",
    ),

    ("titolo2", "Come si verifica che funzioni"),
    (
        "codice",
        "flask controlla-dati-fissi\n"
        "pytest -v",
    ),
    (
        "paragrafo",
        "Il primo comando deve rispondere «Dati fissi completi», il secondo deve dare "
        "22 test passati.",
    ),

    ("titolo2", "Esito"),
    (
        "elenco",
        [
            "Otto tabelle create, con due indici e un vincolo CHECK sul paziente.",
            "Tre reparti e 20 voci della checklist inseriti dalla migrazione.",
            "Amministratore administrator creato, che entra con la sua password.",
            "Dati di prova caricati: 6 pazienti, 7 note, 7 spunte, 4 utenti finti.",
            "pytest: 22 test su 22 passati.",
        ],
    ),

    ("pagina_nuova", None),

    # ==================================================================
    ("titolo1", "Passo 3 — L'accesso"),
    (
        "paragrafo",
        "Obiettivo del passo: entrare davvero nel Cruscotto. Pagina di accesso con "
        "l'aspetto del prototipo, uscita, cambio password obbligatorio, blocco dopo "
        "cinque tentativi falliti, disconnessione per inattività e pagina «Il mio "
        "profilo».",
    ),

    ("titolo2", "I file creati"),
    (
        "albero",
        """app/
  permessi.py        chi può fare cosa: la matrice dei ruoli
  audit.py           registra_evento(): il registro accessi
  sessione.py        scadenza per inattività e obbligo cambio password
  auth/
    __init__.py      il blueprint dell'area accesso
    form.py          i form, con il token CSRF
    servizi.py       le regole: tentativi, blocco, requisiti password
    routes.py        le pagine: accedi, esci, cambia-password, profilo
  pazienti/
    __init__.py      blueprint dell'area pazienti
    routes.py        home segnaposto (diventa vera al passo 4)
  templates/
    base.html        impalcatura minima
    base_app.html    impalcatura con la barra laterale
    _messaggi.html   i messaggi temporanei
    auth/            login, cambio password, profilo
    pazienti/        home
    errori/          403, 404, 500 in italiano
  static/css/
    stile.css        il CSS completo del prototipo
tests/
  test_accesso.py    36 test sull'accesso e sui permessi""",
    ),

    ("titolo2", "I concetti nuovi"),

    ("titolo3", "1. Il blueprint"),
    (
        "paragrafo",
        "Un <b>blueprint</b> è un pezzo di applicazione con le sue pagine, che poi "
        "viene innestato nell'applicazione vera. Serve a non ritrovarsi, fra sei mesi, "
        "con un unico file da duemila righe in cui la funzione del login sta accanto a "
        "quella che genera il PDF.",
    ),
    (
        "paragrafo",
        "Il Cruscotto ne avrà cinque: auth, pazienti, agenda, pdf, utenti. I primi due "
        "esistono già. Dentro ogni blueprint la divisione si ripete: <b>routes.py</b> "
        "si occupa delle pagine, <b>servizi.py</b> delle regole. La regola «dopo 5 "
        "tentativi falliti l'account si blocca» non ha niente a che vedere con l'HTTP, "
        "e infatti i test che la verificano non aprono nessuna pagina.",
    ),

    ("titolo3", "2. La sessione"),
    (
        "paragrafo",
        "Come fa il server a ricordarsi chi sei fra una pagina e l'altra? Con un "
        "<b>cookie di sessione</b>: un pezzetto di dati che il browser riporta indietro "
        "a ogni richiesta. Dentro c'è soltanto l'id dell'utente, non l'utente intero.",
    ),
    (
        "paragrafo",
        "Il cookie è <b>firmato</b> con la SECRET_KEY. Non è cifrato — chi lo apre vede "
        "che contiene l'id 3 — ma non può cambiarlo in 1 per diventare amministratore: "
        "la firma non tornerebbe. Ecco perché la SECRET_KEY è il segreto più importante "
        "del programma, e perché cambiarla costringe tutti a rifare l'accesso.",
    ),
    (
        "paragrafo",
        "Il cookie ha tre protezioni: <b>HttpOnly</b> lo rende invisibile al JavaScript "
        "della pagina, così uno script malevolo non può rubarlo; <b>SameSite=Lax</b> "
        "impedisce che venga allegato a richieste partite da altri siti; <b>Secure</b>, "
        "attivo solo in produzione, vieta di farlo viaggiare senza HTTPS.",
    ),

    ("titolo3", "3. Il token CSRF"),
    (
        "paragrafo",
        "Un esempio concreto. Sei collegato al Cruscotto. Apri in un'altra scheda una "
        "pagina qualsiasi, che di nascosto invia al Cruscotto la richiesta «elimina il "
        "paziente 12». Il tuo browser allega da solo il cookie di sessione, e per il "
        "server la richiesta sembra tua.",
    ),
    (
        "paragrafo",
        "Il <b>token CSRF</b> impedisce questo: ogni form contiene un valore casuale "
        "che il server ha generato per quella sessione, e le richieste che non lo "
        "riportano vengono rifiutate con un errore 400. La pagina esterna quel valore "
        "non può conoscerlo, perché non può leggere il contenuto delle nostre pagine.",
    ),
    (
        "paragrafo",
        "Nei template lo inserisce form.hidden_tag(). È l'unica riga che non va mai "
        "dimenticata quando si scrive un form nuovo: se manca, il form semplicemente "
        "non funziona, il che per fortuna se ne accorge subito.",
    ),

    ("titolo2", "Le regole dell'accesso"),

    ("titolo3", "Il messaggio di errore è sempre lo stesso"),
    (
        "paragrafo",
        "Utente inesistente, password sbagliata, account disattivato, account "
        "bloccato: in tutti e quattro i casi la risposta è «Nome utente o password non "
        "corretti». Se il messaggio cambiasse a seconda del motivo, chi prova nomi a "
        "caso scoprirebbe quali account esistono davvero, che è metà del lavoro.",
    ),
    (
        "riquadro",
        (
            "Un dettaglio meno ovvio: anche il tempo parla",
            "Se il nome utente non esiste, il programma calcola comunque "
            "un'impronta della password e la butta via. Sembra uno spreco, ed è "
            "voluto: senza, la risposta per un utente inesistente arriverebbe molto "
            "più in fretta di quella per uno esistente, e basterebbe cronometrare le "
            "risposte per capire quali nomi sono buoni. Le due strade devono durare "
            "lo stesso.",
        ),
    ),

    ("titolo3", "Il blocco dopo cinque tentativi"),
    (
        "paragrafo",
        "Ogni password sbagliata incrementa un contatore. Al quinto tentativo "
        "l'account resta bloccato per 15 minuti, e in quel periodo <b>rifiuta anche la "
        "password giusta</b>. Il contatore viene azzerato insieme al blocco, così "
        "passati i 15 minuti l'utente ha di nuovo cinque tentativi e non uno solo.",
    ),
    (
        "paragrafo",
        "Un accesso riuscito azzera tutto. Sono cinque tentativi falliti "
        "<i>consecutivi</i>, non cinque in assoluto.",
    ),
    (
        "paragrafo",
        "Poiché il messaggio resta generico, un utente bloccato non capirebbe cosa gli "
        "sta succedendo. Per questo sotto il form c'è una riga fissa che spiega la "
        "regola: «Dopo 5 tentativi falliti l'accesso resta bloccato per 15 minuti». "
        "Informa chi ha diritto di saperlo senza rivelare nulla a nessun altro.",
    ),

    ("titolo3", "Il cambio password obbligatorio"),
    (
        "paragrafo",
        "Chi ha una password temporanea non può aprire nessun'altra pagina: viene "
        "sempre rimandato al cambio password. Il motivo non è formale: la password "
        "temporanea l'ha scelta l'amministratore, quindi finché resta quella "
        "l'amministratore può entrare al posto suo — e le note risulterebbero scritte "
        "dall'utente.",
    ),
    (
        "paragrafo",
        "Fanno eccezione la pagina del cambio password stessa e l'uscita. Senza la "
        "seconda, chi entra con l'account sbagliato resterebbe intrappolato.",
    ),
    (
        "paragrafo",
        "Requisiti della nuova password: almeno 8 caratteri, almeno una lettera e "
        "almeno un numero, diversa da quella attuale. Sono volutamente modesti: in "
        "reparto le password si digitano in fretta, e una regola troppo severa finisce "
        "scritta su un foglietto attaccato al monitor.",
    ),

    ("titolo3", "La disconnessione per inattività"),
    (
        "paragrafo",
        "Dopo 15 minuti senza toccare il programma l'utente viene disconnesso, con il "
        "messaggio «Sessione scaduta per inattività». Il valore sta nel .env.",
    ),
    (
        "paragrafo",
        "Sono 15 minuti di <b>inattività</b>, non di collegamento: ogni richiesta fa "
        "ripartire il conto. Il controllo è scritto in un before_request, cioè una "
        "funzione che Flask esegue prima di ogni richiesta: così vale su tutte le "
        "pagine, comprese quelle che verranno scritte fra sei mesi da chi si sarà "
        "dimenticato di questa regola.",
    ),

    ("titolo2", "La matrice dei permessi"),
    (
        "paragrafo",
        "Tutti i permessi stanno in un unico file, app/permessi.py, come dizionario "
        "ruolo → permessi. Per rispondere a «un OSS può scaricare il PDF?» si guarda "
        "una tabella sola, invece di cercare i controlli sparsi per venti file.",
    ),
    (
        "tabella",
        {
            "intestazioni": ["Azione", "Chi può"],
            "righe": [
                ["Vedere home, Agenda, checklist", "tutti i ruoli"],
                ["Scrivere note", "ADMIN, MEDICO, INFERMIERE"],
                ["Modificare o eliminare una nota", "solo l'autore, nemmeno l'ADMIN"],
                ["Spuntare la checklist", "ADMIN, MEDICO, INFERMIERE"],
                ["Cambiare la gravità", "ADMIN, MEDICO, INFERMIERE"],
                ["Inserire un paziente", "ADMIN, MEDICO, INFERMIERE"],
                ["Modificare la dimissione presunta", "ADMIN, MEDICO, INFERMIERE"],
                ["Dimettere un paziente", "ADMIN, MEDICO, INFERMIERE"],
                ["Spostare un paziente di reparto", "ADMIN, MEDICO, INFERMIERE"],
                ["Scaricare il PDF", "tutti tranne OSS"],
                ["Gestione utenti e registro", "solo ADMIN"],
                ["Cambiare la propria password", "tutti"],
            ],
            "larghezze": [230, 240],
        },
    ),
    (
        "riquadro",
        (
            "La regola che non si negozia",
            "Ogni permesso va verificato sul server. Nascondere un pulsante serve a "
            "non confondere l'utente, non a impedire l'azione: chi conosce "
            "l'indirizzo può sempre provare a chiamarlo a mano scrivendolo nella "
            "barra del browser. Per questo ogni pagina protetta porta il decoratore "
            "@richiede_permesso, che risponde 403 prima ancora di entrare nella "
            "funzione.",
        ),
    ),

    ("titolo2", "Il registro accessi"),
    (
        "paragrafo",
        "Da questo passo il programma scrive nella tabella evento_audit: LOGIN_OK, "
        "LOGIN_FALLITO, LOGOUT, PASSWORD_CAMBIATA. Di ogni evento restano data e ora, "
        "utente, azione e indirizzo IP del PC.",
    ),
    (
        "paragrafo",
        "La funzione registra_evento() <b>non fa il commit</b>: aggiunge soltanto "
        "l'evento alla sessione, e il salvataggio avviene insieme all'operazione che "
        "l'evento descrive. Così, se l'operazione fallisce a metà, non resta nel "
        "registro la traccia di una cosa che non è mai successa.",
    ),
    (
        "paragrafo",
        "Nel registro non finisce mai il testo di una nota, né una password. Serve a "
        "sapere che alle 14:32 Carlo Bianchi ha modificato la nota 87, non a "
        "raccontare una seconda volta cosa c'era scritto. C'è un test che lo "
        "verifica.",
    ),

    ("titolo2", "Le pagine di errore"),
    (
        "paragrafo",
        "403, 404 e 500 hanno ora una pagina in italiano, senza dettagli tecnici. Il "
        "motivo non è solo di garbo: mostrare la struttura interna del programma — "
        "nomi di file, righe di codice, versioni delle librerie — aiuta soltanto chi "
        "volesse attaccarlo. Il messaggio completo finisce nel log del server, dove lo "
        "legge l'IT.",
    ),
    (
        "paragrafo",
        "La pagina 500 fa anche una cosa meno visibile: annulla la sessione del "
        "database. Se l'errore è avvenuto a metà di un salvataggio, restano modifiche "
        "in sospeso che non devono finire salvate per sbaglio alla richiesta "
        "successiva.",
    ),

    ("titolo2", "I test"),
    (
        "paragrafo",
        "Da 22 a <b>61</b>. I nuovi riguardano l'accesso, ed è la parte dove un errore "
        "non si vede a occhio ma fa finire una nota firmata dalla persona sbagliata. "
        "I più significativi:",
    ),
    (
        "elenco",
        [
            "utente inesistente e password sbagliata danno lo stesso messaggio;",
            "un utente disattivato non entra;",
            "cinque tentativi falliti bloccano l'account, quattro no;",
            "l'account bloccato rifiuta anche la password giusta;",
            "scaduto il blocco, l'accesso torna possibile;",
            "chi deve cambiare password non apre altre pagine, ma può uscire;",
            "una password senza numeri, senza lettere o troppo corta viene rifiutata;",
            "la sessione scade dopo i minuti previsti e ogni richiesta fa ripartire "
            "il conto;",
            "nel registro non compare mai la password digitata;",
            "la voce «Gestione utenti» non compare a un infermiere.",
        ],
    ),

    ("titolo2", "Come si verifica che funzioni"),
    ("codice", "flask run"),
    (
        "paragrafo",
        "Si apre http://127.0.0.1:5000 e compare la pagina di accesso con la card "
        "centrata del prototipo. Si entra con <b>administrator</b> / "
        "<b>administrator</b> e si arriva alla home, con nome e ruolo nella barra a "
        "sinistra.",
    ),
    ("paragrafo", "Vale la pena provare anche:"),
    (
        "elenco",
        [
            "una password sbagliata cinque volte di fila, poi quella giusta: "
            "viene rifiutata comunque;",
            "l'accesso come cbianchi / prova2026: la voce «Gestione utenti» sparisce;",
            "scrivere /profilo o /cambia-password nella barra senza essere "
            "collegati: si viene rimandati all'accesso.",
        ],
    ),

    ("titolo2", "Esito"),
    (
        "elenco",
        [
            "Accesso, uscita, cambio password e profilo funzionanti.",
            "Blocco dopo 5 tentativi e scadenza per inattività verificati.",
            "Il form senza token CSRF viene rifiutato con 400.",
            "Registro accessi popolato: LOGIN_OK, LOGIN_FALLITO, LOGOUT, "
            "PASSWORD_CAMBIATA.",
            "pytest: 61 test su 61 passati.",
        ],
    ),

    # ==================================================================
    ("titolo1", "Intermezzo — Il logo della struttura"),
    (
        "paragrafo",
        "Fra il passo 3 e il passo 4 è stato inserito il logo della Casa di Cura: "
        "completo nella pagina di accesso, ridotto al solo stemma nella barra "
        "laterale. Un lavoro da mezz'ora che ha tirato fuori due cose che vale la "
        "pena sapere.",
    ),

    ("titolo2", "Dove è stato messo"),
    (
        "tabella",
        {
            "intestazioni": ["Pagina", "Cosa compare"],
            "righe": [
                [
                    "Accesso",
                    "Marchio completo (stemma e nome), 190 px, centrato sopra il "
                    "titolo. È la pagina d'ingresso: ci sta il marchio per esteso.",
                ],
                [
                    "Barra laterale",
                    "Solo lo stemma, 52 px, sopra la scritta «Cruscotto Degenze». "
                    "La barra è larga 236 px: con il logo completo il titolo sarebbe "
                    "andato a capo.",
                ],
            ],
            "larghezze": [110, 360],
        },
    ),
    (
        "paragrafo",
        "Il nome della struttura non viene scritto due volte: nella pagina di accesso "
        "lo dice il logo, e il sottotitolo è diventato «Accesso riservato al "
        "personale». Nella barra laterale lo stemma ha alt vuoto, perché il nome è "
        "già scritto accanto: un lettore di schermo che leggesse anche l'immagine "
        "ripeterebbe la stessa cosa due volte.",
    ),

    ("titolo2", "Prima sorpresa: il file era per la stampa, non per lo schermo"),
    (
        "paragrafo",
        "Il logo consegnato dalla grafica è un JPG in <b>modo CMYK</b>, con dentro un "
        "profilo colore ISO Coated v2: cioè descritto in inchiostri da tipografia, non "
        "in luce da monitor.",
    ),
    (
        "paragrafo",
        "Aprendolo senza tenerne conto, il ciano del marchio risultava "
        "<b>#00FFFF</b>, un ciano elettrico da schermo. Convertendolo davvero in sRGB "
        "diventa <b>#00A3D4</b>, un azzurro più pieno e più scuro. La seconda è quella "
        "giusta: la prima erano valori di inchiostro letti come se fossero luce.",
    ),
    (
        "riquadro",
        (
            "La differenza pratica",
            "Il colore ingenuo #00FFFF stonava accanto al verde del Cruscotto "
            "(#0E5A55). Quello vero, #00A3D4, ci sta bene. Il colore giusto non è "
            "solo più corretto: era anche più bello, il che capita più spesso di "
            "quanto sembri.",
        ),
    ),

    ("titolo2", "Seconda sorpresa: 1,3 MB per un'immagine da 380 pixel"),
    (
        "paragrafo",
        "Il primo tentativo di ridimensionamento ha prodotto un PNG da 380x291 pixel "
        "che pesava <b>1350 KB</b>. Un'anomalia evidente: quell'immagine, salvata "
        "senza alcuna compressione, occuperebbe 332 KB. Doveva esserci dell'altro "
        "dentro al file.",
    ),
    (
        "paragrafo",
        "C'era: il profilo colore ICC dell'originale, <b>1,8 MB</b>, che Pillow "
        "copiava fedelmente dentro il PNG. Pesava cinque volte l'immagine. Tanto che "
        "Pillow si rifiutava perfino di riaprire il file che aveva appena scritto.",
    ),
    (
        "paragrafo",
        "La soluzione è in due mosse: prima <b>convertire</b> i colori in sRGB usando "
        "il profilo, poi <b>buttarlo via</b>. Cancellarlo e basta avrebbe spostato le "
        "tinte, perché i colori erano espressi secondo quel profilo. In più i colori "
        "vengono ridotti a una tavolozza di 64: il logo usa poche tinte piatte, e il "
        "JPG di partenza aveva sparso attorno a ogni contorno migliaia di sfumature "
        "quasi identiche, che il PNG comprime malissimo.",
    ),
    (
        "codice",
        "originale      2,1 MB   JPG CMYK, profilo ICC da 1,8 MB\n"
        "primo tentativo  1350 KB   profilo copiato dentro il PNG\n"
        "risultato          16 KB   sRGB, senza profilo, 64 colori",
    ),
    (
        "paragrafo",
        "Il tutto sta in <b>docs/prepara_logo.py</b>, che si rilancia se un domani "
        "l'ufficio comunicazione consegnasse un logo nuovo. Due test di guardia "
        "verificano che i loghi vengano serviti e che restino sotto i 100 KB: se "
        "qualcuno copiasse l'originale dentro static senza prepararlo, se ne "
        "accorgerebbe subito.",
    ),
    (
        "paragrafo",
        "Lezione generale: un file consegnato da altri va sempre guardato dentro "
        "prima di metterlo in produzione. «È solo un'immagine» non è una descrizione "
        "sufficiente.",
    ),

    ("pagina_nuova", None),

    # ==================================================================
    ("titolo1", "Passo 4 — La home «Pazienti ricoverati»"),
    (
        "paragrafo",
        "Obiettivo del passo: il cruscotto vero. Tre riquadri, uno per reparto, con "
        "l'elenco dei ricoverati ordinato per data presunta di dimissione, la gravità "
        "cliccabile, l'inserimento di un paziente, la modifica della dimissione, lo "
        "spostamento di reparto e la dimissione.",
    ),

    ("titolo2", "I concetti nuovi"),

    ("titolo3", "1. L'ordinamento naturale"),
    (
        "paragrafo",
        "In ordine alfabetico <b>A-10 viene prima di A-2</b>, perché il carattere «1» "
        "viene prima del «2». In reparto è il contrario: il letto 2 viene prima del 10.",
    ),
    (
        "paragrafo",
        "La soluzione è spezzare la sigla nei suoi pezzi e trattare i numeri come "
        "numeri: «A-2» diventa [\"a-\", 2, \"\"] e «A-10» diventa [\"a-\", 10, \"\"]. "
        "A quel punto 2 è minore di 10 e l'ordine torna quello giusto.",
    ),
    (
        "riquadro",
        (
            "Perché l'ordinamento non lo fa il database",
            "SQL non sa ordinare in modo naturale, e il poco che sa fare si scrive "
            "in modi diversi su SQLite e su SQL Server: il codice smetterebbe di "
            "essere lo stesso nelle due fasi. I pazienti vengono quindi letti dal "
            "database e ordinati in Python. Con un centinaio di ricoverati la "
            "differenza di velocità non è misurabile.",
        ),
    ),
    (
        "paragrafo",
        "L'ordine completo è a tre livelli: prima chi non ha una data di dimissione "
        "va in fondo e mostra «da definire»; poi si ordina per data, dalla più vicina; "
        "a parità di data, per letto in ordine naturale.",
    ),

    ("titolo3", "2. Il salvataggio immediato"),
    (
        "paragrafo",
        "Il pallino della gravità ruota a ogni clic — non valutato, verde, giallo, "
        "rosso, e si ricomincia — e si salva subito, senza ricaricare la pagina. Il "
        "browser manda una richiesta <b>fetch</b> al server, riceve il nuovo stato e "
        "aggiorna il solo pallino.",
    ),
    (
        "paragrafo",
        "Ricaricare l'intera home per cambiare un pallino sarebbe uno spreco, e in "
        "reparto si perderebbe la posizione nella pagina: con tre reparti pieni si "
        "tornerebbe ogni volta in cima.",
    ),
    (
        "paragrafo",
        "Due accortezze meno ovvie. Il pulsante si blocca durante l'attesa: due clic "
        "rapidi farebbero avanzare il ciclo due volte e l'utente vedrebbe un colore "
        "che non ha scelto. E se il salvataggio fallisce compare un avviso che invita "
        "a ricaricare: peggio di un errore è un errore silenzioso, con l'infermiere "
        "convinto di aver segnato un paziente critico.",
    ),

    ("titolo3", "3. Niente JavaScript dentro l'HTML"),
    (
        "paragrafo",
        "Nel prototipo i pulsanti portavano scritto onclick=\"...\" direttamente "
        "nell'HTML. Qui non è possibile: la Content-Security-Policy che abbiamo messo "
        "al passo 1 consente solo codice servito da noi, e un onclick è codice dentro "
        "la pagina. Il browser lo bloccherebbe.",
    ),
    (
        "paragrafo",
        "Tutti i comportamenti sono quindi agganciati in <b>app.js</b>, leggendo gli "
        "attributi data-*. C'è anche un unico ascoltatore per tutta la pagina invece "
        "di uno per pulsante: si chiama <i>delega</i>, il clic risale fino al "
        "documento e lì si guarda da quale pulsante è partito.",
    ),
    (
        "riquadro",
        (
            "Il guaio che questo evita",
            "Un onclick bloccato dalla CSP non dà nessun errore visibile: compare "
            "solo nella console del browser. In reparto si vedrebbe soltanto un "
            "pulsante che non fa niente. C'è un test apposta che controlla che nella "
            "home non compaia nessun onclick, onchange o onsubmit.",
        ),
    ),

    ("titolo2", "Lo spostamento di reparto"),
    (
        "paragrafo",
        "Realizzato come proposto: un pulsante <b>Sposta</b> che apre una finestrella "
        "con reparto di destinazione e nuovo posto letto, e riusa lo stesso controllo "
        "di letto occupato dell'inserimento.",
    ),
    (
        "paragrafo",
        "La cosa importante è che <b>non è un elimina e reinserisci</b>: la riga del "
        "paziente resta la stessa, cambia solo dove si trova. Note, checklist, date e "
        "storia restano attaccate a lui. C'è un test che lo verifica confrontando "
        "l'identificativo prima e dopo.",
    ),

    ("titolo2", "La dimissione del paziente"),
    (
        "paragrafo",
        "La finestra di conferma riporta il testo concordato, comprese le parole sul "
        "foglio da stampare prima. L'eliminazione è logica: lo stato passa a ELIMINATO "
        "con chi e quando, il paziente sparisce dal cruscotto e <b>il letto torna "
        "libero</b> — proprio perché l'indice univoco vale solo sui ricoverati.",
    ),
    (
        "paragrafo",
        "Un dettaglio: le route rifiutano con 404 le operazioni su un paziente già "
        "dimesso. Serve a chi tiene aperta una pagina vecchia e clicca su un pulsante "
        "che nel frattempo non ha più senso — succede spesso, con i PC di reparto "
        "sempre accesi.",
    ),

    # ==================================================================
    ("titolo1", "Passi 5 e 6 — Agenda e checklist"),
    (
        "paragrafo",
        "I due passi stanno insieme perché vivono nella stessa finestra: la checklist "
        "in alto, poi il campo per la nuova nota, poi l'elenco delle note.",
    ),

    ("titolo2", "Il pezzo di pagina che arriva dal server"),
    (
        "paragrafo",
        "L'Agenda si apre come finestra sopra la home e il suo contenuto viene "
        "chiesto al server al momento del clic. Il server non restituisce una pagina "
        "intera né dei dati grezzi: restituisce <b>l'HTML già disegnato</b>, che il "
        "JavaScript infila dentro la finestra.",
    ),
    (
        "riquadro",
        (
            "Perché l'HTML lo fa il server e non il browser",
            "Il testo delle note lo scrivono le persone. Jinja lo mette in pagina "
            "con l'escape automatico, quindi una nota che contenesse per errore o "
            "per malizia del codice resta testo. Costruendo l'HTML a mano nel "
            "browser basterebbe una dimenticanza per trasformare una nota in codice "
            "eseguibile, e il primo a farne le spese sarebbe il collega che la apre.",
        ),
    ),
    (
        "paragrafo",
        "Insieme all'HTML viaggia anche il numero di note visibili: serve ad "
        "aggiornare il contatore sul pulsante «Agenda» nella home, che sta fuori dalla "
        "finestra e quindi non verrebbe ridisegnato.",
    ),

    ("titolo2", "Solo l'autore, nemmeno l'amministratore"),
    (
        "paragrafo",
        "I pulsanti Modifica ed Elimina compaiono soltanto sulle proprie note, e il "
        "server rifiuta comunque chiunque altro — <b>compreso l'ADMIN</b>.",
    ),
    (
        "paragrafo",
        "Non è una svista della specifica: una nota è una dichiarazione firmata da "
        "una persona. Se un amministratore potesse riscriverla, la firma non varrebbe "
        "più niente, e in una struttura sanitaria è esattamente il contrario di quello "
        "che serve.",
    ),
    (
        "paragrafo",
        "Quando una nota viene modificata, il testo precedente finisce in "
        "<b>nota_versione</b> prima di essere sovrascritto, e la nota riceve la data "
        "di modifica. «La nota diceva un'altra cosa» non deve restare una questione di "
        "parola contro parola. L'eliminazione è logica come sempre: la nota sparisce "
        "da Agenda e PDF, ma resta nel database con chi l'ha eliminata e quando.",
    ),

    ("titolo2", "La checklist"),
    (
        "paragrafo",
        "Venti voci su due colonne, contatore e barra di avanzamento, contatore che "
        "diventa verde a 20/20. Ogni spunta si salva subito, senza ricaricare.",
    ),
    (
        "paragrafo",
        "Sulla checklist <b>non si registra chi ha spuntato né quando</b>: lo esclude "
        "la specifica, ed è una scelta sensata. È uno strumento di lavoro condiviso "
        "del reparto, non un registro di responsabilità individuali. C'è un test che "
        "controlla che la tabella abbia due sole colonne, perché è il tipo di cosa che "
        "qualcuno prima o poi «migliorerebbe» aggiungendo un campo.",
    ),
    (
        "paragrafo",
        "Se il salvataggio di una spunta fallisce, il segno viene <b>rimesso com'era</b>. "
        "Lasciarlo dove l'utente l'ha messo sarebbe peggio che non averlo messo "
        "affatto: si crederebbe di aver salvato qualcosa che non c'è.",
    ),
    (
        "paragrafo",
        "Lo stato aperto o chiuso del riquadro viene ricordato in sessionStorage, che "
        "dura quanto la scheda del browser: la preferenza segue il turno di chi sta "
        "lavorando e non resta appiccicata al PC condiviso. Se il browser vieta "
        "sessionStorage — succede in certe configurazioni — la checklist resta "
        "semplicemente aperta: è una comodità, non deve far fallire nulla.",
    ),

    ("titolo2", "I test"),
    (
        "paragrafo",
        "Da 66 a <b>138</b>. I più significativi dei tre passi:",
    ),
    (
        "elenco",
        [
            "«A-2» viene prima di «A-10», e «BOX» dopo entrambi;",
            "chi non ha data di dimissione va in fondo;",
            "il letto occupato viene rifiutato dicendo da chi;",
            "il letto di un paziente dimesso è riassegnabile;",
            "lo spostamento conserva l'identificativo e le date del paziente;",
            "la firma della nota non cambia se l'utente cambia ruolo;",
            "nemmeno l'amministratore può modificare la nota di un altro;",
            "la modifica salva il testo precedente in nota_versione;",
            "riscrivere lo stesso testo non crea una versione inutile;",
            "l'OSS riceve 403 su gravità, note, checklist ed eliminazione;",
            "nel registro non finisce mai il testo di una nota;",
            "nella home non compare nessun onclick.",
        ],
    ),

    ("titolo2", "Come si verifica che funzioni"),
    (
        "paragrafo",
        "Si entra con administrator e si guarda la home: tre riquadri, i pazienti "
        "ordinati per dimissione, i pallini colorati. Poi vale la pena provare:",
    ),
    (
        "elenco",
        [
            "cliccare un pallino più volte: cambia colore e resta cambiato anche "
            "ricaricando;",
            "cliccare una data di dimissione e spostarla: l'elenco si riordina;",
            "aprire l'Agenda di Rossi Mario: cinque note raggruppate per giorno, "
            "una con «modificata il»;",
            "entrare come cbianchi / prova2026: può modificare solo le proprie note;",
            "entrare come gverdi / prova2026 (OSS): vede tutto ma non può toccare "
            "niente.",
        ],
    ),

    ("pagina_nuova", None),

    # ==================================================================
    ("titolo1", "Passo 7 — Il PDF del paziente"),
    (
        "paragrafo",
        "Obiettivo del passo: il foglio da stampare prima di dimettere qualcuno. "
        "Titolo, dati del paziente, checklist su due colonne con le caselle spuntate "
        "e lo storico delle note con le stesse firme dell'Agenda.",
    ),

    ("titolo2", "Perché il PDF lo fa il server"),
    (
        "paragrafo",
        "Il prototipo generava il PDF nel browser, con una libreria da 400 KB "
        "incorporata nella pagina. Qui lo genera il server, con ReportLab. Tre "
        "motivi:",
    ),
    (
        "elenco",
        [
            "funziona uguale su Edge e su Chrome, senza dipendere da cosa il "
            "browser riesce a fare;",
            "non serve internet, e la pagina resta leggera;",
            "il documento riporta i dati del database, non quelli che per caso "
            "erano a schermo in quel momento.",
        ],
    ),

    ("titolo2", "Il font DejaVu incluso nel progetto"),
    (
        "paragrafo",
        "ReportLab ha Helvetica già dentro, e sulle lettere accentate se la cava. Ma "
        "copre solo l'alfabeto occidentale di base: su un carattere fuori elenco "
        "stampa un quadratino nero. La specifica chiede quindi <b>DejaVu Sans incluso "
        "nel progetto</b>, ed è la scelta giusta per un motivo in più: il risultato è "
        "identico sul PC di sviluppo e sulla macchina virtuale, dove i font installati "
        "sono altri.",
    ),
    (
        "paragrafo",
        "I tre file (normale, grassetto, corsivo) stanno in app/static/font/ con la "
        "loro licenza. Vengono registrati una volta sola per processo: ReportLab tiene "
        "un elenco globale, e ripetere la registrazione a ogni PDF sarebbe uno spreco.",
    ),

    ("titolo2", "Le caselle disegnate a mano"),
    (
        "paragrafo",
        "Le caselle della checklist non usano i caratteri ☑ e ☐, ma sono disegnate: "
        "un rettangolo e, se spuntata, due segmenti. Quei simboli non esistono in "
        "tutti i font, e se un domani si cambiasse font al loro posto comparirebbero "
        "dei quadratini vuoti senza che nessuno capisca perché.",
    ),
    (
        "paragrafo",
        "È il primo <i>flowable</i> scritto da noi: una classe che sa disegnarsi da "
        "sola su una tela e che ReportLab impagina come qualunque altro pezzo di "
        "contenuto. Lo stesso vale per il pallino della gravità, con gli stessi colori "
        "dello schermo.",
    ),

    ("titolo2", "Due bug trovati dai test"),
    (
        "riquadro",
        (
            "Il colore senza il cancelletto",
            "La firma di ogni nota è colorata secondo il ruolo. Il colore lo "
            "costruivo con hexval()[2:], che dà «6b4fa0» — ma ReportLab vuole "
            "«#6b4fa0», e senza il cancelletto la generazione del PDF falliva. Non "
            "era visibile da nessuna parte: i PDF senza note funzionavano "
            "benissimo, e il guasto sarebbe comparso la prima volta che qualcuno "
            "stampava una scheda con delle note dentro.",
        ),
    ),
    (
        "paragrafo",
        "Il secondo riguarda i <b>segni speciali nelle note</b>. ReportLab legge i "
        "paragrafi come XML: una nota che contenga «PA &lt; 90 &amp; FC &gt; 100» "
        "farebbe fallire la generazione. I tre caratteri vanno disinnescati, e "
        "l'ordine conta — la &amp; va sostituita per prima, altrimenti si "
        "rovinerebbero le sostituzioni fatte dopo.",
    ),
    (
        "paragrafo",
        "È il tipo di errore che si presenta il giorno in cui un medico scrive una "
        "disuguaglianza in una nota, e non un minuto prima. C'è un test apposta.",
    ),

    ("titolo2", "Dettagli di consegna"),
    (
        "tabella",
        {
            "intestazioni": ["Scelta", "Perché"],
            "righe": [
                [
                    "Content-Disposition: attachment",
                    "Il browser scarica il file invece di aprirlo in una scheda. In "
                    "reparto il gesto è «stampo e allego alla cartella», non «leggo "
                    "a video».",
                ],
                [
                    "Cache-Control: no-store",
                    "La scheda contiene tutte le note del paziente e i PC di reparto "
                    "sono condivisi: non deve restare nella cache del browser.",
                ],
                [
                    "Nome del file ripulito",
                    "«De Santis Anna Maria» diventa "
                    "Agenda_De_Santis_Anna_Maria_2026-09-18.pdf: spazi e caratteri "
                    "strani nel nome di un file scaricato creano guai su Windows.",
                ],
                [
                    "Un collegamento, non un pulsante",
                    "Scaricare un file è una navigazione: così funziona anche il "
                    "tasto destro «Salva con nome».",
                ],
                [
                    "Download registrato",
                    "La scheda porta fuori dal programma tutte le note del paziente: "
                    "sapere chi l'ha scaricata e quando conta.",
                ],
            ],
            "larghezze": [150, 320],
        },
    ),

    ("titolo2", "I test"),
    (
        "paragrafo",
        "Da 138 a <b>162</b>. Per controllare il contenuto dei PDF i test li "
        "rileggono con pypdf, che serve soltanto ai test. I più significativi:",
    ),
    (
        "elenco",
        [
            "il file comincia con %PDF- e finisce con %%EOF;",
            "«Continuità», «Città» e «Perché» si rileggono intatti dal PDF;",
            "una nota con «PA &lt; 90 &amp; FC &gt; 100» non fa fallire la generazione;",
            "le note eliminate non compaiono nel foglio;",
            "il contatore della checklist riflette le spunte vere;",
            "con 60 note il documento va su più pagine e il piè di pagina dice "
            "«Pagina 1 di 5», «Pagina 2 di 5» e così via fino in fondo;",
            "l'OSS riceve 403 e non vede nemmeno il collegamento;",
            "Amministrazione / IT invece può scaricare.",
        ],
    ),

    ("titolo2", "Esito"),
    (
        "elenco",
        [
            "Scheda generata per un paziente vero: 1 pagina, 45 KB.",
            "Dati, checklist 5/20 e cinque note raggruppate per giorno, una con "
            "«modificata il».",
            "Scaricata dal server in ascolto: attachment, no-store, nome corretto.",
            "pytest: 162 test su 162 passati.",
        ],
    ),

    # ------------------------------------------------------------------
    ("titolo1", "Prossimo passo"),
    (
        "paragrafo",
        "<b>Passo 8 — Gestione utenti e registro accessi.</b> La pagina con cui "
        "l'amministratore crea gli account, cambia i ruoli, reimposta le password e "
        "sblocca chi si è chiuso fuori; e la pagina di consultazione del registro, con "
        "filtri per periodo, utente e azione.",
    ),
    (
        "paragrafo",
        "Poi il <b>passo 9</b>: rifinitura grafica fedele al prototipo e chiusura "
        "della Fase 1.",
    ),
]
