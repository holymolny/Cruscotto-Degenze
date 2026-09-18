"""Area «pdf»: la scheda paziente da stampare.

Il PDF si genera sul server e non nel browser. Tre motivi: funziona uguale su
Edge e su Chrome senza dipendere da una libreria caricata nella pagina; non
serve internet; e il documento riporta esattamente i dati del database, non
quelli che per caso erano a schermo in quel momento.
"""

from flask import Blueprint

pdf_bp = Blueprint("pdf", __name__)

from app.pdf import routes  # noqa: E402,F401
