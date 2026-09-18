"""Area «pazienti»: la home del Cruscotto.

Al passo 3 contiene solo la home segnaposto, che serve come approdo dopo
l'accesso. Al passo 4 diventerà l'elenco vero, con i tre riquadri per reparto.
"""

from flask import Blueprint

pazienti_bp = Blueprint("pazienti", __name__)

from app.pazienti import routes  # noqa: E402,F401
