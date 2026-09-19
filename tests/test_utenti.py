"""Test del passo 8: l'area «Gestione utenti».

Due gruppi. Il primo prova le regole da solo, senza aprire nessuna pagina:
sono funzioni normali che ricevono oggetti e sollevano eccezioni. Il secondo
prova le pagine, perché una regola rispettata dai servizi ma dimenticata in
una route non protegge nulla.
"""

import pytest

from app import audit
from app.auth.servizi import account_bloccato
from app.formati import adesso_utc
from app.models import (
    RUOLO_ADMIN,
    RUOLO_INFERMIERE,
    RUOLO_MEDICO,
    RUOLO_OSS,
    EventoAudit,
    Utente,
)
from app.utenti import servizi


def _eventi(db, azione):
    return db.session.query(EventoAudit).filter_by(azione=azione).all()


def _utente(db, username):
    return db.session.query(Utente).filter_by(username=username).one()


# --------------------------------------------------------------------------
# Le regole, senza passare dalle pagine
# --------------------------------------------------------------------------
def test_crea_utente_normalizza_il_nome_utente(db, amministratore):
    utente = servizi.crea_utente(
        nome="  Mario ",
        cognome=" Rossi",
        username="  MRossi ",
        ruolo=RUOLO_MEDICO,
        password="prova2026",
        autore=amministratore,
    )
    db.session.commit()

    assert utente.username == "mrossi"
    assert utente.nome == "Mario"
    assert utente.cognome == "Rossi"


def test_chi_nasce_qui_deve_cambiare_la_password(db, amministratore):
    """La password l'ha scelta l'amministratore: non è ancora personale."""
    utente = servizi.crea_utente(
        nome="Carlo",
        cognome="Bianchi",
        username="cbianchi",
        ruolo=RUOLO_INFERMIERE,
        password="prova2026",
        autore=amministratore,
    )
    db.session.commit()

    assert utente.deve_cambiare_password is True
    assert utente.attivo is True
    assert utente.creato_da == amministratore.id


def test_il_nome_utente_non_si_puo_ripetere(db, amministratore, crea_utente):
    crea_utente(username="mrossi")

    with pytest.raises(servizi.ErroreDiRegola, match="già in uso"):
        servizi.crea_utente(
            nome="Marco",
            cognome="Rossini",
            username="MRossi",  # stesso nome utente, scritto diverso
            ruolo=RUOLO_MEDICO,
            password="prova2026",
            autore=amministratore,
        )


def test_il_nome_utente_non_puo_avere_spazi(db, amministratore):
    with pytest.raises(servizi.ErroreDiRegola, match="spazi"):
        servizi.crea_utente(
            nome="Mario",
            cognome="Rossi",
            username="mario rossi",
            ruolo=RUOLO_MEDICO,
            password="prova2026",
            autore=amministratore,
        )


def test_la_password_iniziale_rispetta_i_requisiti(db, amministratore):
    """Gli stessi che valgono quando un utente se la cambia da sé."""
    with pytest.raises(servizi.ErroreDiRegola, match="numero"):
        servizi.crea_utente(
            nome="Mario",
            cognome="Rossi",
            username="mrossi",
            ruolo=RUOLO_MEDICO,
            password="soltantolettere",
            autore=amministratore,
        )


def test_un_ruolo_inventato_viene_rifiutato(db, amministratore):
    with pytest.raises(servizi.ErroreDiRegola, match="Ruolo non valido"):
        servizi.crea_utente(
            nome="Mario",
            cognome="Rossi",
            username="mrossi",
            ruolo="PRIMARIO",
            password="prova2026",
            autore=amministratore,
        )


# --------------------------------------------------------------------------
# L'ultimo amministratore
# --------------------------------------------------------------------------
def test_lultimo_amministratore_non_si_disattiva(db, amministratore, crea_utente):
    """Senza amministratori attivi nessuno potrebbe più gestire gli utenti."""
    altro = crea_utente(username="capo2", ruolo=RUOLO_ADMIN)

    # Il primo dei due si può disattivare: ne resta un altro.
    servizi.disattiva(amministratore, autore=altro)
    db.session.commit()

    # Adesso «altro» è rimasto solo, e il programma deve rifiutarsi.
    with pytest.raises(servizi.ErroreDiRegola, match="unico amministratore"):
        servizi.disattiva(altro, autore=amministratore)

    assert altro.attivo is True


def test_con_due_amministratori_se_ne_puo_disattivare_uno(db, amministratore, crea_utente):
    altro = crea_utente(username="capo2", ruolo=RUOLO_ADMIN)

    servizi.disattiva(altro, autore=amministratore)
    db.session.commit()

    assert altro.attivo is False
    assert amministratore.attivo is True


