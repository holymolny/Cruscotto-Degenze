"""Le pagine dell'area accesso."""

from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app import audit
from app.audit import registra_evento
from app.auth import auth_bp, servizi
from app.auth.form import FormCambioPassword, FormLogin
from app.estensioni import db
from app.sessione import segna_attivita


@auth_bp.route("/accedi", methods=["GET", "POST"])
def login():
    """Pagina di accesso."""
    if current_user.is_authenticated:
        return redirect(url_for("pazienti.home"))

    form = FormLogin()

    if form.validate_on_submit():
        esito = servizi.tenta_accesso(form.username.data, form.password.data)

        if not esito.riuscito:
            registra_evento(
                audit.LOGIN_FALLITO,
                username_tentato=form.username.data[:50],
            )
            # Il commit serve anche qui: il contatore dei tentativi falliti e
            # l'evento del registro devono restare anche se l'accesso è andato
            # male. Anzi: soprattutto se è andato male.
            db.session.commit()
            flash(esito.errore, "errore")
            return render_template("auth/login.html", form=form), 401

        login_user(esito.utente)
        segna_attivita()
        registra_evento(audit.LOGIN_OK, utente=esito.utente)
        db.session.commit()

        if esito.utente.deve_cambiare_password:
            flash(
                "Prima di iniziare devi scegliere una password personale.",
                "avviso",
            )
            return redirect(url_for("auth.cambio_password"))

        return redirect(_destinazione_dopo_accesso())

    return render_template("auth/login.html", form=form)


@auth_bp.route("/esci")
@login_required
def logout():
    """Uscita volontaria."""
    registra_evento(audit.LOGOUT)
    db.session.commit()

    logout_user()
    session.clear()
    flash("Sei uscito dal Cruscotto.", "avviso")
    return redirect(url_for("auth.login"))


@auth_bp.route("/cambia-password", methods=["GET", "POST"])
@login_required
def cambio_password():
    """Cambio della propria password.

    Stessa pagina in due situazioni: il cambio obbligatorio al primo accesso e
    il cambio volontario dal proprio profilo. Cambia solo il testo introduttivo.
    """
    form = FormCambioPassword()
    obbligatorio = current_user.deve_cambiare_password

    if form.validate_on_submit():
        attuale = form.password_attuale.data
        nuova = form.nuova_password.data

        if not current_user.password_corretta(attuale):
            flash("La password attuale non è corretta.", "errore")
            return render_template(
                "auth/cambio_password.html", form=form, obbligatorio=obbligatorio
            )

        errore = servizi.errore_nuova_password(nuova, password_attuale=attuale)
        if errore:
            flash(errore, "errore")
            return render_template(
                "auth/cambio_password.html", form=form, obbligatorio=obbligatorio
            )

        servizi.cambia_password(current_user, nuova)
        # Nel registro finisce che la password è cambiata, mai quale sia.
        registra_evento(audit.PASSWORD_CAMBIATA, entita="utente", entita_id=current_user.id)
        db.session.commit()

        flash("Password aggiornata.", "successo")
        return redirect(url_for("pazienti.home"))

    return render_template(
        "auth/cambio_password.html", form=form, obbligatorio=obbligatorio
    )


@auth_bp.route("/profilo")
@login_required
def profilo():
    """«Il mio profilo»: i propri dati e il collegamento al cambio password."""
    return render_template("auth/profilo.html")


# --------------------------------------------------------------------------
# Funzioni di appoggio
# --------------------------------------------------------------------------
def _destinazione_dopo_accesso() -> str:
    """Dove mandare l'utente appena entrato.

    Se stava cercando di aprire una pagina precisa, Flask-Login l'ha messa da
    parte nel parametro «next»: lo rispettiamo, ma solo se è un indirizzo
    interno. Accettare un «next» qualsiasi permetterebbe a un collegamento
    malevolo di spedire l'utente su un sito esterno subito dopo l'accesso,
    facendogli credere di essere ancora nel Cruscotto.
    """
    destinazione = request.args.get("next")
    if destinazione and destinazione.startswith("/") and not destinazione.startswith("//"):
        return destinazione
    return url_for("pazienti.home")
