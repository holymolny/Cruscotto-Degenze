"""Scadenza della sessione e obbligo di cambiare la password.

Due controlli che devono valere su <b>tutte</b> le pagine, non su quelle che
uno si ricorda di proteggere. Per questo stanno in un before_request: una
funzione che Flask esegue prima di ogni richiesta, qualunque sia la pagina.
"""

from __future__ import annotations

from flask import Flask, flash, redirect, request, session, url_for
from flask_login import current_user, logout_user

from app.formati import adesso_utc

CHIAVE_ULTIMA_ATTIVITA = "ultima_attivita"

# Pagine raggiungibili anche da chi deve ancora cambiare la password.
# Senza queste eccezioni l'utente verrebbe rimandato al cambio password
# all'infinito, compresa la pagina del cambio password stessa.
ENDPOINT_SEMPRE_PERMESSI = {
    "auth.cambio_password",
    "auth.logout",
    "auth.login",
    "static",
}


def segna_attivita() -> None:
    """Annota nella sessione il momento dell'ultima richiesta.

    La sessione di Flask è un cookie firmato: il contenuto viaggia nel
    browser, ma è firmato con la SECRET_KEY, quindi l'utente non può
    modificarlo senza che il server se ne accorga.
    """
    session.permanent = True
    session[CHIAVE_ULTIMA_ATTIVITA] = adesso_utc().timestamp()


def registra_controlli_sessione(app: Flask) -> None:
    """Attacca all'applicazione i due controlli. Chiamata da create_app()."""

    @app.before_request
    def scadenza_per_inattivita():
        """Disconnette chi non tocca il programma da troppo tempo.

        I PC di reparto sono condivisi e restano accesi tutto il giorno: se
        qualcuno si allontana senza uscire, il collega successivo si
        ritroverebbe collegato con il nome del primo, e le note finirebbero
        firmate dalla persona sbagliata.
        """
        if not current_user.is_authenticated:
            return None

        limite_minuti = app.config["MINUTI_INATTIVITA"]
        ultima = session.get(CHIAVE_ULTIMA_ATTIVITA)

        if ultima is not None:
            inattivo_da = adesso_utc().timestamp() - ultima
            if inattivo_da > limite_minuti * 60:
                logout_user()
                session.clear()
                flash(
                    f"Sessione scaduta dopo {limite_minuti} minuti di inattività. "
                    "Accedi di nuovo.",
                    "avviso",
                )
                return redirect(url_for("auth.login"))

        # Ogni richiesta fa ripartire il conto: sono 15 minuti di inattività,
        # non 15 minuti di collegamento.
        segna_attivita()
        return None

    @app.before_request
    def obbligo_cambio_password():
        """Chi ha una password temporanea non può usare il resto del programma.

        Serve perché la password temporanea l'ha scelta l'amministratore, e
        finché resta quella l'amministratore può entrare al posto suo — e le
        note risulterebbero scritte dall'utente.
        """
        if not current_user.is_authenticated:
            return None
        if not current_user.deve_cambiare_password:
            return None
        if request.endpoint in ENDPOINT_SEMPRE_PERMESSI:
            return None

        return redirect(url_for("auth.cambio_password"))
