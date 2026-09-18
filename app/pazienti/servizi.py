"""Le regole sui pazienti, separate dalle pagine web.

Ordinamento, controllo del letto occupato, inserimento, dimissione,
spostamento di reparto. Nessuna di queste regole ha a che vedere con l'HTTP:
stanno qui perché possano essere lette e provate senza tirare in ballo form e
richieste.
"""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import func

from app.estensioni import db
from app.formati import adesso_utc, oggi_italia
from app.models import (
    CICLO_GRAVITA,
    STATO_ELIMINATO,
    STATO_RICOVERATO,
    Nota,
    Paziente,
    Reparto,
)

LUNGHEZZA_MASSIMA_NOME = 80
LUNGHEZZA_MASSIMA_LETTO = 10


class ErroreDiRegola(Exception):
    """Una regola del Cruscotto è stata violata.

    Il messaggio è già scritto in italiano per l'utente: la route deve solo
    mostrarlo, senza doverlo tradurre o interpretare.
    """


# --------------------------------------------------------------------------
# Ordinamento
# --------------------------------------------------------------------------
def chiave_naturale(testo: str) -> list:
    """Chiave per ordinare i letti come li legge una persona.

    In ordine alfabetico «A-10» verrebbe prima di «A-2», perché il carattere
    «1» viene prima del «2». Ma in reparto il letto 2 viene prima del 10.

    La soluzione è spezzare la sigla nei suoi pezzi e trattare i numeri come
    numeri: «A-2» diventa ["a-", 2, ""] e «A-10» diventa ["a-", 10, ""].
    A quel punto 2 < 10 e l'ordine torna quello giusto.
    """
    pezzi = re.split(r"(\d+)", testo)
    return [int(pezzo) if pezzo.isdigit() else pezzo.lower() for pezzo in pezzi]


def chiave_ordinamento(paziente: Paziente) -> tuple:
    """Ordina come chiede la specifica: prima chi esce prima.

    Tre criteri in cascata:
      1. chi non ha una data di dimissione va in fondo (False viene prima di
         True quando si ordina, e «senza data» è True);
      2. poi per data, dalla più vicina alla più lontana;
      3. a parità di data, per letto in ordine naturale.
    """
    senza_data = paziente.data_dimissione_presunta is None
    # date.max è un segnaposto: le righe senza data sono già in fondo per il
    # primo criterio, ma la tupla ha bisogno comunque di un valore confrontabile.
    data = paziente.data_dimissione_presunta or date.max
    return (senza_data, data, chiave_naturale(paziente.posto_letto))


def pazienti_ricoverati(reparto_id: int) -> list[Paziente]:
    """I pazienti di un reparto, già nell'ordine in cui vanno mostrati.

    L'ordinamento avviene in Python e non nel database di proposito:
    l'ordine naturale dei letti («A-2» prima di «A-10») SQL non sa farlo, e
    la scrittura cambierebbe fra SQLite e SQL Server. Con al massimo un
    centinaio di ricoverati la differenza di velocità non è misurabile.
    """
    pazienti = (
        db.session.query(Paziente)
        .filter_by(reparto_id=reparto_id, stato=STATO_RICOVERATO)
        .all()
    )
    return sorted(pazienti, key=chiave_ordinamento)


def conteggio_note(pazienti: list[Paziente]) -> dict[int, int]:
    """Quante note visibili ha ciascun paziente.

    Una sola interrogazione per tutti, invece di una per paziente: con tre
    reparti pieni sarebbero un centinaio di viaggi al database per disegnare
    una pagina sola.
    """
    if not pazienti:
        return {}

    identificativi = [paziente.id for paziente in pazienti]
    righe = (
        db.session.query(Nota.paziente_id, func.count(Nota.id))
        .filter(Nota.paziente_id.in_(identificativi), Nota.eliminata.is_(False))
        .group_by(Nota.paziente_id)
        .all()
    )
    conteggi = dict(righe)
    return {paziente.id: conteggi.get(paziente.id, 0) for paziente in pazienti}


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------
def occupante_del_letto(
    reparto_id: int, posto_letto: str, escludi_paziente_id: int | None = None
) -> Paziente | None:
    """Il paziente che occupa quel letto, se c'è.

    Il controllo lo fa anche il database con un indice univoco. Qui serve per
    poter dire all'utente <i>chi</i> c'è in quel letto, invece di mostrargli
    un errore tecnico.
    """
    interrogazione = db.session.query(Paziente).filter_by(
        reparto_id=reparto_id,
        posto_letto=posto_letto,
        stato=STATO_RICOVERATO,
    )
    if escludi_paziente_id is not None:
        interrogazione = interrogazione.filter(Paziente.id != escludi_paziente_id)
    return interrogazione.first()


def _controlla_letto_libero(
    reparto_id: int, posto_letto: str, escludi_paziente_id: int | None = None
) -> None:
    occupante = occupante_del_letto(reparto_id, posto_letto, escludi_paziente_id)
    if occupante is not None:
        raise ErroreDiRegola(
            f"Il letto {posto_letto} risulta occupato da {occupante.etichetta}."
        )


