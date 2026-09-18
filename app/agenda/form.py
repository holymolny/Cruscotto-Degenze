"""I form dell'Agenda."""

from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class FormNota(FlaskForm):
    """Usato sia per scrivere una nota nuova sia per modificarne una."""

    testo = TextAreaField(
        "Nota",
        validators=[
            DataRequired(message="Il testo della nota non può essere vuoto."),
            Length(max=2000, message="La nota non può superare 2000 caratteri."),
        ],
    )
    invia = SubmitField("Salva nota")


class FormSenzaCampi(FlaskForm):
    """Porta soltanto il token CSRF, per le azioni che non chiedono dati.

    L'eliminazione di una nota non ha campi da compilare, ma cambia comunque
    qualcosa: senza token, un sito esterno potrebbe farla eseguire al posto
    dell'utente sfruttando la sua sessione aperta.
    """

    invia = SubmitField("Conferma")
