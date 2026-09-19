"""Le regole sugli utenti, separate dalle pagine web.

Come per i pazienti: qui dentro non si parla di HTTP. Una regola come «non si
può disattivare l'ultimo amministratore» deve poter essere letta e provata
senza tirare in ballo form, richieste e redirect.

La regola più importante è proprio quella. Se il Cruscotto restasse senza
nemmeno un amministratore attivo, nessuno potrebbe più creare utenti né
riattivare nessuno: si rientrerebbe solo dal terminale, sulla macchina su cui
il programma è installato. Per questo l'ultimo amministratore non si può né
disattivare né retrocedere di ruolo.
"""

from __future__ import annotations

from app.auth.servizi import errore_nuova_password, sblocca
from app.estensioni import db
from app.models import (
    RUOLI,
    RUOLO_ADMIN,
    RUOLO_AMMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
    Utente,
)

LUNGHEZZA_MASSIMA_NOME = 80
LUNGHEZZA_MASSIMA_USERNAME = 50

# L'ordine in cui i ruoli compaiono nel menu a tendina. Non è quello di RUOLI
# in models.py, che comincia dall'amministratore: qui davanti mettiamo i ruoli
# che si assegnano tutti i giorni, e l'amministratore in fondo, dove si sceglie
# di rado e apposta.
RUOLI_ASSEGNABILI = [
    RUOLO_MEDICO,
    RUOLO_INFERMIERE,
    RUOLO_OSS,
    RUOLO_AMMIN,
    RUOLO_ADMIN,
]


class ErroreDiRegola(Exception):
    """Una regola del Cruscotto è stata violata.

    Il messaggio è già scritto in italiano per l'utente: la route deve solo
    mostrarlo, senza doverlo tradurre o interpretare.
    """


# --------------------------------------------------------------------------
# Lettura
# --------------------------------------------------------------------------
def elenco_utenti() -> list[Utente]:
    """Tutti gli utenti, attivi per primi e poi in ordine alfabetico.

    I disattivati restano in elenco, in fondo: servono a capire chi c'era e a
    poter riattivare qualcuno che torna dopo un'assenza.
    """
    return (
        db.session.query(Utente)
        .order_by(Utente.attivo.desc(), Utente.cognome, Utente.nome)
        .all()
    )


def utente_per_id(utente_id: int) -> Utente | None:
    return db.session.get(Utente, utente_id)


def amministratori_attivi() -> int:
    """Quanti amministratori attivi ci sono in tutto.

    Serve all'elenco: quando ne resta uno solo, i pulsanti che lo
    toglierebbero di mezzo vanno disegnati spenti. Il divieto vero resta
    comunque quello del server, qui sotto.
    """
    return (
        db.session.query(Utente)
        .filter(Utente.ruolo == RUOLO_ADMIN, Utente.attivo.is_(True))
        .count()
    )


def altri_amministratori_attivi(utente_id: int) -> int:
    """Quanti amministratori attivi ci sono oltre a questo."""
    return (
        db.session.query(Utente)
        .filter(
            Utente.ruolo == RUOLO_ADMIN,
            Utente.attivo.is_(True),
            Utente.id != utente_id,
        )
        .count()
    )


# --------------------------------------------------------------------------
# Controlli
# --------------------------------------------------------------------------
def _pulisci(testo: str, lunghezza_massima: int, nome_campo: str) -> str:
    """Toglie gli spazi ai bordi e controlla la lunghezza."""
    pulito = (testo or "").strip()
    if not pulito:
        raise ErroreDiRegola(f"{nome_campo} è obbligatorio.")
    if len(pulito) > lunghezza_massima:
        raise ErroreDiRegola(
            f"{nome_campo} non può superare {lunghezza_massima} caratteri."
        )
    return pulito


def _controlla_ruolo(ruolo: str) -> str:
    if ruolo not in RUOLI:
        raise ErroreDiRegola("Ruolo non valido.")
    return ruolo


def _controlla_username(username: str) -> str:
    """Normalizza il nome utente e verifica che sia libero.

    Serve solo alla creazione: il nome utente, una volta assegnato, non si
    cambia più. Vedi modifica_utente() per il perché.
    """
    grezzo = _pulisci(username, LUNGHEZZA_MASSIMA_USERNAME, "Il nome utente")

    if " " in grezzo:
        raise ErroreDiRegola(
            "Il nome utente non può contenere spazi. "
            "Di solito si usa l'iniziale del nome seguita dal cognome: mrossi."
        )

    pulito = Utente.normalizza_username(grezzo)

    if db.session.query(Utente).filter_by(username=pulito).first() is not None:
        raise ErroreDiRegola(f"Il nome utente «{pulito}» è già in uso.")

    return pulito


def _controlla_password(password: str) -> None:
    """Applica alle password scelte dall'amministratore gli stessi requisiti
    che valgono quando un utente se la cambia da sé.

    Sarebbe incoerente pretendere una lettera e un numero all'utente e
    accettare «12345678» da chi glieli assegna.
    """
    errore = errore_nuova_password(password)
    if errore:
        raise ErroreDiRegola(errore)


