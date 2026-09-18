"""Test del passo 3: l'accesso.

Sono i test più importanti scritti finora: riguardano chi entra nel programma
e con quali panni. Un errore qui non si vede a occhio, ma fa finire una nota
firmata dalla persona sbagliata.
"""

from datetime import timedelta

from app import audit
from app.auth import servizi
from app.formati import adesso_utc
from app.models import (
    RUOLO_ADMIN,
    RUOLO_AMMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
    EventoAudit,
)
from app.permessi import (
    ELIMINARE_PAZIENTE,
    GESTIRE_UTENTI,
    SCARICARE_PDF,
    SCRIVERE_NOTE,
    ha_permesso,
)


def _eventi(db, azione):
    return db.session.query(EventoAudit).filter_by(azione=azione).all()


# --------------------------------------------------------------------------
# Accesso riuscito
# --------------------------------------------------------------------------
def test_accesso_con_credenziali_giuste(client, amministratore, accedi):
    risposta = accedi("capo", "capo1234")

    assert risposta.status_code == 302
    assert risposta.headers["Location"] == "/"


def test_dopo_laccesso_la_barra_mostra_nome_e_ruolo(client, amministratore, accedi):
    accedi("capo", "capo1234")

    pagina = client.get("/").get_data(as_text=True)

    assert "Anna Ricci" in pagina
    assert "Amministratore" in pagina


def test_il_nome_utente_non_distingue_le_maiuscole(client, amministratore, accedi):
    risposta = accedi("CAPO", "capo1234")

    assert risposta.status_code == 302


def test_laccesso_riuscito_finisce_nel_registro(db, amministratore, accedi):
    accedi("capo", "capo1234")

    eventi = _eventi(db, audit.LOGIN_OK)

    assert len(eventi) == 1
    assert eventi[0].utente_id == amministratore.id


def test_laccesso_aggiorna_lultimo_accesso(db, amministratore, accedi):
    assert amministratore.ultimo_accesso is None

    accedi("capo", "capo1234")

    assert amministratore.ultimo_accesso is not None


# --------------------------------------------------------------------------
# Accesso rifiutato
# --------------------------------------------------------------------------
def test_password_sbagliata(client, amministratore, accedi):
    risposta = accedi("capo", "sbagliata1")

    assert risposta.status_code == 401
    assert servizi.ERRORE_ACCESSO in risposta.get_data(as_text=True)


def test_utente_inesistente_da_lo_stesso_messaggio(client, accedi):
    """Se il messaggio cambiasse, chi prova nomi a caso capirebbe quali esistono."""
    risposta = accedi("nessuno", "qualsiasi1")

    assert risposta.status_code == 401
    assert servizi.ERRORE_ACCESSO in risposta.get_data(as_text=True)


def test_utente_disattivato_non_entra(client, crea_utente, accedi):
    crea_utente(username="sospeso", password="password1", attivo=False)

    risposta = accedi("sospeso", "password1")

    assert risposta.status_code == 401


def test_il_tentativo_fallito_finisce_nel_registro(db, amministratore, accedi):
    accedi("capo", "sbagliata1")

    eventi = _eventi(db, audit.LOGIN_FALLITO)

    assert len(eventi) == 1
    assert eventi[0].username_tentato == "capo"


def test_il_registro_non_contiene_mai_la_password(db, amministratore, accedi):
    accedi("capo", "PasswordSegreta9")

    for evento in db.session.query(EventoAudit).all():
        assert "PasswordSegreta9" not in (evento.dettagli or "")
        assert "PasswordSegreta9" not in (evento.username_tentato or "")


# --------------------------------------------------------------------------
# Blocco dopo 5 tentativi
# --------------------------------------------------------------------------
def test_cinque_tentativi_falliti_bloccano_laccount(db, amministratore, accedi):
    for _ in range(5):
        accedi("capo", "sbagliata1")

    assert servizi.account_bloccato(amministratore)


def test_laccount_bloccato_rifiuta_anche_la_password_giusta(db, amministratore, accedi):
    for _ in range(5):
        accedi("capo", "sbagliata1")

    risposta = accedi("capo", "capo1234")

    assert risposta.status_code == 401


