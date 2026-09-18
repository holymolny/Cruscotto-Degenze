"""Test dell'impalcatura: quello che deve valere per tutte le pagine.

La pagina di prova del passo 1 non esiste più: dal passo 3 la radice del sito
è la home del Cruscotto, ed è riservata a chi ha fatto l'accesso.
"""


def test_la_pagina_di_accesso_risponde(client):
    risposta = client.get("/accedi")

    assert risposta.status_code == 200
    assert "Cruscotto Degenze" in risposta.get_data(as_text=True)


def test_le_intestazioni_di_sicurezza_ci_sono(client):
    """Se un giorno qualcuno le togliesse per sbaglio, questo test lo segnala."""
    risposta = client.get("/accedi")

    assert risposta.headers["X-Content-Type-Options"] == "nosniff"
    assert risposta.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in risposta.headers["Content-Security-Policy"]


def test_le_intestazioni_valgono_anche_sui_redirect(client):
    """Anche una risposta 302 esce dal server, quindi va protetta uguale."""
    risposta = client.get("/")

    assert risposta.status_code == 302
    assert risposta.headers["X-Content-Type-Options"] == "nosniff"


def test_la_pagina_404_e_in_italiano(client):
    risposta = client.get("/una-pagina-che-non-esiste")

    assert risposta.status_code == 404
    assert "Pagina non trovata" in risposta.get_data(as_text=True)


def test_il_logo_compare_nella_pagina_di_accesso(client):
    pagina = client.get("/accedi").get_data(as_text=True)

    assert "img/logo-casa-cura.png" in pagina


def test_la_pagina_di_accesso_dice_a_chi_rivolgersi(client):
    """Chi non riesce a entrare deve sapere chi chiamare senza doverlo chiedere."""
    pagina = client.get("/accedi").get_data(as_text=True)

    assert "interno 286" in pagina
    assert "amministratore" in pagina


def test_nessun_messaggio_quando_si_viene_rimandati_allaccesso(client):
    """Chi arriva qui vede già il form: dirgli di accedere è superfluo."""
    pagina = client.get("/", follow_redirects=True).get_data(as_text=True)

    assert "Devi accedere" not in pagina
    assert 'class="messaggi"' not in pagina


def test_i_loghi_sono_serviti_e_leggeri(client):
    """Su un PC di reparto un logo pesante è un'attesa a ogni accesso.

    L'originale consegnato dalla grafica pesa 2,1 MB: se un domani qualcuno
    lo copiasse dentro static senza prepararlo, questo test lo fermerebbe.
    """
    for nome in ("logo-casa-cura.png", "logo-emblema.png"):
        risposta = client.get(f"/static/img/{nome}")

        assert risposta.status_code == 200
        assert risposta.headers["Content-Type"] == "image/png"
        assert len(risposta.data) < 100_000, f"{nome} è troppo pesante"


def test_la_pagina_404_non_mostra_dettagli_tecnici(client):
    testo = client.get("/una-pagina-che-non-esiste").get_data(as_text=True)

    assert "Traceback" not in testo
    assert "werkzeug" not in testo.lower()
