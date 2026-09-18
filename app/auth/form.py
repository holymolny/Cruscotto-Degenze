"""I form dell'area accesso.

Un form di Flask-WTF fa tre cose insieme: descrive i campi, li controlla
quando arrivano, e porta con sé il <b>token CSRF</b>.

Cos'è il token CSRF, con un esempio. Sei collegato al Cruscotto. Apri in
un'altra scheda una pagina qualsiasi, che di nascosto invia al Cruscotto la
richiesta «elimina il paziente 12». Il tuo browser allega da solo il cookie
di sessione, e per il server la richiesta sembra tua. Il token CSRF impedisce
questo: ogni form contiene un valore casuale che il server ha generato per
quella sessione, e le richieste che non lo riportano vengono rifiutate. La
pagina esterna quel valore non può conoscerlo.

Il token lo inserisce form.hidden_tag() nei template. Non va mai dimenticato.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length


class FormLogin(FlaskForm):
    username = StringField(
        "Nome utente",
        validators=[DataRequired(message="Scrivi il nome utente.")],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Scrivi la password.")],
    )
    invia = SubmitField("Accedi")


class FormCambioPassword(FlaskForm):
    """Usato sia per il cambio obbligatorio sia dalla pagina «Il mio profilo»."""

    password_attuale = PasswordField(
        "Password attuale",
        validators=[DataRequired(message="Scrivi la password attuale.")],
    )
    nuova_password = PasswordField(
        "Nuova password",
        validators=[
            DataRequired(message="Scrivi la nuova password."),
            Length(min=8, message="La password deve avere almeno 8 caratteri."),
        ],
    )
    conferma_password = PasswordField(
        "Ripeti la nuova password",
        validators=[
            DataRequired(message="Ripeti la nuova password."),
            EqualTo("nuova_password", message="Le due password non coincidono."),
        ],
    )
    invia = SubmitField("Cambia password")
