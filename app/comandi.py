"""Comandi da lanciare nel terminale, non dal browser.

Si registrano su Flask e si usano così:

    flask crea-admin
    flask dati-demo

Servono per le operazioni che non hanno senso come pagina web: il primo
amministratore non può crearlo nessuno dall'interno del programma, perché per
entrare nel programma bisogna già essere qualcuno.
"""

from __future__ import annotations

import click
from flask import Flask

from app.dati_fissi import REPARTI, VOCI_CHECKLIST
from app.estensioni import db
from app.formati import oggi_italia
from app.models import (
    RUOLO_ADMIN,
    RUOLO_AMMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
    STATO_RICOVERATO,
    ChecklistSpunta,
    Nota,
    Paziente,
    Reparto,
    Utente,
    VoceChecklist,
)

LUNGHEZZA_MINIMA_PASSWORD = 8


def registra_comandi(app: Flask) -> None:
    """Attacca i comandi all'applicazione. Chiamata da create_app()."""
    app.cli.add_command(crea_admin)
    app.cli.add_command(dati_demo)
    app.cli.add_command(controlla_dati_fissi)


@click.command("crea-admin")
@click.option("--nome", prompt="Nome", help="Nome di battesimo.")
@click.option("--cognome", prompt="Cognome", help="Cognome.")
@click.option("--username", prompt="Nome utente", help="Nome usato per accedere.")
@click.option(
    "--password",
    prompt="Password",
    hide_input=True,
    confirmation_prompt=True,
    help="Almeno 8 caratteri.",
)
def crea_admin(nome: str, cognome: str, username: str, password: str) -> None:
    """Crea il primo amministratore del Cruscotto.

    Va lanciato una volta sola, subito dopo l'installazione. Da qui in avanti
    tutti gli altri utenti si creano dalla pagina Gestione utenti.
    """
    nome = nome.strip()
    cognome = cognome.strip()
    username_pulito = Utente.normalizza_username(username)

    if not nome or not cognome or not username_pulito:
        raise click.ClickException("Nome, cognome e nome utente non possono essere vuoti.")

    if len(password) < LUNGHEZZA_MINIMA_PASSWORD:
        raise click.ClickException(
            f"La password deve avere almeno {LUNGHEZZA_MINIMA_PASSWORD} caratteri."
        )

    if db.session.query(Utente).filter_by(username=username_pulito).first():
        raise click.ClickException(f"Il nome utente «{username_pulito}» esiste già.")

    amministratore = Utente(
        username=username_pulito,
        nome=nome,
        cognome=cognome,
        ruolo=RUOLO_ADMIN,
        attivo=True,
        # Il cambio obbligatorio serve quando la password l'ha scelta qualcun
        # altro per te. Qui la scegli tu, in un terminale, quindi non serve.
        deve_cambiare_password=False,
        creato_da=None,  # non c'era nessuno prima di lui
    )
    amministratore.imposta_password(password)

    db.session.add(amministratore)
    db.session.commit()

    click.echo(f"Amministratore «{username_pulito}» creato ({nome} {cognome}).")
    if username_pulito == password.lower():
        click.echo(
            "ATTENZIONE: la password è uguale al nome utente. Va bene per le "
            "prove in locale, ma cambiala prima di installare sulla macchina "
            "virtuale."
        )


