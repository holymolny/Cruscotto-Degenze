"""Test del passo 7: la scheda paziente in PDF."""

from datetime import date

import pytest

from app import audit
from app.agenda import servizi as servizi_agenda
from app.models import RUOLO_AMMIN, RUOLO_INFERMIERE, RUOLO_OSS, EventoAudit
from app.pdf import generatore


@pytest.fixture
def paziente(crea_paziente):
    return crea_paziente(
        nome="Mario",
        cognome="Rossi",
        posto_letto="A-01",
        data_arrivo=date(2026, 9, 10),
        data_dimissione_presunta=date(2026, 9, 25),
    )


@pytest.fixture
def infermiere(crea_utente):
    return crea_utente(
        username="cbianchi",
        password="password1",
        ruolo=RUOLO_INFERMIERE,
        nome="Carlo",
        cognome="Bianchi",
    )


def _genera(paziente, utente, note=()):
    return generatore.genera_scheda(
        paziente=paziente,
        note=list(note),
        voci=servizi_agenda.voci_checklist(),
        spuntati=servizi_agenda.codici_spuntati(paziente.id),
        utente=utente,
        nome_struttura="Casa di Cura Misericordia Navacchio",
    )


# --------------------------------------------------------------------------
# Il file
# --------------------------------------------------------------------------
def test_il_pdf_viene_generato(db, paziente, amministratore):
    contenuto = _genera(paziente, amministratore)

    # Ogni PDF comincia con questa firma: se manca, non è un PDF.
    assert contenuto.startswith(b"%PDF-")
    assert contenuto.rstrip().endswith(b"%%EOF")
    assert len(contenuto) > 1000


def test_il_nome_del_file_segue_lo_schema(db, paziente):
    nome = generatore.nome_file(paziente, date(2026, 9, 18))

    assert nome == "Agenda_Rossi_Mario_2026-09-18.pdf"


def test_il_nome_del_file_regge_cognomi_con_spazi(db, crea_paziente):
    paziente = crea_paziente(nome="Anna Maria", cognome="De Santis", posto_letto="A-09")

    nome = generatore.nome_file(paziente, date(2026, 9, 18))

    assert " " not in nome
    assert nome == "Agenda_De_Santis_Anna_Maria_2026-09-18.pdf"


# --------------------------------------------------------------------------
# Il contenuto
# --------------------------------------------------------------------------
def _testo_del_pdf(contenuto: bytes) -> str:
    """Estrae il testo dal PDF per poterlo controllare.

    pypdf non è fra le dipendenze del progetto: serve solo qui, e installarlo
    sulla macchina virtuale per un controllo che si fa in sviluppo sarebbe
    codice in più da tenere aggiornato per niente.
    """
    pypdf = pytest.importorskip("pypdf", reason="pypdf serve solo a leggere i PDF nei test")
    from io import BytesIO

    lettore = pypdf.PdfReader(BytesIO(contenuto))
    return "\n".join(pagina.extract_text() for pagina in lettore.pages)


def test_il_pdf_contiene_i_dati_del_paziente(db, paziente, amministratore):
    testo = _testo_del_pdf(_genera(paziente, amministratore))

    assert "Scheda paziente e Agenda" in testo
    assert "Casa di Cura Misericordia Navacchio" in testo
    assert "Rossi Mario" in testo
    assert "A-01" in testo
    assert "10/09/2026" in testo
    assert "25/09/2026" in testo


def test_senza_dimissione_il_pdf_scrive_da_definire(db, crea_paziente, amministratore):
    paziente = crea_paziente(data_dimissione_presunta=None)

    testo = _testo_del_pdf(_genera(paziente, amministratore))

    assert "da definire" in testo


def test_il_pdf_dice_chi_lha_generato(db, paziente, infermiere):
    testo = _testo_del_pdf(_genera(paziente, infermiere))

    assert "Documento generato il" in testo
    assert "Infermiere: Carlo Bianchi" in testo


def test_il_pdf_contiene_tutte_le_voci_della_checklist(db, paziente, amministratore):
    testo = _testo_del_pdf(_genera(paziente, amministratore))

    assert "Checklist dimissione" in testo
    assert "0/20" in testo
    for voce in ("Paziente dimissibile", "Effetti personali consegnati"):
        assert voce in testo


def test_il_contatore_della_checklist_riflette_le_spunte(db, paziente, amministratore):
    servizi_agenda.imposta_spunta(paziente, "DIMISSIBILE", True)
    servizi_agenda.imposta_spunta(paziente, "ESAMI", True)
    db.session.commit()

    testo = _testo_del_pdf(_genera(paziente, amministratore))

    assert "2/20" in testo


def test_il_pdf_contiene_le_note_con_la_firma(db, paziente, infermiere, amministratore):
    servizi_agenda.crea_nota(paziente, infermiere, "Parametri stabili nel turno.")
    db.session.commit()
    note = servizi_agenda.note_visibili(paziente.id)

    testo = _testo_del_pdf(_genera(paziente, amministratore, note))

    assert "Parametri stabili nel turno." in testo
    assert "Infermiere:" in testo
    assert "Carlo Bianchi" in testo


def test_il_pdf_segnala_le_note_modificate(db, paziente, infermiere, amministratore):
    nota = servizi_agenda.crea_nota(paziente, infermiere, "Testo iniziale.")
    db.session.commit()
    servizi_agenda.modifica_nota(nota, infermiere, "Testo corretto.")
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    assert "modificata il" in testo


