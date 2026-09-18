"""I modelli: le tabelle del database descritte come classi Python.

Un <i>modello</i> è una classe che rappresenta una tabella: ogni attributo è
una colonna, ogni oggetto della classe è una riga. SQLAlchemy fa da
traduttore: quando scriviamo

    paziente.cognome = "Rossi"
    db.session.commit()

lui genera l'istruzione SQL UPDATE corrispondente e la manda al database.

Il vantaggio non è solo la comodità di non scrivere SQL a mano. È che lo
stesso identico codice funziona su SQLite (Fase 1, sul PC) e su SQL Server
(Fase 2, sulla macchina virtuale): è SQLAlchemy a conoscere le differenze fra
i due. E non esiste il rischio di SQL injection, perché non costruiamo mai
un'istruzione incollando insieme pezzi di testo.

Nota sui tipi di testo: usiamo Unicode e UnicodeText invece di String e Text.
Su SQLite non cambia nulla, ma su SQL Server significa colonne NVARCHAR
invece di VARCHAR — cioè lettere accentate salvate correttamente. "Città" in
una colonna VARCHAR diventerebbe "Citt?".
"""

from __future__ import annotations

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.estensioni import db
from app.formati import adesso_utc

# --------------------------------------------------------------------------
# Valori ammessi, scritti in un punto solo.
# Non usiamo il tipo Enum del database: cambiarlo su SQL Server richiede di
# ricostruire la colonna, mentre così basta una riga di Python.
# --------------------------------------------------------------------------
RUOLO_ADMIN = "ADMIN"
RUOLO_MEDICO = "MEDICO"
RUOLO_INFERMIERE = "INFERMIERE"
RUOLO_OSS = "OSS"
RUOLO_AMMIN = "AMMIN"

# Codice salvato nel database -> etichetta mostrata all'utente.
RUOLI = {
    RUOLO_ADMIN: "Amministratore",
    RUOLO_MEDICO: "Medico",
    RUOLO_INFERMIERE: "Infermiere",
    RUOLO_OSS: "OSS",
    RUOLO_AMMIN: "Amministrazione / IT",
}

GRAVITA_NON_VALUTATO = "nv"
GRAVITA = {
    GRAVITA_NON_VALUTATO: "Non valutato",
    "verde": "Stabile",
    "giallo": "Instabile",
    "rosso": "Critico",
}

# L'ordine del ciclo quando si clicca sul pallino nella home.
CICLO_GRAVITA = [GRAVITA_NON_VALUTATO, "verde", "giallo", "rosso"]

STATO_RICOVERATO = "RICOVERATO"
STATO_ELIMINATO = "ELIMINATO"


class Reparto(db.Model):
    """I tre reparti della struttura. Tabella fissa, creata dalla migrazione."""

    __tablename__ = "reparto"

    id = db.Column(db.Integer, primary_key=True)
    codice = db.Column(db.Unicode(10), unique=True, nullable=False)
    nome = db.Column(db.Unicode(60), nullable=False)
    ordine = db.Column(db.Integer, nullable=False)

    pazienti = db.relationship("Paziente", back_populates="reparto")

    def __repr__(self) -> str:
        return f"<Reparto {self.codice}>"


