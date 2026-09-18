"""I dati che esistono da sempre: i tre reparti e le 20 voci della checklist.

Stanno qui e non dentro la migrazione perché servono in due posti: la
migrazione li inserisce nel database la prima volta, e i test li usano per
costruire un database di prova. Scriverli una volta sola evita che le due
copie prendano strade diverse.
"""

# (codice, nome mostrato, ordine di visualizzazione)
REPARTI = [
    ("AOUP", "AOUP", 1),
    ("S1", "Setting 1 — Low Care 1", 2),
    ("S2", "Setting 2 — Low Care 2", 3),
]

# (codice, testo). L'ordine della lista è l'ordine di visualizzazione.
VOCI_CHECKLIST = [
    ("DIMISSIBILE", "Paziente dimissibile"),
    ("ESAMI", "Esami completati"),
    ("REFERTI", "Referti acquisiti"),
    ("TERAPIA", "Terapia definita"),
    ("PRESCRIZIONI", "Prescrizioni predisposte"),
    ("LETTERA_PRED", "Lettera di dimissione predisposta"),
    ("LETTERA_FIRMA", "Lettera firmata"),
    ("CATETERE", "Catetere: definito mantenimento/rimozione"),
    ("MEDICAZIONI", "Medicazioni programmate"),
    ("AUSILI", "Ausili prescritti"),
    ("PALLIATIVISTI", "Palliativisti attivati se necessari"),
    ("CONTINUITA", "Continuità assistenziale attivata"),
    ("DATA_DIM", "Data dimissione concordata"),
    ("FAMILIARI", "Familiari avvisati"),
    ("TRASP_DEFINITO", "Trasporto necessario definito"),
    ("TRASP_RICHIESTO", "Trasporto richiesto"),
    ("TRASP_CONFERMATO", "Trasporto confermato"),
    ("DOCUMENTAZIONE", "Documentazione consegnata"),
    ("FARMACI", "Farmaci consegnati/prescritti"),
    ("EFFETTI", "Effetti personali consegnati"),
]
