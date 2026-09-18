"""Area «agenda»: le note organizzative e la checklist di dimissione.

Le pagine di quest'area non restituiscono pagine intere ma <i>pezzi</i> di
pagina: l'Agenda vive dentro una finestra aperta sopra la home, e ricaricare
tutto il cruscotto a ogni nota salvata farebbe perdere la posizione e il
contesto a chi sta lavorando.
"""

from flask import Blueprint

agenda_bp = Blueprint("agenda", __name__)

from app.agenda import routes  # noqa: E402,F401
