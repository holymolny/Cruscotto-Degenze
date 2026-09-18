"""Le regole dell'accesso, separate dalle pagine web.

Perché in un file a parte e non dentro routes.py? Perché una regola come
«dopo 5 tentativi falliti l'account si blocca» non ha niente a che vedere con
l'HTTP: deve poter essere letta, capita e provata senza tirare in ballo form,
richieste e redirect. I test di questo file, infatti, non aprono nessuna
pagina.
"""

from __future__ import annotations

import re
from datetime import timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from app.estensioni import db
from app.formati import adesso_utc
from app.models import Utente

# Messaggio unico per ogni accesso rifiutato, qualunque sia il motivo:
# utente inesistente, password sbagliata, account disattivato o bloccato.
# Se cambiasse a seconda del caso, chi prova nomi a caso capirebbe quali
# esistono davvero.
ERRORE_ACCESSO = "Nome utente o password non corretti."

LUNGHEZZA_MINIMA_PASSWORD = 8


class EsitoAccesso:
    """Il risultato di un tentativo di accesso.

    Una classetta invece di una tupla: leggere `esito.riuscito` è più chiaro
    di ricordarsi che il primo elemento era l'utente e il secondo l'errore.
    """

    def __init__(self, utente: Utente | None, errore: str | None):
        self.utente = utente
        self.errore = errore

    @property
    def riuscito(self) -> bool:
        return self.utente is not None


def tenta_accesso(username: str, password: str) -> EsitoAccesso:
    """Verifica le credenziali e aggiorna i contatori dell'utente.

    Non fa il commit e non apre la sessione: di quello si occupa la route.
    Qui si decide soltanto se le credenziali vanno bene e si tiene il conto
    dei tentativi.
    """
    username_pulito = Utente.normalizza_username(username)
    utente = db.session.query(Utente).filter_by(username=username_pulito).first()

    if utente is None:
        # Calcoliamo comunque un'impronta, buttandola via. Serve a far durare
        # un nome utente inesistente quanto uno esistente: altrimenti chi
        # cronometra le risposte capirebbe quali account esistono.
        generate_password_hash(password)
        return EsitoAccesso(None, ERRORE_ACCESSO)

    if account_bloccato(utente):
        return EsitoAccesso(None, ERRORE_ACCESSO)

    if not utente.attivo:
        return EsitoAccesso(None, ERRORE_ACCESSO)

    if not utente.password_corretta(password):
        _registra_tentativo_fallito(utente)
        return EsitoAccesso(None, ERRORE_ACCESSO)

    # Accesso riuscito: si azzera tutto e si annota il momento.
    utente.tentativi_falliti = 0
    utente.bloccato_fino = None
    utente.ultimo_accesso = adesso_utc()
    return EsitoAccesso(utente, None)


def account_bloccato(utente: Utente) -> bool:
    """Vero se l'account è ancora dentro i 15 minuti di blocco."""
    if utente.bloccato_fino is None:
        return False
    return utente.bloccato_fino > adesso_utc()


def _registra_tentativo_fallito(utente: Utente) -> None:
    """Incrementa il contatore e blocca l'account se ha superato il limite."""
    massimo = current_app.config["TENTATIVI_MASSIMI"]
    minuti = current_app.config["MINUTI_BLOCCO"]

    utente.tentativi_falliti = (utente.tentativi_falliti or 0) + 1

    if utente.tentativi_falliti >= massimo:
        utente.bloccato_fino = adesso_utc() + timedelta(minutes=minuti)
        # Azzerato di proposito: passati i 15 minuti l'utente ha di nuovo
        # cinque tentativi, non uno solo.
        utente.tentativi_falliti = 0


def sblocca(utente: Utente) -> None:
    """Toglie il blocco a un account. Lo usa l'ADMIN dalla gestione utenti."""
    utente.bloccato_fino = None
    utente.tentativi_falliti = 0


def errore_nuova_password(nuova: str, password_attuale: str | None = None) -> str | None:
    """Controlla che una nuova password rispetti i requisiti.

    Restituisce il messaggio d'errore, oppure None se va bene.

    I requisiti sono quelli della specifica: almeno 8 caratteri, almeno una
    lettera e un numero, diversa da quella precedente. Sono volutamente
    modesti: in reparto le password si digitano in fretta, e una regola troppo
    severa finisce scritta su un foglietto attaccato al monitor.
    """
    if len(nuova) < LUNGHEZZA_MINIMA_PASSWORD:
        return f"La password deve avere almeno {LUNGHEZZA_MINIMA_PASSWORD} caratteri."

    if not re.search(r"[A-Za-zÀ-ÿ]", nuova):
        return "La password deve contenere almeno una lettera."

    if not re.search(r"\d", nuova):
        return "La password deve contenere almeno un numero."

    if password_attuale is not None and nuova == password_attuale:
        return "La nuova password deve essere diversa da quella attuale."

    return None


def cambia_password(utente: Utente, nuova: str) -> None:
    """Imposta la nuova password e toglie l'obbligo di cambiarla."""
    utente.imposta_password(nuova)
    utente.deve_cambiare_password = False