def test_lultimo_amministratore_non_si_retrocede(db, amministratore, crea_utente):
    altro = crea_utente(username="capo2", ruolo=RUOLO_ADMIN)

    # Retrocedere il primo si può: «altro» resta amministratore.
    servizi.modifica_utente(
        amministratore, nome="Anna", cognome="Ricci", ruolo=RUOLO_MEDICO, autore=altro
    )
    db.session.commit()

    with pytest.raises(servizi.ErroreDiRegola, match="unico amministratore"):
        servizi.modifica_utente(
            altro, nome="Capo", cognome="Due", ruolo=RUOLO_MEDICO, autore=amministratore
        )

    assert altro.ruolo == RUOLO_ADMIN


def test_non_ci_si_disattiva_da_soli(db, amministratore, crea_utente):
    """Anche con un altro amministratore in giro: ci si chiuderebbe fuori."""
    crea_utente(username="capo2", ruolo=RUOLO_ADMIN)

    with pytest.raises(
        servizi.ErroreDiRegola, match="^Non puoi disattivare il tuo stesso account\\.$"
    ):
        servizi.disattiva(amministratore, autore=amministratore)

    assert amministratore.attivo is True


def test_non_ci_si_cambia_ruolo_da_soli(db, amministratore, crea_utente):
    crea_utente(username="capo2", ruolo=RUOLO_ADMIN)

    # La frase per intero, non un pezzo: comporla a partire dal verbo dava
    # risultati come «cambiare ruolo al il tuo stesso account».
    with pytest.raises(
        servizi.ErroreDiRegola, match="^Non puoi cambiare ruolo al tuo stesso account\\.$"
    ):
        servizi.modifica_utente(
            amministratore,
            nome="Anna",
            cognome="Ricci",
            ruolo=RUOLO_OSS,
            autore=amministratore,
        )

    assert amministratore.ruolo == RUOLO_ADMIN


def test_cambiare_solo_nome_e_cognome_a_se_stessi_si_puo(db, amministratore):
    """Il divieto riguarda il ruolo, non il resto."""
    servizi.modifica_utente(
        amministratore,
        nome="Annamaria",
        cognome="Ricci",
        ruolo=RUOLO_ADMIN,
        autore=amministratore,
    )
    db.session.commit()

    assert amministratore.nome == "Annamaria"


# --------------------------------------------------------------------------
# Disattivazione, riattivazione, password
# --------------------------------------------------------------------------
def test_riattivare_toglie_anche_il_blocco(db, amministratore, crea_utente):
    from datetime import timedelta

    utente = crea_utente(username="mrossi", ruolo=RUOLO_MEDICO, attivo=False)
    utente.bloccato_fino = adesso_utc() + timedelta(minutes=15)
    utente.tentativi_falliti = 3
    db.session.commit()

    servizi.riattiva(utente)
    db.session.commit()

    assert utente.attivo is True
    assert account_bloccato(utente) is False


def test_reimpostare_la_password_obbliga_a_cambiarla(db, crea_utente):
    utente = crea_utente(username="mrossi", password="vecchia01", ruolo=RUOLO_MEDICO)

    servizi.reimposta_password(utente, "nuova2026")
    db.session.commit()

    assert utente.password_corretta("nuova2026")
    assert not utente.password_corretta("vecchia01")
    assert utente.deve_cambiare_password is True


def test_reimpostare_la_password_sblocca_laccount(db, crea_utente):
    """Chi chiede la password nuova ha quasi sempre già sbagliato cinque volte."""
    from datetime import timedelta

    utente = crea_utente(username="mrossi", ruolo=RUOLO_MEDICO)
    utente.bloccato_fino = adesso_utc() + timedelta(minutes=15)
    db.session.commit()

    servizi.reimposta_password(utente, "nuova2026")
    db.session.commit()

    assert account_bloccato(utente) is False


def test_non_si_disattiva_due_volte(db, amministratore, crea_utente):
    utente = crea_utente(username="mrossi", ruolo=RUOLO_MEDICO, attivo=False)

    with pytest.raises(servizi.ErroreDiRegola, match="già disattivato"):
        servizi.disattiva(utente, autore=amministratore)


# --------------------------------------------------------------------------
# L'elenco
# --------------------------------------------------------------------------
def test_gli_attivi_vengono_prima_dei_disattivati(db, amministratore, crea_utente):
    crea_utente(username="aaa", cognome="Aaa", ruolo=RUOLO_MEDICO, attivo=False)
    crea_utente(username="zzz", cognome="Zzz", ruolo=RUOLO_MEDICO, attivo=True)

    elenco = servizi.elenco_utenti()

    assert elenco[-1].username == "aaa"
    assert all(u.attivo for u in elenco[:-1])