def _controlla_date(data_arrivo: date, data_dimissione: date | None) -> None:
    if data_dimissione is not None and data_dimissione < data_arrivo:
        raise ErroreDiRegola(
            "La dimissione presunta non può essere precedente alla data di arrivo."
        )


def _pulisci(testo: str, lunghezza_massima: int, nome_campo: str) -> str:
    """Toglie gli spazi ai bordi e controlla la lunghezza.

    Gli spazi in più non sono un dettaglio: «Rossi » e «Rossi» sarebbero due
    cognomi diversi in ogni ricerca futura.
    """
    pulito = (testo or "").strip()
    if not pulito:
        raise ErroreDiRegola(f"{nome_campo} è obbligatorio.")
    if len(pulito) > lunghezza_massima:
        raise ErroreDiRegola(
            f"{nome_campo} non può superare {lunghezza_massima} caratteri."
        )
    return pulito


# --------------------------------------------------------------------------
# Operazioni
# --------------------------------------------------------------------------
def crea_paziente(
    *,
    reparto_id: int,
    nome: str,
    cognome: str,
    posto_letto: str,
    data_arrivo: date,
    data_dimissione_presunta: date | None,
    autore_id: int,
) -> Paziente:
    """Inserisce un nuovo paziente. Non fa il commit."""
    reparto = db.session.get(Reparto, reparto_id)
    if reparto is None:
        raise ErroreDiRegola("Reparto non valido.")

    nome = _pulisci(nome, LUNGHEZZA_MASSIMA_NOME, "Il nome")
    cognome = _pulisci(cognome, LUNGHEZZA_MASSIMA_NOME, "Il cognome")
    posto_letto = _pulisci(posto_letto, LUNGHEZZA_MASSIMA_LETTO, "Il posto letto")

    _controlla_date(data_arrivo, data_dimissione_presunta)
    _controlla_letto_libero(reparto_id, posto_letto)

    paziente = Paziente(
        reparto_id=reparto_id,
        nome=nome,
        cognome=cognome,
        posto_letto=posto_letto,
        data_arrivo=data_arrivo,
        data_dimissione_presunta=data_dimissione_presunta,
        stato=STATO_RICOVERATO,
        creato_da=autore_id,
    )
    db.session.add(paziente)
    return paziente


def modifica_dimissione(paziente: Paziente, nuova_data: date | None) -> None:
    """Cambia la data presunta di dimissione, che si può anche svuotare."""
    _controlla_date(paziente.data_arrivo, nuova_data)
    paziente.data_dimissione_presunta = nuova_data


def prossima_gravita(attuale: str) -> str:
    """Il colore successivo nel ciclo non valutato -> verde -> giallo -> rosso.

    Un solo clic ripetuto attraversa tutti gli stati e torna al punto di
    partenza: in reparto è più rapido di un menu a tendina.
    """
    if attuale not in CICLO_GRAVITA:
        # Un valore inatteso nel database non deve bloccare l'infermiere:
        # si riparte semplicemente dall'inizio del ciclo.
        return CICLO_GRAVITA[1]
    posizione = CICLO_GRAVITA.index(attuale)
    return CICLO_GRAVITA[(posizione + 1) % len(CICLO_GRAVITA)]


def sposta_di_reparto(
    paziente: Paziente, nuovo_reparto_id: int, nuovo_posto_letto: str
) -> None:
    """Sposta un paziente in un altro reparto, o in un altro letto.

    Note, checklist e date restano attaccate al paziente: cambia solo dove
    si trova. Per questo non si usa «elimina e reinserisci», che perderebbe
    tutta la sua storia.
    """
    reparto = db.session.get(Reparto, nuovo_reparto_id)
    if reparto is None:
        raise ErroreDiRegola("Reparto non valido.")

    nuovo_posto_letto = _pulisci(
        nuovo_posto_letto, LUNGHEZZA_MASSIMA_LETTO, "Il posto letto"
    )

    if (
        paziente.reparto_id == nuovo_reparto_id
        and paziente.posto_letto == nuovo_posto_letto
    ):
        raise ErroreDiRegola("Il paziente si trova già in questo reparto e letto.")

    _controlla_letto_libero(
        nuovo_reparto_id, nuovo_posto_letto, escludi_paziente_id=paziente.id
    )

    paziente.reparto_id = nuovo_reparto_id
    paziente.posto_letto = nuovo_posto_letto


def elimina_paziente(paziente: Paziente, autore_id: int) -> None:
    """Eliminazione logica: il paziente sparisce, la riga resta.

    Il letto torna libero perché l'indice univoco vale solo sui RICOVERATI.
    Note, versioni e spunte restano nel database: senza il paziente non
    avrebbero più contesto, e le note devono poter risalire a chi le ha
    scritte anche a distanza di anni.
    """
    if paziente.stato == STATO_ELIMINATO:
        raise ErroreDiRegola("Questo paziente è già stato dimesso.")

    paziente.stato = STATO_ELIMINATO
    paziente.eliminato_il = adesso_utc()
    paziente.eliminato_da = autore_id


def data_arrivo_predefinita() -> date:
    """Oggi, secondo il calendario italiano."""
    return oggi_italia()
