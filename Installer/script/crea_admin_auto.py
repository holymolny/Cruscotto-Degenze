"""Crea il primo amministratore senza fare domande.

Il comando «flask crea-admin» chiede i dati a chi lo lancia dal terminale.
Durante l'installazione, però, i dati li ha già raccolti la procedura
guidata: rifarli chiedere in una finestra nera sarebbe sia brutto sia
fragile. Qui li leggiamo dalle variabili d'ambiente preparate da
Configura.ps1, e per il resto facciamo le stesse identiche cose di
app/comandi.py — stessi controlli, stesso utente.

Le variabili d'ambiente, e non gli argomenti della riga di comando, perché
gli argomenti di un processo sono leggibili da qualunque altro programma
guardi l'elenco dei processi: la password finirebbe in chiaro là dentro.

    set CRUSCOTTO_ADMIN_NOME=Mario
    set CRUSCOTTO_ADMIN_COGNOME=Rossi
    set CRUSCOTTO_ADMIN_USERNAME=mrossi
    set CRUSCOTTO_ADMIN_PASSWORD=...
    .venv\\Scripts\\python.exe installazione\\crea_admin_auto.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Questo file sta in «installazione», una cartella sotto la radice del
# programma: senza questa riga «import app» non troverebbe nulla, perché
# Python cerca i moduli a partire dalla cartella dello script.
RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from app import create_app  # noqa: E402
from app.comandi import LUNGHEZZA_MINIMA_PASSWORD  # noqa: E402
from app.estensioni import db  # noqa: E402
from app.models import RUOLO_ADMIN, Utente  # noqa: E402


def _leggi(nome_variabile: str) -> str:
    return os.environ.get(nome_variabile, "").strip()


def main() -> int:
    nome = _leggi("CRUSCOTTO_ADMIN_NOME")
    cognome = _leggi("CRUSCOTTO_ADMIN_COGNOME")
    # La password non si "strippa": uno spazio all'inizio o alla fine è un
    # carattere come un altro, e toglierlo significherebbe salvare una
    # password diversa da quella che la persona ha digitato.
    password = os.environ.get("CRUSCOTTO_ADMIN_PASSWORD", "")
    username = Utente.normalizza_username(_leggi("CRUSCOTTO_ADMIN_USERNAME"))

    if not nome or not cognome or not username:
        print("Nome, cognome e nome utente non possono essere vuoti.", file=sys.stderr)
        return 1

    if len(password) < LUNGHEZZA_MINIMA_PASSWORD:
        print(
            f"La password deve avere almeno {LUNGHEZZA_MINIMA_PASSWORD} caratteri.",
            file=sys.stderr,
        )
        return 1

    app = create_app()
    with app.app_context():
        # Reinstallazione sopra un'installazione esistente: il database c'è
        # già, con dentro gli utenti veri. Rifare l'amministratore sarebbe
        # nella migliore delle ipotesi inutile, nella peggiore un modo per
        # ritrovarsi due account con lo stesso nome.
        gia_presente = db.session.query(Utente).filter_by(ruolo=RUOLO_ADMIN).first()
        if gia_presente is not None:
            print(
                f"C'è già un amministratore («{gia_presente.username}»): "
                "lascio il database com'è."
            )
            return 0

        if db.session.query(Utente).filter_by(username=username).first() is not None:
            print(f"Il nome utente «{username}» esiste già.", file=sys.stderr)
            return 1

        amministratore = Utente(
            username=username,
            nome=nome,
            cognome=cognome,
            ruolo=RUOLO_ADMIN,
            attivo=True,
            # La password l'ha scelta chi sta installando, non qualcun altro
            # per lui: non ha senso obbligarlo a cambiarla al primo accesso.
            deve_cambiare_password=False,
            creato_da=None,  # non c'era nessuno prima di lui
        )
        amministratore.imposta_password(password)

        db.session.add(amministratore)
        db.session.commit()

    print(f"Amministratore «{username}» creato ({nome} {cognome}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
