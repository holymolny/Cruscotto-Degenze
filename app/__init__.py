"""Cruscotto Degenze — costruzione dell'applicazione.

Qui vive create_app(), la "fabbrica" che costruisce l'oggetto Flask.
Usiamo una fabbrica invece di una variabile globale perché così possiamo
costruire applicazioni diverse a partire dallo stesso codice: una per lo
sviluppo con SQLite, una per i test con un database usa-e-getta, una per la
produzione su SQL Server.
"""

from __future__ import annotations

import os

from flask import Flask, render_template

from app.comandi import registra_comandi
from app.config import CONFIGURAZIONI
from app.estensioni import csrf, db, login_manager, migrate
from app.sessione import registra_controlli_sessione


def create_app(nome_configurazione: str | None = None) -> Flask:
    """Costruisce e restituisce l'applicazione Flask pronta all'uso."""
    app = Flask(__name__)

    nome_configurazione = nome_configurazione or os.environ.get("FLASK_CONFIG", "sviluppo")
    if nome_configurazione not in CONFIGURAZIONI:
        raise RuntimeError(
            f"FLASK_CONFIG vale '{nome_configurazione}', ma i valori ammessi sono: "
            + ", ".join(CONFIGURAZIONI)
        )
    app.config.from_object(CONFIGURAZIONI[nome_configurazione])

    # Meglio fermarsi subito all'avvio che scoprire in reparto che le sessioni
    # sono firmate con una chiave di ripiego.
    if nome_configurazione == "produzione" and not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY mancante nel file .env: in produzione è obbligatoria.")

    _collega_estensioni(app)
    _registra_blueprint(app)
    _registra_intestazioni_sicurezza(app)
    _registra_pagine_errore(app)
    _registra_aiuti_template(app)

    registra_controlli_sessione(app)
    registra_comandi(app)

    return app


def _collega_estensioni(app: Flask) -> None:
    """Attacca all'applicazione le estensioni create in estensioni.py."""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Import necessario anche se qui non usiamo i nomi: serve a far eseguire
    # models.py, così le tabelle si registrano su db.metadata. Senza questa
    # riga "flask db migrate" non troverebbe nulla da creare.
    from app import models  # noqa: F401

    # Dove mandare chi apre una pagina riservata senza essere collegato.
    login_manager.login_view = "auth.login"
    # Nessun messaggio: chi arriva qui si trova già davanti alla pagina di
    # accesso, e spiegargli che deve accedere è superfluo. Con login_message
    # vuoto Flask-Login salta il riquadro e non lo mostra affatto.
    login_manager.login_message = None

    @login_manager.user_loader
    def carica_utente(id_utente: str):
        """Ricostruisce l'utente a ogni richiesta, partendo dal suo id.

        Nel cookie di sessione c'è solo l'id, non l'utente intero: se
        cambiassimo il ruolo di qualcuno, la modifica avrebbe effetto dalla
        richiesta successiva, senza bisogno che rifaccia l'accesso.
        """
        return db.session.get(models.Utente, int(id_utente))


def _registra_blueprint(app: Flask) -> None:
    """Innesta nell'applicazione le aree in cui è diviso il programma."""
    from app.agenda import agenda_bp
    from app.auth import auth_bp
    from app.pazienti import pazienti_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pazienti_bp)
    app.register_blueprint(agenda_bp)


def _registra_aiuti_template(app: Flask) -> None:
    """Rende disponibili ai template alcune funzioni e costanti.

    Senza questo, ogni route dovrebbe passare utente_puo() al template che ne
    ha bisogno: con venti pagine diventerebbe una ripetizione continua.
    """
    from app import permessi
    from app.agenda import servizi as servizi_agenda
    from app.formati import a_ora_italiana, data_italiana, oggi_italia

    def momento_italiano(momento, se_manca: str = "mai") -> str:
        """Una data e ora in formato gg/mm/aaaa hh:mm, in ora italiana."""
        locale = a_ora_italiana(momento)
        return se_manca if locale is None else locale.strftime("%d/%m/%Y %H:%M")

    def etichetta_ruolo_nota(ruolo: str) -> str:
        """«Medico», «Infermiere» — come si firma una nota."""
        return servizi_agenda.FIRMA_RUOLO.get(ruolo, ruolo)

    app.jinja_env.globals.update(
        utente_puo=permessi.utente_puo,
        data_italiana=data_italiana,
        momento_italiano=momento_italiano,
        a_ora_italiana=a_ora_italiana,
        oggi_italia=oggi_italia,
        etichetta_ruolo_nota=etichetta_ruolo_nota,
        intestazione_giorno=servizi_agenda.intestazione_giorno,
        GESTIRE_UTENTI=permessi.GESTIRE_UTENTI,
        SCARICARE_PDF=permessi.SCARICARE_PDF,
        SCRIVERE_NOTE=permessi.SCRIVERE_NOTE,
        CAMBIARE_GRAVITA=permessi.CAMBIARE_GRAVITA,
        INSERIRE_PAZIENTE=permessi.INSERIRE_PAZIENTE,
        MODIFICARE_DIMISSIONE=permessi.MODIFICARE_DIMISSIONE,
        ELIMINARE_PAZIENTE=permessi.ELIMINARE_PAZIENTE,
        SPOSTARE_PAZIENTE=permessi.SPOSTARE_PAZIENTE,
        SPUNTARE_CHECKLIST=permessi.SPUNTARE_CHECKLIST,
    )


def _registra_pagine_errore(app: Flask) -> None:
    """Pagine di errore in italiano, senza dettagli tecnici."""

    @app.errorhandler(403)
    def non_consentito(errore):
        return render_template("errori/403.html"), 403

    @app.errorhandler(404)
    def non_trovato(errore):
        return render_template("errori/404.html"), 404

    @app.errorhandler(500)
    def errore_interno(errore):
        # La sessione va annullata: se l'errore è avvenuto a metà di un
        # salvataggio, restano modifiche in sospeso che non devono finire nel
        # database per sbaglio alla richiesta successiva.
        db.session.rollback()
        return render_template("errori/500.html"), 500


def _registra_intestazioni_sicurezza(app: Flask) -> None:
    """Aggiunge le intestazioni HTTP di sicurezza a ogni risposta.

    La Content-Security-Policy vale anche come promemoria tecnico: consente
    solo risorse servite da questo stesso sito, quindi se per distrazione
    qualcuno aggiungesse un riferimento a una CDN smetterebbe di funzionare
    subito qui in sviluppo, invece che in reparto senza internet.
    """

    @app.after_request
    def aggiungi_intestazioni(risposta):
        # Il browser non deve indovinare il tipo di un file: se diciamo che è
        # testo, lo tratta come testo e non come programma da eseguire.
        risposta.headers["X-Content-Type-Options"] = "nosniff"
        # Nessun altro sito può incorniciare il Cruscotto dentro una sua pagina.
        risposta.headers["X-Frame-Options"] = "DENY"
        risposta.headers["Referrer-Policy"] = "same-origin"
        risposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'"
        )
        return risposta
