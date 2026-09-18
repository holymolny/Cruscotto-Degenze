"""La pagina che consegna il PDF."""

from __future__ import annotations

from flask import Response, abort, current_app
from flask_login import current_user, login_required

from app import audit
from app.agenda import servizi as servizi_agenda
from app.audit import registra_evento
from app.estensioni import db
from app.models import STATO_RICOVERATO, Paziente
from app.pdf import generatore, pdf_bp
from app.permessi import SCARICARE_PDF, richiede_permesso


@pdf_bp.route("/paziente/<int:paziente_id>/pdf")
@login_required
@richiede_permesso(SCARICARE_PDF)
def scheda(paziente_id: int):
    """Genera e consegna la scheda del paziente."""
    paziente = (
        db.session.query(Paziente)
        .filter_by(id=paziente_id, stato=STATO_RICOVERATO)
        .first()
    )
    if paziente is None:
        abort(404)

    contenuto = generatore.genera_scheda(
        paziente=paziente,
        note=servizi_agenda.note_visibili(paziente.id),
        voci=servizi_agenda.voci_checklist(),
        spuntati=servizi_agenda.codici_spuntati(paziente.id),
        utente=current_user,
        nome_struttura=current_app.config["NOME_STRUTTURA"],
    )

    # Il download va nel registro: la scheda contiene tutte le note del
    # paziente, quindi sapere chi l'ha portata fuori dal programma conta.
    registra_evento(
        audit.PDF_SCARICATO,
        entita="paziente",
        entita_id=paziente.id,
        dettagli=f"{paziente.etichetta}, letto {paziente.posto_letto}",
    )
    db.session.commit()

    risposta = Response(contenuto, mimetype="application/pdf")
    # attachment: il browser scarica il file invece di aprirlo in una scheda.
    # In reparto il gesto è «stampo e allego alla cartella», non «leggo a video».
    risposta.headers["Content-Disposition"] = (
        f'attachment; filename="{generatore.nome_file(paziente)}"'
    )
    # Il PDF contiene dati del paziente: non deve restare nella cache del
    # browser di un PC condiviso.
    risposta.headers["Cache-Control"] = "no-store"
    return risposta
