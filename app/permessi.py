"""Chi può fare cosa: la matrice dei permessi, scritta in un punto solo.

Tutto il programma chiede qui il permesso di fare qualcosa. Il vantaggio è
che per rispondere alla domanda «un OSS può scaricare il PDF?» si guarda una
tabella sola, invece di cercare i controlli sparsi per venti file.

Regola non negoziabile: <b>ogni permesso va verificato sul server</b>.
Nascondere un pulsante serve a non confondere l'utente, non a impedire
l'azione: chi conosce l'indirizzo può sempre provare a chiamarlo a mano.
Per questo ogni route protetta porta il decoratore @richiede_permesso, che
risponde 403 a chi non ha diritto.
"""

from __future__ import annotations

from functools import wraps

from flask import abort
from flask_login import current_user

from app.models import (
    RUOLO_ADMIN,
    RUOLO_AMMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
)

# --------------------------------------------------------------------------
# I permessi, uno per azione. Il nome è quello che si legge nelle route.
# --------------------------------------------------------------------------
SCRIVERE_NOTE = "scrivere_note"
SPUNTARE_CHECKLIST = "spuntare_checklist"
CAMBIARE_GRAVITA = "cambiare_gravita"
INSERIRE_PAZIENTE = "inserire_paziente"
MODIFICARE_DIMISSIONE = "modificare_dimissione"
ELIMINARE_PAZIENTE = "eliminare_paziente"
SPOSTARE_PAZIENTE = "spostare_paziente"
SCARICARE_PDF = "scaricare_pdf"
GESTIRE_UTENTI = "gestire_utenti"
VEDERE_REGISTRO = "vedere_registro"

# Vedere la home, l'Agenda e la checklist non compare qui: lo possono fare
# tutti i ruoli, quindi basta essere collegati.

PERMESSI: dict[str, frozenset[str]] = {
    RUOLO_ADMIN: frozenset(
        {
            SCRIVERE_NOTE,
            SPUNTARE_CHECKLIST,
            CAMBIARE_GRAVITA,
            INSERIRE_PAZIENTE,
            MODIFICARE_DIMISSIONE,
            ELIMINARE_PAZIENTE,
            SPOSTARE_PAZIENTE,
            SCARICARE_PDF,
            GESTIRE_UTENTI,
            VEDERE_REGISTRO,
        }
    ),
    RUOLO_MEDICO: frozenset(
        {
            SCRIVERE_NOTE,
            SPUNTARE_CHECKLIST,
            CAMBIARE_GRAVITA,
            INSERIRE_PAZIENTE,
            MODIFICARE_DIMISSIONE,
            # Dimissione del paziente concordata con Micky: la specifica
            # iniziale la riservava all'ADMIN, ma in reparto il medico e
            # l'infermiere devono poter liberare un letto senza chiamare l'IT.
            ELIMINARE_PAZIENTE,
            SPOSTARE_PAZIENTE,
            SCARICARE_PDF,
        }
    ),
    RUOLO_INFERMIERE: frozenset(
        {
            SCRIVERE_NOTE,
            SPUNTARE_CHECKLIST,
            CAMBIARE_GRAVITA,
            INSERIRE_PAZIENTE,
            MODIFICARE_DIMISSIONE,
            ELIMINARE_PAZIENTE,
            SPOSTARE_PAZIENTE,
            SCARICARE_PDF,
        }
    ),
    # L'OSS consulta e basta: nemmeno il PDF, che conterrebbe tutte le note.
    RUOLO_OSS: frozenset(),
    # Amministrazione / IT consulta e può stampare, ma non scrive nulla di
    # clinico-organizzativo.
    RUOLO_AMMIN: frozenset({SCARICARE_PDF}),
}


def ha_permesso(ruolo: str, permesso: str) -> bool:
    """Risponde alla domanda «questo ruolo può fare questa cosa?»."""
    return permesso in PERMESSI.get(ruolo, frozenset())


def utente_puo(permesso: str) -> bool:
    """Come ha_permesso, ma riferito all'utente collegato adesso.

    Serve soprattutto ai template, per decidere se disegnare un pulsante.
    Nascondere il pulsante non sostituisce il controllo sul server: lo
    affianca soltanto.
    """
    if not current_user.is_authenticated:
        return False
    return ha_permesso(current_user.ruolo, permesso)


def richiede_permesso(permesso: str):
    """Decoratore che protegge una route.

    Si usa così:

        @pazienti_bp.route("/paziente/<int:id>/elimina", methods=["POST"])
        @login_required
        @richiede_permesso(ELIMINARE_PAZIENTE)
        def elimina(id):
            ...

    Chi non ha il permesso riceve 403 con una pagina in italiano, e non
    arriva mai dentro la funzione.
    """

    def decoratore(funzione):
        @wraps(funzione)
        def controllo(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not ha_permesso(current_user.ruolo, permesso):
                abort(403)
            return funzione(*args, **kwargs)

        return controllo

    return decoratore
