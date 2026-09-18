"""Configurazioni dell'applicazione.

Una classe per ogni situazione d'uso: sviluppo sul PC, esecuzione dei test,
produzione sulla macchina virtuale. La scelta avviene con la variabile
FLASK_CONFIG nel file .env, così lo stesso codice gira ovunque senza essere
modificato: cambia solo la configurazione.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Le variabili del file .env vanno lette QUI, prima delle classi qui sotto:
# Python esegue il corpo di una classe nel momento in cui importa il modulo,
# quindi se caricassimo il .env più tardi os.environ sarebbe ancora vuoto.
load_dotenv()

# Cartella che contiene "app". Costruiamo percorsi assoluti a partire da qui,
# così i comandi funzionano da qualunque directory venga lanciato il terminale.
RADICE = Path(__file__).resolve().parent.parent


class ConfigBase:
    """Impostazioni valide in tutte le situazioni."""

    NOME_STRUTTURA = "Casa di Cura Misericordia Navacchio"

    # Dice a quale delle tre situazioni stiamo girando. Serve ai comandi che
    # devono funzionare solo in sviluppo, come "flask dati-demo".
    # Non usiamo DEBUG per questo: il comando "flask" lo riscrive a False
    # quando carica l'applicazione, quindi non è affidabile.
    AMBIENTE = "sviluppo"

    SECRET_KEY = os.environ.get("SECRET_KEY", "")

    # SQLite in locale, SQL Server sulla VM: cambia solo questa variabile.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{RADICE / 'cruscotto.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # I PC di reparto sono condivisi e restano accesi tutto il giorno:
    # la sessione deve scadere da sola.
    MINUTI_INATTIVITA = int(os.environ.get("MINUTI_INATTIVITA", "15"))

    # Difesa contro chi prova password a raffica.
    TENTATIVI_MASSIMI = int(os.environ.get("TENTATIVI_MASSIMI", "5"))
    MINUTI_BLOCCO = int(os.environ.get("MINUTI_BLOCCO", "15"))

    # Quanto dura il cookie di sessione. È la stessa soglia dell'inattività:
    # il nostro controllo dà il messaggio in italiano, questo è la rete di
    # sicurezza sotto, che vale anche se il controllo non venisse eseguito.
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=MINUTI_INATTIVITA)
    # Ogni risposta rinnova la scadenza del cookie: sono minuti di
    # inattività, non minuti di collegamento.
    SESSION_REFRESH_EACH_REQUEST = True

    # HttpOnly: il cookie di sessione non è leggibile dal JavaScript della
    # pagina, quindi un eventuale script malevolo non può rubare la sessione.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False


class ConfigSviluppo(ConfigBase):
    """Fase 1: sviluppo sul PC Windows, database SQLite."""

    AMBIENTE = "sviluppo"
    DEBUG = True
    # In sviluppo una chiave di ripiego va bene: il database contiene dati
    # finti e il PC è tuo. In produzione invece la chiave è obbligatoria.
    SECRET_KEY = os.environ.get("SECRET_KEY") or "chiave-solo-per-sviluppo"


class ConfigTest(ConfigBase):
    """Esecuzione dei test automatici con pytest."""

    AMBIENTE = "test"
    TESTING = True
    SECRET_KEY = "chiave-per-i-test"
    # Database in memoria: nasce e muore insieme al singolo test, così i test
    # non si sporcano a vicenda e non toccano il database vero.
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    # I test chiamano le route direttamente, senza passare da un form del
    # browser: il token CSRF non avrebbe modo di essere generato.
    WTF_CSRF_ENABLED = False


class ConfigProduzione(ConfigBase):
    """Fase 2: macchina virtuale, SQL Server, IIS davanti."""

    AMBIENTE = "produzione"
    DEBUG = False
    # Dietro IIS il traffico è HTTPS: il cookie non deve mai viaggiare in chiaro.
    SESSION_COOKIE_SECURE = True


CONFIGURAZIONI = {
    "sviluppo": ConfigSviluppo,
    "test": ConfigTest,
    "produzione": ConfigProduzione,
}
