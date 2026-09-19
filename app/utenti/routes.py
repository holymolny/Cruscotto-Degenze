"""Le pagine dell'area «Gestione utenti».

Ogni route qui dentro porta @richiede_permesso(GESTIRE_UTENTI), che in pratica
significa «solo l'amministratore». Nascondere la voce nel menu a chi non ha il
permesso serve a non confonderlo, non a fermarlo: chi conosce l'indirizzo può
sempre provare a scriverlo a mano, e lì risponde il decoratore con un 403.
"""

from __future__ import annotations

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import audit
from app.audit import registra_evento
from app.auth.servizi import account_bloccato
from app.estensioni import db
from app.models import RUOLI, RUOLO_ADMIN, Utente
from app.permessi import GESTIRE_UTENTI, richiede_permesso
from app.utenti import servizi, utenti_bp
from app.utenti.form import (
    FormConferma,
    FormModificaUtente,
    FormNuovoUtente,
    FormPassword,
)


@utenti_bp.route("/utenti")
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def elenco():
    """L'elenco degli account, con le azioni che si possono fare su ciascuno."""
    utenti = servizi.elenco_utenti()

    # Calcolato qui e passato al template: «è bloccato?» dipende dall'ora
    # attuale, e un template non è il posto dove fare conti sul tempo.
    bloccati = {utente.id for utente in utenti if account_bloccato(utente)}

    # Serve al template per sapere se disegnare attivi o spenti i pulsanti che
    # toglierebbero l'ultimo amministratore: se ne resta uno solo, quello è lui.
    admin_attivi = servizi.amministratori_attivi()

    return render_template(
        "utenti/elenco.html",
        utenti=utenti,
        bloccati=bloccati,
        admin_attivi=admin_attivi,
        ruolo_admin=RUOLO_ADMIN,
        form_nuovo=FormNuovoUtente(),
        form_modifica=FormModificaUtente(),
        form_password=FormPassword(),
        form_conferma=FormConferma(),
    )


@utenti_bp.route("/utenti/nuovo", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def nuovo():
    """Creazione di un account."""
    form = FormNuovoUtente()

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("utenti.elenco"))

    try:
        utente = servizi.crea_utente(
            nome=form.nome.data,
            cognome=form.cognome.data,
            username=form.username.data,
            ruolo=form.ruolo.data,
            password=form.password.data,
            autore=current_user,
        )
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("utenti.elenco"))

    # flush() assegna l'id senza chiudere la transazione: serve per poterlo
    # scrivere nel registro insieme alla creazione.
    db.session.flush()
    registra_evento(
        audit.UTENTE_CREATO,
        entita="utente",
        entita_id=utente.id,
        # Nel registro il nome utente e il ruolo, mai la password.
        dettagli=f"{utente.username} ({utente.etichetta_ruolo})",
    )
    db.session.commit()

    flash(
        f"Utente «{utente.username}» creato. "
        f"Al primo accesso dovrà scegliere una password personale.",
        "successo",
    )
    return redirect(url_for("utenti.elenco"))


@utenti_bp.route("/utenti/<int:utente_id>/modifica", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def modifica(utente_id: int):
    """Cambio di nome, cognome e ruolo."""
    utente = _utente(utente_id)
    form = FormModificaUtente()

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("utenti.elenco"))

    ruolo_precedente = utente.ruolo

    try:
        servizi.modifica_utente(
            utente,
            nome=form.nome.data,
            cognome=form.cognome.data,
            ruolo=form.ruolo.data,
            autore=current_user,
        )
    except servizi.ErroreDiRegola as errore:
        # Niente rollback: i servizi controllano tutto prima di toccare
        # l'oggetto, quindi quando arriva l'eccezione nel database non è
        # cambiato nulla. Vale per tutte le route di questo file.
        flash(str(errore), "errore")
        return redirect(url_for("utenti.elenco"))

    dettagli = f"{utente.username}: {utente.nome_completo}"
    if utente.ruolo != ruolo_precedente:
        dettagli += (
            f", ruolo da {RUOLI.get(ruolo_precedente, ruolo_precedente)} "
            f"a {utente.etichetta_ruolo}"
        )

    registra_evento(
        audit.UTENTE_MODIFICATO, entita="utente", entita_id=utente.id, dettagli=dettagli
    )
    db.session.commit()

    flash(f"Dati di «{utente.username}» aggiornati.", "successo")
    return redirect(url_for("utenti.elenco"))