def test_quattro_tentativi_non_bastano_a_bloccare(db, amministratore, accedi):
    for _ in range(4):
        accedi("capo", "sbagliata1")

    assert not servizi.account_bloccato(amministratore)
    assert accedi("capo", "capo1234").status_code == 302


def test_laccesso_riuscito_azzera_il_contatore(db, amministratore, accedi):
    for _ in range(3):
        accedi("capo", "sbagliata1")
    accedi("capo", "capo1234")

    assert amministratore.tentativi_falliti == 0


def test_passati_i_quindici_minuti_il_blocco_scade(db, amministratore, accedi):
    for _ in range(5):
        accedi("capo", "sbagliata1")

    # Spostiamo indietro la scadenza invece di aspettare davvero.
    amministratore.bloccato_fino = adesso_utc() - timedelta(seconds=1)
    db.session.commit()

    assert not servizi.account_bloccato(amministratore)
    assert accedi("capo", "capo1234").status_code == 302


def test_dopo_lo_sblocco_ci_sono_di_nuovo_cinque_tentativi(db, amministratore, accedi):
    """Il contatore si azzera insieme al blocco, non resta a 5."""
    for _ in range(5):
        accedi("capo", "sbagliata1")

    assert amministratore.tentativi_falliti == 0


# --------------------------------------------------------------------------
# Uscita
# --------------------------------------------------------------------------
def test_uscita(client, amministratore, accedi, db):
    accedi("capo", "capo1234")

    risposta = client.get("/esci")

    assert risposta.status_code == 302
    assert risposta.headers["Location"] == "/accedi"
    assert len(_eventi(db, audit.LOGOUT)) == 1
    # Dopo l'uscita la home torna a essere irraggiungibile.
    assert client.get("/").status_code == 302


def test_chi_non_e_collegato_viene_mandato_al_login(client):
    risposta = client.get("/")

    assert risposta.status_code == 302
    assert "/accedi" in risposta.headers["Location"]


# --------------------------------------------------------------------------
# Cambio password obbligatorio
# --------------------------------------------------------------------------
def test_chi_deve_cambiare_password_non_apre_altre_pagine(
    client, crea_utente, accedi
):
    crea_utente(username="nuovo", password="temporanea1", deve_cambiare_password=True)
    accedi("nuovo", "temporanea1")

    risposta = client.get("/")

    assert risposta.status_code == 302
    assert risposta.headers["Location"] == "/cambia-password"


def test_chi_deve_cambiare_password_puo_comunque_uscire(client, crea_utente, accedi):
    """Altrimenti chi sbaglia account resterebbe intrappolato."""
    crea_utente(username="nuovo", password="temporanea1", deve_cambiare_password=True)
    accedi("nuovo", "temporanea1")

    assert client.get("/esci").status_code == 302


def test_il_cambio_password_toglie_lobbligo(client, db, crea_utente, accedi):
    utente = crea_utente(
        username="nuovo", password="temporanea1", deve_cambiare_password=True
    )
    accedi("nuovo", "temporanea1")

    risposta = client.post(
        "/cambia-password",
        data={
            "password_attuale": "temporanea1",
            "nuova_password": "miapassword9",
            "conferma_password": "miapassword9",
        },
    )

    assert risposta.status_code == 302
    assert not utente.deve_cambiare_password
    assert utente.password_corretta("miapassword9")
    assert len(_eventi(db, audit.PASSWORD_CAMBIATA)) == 1


def test_il_cambio_password_richiede_quella_attuale(client, crea_utente, accedi):
    utente = crea_utente(username="nuovo", password="temporanea1")
    accedi("nuovo", "temporanea1")

    client.post(
        "/cambia-password",
        data={
            "password_attuale": "sbagliata1",
            "nuova_password": "miapassword9",
            "conferma_password": "miapassword9",
        },
    )

    assert utente.password_corretta("temporanea1")


# --------------------------------------------------------------------------
# Requisiti della nuova password
# --------------------------------------------------------------------------
def test_password_troppo_corta_rifiutata():
    assert servizi.errore_nuova_password("abc123") is not None


def test_password_senza_numeri_rifiutata():
    assert servizi.errore_nuova_password("soltantolettere") is not None


def test_password_senza_lettere_rifiutata():
    assert servizi.errore_nuova_password("123456789") is not None


def test_password_uguale_alla_precedente_rifiutata():
    errore = servizi.errore_nuova_password("password1", password_attuale="password1")

    assert errore is not None


