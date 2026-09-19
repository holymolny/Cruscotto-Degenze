"""Area «Gestione utenti»: chi può entrare nel Cruscotto e con quale ruolo.

Riservata all'amministratore. È l'unico punto del programma da cui si creano
gli account: il primo amministratore invece nasce dal terminale con
«flask crea-admin», perché per usare questa pagina bisogna già essere entrati.

Gli utenti non si cancellano mai, si disattivano. Le note portano la firma di
chi le ha scritte, e una firma che rimanda a un utente sparito non si potrebbe
più risolvere.
"""

from flask import Blueprint

utenti_bp = Blueprint("utenti", __name__)

from app.utenti import routes  # noqa: E402,F401