@utenti_bp.route("/utenti/<int:utente_id>/password", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def reimposta_password(utente_id: int):
    """Assegna una password nuova a chi l'ha dimenticata."""
    utente = _utente(utente_id)
    form = FormPassword()

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("utenti.elenco"))

    try:
        servizi.reimposta_password(utente, form.password.data)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("utenti.elenco"))

    # Nel registro finisce che la password è stata reimpostata, mai quale sia.
    registra_evento(
        audit.PASSWORD_REIMPOSTATA,
        entita="utente",
        entita_id=utente.id,
        dettagli=utente.username,
    )
    db.session.commit()

    flash(
        f"Password di «{utente.username}» reimpostata. "
        f"Comunicagliela a voce: al primo accesso dovrà cambiarla.",
        "successo",
    )
    return redirect(url_for("utenti.elenco"))


@utenti_bp.route("/utenti/<int:utente_id>/disattiva", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def disattiva(utente_id: int):
    """Toglie l'accesso senza cancellare nulla."""
    utente = _utente(utente_id)

    if not FormConferma().validate_on_submit():
        flash("Richiesta non valida. Riprova.", "errore")
        return redirect(url_for("utenti.elenco"))

    try:
        servizi.disattiva(utente, current_user)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("utenti.elenco"))

    registra_evento(
        audit.UTENTE_MODIFICATO,
        entita="utente",
        entita_id=utente.id,
        dettagli=f"{utente.username} disattivato",
    )
    db.session.commit()

    flash(
        f"«{utente.username}» non può più accedere. "
        f"Le note che ha scritto restano al loro posto.",
        "successo",
    )
    return redirect(url_for("utenti.elenco"))


@utenti_bp.route("/utenti/<int:utente_id>/riattiva", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def riattiva(utente_id: int):
    """Ridà l'accesso a chi era stato disattivato."""
    utente = _utente(utente_id)

    if not FormConferma().validate_on_submit():
        flash("Richiesta non valida. Riprova.", "errore")
        return redirect(url_for("utenti.elenco"))

    try:
        servizi.riattiva(utente)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("utenti.elenco"))

    registra_evento(
        audit.UTENTE_MODIFICATO,
        entita="utente",
        entita_id=utente.id,
        dettagli=f"{utente.username} riattivato",
    )
    db.session.commit()

    flash(f"«{utente.username}» può accedere di nuovo.", "successo")
    return redirect(url_for("utenti.elenco"))


@utenti_bp.route("/utenti/<int:utente_id>/sblocca", methods=["POST"])
@login_required
@richiede_permesso(GESTIRE_UTENTI)
def sblocca(utente_id: int):
    """Toglie il blocco scattato dopo cinque tentativi falliti."""
    utente = _utente(utente_id)

    if not FormConferma().validate_on_submit():
        flash("Richiesta non valida. Riprova.", "errore")
        return redirect(url_for("utenti.elenco"))

    servizi.sblocca_account(utente)
    registra_evento(
        audit.UTENTE_MODIFICATO,
        entita="utente",
        entita_id=utente.id,
        dettagli=f"{utente.username} sbloccato",
    )
    db.session.commit()

    flash(f"«{utente.username}» può riprovare ad accedere subito.", "successo")
    return redirect(url_for("utenti.elenco"))


# --------------------------------------------------------------------------
# Funzioni di appoggio
# --------------------------------------------------------------------------
def _utente(utente_id: int) -> Utente:
    """Recupera un utente, o risponde 404."""
    utente = servizi.utente_per_id(utente_id)
    if utente is None:
        abort(404)
    return utente


def _mostra_errori_del_form(form) -> None:
    """Trasforma gli errori di un form in messaggi per l'utente.

    I form vivono dentro finestre che dopo l'invio si chiudono: non c'è dove
    mostrare l'errore accanto al campo, quindi diventa un messaggio in cima
    alla pagina.
    """
    for campo in form:
        for errore in campo.errors:
            flash(errore, "errore")
    if not any(campo.errors for campo in form):
        flash("Richiesta non valida. Riprova.", "errore")
