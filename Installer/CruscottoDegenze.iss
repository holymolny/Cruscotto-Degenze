; ==========================================================================
;  Cruscotto Degenze — installer per Windows
;
;  Questo file descrive il programma di installazione. Si compila con
;  Inno Setup, che lo trasforma in un unico CruscottoDegenze-Setup.exe con
;  dentro tutti i file del programma:
;
;      powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1
;
;  Il setup .exe si limita a copiare i file e a raccogliere i dati
;  dell'amministratore; il lavoro vero (Python, librerie, database) lo fa
;  poi installazione\Configura.ps1. La divisione è voluta: quello script si
;  può rilanciare da solo se qualcosa va storto, senza reinstallare tutto.
; ==========================================================================

#define NomeApp        "Cruscotto Degenze"
#define VersioneApp    "2.1"
#define Editore        "Casa di Cura Misericordia Navacchio"
#define NomeEseguibile "Avvia.cmd"

[Setup]
; Identifica il programma per Windows: non va mai cambiato, altrimenti una
; nuova versione verrebbe installata accanto alla vecchia invece che sopra.
AppId={{98DB173F-EEC3-41EF-AB39-334246A8AC3C}
AppName={#NomeApp}
AppVersion={#VersioneApp}
AppVerName={#NomeApp} {#VersioneApp}
AppPublisher={#Editore}
VersionInfoDescription=Installazione del {#NomeApp}
VersionInfoVersion=2.1.0.0

; Installazione solo per l'utente corrente, senza chiedere i permessi di
; amministratore. Non è solo una comodità: il programma scrive il proprio
; database (cruscotto.db) nella cartella in cui è installato, e dentro
; "Programmi" Windows non glielo lascerebbe fare.
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\CruscottoDegenze
DefaultGroupName={#NomeApp}
UninstallDisplayName={#NomeApp}
UninstallDisplayIcon={app}\risorse\cruscotto.ico

; Il Cruscotto gira su Python a 64 bit.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

OutputDir=Output
OutputBaseFilename=CruscottoDegenze-Setup
SetupIconFile=risorse\cruscotto.ico
Compression=lzma2/max
SolidCompression=yes

WizardStyle=modern
WizardImageFile=risorse\wizard-grande.bmp
WizardSmallImageFile=risorse\wizard-piccolo.bmp
DisableProgramGroupPage=yes
ShowLanguageDialog=no

[Languages]
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"

[Messages]
it.WelcomeLabel2=Questa procedura installa il [name/ver] su questo computer.%n%nIl Cruscotto ha bisogno di Python per funzionare: se non è già presente, verrà scaricato e installato automaticamente. Serve quindi una connessione a internet, ma solo adesso: una volta installato il programma funziona anche senza.%n%nSi consiglia di chiudere le altre applicazioni prima di procedere.
it.FinishedLabelNoIcons=Il [name] è installato e pronto all'uso.
it.FinishedLabel=Il [name] è installato e pronto all'uso.%n%nPer accendere il programma usa il collegamento «{#NomeApp}». Si aprirà una finestra nera, che è il programma stesso in funzione, e subito dopo il browser sulla pagina di accesso.%n%nEntra con le credenziali dell'amministratore: da «Gestione utenti» potrai poi creare tutti gli altri account.

[Tasks]
Name: "collegamentodesktop"; Description: "Crea un collegamento sul &Desktop"; GroupDescription: "Collegamenti:"

[Files]
; --- Il programma ---
Source: "..\app\*";        DestDir: "{app}\app";        Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,*.pyo,__pycache__\*,*\__pycache__\*"
Source: "..\migrations\*"; DestDir: "{app}\migrations"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,*.pyo,__pycache__\*,*\__pycache__\*"
Source: "..\tests\*";      DestDir: "{app}\tests";      Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pyc,*.pyo,__pycache__\*,*\__pycache__\*"
Source: "..\wsgi.py";         DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example";     DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md";        DestDir: "{app}"; Flags: ignoreversion

; --- Documentazione ---
Source: "..\docs\Diario_Cruscotto_Degenze.pdf";          DestDir: "{app}\docs";     Flags: ignoreversion
Source: "..\docs\Guida_Tecnica_Cruscotto_Degenze.pdf";   DestDir: "{app}\docs";     Flags: ignoreversion
Source: "..\PromptIA\Documentazione_Cruscotto_Degenze.pdf"; DestDir: "{app}\PromptIA"; Flags: ignoreversion
Source: "..\PromptIA\Prompt_Cruscotto_Degenze.pdf";         DestDir: "{app}\PromptIA"; Flags: ignoreversion

; --- Avvio e configurazione ---
; Avvia.cmd sta nella radice perché è il file che la persona cerca quando
; apre la cartella del programma; il resto sta in "installazione", che è
; roba da non toccare.
Source: "script\Avvia.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "script\*";         DestDir: "{app}\installazione"; Flags: ignoreversion; Excludes: "Avvia.cmd"
Source: "risorse\cruscotto.ico"; DestDir: "{app}\risorse"; Flags: ignoreversion

[Icons]
Name: "{group}\{#NomeApp}"; Filename: "{app}\{#NomeEseguibile}"; WorkingDir: "{app}"; IconFilename: "{app}\risorse\cruscotto.ico"; Comment: "Accende il Cruscotto Degenze e apre la pagina di accesso"
Name: "{group}\Cartella del programma"; Filename: "{app}"
Name: "{group}\Diario di sviluppo"; Filename: "{app}\docs\Diario_Cruscotto_Degenze.pdf"
Name: "{group}\Guida tecnica"; Filename: "{app}\docs\Guida_Tecnica_Cruscotto_Degenze.pdf"
Name: "{autodesktop}\{#NomeApp}"; Filename: "{app}\{#NomeEseguibile}"; WorkingDir: "{app}"; IconFilename: "{app}\risorse\cruscotto.ico"; Tasks: collegamentodesktop

[Run]
Filename: "{app}\{#NomeEseguibile}"; Description: "Avvia subito il {#NomeApp}"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent shellexec

[UninstallDelete]
; Roba nata dopo l'installazione, che quindi il setup non sa di aver messo
; là e non toglierebbe da solo. Le cartelle __pycache__ non stanno qui: sono
; sparse nelle sottocartelle e i caratteri jolly di questa sezione non ci
; scendono dentro. Le toglie il codice, più in basso.
Type: filesandordirs; Name: "{app}\.venv"
Type: filesandordirs; Name: "{app}\.pytest_cache"
Type: files;          Name: "{app}\cruscotto.db-journal"

; ==========================================================================
;  Codice
; ==========================================================================
[Code]

const
  LUNGHEZZA_MINIMA_PASSWORD = 8;
  PORTA_CRUSCOTTO = 8000;

var
  PaginaAdmin: TInputQueryWizardPage;

{ ---------------------------------------------------------------------- }
{  Il Cruscotto è acceso?                                                 }
{ ---------------------------------------------------------------------- }

function CruscottoInEsecuzione(): Boolean;
var
  Codice: Integer;
  Comando: String;
begin
  { Se il server è acceso, i file dentro .venv sono in uso e né
    l'installazione né la disinstallazione riuscirebbero a toccarli. Meglio
    dirlo subito con parole chiare che lasciar fallire la copia dei file.

    Chiediamo a PowerShell di provare a collegarsi alla porta del Cruscotto:
    se risponde qualcuno, il programma è in funzione. Codice 10 = acceso. }
  Result := False;
  Comando :=
    '-NoProfile -ExecutionPolicy Bypass -Command "' +
    '$c = New-Object System.Net.Sockets.TcpClient; ' +
    'try { $t = $c.BeginConnect(''127.0.0.1'', ' + IntToStr(PORTA_CRUSCOTTO) + ', $null, $null); ' +
    'if ($t.AsyncWaitHandle.WaitOne(500)) { $c.EndConnect($t); $c.Close(); exit 10 } } ' +
    'catch { }; ' +
    '$c.Close(); exit 0"';

  { Se PowerShell non parte proprio, tiriamo dritto: peggio che possa
    succedere è il messaggio d'errore meno chiaro di prima. }
  if Exec('powershell.exe', Comando, '', SW_HIDE, ewWaitUntilTerminated, Codice) then
    Result := (Codice = 10);
end;

function AvvisaSeAcceso(): Boolean;
begin
  Result := True;
  if CruscottoInEsecuzione() then
  begin
    MsgBox('Il Cruscotto Degenze risulta acceso in questo momento.' + #13#10#13#10 +
           'Chiudi la finestra nera del programma (quella con scritto ' +
           '«Cruscotto Degenze») e poi riprova.',
           mbError, MB_OK);
    Result := False;
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := AvvisaSeAcceso();
end;

function InitializeUninstall(): Boolean;
begin
  Result := AvvisaSeAcceso();
end;

{ ---------------------------------------------------------------------- }
{  Pagina dell'amministratore                                             }
{ ---------------------------------------------------------------------- }

procedure InitializeWizard();
begin
  PaginaAdmin := CreateInputQueryPage(wpSelectDir,
    'Amministratore del Cruscotto',
    'Chi potrà entrare nel programma e creare gli altri utenti.',
    'Il primo amministratore non può crearlo nessuno dall''interno del programma: ' +
    'per entrare bisogna già essere qualcuno. Lo creiamo adesso.' + #13#10 +
    'Con queste credenziali farai il primo accesso; da lì potrai creare tutti gli altri utenti.');

  PaginaAdmin.Add('Nome:', False);
  PaginaAdmin.Add('Cognome:', False);
  PaginaAdmin.Add('Nome utente (quello che scriverai per accedere):', False);
  PaginaAdmin.Add('Password (almeno ' + IntToStr(LUNGHEZZA_MINIMA_PASSWORD) + ' caratteri):', True);
  PaginaAdmin.Add('Ripeti la password:', True);
end;

function ContieneSpazi(const Testo: String): Boolean;
var
  i: Integer;
begin
  Result := False;
  for i := 1 to Length(Testo) do
    if Testo[i] = ' ' then
    begin
      Result := True;
      Exit;
    end;
end;

function CartellaScrivibile(const Cartella: String): Boolean;
var
  Prova: String;
begin
  { Non basta guardare il percorso: quello che conta è se ci possiamo
    davvero scrivere, perché là dentro finirà il database dei pazienti.
    Quindi proviamo per davvero, e poi cancelliamo. }
  Result := False;
  if not ForceDirectories(Cartella) then Exit;

  Prova := AddBackslash(Cartella) + 'prova-scrittura.tmp';
  if SaveStringToFile(Prova, 'prova', False) then
  begin
    DeleteFile(Prova);
    Result := True;
  end;
end;

function InstallazioneGiaPresente(): Boolean;
begin
  { C'è già un database nella cartella scelta: questa non è una prima
    installazione ma un aggiornamento. }
  Result := FileExists(AddBackslash(WizardDirValue) + 'cruscotto.db');
end;

function ShouldSkipPage(PaginaID: Integer): Boolean;
begin
  Result := False;

  { Sopra un'installazione esistente la pagina dell'amministratore non ha
    senso: gli utenti ci sono già nel database, e Configura.ps1 si guarderebbe
    comunque bene dal ricrearli. Chiederli lo stesso farebbe solo credere che
    le credenziali vecchie non valgano più. }
  if (PaginaID = PaginaAdmin.ID) and InstallazioneGiaPresente() then
    Result := True;
end;

function NextButtonClick(PaginaCorrente: Integer): Boolean;
var
  Nome, Cognome, Username, Password, Conferma: String;
begin
  Result := True;

  { In installazione silenziosa le pagine non si vedono, ma Inno chiama lo
    stesso questa funzione. Controllare i campi là avrebbe l'effetto di far
    fallire l'installazione per dei dati che nessuno ha avuto modo di
    inserire, e per giunta davanti a una finestra d'errore che nessuno
    vedrà. Tiriamo dritto: l'amministratore si creerà poi a mano. }
  if WizardSilent() then Exit;

  if PaginaCorrente = wpSelectDir then
  begin
    if not CartellaScrivibile(WizardDirValue) then
    begin
      MsgBox('Non riesco a scrivere in questa cartella.' + #13#10#13#10 +
             'Il Cruscotto tiene il proprio database dentro la cartella in cui è ' +
             'installato, quindi deve poterci scrivere. Cartelle come ' +
             '«C:\Programmi» non vanno bene: scegline una dentro la tua cartella ' +
             'utente.',
             mbError, MB_OK);
      Result := False;
    end;
    Exit;
  end;

  if PaginaCorrente = PaginaAdmin.ID then
  begin
    Nome     := Trim(PaginaAdmin.Values[0]);
    Cognome  := Trim(PaginaAdmin.Values[1]);
    Username := Trim(PaginaAdmin.Values[2]);
    Password := PaginaAdmin.Values[3];
    Conferma := PaginaAdmin.Values[4];

    if (Nome = '') or (Cognome = '') or (Username = '') then
    begin
      MsgBox('Nome, cognome e nome utente non possono essere vuoti.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if ContieneSpazi(Username) then
    begin
      MsgBox('Il nome utente non può contenere spazi.' + #13#10 +
             'Di solito si usa l''iniziale del nome seguita dal cognome: mrossi, cbianchi.',
             mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if Length(Password) < LUNGHEZZA_MINIMA_PASSWORD then
    begin
      MsgBox('La password deve avere almeno ' + IntToStr(LUNGHEZZA_MINIMA_PASSWORD) +
             ' caratteri.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if Password <> Conferma then
    begin
      MsgBox('Le due password non coincidono.', mbError, MB_OK);
      PaginaAdmin.Values[3] := '';
      PaginaAdmin.Values[4] := '';
      Result := False;
      Exit;
    end;

    if Lowercase(Password) = Lowercase(Username) then
    begin
      { Non la blocchiamo: è il PC di casa e la scelta è di chi installa.
        Ma è giusto che sappia cosa sta facendo. }
      if MsgBox('La password è uguale al nome utente.' + #13#10#13#10 +
                'Va bene per le prove in locale, ma non usarla mai sulla macchina ' +
                'virtuale in reparto.' + #13#10#13#10 + 'Vuoi tenerla lo stesso?',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDNO then
      begin
        Result := False;
        Exit;
      end;
    end;
  end;
end;

{ ---------------------------------------------------------------------- }
{  Dopo la copia dei file: configurazione vera e propria                  }
{ ---------------------------------------------------------------------- }

procedure CurStepChanged(Passo: TSetupStep);
var
  Codice: Integer;
  Righe: TArrayOfString;
  FileCredenziali, Parametri: String;
begin
  if Passo <> ssPostInstall then Exit;

  { Le credenziali passano da un file e non dalla riga di comando: gli
    argomenti di un processo sono leggibili da chiunque guardi l'elenco dei
    processi, e là dentro ci sarebbe la password in chiaro. Il file lo
    cancella Configura.ps1 appena l'ha letto. }
  FileCredenziali := ExpandConstant('{app}\installazione\amministratore.dati');

  { In installazione silenziosa (/SILENT, /VERYSILENT) le pagine della
    procedura guidata non vengono mai mostrate, quindi i campi sono vuoti.
    In quel caso non scriviamo il file: Configura.ps1 salta il passo e
    l'amministratore si crea dopo, a mano, con «flask crea-admin». }
  if (PaginaAdmin <> nil) and
     (Trim(PaginaAdmin.Values[0]) <> '') and (Trim(PaginaAdmin.Values[1]) <> '') and
     (Trim(PaginaAdmin.Values[2]) <> '') and (PaginaAdmin.Values[3] <> '') then
  begin
    SetArrayLength(Righe, 4);
    Righe[0] := Trim(PaginaAdmin.Values[0]);
    Righe[1] := Trim(PaginaAdmin.Values[1]);
    Righe[2] := Trim(PaginaAdmin.Values[2]);
    Righe[3] := PaginaAdmin.Values[3];

    if not SaveStringsToUTF8File(FileCredenziali, Righe, False) then
      MsgBox('Non riesco a scrivere i dati dell''amministratore.' + #13#10 +
             'L''installazione continua: potrai crearlo dopo con il comando ' +
             '«.venv\Scripts\flask.exe crea-admin».', mbInformation, MB_OK);
  end;

  WizardForm.StatusLabel.Caption :=
    'Preparazione di Python, delle librerie e del database: può richiedere qualche minuto...';

  Parametri :=
    '-NoProfile -ExecutionPolicy Bypass -File "' +
    ExpandConstant('{app}\installazione\Configura.ps1') + '" -CartellaApp "' +
    ExpandConstant('{app}') + '"';

  { SW_SHOW e non SW_HIDE: lo scaricamento delle librerie dura minuti, e una
    finestra ferma senza spiegazioni sembra un programma bloccato. Così si
    vede che sta lavorando. }
  if not Exec('powershell.exe', Parametri, ExpandConstant('{app}'), SW_SHOW,
              ewWaitUntilTerminated, Codice) then
  begin
    MsgBox('Non riesco ad avviare PowerShell, che serve a completare ' +
           'l''installazione.' + #13#10#13#10 +
           'I file sono stati copiati. Puoi riprendere da lì aprendo la cartella ' +
           'del programma e lanciando installazione\Configura.ps1.',
           mbError, MB_OK);
  end
  else if Codice <> 0 then
  begin
    MsgBox('La configurazione non è andata a buon fine.' + #13#10#13#10 +
           'Il motivo era scritto nella finestra che si è appena chiusa: la causa ' +
           'più comune è la mancanza di connessione a internet, che serve per ' +
           'scaricare Python e le librerie.' + #13#10#13#10 +
           'I file sono al loro posto: sistemata la connessione, rilancia ' +
           'installazione\Configura.ps1 dalla cartella del programma, senza ' +
           'bisogno di reinstallare.',
           mbError, MB_OK);
  end;

  { Rete di sicurezza: se Configura.ps1 si è interrotto prima di cancellarlo,
    il file con la password non deve restare sul disco. }
  DeleteFile(FileCredenziali);
end;

{ ---------------------------------------------------------------------- }
{  Disinstallazione                                                       }
{ ---------------------------------------------------------------------- }

procedure CurUninstallStepChanged(Passo: TUninstallStep);
var
  Cartella: String;
begin
  Cartella := ExpandConstant('{app}');

  if Passo = usUninstall then
  begin
    { I dati non si buttano via senza chiedere: in quel file ci sono i
      pazienti, le note e gli utenti. }
    if FileExists(AddBackslash(Cartella) + 'cruscotto.db') then
      if MsgBox('Vuoi eliminare anche i dati del Cruscotto?' + #13#10#13#10 +
                'Si tratta del database (pazienti, note, utenti) e del file di ' +
                'configurazione.' + #13#10#13#10 +
                'Rispondi No se pensi di reinstallare il programma: i dati ' +
                'verranno ritrovati al loro posto.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DeleteFile(AddBackslash(Cartella) + 'cruscotto.db');
        DeleteFile(AddBackslash(Cartella) + '.env');
      end;
    Exit;
  end;

  if Passo = usPostUninstall then
  begin
    { Mentre il programma gira, Python semina cartelle __pycache__ accanto a
      ogni file di codice. Il setup non le ha messe lui, quindi non le toglie,
      e senza questa pulizia resterebbe in giro lo scheletro delle cartelle.
      Le svuotiamo per intero: qui dentro non c'è nulla che non abbiamo
      installato noi — i dati stanno nella radice, non qua sotto. }
    DelTree(AddBackslash(Cartella) + 'app', True, True, True);
    DelTree(AddBackslash(Cartella) + 'migrations', True, True, True);
    DelTree(AddBackslash(Cartella) + 'tests', True, True, True);
    DelTree(AddBackslash(Cartella) + 'installazione', True, True, True);
    DelTree(AddBackslash(Cartella) + '__pycache__', True, True, True);

    { Riesce solo se è rimasta vuota, cioè se i dati sono stati eliminati. }
    RemoveDir(Cartella);
  end;
end;
