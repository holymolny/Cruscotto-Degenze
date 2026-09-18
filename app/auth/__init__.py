"""Area «accesso»: login, logout, cambio password, profilo.

Un <b>blueprint</b> è un pezzo di applicazione con le sue pagine e i suoi
template, che poi viene innestato nell'applicazione vera. Serve a non
ritrovarsi, fra sei mesi, con un unico file da duemila righe in cui la
funzione del login sta accanto a quella che genera il PDF.

Ogni area del Cruscotto avrà il suo: auth, pazienti, agenda, pdf, utenti.
"""

from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# L'import sta in fondo, e non in cima, di proposito: routes.py ha bisogno di
# auth_bp per registrarci sopra le pagine, quindi il blueprint deve esistere
# prima. Metterlo in cima darebbe un errore di import circolare.
from app.auth import routes  # noqa: E402,F401
