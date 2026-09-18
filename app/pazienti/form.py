"""I form dell'area pazienti.

I controlli sui singoli campi (obbligatorio, lunghezza massima) stanno qui.
Le regole che hanno bisogno del database — il letto occupato, la dimissione
prima dell'arrivo — stanno invece in servizi.py: un form non deve interrogare
il database, altrimenti non si riesce più a provarlo da solo.
"""

from wtforms import DateField, HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from flask_wtf import FlaskForm


class FormNuovoPaziente(FlaskForm):
    reparto_id = HiddenField(validators=[DataRequired()])
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
    posto_letto = StringField(
        "Posto letto",
        validators=[
            DataRequired(message="Il posto letto è obbligatorio."),
            Length(max=10, message="Il posto letto non può superare 10 caratteri."),
        ],
    )
    data_arrivo = DateField(
        "Data di arrivo",
        validators=[DataRequired(message="La data di arrivo è obbligatoria.")],
    )
    # Optional() accetta il campo vuoto: la dimissione presunta spesso non si
    # conosce al momento del ricovero.
    data_dimissione_presunta = DateField(
        "Data presunta di dimissione", validators=[Optional()]
    )
    invia = SubmitField("Inserisci paziente")


class FormDimissione(FlaskForm):
    """Modifica della sola data presunta di dimissione."""

    data_dimissione_presunta = DateField(
        "Dimissione presunta", validators=[Optional()]
    )
    invia = SubmitField("Salva")


class FormSposta(FlaskForm):
    """Spostamento in un altro reparto, o in un altro letto dello stesso."""

    reparto_id = SelectField("Reparto di destinazione", coerce=int)
    posto_letto = StringField(
        "Nuovo posto letto",
        validators=[
            DataRequired(message="Il posto letto è obbligatorio."),
            Length(max=10, message="Il posto letto non può superare 10 caratteri."),
        ],
    )
    invia = SubmitField("Sposta")


class FormConferma(FlaskForm):
    """Form senza campi, che porta solo il token CSRF.

    Serve alle azioni che non chiedono dati ma cambiano qualcosa, come la
    dimissione di un paziente. Anche un'azione senza campi va protetta: senza
    token, un sito esterno potrebbe farla eseguire al posto dell'utente.
    """

    invia = SubmitField("Conferma")
