"""Test del passo 4: la home «Pazienti ricoverati»."""

from datetime import date, timedelta

import pytest

from app import audit
from app.models import (
    RUOLO_INFERMIERE,
    RUOLO_OSS,
    STATO_ELIMINATO,
    STATO_RICOVERATO,
    EventoAudit,
    Paziente,
    Reparto,
)
from app.pazienti import servizi


def _eventi(db, azione):
    return db.session.query(EventoAudit).filter_by(azione=azione).all()


def _id_reparto(db, codice):
    return db.session.query(Reparto).filter_by(codice=codice).one().id


# --------------------------------------------------------------------------
# Ordinamento naturale dei letti
# --------------------------------------------------------------------------
def test_il_letto_2_viene_prima_del_letto_10():
    """In ordine alfabetico «A-10» verrebbe prima di «A-2». In reparto no."""
    letti = ["A-10", "A-2", "A-1", "A-21", "A-3"]

    ordinati = sorted(letti, key=servizi.chiave_naturale)

    assert ordinati == ["A-1", "A-2", "A-3", "A-10", "A-21"]


def test_lordinamento_naturale_ignora_le_maiuscole():
    assert sorted(["b-1", "A-2"], key=servizi.chiave_naturale) == ["A-2", "b-1"]


def test_lordinamento_naturale_regge_letti_senza_numeri():
    assert sorted(["BOX", "A-1"], key=servizi.chiave_naturale) == ["A-1", "BOX"]


# --------------------------------------------------------------------------
# Ordinamento dell'elenco
# --------------------------------------------------------------------------
def test_i_pazienti_sono_ordinati_per_dimissione(db, crea_paziente):
    oggi = date(2026, 9, 20)
    crea_paziente(posto_letto="A-01", cognome="Tardi", data_dimissione_presunta=oggi + timedelta(days=10))
    crea_paziente(posto_letto="A-02", cognome="Presto", data_dimissione_presunta=oggi + timedelta(days=1))
    crea_paziente(posto_letto="A-03", cognome="Medio", data_dimissione_presunta=oggi + timedelta(days=5))

    elenco = servizi.pazienti_ricoverati(_id_reparto(db, "AOUP"))

    assert [p.cognome for p in elenco] == ["Presto", "Medio", "Tardi"]


def test_chi_non_ha_data_va_in_fondo(db, crea_paziente):
    crea_paziente(posto_letto="A-01", cognome="SenzaData", data_dimissione_presunta=None)
    crea_paziente(
        posto_letto="A-02", cognome="ConData", data_dimissione_presunta=date(2026, 12, 31)
    )

    elenco = servizi.pazienti_ricoverati(_id_reparto(db, "AOUP"))

    assert [p.cognome for p in elenco] == ["ConData", "SenzaData"]


def test_a_parita_di_data_ordina_per_letto_naturale(db, crea_paziente):
    stessa_data = date(2026, 10, 1)
    crea_paziente(posto_letto="A-10", cognome="Dieci", data_dimissione_presunta=stessa_data)
    crea_paziente(posto_letto="A-2", cognome="Due", data_dimissione_presunta=stessa_data)

    elenco = servizi.pazienti_ricoverati(_id_reparto(db, "AOUP"))

    assert [p.cognome for p in elenco] == ["Due", "Dieci"]


def test_i_pazienti_eliminati_non_compaiono(db, crea_paziente):
    paziente = crea_paziente(posto_letto="A-01")
    paziente.stato = STATO_ELIMINATO
    db.session.commit()

    assert servizi.pazienti_ricoverati(_id_reparto(db, "AOUP")) == []


# --------------------------------------------------------------------------
# Inserimento
# --------------------------------------------------------------------------
def test_inserimento_dalla_pagina(client, db, amministratore, accedi):
    accedi("capo", "capo1234")

    risposta = client.post(
        "/paziente/nuovo",
        data={
            "reparto_id": _id_reparto(db, "AOUP"),
            "nome": "Mario",
            "cognome": "Rossi",
            "posto_letto": "A-01",
            "data_arrivo": "2026-09-18",
            "data_dimissione_presunta": "",
        },
    )

    assert risposta.status_code == 302
    paziente = db.session.query(Paziente).filter_by(cognome="Rossi").one()
    assert paziente.posto_letto == "A-01"
    assert paziente.gravita == "nv"
    assert paziente.stato == STATO_RICOVERATO
    assert len(_eventi(db, audit.PAZIENTE_CREATO)) == 1


