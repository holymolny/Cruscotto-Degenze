"""voce checklist «Modulo Privacy Somministrato»

Aggiunge in fondo alla checklist di dimissione la voce PRIVACY.

L'inserimento avviene solo se la voce manca. Su un database nuovo ci pensa
già la migrazione iniziale, che legge l'elenco completo da dati_fissi.py;
su un database già installato invece la voce non c'è, e la aggiungiamo qui.
Così la stessa migrazione va bene in entrambi i casi.

Revision ID: b7e2a91c4d10
Revises: 042c1d4c264a
Create Date: 2026-09-21 09:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e2a91c4d10'
down_revision = '042c1d4c264a'
branch_labels = None
depends_on = None

# Scritti qui e non letti da dati_fissi.py: la migrazione deve restare
# identica anche se un domani l'elenco cambia.
CODICE = "PRIVACY"
TESTO = "Modulo Privacy Somministrato"

tabella_voce = sa.table(
    "voce_checklist",
    sa.column("codice", sa.Unicode),
    sa.column("testo", sa.Unicode),
    sa.column("ordine", sa.Integer),
    sa.column("attiva", sa.Boolean),
)


def upgrade():
    connessione = op.get_bind()
    esiste = connessione.execute(
        sa.select(tabella_voce.c.codice).where(tabella_voce.c.codice == CODICE)
    ).first()
    if esiste:
        return

    ultimo = connessione.execute(sa.select(sa.func.max(tabella_voce.c.ordine))).scalar() or 0
    op.bulk_insert(
        tabella_voce,
        [{"codice": CODICE, "testo": TESTO, "ordine": ultimo + 1, "attiva": True}],
    )


def downgrade():
    # Prima le spunte, che puntano alla voce: altrimenti il vincolo di chiave
    # esterna impedirebbe di cancellarla.
    op.execute(sa.text("DELETE FROM checklist_spunta WHERE voce_codice = :c").bindparams(c=CODICE))
    op.execute(tabella_voce.delete().where(tabella_voce.c.codice == CODICE))