def _controlla_non_e_se_stesso(utente: Utente, autore: Utente, messaggio: str) -> None:
    """Il messaggio arriva già scritto per intero.

    Provare a comporlo da un pezzo di frase produceva risultati come «Non puoi
    cambiare ruolo al il tuo stesso account»: l'italiano fonde preposizione e
    articolo, e una formula unica non regge per tutti i verbi.
    """
    if utente.id == autore.id:
        raise ErroreDiRegola(messaggio)


def _controlla_non_ultimo_admin(utente: Utente, motivo: str) -> None:
    """Impedisce di restare senza amministratori attivi."""
    if utente.ruolo != RUOLO_ADMIN or not utente.attivo:
        return
    if altri_amministratori_attivi(utente.id) == 0:
        raise ErroreDiRegola(
            f"{utente.nome_completo} è l'unico amministratore attivo: "
            f"non si può {motivo}. Creane prima un altro."
        )


# --------------------------------------------------------------------------
# Operazioni
# --------------------------------------------------------------------------
def crea_utente(
    *,
    nome: str,
    cognome: str,
    username: str,
    ruolo: str,
    password: str,
    autore: Utente,
) -> Utente:
    """Crea un account. Non fa il commit."""
    nome = _pulisci(nome, LUNGHEZZA_MASSIMA_NOME, "Il nome")
    cognome = _pulisci(cognome, LUNGHEZZA_MASSIMA_NOME, "Il cognome")
    username = _controlla_username(username)
    ruolo = _controlla_ruolo(ruolo)
    _controlla_password(password)

    utente = Utente(
        username=username,
        nome=nome,
        cognome=cognome,
        ruolo=ruolo,
        attivo=True,
        # La password l'ha scelta l'amministratore, non l'interessato: al
        # primo accesso deve sostituirla con una che sappia solo lui.
        deve_cambiare_password=True,
        creato_da=autore.id,
    )
    utente.imposta_password(password)
    db.session.add(utente)
    return utente


def modifica_utente(
    utente: Utente, *, nome: str, cognome: str, ruolo: str, autore: Utente
) -> None:
    """Cambia nome, cognome e ruolo. Il nome utente non si tocca.

    Il nome utente resta quello di sempre di proposito: compare nel registro
    accessi di tutte le operazioni già fatte, e cambiarlo renderebbe quelle
    righe difficili da attribuire.
    """
    nome = _pulisci(nome, LUNGHEZZA_MASSIMA_NOME, "Il nome")
    cognome = _pulisci(cognome, LUNGHEZZA_MASSIMA_NOME, "Il cognome")
    ruolo = _controlla_ruolo(ruolo)

    if ruolo != utente.ruolo:
        _controlla_non_e_se_stesso(
            utente, autore, "Non puoi cambiare ruolo al tuo stesso account."
        )
        _controlla_non_ultimo_admin(utente, "togliergli il ruolo di amministratore")

    utente.nome = nome
    utente.cognome = cognome
    utente.ruolo = ruolo


def disattiva(utente: Utente, autore: Utente) -> None:
    """Toglie l'accesso senza cancellare nulla."""
    if not utente.attivo:
        raise ErroreDiRegola(f"{utente.nome_completo} è già disattivato.")

    _controlla_non_e_se_stesso(
        utente, autore, "Non puoi disattivare il tuo stesso account."
    )
    _controlla_non_ultimo_admin(utente, "disattivarlo")

    utente.attivo = False


def riattiva(utente: Utente) -> None:
    """Ridà l'accesso a chi era stato disattivato.

    Si toglie anche l'eventuale blocco per tentativi falliti: chi rientra
    dopo mesi non deve trovare la porta chiusa per un blocco di allora.
    """
    if utente.attivo:
        raise ErroreDiRegola(f"{utente.nome_completo} è già attivo.")

    utente.attivo = True
    sblocca(utente)


def reimposta_password(utente: Utente, nuova: str) -> None:
    """L'amministratore assegna una password nuova a chi l'ha dimenticata.

    Non può leggere quella vecchia — nel database c'è solo l'impronta — quindi
    l'unica strada è sostituirla. L'interessato dovrà cambiarla al primo
    accesso: una password che conosce anche l'amministratore non è personale.
    """
    _controlla_password(nuova)

    utente.imposta_password(nuova)
    utente.deve_cambiare_password = True
    # Chi chiede una password nuova ha quasi sempre già sbagliato cinque volte
    # la vecchia, e si ritroverebbe bloccato proprio adesso.
    sblocca(utente)


def sblocca_account(utente: Utente) -> None:
    """Toglie il blocco scattato dopo cinque tentativi falliti.

    Il come sta in auth/servizi.py, insieme alla regola che fa scattare il
    blocco: le due cose vanno lette vicine, e duplicare qui le due righe
    significherebbe doversi ricordare di cambiarle in due posti.
    """
    sblocca(utente)