def test_password_valida_accettata():
    assert servizi.errore_nuova_password("reparto2026") is None


def test_gli_accenti_contano_come_lettere():
    """«perché2026» deve passare: la È è una lettera a tutti gli effetti."""
    assert servizi.errore_nuova_password("perché2026") is None


# --------------------------------------------------------------------------
# Scadenza per inattività
# --------------------------------------------------------------------------
def test_la_sessione_scade_dopo_i_minuti_previsti(client, app, amministratore, accedi):
    accedi("capo", "capo1234")
    minuti = app.config["MINUTI_INATTIVITA"]

    # Facciamo credere alla sessione che l'ultima attività sia vecchia.
    with client.session_transaction() as sessione:
        sessione["ultima_attivita"] = (
            adesso_utc() - timedelta(minutes=minuti + 1)
        ).timestamp()

    risposta = client.get("/")

    assert risposta.status_code == 302
    assert risposta.headers["Location"] == "/accedi"


def test_una_sessione_attiva_non_scade(client, app, amministratore, accedi):
    accedi("capo", "capo1234")
    minuti = app.config["MINUTI_INATTIVITA"]

    with client.session_transaction() as sessione:
        sessione["ultima_attivita"] = (
            adesso_utc() - timedelta(minutes=minuti - 1)
        ).timestamp()

    assert client.get("/").status_code == 200


def test_ogni_richiesta_fa_ripartire_il_conto(client, app, amministratore, accedi):
    """Sono 15 minuti di inattività, non 15 minuti di collegamento."""
    accedi("capo", "capo1234")
    minuti = app.config["MINUTI_INATTIVITA"]

    with client.session_transaction() as sessione:
        vecchio = (adesso_utc() - timedelta(minutes=minuti - 1)).timestamp()
        sessione["ultima_attivita"] = vecchio

    client.get("/")

    with client.session_transaction() as sessione:
        assert sessione["ultima_attivita"] > vecchio


# --------------------------------------------------------------------------
# Matrice dei permessi
# --------------------------------------------------------------------------
def test_solo_ladmin_gestisce_gli_utenti():
    assert ha_permesso(RUOLO_ADMIN, GESTIRE_UTENTI)
    for ruolo in (RUOLO_MEDICO, RUOLO_INFERMIERE, RUOLO_OSS, RUOLO_AMMIN):
        assert not ha_permesso(ruolo, GESTIRE_UTENTI)


def test_scrivono_note_solo_admin_medico_infermiere():
    for ruolo in (RUOLO_ADMIN, RUOLO_MEDICO, RUOLO_INFERMIERE):
        assert ha_permesso(ruolo, SCRIVERE_NOTE)
    for ruolo in (RUOLO_OSS, RUOLO_AMMIN):
        assert not ha_permesso(ruolo, SCRIVERE_NOTE)


def test_il_pdf_lo_scaricano_tutti_tranne_loss():
    for ruolo in (RUOLO_ADMIN, RUOLO_MEDICO, RUOLO_INFERMIERE, RUOLO_AMMIN):
        assert ha_permesso(ruolo, SCARICARE_PDF)
    assert not ha_permesso(RUOLO_OSS, SCARICARE_PDF)


def test_dimettono_un_paziente_admin_medico_infermiere():
    """Decisione concordata: la specifica lo riservava al solo ADMIN."""
    for ruolo in (RUOLO_ADMIN, RUOLO_MEDICO, RUOLO_INFERMIERE):
        assert ha_permesso(ruolo, ELIMINARE_PAZIENTE)
    for ruolo in (RUOLO_OSS, RUOLO_AMMIN):
        assert not ha_permesso(ruolo, ELIMINARE_PAZIENTE)


def test_lo_stemma_compare_nella_barra_laterale(client, amministratore, accedi):
    accedi("capo", "capo1234")

    assert "img/logo-emblema.png" in client.get("/").get_data(as_text=True)


def test_la_voce_gestione_utenti_compare_solo_alladmin(
    client, crea_utente, accedi
):
    crea_utente(username="inf", password="password1", ruolo=RUOLO_INFERMIERE)
    accedi("inf", "password1")

    assert "Gestione utenti" not in client.get("/").get_data(as_text=True)
