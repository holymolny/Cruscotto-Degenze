"""Le pagine dell'area pazienti."""

from __future__ import annotations

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import audit
from app.audit import registra_evento
from app.estensioni import db
from app.formati import data_italiana
from app.models import GRAVITA, STATO_RICOVERATO, Paziente, Reparto
from app.pazienti import pazienti_bp, servizi
from app.pazienti.form import (
    FormConferma,
    FormDimissione,
    FormNuovoPaziente,
    FormSposta,
)
from app.permessi import (
    CAMBIARE_GRAVITA,
    ELIMINARE_PAZIENTE,
    INSERIRE_PAZIENTE,
    MODIFICARE_DIMISSIONE,
    SPOSTARE_PAZIENTE,
    richiede_permesso,
)


@pazienti_bp.route("/")
@login_required
def home():
    """Home «Pazienti ricoverati»: i tre reparti con i loro ricoverati."""
    reparti = db.session.query(Reparto).order_by(Reparto.ordine).all()

    elenchi = {}
    note_per_paziente = {}
    for reparto in reparti:
        pazienti = servizi.pazienti_ricoverati(reparto.id)
        elenchi[reparto.id] = pazienti
        note_per_paziente.update(servizi.conteggio_note(pazienti))

    form_nuovo = FormNuovoPaziente()
    form_nuovo.data_arrivo.data = servizi.data_arrivo_predefinita()

    form_sposta = FormSposta()
    form_sposta.reparto_id.choices = [(r.id, r.nome) for r in reparti]

    return render_template(
        "pazienti/home.html",
        reparti=reparti,
        elenchi=elenchi,
        note_per_paziente=note_per_paziente,
        form_nuovo=form_nuovo,
        form_dimissione=FormDimissione(),
        form_sposta=form_sposta,
        form_conferma=FormConferma(),
        gravita_etichette=GRAVITA,
    )


@pazienti_bp.route("/paziente/nuovo", methods=["POST"])
@login_required
@richiede_permesso(INSERIRE_PAZIENTE)
def nuovo():
    """Inserimento di un paziente."""
    form = FormNuovoPaziente()

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("pazienti.home"))

    try:
        paziente = servizi.crea_paziente(
            reparto_id=int(form.reparto_id.data),
            nome=form.nome.data,
            cognome=form.cognome.data,
            posto_letto=form.posto_letto.data,
            data_arrivo=form.data_arrivo.data,
            data_dimissione_presunta=form.data_dimissione_presunta.data,
            autore_id=current_user.id,
        )
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("pazienti.home"))

    # flush() assegna l'id al paziente senza chiudere la transazione: serve
    # per poterlo scrivere nel registro insieme all'inserimento.
    db.session.flush()
    registra_evento(
        audit.PAZIENTE_CREATO,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"{paziente.etichetta}, letto {paziente.posto_letto}",
    )
    db.session.commit()

    flash(f"Paziente {paziente.etichetta} inserito nel letto {paziente.posto_letto}.", "successo")
    return redirect(url_for("pazienti.home"))


@pazienti_bp.route("/paziente/<int:paziente_id>/gravita", methods=["POST"])
@login_required
@richiede_permesso(CAMBIARE_GRAVITA)
def cambia_gravita(paziente_id: int):
    """Fa ruotare il pallino della gravità e risponde in JSON.

    Questa route non restituisce una pagina ma solo il nuovo stato: la
    chiama il JavaScript e aggiorna il pallino sul posto, senza ricaricare.
    Ricaricare l'intera home per cambiare un pallino sarebbe uno spreco, e
    in reparto si perderebbe la posizione nella pagina.
    """
    paziente = _paziente_ricoverato(paziente_id)

    precedente = paziente.gravita
    paziente.gravita = servizi.prossima_gravita(precedente)

    registra_evento(
        audit.GRAVITA_MODIFICATA,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"da {precedente} a {paziente.gravita}",
    )
    db.session.commit()

    return jsonify(
        {
            "gravita": paziente.gravita,
            "etichetta": GRAVITA.get(paziente.gravita, paziente.gravita),
        }
    )