class Utente(UserMixin, db.Model):
    """Chi usa il programma. Gli account li crea l'amministratore.

    Gli utenti non si cancellano mai: le note devono sempre poter risalire a
    chi le ha scritte. Per togliere l'accesso a qualcuno si usa attivo=False.

    UserMixin aggiunge i metodi che Flask-Login si aspetta di trovare
    (is_authenticated, get_id e compagnia): sono sempre uguali, e scriverli a
    mano sarebbe solo un'occasione per sbagliarli.
    """

    __tablename__ = "utente"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode(50), unique=True, nullable=False)
    nome = db.Column(db.Unicode(80), nullable=False)
    cognome = db.Column(db.Unicode(80), nullable=False)
    ruolo = db.Column(db.Unicode(12), nullable=False)

    # Mai la password: solo la sua impronta. Vedi imposta_password().
    password_hash = db.Column(db.Unicode(255), nullable=False)

    attivo = db.Column(db.Boolean, nullable=False, default=True)
    deve_cambiare_password = db.Column(db.Boolean, nullable=False, default=True)

    # Contatore per il blocco dopo 5 tentativi falliti consecutivi.
    tentativi_falliti = db.Column(db.Integer, nullable=False, default=0)
    bloccato_fino = db.Column(db.DateTime, nullable=True)
    ultimo_accesso = db.Column(db.DateTime, nullable=True)

    creato_il = db.Column(db.DateTime, nullable=False, default=adesso_utc)
    # Vuoto per il primo amministratore: non c'era nessuno prima di lui.
    creato_da = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=True)

    @staticmethod
    def normalizza_username(username: str) -> str:
        """Il nome utente si salva e si confronta sempre in minuscolo.

        SQLite e SQL Server trattano le maiuscole in modo diverso a seconda
        della configurazione: normalizzando qui, "MRossi" e "mrossi" sono lo
        stesso account su entrambi, senza dipendere dal database.
        """
        return username.strip().lower()

    def imposta_password(self, password: str) -> None:
        """Salva l'impronta della password, non la password.

        generate_password_hash applica l'algoritmo scrypt: una funzione che
        trasforma la password in una stringa illeggibile e da cui non si può
        tornare indietro. Nemmeno noi che abbiamo il database possiamo sapere
        qual è la password di un utente: al momento dell'accesso rifacciamo lo
        stesso calcolo e confrontiamo i due risultati.

        Se un domani il database venisse copiato, le password resterebbero
        comunque inutilizzabili.
        """
        self.password_hash = generate_password_hash(password)

    def password_corretta(self, password: str) -> bool:
        """Verifica una password contro l'impronta salvata."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        """Flask-Login chiama così il «può entrare?».

        Lo colleghiamo alla nostra colonna attivo: un utente disattivato non
        entra, e se era già collegato viene buttato fuori alla richiesta
        successiva. Senza questa riga UserMixin risponderebbe sempre «sì».
        """
        return bool(self.attivo)

    @property
    def nome_completo(self) -> str:
        """«Mario Rossi» — come compare nella firma delle note."""
        return f"{self.nome} {self.cognome}"

    @property
    def etichetta_ruolo(self) -> str:
        return RUOLI.get(self.ruolo, self.ruolo)

    def __repr__(self) -> str:
        return f"<Utente {self.username} ({self.ruolo})>"


class Paziente(db.Model):
    """Un paziente ricoverato.

    Non è una cartella clinica: niente codice fiscale, niente diagnosi,
    niente terapie. Solo ciò che serve a organizzare la degenza.
    """

    __tablename__ = "paziente"

    id = db.Column(db.Integer, primary_key=True)
    reparto_id = db.Column(db.Integer, db.ForeignKey("reparto.id"), nullable=False)

    nome = db.Column(db.Unicode(80), nullable=False)
    cognome = db.Column(db.Unicode(80), nullable=False)
    posto_letto = db.Column(db.Unicode(10), nullable=False)

    gravita = db.Column(
        db.Unicode(6), nullable=False, default=GRAVITA_NON_VALUTATO
    )

    data_arrivo = db.Column(db.Date, nullable=False)
    data_dimissione_presunta = db.Column(db.Date, nullable=True)

    stato = db.Column(db.Unicode(12), nullable=False, default=STATO_RICOVERATO)

    creato_il = db.Column(db.DateTime, nullable=False, default=adesso_utc)
    creato_da = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=False)

    # Eliminazione logica: il paziente sparisce dal cruscotto e il letto torna
    # libero, ma la riga resta, perché le note devono conservare il contesto.
    eliminato_il = db.Column(db.DateTime, nullable=True)
    eliminato_da = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=True)

    reparto = db.relationship("Reparto", back_populates="pazienti")
    note = db.relationship("Nota", back_populates="paziente")
    spunte = db.relationship("ChecklistSpunta", back_populates="paziente")

    __table_args__ = (
        # Una dimissione prevista prima dell'arrivo è un errore di battitura.
        # Il controllo lo fa anche l'applicazione, con un messaggio in
        # italiano; qui è la rete di sicurezza del database, che nessun bug
        # dell'applicazione può aggirare.
        db.CheckConstraint(
            "data_dimissione_presunta IS NULL "
            "OR data_dimissione_presunta >= data_arrivo",
            name="ck_paziente_dimissione_dopo_arrivo",
        ),
        # Due pazienti non possono occupare lo stesso letto. Ma il vincolo
        # vale solo per i RICOVERATI: se contasse anche gli eliminati, un
        # letto usato in passato resterebbe bloccato per sempre. Si chiama
        # "indice parziale"; SQLite e SQL Server lo supportano entrambi, con
        # sintassi diversa, e SQLAlchemy sceglie quella giusta.
        db.Index(
            "ux_paziente_letto_occupato",
            "reparto_id",
            "posto_letto",
            unique=True,
            sqlite_where=db.text("stato = 'RICOVERATO'"),
            mssql_where=db.text("stato = 'RICOVERATO'"),
        ),
        # La home chiede sempre "i ricoverati di questo reparto ordinati per
        # dimissione": questo indice le fa trovare già pronte.
        db.Index(
            "ix_paziente_cruscotto",
            "stato",
            "reparto_id",
            "data_dimissione_presunta",
        ),
    )

    @property
    def etichetta(self) -> str:
        """«Rossi Mario» — come compare in elenco nella home."""
        return f"{self.cognome} {self.nome}"

    @property
    def etichetta_gravita(self) -> str:
        return GRAVITA.get(self.gravita, self.gravita)

    def __repr__(self) -> str:
        return f"<Paziente {self.etichetta} letto {self.posto_letto}>"


class Nota(db.Model):
    """Una nota organizzativa dell'Agenda del paziente.

    Autore e ruolo vengono copiati dentro la nota al momento della scrittura,
    invece di essere letti dall'utente collegato ogni volta che si mostra la
    nota. Motivo: se Carlo Bianchi da infermiere diventasse medico, le note
    che ha scritto da infermiere devono restare firmate «Infermiere: Carlo
    Bianchi». Una firma racconta com'erano le cose quel giorno.
    """

    __tablename__ = "nota"

    id = db.Column(db.Integer, primary_key=True)
    paziente_id = db.Column(db.Integer, db.ForeignKey("paziente.id"), nullable=False)

    autore_id = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=False)
    autore_nome = db.Column(db.Unicode(170), nullable=False)
    autore_ruolo = db.Column(db.Unicode(12), nullable=False)

    testo = db.Column(db.UnicodeText, nullable=False)

    # Data italiana del giorno in cui è stata scritta: è quella che raggruppa
    # le note sotto le intestazioni «Oggi, 16/09/2026» in Agenda.
    data_nota = db.Column(db.Date, nullable=False)

    creata_il = db.Column(db.DateTime, nullable=False, default=adesso_utc)
    modificata_il = db.Column(db.DateTime, nullable=True)

    eliminata = db.Column(db.Boolean, nullable=False, default=False)
    eliminata_il = db.Column(db.DateTime, nullable=True)
    eliminata_da = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=True)

    paziente = db.relationship("Paziente", back_populates="note")
    versioni = db.relationship("NotaVersione", back_populates="nota")

    __table_args__ = (
        # L'Agenda chiede sempre "le note non eliminate di questo paziente,
        # dalla più recente": le colonne sono in quest'ordine apposta.
        db.Index("ix_nota_agenda", "paziente_id", "eliminata", "data_nota", "id"),
    )

    def __repr__(self) -> str:
        return f"<Nota {self.id} paziente {self.paziente_id}>"


class NotaVersione(db.Model):
    """Il testo precedente di una nota, conservato quando viene modificata.

    Serve a poter ricostruire cosa c'era scritto prima. In una struttura
    sanitaria "la nota diceva un'altra cosa" non può essere una questione di
    parola contro parola.
    """

    __tablename__ = "nota_versione"

    id = db.Column(db.Integer, primary_key=True)
    nota_id = db.Column(db.Integer, db.ForeignKey("nota.id"), nullable=False)
    testo_precedente = db.Column(db.UnicodeText, nullable=False)
    sostituito_il = db.Column(db.DateTime, nullable=False, default=adesso_utc)
    sostituito_da = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=False)

    nota = db.relationship("Nota", back_populates="versioni")

    def __repr__(self) -> str:
        return f"<NotaVersione nota {self.nota_id}>"


class VoceChecklist(db.Model):
    """Una delle 20 voci della checklist di dimissione.

    La chiave primaria è il codice, non un numero: le spunte dei pazienti si
    agganciano al codice, quindi il testo della voce si può correggere senza
    che nessuno perda le spunte già fatte.
    """

    __tablename__ = "voce_checklist"

    codice = db.Column(db.Unicode(20), primary_key=True)
    testo = db.Column(db.Unicode(120), nullable=False)
    ordine = db.Column(db.Integer, nullable=False)
    attiva = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<VoceChecklist {self.codice}>"


class ChecklistSpunta(db.Model):
    """Una riga = una voce spuntata per un paziente.

    Non c'è una colonna "spuntato sì/no": l'esistenza della riga <i>è</i> la
    spunta. Togliere la spunta significa cancellare la riga. È l'unica
    cancellazione fisica del programma, ed è voluta: la specifica dice
    esplicitamente che sulle spunte non si tiene traccia di chi e quando.
    """

    __tablename__ = "checklist_spunta"

    paziente_id = db.Column(
        db.Integer, db.ForeignKey("paziente.id"), primary_key=True
    )
    voce_codice = db.Column(
        db.Unicode(20), db.ForeignKey("voce_checklist.codice"), primary_key=True
    )

    paziente = db.relationship("Paziente", back_populates="spunte")

    def __repr__(self) -> str:
        return f"<Spunta paziente {self.paziente_id} voce {self.voce_codice}>"


class EventoAudit(db.Model):
    """Il registro accessi: chi ha fatto cosa e quando.

    Tabella in sola aggiunta: il programma ci scrive righe nuove e non
    modifica né cancella mai quelle vecchie. In Fase 2 lo garantirà anche SQL
    Server, negando UPDATE e DELETE al login dell'applicazione.

    Il campo "dettagli" non contiene mai il testo delle note: sarebbe un dato
    sanitario finito in un registro tecnico.
    """

    __tablename__ = "evento_audit"

    # Il registro cresce all'infinito, quindi su SQL Server serve un BIGINT.
    # Ma SQLite sa numerare da solo soltanto le colonne INTEGER: with_variant
    # dice a SQLAlchemy di usare il tipo giusto a seconda del database.
    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    quando = db.Column(db.DateTime, nullable=False, default=adesso_utc, index=True)

    utente_id = db.Column(db.Integer, db.ForeignKey("utente.id"), nullable=True)
    # Nei login falliti l'utente potrebbe non esistere: salviamo il nome
    # tentato, che è comunque utile per accorgersi di tentativi ripetuti.
    username_tentato = db.Column(db.Unicode(50), nullable=True)

    azione = db.Column(db.Unicode(30), nullable=False, index=True)
    entita = db.Column(db.Unicode(20), nullable=True)
    entita_id = db.Column(db.Integer, nullable=True)
    dettagli = db.Column(db.Unicode(255), nullable=True)
    indirizzo_ip = db.Column(db.Unicode(45), nullable=False)

    def __repr__(self) -> str:
        return f"<EventoAudit {self.azione} {self.quando}>"