def test_le_note_eliminate_non_finiscono_nel_pdf(db, paziente, infermiere, amministratore):
    nota = servizi_agenda.crea_nota(paziente, infermiere, "Nota da non stampare.")
    db.session.commit()
    servizi_agenda.elimina_nota(nota, infermiere)
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    assert "Nota da non stampare" not in testo


def test_il_pdf_ha_il_piede_di_pagina(db, paziente, amministratore):
    testo = _testo_del_pdf(_genera(paziente, amministratore))

    assert "Rossi Mario - letto A-01" in testo
    assert "Pagina 1 di 1" in testo


def test_gli_accenti_sopravvivono_nel_pdf(db, paziente, infermiere, amministratore):
    """È il motivo per cui il font DejaVu è incluso nel progetto."""
    servizi_agenda.crea_nota(
        paziente, infermiere, "Continuità assistenziale attivata. Città: Pisa. Perché?"
    )
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    assert "Continuità" in testo
    assert "Città" in testo
    assert "Perché" in testo


def test_una_nota_con_segni_speciali_non_rompe_il_pdf(db, paziente, infermiere, amministratore):
    """ReportLab legge i paragrafi come XML: «PA < 90» lo farebbe fallire.

    È il tipo di errore che comparirebbe solo il giorno in cui un medico
    scrive una disuguaglianza in una nota.
    """
    servizi_agenda.crea_nota(paziente, infermiere, "PA < 90 & FC > 100. Diuresi <500ml.")
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    assert "PA < 90" in testo
    assert "FC > 100" in testo


def test_gli_a_capo_delle_note_restano(db, paziente, infermiere, amministratore):
    servizi_agenda.crea_nota(paziente, infermiere, "Prima riga.\nSeconda riga.")
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    assert "Prima riga." in testo
    assert "Seconda riga." in testo


def test_molte_note_producono_piu_pagine_numerate(db, paziente, infermiere, amministratore):
    """Il totale nel piè di pagina deve essere giusto su ogni pagina.

    È il punto in cui la tecnica della «tela numerata» si guadagna il pane:
    ReportLab, mentre disegna la pagina 1, non sa ancora quante saranno.
    """
    import re

    for numero in range(60):
        servizi_agenda.crea_nota(paziente, infermiere, f"Nota numero {numero}. " * 8)
    db.session.commit()

    testo = _testo_del_pdf(
        _genera(paziente, amministratore, servizi_agenda.note_visibili(paziente.id))
    )

    piedi = re.findall(r"Pagina (\d+) di (\d+)", testo)
    totale = int(piedi[0][1])

    assert totale > 1, "con 60 note il documento deve andare su più pagine"
    # Una riga per pagina, numerate da 1 a N, tutte con lo stesso totale.
    assert [(str(n), str(totale)) for n in range(1, totale + 1)] == piedi


# --------------------------------------------------------------------------
# La pagina e i permessi
# --------------------------------------------------------------------------
def test_scaricamento_dalla_pagina(client, db, paziente, amministratore, accedi):
    accedi("capo", "capo1234")

    risposta = client.get(f"/paziente/{paziente.id}/pdf")

    assert risposta.status_code == 200
    assert risposta.mimetype == "application/pdf"
    assert risposta.data.startswith(b"%PDF-")


def test_il_pdf_viene_scaricato_non_aperto(client, db, paziente, amministratore, accedi):
    accedi("capo", "capo1234")

    risposta = client.get(f"/paziente/{paziente.id}/pdf")

    disposizione = risposta.headers["Content-Disposition"]
    assert disposizione.startswith("attachment")
    assert "Agenda_Rossi_Mario_" in disposizione


def test_il_pdf_non_resta_nella_cache_del_browser(client, db, paziente, amministratore, accedi):
    """I PC di reparto sono condivisi: la scheda contiene tutte le note."""
    accedi("capo", "capo1234")

    risposta = client.get(f"/paziente/{paziente.id}/pdf")

    assert "no-store" in risposta.headers["Cache-Control"]


def test_il_download_finisce_nel_registro(client, db, paziente, amministratore, accedi):
    accedi("capo", "capo1234")

    client.get(f"/paziente/{paziente.id}/pdf")

    eventi = db.session.query(EventoAudit).filter_by(azione=audit.PDF_SCARICATO).all()
    assert len(eventi) == 1
    assert eventi[0].entita_id == paziente.id


def test_loss_non_puo_scaricare_il_pdf(client, db, paziente, crea_utente, accedi):
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    assert client.get(f"/paziente/{paziente.id}/pdf").status_code == 403


def test_lammin_puo_scaricare_il_pdf(client, db, paziente, crea_utente, accedi):
    crea_utente(username="it", password="password1", ruolo=RUOLO_AMMIN)
    accedi("it", "password1")

    assert client.get(f"/paziente/{paziente.id}/pdf").status_code == 200


def test_loss_non_vede_il_pulsante_pdf(client, db, paziente, crea_utente, accedi):
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    assert "/pdf" not in client.get("/").get_data(as_text=True)


def test_il_pdf_di_un_paziente_dimesso_da_404(client, db, paziente, amministratore, accedi):
    from app.pazienti import servizi as servizi_pazienti

    servizi_pazienti.elimina_paziente(paziente, amministratore.id)
    db.session.commit()
    accedi("capo", "capo1234")

    assert client.get(f"/paziente/{paziente.id}/pdf").status_code == 404
