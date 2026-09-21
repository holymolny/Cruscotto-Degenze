"""Costruzione del PDF «Informativa sul programma».

È il documento che si scarica dalla pagina di accesso: spiega che cos'è il
Cruscotto, come è stato realizzato, dove funziona, quali dati tratta e con
quali cautele. Serve a chi lo usa per sapere con che cosa ha a che fare, e a
chi dovesse fare un controllo per trovare tutto in un posto solo.

Non contiene dati di pazienti né di utenti: per questo si può scaricare anche
senza aver fatto l'accesso.

I mattoncini (font, colori, piè di pagina numerato) sono quelli della scheda
paziente in generatore.py, così i due documenti hanno lo stesso aspetto.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.formati import data_italiana, oggi_italia
from app.pdf.generatore import (
    BORDO,
    GRASSETTO,
    INCHIOSTRO,
    LARGHEZZA_UTILE,
    MARGINE,
    NORMALE,
    PAGINA,
    TENUE,
    TelaNumerata,
    registra_font,
)

# L'azzurro del logo, lo stesso della scritta «Cruscotto Degenze» a video.
AZZURRO = colors.HexColor("#00A3D4")

LOGO = Path(__file__).resolve().parent.parent / "static" / "img" / "logo-casa-cura.png"
# Proporzioni del file originale (380 x 291 pixel): le scriviamo qui invece
# di leggerle dall'immagine per non dover caricare Pillow solo per questo.
LARGHEZZA_LOGO = 52 * mm
ALTEZZA_LOGO = LARGHEZZA_LOGO * 291 / 380

NOME_FILE = "Informativa_Cruscotto_Degenze.pdf"


def _stili() -> dict[str, ParagraphStyle]:
    corpo = ParagraphStyle(
        "corpo", fontName=NORMALE, fontSize=9.5, leading=14,
        textColor=INCHIOSTRO, alignment=TA_JUSTIFY, spaceAfter=6,
    )
    return {
        "corpo": corpo,
        "titolo": ParagraphStyle(
            "titolo", fontName=GRASSETTO, fontSize=17, leading=22,
            textColor=AZZURRO, alignment=1, spaceBefore=10, spaceAfter=2,
        ),
        "sottotitolo": ParagraphStyle(
            "sottotitolo", fontName=NORMALE, fontSize=9.5, leading=13,
            textColor=TENUE, alignment=1, spaceAfter=18,
        ),
        "sezione": ParagraphStyle(
            "sezione", fontName=GRASSETTO, fontSize=11, leading=15,
            textColor=AZZURRO, spaceBefore=12, spaceAfter=6,
        ),
        "elenco": ParagraphStyle(
            "elenco", parent=corpo, leftIndent=12, bulletIndent=2, spaceAfter=3,
        ),
        "cella": ParagraphStyle(
            "cella", fontName=NORMALE, fontSize=8.5, leading=11, textColor=TENUE,
        ),
        "avvertenza": ParagraphStyle(
            "avvertenza", parent=corpo, fontSize=8, leading=11, textColor=TENUE,
            spaceBefore=10,
        ),
    }


def _elenco(voci: list[str], stili) -> list:
    return [Paragraph(voce, stili["elenco"], bulletText="•") for voce in voci]


def _sezione(titolo: str, contenuto: list, stili) -> list:
    # Il titolo non deve restare da solo in fondo a una pagina.
    return [KeepTogether([Paragraph(titolo, stili["sezione"]), contenuto[0]]), *contenuto[1:]]


def _testata(nome_struttura: str, stili) -> list:
    logo = Image(str(LOGO), width=LARGHEZZA_LOGO, height=ALTEZZA_LOGO)
    logo.hAlign = "CENTER"
    return [
        logo,
        Paragraph("Informativa sul programma Cruscotto Degenze", stili["titolo"]),
        Paragraph(
            f"{nome_struttura} — scheda descrittiva, trattamento dei dati e "
            "misure di sicurezza",
            stili["sottotitolo"],
        ),
    ]


def _contenuto(config, stili) -> list:
    p = lambda testo: Paragraph(testo, stili["corpo"])  # noqa: E731
    struttura = config["NOME_STRUTTURA"]
    tentativi = config["TENTATIVI_MASSIMI"]
    blocco = config["MINUTI_BLOCCO"]
    inattivita = config["MINUTI_INATTIVITA"]

    storia = []

    storia += _sezione("1. Che cos'è il programma", [
        p(
            "Il Cruscotto Degenze è uno strumento informatico <b>ad uso interno, di "
            f"natura amministrativa e organizzativa</b>, in uso presso la {struttura}. "
            "Serve al personale per avere sotto controllo i posti letto occupati nei "
            "reparti, le date di arrivo e di dimissione presunta, la checklist delle "
            "attività da completare prima della dimissione e le note operative di "
            "passaggio fra un turno e l'altro."
        ),
        p("Il programma, in particolare:"),
        *_elenco([
            "<b>non è la cartella clinica</b> e non sostituisce alcun documento "
            "sanitario ufficiale;",
            "non formula diagnosi, non propone terapie e non calcola parametri "
            "clinici;",
            "non prende decisioni in modo automatico: ogni informazione viene "
            "inserita, letta e valutata da una persona.",
        ], stili),
        p(
            "Per queste ragioni non ha una destinazione d'uso medica e <b>non è un "
            "dispositivo medico</b> ai sensi del Regolamento (UE) 2017/745: è un "
            "software di gestione e organizzazione del lavoro."
        ),
    ], stili)

    storia += _sezione("2. Come è stato realizzato: utilizzo dell'intelligenza artificiale", [
        p(
            "Il codice del programma è stato scritto <b>con l'ausilio di strumenti di "
            "intelligenza artificiale generativa</b> (assistenti alla programmazione), "
            "sotto la guida, il controllo e la responsabilità di una persona, che ha "
            "definito i requisiti, esaminato il codice prodotto e ne ha verificato il "
            "funzionamento."
        ),
        *_elenco([
            "L'intelligenza artificiale è stata usata <b>solo durante lo "
            "sviluppo</b>, come strumento di scrittura del codice.",
            "Il programma in funzione <b>non contiene e non utilizza sistemi di "
            "intelligenza artificiale</b>: non invia dati a servizi di IA, non "
            "effettua profilazione e non adotta decisioni automatizzate ai sensi "
            "dell'art. 22 del Regolamento (UE) 2016/679.",
            "Il funzionamento è verificato da una serie di test automatici, "
            "rieseguiti a ogni modifica; ogni modifica al codice è registrata e "
            "rintracciabile nello storico delle versioni.",
        ], stili),
        p(
            "Il programma, quindi, non è un sistema di intelligenza artificiale ai "
            "sensi del Regolamento (UE) 2024/1689 (AI Act) e non ricade nelle "
            "disposizioni sull'impiego dell'intelligenza artificiale in ambito "
            "sanitario della Legge 23 settembre 2025, n. 132. Questa informativa è "
            "resa comunque, per trasparenza verso chi lo utilizza."
        ),
    ], stili)

    storia += _sezione("3. Dove funziona", [
        p(
            "Il programma è installato sui sistemi della struttura e funziona "
            "<b>esclusivamente sulla rete locale (LAN) interna</b>:"
        ),
        *_elenco([
            "non è raggiungibile da internet;",
            "non utilizza servizi cloud né servizi esterni di alcun tipo, e non "
            "carica risorse da siti di terzi;",
            "i dati restano nel database interno della struttura e non vengono "
            "trasferiti all'esterno, né tanto meno fuori dall'Unione europea.",
        ], stili),
    ], stili)

    storia += _sezione("4. Dati trattati", [
        p("<b>Dati dei pazienti ricoverati</b>: nome e cognome, reparto e posto "
          "letto, data di arrivo e data di dimissione presunta, livello di priorità "
          "organizzativa, stato della checklist di dimissione, note operative del "
          "personale."),
        p("<b>Dati del personale</b>: nome, cognome, nome utente, ruolo e registro "
          "delle operazioni svolte nel programma."),
        p(
            "Il programma non prevede campi per codice fiscale, diagnosi o terapie. "
            "Le note e il livello di priorità possono tuttavia contenere informazioni "
            "riferibili allo stato di salute (categorie particolari di dati, art. 9 "
            "del Regolamento (UE) 2016/679). Il loro trattamento avviene per finalità "
            "di cura e di gestione dei servizi sanitari (art. 9, par. 2, lett. h), "
            "da parte di personale autorizzato e soggetto al segreto professionale "
            "(art. 9, par. 3). Nelle note vanno riportate solo le informazioni "
            "strettamente necessarie all'organizzazione del lavoro."
        ),
        p(
            f"Titolare del trattamento è la {struttura}. I dati sono conservati nel "
            "database interno per il tempo necessario alla gestione del ricovero, "
            "secondo le regole di conservazione adottate dalla struttura."
        ),
    ], stili)

    storia += _sezione("5. Misure di sicurezza", [
        p(
            "In attuazione degli artt. 25 e 32 del Regolamento (UE) 2016/679 "
            "(protezione dei dati fin dalla progettazione e sicurezza del "
            "trattamento), il programma adotta le seguenti misure:"
        ),
        *_elenco([
            "accesso solo con credenziali personali, create e gestite "
            "dall'amministratore; non è possibile registrarsi da soli;",
            "password mai conservate in chiaro, ma protette con l'algoritmo "
            "scrypt; cambio obbligatorio della password al primo accesso;",
            f"blocco dell'accesso dopo {tentativi} tentativi falliti per "
            f"{blocco} minuti;",
            f"chiusura automatica della sessione dopo {inattivita} minuti di "
            "inattività, pensata per i PC condivisi di reparto;",
            "profili di autorizzazione per ruolo: ciascuno vede e modifica solo "
            "ciò che compete alla sua funzione;",
            "registro delle attività: accessi, tentativi falliti, uscite, "
            "inserimento, modifica ed eliminazione di pazienti e note, download "
            "delle schede, gestione degli utenti;",
            "protezioni contro gli attacchi più comuni alle applicazioni web "
            "(token anti-CSRF, Content-Security-Policy, cookie di sessione non "
            "leggibili dagli script);",
            "le schede paziente in PDF non vengono conservate nella memoria del "
            "browser.",
        ], stili),
    ], stili)

    storia += _sezione("6. Adempimenti a cura della struttura", [
        *_elenco([
            "riportare il trattamento nel registro delle attività di trattamento "
            "(art. 30 del Regolamento (UE) 2016/679);",
            "sottoporre il programma alla valutazione del Responsabile della "
            "protezione dei dati (DPO) della struttura;",
            "autorizzare e istruire il personale che vi accede (art. 29 del "
            "Regolamento e art. 2-quaterdecies del D.Lgs. 196/2003);",
            "eseguire copie di sicurezza periodiche del database.",
        ], stili),
    ], stili)

    storia += _sezione("7. Riferimenti normativi", [
        *_elenco([
            "Regolamento (UE) 2016/679 (GDPR), protezione dei dati personali;",
            "D.Lgs. 30 giugno 2003, n. 196 (Codice in materia di protezione dei "
            "dati personali), come modificato dal D.Lgs. 10 agosto 2018, n. 101;",
            "Regolamento (UE) 2024/1689 (AI Act), intelligenza artificiale;",
            "Legge 23 settembre 2025, n. 132, disposizioni in materia di "
            "intelligenza artificiale;",
            "Regolamento (UE) 2017/745 (MDR), dispositivi medici.",
        ], stili),
    ], stili)

    storia.append(Spacer(1, 6))
    storia.append(KeepTogether([
        Paragraph("8. Presa visione", stili["sezione"]),
        _tabella_firme(stili),
    ]))

    storia.append(Paragraph(
        f"Documento generato dal programma il {data_italiana(oggi_italia())}. "
        "Descrive le caratteristiche tecniche e organizzative del Cruscotto Degenze "
        "e non sostituisce le valutazioni del Responsabile della protezione dei "
        "dati della struttura.",
        stili["avvertenza"],
    ))
    return storia


def _tabella_firme(stili) -> Table:
    """Righe vuote da compilare a penna: ruolo, nome, data, firma."""
    ruoli = [
        "Sviluppatore del programma",
        "Amministratore del programma",
        "Direzione / Titolare del trattamento",
    ]
    intestazione = [
        Paragraph(testo, stili["cella"]) for testo in ("Ruolo", "Nome e cognome", "Data", "Firma")
    ]
    righe = [intestazione] + [[Paragraph(r, stili["cella"]), "", "", ""] for r in ruoli]

    tabella = Table(
        righe,
        colWidths=[LARGHEZZA_UTILE * q for q in (0.32, 0.28, 0.14, 0.26)],
        rowHeights=[None] + [26] * len(ruoli),
    )
    tabella.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), PAGINA),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDO),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabella


def genera_informativa(config) -> bytes:
    """Costruisce il PDF e restituisce i byte pronti da scaricare."""
    registra_font()
    stili = _stili()
    nome_struttura = config["NOME_STRUTTURA"]

    memoria = BytesIO()
    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        leftMargin=MARGINE,
        rightMargin=MARGINE,
        topMargin=14 * mm,
        bottomMargin=20 * mm,
        title="Informativa sul programma Cruscotto Degenze",
        author=nome_struttura,
        subject="Informativa, trattamento dei dati e misure di sicurezza",
    )

    storia = _testata(nome_struttura, stili) + _contenuto(config, stili)

    def crea_tela(*args, **kwargs):
        return TelaNumerata(*args, piede="Cruscotto Degenze — Informativa sul programma", **kwargs)

    documento.build(storia, canvasmaker=crea_tela)
    return memoria.getvalue()