@click.command("dati-demo")
@click.option(
    "--azzera",
    is_flag=True,
    help="Toglie prima i dati demo già presenti, invece di aggiungerne altri.",
)
def dati_demo(azzera: bool) -> None:
    """Carica pazienti, utenti e note di esempio, gli stessi del prototipo.

    Comando riservato allo sviluppo: serve ad avere qualcosa da guardare
    mentre si costruisce la home. In produzione si rifiuta di partire.
    """
    from flask import current_app

    if current_app.config["AMBIENTE"] not in ("sviluppo", "test"):
        raise click.ClickException(
            "dati-demo funziona solo in sviluppo. In produzione i pazienti si "
            "inseriscono dal programma."
        )

    if azzera:
        _svuota_dati_demo()

    utenti = _crea_utenti_demo()
    pazienti = _crea_pazienti_demo(utenti["admin"])
    _crea_note_demo(pazienti, utenti)
    _crea_spunte_demo(pazienti)

    db.session.commit()

    # utenti contiene anche l'amministratore vero, che non è un utente di prova.
    click.echo(
        f"Creati {len(UTENTI_DEMO)} utenti di prova, {len(pazienti)} pazienti "
        "e le loro note."
    )
    click.echo(f"Password di tutti gli utenti di prova: {PASSWORD_DEMO}")
    for _, username, nome, cognome, ruolo in UTENTI_DEMO:
        click.echo(f"  {username:<12} {nome} {cognome} ({ruolo})")


@click.command("controlla-dati-fissi")
def controlla_dati_fissi() -> None:
    """Verifica che reparti e voci della checklist siano al loro posto.

    Utile dopo un aggiornamento sulla macchina virtuale, per accorgersi subito
    se una migrazione non è andata a buon fine.
    """
    reparti = db.session.query(Reparto).count()
    voci = db.session.query(VoceChecklist).count()

    click.echo(f"Reparti: {reparti} (attesi {len(REPARTI)})")
    click.echo(f"Voci della checklist: {voci} (attese {len(VOCI_CHECKLIST)})")

    if reparti != len(REPARTI) or voci != len(VOCI_CHECKLIST):
        raise click.ClickException("I dati fissi non sono completi: controlla le migrazioni.")

    click.echo("Dati fissi completi.")


# --------------------------------------------------------------------------
# Funzioni di appoggio per dati-demo
# --------------------------------------------------------------------------
UTENTI_DEMO = [
    # (chiave interna, username, nome, cognome, ruolo)
    ("medico", "mrossi", "Mario", "Rossi", RUOLO_MEDICO),
    ("infermiere", "cbianchi", "Carlo", "Bianchi", RUOLO_INFERMIERE),
    ("oss", "gverdi", "Giulia", "Verdi", RUOLO_OSS),
    ("ammin", "ufficioit", "Ufficio", "IT", RUOLO_AMMIN),
]

PASSWORD_DEMO = "prova2026"


def _svuota_dati_demo() -> None:
    """Toglie pazienti, note e utenti di prova per ripartire puliti.

    È l'unico punto del programma che cancella davvero delle righe, ed è
    accettabile solo perché riguarda dati finti in sviluppo.
    """
    db.session.query(ChecklistSpunta).delete()
    db.session.query(Nota).delete()
    db.session.query(Paziente).delete()
    usernames = [u[1] for u in UTENTI_DEMO]
    db.session.query(Utente).filter(Utente.username.in_(usernames)).delete(
        synchronize_session=False
    )
    db.session.commit()


def _crea_utenti_demo() -> dict[str, Utente]:
    """Crea gli utenti di prova, uno per ruolo, se non esistono già."""
    utenti: dict[str, Utente] = {}

    # L'amministratore vero serve come "autore" dei pazienti demo.
    amministratore = db.session.query(Utente).filter_by(ruolo=RUOLO_ADMIN).first()
    if amministratore is None:
        raise click.ClickException(
            "Prima lancia «flask crea-admin»: i pazienti di prova hanno bisogno "
            "di un utente che risulti averli inseriti."
        )
    utenti["admin"] = amministratore

    for chiave, username, nome, cognome, ruolo in UTENTI_DEMO:
        utente = db.session.query(Utente).filter_by(username=username).first()
        if utente is None:
            utente = Utente(
                username=username,
                nome=nome,
                cognome=cognome,
                ruolo=ruolo,
                attivo=True,
                # Dati finti in sviluppo: il cambio obbligatorio renderebbe
                # solo più scomodo passare da un ruolo all'altro per provare.
                deve_cambiare_password=False,
                creato_da=amministratore.id,
            )
            utente.imposta_password(PASSWORD_DEMO)
            db.session.add(utente)
        utenti[chiave] = utente

    db.session.flush()  # assegna gli id, che servono subito dopo per le note
    return utenti


