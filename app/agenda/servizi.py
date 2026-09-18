"""Le regole dell'Agenda: note e checklist di dimissione."""

from __future__ import annotations

from datetime import date

from app.estensioni import db
from app.formati import adesso_utc, oggi_italia
from app.models import (
    ChecklistSpunta,
    Nota,
    NotaVersione,
    Paziente,
    Utente,
    VoceChecklist,
)

LUNGHEZZA_MASSIMA_NOTA = 2000

# Come si firma una nota, per ruolo. Solo tre ruoli possono scrivere, quindi
# solo tre compaiono qui.
FIRMA_RUOLO = {
    "ADMIN": "Amministratore",
    "MEDICO": "Medico",
    "INFERMIERE": "Infermiere",
}


class ErroreDiRegola(Exception):
    """Una regola dell'Agenda è stata violata. Il messaggio è già in italiano."""


def etichetta_firma(ruolo: str, nome: str) -> str:
    """«Medico: Mario Rossi» — come compare in testa a ogni nota."""
    return f"{FIRMA_RUOLO.get(ruolo, ruolo)}: {nome}"


# --------------------------------------------------------------------------
# Lettura delle note
# --------------------------------------------------------------------------
def note_visibili(paziente_id: int) -> list[Nota]:
    """Le note non eliminate, dalla più recente alla più vecchia.

    A parità di giorno viene prima quella inserita dopo: si ordina anche per
    id decrescente. L'id cresce a ogni inserimento, quindi fa da orologio
    anche quando due note portano la stessa data.
    """
    return (
        db.session.query(Nota)
        .filter(Nota.paziente_id == paziente_id, Nota.eliminata.is_(False))
        .order_by(Nota.data_nota.desc(), Nota.id.desc())
        .all()
    )


def conta_note_visibili(paziente_id: int) -> int:
    return (
        db.session.query(Nota)
        .filter(Nota.paziente_id == paziente_id, Nota.eliminata.is_(False))
        .count()
    )


def raggruppa_per_giorno(note: list[Nota]) -> list[tuple[date, list[Nota]]]:
    """Raggruppa le note sotto l'intestazione del loro giorno.

    Le note arrivano già ordinate, quindi basta scorrerle una volta e aprire
    un gruppo nuovo ogni volta che la data cambia. Non serve ordinare di
    nuovo né usare un dizionario.
    """
    gruppi: list[tuple[date, list[Nota]]] = []
    for nota in note:
        if gruppi and gruppi[-1][0] == nota.data_nota:
            gruppi[-1][1].append(nota)
        else:
            gruppi.append((nota.data_nota, [nota]))
    return gruppi


def intestazione_giorno(giorno: date) -> str:
    """«Oggi, 18/09/2026» per la data di oggi, altrimenti solo la data."""
    formattata = giorno.strftime("%d/%m/%Y")
    return f"Oggi, {formattata}" if giorno == oggi_italia() else formattata


# --------------------------------------------------------------------------
# Scrittura delle note
# --------------------------------------------------------------------------
def _controlla_testo(testo: str) -> str:
    pulito = (testo or "").strip()
    if not pulito:
        raise ErroreDiRegola("Il testo della nota non può essere vuoto.")
    if len(pulito) > LUNGHEZZA_MASSIMA_NOTA:
        raise ErroreDiRegola(
            f"La nota non può superare {LUNGHEZZA_MASSIMA_NOTA} caratteri."
        )
    return pulito


def crea_nota(paziente: Paziente, autore: Utente, testo: str) -> Nota:
    """Scrive una nota nuova. Non fa il commit.

    Nome e ruolo dell'autore vengono copiati dentro la nota adesso, e non
    letti dall'utente ogni volta che la nota viene mostrata: se un domani
    Carlo Bianchi da infermiere diventasse medico, questa nota deve restare
    firmata «Infermiere: Carlo Bianchi». Una firma racconta com'erano le cose
    quel giorno.
    """
    nota = Nota(
        paziente_id=paziente.id,
        autore_id=autore.id,
        autore_nome=autore.nome_completo,
        autore_ruolo=autore.ruolo,
        testo=_controlla_testo(testo),
        # Data italiana: una nota scritta all'una di notte del 17 deve
        # comparire sotto il 17, non sotto il 16.
        data_nota=oggi_italia(),
    )
    db.session.add(nota)
    return nota


