"""I form dell'area «Gestione utenti».

Qui stanno i controlli sui singoli campi: obbligatorio, lunghezza massima, le
due password uguali. Le regole che hanno bisogno del database — il nome utente
già preso, l'ultimo amministratore che non si può disattivare — stanno invece
in servizi.py.

La stessa divisione dei pazienti, e per lo stesso motivo: un form che
interroga il database non si riesce più a provare da solo.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from app.models import RUOLI
from app.utenti.servizi import RUOLI_ASSEGNABILI

# (codice, etichetta) nell'ordine in cui si scelgono di solito.
SCELTE_RUOLO = [(codice, RUOLI[codice]) for codice in RUOLI_ASSEGNABILI]


class FormNuovoUtente(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[
            DataRequired(message="Il nome è obbligatorio."),
            Length(max=80, message="Il nome non può superare 80 caratteri."),
        ],
    )
    cognome = StringField(
        "Cognome",
        validators=[
            DataRequired(message="Il cognome è obbligatorio."),
            Length(max=80, message="Il cognome non può superare 80 caratteri."),
        ],
    )
    username = StringField(
        "Nome utente",
        validators=[
            DataRequired(message="Il nome utente è obbligatorio."),
            Length(max=50, message="Il nome utente non può superare 50 caratteri."),
        ],
    )
    ruolo = SelectField("Ruolo", choices=SCELTE_RUOLO, validate_choice=False)
    password = PasswordField(
        "Password iniziale",
        validators=[
            DataRequired(message="Scrivi la password iniziale."),
            Length(min=8, message="La password deve avere almeno 8 caratteri."),
        ],
    )
    conferma_password = PasswordField(
        "Ripeti la password",
        validators=[
            DataRequired(message="Ripeti la password."),
            EqualTo("password", message="Le due password non coincidono."),
        ],
    )
    invia = SubmitField("Crea utente")


class FormModificaUtente(FlaskForm):
    """Nome, cognome e ruolo. Il nome utente non si modifica: vedi servizi.py."""

    nome = StringField(
        "Nome",
        validators=[
            DataRequired(message="Il nome è obbligatorio."),
            Length(max=80, message="Il nome non può superare 80 caratteri."),
        ],
    )
    cognome = StringField(
        "Cognome",
        validators=[
            DataRequired(message="Il cognome è obbligatorio."),
            Length(max=80, message="Il cognome non può superare 80 caratteri."),
        ],
    )
    ruolo = SelectField("Ruolo", choices=SCELTE_RUOLO, validate_choice=False)
    invia = SubmitField("Salva")


class FormPassword(FlaskForm):
    """Reimpostazione della password di qualcun altro."""

    password = PasswordField(
        "Nuova password",
        validators=[
            DataRequired(message="Scrivi la nuova password."),
            Length(min=8, message="La password deve avere almeno 8 caratteri."),
        ],
    )
    conferma_password = PasswordField(
        "Ripeti la password",
        validators=[
            DataRequired(message="Ripeti la password."),
            EqualTo("password", message="Le due password non coincidono."),
        ],
    )
    invia = SubmitField("Reimposta password")


class FormConferma(FlaskForm):
    """Form senza campi, che porta solo il token CSRF.

    Serve a disattivare, riattivare e sbloccare: azioni che non chiedono dati
    ma cambiano qualcosa, e che quindi vanno protette lo stesso. Senza token,
    un sito esterno potrebbe farle eseguire all'amministratore a sua insaputa.
    """

    invia = SubmitField("Conferma")
