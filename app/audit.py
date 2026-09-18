"""Il registro accessi: chi ha fatto cosa, quando e da quale PC.

Regola della tabella: <b>si scrive soltanto</b>. Il programma non modifica e
non cancella mai un evento già registrato. In Fase 2 lo garantirà anche SQL
Server, negando UPDATE e DELETE al login usato dall'applicazione: così la
regola vale anche se un domani un bug provasse a violarla.

Regola sulla privacy: nel campo «dettagli» non finisce mai il testo di una
nota. Il registro serve a sapere che alle 14:32 Carlo Bianchi ha modificato
la nota 87, non a raccontare una seconda volta cosa c'era scritto.
"""

from __future__ import annotations

from flask import has_request_context, request
from flask_login import current_user

from app.estensioni import db
from app.models import EventoAudit

# --------------------------------------------------------------------------
# I nomi delle azioni, scritti una volta sola per non sbagliarli a memoria.
# --------------------------------------------------------------------------
LOGIN_OK = "LOGIN_OK"
LOGIN_FALLITO = "LOGIN_FALLITO"
LOGOUT = "LOGOUT"
PAZIENTE_CREATO = "PAZIENTE_CREATO"
PAZIENTE_ELIMINATO = "PAZIENTE_ELIMINATO"
PAZIENTE_SPOSTATO = "PAZIENTE_SPOSTATO"
DIMISSIONE_MODIFICATA = "DIMISSIONE_MODIFICATA"
GRAVITA_MODIFICATA = "GRAVITA_MODIFICATA"
NOTA_CREATA = "NOTA_CREATA"
NOTA_MODIFICATA = "NOTA_MODIFICATA"
NOTA_ELIMINATA = "NOTA_ELIMINATA"
PDF_SCARICATO = "PDF_SCARICATO"
UTENTE_CREATO = "UTENTE_CREATO"
UTENTE_MODIFICATO = "UTENTE_MODIFICATO"
PASSWORD_REIMPOSTATA = "PASSWORD_REIMPOSTATA"
PASSWORD_CAMBIATA = "PASSWORD_CAMBIATA"

# Etichette per la pagina di consultazione del registro (passo 8).
ETICHETTE_AZIONI = {
    LOGIN_OK: "Accesso riuscito",
    LOGIN_FALLITO: "Accesso fallito",
    LOGOUT: "Uscita",
    PAZIENTE_CREATO: "Paziente inserito",
    PAZIENTE_ELIMINATO: "Paziente dimesso",
    PAZIENTE_SPOSTATO: "Paziente spostato di reparto",
    DIMISSIONE_MODIFICATA: "Dimissione presunta modificata",
    GRAVITA_MODIFICATA: "Gravità modificata",
    NOTA_CREATA: "Nota scritta",
    NOTA_MODIFICATA: "Nota modificata",
    NOTA_ELIMINATA: "Nota eliminata",
    PDF_SCARICATO: "PDF scaricato",
    UTENTE_CREATO: "Utente creato",
    UTENTE_MODIFICATO: "Utente modificato",
    PASSWORD_REIMPOSTATA: "Password reimpostata",
    PASSWORD_CAMBIATA: "Password cambiata",
}

LUNGHEZZA_MASSIMA_DETTAGLI = 255


def indirizzo_client() -> str:
    """L'indirizzo IP del PC che ha fatto la richiesta.

    In Fase 2 le richieste arrivano da IIS, non direttamente dal PC di
    reparto: senza accorgimenti il registro riporterebbe sempre 127.0.0.1.
    Per questo IIS inoltrerà l'header X-Forwarded-For e Flask lo leggerà con
    ProxyFix, che rimette request.remote_addr al valore giusto.
    """
    if not has_request_context():
        # Succede nei comandi da terminale: non c'è nessun PC che chiama.
        return "terminale"
    return request.remote_addr or "sconosciuto"


def registra_evento(
    azione: str,
    *,
    utente=None,
    username_tentato: str | None = None,
    entita: str | None = None,
    entita_id: int | None = None,
    dettagli: str | None = None,
) -> EventoAudit:
    """Aggiunge un evento al registro.

    <b>Non fa il commit</b>: aggiunge soltanto alla sessione. Così l'evento e
    l'operazione che descrive vengono salvati insieme, in un colpo solo. Se
    l'operazione fallisce a metà, non resta nel registro la traccia di una
    cosa che non è mai successa.

    L'utente si può indicare esplicitamente: serve al login, dove nel momento
    in cui registriamo l'evento la sessione non è ancora aperta.
    """
    if utente is None and current_user and current_user.is_authenticated:
        utente = current_user

    if dettagli is not None and len(dettagli) > LUNGHEZZA_MASSIMA_DETTAGLI:
        # Meglio un dettaglio troncato che un errore del database in faccia
        # all'utente mentre sta salvando una nota.
        dettagli = dettagli[: LUNGHEZZA_MASSIMA_DETTAGLI - 1] + "…"

    evento = EventoAudit(
        utente_id=utente.id if utente is not None else None,
        username_tentato=username_tentato,
        azione=azione,
        entita=entita,
        entita_id=entita_id,
        dettagli=dettagli,
        indirizzo_ip=indirizzo_client(),
    )
    db.session.add(evento)
    return evento