def test_gli_spazi_ai_bordi_vengono_tolti(db, amministratore):
    paziente = servizi.crea_paziente(
        reparto_id=_id_reparto(db, "AOUP"),
        nome="  Mario  ",
        cognome="  Rossi ",
        posto_letto=" A-01 ",
        data_arrivo=date(2026, 9, 1),
        data_dimissione_presunta=None,
        autore_id=amministratore.id,
    )

    assert paziente.nome == "Mario"
    assert paziente.cognome == "Rossi"
    assert paziente.posto_letto == "A-01"


def test_il_letto_occupato_viene_rifiutato_col_nome(db, crea_paziente, amministratore):
    crea_paziente(posto_letto="A-01", nome="Mario", cognome="Rossi")

    with pytest.raises(servizi.ErroreDiRegola) as errore:
        servizi.crea_paziente(
            reparto_id=_id_reparto(db, "AOUP"),
            nome="Anna",
            cognome="Bianchi",
            posto_letto="A-01",
            data_arrivo=date(2026, 9, 1),
            data_dimissione_presunta=None,
            autore_id=amministratore.id,
        )

    assert "A-01" in str(errore.value)
    assert "Rossi Mario" in str(errore.value)


def test_il_letto_di_un_eliminato_e_riassegnabile(db, crea_paziente, amministratore):
    primo = crea_paziente(posto_letto="A-01")
    primo.stato = STATO_ELIMINATO
    db.session.commit()

    nuovo = servizi.crea_paziente(
        reparto_id=_id_reparto(db, "AOUP"),
        nome="Anna",
        cognome="Bianchi",
        posto_letto="A-01",
        data_arrivo=date(2026, 9, 1),
        data_dimissione_presunta=None,
        autore_id=amministratore.id,
    )
    db.session.commit()

    assert nuovo.id is not None


def test_la_dimissione_prima_dellarrivo_viene_rifiutata(db, amministratore):
    with pytest.raises(servizi.ErroreDiRegola):
        servizi.crea_paziente(
            reparto_id=_id_reparto(db, "AOUP"),
            nome="Mario",
            cognome="Rossi",
            posto_letto="A-01",
            data_arrivo=date(2026, 9, 10),
            data_dimissione_presunta=date(2026, 9, 5),
            autore_id=amministratore.id,
        )


def test_un_nome_vuoto_viene_rifiutato(db, amministratore):
    with pytest.raises(servizi.ErroreDiRegola):
        servizi.crea_paziente(
            reparto_id=_id_reparto(db, "AOUP"),
            nome="   ",
            cognome="Rossi",
            posto_letto="A-01",
            data_arrivo=date(2026, 9, 1),
            data_dimissione_presunta=None,
            autore_id=amministratore.id,
        )


# --------------------------------------------------------------------------
# Gravità
# --------------------------------------------------------------------------
def test_il_ciclo_della_gravita():
    assert servizi.prossima_gravita("nv") == "verde"
    assert servizi.prossima_gravita("verde") == "giallo"
    assert servizi.prossima_gravita("giallo") == "rosso"
    assert servizi.prossima_gravita("rosso") == "nv"


