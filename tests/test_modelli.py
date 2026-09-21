"""Test del passo 2: il database si comporta come previsto.

Questi test non provano Python: provano le <i>regole</i> che abbiamo chiesto
al database di far rispettare. Sono quelli che, fra sei mesi, diranno se una
modifica apparentemente innocua ha rotto qualcosa di importante.
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.dati_fissi import REPARTI, VOCI_CHECKLIST
from app.models import (
    RUOLO_INFERMIERE,
    STATO_ELIMINATO,
    Reparto,
    Utente,
    VoceChecklist,
)


# --------------------------------------------------------------------------
# Dati fissi
# --------------------------------------------------------------------------
def test_i_tre_reparti_esistono(db):
    codici = [r.codice for r in db.session.query(Reparto).order_by(Reparto.ordine)]

    assert codici == ["AOUP", "S1", "S2"]


def test_le_voci_della_checklist_esistono(db):
    voci = db.session.query(VoceChecklist).order_by(VoceChecklist.ordine).all()

    assert len(voci) == len(VOCI_CHECKLIST) == 21
    assert voci[0].codice == "DIMISSIBILE"
    assert voci[-1].codice == "PRIVACY"


def test_gli_accenti_sopravvivono_al_salvataggio(db):
    """Se i tipi Unicode fossero sbagliati, «Continuità» tornerebbe «Continuit?»."""
    voce = db.session.get(VoceChecklist, "CONTINUITA")

    assert voce.testo == "Continuità assistenziale attivata"


def test_il_nome_del_reparto_conserva_il_trattino_lungo(db):
    reparto = db.session.query(Reparto).filter_by(codice="S1").one()

    assert reparto.nome == "Setting 1 — Low Care 1"


# --------------------------------------------------------------------------
# Password
# --------------------------------------------------------------------------
def test_la_password_non_viene_mai_salvata_in_chiaro(db):
    utente = Utente(
        username="cbianchi", nome="Carlo", cognome="Bianchi", ruolo=RUOLO_INFERMIERE
    )
    utente.imposta_password("segreto123")

    assert "segreto123" not in utente.password_hash
    assert utente.password_hash.startswith("scrypt:")


def test_la_password_giusta_viene_riconosciuta(db):
    utente = Utente(
        username="cbianchi", nome="Carlo", cognome="Bianchi", ruolo=RUOLO_INFERMIERE
    )
    utente.imposta_password("segreto123")

    assert utente.password_corretta("segreto123")
    assert not utente.password_corretta("segreto124")
    assert not utente.password_corretta("Segreto123")


def test_due_utenti_con_la_stessa_password_hanno_impronte_diverse(db):
    """Ogni impronta usa un «sale» casuale.

    Senza, chi rubasse il database vedrebbe subito quali utenti condividono la
    stessa password, e una sola password indovinata ne aprirebbe più di una.
    """
    primo = Utente(username="a", nome="A", cognome="A", ruolo=RUOLO_INFERMIERE)
    secondo = Utente(username="b", nome="B", cognome="B", ruolo=RUOLO_INFERMIERE)
    primo.imposta_password("stessapassword")
    secondo.imposta_password("stessapassword")

    assert primo.password_hash != secondo.password_hash


def test_il_nome_utente_si_normalizza_in_minuscolo():
    assert Utente.normalizza_username("  MRossi  ") == "mrossi"
    assert Utente.normalizza_username("MROSSI") == "mrossi"


def test_il_nome_utente_e_unico(db):
    for _ in range(2):
        utente = Utente(
            username="mrossi", nome="Mario", cognome="Rossi", ruolo=RUOLO_INFERMIERE
        )
        utente.imposta_password("password1")
        db.session.add(utente)

    with pytest.raises(IntegrityError):
        db.session.commit()


# --------------------------------------------------------------------------
# Regole sul paziente
# --------------------------------------------------------------------------
def test_un_letto_occupato_non_si_puo_riassegnare(db, crea_paziente):
    crea_paziente(codice_reparto="AOUP", posto_letto="A-01")

    with pytest.raises(IntegrityError):
        crea_paziente(
            codice_reparto="AOUP", posto_letto="A-01", nome="Anna", cognome="Bianchi"
        )


def test_lo_stesso_letto_in_reparti_diversi_e_ammesso(db, crea_paziente):
    """A-01 dell'AOUP e A-01 del Setting 1 sono due letti diversi."""
    crea_paziente(codice_reparto="AOUP", posto_letto="A-01")
    secondo = crea_paziente(
        codice_reparto="S1", posto_letto="A-01", nome="Anna", cognome="Bianchi"
    )

    assert secondo.id is not None


def test_il_letto_di_un_paziente_eliminato_torna_libero(db, crea_paziente):
    """È il motivo per cui l'indice è «parziale».

    Se contasse anche i pazienti eliminati, un letto usato in passato
    resterebbe bloccato per sempre.
    """
    primo = crea_paziente(posto_letto="A-01")
    primo.stato = STATO_ELIMINATO
    db.session.commit()

    nuovo = crea_paziente(posto_letto="A-01", nome="Anna", cognome="Bianchi")

    assert nuovo.id is not None


def test_la_dimissione_non_puo_precedere_larrivo(db, crea_paziente):
    with pytest.raises(IntegrityError):
        crea_paziente(
            data_arrivo=date(2026, 9, 10),
            data_dimissione_presunta=date(2026, 9, 5),
        )


def test_la_dimissione_puo_coincidere_con_larrivo(db, crea_paziente):
    """Un ricovero di un giorno solo è legittimo."""
    paziente = crea_paziente(
        data_arrivo=date(2026, 9, 10), data_dimissione_presunta=date(2026, 9, 10)
    )

    assert paziente.id is not None


def test_la_dimissione_puo_mancare(db, crea_paziente):
    paziente = crea_paziente(data_dimissione_presunta=None)

    assert paziente.data_dimissione_presunta is None


def test_un_nuovo_paziente_parte_non_valutato(db, crea_paziente):
    paziente = crea_paziente()

    assert paziente.gravita == "nv"
    assert paziente.etichetta_gravita == "Non valutato"
    assert paziente.spunte == []


def test_letichetta_del_paziente_e_cognome_nome(db, crea_paziente):
    paziente = crea_paziente(nome="Mario", cognome="Rossi")

    assert paziente.etichetta == "Rossi Mario"


def test_il_nome_completo_dellutente_e_nome_cognome(amministratore):
    """Nelle firme delle note l'ordine è l'opposto: «Anna Ricci», non «Ricci Anna»."""
    assert amministratore.nome_completo == "Anna Ricci"
    assert amministratore.etichetta_ruolo == "Amministratore"


# --------------------------------------------------------------------------
# Coerenza fra i dati fissi e la specifica
# --------------------------------------------------------------------------
def test_i_codici_della_checklist_sono_tutti_diversi():
    codici = [codice for codice, _ in VOCI_CHECKLIST]

    assert len(codici) == len(set(codici))


def test_i_codici_dei_reparti_sono_tutti_diversi():
    codici = [codice for codice, _, _ in REPARTI]

    assert len(codici) == len(set(codici))
