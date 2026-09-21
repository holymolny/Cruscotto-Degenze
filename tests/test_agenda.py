"""Test dei passi 5 e 6: Agenda delle note e checklist di dimissione."""

from datetime import date, timedelta

import pytest

from app import audit
from app.agenda import servizi
from app.dati_fissi import VOCI_CHECKLIST
from app.formati import oggi_italia
from app.models import (
    RUOLO_ADMIN,
    RUOLO_AMMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
    ChecklistSpunta,
    EventoAudit,
    Nota,
    NotaVersione,
)


def _eventi(db, azione):
    return db.session.query(EventoAudit).filter_by(azione=azione).all()


@pytest.fixture
def paziente(crea_paziente):
    return crea_paziente(nome="Mario", cognome="Rossi", posto_letto="A-01")


@pytest.fixture
def infermiere(crea_utente):
    return crea_utente(
        username="cbianchi",
        password="password1",
        ruolo=RUOLO_INFERMIERE,
        nome="Carlo",
        cognome="Bianchi",
    )


@pytest.fixture
def medico(crea_utente):
    return crea_utente(
        username="mrossi",
        password="password1",
        ruolo=RUOLO_MEDICO,
        nome="Mario",
        cognome="Rossi",
    )


# --------------------------------------------------------------------------
# Scrittura delle note
# --------------------------------------------------------------------------
def test_la_nota_conserva_la_firma_di_chi_scrive(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Parametri stabili.")
    db.session.commit()

    assert nota.autore_nome == "Carlo Bianchi"
    assert nota.autore_ruolo == RUOLO_INFERMIERE
    assert nota.data_nota == oggi_italia()


def test_la_firma_non_cambia_se_lutente_cambia_ruolo(db, paziente, infermiere):
    """È il motivo per cui nome e ruolo sono copiati dentro la nota."""
    nota = servizi.crea_nota(paziente, infermiere, "Medicazione eseguita.")
    db.session.commit()

    infermiere.ruolo = RUOLO_MEDICO
    infermiere.cognome = "Bianchi-Neri"
    db.session.commit()

    assert nota.autore_ruolo == RUOLO_INFERMIERE
    assert nota.autore_nome == "Carlo Bianchi"


def test_una_nota_vuota_viene_rifiutata(db, paziente, infermiere):
    with pytest.raises(servizi.ErroreDiRegola):
        servizi.crea_nota(paziente, infermiere, "    ")


def test_una_nota_troppo_lunga_viene_rifiutata(db, paziente, infermiere):
    with pytest.raises(servizi.ErroreDiRegola):
        servizi.crea_nota(paziente, infermiere, "x" * 2001)


def test_duemila_caratteri_esatti_sono_ammessi(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "x" * 2000)
    db.session.commit()

    assert len(nota.testo) == 2000


def test_gli_a_capo_vengono_conservati(db, paziente, infermiere):
    servizi.crea_nota(paziente, infermiere, "Prima riga.\nSeconda riga.")
    db.session.commit()

    assert "\n" in servizi.note_visibili(paziente.id)[0].testo


# --------------------------------------------------------------------------
# Ordine e raggruppamento
# --------------------------------------------------------------------------
def test_le_note_vanno_dalla_piu_recente_alla_piu_vecchia(db, paziente, infermiere):
    oggi = oggi_italia()
    for scarto, testo in ((-2, "vecchia"), (0, "nuova"), (-1, "media")):
        nota = servizi.crea_nota(paziente, infermiere, testo)
        db.session.flush()
        nota.data_nota = oggi + timedelta(days=scarto)
    db.session.commit()

    testi = [nota.testo for nota in servizi.note_visibili(paziente.id)]

    assert testi == ["nuova", "media", "vecchia"]


def test_a_parita_di_giorno_viene_prima_lultima_scritta(db, paziente, infermiere):
    servizi.crea_nota(paziente, infermiere, "prima")
    db.session.commit()
    servizi.crea_nota(paziente, infermiere, "seconda")
    db.session.commit()

    testi = [nota.testo for nota in servizi.note_visibili(paziente.id)]

    assert testi == ["seconda", "prima"]


def test_le_note_si_raggruppano_per_giorno(db, paziente, infermiere):
    oggi = oggi_italia()
    for scarto in (0, 0, -1):
        nota = servizi.crea_nota(paziente, infermiere, "testo")
        db.session.flush()
        nota.data_nota = oggi + timedelta(days=scarto)
    db.session.commit()

    gruppi = servizi.raggruppa_per_giorno(servizi.note_visibili(paziente.id))

    assert len(gruppi) == 2
    assert len(gruppi[0][1]) == 2
    assert len(gruppi[1][1]) == 1


def test_lintestazione_di_oggi_dice_oggi():
    oggi = oggi_italia()

    assert servizi.intestazione_giorno(oggi).startswith("Oggi, ")
    assert servizi.intestazione_giorno(date(2020, 1, 15)) == "15/01/2020"


# --------------------------------------------------------------------------
# Modifica: solo l'autore
# --------------------------------------------------------------------------
def test_lautore_puo_modificare_la_propria_nota(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Testo iniziale.")
    db.session.commit()

    servizi.modifica_nota(nota, infermiere, "Testo corretto.")
    db.session.commit()

    assert nota.testo == "Testo corretto."
    assert nota.modificata_il is not None


def test_la_modifica_conserva_il_testo_precedente(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Testo iniziale.")
    db.session.commit()

    servizi.modifica_nota(nota, infermiere, "Testo corretto.")
    db.session.commit()

    versioni = db.session.query(NotaVersione).filter_by(nota_id=nota.id).all()
    assert len(versioni) == 1
    assert versioni[0].testo_precedente == "Testo iniziale."
    assert versioni[0].sostituito_da == infermiere.id


def test_un_altro_utente_non_puo_modificare(db, paziente, infermiere, medico):
    nota = servizi.crea_nota(paziente, infermiere, "Testo dell'infermiere.")
    db.session.commit()

    with pytest.raises(servizi.ErroreDiRegola):
        servizi.modifica_nota(nota, medico, "Riscritta dal medico.")


def test_nemmeno_lamministratore_puo_modificare(db, paziente, infermiere, amministratore):
    """Una nota è una dichiarazione firmata: se l'ADMIN potesse riscriverla,
    la firma non varrebbe più niente."""
    nota = servizi.crea_nota(paziente, infermiere, "Testo dell'infermiere.")
    db.session.commit()

    with pytest.raises(servizi.ErroreDiRegola):
        servizi.modifica_nota(nota, amministratore, "Riscritta dall'admin.")


def test_la_modifica_non_puo_svuotare_la_nota(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Testo iniziale.")
    db.session.commit()

    with pytest.raises(servizi.ErroreDiRegola):
        servizi.modifica_nota(nota, infermiere, "   ")


def test_riscrivere_lo_stesso_testo_non_crea_una_versione(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Testo uguale.")
    db.session.commit()

    servizi.modifica_nota(nota, infermiere, "Testo uguale.")
    db.session.commit()

    assert db.session.query(NotaVersione).count() == 0
    assert nota.modificata_il is None


# --------------------------------------------------------------------------
# Eliminazione: logica, solo l'autore
# --------------------------------------------------------------------------
def test_lautore_puo_eliminare_la_propria_nota(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Da eliminare.")
    db.session.commit()

    servizi.elimina_nota(nota, infermiere)
    db.session.commit()

    assert nota.eliminata
    assert nota.eliminata_da == infermiere.id
    assert servizi.note_visibili(paziente.id) == []


def test_la_nota_eliminata_resta_nel_database(db, paziente, infermiere):
    nota = servizi.crea_nota(paziente, infermiere, "Da eliminare.")
    db.session.commit()
    identificativo = nota.id

    servizi.elimina_nota(nota, infermiere)
    db.session.commit()

    assert db.session.get(Nota, identificativo) is not None


def test_un_altro_utente_non_puo_eliminare(db, paziente, infermiere, medico):
    nota = servizi.crea_nota(paziente, infermiere, "Testo.")
    db.session.commit()

    with pytest.raises(servizi.ErroreDiRegola):
        servizi.elimina_nota(nota, medico)


# --------------------------------------------------------------------------
# Dalle pagine
# --------------------------------------------------------------------------
def test_apertura_dellagenda(client, paziente, infermiere, accedi):
    accedi("cbianchi", "password1")

    risposta = client.get(f"/paziente/{paziente.id}/agenda")

    assert risposta.status_code == 200
    dati = risposta.get_json()
    assert dati["note"] == 0
    assert "Checklist dimissione" in dati["html"]


def test_scrittura_di_una_nota_dalla_pagina(client, db, paziente, infermiere, accedi):
    accedi("cbianchi", "password1")

    risposta = client.post(
        f"/paziente/{paziente.id}/nota", data={"testo": "Parametri stabili."}
    )

    dati = risposta.get_json()
    assert dati["note"] == 1
    assert "Parametri stabili." in dati["html"]
    assert "Infermiere:" in dati["html"]
    assert len(_eventi(db, audit.NOTA_CREATA)) == 1


def test_il_registro_non_contiene_il_testo_della_nota(client, db, paziente, infermiere, accedi):
    accedi("cbianchi", "password1")
    client.post(f"/paziente/{paziente.id}/nota", data={"testo": "Diagnosi riservata."})

    for evento in db.session.query(EventoAudit).all():
        assert "Diagnosi riservata" not in (evento.dettagli or "")


def test_loss_non_puo_scrivere_note(client, paziente, crea_utente, accedi):
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    risposta = client.post(f"/paziente/{paziente.id}/nota", data={"testo": "Prova."})

    assert risposta.status_code == 403


def test_loss_vede_lagenda_in_sola_lettura(client, paziente, crea_utente, accedi):
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    html = client.get(f"/paziente/{paziente.id}/agenda").get_json()["html"]

    assert "non scrivere note" in html
    assert 'data-azione="modifica-nota"' not in html


def test_il_server_rifiuta_la_modifica_di_una_nota_altrui(
    client, db, paziente, infermiere, medico, accedi
):
    """Il pulsante non compare, ma chi conosce l'indirizzo può provare lo stesso."""
    nota = servizi.crea_nota(paziente, infermiere, "Testo dell'infermiere.")
    db.session.commit()

    accedi("mrossi", "password1")
    risposta = client.post(f"/nota/{nota.id}/modifica", data={"testo": "Riscritta."})

    assert nota.testo == "Testo dell'infermiere."
    assert "Solo chi ha scritto la nota" in risposta.get_json()["html"]


def test_eliminazione_di_una_nota_dalla_pagina(client, db, paziente, infermiere, accedi):
    nota = servizi.crea_nota(paziente, infermiere, "Da eliminare.")
    db.session.commit()
    accedi("cbianchi", "password1")

    risposta = client.post(f"/nota/{nota.id}/elimina", data={})

    assert nota.eliminata
    assert risposta.get_json()["note"] == 0
    assert len(_eventi(db, audit.NOTA_ELIMINATA)) == 1


def test_il_contatore_note_in_home_si_aggiorna(client, db, paziente, infermiere, accedi):
    accedi("cbianchi", "password1")
    client.post(f"/paziente/{paziente.id}/nota", data={"testo": "Prima nota."})

    home = client.get("/").get_data(as_text=True)

    assert f'data-contatore-note="{paziente.id}">1<' in home


# --------------------------------------------------------------------------
# Checklist
# --------------------------------------------------------------------------
def test_un_nuovo_paziente_ha_la_checklist_vuota(db, paziente):
    assert servizi.codici_spuntati(paziente.id) == set()


def test_spuntare_e_togliere_una_voce(db, paziente):
    totale = servizi.imposta_spunta(paziente, "DIMISSIBILE", True)
    db.session.commit()
    assert totale == 1
    assert "DIMISSIBILE" in servizi.codici_spuntati(paziente.id)

    totale = servizi.imposta_spunta(paziente, "DIMISSIBILE", False)
    db.session.commit()
    assert totale == 0


def test_spuntare_due_volte_non_raddoppia(db, paziente):
    servizi.imposta_spunta(paziente, "ESAMI", True)
    totale = servizi.imposta_spunta(paziente, "ESAMI", True)
    db.session.commit()

    assert totale == 1


def test_una_voce_inesistente_viene_rifiutata(db, paziente):
    with pytest.raises(servizi.ErroreDiRegola):
        servizi.imposta_spunta(paziente, "NON_ESISTE", True)


def test_la_spunta_non_registra_chi_e_quando(db, paziente):
    """La specifica lo esclude: è uno strumento di reparto, non un registro."""
    servizi.imposta_spunta(paziente, "ESAMI", True)
    db.session.commit()

    spunta = db.session.query(ChecklistSpunta).one()
    colonne = {colonna.name for colonna in spunta.__table__.columns}

    assert colonne == {"paziente_id", "voce_codice"}


def test_spunta_dalla_pagina(client, db, paziente, infermiere, accedi):
    accedi("cbianchi", "password1")

    risposta = client.post(
        f"/paziente/{paziente.id}/checklist",
        json={"codice": "DIMISSIBILE", "spuntata": True},
    )

    assert risposta.status_code == 200
    assert risposta.get_json() == {"spuntate": 1, "totale": len(VOCI_CHECKLIST)}


def test_loss_non_puo_spuntare(client, db, paziente, crea_utente, accedi):
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    risposta = client.post(
        f"/paziente/{paziente.id}/checklist",
        json={"codice": "DIMISSIBILE", "spuntata": True},
    )

    assert risposta.status_code == 403
    assert servizi.codici_spuntati(paziente.id) == set()


def test_lammin_vede_la_checklist_disabilitata(client, paziente, crea_utente, accedi):
    crea_utente(username="it", password="password1", ruolo=RUOLO_AMMIN)
    accedi("it", "password1")

    html = client.get(f"/paziente/{paziente.id}/agenda").get_json()["html"]

    assert "disabled" in html
    assert "non modificarla" in html


def test_il_contatore_arriva_in_fondo(db, paziente):
    for codice, _ in VOCI_CHECKLIST:
        totale = servizi.imposta_spunta(paziente, codice, True)
    db.session.commit()

    assert totale == len(VOCI_CHECKLIST)


def test_le_spunte_restano_dopo_leliminazione_del_paziente(db, paziente, amministratore):
    """Note, versioni e checklist restano nel database: lo dice la specifica."""
    from app.pazienti import servizi as servizi_pazienti

    servizi.imposta_spunta(paziente, "ESAMI", True)
    db.session.commit()

    servizi_pazienti.elimina_paziente(paziente, amministratore.id)
    db.session.commit()

    assert db.session.query(ChecklistSpunta).filter_by(paziente_id=paziente.id).count() == 1
