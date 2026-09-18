"""Attrezzatura comune ai test.

pytest carica questo file da solo: le funzioni marcate con @pytest.fixture
diventano disponibili a tutti i test, che le richiedono semplicemente
mettendone il nome tra i parametri.
"""

from datetime import date

import pytest

from app import create_app
from app.dati_fissi import REPARTI, VOCI_CHECKLIST
from app.estensioni import db as database
from app.models import (
    RUOLO_ADMIN,
    STATO_RICOVERATO,
    Paziente,
    Reparto,
    Utente,
    VoceChecklist,
)


@pytest.fixture
def app():
    """Un'applicazione con un database in memoria, nuovo per ogni test.

    Il database vive nella RAM e sparisce a fine test: i test non possono
    sporcarsi a vicenda e non toccano mai il cruscotto.db vero.

    Le tabelle qui si creano con create_all() invece che con le migrazioni,
    perché è immediato; i dati fissi li rimettiamo a mano, dato che nella
    realtà li inserisce la migrazione.
    """
    applicazione = create_app("test")

    with applicazione.app_context():
        database.create_all()
        _inserisci_dati_fissi()
        yield applicazione
        database.session.remove()
        database.drop_all()


def _inserisci_dati_fissi() -> None:
    for codice, nome, ordine in REPARTI:
        database.session.add(Reparto(codice=codice, nome=nome, ordine=ordine))
    for posizione, (codice, testo) in enumerate(VOCI_CHECKLIST, start=1):
        database.session.add(
            VoceChecklist(codice=codice, testo=testo, ordine=posizione, attiva=True)
        )
    database.session.commit()


@pytest.fixture
def client(app):
    """Un finto browser che parla con l'applicazione senza rete né server."""
    return app.test_client()


@pytest.fixture
def db(app):
    """La sessione del database, già dentro il contesto dell'applicazione."""
    return database


@pytest.fixture
def crea_utente(db):
    """Restituisce una funzione che crea utenti con pochi parametri."""

    def _crea(
        username: str = "utente",
        password: str = "password1",
        ruolo: str = RUOLO_ADMIN,
        nome: str = "Nome",
        cognome: str = "Cognome",
        attivo: bool = True,
        deve_cambiare_password: bool = False,
    ) -> Utente:
        utente = Utente(
            username=Utente.normalizza_username(username),
            nome=nome,
            cognome=cognome,
            ruolo=ruolo,
            attivo=attivo,
            deve_cambiare_password=deve_cambiare_password,
        )
        utente.imposta_password(password)
        db.session.add(utente)
        db.session.commit()
        return utente

    return _crea


@pytest.fixture
def accedi(client):
    """Restituisce una funzione che esegue l'accesso come farebbe un browser."""

    def _accedi(username: str = "capo", password: str = "capo1234"):
        return client.post(
            "/accedi",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    return _accedi


@pytest.fixture
def amministratore(db):
    """Un amministratore pronto all'uso, per i test che hanno bisogno di un autore."""
    utente = Utente(
        username="capo",
        nome="Anna",
        cognome="Ricci",
        ruolo=RUOLO_ADMIN,
        deve_cambiare_password=False,
    )
    utente.imposta_password("capo1234")
    db.session.add(utente)
    db.session.commit()
    return utente


@pytest.fixture
def crea_paziente(db, amministratore):
    """Restituisce una funzione che crea pazienti con pochi parametri.

    Nei test serve continuamente un paziente qualsiasi: così ogni test scrive
    solo i campi che gli interessano davvero e il resto ha valori sensati.
    """

    def _crea(
        codice_reparto: str = "AOUP",
        posto_letto: str = "A-01",
        nome: str = "Mario",
        cognome: str = "Rossi",
        data_arrivo: date | None = None,
        data_dimissione_presunta: date | None = None,
        stato: str = STATO_RICOVERATO,
    ) -> Paziente:
        reparto = db.session.query(Reparto).filter_by(codice=codice_reparto).one()
        paziente = Paziente(
            reparto_id=reparto.id,
            nome=nome,
            cognome=cognome,
            posto_letto=posto_letto,
            data_arrivo=data_arrivo or date(2026, 9, 1),
            data_dimissione_presunta=data_dimissione_presunta,
            stato=stato,
            creato_da=amministratore.id,
        )
        db.session.add(paziente)
        db.session.commit()
        return paziente

    return _crea