# --------------------------------------------------------------------------
# Le pagine: permessi
# --------------------------------------------------------------------------
def test_lamministratore_vede_lelenco(client, amministratore, accedi):
    accedi()

    risposta = client.get("/utenti")

    assert risposta.status_code == 200
    assert "Gestione utenti" in risposta.get_data(as_text=True)


@pytest.mark.parametrize("ruolo", [RUOLO_MEDICO, RUOLO_INFERMIERE, RUOLO_OSS])
def test_chi_non_e_amministratore_riceve_403(client, crea_utente, accedi, ruolo):
    """Nascondere la voce nel menu non basta: la route deve rifiutare."""
    crea_utente(username="tizio", password="prova2026", ruolo=ruolo)
    accedi("tizio", "prova2026")

    assert client.get("/utenti").status_code == 403
    assert client.post("/utenti/nuovo", data={}).status_code == 403


def test_senza_accesso_si_viene_rimandati_alla_pagina_di_accesso(client):
    risposta = client.get("/utenti")

    assert risposta.status_code == 302
    assert "/accedi" in risposta.headers["Location"]


# --------------------------------------------------------------------------
# Le pagine: operazioni
# --------------------------------------------------------------------------
def test_creare_un_utente_dalla_pagina(client, db, amministratore, accedi):
    accedi()

    risposta = client.post(
        "/utenti/nuovo",
        data={
            "nome": "Mario",
            "cognome": "Rossi",
            "username": "mrossi",
            "ruolo": RUOLO_MEDICO,
            "password": "prova2026",
            "conferma_password": "prova2026",
        },
        follow_redirects=True,
    )

    assert risposta.status_code == 200
    utente = _utente(db, "mrossi")
    assert utente.ruolo == RUOLO_MEDICO
    assert len(_eventi(db, audit.UTENTE_CREATO)) == 1


def test_la_password_non_finisce_mai_nel_registro(client, db, amministratore, accedi):
    accedi()
    client.post(
        "/utenti/nuovo",
        data={
            "nome": "Mario",
            "cognome": "Rossi",
            "username": "mrossi",
            "ruolo": RUOLO_MEDICO,
            "password": "segretissima9",
            "conferma_password": "segretissima9",
        },
    )

    for evento in db.session.query(EventoAudit).all():
        assert "segretissima9" not in (evento.dettagli or "")


def test_due_password_diverse_non_creano_niente(client, db, amministratore, accedi):
    accedi()

    client.post(
        "/utenti/nuovo",
        data={
            "nome": "Mario",
            "cognome": "Rossi",
            "username": "mrossi",
            "ruolo": RUOLO_MEDICO,
            "password": "prova2026",
            "conferma_password": "prova2027",
        },
    )

    assert db.session.query(Utente).filter_by(username="mrossi").first() is None


def test_disattivare_dalla_pagina(client, db, amministratore, crea_utente, accedi):
    utente = crea_utente(username="mrossi", ruolo=RUOLO_MEDICO)
    accedi()

    client.post(f"/utenti/{utente.id}/disattiva", follow_redirects=True)

    assert _utente(db, "mrossi").attivo is False


def test_lultimo_amministratore_resiste_anche_dalla_pagina(
    client, db, amministratore, accedi
):
    """La difesa vera sta sul server, non nel pulsante disegnato spento."""
    accedi()

    client.post(f"/utenti/{amministratore.id}/disattiva", follow_redirects=True)

    assert _utente(db, "capo").attivo is True


def test_un_utente_inesistente_da_404(client, amministratore, accedi):
    accedi()

    assert client.post("/utenti/9999/disattiva").status_code == 404


def test_reimpostare_la_password_dalla_pagina(
    client, db, amministratore, crea_utente, accedi
):
    utente = crea_utente(username="mrossi", password="vecchia01", ruolo=RUOLO_MEDICO)
    accedi()

    client.post(
        f"/utenti/{utente.id}/password",
        data={"password": "nuova2026", "conferma_password": "nuova2026"},
        follow_redirects=True,
    )

    aggiornato = _utente(db, "mrossi")
    assert aggiornato.password_corretta("nuova2026")
    assert len(_eventi(db, audit.PASSWORD_REIMPOSTATA)) == 1


def test_modificare_ruolo_dalla_pagina(client, db, amministratore, crea_utente, accedi):
    utente = crea_utente(username="mrossi", ruolo=RUOLO_MEDICO)
    accedi()

    client.post(
        f"/utenti/{utente.id}/modifica",
        data={"nome": "Mario", "cognome": "Rossi", "ruolo": RUOLO_INFERMIERE},
        follow_redirects=True,
    )

    assert _utente(db, "mrossi").ruolo == RUOLO_INFERMIERE
    assert len(_eventi(db, audit.UTENTE_MODIFICATO)) == 1