def controlla_autore(nota: Nota, utente: Utente) -> None:
    """Solo l'autore può toccare la propria nota. Nemmeno l'ADMIN.

    Non è una svista: una nota è una dichiarazione firmata da una persona.
    Se un amministratore potesse riscriverla, la firma non varrebbe più
    niente, e in una struttura sanitaria è esattamente il contrario di quello
    che serve.
    """
    if nota.autore_id != utente.id:
        raise ErroreDiRegola("Solo chi ha scritto la nota può modificarla o eliminarla.")


def modifica_nota(nota: Nota, autore: Utente, nuovo_testo: str) -> None:
    """Cambia il testo di una nota, conservando quello precedente."""
    controlla_autore(nota, autore)
    if nota.eliminata:
        raise ErroreDiRegola("Questa nota è stata eliminata.")

    pulito = _controlla_testo(nuovo_testo)
    if pulito == nota.testo:
        return

    # Il testo vecchio va messo da parte prima di sovrascriverlo: in una
    # struttura sanitaria «la nota diceva un'altra cosa» non può restare una
    # questione di parola contro parola.
    db.session.add(
        NotaVersione(
            nota_id=nota.id,
            testo_precedente=nota.testo,
            sostituito_da=autore.id,
        )
    )
    nota.testo = pulito
    nota.modificata_il = adesso_utc()


def elimina_nota(nota: Nota, autore: Utente) -> None:
    """Eliminazione logica: sparisce da Agenda e PDF, resta nel database."""
    controlla_autore(nota, autore)
    if nota.eliminata:
        raise ErroreDiRegola("Questa nota è già stata eliminata.")

    nota.eliminata = True
    nota.eliminata_il = adesso_utc()
    nota.eliminata_da = autore.id


# --------------------------------------------------------------------------
# Checklist di dimissione
# --------------------------------------------------------------------------
def voci_checklist() -> list[VoceChecklist]:
    return (
        db.session.query(VoceChecklist)
        .filter_by(attiva=True)
        .order_by(VoceChecklist.ordine)
        .all()
    )


def codici_spuntati(paziente_id: int) -> set[str]:
    """I codici delle voci spuntate per questo paziente.

    Un insieme e non una lista: nel template si controlla una voce alla
    volta, e la ricerca in un insieme è immediata.
    """
    righe = (
        db.session.query(ChecklistSpunta.voce_codice)
        .filter_by(paziente_id=paziente_id)
        .all()
    )
    return {codice for (codice,) in righe}


def imposta_spunta(paziente: Paziente, codice: str, spuntata: bool) -> int:
    """Mette o toglie una spunta. Restituisce il nuovo totale.

    Non si registra chi ha spuntato né quando: la specifica lo esclude
    esplicitamente. La checklist è uno strumento di lavoro condiviso del
    reparto, non un registro di responsabilità individuali.
    """
    voce = db.session.get(VoceChecklist, codice)
    if voce is None or not voce.attiva:
        raise ErroreDiRegola("Voce della checklist non valida.")

    esistente = db.session.get(ChecklistSpunta, (paziente.id, codice))

    if spuntata and esistente is None:
        db.session.add(ChecklistSpunta(paziente_id=paziente.id, voce_codice=codice))
    elif not spuntata and esistente is not None:
        # L'unica cancellazione fisica del programma, ed è voluta: la riga
        # <i>è</i> la spunta, quindi togliere la spunta significa toglierla.
        db.session.delete(esistente)

    db.session.flush()
    return (
        db.session.query(ChecklistSpunta).filter_by(paziente_id=paziente.id).count()
    )
