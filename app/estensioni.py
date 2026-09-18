"""Le estensioni di Flask, create qui una volta sola.

Perché in un file a parte e non dentro create_app()? Perché servono anche
agli altri moduli: models.py ha bisogno di "db" per definire le tabelle.
Se "db" nascesse dentro create_app(), models.py dovrebbe importare
l'applicazione, e l'applicazione importa models.py: i due file si
aspetterebbero a vicenda e Python si fermerebbe con un errore di import
circolare.

La soluzione standard di Flask è questa: le estensioni nascono vuote qui,
e vengono collegate all'applicazione più tardi con init_app().
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Traduce le classi Python in tabelle del database e viceversa.
db = SQLAlchemy()

# Tiene allineata la struttura del database quando i modelli cambiano.
migrate = Migrate()

# Ricorda chi è collegato e protegge le pagine riservate.
login_manager = LoginManager()

# Impedisce che un sito esterno faccia eseguire azioni al tuo browser
# sfruttando la sessione aperta sul Cruscotto.
csrf = CSRFProtect()
