"""Punto di ingresso per il server di produzione (Waitress).

Waitress non sa nulla di create_app(): si aspetta di trovare in un file una
variabile già pronta, che per convenzione si chiama "app". Questo file serve
solo a costruirla.

    waitress-serve --listen=127.0.0.1:8000 wsgi:app
"""

from app import create_app

app = create_app()