@pazienti_bp.route("/paziente/<int:paziente_id>/dimissione", methods=["POST"])
@login_required
@richiede_permesso(MODIFICARE_DIMISSIONE)
def modifica_dimissione(paziente_id: int):
    """Cambia la data presunta di dimissione. Si può anche svuotare."""
    paziente = _paziente_ricoverato(paziente_id)
    form = FormDimissione()

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("pazienti.home"))

    precedente = paziente.data_dimissione_presunta
    nuova = form.data_dimissione_presunta.data

    try:
        servizi.modifica_dimissione(paziente, nuova)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("pazienti.home"))

    registra_evento(
        audit.DIMISSIONE_MODIFICATA,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"da {data_italiana(precedente)} a {data_italiana(nuova)}",
    )
    db.session.commit()

    flash(
        f"Dimissione presunta di {paziente.etichetta}: {data_italiana(nuova)}.",
        "successo",
    )
    return redirect(url_for("pazienti.home"))


@pazienti_bp.route("/paziente/<int:paziente_id>/sposta", methods=["POST"])
@login_required
@richiede_permesso(SPOSTARE_PAZIENTE)
def sposta(paziente_id: int):
    """Sposta un paziente in un altro reparto o in un altro letto."""
    paziente = _paziente_ricoverato(paziente_id)

    form = FormSposta()
    form.reparto_id.choices = [
        (r.id, r.nome) for r in db.session.query(Reparto).order_by(Reparto.ordine)
    ]

    if not form.validate_on_submit():
        _mostra_errori_del_form(form)
        return redirect(url_for("pazienti.home"))

    provenienza = f"{paziente.reparto.codice} {paziente.posto_letto}"

    try:
        servizi.sposta_di_reparto(paziente, form.reparto_id.data, form.posto_letto.data)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("pazienti.home"))

    db.session.flush()
    registra_evento(
        audit.PAZIENTE_SPOSTATO,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"da {provenienza} a {paziente.reparto.codice} {paziente.posto_letto}",
    )
    db.session.commit()

    flash(
        f"{paziente.etichetta} spostato in {paziente.reparto.nome}, "
        f"letto {paziente.posto_letto}.",
        "successo",
    )
    return redirect(url_for("pazienti.home"))


@pazienti_bp.route("/paziente/<int:paziente_id>/elimina", methods=["POST"])
@login_required
@richiede_permesso(ELIMINARE_PAZIENTE)
def elimina(paziente_id: int):
    """Dimissione del paziente: sparisce dal cruscotto e il letto torna libero."""
    paziente = _paziente_ricoverato(paziente_id)
    form = FormConferma()

    if not form.validate_on_submit():
        flash("Richiesta non valida. Riprova.", "errore")
        return redirect(url_for("pazienti.home"))

    etichetta = paziente.etichetta
    letto = paziente.posto_letto

    try:
        servizi.elimina_paziente(paziente, current_user.id)
    except servizi.ErroreDiRegola as errore:
        flash(str(errore), "errore")
        return redirect(url_for("pazienti.home"))

    registra_evento(
        audit.PAZIENTE_ELIMINATO,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"{etichetta}, letto {letto}",
    )
    db.session.commit()

    flash(f"{etichetta} è stato dimesso. Il letto {letto} è di nuovo libero.", "successo")
    return redirect(url_for("pazienti.home"))


# --------------------------------------------------------------------------
# Funzioni di appoggio
# --------------------------------------------------------------------------
def _paziente_ricoverato(paziente_id: int) -> Paziente:
    """Recupera un paziente ricoverato, o risponde 404.

    Filtriamo sullo stato di proposito: un paziente già dimesso non deve
    poter essere modificato da chi tiene aperta una pagina vecchia e clicca
    su un pulsante che nel frattempo non ha più senso.
    """
    paziente = (
        db.session.query(Paziente)
        .filter_by(id=paziente_id, stato=STATO_RICOVERATO)
        .first()
    )
    if paziente is None:
        from flask import abort

        abort(404)
    return paziente


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
