"""Date e orari: come si salvano e come si mostrano.

Regola del progetto: nel database si salva sempre in <b>UTC</b>, all'utente si
mostra sempre in ora italiana. Il motivo è l'ora legale. Se salvassimo l'ora
italiana, le note scritte alle 02:30 della notte in cui le lancette tornano
indietro esisterebbero due volte, e non ci sarebbe modo di sapere quale è
venuta prima. In UTC il tempo scorre sempre dritto.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

# Su Windows i fusi orari non sono inclusi in Python: li fornisce il
# pacchetto "tzdata", elencato in requirements.txt.
FUSO_ITALIA = ZoneInfo("Europe/Rome")


def adesso_utc() -> datetime:
    """Il momento attuale in UTC, senza l'indicazione del fuso.

    Perché "senza fuso": SQLite non sa memorizzare il fuso orario e SQL Server
    lo gestisce in modo diverso ancora. Salvando sempre un UTC "nudo" il dato
    è identico sui due database, e la conversione avviene solo al momento di
    mostrarlo.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def a_ora_italiana(momento: datetime | None) -> datetime | None:
    """Converte un momento salvato in UTC nell'ora italiana corrispondente."""
    if momento is None:
        return None
    return momento.replace(tzinfo=timezone.utc).astimezone(FUSO_ITALIA)


def oggi_italia() -> date:
    """La data di oggi secondo il calendario italiano.

    Serve per data_nota: una nota scritta all'una di notte del 17 deve
    risultare del 17, non del 16, anche se in UTC sono ancora le 23 del 16.
    """
    return datetime.now(FUSO_ITALIA).date()


def data_italiana(valore: date | None, se_manca: str = "da definire") -> str:
    """Formatta una data come gg/mm/aaaa, il formato usato in tutto il programma."""
    if valore is None:
        return se_manca
    return valore.strftime("%d/%m/%Y")
