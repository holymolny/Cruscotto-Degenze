"""Avvia il Cruscotto Degenze con Waitress.

Waitress è lo stesso server che verrà usato in reparto: meglio provare qui
quello vero che il server di sviluppo di Flask, che è comodo per scrivere
codice ma non è fatto per essere usato davvero.

Sul PC il programma ascolta solo su 127.0.0.1, cioè su questo stesso
computer: nessun altro sulla rete di casa può collegarsi.

    .venv\\Scripts\\python.exe installazione\\server.py
"""

from __future__ import annotations

import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from waitress import serve  # noqa: E402

from app import create_app  # noqa: E402

INDIRIZZO = "127.0.0.1"
PORTA = 8000


def main() -> None:
    applicazione = create_app()

    print()
    print("  ============================================================")
    print("   Cruscotto Degenze")
    print("  ============================================================")
    print(f"   Indirizzo:  http://{INDIRIZZO}:{PORTA}")
    print("   Il browser dovrebbe aprirsi da solo fra pochi istanti.")
    print()
    print("   NON chiudere questa finestra mentre usi il programma:")
    print("   è qui dentro che gira. Per spegnerlo, chiudila o premi Ctrl+C.")
    print("  ============================================================")
    print(flush=True)

    # ident: il nome con cui il server si presenta nelle risposte HTTP. Quello
    # predefinito direbbe "waitress" e la sua versione, che è un'informazione
    # in più regalata a chi volesse cercare falle note.
    serve(applicazione, listen=f"{INDIRIZZO}:{PORTA}", ident="Cruscotto Degenze")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n   Cruscotto Degenze spento.")