def _giorno(scarto: int):
    """Una data relativa a oggi: _giorno(-4) è quattro giorni fa."""
    from datetime import timedelta

    return oggi_italia() + timedelta(days=scarto)


def _crea_pazienti_demo(autore: Utente) -> dict[int, Paziente]:
    """I sei pazienti del prototipo, con le date sempre relative a oggi."""
    reparti = {r.codice: r for r in db.session.query(Reparto).all()}

    definizioni = [
        # (n., reparto, nome, cognome, letto, gravità, arrivo, dimissione)
        (1, "AOUP", "Mario", "Rossi", "A-01", "rosso", -4, 3),
        (2, "AOUP", "Anna", "Bianchi", "A-03", "giallo", 0, 7),
        (3, "AOUP", "Sergio", "Manetti", "A-06", "nv", -8, 1),
        (4, "S1", "Giulia", "Conti", "L1-02", "verde", -12, 0),
        (5, "S1", "Paolo", "Neri", "L1-05", "giallo", -2, None),
        (6, "S2", "Luca", "Ferri", "L2-01", "verde", -15, 5),
    ]

    pazienti: dict[int, Paziente] = {}
    for numero, codice_reparto, nome, cognome, letto, gravita, arrivo, uscita in definizioni:
        paziente = Paziente(
            reparto_id=reparti[codice_reparto].id,
            nome=nome,
            cognome=cognome,
            posto_letto=letto,
            gravita=gravita,
            data_arrivo=_giorno(arrivo),
            data_dimissione_presunta=None if uscita is None else _giorno(uscita),
            stato=STATO_RICOVERATO,
            creato_da=autore.id,
        )
        db.session.add(paziente)
        pazienti[numero] = paziente

    db.session.flush()
    return pazienti


def _crea_note_demo(pazienti: dict[int, Paziente], utenti: dict[str, Utente]) -> None:
    """Le sette note del prototipo, firmate come là."""
    definizioni = [
        # (paziente, autore, testo, giorni fa, modificata?)
        (1, "infermiere", "Ingresso da PS. Parametri instabili, monitoraggio ogni 2 ore.", -4, False),
        (1, "medico", "Emocromo di controllo richiesto. Proseguire terapia antibiotica ev, rivalutare a 48h.", -3, False),
        (1, "infermiere", "Medicazione CVP sostituita. Cute integra.", -1, False),
        (1, "medico", "Miglioramento clinico, satura in aria ambiente. Dimissione prevista tra 3 giorni.", 0, True),
        (1, "infermiere", "Parametri stabili nel turno di mattina.", 0, False),
        (4, "infermiere", "Fisioterapia motoria, buona risposta.", -1, False),
        (4, "medico", "Valutare dimissione protetta con ADI.", -2, False),
    ]

    for numero_paziente, chiave_autore, testo, scarto, modificata in definizioni:
        autore = utenti[chiave_autore]
        nota = Nota(
            paziente_id=pazienti[numero_paziente].id,
            autore_id=autore.id,
            # La firma si "fotografa" adesso: vedi il commento nel modello Nota.
            autore_nome=autore.nome_completo,
            autore_ruolo=autore.ruolo,
            testo=testo,
            data_nota=_giorno(scarto),
            modificata_il=None,
        )
        if modificata:
            from app.formati import adesso_utc

            nota.modificata_il = adesso_utc()
        db.session.add(nota)


def _crea_spunte_demo(pazienti: dict[int, Paziente]) -> None:
    """Qualche voce già spuntata, per vedere il contatore in funzione."""
    spunte = {
        1: ["DIMISSIBILE", "ESAMI", "REFERTI", "TERAPIA", "FAMILIARI"],
        4: ["DIMISSIBILE", "DATA_DIM"],
    }

    for numero_paziente, codici in spunte.items():
        for codice in codici:
            db.session.add(
                ChecklistSpunta(
                    paziente_id=pazienti[numero_paziente].id, voce_codice=codice
                )
            )
