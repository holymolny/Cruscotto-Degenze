"""Le pagine dell'Agenda.

Queste route restituiscono JSON con dentro un pezzo di HTML già disegnato dal
server, non una pagina intera. Perché l'HTML lo fa il server e non il
JavaScript? Perché il testo delle note lo scrivono le persone, e Jinja lo
mette in pagina con l'escape automatico: costruendolo a mano nel browser
basterebbe una dimenticanza per trasformare una nota in codice eseguibile.
"""

from __future__ import annotations

from flask import abort, jsonify, render_template, request
from flask_login import current_user, login_required

from app import audit
from app.agenda import agenda_bp, servizi
from app.agenda.form import FormNota, FormSenzaCampi
from app.audit import registra_evento
from app.estensioni import db
from app.models import STATO_RICOVERATO, Nota, Paziente
from app.permessi import (
    SCRIVERE_NOTE,
    SPUNTARE_CHECKLIST,
    ha_permesso,
    richiede_permesso,
)


@agenda_bp.route("/paziente/<int:paziente_id>/agenda")
@login_required
def apri(paziente_id: int):
    """Il contenuto dell'Agenda di un paziente."""
    paziente = _paziente_ricoverato(paziente_id)
    return _risposta_agenda(paziente)


@agenda_bp.route("/paziente/<int:paziente_id>/nota", methods=["POST"])
@login_required
@richiede_permesso(SCRIVERE_NOTE)
def crea_nota(paziente_id: int):
    """Scrive una nota nuova."""
    paziente = _paziente_ricoverato(paziente_id)
    form = FormNota()

    if not form.validate_on_submit():
        return _risposta_agenda(paziente, errore=_primo_errore(form))

    try:
        nota = servizi.crea_nota(paziente, current_user, form.testo.data)
    except servizi.ErroreDiRegola as errore:
        return _risposta_agenda(paziente, errore=str(errore))

    db.session.flush()
    # Nel registro finisce che una nota è stata scritta, mai cosa dice:
    # sarebbe un dato sanitario copiato in un registro tecnico.
    registra_evento(
        audit.NOTA_CREATA,
        entita="nota",
        entita_id=nota.id,
        dettagli=f"paziente {paziente.id}",
    )
    db.session.commit()

    return _risposta_agenda(paziente)


@agenda_bp.route("/nota/<int:nota_id>/modifica", methods=["POST"])
@login_required
@richiede_permesso(SCRIVERE_NOTE)
def modifica_nota(nota_id: int):
    """Modifica una nota. Solo l'autore, nemmeno l'ADMIN."""
    nota = _nota_viva(nota_id)
    paziente = _paziente_ricoverato(nota.paziente_id)
    form = FormNota()

    if not form.validate_on_submit():
        return _risposta_agenda(paziente, errore=_primo_errore(form))

    try:
        servizi.modifica_nota(nota, current_user, form.testo.data)
    except servizi.ErroreDiRegola as errore:
        return _risposta_agenda(paziente, errore=str(errore))

    registra_evento(
        audit.NOTA_MODIFICATA,
        entita="nota",
        entita_id=nota.id,
        dettagli=f"paziente {paziente.id}",
    )
    db.session.commit()

    return _risposta_agenda(paziente)


@agenda_bp.route("/nota/<int:nota_id>/elimina", methods=["POST"])
@login_required
@richiede_permesso(SCRIVERE_NOTE)
def elimina_nota(nota_id: int):
    """Eliminazione logica di una nota. Solo l'autore."""
    nota = _nota_viva(nota_id)
    paziente = _paziente_ricoverato(nota.paziente_id)

    if not FormSenzaCampi().validate_on_submit():
        return _risposta_agenda(paziente, errore="Richiesta non valida. Riprova.")

    try:
        servizi.elimina_nota(nota, current_user)
    except servizi.ErroreDiRegola as errore:
        return _risposta_agenda(paziente, errore=str(errore))

    registra_evento(
        audit.NOTA_ELIMINATA,
        entita="nota",
        entita_id=nota.id,
        dettagli=f"paziente {paziente.id}",
    )
    db.session.commit()

    return _risposta_agenda(paziente)


@agenda_bp.route("/paziente/<int:paziente_id>/checklist", methods=["POST"])
@login_required
@richiede_permesso(SPUNTARE_CHECKLIST)
def spunta_checklist(paziente_id: int):
    """Mette o toglie una spunta. Risponde solo con il nuovo totale.

    Qui non serve ridisegnare niente: il browser ha già messo il segno nella
    casella, e la risposta serve solo ad aggiornare il contatore e la barra.
    """
    paziente = _paziente_ricoverato(paziente_id)
    dati = request.get_json(silent=True) or {}

    codice = dati.get("codice")
    spuntata = bool(dati.get("spuntata"))
    if not codice:
        abort(400)

    try:
        totale = servizi.imposta_spunta(paziente, codice, spuntata)
    except servizi.ErroreDiRegola:
        abort(400)

    db.session.commit()

    voci = servizi.voci_checklist()
    return jsonify({"spuntate": totale, "totale": len(voci)})


# --------------------------------------------------------------------------
# Funzioni di appoggio
# --------------------------------------------------------------------------
def _risposta_agenda(paziente: Paziente, errore: str | None = None):
    """Disegna il contenuto dell'Agenda e lo restituisce in JSON.

    Insieme all'HTML viaggia il numero di note visibili: serve ad aggiornare
    il contatore sul pulsante «Agenda» nella home, che sta fuori dalla
    finestra e quindi non verrebbe ridisegnato.
    """
    note = servizi.note_visibili(paziente.id)
    voci = servizi.voci_checklist()
    spuntate = servizi.codici_spuntati(paziente.id)

    html = render_template(
        "agenda/_contenuto.html",
        paziente=paziente,
        gruppi=servizi.raggruppa_per_giorno(note),
        voci_checklist=voci,
        codici_spuntati=spuntate,
        totale_spuntate=len(spuntate),
        totale_voci=len(voci),
        form_nota=FormNota(formdata=None),
        form_senza_campi=FormSenzaCampi(formdata=None),
        errore=errore,
        puo_scrivere=ha_permesso(current_user.ruolo, SCRIVERE_NOTE),
        puo_spuntare=ha_permesso(current_user.ruolo, SPUNTARE_CHECKLIST),
    )

    return jsonify(
        {
            "html": html,
            "note": len(note),
            "paziente": paziente.id,
            "ok": errore is None,
        }
    )


def _paziente_ricoverato(paziente_id: int) -> Paziente:
    paziente = (
        db.session.query(Paziente)
        .filter_by(id=paziente_id, stato=STATO_RICOVERATO)
        .first()
    )
    if paziente is None:
        abort(404)
    return paziente


def _nota_viva(nota_id: int) -> Nota:
    nota = db.session.get(Nota, nota_id)
    if nota is None or nota.eliminata:
        abort(404)
    return nota


def _primo_errore(form) -> str:
    for campo in form:
        if campo.errors:
            return campo.errors[0]
    return "Richiesta non valida. Riprova."