def test_cambio_gravita_dalla_pagina(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente()
    accedi("capo", "capo1234")

    risposta = client.post(f"/paziente/{paziente.id}/gravita")

    assert risposta.status_code == 200
    assert risposta.get_json() == {"gravita": "verde", "etichetta": "Stabile"}
    assert paziente.gravita == "verde"
    assert len(_eventi(db, audit.GRAVITA_MODIFICATA)) == 1


def test_loss_non_puo_cambiare_la_gravita(client, db, crea_paziente, crea_utente, accedi):
    paziente = crea_paziente()
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    risposta = client.post(f"/paziente/{paziente.id}/gravita")

    assert risposta.status_code == 403
    assert paziente.gravita == "nv"


# --------------------------------------------------------------------------
# Dimissione presunta
# --------------------------------------------------------------------------
def test_modifica_dimissione_dalla_pagina(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente(data_arrivo=date(2026, 9, 1))
    accedi("capo", "capo1234")

    client.post(
        f"/paziente/{paziente.id}/dimissione",
        data={"data_dimissione_presunta": "2026-09-30"},
    )

    assert paziente.data_dimissione_presunta == date(2026, 9, 30)
    assert len(_eventi(db, audit.DIMISSIONE_MODIFICATA)) == 1


def test_la_dimissione_si_puo_svuotare(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente(
        data_arrivo=date(2026, 9, 1), data_dimissione_presunta=date(2026, 9, 30)
    )
    accedi("capo", "capo1234")

    client.post(f"/paziente/{paziente.id}/dimissione", data={"data_dimissione_presunta": ""})

    assert paziente.data_dimissione_presunta is None


def test_la_dimissione_non_puo_finire_prima_dellarrivo(
    client, db, crea_paziente, amministratore, accedi
):
    paziente = crea_paziente(data_arrivo=date(2026, 9, 10))
    accedi("capo", "capo1234")

    client.post(
        f"/paziente/{paziente.id}/dimissione",
        data={"data_dimissione_presunta": "2026-09-05"},
    )

    assert paziente.data_dimissione_presunta is None


# --------------------------------------------------------------------------
# Spostamento di reparto
# --------------------------------------------------------------------------
def test_spostamento_in_un_altro_reparto(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente(codice_reparto="AOUP", posto_letto="A-01")
    destinazione = _id_reparto(db, "S1")
    accedi("capo", "capo1234")

    client.post(
        f"/paziente/{paziente.id}/sposta",
        data={"reparto_id": destinazione, "posto_letto": "L1-07"},
    )

    assert paziente.reparto_id == destinazione
    assert paziente.posto_letto == "L1-07"
    assert len(_eventi(db, audit.PAZIENTE_SPOSTATO)) == 1


def test_lo_spostamento_conserva_la_storia(db, crea_paziente):
    """Note e date restano attaccate al paziente: non è un reinserimento."""
    paziente = crea_paziente(
        codice_reparto="AOUP",
        posto_letto="A-01",
        data_arrivo=date(2026, 9, 1),
        data_dimissione_presunta=date(2026, 9, 30),
    )
    identificativo = paziente.id

    servizi.sposta_di_reparto(paziente, _id_reparto(db, "S2"), "L2-03")
    db.session.commit()

    assert paziente.id == identificativo
    assert paziente.data_arrivo == date(2026, 9, 1)
    assert paziente.data_dimissione_presunta == date(2026, 9, 30)


def test_non_si_sposta_su_un_letto_occupato(db, crea_paziente):
    primo = crea_paziente(codice_reparto="S1", posto_letto="L1-02", cognome="Conti")
    secondo = crea_paziente(codice_reparto="AOUP", posto_letto="A-01")

    with pytest.raises(servizi.ErroreDiRegola) as errore:
        servizi.sposta_di_reparto(secondo, primo.reparto_id, "L1-02")

    assert "Conti" in str(errore.value)


def test_spostare_un_paziente_dove_gia_si_trova_e_un_errore(db, crea_paziente):
    paziente = crea_paziente(codice_reparto="AOUP", posto_letto="A-01")

    with pytest.raises(servizi.ErroreDiRegola):
        servizi.sposta_di_reparto(paziente, paziente.reparto_id, "A-01")


# --------------------------------------------------------------------------
# Eliminazione
# --------------------------------------------------------------------------
def test_eliminazione_dalla_pagina(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente()
    accedi("capo", "capo1234")

    client.post(f"/paziente/{paziente.id}/elimina", data={})

    assert paziente.stato == STATO_ELIMINATO
    assert paziente.eliminato_da == amministratore.id
    assert paziente.eliminato_il is not None
    assert len(_eventi(db, audit.PAZIENTE_ELIMINATO)) == 1


def test_leliminazione_e_logica_la_riga_resta(client, db, crea_paziente, amministratore, accedi):
    paziente = crea_paziente()
    identificativo = paziente.id
    accedi("capo", "capo1234")

    client.post(f"/paziente/{paziente.id}/elimina", data={})

    assert db.session.get(Paziente, identificativo) is not None


def test_linfermiere_puo_eliminare(client, db, crea_paziente, crea_utente, accedi):
    """Decisione concordata: la specifica lo riservava al solo ADMIN."""
    paziente = crea_paziente()
    crea_utente(username="inf", password="password1", ruolo=RUOLO_INFERMIERE)
    accedi("inf", "password1")

    client.post(f"/paziente/{paziente.id}/elimina", data={})

    assert paziente.stato == STATO_ELIMINATO


def test_loss_non_puo_eliminare(client, db, crea_paziente, crea_utente, accedi):
    paziente = crea_paziente()
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    risposta = client.post(f"/paziente/{paziente.id}/elimina", data={})

    assert risposta.status_code == 403
    assert paziente.stato == STATO_RICOVERATO


def test_un_paziente_gia_eliminato_da_404(client, db, crea_paziente, amministratore, accedi):
    """Chi tiene aperta una pagina vecchia non deve poter agire su dati superati."""
    paziente = crea_paziente()
    accedi("capo", "capo1234")
    client.post(f"/paziente/{paziente.id}/elimina", data={})

    risposta = client.post(f"/paziente/{paziente.id}/elimina", data={})

    assert risposta.status_code == 404


# --------------------------------------------------------------------------
# La pagina
# --------------------------------------------------------------------------
def test_la_home_mostra_i_tre_reparti(client, amministratore, accedi):
    accedi("capo", "capo1234")

    pagina = client.get("/").get_data(as_text=True)

    assert "AOUP" in pagina
    assert "Setting 1 — Low Care 1" in pagina
    assert "Setting 2 — Low Care 2" in pagina


def test_il_conteggio_e_al_singolare_con_un_paziente(client, crea_paziente, amministratore, accedi):
    crea_paziente()
    accedi("capo", "capo1234")

    pagina = client.get("/").get_data(as_text=True)

    assert "1 paziente" in pagina
    assert "nessun paziente" in pagina  # gli altri due reparti sono vuoti


def test_un_reparto_vuoto_lo_dice(client, amministratore, accedi):
    accedi("capo", "capo1234")

    pagina = client.get("/").get_data(as_text=True)

    assert "Nessun paziente ricoverato in questo reparto" in pagina


def test_il_paziente_compare_come_cognome_nome(client, crea_paziente, amministratore, accedi):
    crea_paziente(nome="Mario", cognome="Rossi")
    accedi("capo", "capo1234")

    assert "Rossi Mario" in client.get("/").get_data(as_text=True)


def test_senza_data_la_home_scrive_da_definire(client, crea_paziente, amministratore, accedi):
    crea_paziente(data_dimissione_presunta=None)
    accedi("capo", "capo1234")

    assert "da definire" in client.get("/").get_data(as_text=True)


def test_loss_non_vede_i_pulsanti_che_non_puo_usare(
    client, crea_paziente, crea_utente, accedi
):
    crea_paziente()
    crea_utente(username="oss", password="password1", ruolo=RUOLO_OSS)
    accedi("oss", "password1")

    pagina = client.get("/").get_data(as_text=True)

    assert "Inserisci paziente" not in pagina
    assert 'data-azione="apri-elimina"' not in pagina
    assert "sola lettura" in pagina


def test_la_home_non_contiene_javascript_dentro_lhtml(
    client, crea_paziente, amministratore, accedi
):
    """La Content-Security-Policy lo bloccherebbe, e il pulsante non funzionerebbe.

    Il guaio è che l'errore comparirebbe solo nella console del browser: in
    reparto si vedrebbe soltanto un pulsante che non fa niente.
    """
    crea_paziente()
    accedi("capo", "capo1234")

    pagina = client.get("/").get_data(as_text=True)

    assert "onclick=" not in pagina
    assert "onchange=" not in pagina
    assert "onsubmit=" not in pagina
