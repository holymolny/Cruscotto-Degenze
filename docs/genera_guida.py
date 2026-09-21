"""Genera il PDF «Guida tecnica del Cruscotto Degenze».

Uso, dalla cartella del progetto con l'ambiente virtuale attivo:

    python docs/genera_guida.py

Il diario (genera_diario.py) racconta come si è arrivati fin qui; questa guida
invece fotografa com'è fatto il programma oggi: architettura, database con lo
schema ER, sicurezza, come modificarlo, l'installer e la Fase 2 sulla
macchina virtuale. Quando il programma cambia in modo importante, si aggiorna
il testo qui sotto e si rilancia lo script.

Gli schemi (flusso delle richieste, schema ER, architettura della VM) sono
disegnati con reportlab.graphics: rettangoli, linee e scritte, senza immagini
esterne, così restano nitidi a qualunque ingrandimento.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RADICE))

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    CondPageBreak,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.formati import data_italiana, oggi_italia  # noqa: E402
from app.pdf.generatore import (  # noqa: E402
    GRASSETTO,
    NORMALE,
    TelaNumerata,
    registra_font,
)

# --------------------------------------------------------------------------
# Colori e misure
# --------------------------------------------------------------------------
AZZURRO = colors.HexColor("#00A3D4")
AZZURRO_TENUE = colors.HexColor("#E5F5FB")
BLU = colors.HexColor("#1E5FA6")
GIALLO = colors.HexColor("#FBE116")
GIALLO_TENUE = colors.HexColor("#FEF9D6")
INCHIOSTRO = colors.HexColor("#1B211F")
TENUE = colors.HexColor("#5C6763")
BORDO = colors.HexColor("#D5DAD7")
PAGINA = colors.HexColor("#F3F5F4")

MARGINE = 20 * mm
LARGHEZZA_UTILE = A4[0] - 2 * MARGINE

LOGO = RADICE / "app" / "static" / "img" / "logo-casa-cura.png"
USCITA = RADICE / "docs" / "Guida_Tecnica_Cruscotto_Degenze.pdf"
TITOLO = "Guida tecnica del Cruscotto Degenze"


# --------------------------------------------------------------------------
# Stili
# --------------------------------------------------------------------------
def crea_stili() -> dict[str, ParagraphStyle]:
    corpo = ParagraphStyle(
        "corpo", fontName=NORMALE, fontSize=9.5, leading=14.2,
        textColor=INCHIOSTRO, alignment=TA_JUSTIFY, spaceAfter=6,
    )
    return {
        "corpo": corpo,
        "copertina_titolo": ParagraphStyle(
            "ct", fontName=GRASSETTO, fontSize=26, leading=32,
            textColor=AZZURRO, alignment=TA_CENTER, spaceAfter=10,
        ),
        "copertina_sotto": ParagraphStyle(
            "cs", fontName=NORMALE, fontSize=12, leading=17,
            textColor=TENUE, alignment=TA_CENTER, spaceAfter=6,
        ),
        "capitolo": ParagraphStyle(
            "capitolo", fontName=GRASSETTO, fontSize=17, leading=22,
            textColor=AZZURRO, spaceBefore=4, spaceAfter=10,
        ),
        "paragrafo": ParagraphStyle(
            "paragrafo", fontName=GRASSETTO, fontSize=11.5, leading=15,
            textColor=BLU, spaceBefore=10, spaceAfter=5,
        ),
        "elenco": ParagraphStyle(
            "elenco", parent=corpo, leftIndent=13, bulletIndent=3, spaceAfter=3,
        ),
        "cella": ParagraphStyle(
            "cella", fontName=NORMALE, fontSize=8.5, leading=11.2, textColor=INCHIOSTRO,
        ),
        "cella_testa": ParagraphStyle(
            "cella_testa", fontName=GRASSETTO, fontSize=8.5, leading=11.2,
            textColor=colors.white,
        ),
        "codice": ParagraphStyle(
            "codice", fontName="Courier", fontSize=8, leading=10.6,
            textColor=INCHIOSTRO,
        ),
        "riquadro": ParagraphStyle(
            "riquadro", parent=corpo, fontSize=9, leading=13, spaceAfter=0,
        ),
        "didascalia": ParagraphStyle(
            "didascalia", fontName=NORMALE, fontSize=8, leading=11,
            textColor=TENUE, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10,
        ),
        "indice": ParagraphStyle(
            "indice", fontName=NORMALE, fontSize=10.5, leading=17, textColor=INCHIOSTRO,
        ),
    }


S = crea_stili()


# --------------------------------------------------------------------------
# Mattoncini di testo
# --------------------------------------------------------------------------
def capitolo(titolo: str) -> list:
    return [PageBreak(), Paragraph(titolo, S["capitolo"])]


def par(titolo: str) -> list:
    # CondPageBreak: se in fondo alla pagina restano meno di 3 cm, il titolo
    # passa alla pagina dopo invece di restare orfano.
    return [CondPageBreak(30 * mm), Paragraph(titolo, S["paragrafo"])]


def p(testo: str) -> Paragraph:
    return Paragraph(testo, S["corpo"])


def elenco(*voci: str) -> list:
    return [Paragraph(voce, S["elenco"], bulletText="•") for voce in voci]


def numerato(*voci: str, inizio: int = 1) -> list:
    return [
        Paragraph(voce, S["elenco"], bulletText=f"{i}.")
        for i, voce in enumerate(voci, start=inizio)
    ]


def codice(testo: str) -> Table:
    """Un blocco di comandi o di codice, su sfondo grigio.

    Il font è Courier, che ReportLab ha già dentro: copre le lettere
    accentate ma non simboli come le frecce, che qui quindi non vanno usati.
    """
    blocco = Preformatted(testo.strip("\n"), S["codice"])
    tabella = Table([[blocco]], colWidths=[LARGHEZZA_UTILE])
    tabella.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAGINA),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([tabella, Spacer(1, 7)])


def riquadro(titolo: str, testo: str, sfondo=AZZURRO_TENUE, bordo=AZZURRO) -> list:
    contenuto = Paragraph(f"<b>{titolo}</b><br/>{testo}", S["riquadro"])
    tabella = Table([[contenuto]], colWidths=[LARGHEZZA_UTILE])
    tabella.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), sfondo),
        ("LINEBEFORE", (0, 0), (0, -1), 3, bordo),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return [Spacer(1, 3), tabella, Spacer(1, 9)]


def attenzione(titolo: str, testo: str) -> list:
    return riquadro(titolo, testo, sfondo=GIALLO_TENUE, bordo=colors.HexColor("#D9B800"))


def tabella(intestazione: list[str], righe: list[list[str]], larghezze: list[float]) -> list:
    """Tabella con intestazione azzurra; larghezze in frazioni della pagina."""
    dati = [[Paragraph(t, S["cella_testa"]) for t in intestazione]]
    dati += [[Paragraph(str(c), S["cella"]) for c in riga] for riga in righe]
    t = Table(dati, colWidths=[LARGHEZZA_UTILE * f for f in larghezze], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZZURRO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAGINA]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [t, Spacer(1, 9)]


def didascalia(testo: str) -> Paragraph:
    return Paragraph(testo, S["didascalia"])


# --------------------------------------------------------------------------
# Disegni
# --------------------------------------------------------------------------
def _freccia(d: Drawing, x1, y1, x2, y2, colore=TENUE, spessore=1.1) -> None:
    d.add(Line(x1, y1, x2, y2, strokeColor=colore, strokeWidth=spessore))
    angolo = math.atan2(y2 - y1, x2 - x1)
    lato = 6
    punte = [
        x2, y2,
        x2 - lato * math.cos(angolo - 0.4), y2 - lato * math.sin(angolo - 0.4),
        x2 - lato * math.cos(angolo + 0.4), y2 - lato * math.sin(angolo + 0.4),
    ]
    d.add(Polygon(punte, fillColor=colore, strokeColor=colore, strokeWidth=0.5))


def _scatola(d: Drawing, x, y, larghezza, altezza, titolo, righe=(), colore=AZZURRO) -> None:
    """Rettangolo con titolo in grassetto e righe più piccole, centrati."""
    d.add(Rect(x, y, larghezza, altezza, rx=5, ry=5, fillColor=colors.white,
               strokeColor=colore, strokeWidth=1.2))
    centro = x + larghezza / 2
    totale = 12 + 10 * len(righe)
    alto = y + altezza / 2 + totale / 2 - 10
    d.add(String(centro, alto, titolo, fontName=GRASSETTO, fontSize=9,
                 fillColor=INCHIOSTRO, textAnchor="middle"))
    for i, riga in enumerate(righe):
        d.add(String(centro, alto - 12 - 10 * i, riga, fontName=NORMALE, fontSize=7.5,
                     fillColor=TENUE, textAnchor="middle"))


def disegno_flusso_fase1() -> Drawing:
    """Browser -> Waitress -> Flask -> database, e ritorno."""
    d = Drawing(LARGHEZZA_UTILE, 125)
    larghezza, altezza, y = 102, 58, 45
    passo = (LARGHEZZA_UTILE - larghezza) / 3
    scatole = [
        ("Browser", ["Edge o Chrome", "sul PC"]),
        ("Waitress", ["il server web", "127.0.0.1:8000"]),
        ("Flask (app/)", ["route, servizi,", "modelli, template"]),
        ("cruscotto.db", ["database SQLite", "(un file)"]),
    ]
    for i, (titolo, righe) in enumerate(scatole):
        _scatola(d, i * passo, y, larghezza, altezza, titolo, righe,
                 colore=BLU if i == 3 else AZZURRO)
    etichette = ["1. richiesta HTTP", "2. la passa a Flask", "3. legge / scrive"]
    for i, etichetta in enumerate(etichette):
        x1 = i * passo + larghezza + 3
        x2 = (i + 1) * passo - 3
        _freccia(d, x1, y + altezza - 16, x2, y + altezza - 16)
        d.add(String((x1 + x2) / 2, y + altezza + 6, etichetta, fontName=NORMALE,
                     fontSize=7, fillColor=TENUE, textAnchor="middle"))
    # Il ritorno: la pagina HTML costruita dal template torna al browser.
    x_flask = 2 * passo + larghezza / 2
    x_browser = larghezza / 2
    d.add(Line(x_flask, y, x_flask, 18, strokeColor=AZZURRO, strokeWidth=1.1))
    d.add(Line(x_flask, 18, x_browser, 18, strokeColor=AZZURRO, strokeWidth=1.1))
    _freccia(d, x_browser, 18, x_browser, y - 1, colore=AZZURRO)
    d.add(String((x_flask + x_browser) / 2, 6,
                 "4. risposta: la pagina HTML costruita dal template (o un PDF, o dati JSON)",
                 fontName=NORMALE, fontSize=7, fillColor=AZZURRO, textAnchor="middle"))
    return d


def _tabella_er(d: Drawing, x, alto, nome, colonne, larghezza=135) -> tuple[float, float]:
    """Disegna una tabella dello schema ER; restituisce (basso, alto)."""
    riga = 11
    altezza = 16 + riga * len(colonne) + 5
    basso = alto - altezza
    d.add(Rect(x, basso, larghezza, altezza, fillColor=colors.white,
               strokeColor=BLU, strokeWidth=1))
    d.add(Rect(x, alto - 16, larghezza, 16, fillColor=BLU, strokeColor=BLU, strokeWidth=1))
    d.add(String(x + 6, alto - 11.5, nome, fontName=GRASSETTO, fontSize=8.5,
                 fillColor=colors.white))
    for i, (colonna, etichetta) in enumerate(colonne):
        yy = alto - 16 - riga * (i + 1) + 2.5
        d.add(String(x + 6, yy, colonna, fontName=GRASSETTO if "PK" in etichetta else NORMALE,
                     fontSize=7.3, fillColor=INCHIOSTRO))
        if etichetta:
            d.add(String(x + larghezza - 5, yy, etichetta, fontName=GRASSETTO, fontSize=6.3,
                         fillColor=AZZURRO if "PK" in etichetta else TENUE,
                         textAnchor="end"))
    return basso, alto


def _relazione(d: Drawing, punti, uno, molti) -> None:
    """Linea di relazione «uno a molti»: '1' all'inizio, 'N' alla fine."""
    for (x1, y1), (x2, y2) in zip(punti, punti[1:]):
        d.add(Line(x1, y1, x2, y2, strokeColor=TENUE, strokeWidth=0.9))
    for (xx, yy), testo in ((uno, "1"), (molti, "N")):
        d.add(String(xx, yy, testo, fontName=GRASSETTO, fontSize=7.5, fillColor=AZZURRO))


def disegno_er() -> Drawing:
    d = Drawing(LARGHEZZA_UTILE, 535)
    a, b, c = 15, 184, 353  # le tre colonne

    _tabella_er(d, a, 530, "reparto", [
        ("id", "PK"), ("codice", "unico"), ("nome", ""), ("ordine", ""),
    ])
    _tabella_er(d, b, 530, "paziente", [
        ("id", "PK"), ("reparto_id", "FK"), ("nome", ""), ("cognome", ""),
        ("posto_letto", ""), ("gravita", ""), ("data_arrivo", ""),
        ("data_dimissione_presunta", ""), ("stato", ""),
        ("creato_da", "FK"), ("eliminato_da", "FK"),
    ])
    _tabella_er(d, c, 530, "voce_checklist", [
        ("codice", "PK"), ("testo", ""), ("ordine", ""), ("attiva", ""),
    ])
    _tabella_er(d, c, 415, "checklist_spunta", [
        ("paziente_id", "PK FK"), ("voce_codice", "PK FK"),
    ])
    _tabella_er(d, a, 430, "utente", [
        ("id", "PK"), ("username", "unico"), ("nome", ""), ("cognome", ""),
        ("ruolo", ""), ("password_hash", ""), ("attivo", ""),
        ("deve_cambiare_password", ""), ("tentativi_falliti", ""),
        ("bloccato_fino", ""), ("ultimo_accesso", ""), ("creato_da", "FK"),
    ])
    _tabella_er(d, b, 350, "nota", [
        ("id", "PK"), ("paziente_id", "FK"), ("autore_id", "FK"),
        ("autore_nome", ""), ("autore_ruolo", ""), ("testo", ""),
        ("data_nota", ""), ("creata_il", ""), ("modificata_il", ""),
        ("eliminata", ""), ("eliminata_da", "FK"),
    ])
    _tabella_er(d, a, 245, "evento_audit", [
        ("id", "PK"), ("quando", ""), ("utente_id", "FK"),
        ("username_tentato", ""), ("azione", ""), ("entita", ""),
        ("entita_id", ""), ("dettagli", ""), ("indirizzo_ip", ""),
    ])
    _tabella_er(d, b, 170, "nota_versione", [
        ("id", "PK"), ("nota_id", "FK"), ("testo_precedente", ""),
        ("sostituito_il", ""), ("sostituito_da", "FK"),
    ])

    # reparto 1 -- N paziente
    _relazione(d, [(150, 497), (184, 497)], (153, 500), (176, 500))
    # utente 1 -- N paziente (creato_da, eliminato_da)
    _relazione(d, [(150, 410), (184, 410)], (153, 413), (176, 413))
    # utente 1 -- N nota (autore_id, eliminata_da)
    _relazione(d, [(150, 305), (184, 305)], (153, 308), (176, 308))
    # utente 1 -- N nota_versione (sostituito_da)
    _relazione(d, [(150, 285), (184, 135)], (153, 276), (176, 139))
    # utente 1 -- N evento_audit
    _relazione(d, [(82, 276), (82, 245)], (86, 267), (86, 248))
    # paziente 1 -- N nota
    _relazione(d, [(251, 387), (251, 350)], (255, 378), (255, 353))
    # nota 1 -- N nota_versione
    _relazione(d, [(251, 207), (251, 170)], (255, 198), (255, 173))
    # paziente 1 -- N checklist_spunta
    _relazione(d, [(319, 395), (353, 395)], (322, 398), (345, 398))
    # voce_checklist 1 -- N checklist_spunta
    _relazione(d, [(420, 464), (420, 415)], (424, 455), (424, 418))
    # utente.creato_da -> utente: chi ha creato l'account
    d.add(Line(15, 400, 5, 400, strokeColor=TENUE, strokeWidth=0.9))
    d.add(Line(5, 400, 5, 380, strokeColor=TENUE, strokeWidth=0.9))
    d.add(Line(5, 380, 15, 380, strokeColor=TENUE, strokeWidth=0.9))

    # Legenda
    legenda = [
        ("PK", "chiave primaria: identifica la riga"),
        ("FK", "chiave esterna: punta a un'altra tabella"),
        ("1 — N", "una riga di qua, molte di là"),
    ]
    for i, (sigla, testo) in enumerate(legenda):
        yy = 70 - 13 * i
        d.add(String(c, yy, sigla, fontName=GRASSETTO, fontSize=7.5, fillColor=AZZURRO))
        d.add(String(c + 30, yy, testo, fontName=NORMALE, fontSize=7.3, fillColor=TENUE))
    return d


def disegno_fase2() -> Drawing:
    """PC di reparto -> IIS -> Waitress -> SQL Server, con il DNS."""
    d = Drawing(LARGHEZZA_UTILE, 205)
    larghezza, altezza, y = 96, 58, 40
    passo = (LARGHEZZA_UTILE - larghezza) / 3
    xs = [i * passo for i in range(4)]

    # La VM: un riquadro tratteggiato attorno a IIS e Waitress.
    d.add(Rect(xs[1] - 8, 14, xs[2] + larghezza - xs[1] + 16, altezza + 40,
               rx=6, ry=6, fillColor=AZZURRO_TENUE, strokeColor=AZZURRO,
               strokeWidth=0.8, strokeDashArray=[3, 2]))
    d.add(String(xs[1] - 1, 21, "VM degenze-misnav (Windows Server)",
                 fontName=GRASSETTO, fontSize=7.5, fillColor=AZZURRO))

    _scatola(d, xs[0], y, larghezza, altezza, "PC di reparto", ["browser, nel dominio", "cdcmisnav.local"])
    _scatola(d, xs[1], y, larghezza, altezza, "IIS", ["HTTPS, porta 443", "certificato CA interna"])
    _scatola(d, xs[2], y, larghezza, altezza, "Waitress + Flask", ["servizio Windows", "127.0.0.1:8000"])
    _scatola(d, xs[3], y, larghezza, altezza, "SQL Server", ["sql-misnav", "DB CruscottoDegenze"], colore=BLU)

    for i, etichetta in enumerate(["443", "proxy", "1433"]):
        x1 = xs[i] + larghezza + 3
        x2 = xs[i + 1] - 3
        _freccia(d, x1, y + altezza / 2, x2, y + altezza / 2)
        d.add(String((x1 + x2) / 2, y + altezza / 2 + 5, etichetta, fontName=NORMALE,
                     fontSize=6.5, fillColor=TENUE, textAnchor="middle"))

    # Il DNS, sopra il PC.
    _scatola(d, xs[0], 158, larghezza, 42, "DNS dc-misnav1", ["192.168.5.210"], colore=TENUE)
    _freccia(d, 36, y + altezza + 2, 36, 156)
    _freccia(d, 60, 156, 60, y + altezza + 2, colore=AZZURRO)
    d.add(String(68, 136, "«qual è l'IP di degenze.cdcmisnav.local?»", fontName=NORMALE,
                 fontSize=6.8, fillColor=TENUE))
    d.add(String(68, 125, "risposta: l'IP della VM", fontName=NORMALE,
                 fontSize=6.8, fillColor=AZZURRO))
    return d


# --------------------------------------------------------------------------
# Il contenuto
# --------------------------------------------------------------------------
def copertina() -> list:
    logo = Image(str(LOGO), width=70 * mm, height=70 * mm * 291 / 380)
    return [
        Spacer(1, 40 * mm),
        logo,
        Spacer(1, 16 * mm),
        Paragraph(TITOLO, S["copertina_titolo"]),
        Paragraph(
            "Com'è fatto, come funziona, come si modifica<br/>"
            "e come si porta sulla macchina virtuale",
            S["copertina_sotto"],
        ),
        Spacer(1, 18 * mm),
        Paragraph(
            f"Casa di Cura Misericordia Navacchio<br/>Aggiornata al {data_italiana(oggi_italia())}",
            S["copertina_sotto"],
        ),
    ]


INDICE = [
    "1. Il programma in breve",
    "2. Come funziona: browser, server e 127.0.0.1",
    "3. Le tecnologie usate",
    "4. Le cartelle del progetto",
    "5. Il database",
    "6. Accesso, ruoli e sicurezza",
    "7. Mettere mano al programma",
    "8. L'installer e la prova sul PC dell'infermiere",
    "9. Fase 2: la macchina virtuale",
    "10. Comandi utili",
    "11. Glossario",
]


def indice() -> list:
    return [PageBreak(), Paragraph("Indice", S["capitolo"])] + [
        Paragraph(voce, S["indice"]) for voce in INDICE
    ] + [Spacer(1, 12)] + riquadro(
        "Come leggere questa guida",
        "I capitoli 1–4 spiegano l'idea generale e bastano per capire che cosa succede "
        "quando qualcuno apre il Cruscotto. I capitoli 5–7 servono quando si vuole "
        "modificare qualcosa. I capitoli 8 e 9 riguardano l'installazione: oggi sul PC "
        "di reparto, domani sulla macchina virtuale. Le parole tecniche meno comuni sono "
        "spiegate nel glossario in fondo.",
    )


def cap1() -> list:
    return capitolo("1. Il programma in breve") + [
        p(
            "Il <b>Cruscotto Degenze</b> è un'applicazione web interna della Casa di Cura "
            "Misericordia Navacchio. Serve a vedere in un colpo d'occhio i pazienti "
            "ricoverati nei tre reparti (AOUP, Setting 1 — Low Care 1, Setting 2 — Low "
            "Care 2), a organizzare le dimissioni e a lasciare note fra un turno e l'altro."
        ),
        p("Cosa si può fare:"),
        *elenco(
            "vedere per ogni reparto i pazienti ricoverati, con letto, date e un pallino "
            "colorato di gravità (non valutato, stabile, instabile, critico);",
            "inserire, spostare di letto o reparto e dimettere un paziente;",
            "scrivere, modificare ed eliminare note nell'<b>Agenda</b> del paziente; ogni "
            "modifica conserva il testo precedente;",
            "spuntare le 21 voci della <b>checklist di dimissione</b>;",
            "scaricare la <b>scheda del paziente in PDF</b>, con dati, checklist e note;",
            "gestire gli utenti (solo l'amministratore): crearli, cambiarne il ruolo, "
            "reimpostare la password, disattivarli, sbloccarli.",
        ),
        *riquadro(
            "Cosa il Cruscotto non è",
            "Non è una cartella clinica: i dati clinici restano in ResMedica. Qui si "
            "registra solo il minimo necessario a organizzare degenza e dimissione.",
        ),
        *par("Le due fasi del progetto"),
        *tabella(
            ["", "Fase 1 — oggi", "Fase 2 — domani"],
            [
                ["Dove gira", "Sul singolo PC, installato con il setup", "Su una macchina virtuale nel datacenter"],
                ["Chi lo usa", "Solo chi siede a quel PC", "Tutti i PC di reparto del dominio"],
                ["Indirizzo", "http://127.0.0.1:8000", "https://degenze.cdcmisnav.local"],
                ["Database", "SQLite: il file cruscotto.db", "SQL Server su sql-misnav"],
                ["Server", "Waitress in una finestra nera", "Waitress come servizio Windows, dietro IIS"],
                ["Cifratura", "Non serve: il traffico non esce dal PC", "HTTPS con il certificato della CA interna"],
            ],
            [0.18, 0.41, 0.41],
        ),
        p(
            "Il codice è <b>lo stesso</b> nelle due fasi. Cambiano solo il file di "
            "configurazione <font face='Courier'>.env</font> e ciò che sta intorno al "
            "programma (IIS, servizio, database)."
        ),
    ]


def cap2() -> list:
    return capitolo("2. Come funziona: browser, server e 127.0.0.1") + [
        p(
            "Un'applicazione web è divisa in due. Il <b>browser</b> (Edge, Chrome) mostra "
            "le pagine e raccoglie i clic. Il <b>server</b> è un programma sempre in "
            "ascolto che riceve le richieste del browser, legge o scrive i dati e "
            "risponde con una pagina. Nel Cruscotto il server è la famosa «finestra "
            "nera»: finché resta aperta il programma funziona, chiudendola si spegne."
        ),
        disegno_flusso_fase1(),
        didascalia("Figura 1 — Il percorso di una richiesta nella Fase 1, tutto dentro lo stesso PC."),
        *par("Che cos'è 127.0.0.1"),
        p(
            "Ogni computer in rete ha un indirizzo IP, per esempio 192.168.0.45. Oltre a "
            "quello, ogni computer ha un indirizzo speciale che significa sempre "
            "«<b>me stesso</b>»: <b>127.0.0.1</b>, chiamato anche <i>localhost</i> o "
            "indirizzo di <i>loopback</i>. Il traffico verso 127.0.0.1 non esce mai dalla "
            "scheda di rete: va e torna dentro lo stesso computer."
        ),
        p(
            "Il server del Cruscotto si mette in ascolto proprio su 127.0.0.1. "
            "Conseguenza pratica: <b>solo il PC su cui è installato può aprirlo</b>. Un "
            "altro PC che scrivesse 127.0.0.1 nel browser parlerebbe con se stesso, dove "
            "il Cruscotto non c'è. È una protezione voluta, ed è il motivo per cui la "
            "Fase 1 non ha bisogno di HTTPS: i dati non viaggiano sulla rete."
        ),
        *par("Le porte: :8000 e :5000"),
        p(
            "Su un computer possono girare molti server insieme. Per distinguerli, "
            "ognuno ascolta su una <b>porta</b> diversa, un numero da 1 a 65535. "
            "L'indirizzo completo è IP più porta:"
        ),
        *tabella(
            ["Indirizzo", "Chi risponde", "Quando si usa"],
            [
                ["http://127.0.0.1:8000", "Waitress, il server «vero»", "Programma installato con il setup"],
                ["http://127.0.0.1:5000", "Il server di sviluppo di Flask (flask run)", "Mentre si modifica il codice"],
                ["https://degenze.cdcmisnav.local", "IIS sulla VM (porta 443, sottintesa)", "Fase 2"],
            ],
            [0.34, 0.36, 0.30],
        ),
        p(
            "Usare due porte diverse permette di tenere acceso il programma installato "
            "e, contemporaneamente, la copia su cui si sta lavorando, senza che si "
            "disturbino."
        ),
        *attenzione(
            "E se volessi aprirlo da un altro PC?",
            "Bisognerebbe far ascoltare il server su 0.0.0.0 (cioè su tutte le schede di "
            "rete) e aprire la porta nel firewall di Windows. Il traffico però viaggerebbe "
            "in chiaro, password comprese: si fa solo con dati finti. La strada giusta per "
            "l'uso condiviso è la Fase 2 (capitolo 9).",
        ),
        *par("Cosa succede quando si clicca «Accedi»"),
        *numerato(
            "Il browser invia al server nome utente e password (una richiesta <i>POST</i> "
            "all'indirizzo <font face='Courier'>/accedi</font>).",
            "Flask cerca la funzione associata a quell'indirizzo, la <b>route</b> "
            "<font face='Courier'>login()</font> in <font face='Courier'>app/auth/routes.py</font>.",
            "La route chiama i <b>servizi</b> (<font face='Courier'>app/auth/servizi.py</font>), "
            "che contengono la logica: l'utente esiste? è attivo? è bloccato? la password è giusta?",
            "I servizi usano i <b>modelli</b> (<font face='Courier'>app/models.py</font>) per "
            "leggere la tabella <font face='Courier'>utente</font> e aggiornare il contatore "
            "dei tentativi falliti.",
            "Se va tutto bene, Flask crea la <b>sessione</b>: un cookie firmato con la "
            "SECRET_KEY, che il browser rimanderà a ogni richiesta successiva per dire «sono sempre io».",
            "Il browser viene rimandato alla home; la route della home legge i pazienti e "
            "li passa al <b>template</b> <font face='Courier'>pazienti/home.html</font>, che "
            "costruisce la pagina HTML.",
        ),
        p(
            "Tutto il programma segue questo schema: <b>route → servizi → modelli → "
            "template</b>. Quando si cerca dove intervenire, basta chiedersi a quale dei "
            "quattro livelli appartiene la modifica."
        ),
    ]


def cap3() -> list:
    return capitolo("3. Le tecnologie usate") + [
        p("Tutte gratuite e open source, tutte installate dal setup o da "
          "<font face='Courier'>pip install -r requirements.txt</font>."),
        *tabella(
            ["Componente", "A cosa serve"],
            [
                ["<b>Python 3.12</b>", "Il linguaggio in cui è scritto il programma."],
                ["<b>Flask</b>", "Il «telaio» dell'applicazione web: collega gli indirizzi (route) alle funzioni Python."],
                ["<b>Jinja2</b>", "Il motore dei template: pagine HTML con dei «buchi» che Flask riempie con i dati."],
                ["<b>SQLAlchemy</b> + Flask-SQLAlchemy", "L'<i>ORM</i>: permette di usare il database con classi Python invece di scrivere SQL a mano. Lo stesso codice funziona con SQLite e con SQL Server."],
                ["<b>Alembic</b> + Flask-Migrate", "Le <i>migrazioni</i>: modifiche al database scritte come file, applicate in ordine."],
                ["<b>Flask-Login</b>", "Gestisce chi è collegato e protegge le pagine riservate."],
                ["<b>Flask-WTF</b>", "I form, con il token anti-CSRF."],
                ["<b>ReportLab</b>", "Genera i PDF (scheda paziente, informativa, questa guida)."],
                ["<b>Waitress</b>", "Il server web di produzione che fa girare Flask."],
                ["<b>python-dotenv</b>", "Legge le impostazioni dal file .env."],
                ["<b>pytest</b>", "Esegue i test automatici (circa 200)."],
                ["<b>Inno Setup</b>", "Costruisce il setup .exe (solo sul PC di sviluppo)."],
            ],
            [0.30, 0.70],
        ),
        *riquadro(
            "Niente internet",
            "Il programma non carica nulla da internet: niente font di Google, niente "
            "librerie da CDN. CSS e JavaScript sono scritti a mano in "
            "<font face='Courier'>app/static</font>. Così funziona anche con la rete "
            "esterna staccata. Lo garantisce anche la Content-Security-Policy "
            "(capitolo 6): se qualcuno aggiungesse per sbaglio un link esterno, il "
            "browser lo bloccherebbe subito.",
        ),
    ]


def cap4() -> list:
    return capitolo("4. Le cartelle del progetto") + [
        codice(r"""
Cruscotto-Degenze\
  app\                     IL PROGRAMMA
    __init__.py            create_app(): costruisce l'applicazione
    config.py              impostazioni Sviluppo / Test / Produzione
    models.py              le tabelle del database, come classi Python
    dati_fissi.py          reparti e voci della checklist
    permessi.py            chi puo' fare cosa (matrice dei ruoli)
    audit.py               registro delle attivita'
    sessione.py            scadenza per inattivita', cambio password obbligato
    comandi.py             comandi da terminale: crea-admin, dati-demo, ...
    formati.py             date in italiano, fuso orario
    auth\                  accesso, uscita, cambio password, profilo
    pazienti\              home, nuovo paziente, gravita', sposta, dimetti
    agenda\                note e checklist
    pdf\                   scheda paziente e informativa in PDF
    utenti\                gestione utenti (solo amministratore)
    templates\             le pagine HTML (Jinja2)
    static\                css\stile.css, js\app.js, immagini, font
  migrations\versions\     le migrazioni del database, una per file
  tests\                   i test automatici
  docs\                    diario di sviluppo e questa guida
  Installer\               costruzione del setup .exe
  PromptIA\                specifica iniziale e prototipo grafico
  wsgi.py                  punto di ingresso per Waitress
  requirements.txt         librerie Python, con versione bloccata
  .env                     impostazioni locali e segreti (NON va su Git)
  cruscotto.db             il database SQLite (NON va su Git)
"""),
        p(
            "Ogni area funzionale (auth, pazienti, agenda, pdf, utenti) è un "
            "<b>blueprint</b> di Flask, cioè un pezzo di programma con le sue route. "
            "Dentro ciascuna si ritrovano gli stessi file:"
        ),
        *tabella(
            ["File", "Contiene"],
            [
                ["routes.py", "Le funzioni collegate agli indirizzi: ricevono la richiesta, controllano i permessi, chiamano i servizi, scelgono il template."],
                ["servizi.py", "La logica vera: regole, controlli, letture e scritture sul database. Non sanno nulla di HTML."],
                ["form.py", "I campi dei moduli e i loro controlli (obbligatorio, lunghezza massima, ...)."],
                ["__init__.py", "Crea il blueprint."],
            ],
            [0.2, 0.8],
        ),
        *riquadro(
            "Perché separare route e servizi",
            "I servizi si possono provare con i test senza passare dal browser, e la stessa "
            "regola (per esempio «un letto non può essere occupato da due pazienti») sta "
            "in un posto solo, anche se la usano più pagine.",
        ),
    ]


def cap5() -> list:
    return capitolo("5. Il database") + [
        *par("5.1 SQLite ora, SQL Server dopo"),
        p(
            "Nella Fase 1 il database è <b>SQLite</b>: un unico file, "
            "<font face='Courier'>cruscotto.db</font>, nella cartella del programma. Non "
            "c'è un server di database da installare: la libreria che lo legge è già "
            "dentro Python. Nella Fase 2 lo stesso schema verrà creato su <b>SQL "
            "Server</b>."
        ),
        p(
            "Il codice non scrive quasi mai SQL a mano: usa <b>SQLAlchemy</b>, che "
            "traduce le operazioni sulle classi di <font face='Courier'>models.py</font> "
            "nel dialetto SQL giusto per il database in uso. Per passare da SQLite a SQL "
            "Server basta cambiare la riga <font face='Courier'>DATABASE_URL</font> nel "
            "file <font face='Courier'>.env</font>."
        ),
        *par("5.2 Lo schema ER"),
        p(
            "Lo schema <b>entità-relazioni</b> (ER) mostra le tabelle, le colonne più "
            "importanti e i collegamenti. Una linea «1 — N» vuol dire che a una riga "
            "della prima tabella corrispondono molte righe della seconda: un reparto ha "
            "molti pazienti, un paziente ha molte note, e così via."
        ),
        KeepTogether([disegno_er(), didascalia(
            "Figura 2 — Schema ER. Le tabelle sono otto. Il piccolo anello a sinistra di "
            "«utente» indica che creato_da punta a un altro utente: chi ha creato l'account."
        )]),
        p(
            "<font face='Courier'>checklist_spunta</font> è una <b>tabella ponte</b>: "
            "realizza la relazione «molti a molti» fra pazienti e voci della checklist "
            "(un paziente ha molte voci spuntate, una voce è spuntata per molti "
            "pazienti). La sua chiave primaria è la coppia paziente + voce."
        ),
        *par("5.3 Le tabelle una per una"),
        *tabella(
            ["Tabella", "Cosa contiene", "Da sapere"],
            [
                ["reparto", "I tre reparti.", "Dati fissi, inseriti dalla migrazione iniziale (app/dati_fissi.py)."],
                ["utente", "Gli account del personale.", "La password non c'è: c'è solo il suo hash. Ruoli: ADMIN, MEDICO, INFERMIERE, OSS, AMMIN."],
                ["paziente", "I pazienti, ricoverati e dimessi.", "stato = RICOVERATO o ELIMINATO. gravita = nv, verde, giallo, rosso."],
                ["nota", "Le note dell'Agenda.", "Nome e ruolo dell'autore sono copiati al momento della scrittura: la firma resta giusta anche se poi l'utente cambia ruolo."],
                ["nota_versione", "Il testo precedente di ogni nota modificata.", "Una riga per ogni modifica: la storia completa si ricostruisce sempre."],
                ["voce_checklist", "Le 21 voci della checklist.", "Chiave = codice (es. PRIVACY). attiva = false nasconde una voce senza perderne lo storico."],
                ["checklist_spunta", "Quali voci sono spuntate per quale paziente.", "La riga esiste = voce spuntata. È l'unica tabella in cui si cancella davvero."],
                ["evento_audit", "Il registro delle attività.", "Chi, quando, cosa, da quale IP. Si scrive e basta: non si modifica mai."],
            ],
            [0.18, 0.32, 0.50],
        ),
        *par("5.4 Le regole importanti"),
        *elenco(
            "<b>Non si cancella quasi nulla.</b> Un paziente dimesso non sparisce: passa a "
            "stato ELIMINATO, con data e autore. Una nota eliminata resta con "
            "<font face='Courier'>eliminata = true</font>. Così si può sempre ricostruire "
            "cosa è successo. (Nella Fase 2 lo garantirà anche SQL Server, negando "
            "all'utente del programma il permesso DELETE.)",
            "<b>Un letto, un paziente.</b> L'indice <font face='Courier'>ux_paziente_letto_occupato</font> "
            "impedisce due pazienti RICOVERATI nello stesso letto dello stesso reparto. È un "
            "indice <i>parziale</i>: i pazienti dimessi non contano, altrimenti un letto "
            "usato una volta resterebbe bloccato per sempre.",
            "<b>La dimissione non precede l'arrivo.</b> Un vincolo CHECK nel database lo "
            "impedisce anche se l'applicazione avesse un bug.",
            "<b>Orari in UTC.</b> Date e ore di sistema (creata_il, quando, ...) sono salvate "
            "in tempo universale e convertite in ora italiana solo per la visualizzazione "
            "(<font face='Courier'>app/formati.py</font>). Così il cambio dell'ora legale non "
            "crea buchi o doppioni.",
            "<b>Registro delle attività.</b> Ogni operazione importante scrive una riga in "
            "evento_audit: accessi riusciti e falliti, uscite, pazienti creati, spostati, "
            "dimessi, note, PDF scaricati, gestione utenti. La pagina per consultarlo è "
            "ancora da fare (passo 8b).",
        ),
        *par("5.5 Guardare dentro il database"),
        p(
            "Per curiosare nel file <font face='Courier'>cruscotto.db</font> il modo più "
            "comodo è <b>DB Browser for SQLite</b> (gratuito, sqlitebrowser.org). Apri il "
            "file, scheda <i>Sfoglia dati</i>, scegli la tabella."
        ),
        *attenzione(
            "Regole di prudenza",
            "Apri il database in <b>sola lettura</b> (c'è l'opzione nel menu Apri). Non "
            "modificare i dati a mano mentre il programma è acceso. Per fare una copia di "
            "sicurezza, spegni il programma (chiudi la finestra nera) e copia il file "
            "cruscotto.db altrove: è tutto lì dentro.",
        ),
        *par("5.6 Le migrazioni"),
        p(
            "Una <b>migrazione</b> è un file Python che descrive una modifica al database: "
            "crea una tabella, aggiunge una colonna, inserisce una voce. Stanno in "
            "<font face='Courier'>migrations/versions/</font>, ciascuna sa qual è la "
            "precedente e il database ricorda (nella tabella "
            "<font face='Courier'>alembic_version</font>) a che punto è arrivato. Il "
            "comando <font face='Courier'>flask db upgrade</font> applica in ordine quelle "
            "che mancano: per questo un aggiornamento non perde i dati."
        ),
        *tabella(
            ["Migrazione", "Cosa fa"],
            [
                ["042c1d4c264a", "Struttura iniziale: le otto tabelle, i reparti e le voci della checklist."],
                ["b7e2a91c4d10", "Aggiunge la voce «Modulo Privacy Somministrato» ai database già esistenti."],
            ],
            [0.22, 0.78],
        ),
        codice(r"""
# dopo aver modificato app/models.py:
flask db migrate -m "descrizione breve"   # scrive la migrazione
# RILEGGI il file creato in migrations\versions\ prima di andare avanti
flask db upgrade                          # la applica al tuo database
flask db downgrade                        # torna indietro di una
"""),
        *attenzione(
            "La regola d'oro",
            "Una migrazione già applicata su un altro PC (o sulla VM) <b>non si modifica "
            "mai</b>: se c'è da correggere qualcosa, se ne scrive una nuova. Il PC "
            "dell'infermiere non rieseguirebbe la migrazione cambiata, e i due database "
            "prenderebbero strade diverse.",
        ),
    ]


def cap6() -> list:
    si, no = "✔", "—"
    return capitolo("6. Accesso, ruoli e sicurezza") + [
        *par("6.1 Ruoli e permessi"),
        p(
            "La matrice sta in un solo file, <font face='Courier'>app/permessi.py</font>. "
            "Ogni route protetta ha il decoratore <font face='Courier'>@richiede_permesso</font>, "
            "che risponde «403 — non consentito» a chi non ha diritto. Nascondere un "
            "pulsante nella pagina serve solo a non confondere: il controllo vero è sempre "
            "sul server."
        ),
        *tabella(
            ["Permesso", "Ammin.", "Medico", "Infermiere", "OSS", "Ammin./IT"],
            [
                ["Vedere pazienti, Agenda, checklist", si, si, si, si, si],
                ["Scrivere note, spuntare la checklist", si, si, si, no, no],
                ["Cambiare la gravità", si, si, si, no, no],
                ["Inserire, spostare, dimettere pazienti", si, si, si, no, no],
                ["Modificare la dimissione presunta", si, si, si, no, no],
                ["Scaricare la scheda PDF", si, si, si, no, si],
                ["Gestire gli utenti", si, no, no, no, no],
            ],
            [0.35, 0.12, 0.12, 0.15, 0.10, 0.16],
        ),
        *par("6.2 Le protezioni"),
        *tabella(
            ["Misura", "Come funziona", "Dove"],
            [
                ["Password protette", "Salvate come hash scrypt: non si possono rileggere, solo verificare.", "models.py"],
                ["Cambio al primo accesso", "Chi riceve una password dall'amministratore deve sceglierne una propria.", "sessione.py"],
                ["Blocco dopo 5 tentativi", "Dopo 5 password sbagliate l'account resta bloccato 15 minuti. L'amministratore può sbloccarlo prima.", "auth/servizi.py, config.py"],
                ["Scadenza per inattività", "Dopo 15 minuti senza attività la sessione si chiude: i PC di reparto sono condivisi.", "sessione.py, config.py"],
                ["Token CSRF", "Ogni modulo contiene un codice segreto: un sito esterno non può inviare moduli al posto dell'utente.", "Flask-WTF"],
                ["Content-Security-Policy", "Il browser esegue solo script e stili serviti dal Cruscotto stesso.", "app/__init__.py"],
                ["Cookie protetti", "Il cookie di sessione non è leggibile dagli script; in produzione viaggia solo su HTTPS.", "config.py"],
                ["Registro attività", "Tutto ciò che conta finisce in evento_audit.", "audit.py"],
            ],
            [0.26, 0.52, 0.22],
        ),
        *par("6.3 Il file .env"),
        p(
            "Contiene le impostazioni che cambiano da un'installazione all'altra e i "
            "segreti. Non va mai su Git (lo esclude <font face='Courier'>.gitignore</font>) e "
            "non va mandato per email."
        ),
        codice(r"""
SECRET_KEY=...lunga stringa casuale...   # firma i cookie di sessione
FLASK_CONFIG=sviluppo                    # sviluppo | test | produzione
DATABASE_URL=                            # vuoto = cruscotto.db (SQLite)
MINUTI_INATTIVITA=15
FLASK_APP=wsgi.py
"""),
        p(
            "Se si cambia la SECRET_KEY, tutti gli utenti collegati devono rifare "
            "l'accesso. Il setup ne genera una casuale e non la riscrive negli "
            "aggiornamenti."
        ),
    ]


def cap7() -> list:
    return capitolo("7. Mettere mano al programma") + [
        *par("7.1 Preparare il PC di sviluppo"),
        p("Servono Python 3.12, Git e Visual Studio Code. Poi, una volta sola, dalla "
          "cartella del progetto:"),
        codice(r"""
py -3.12 -m venv .venv                   # crea l'ambiente virtuale
.\.venv\Scripts\Activate.ps1             # lo attiva (a ogni nuovo terminale)
pip install -r requirements.txt          # installa le librerie
copy .env.example .env                   # poi metti una SECRET_KEY nel .env
flask db upgrade                         # crea cruscotto.db
flask crea-admin                         # il tuo amministratore
flask dati-demo                          # facoltativo: pazienti e utenti finti
"""),
        *riquadro(
            "Cos'è l'ambiente virtuale (.venv)",
            "Una cartella con una copia privata di Python e delle librerie del progetto, "
            "nelle versioni esatte di requirements.txt. Così aggiornare una libreria per "
            "un altro programma non rompe il Cruscotto. Non va su Git: si ricrea con i "
            "comandi qui sopra.",
        ),
        *par("7.2 Il ciclo di lavoro"),
        *numerato(
            "Avvia il server di sviluppo: <font face='Courier'>flask run --debug</font> e apri "
            "<font face='Courier'>http://127.0.0.1:5000</font>. Con --debug il server si "
            "riavvia da solo a ogni modifica: basta ricaricare la pagina (Ctrl+F5 se è "
            "cambiato CSS o JavaScript).",
            "Fai la modifica.",
            "Lancia i test: <font face='Courier'>pytest</font>. Devono passare tutti. Se ne "
            "fallisce uno, leggi il messaggio: spesso è il test a dirti cosa hai rotto.",
            "Salva il lavoro su Git: <font face='Courier'>git add .</font> e "
            "<font face='Courier'>git commit -m \"cosa ho fatto\"</font>.",
            "Se la modifica deve arrivare al PC dell'infermiere, ricompila il setup "
            "(capitolo 8) e reinstallalo sulla stessa cartella.",
        ),
        *par("7.3 Dove si tocca per..."),
        *tabella(
            ["Voglio...", "File da toccare"],
            [
                ["Cambiare un testo in una pagina", "app/templates/... (cerca la frase con Ctrl+Shift+F in VS Code)"],
                ["Cambiare colori, spaziature, caratteri", "app/static/css/stile.css (i colori principali sono variabili in cima al file)"],
                ["Cambiare un comportamento nella pagina (finestre, clic)", "app/static/js/app.js"],
                ["Aggiungere o togliere una voce della checklist", "app/dati_fissi.py + una nuova migrazione (vedi 7.4)"],
                ["Aggiungere un reparto", "app/dati_fissi.py + una nuova migrazione, come per la checklist"],
                ["Cambiare chi può fare cosa", "app/permessi.py (e i test in tests/)"],
                ["Aggiungere un campo al paziente", "models.py, poi flask db migrate; il form in pazienti/form.py; la pagina in templates/pazienti; il PDF in pdf/generatore.py"],
                ["Cambiare i minuti di blocco o di inattività", "config.py o, meglio, il file .env"],
                ["Cambiare il PDF del paziente", "app/pdf/generatore.py"],
                ["Cambiare l'informativa legale", "app/pdf/informativa.py"],
                ["Cambiare l'installer", "Installer/CruscottoDegenze.iss e Installer/script/"],
            ],
            [0.40, 0.60],
        ),
        *par("7.4 Esempio completo: una voce nuova nella checklist"),
        p("Così è stata aggiunta «Modulo Privacy Somministrato»:"),
        *numerato(
            "In <font face='Courier'>app/dati_fissi.py</font> si aggiunge in fondo a "
            "VOCI_CHECKLIST la riga <font face='Courier'>(\"PRIVACY\", \"Modulo Privacy "
            "Somministrato\")</font>. Il codice (PRIVACY) è la chiave: massimo 20 caratteri, "
            "maiuscolo, senza spazi.",
            "Si scrive una migrazione che inserisce la voce nei database già esistenti "
            "(<font face='Courier'>migrations/versions/b7e2a91c4d10_...py</font>). Inserisce "
            "solo se la voce manca, perché sui database nuovi la mette già la migrazione "
            "iniziale.",
            "<font face='Courier'>flask db upgrade</font> sul proprio database e "
            "<font face='Courier'>flask controlla-dati-fissi</font> per verificare: "
            "«Voci della checklist: 21 (attese 21)».",
            "<font face='Courier'>pytest</font>: i test che contavano le voci ora le leggono "
            "dall'elenco invece di avere il numero scritto a mano.",
            "Commit, ricompilazione del setup, reinstallazione: il setup esegue "
            "<font face='Courier'>flask db upgrade</font> da solo, e la voce compare senza "
            "toccare pazienti e spunte.",
        ),
        *par("7.5 Lavorare con l'assistente IA"),
        *elenco(
            "Chiedi una modifica alla volta, piccola e ben descritta.",
            "Fatti spiegare cosa ha cambiato e in quali file; rileggi le differenze in VS Code "
            "(scheda Controllo del codice sorgente) prima del commit.",
            "Pretendi che i test passino, e che per ogni comportamento nuovo ci sia un test.",
            "Mai incollare nella chat password vere, il contenuto del .env o dati di pazienti reali.",
        ),
    ]


def cap8() -> list:
    return capitolo("8. L'installer e la prova sul PC dell'infermiere") + [
        *par("8.1 Costruire il setup"),
        p(
            "Il setup <font face='Courier'>CruscottoDegenze-Setup.exe</font> contiene una "
            "<b>copia</b> dei file del programma: dopo ogni modifica va ricompilato, "
            "altrimenti installa la versione vecchia. Dalla cartella del progetto:"
        ),
        codice(r"""
powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1
"""),
        p(
            "Il risultato è <font face='Courier'>Installer\\Output\\CruscottoDegenze-Setup.exe</font> "
            "(circa 4 MB). Serve Inno Setup 6: se manca, lo script lo installa con winget. Il "
            ".exe non va su Git (è in .gitignore): se si scarica il progetto da capo, va "
            "ricompilato."
        ),
        *par("8.2 Cosa fa il setup"),
        *tabella(
            ["#", "Passo"],
            [
                ["1", "Chiede la cartella e i dati del primo amministratore (nome, cognome, nome utente, password)."],
                ["2", "Copia i file in %LOCALAPPDATA%\\Programs\\CruscottoDegenze. Non in C:\\Programmi, dove il programma non potrebbe scrivere il proprio database senza permessi di amministratore."],
                ["3", "Installa Python 3.12, se non c'è."],
                ["4", "Crea l'ambiente virtuale .venv e scarica le librerie (<b>serve internet</b>)."],
                ["5", "Scrive il .env con una SECRET_KEY casuale."],
                ["6", "Crea o aggiorna il database con flask db upgrade."],
                ["7", "Crea l'amministratore e mette i collegamenti su Desktop e menu Start."],
            ],
            [0.06, 0.94],
        ),
        *par("8.3 La prova sul PC dell'infermiere, passo per passo"),
        *numerato(
            "Copia <font face='Courier'>CruscottoDegenze-Setup.exe</font> sulla chiavetta.",
            "Sul PC dell'infermiere, collegato a internet, fai doppio clic sul file. Se "
            "compare «Windows ha protetto il PC», clicca <i>Ulteriori informazioni</i> e poi "
            "<i>Esegui comunque</i>: succede a ogni programma senza firma digitale.",
            "Segui la procedura e inserisci i dati del primo amministratore (tu). "
            "L'installazione non chiede i permessi di amministratore di Windows.",
            "Alla fine si apre la finestra nera e poi il browser su "
            "<font face='Courier'>http://127.0.0.1:8000</font>. Entra con l'amministratore.",
            "Da <i>Gestione utenti</i> crea l'account dell'infermiere, con ruolo Infermiere e "
            "una password provvisoria. Al primo accesso gli verrà chiesto di cambiarla.",
            "Spiega che la <b>finestra nera è il programma</b>: va lasciata aperta (si può "
            "ridurre a icona). Chiudendola il Cruscotto si spegne.",
        ),
        *attenzione(
            "Da sapere per la prova",
            "I dati inseriti restano <b>solo su quel PC</b>, nel file cruscotto.db della "
            "cartella di installazione, e nessun altro PC li vede. Non c'è un backup "
            "automatico. Per la prova è meglio usare dati finti o ridotti al minimo; se si "
            "usano dati reali, il PC deve essere protetto dalla password di Windows e "
            "l'informativa (link sulla pagina di accesso) va condivisa con chi partecipa.",
        ),
        *par("8.4 Aggiornare, salvare, disinstallare"),
        *elenco(
            "<b>Aggiornare</b>: chiudi la finestra nera e rilancia il nuovo setup sulla stessa "
            "cartella. Database, utenti e .env restano; la pagina del primo amministratore "
            "viene saltata; il database viene portato all'ultima versione.",
            "<b>Copia di sicurezza</b>: a programma spento, copia "
            "<font face='Courier'>%LOCALAPPDATA%\\Programs\\CruscottoDegenze\\cruscotto.db</font> "
            "su una chiavetta o in una cartella sicura. Per ripristinarlo, rimetti il file al suo posto.",
            "<b>Disinstallare</b>: da Impostazioni di Windows → App, come ogni programma.",
        ),
        *par("8.5 Problemi frequenti"),
        *tabella(
            ["Sintomo", "Rimedio"],
            [
                ["Il setup si ferma sulle librerie", "Manca internet. Collega il PC e rilancia solo la configurazione: powershell -ExecutionPolicy Bypass -File installazione\\Configura.ps1 dalla cartella del programma."],
                ["«Il Cruscotto è acceso»", "Chiudi la finestra nera e riprova."],
                ["Il browser non si apre", "Il server è partito più lentamente: vai a mano su http://127.0.0.1:8000."],
                ["Utente bloccato", "Aspetta 15 minuti, oppure l'amministratore lo sblocca da Gestione utenti."],
                ["Password dell'amministratore dimenticata", "Dalla cartella del programma: .venv\\Scripts\\flask.exe crea-admin, per creare un secondo amministratore."],
            ],
            [0.32, 0.68],
        ),
    ]


def cap9() -> list:
    return capitolo("9. Fase 2: la macchina virtuale") + [
        p(
            "Nella Fase 2 il Cruscotto diventa un servizio di rete: un'unica installazione "
            "su una macchina virtuale del datacenter, raggiunta da tutti i PC di reparto "
            "all'indirizzo <b>https://degenze.cdcmisnav.local</b>, con i dati su SQL Server "
            "e i backup del datacenter."
        ),
        *par("9.1 L'architettura"),
        disegno_fase2(),
        didascalia("Figura 3 — Il percorso di una richiesta nella Fase 2."),
        *numerato(
            "Il PC chiede al DNS (dc-misnav1) l'indirizzo di degenze.cdcmisnav.local e riceve l'IP della VM.",
            "Il browser si collega in HTTPS sulla porta 443. Il traffico passa dai FortiGate, che devono permetterlo.",
            "Sulla VM risponde <b>IIS</b>, con il certificato della CA interna ca-misnav: i PC del dominio lo riconoscono, quindi niente avvisi.",
            "IIS fa da <b>reverse proxy</b>: non esegue il programma, ma inoltra la richiesta a Waitress, che ascolta "
            "solo su 127.0.0.1:8000 e quindi è irraggiungibile da fuori della VM.",
            "Waitress fa girare Flask, che legge e scrive su SQL Server (sql-misnav, porta 1433).",
        ),
        *riquadro(
            "Perché IIS davanti a Waitress",
            "Waitress è ottimo per le applicazioni Python ma non gestisce HTTPS. IIS sì, usa i "
            "certificati della CA interna ed è già conosciuto in struttura. Ognuno fa ciò che "
            "sa fare meglio: IIS cifra, Waitress esegue il programma.",
        ),
        *par("9.2 Cosa manca ancora nel codice"),
        p(
            "Il programma è stato scritto pensando alla Fase 2 (SQLAlchemy, configurazione "
            "«produzione», indici compatibili con SQL Server), ma alcune cose vanno ancora "
            "preparate <b>prima</b> dell'installazione. La documentazione iniziale le cita "
            "come se esistessero: ad oggi <b>non ci sono</b>."
        ),
        *tabella(
            ["Da fare", "Perché"],
            [
                ["Cartella deploy/ con installa.ps1, aggiorna.ps1, crea_database.sql, web.config e la guida DEPLOY.md", "Per installare e aggiornare la VM in modo ripetibile, senza affidarsi alla memoria."],
                ["Attivare ProxyFix in wsgi.py", "Dietro IIS ogni richiesta arriva da 127.0.0.1: senza ProxyFix il registro delle attività scriverebbe sempre quell'IP invece di quello del PC di reparto."],
                ["Scommentare pyodbc in requirements.txt e installare l'ODBC Driver 18 sulla VM", "È il «ponte» fra Python e SQL Server."],
                ["Log su file (cartella logs/)", "Un servizio non ha una finestra: gli errori devono finire in un file da consultare."],
                ["Pagina di consultazione del registro attività (passo 8b)", "Gli eventi sono già scritti, manca la pagina per leggerli."],
                ["Prova completa delle migrazioni su SQL Server", "Da fare nella prova generale (9.3): SQLite perdona cose che SQL Server non perdona."],
            ],
            [0.45, 0.55],
        ),
        p("Per esempio, ProxyFix sono due righe in <font face='Courier'>wsgi.py</font>:"),
        codice(r"""
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
"""),
        *par("9.3 Prima: la prova generale sul tuo PC"),
        p(
            "Prima di toccare il datacenter conviene ripetere tutta l'installazione su una "
            "VM di prova. Se la prova va liscia, l'installazione vera sarà una ripetizione."
        ),
        *elenco(
            "<b>Hyper-V</b>: su Windows 11 Pro si attiva da PowerShell come amministratore con "
            "<font face='Courier'>Enable-WindowsOptionalFeature -Online -FeatureName "
            "Microsoft-Hyper-V -All</font>, poi si riavvia.",
            "<b>Sistema</b>: Windows Server 2025 Evaluation, gratuito per 180 giorni.",
            "<b>Database</b>: SQL Server Express, gratuito, sulla stessa VM.",
            "<b>Risorse</b>: 2 vCPU, 4 GB di RAM, 60 GB di disco (sul PC servono almeno 16 GB di RAM).",
            "<b>Certificato</b>: autofirmato; il browser mostrerà un avviso, ed è normale.",
            "Prova anche un <b>backup e un ripristino</b> del database: un backup mai provato non è un backup.",
        ),
        *par("9.4 Cosa chiedere al consulente (Marco Bottalico)"),
        *elenco(
            "<b>VM degenze-misnav</b>: Windows Server 2025 Standard, 2 vCPU, 4 GB RAM, 80 GB di "
            "disco, nel dominio cdcmisnav.local, IP statico nella rete 192.168.5.0/24, agente SentinelOne.",
            "<b>SQL Server su sql-misnav</b>: conferma che può ospitare il database "
            "CruscottoDegenze, nome esatto dell'istanza, autenticazione mista attiva, "
            "database incluso nel piano di backup.",
            "<b>Regole FortiGate</b>: postazioni 192.168.0.0/24 verso la VM sulle porte 443 e "
            "80; VM verso sql-misnav sulla porta 1433.",
            "<b>Certificato</b>: modello «Server Web» pubblicato sulla CA ca-misnav, con "
            "permesso di richiesta per la VM.",
        ),
        *par("9.5 I passi di installazione"),
        *numerato(
            "<b>DNS</b>: su dc-misnav1, un record A «degenze» nella zona cdcmisnav.local che punta all'IP della VM.",
            "<b>Database e login su sql-misnav</b>: un database CruscottoDegenze e due login, "
            "uno per il programma (lettura e scrittura) e uno solo per le migrazioni (proprietario).",
            "<b>Prerequisiti sulla VM</b>: Python 3.12 per tutti gli utenti, ODBC Driver 18 for "
            "SQL Server, ruolo IIS, moduli URL Rewrite e Application Request Routing, NSSM.",
            "<b>Programma</b>: copia in C:\\Apps\\CruscottoDegenze, crea .venv, installa le "
            "librerie, scrivi il .env di produzione (9.6), lancia flask db upgrade con il login "
            "delle migrazioni.",
            "<b>Servizio Windows</b> con NSSM, perché Waitress parta da solo all'accensione:",
        ),
        codice(r"""
nssm install CruscottoDegenze C:\Apps\CruscottoDegenze\.venv\Scripts\waitress-serve.exe
nssm set CruscottoDegenze AppParameters "--listen=127.0.0.1:8000 wsgi:app"
nssm set CruscottoDegenze AppDirectory C:\Apps\CruscottoDegenze
nssm start CruscottoDegenze
"""),
        *numerato(
            "<b>Certificato</b>: da certlm.msc sulla VM, Personale → Richiedi nuovo "
            "certificato, modello «Server Web», con degenze.cdcmisnav.local nel campo SAN.",
            "<b>IIS</b>: sito sulla porta 443 con il certificato; in Application Request "
            "Routing → Server Proxy Settings abilita il proxy; una regola che inoltra tutto a "
            "http://127.0.0.1:8000 e una che porta la porta 80 su HTTPS.",
            "<b>Firewall di Windows</b>: in ingresso solo le porte 80 e 443.",
            "<b>Verifica</b>: da un PC di reparto apri https://degenze.cdcmisnav.local. Deve "
            "comparire il lucchetto senza avvisi; login, note, checklist e PDF devono "
            "funzionare. Riavvia la VM e controlla che il servizio riparta da solo.",
            "<b>Utenti reali</b>: flask crea-admin per il primo amministratore, poi dal "
            "programma gli account di medici e infermieri.",
            inizio=6,
        ),
        p("Uno scheletro del <font face='Courier'>web.config</font> di IIS (da provare nella prova generale):"),
        codice(r"""
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Da HTTP a HTTPS" stopProcessing="true">
          <match url="(.*)" />
          <conditions><add input="{HTTPS}" pattern="off" /></conditions>
          <action type="Redirect" url="https://{HTTP_HOST}/{R:1}" />
        </rule>
        <rule name="Cruscotto" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
"""),
        *par("9.6 Il .env di produzione"),
        codice(r"""
FLASK_APP=wsgi.py
FLASK_CONFIG=produzione
SECRET_KEY=<nuova stringa casuale, diversa da quella dei PC>
DATABASE_URL=mssql+pyodbc://degenze_app:<password>@sql-misnav.cdcmisnav.local/CruscottoDegenze?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes
MINUTI_INATTIVITA=15
"""),
        p(
            "Con <font face='Courier'>FLASK_CONFIG=produzione</font> il programma si rifiuta "
            "di partire senza SECRET_KEY, spegne la modalità debug e manda il cookie di "
            "sessione solo su HTTPS. DATABASE_URL va scritta su una sola riga."
        ),
        *attenzione(
            "Due punti da verificare con il consulente",
            "<b>Certificato di SQL Server</b>: se non è emesso dalla CA interna, la connessione "
            "con Encrypt=yes può fallire; temporaneamente si aggiunge "
            "TrustServerCertificate=yes, poi si sistema il certificato.<br/>"
            "<b>PC nel vecchio dominio misericordianavacchio.local</b>: potrebbero non "
            "risolvere cdcmisnav.local e non fidarsi della CA ca-misnav. Servono un inoltro "
            "condizionale DNS e il certificato della CA distribuito via GPO.",
        ),
        *par("9.7 Portare i dati dalla Fase 1 alla Fase 2"),
        p(
            "I dati della prova sui PC (SQLite) <b>non passano</b> da soli su SQL Server. La "
            "via consigliata è partire puliti sulla VM: la prova serve a raccogliere "
            "commenti, non a produrre dati da conservare. Se servisse davvero travasarli, "
            "si può scrivere uno script apposito, da provare prima sulla VM di prova."
        ),
        *par("9.8 Backup, aggiornamenti, controlli"),
        *elenco(
            "<b>Backup del database</b>: completo e giornaliero su sql-misnav, con conservazione "
            "da concordare (per esempio 30 giorni). È la cosa più importante: il programma si "
            "reinstalla in mezz'ora, i dati no.",
            "<b>VM</b>: snapshot prima di ogni aggiornamento. <b>.env</b>: copia in un luogo "
            "sicuro ad accesso limitato, perché contiene le password.",
            "<b>Aggiornare il programma</b>, fuori dall'orario di punta: backup del database → "
            "arresto del servizio → nuovo codice → pip install -r requirements.txt → flask db "
            "upgrade → riavvio del servizio → verifica. Se qualcosa va storto si ripristinano "
            "codice e database salvati.",
            "<b>Controlli periodici</b>: log degli errori; account di chi lascia la struttura "
            "disattivati subito; una volta al mese verifica degli account attivi; aggiornamenti "
            "di Windows e, passando prima dalla VM di prova, delle librerie Python.",
        ),
    ]


def cap10() -> list:
    return capitolo("10. Comandi utili") + [
        p("Da un terminale nella cartella del progetto, con l'ambiente virtuale attivo "
          "(<font face='Courier'>.\\.venv\\Scripts\\Activate.ps1</font>):"),
        codice(r"""
flask run --debug                 # server di sviluppo su http://127.0.0.1:5000
waitress-serve --listen=127.0.0.1:8000 wsgi:app   # come il programma installato

pytest                            # tutti i test
pytest -v                         # elencandoli uno per uno
pytest tests\test_pdf.py          # solo un file

flask db upgrade                  # porta il database all'ultima versione
flask db migrate -m "..."         # nuova migrazione dopo aver cambiato models.py
flask db downgrade                # annulla l'ultima migrazione
flask db current                  # a che migrazione e' il database

flask crea-admin                  # crea un amministratore
flask dati-demo                   # dati di prova (solo in sviluppo)
flask dati-demo --azzera          # come sopra, ripartendo da zero
flask controlla-dati-fissi        # reparti e voci della checklist ci sono tutti?

python docs\genera_guida.py       # rigenera questa guida
python docs\genera_diario.py      # rigenera il diario di sviluppo

powershell -ExecutionPolicy Bypass -File Installer\Compila.ps1   # ricompila il setup

git status                        # cosa e' cambiato
git add .                         # prepara tutto per il commit
git commit -m "messaggio"         # salva una versione
git log --oneline                 # la storia delle versioni
"""),
    ]


def cap11() -> list:
    voci = [
        ("127.0.0.1 / localhost", "L'indirizzo che per ogni computer significa «me stesso». Il traffico non esce dal PC."),
        ("Porta", "Numero che distingue i server in ascolto sullo stesso computer (8000, 5000, 443...)."),
        ("HTTP / HTTPS", "Il protocollo con cui browser e server si parlano. HTTPS è la versione cifrata, con certificato."),
        ("Route", "Associazione fra un indirizzo (/accedi) e la funzione Python che risponde."),
        ("Template", "Pagina HTML con dei segnaposto che Flask riempie con i dati (Jinja2)."),
        ("Blueprint", "Un pezzo del programma Flask con le sue route (auth, pazienti, agenda, pdf, utenti)."),
        ("ORM", "Libreria (SQLAlchemy) che fa usare il database come oggetti Python, senza scrivere SQL."),
        ("Migrazione", "File che descrive una modifica al database, applicato con flask db upgrade."),
        ("Chiave primaria / esterna", "La primaria identifica una riga; l'esterna punta a una riga di un'altra tabella."),
        ("Hash", "Trasformazione a senso unico: dalla password si ottiene l'hash, ma dall'hash non si torna alla password."),
        ("Sessione / cookie", "Il «tesserino» firmato che il browser mostra a ogni richiesta per dire chi è."),
        ("CSRF", "Attacco in cui un sito esterno invia moduli a nome dell'utente. Il token CSRF lo impedisce."),
        ("Ambiente virtuale", "Cartella .venv con Python e le librerie del progetto, separati dal resto del PC."),
        ("Reverse proxy", "Server (IIS) che riceve le richieste dall'esterno e le inoltra al programma vero (Waitress)."),
        ("Servizio Windows", "Programma che parte da solo all'accensione e gira senza finestra (con NSSM)."),
        ("DNS", "Il «servizio elenco» che traduce un nome (degenze.cdcmisnav.local) in un indirizzo IP."),
        ("Certificato / CA", "Documento digitale che prova l'identità del server; la CA interna (ca-misnav) lo firma."),
        ("Audit", "Registro delle attività: chi ha fatto cosa, quando, da dove."),
    ]
    return capitolo("11. Glossario") + tabella(
        ["Termine", "Significato"], [[f"<b>{t}</b>", s] for t, s in voci], [0.27, 0.73]
    )


# --------------------------------------------------------------------------
# Costruzione
# --------------------------------------------------------------------------
def genera() -> Path:
    registra_font()

    documento = SimpleDocTemplate(
        str(USCITA),
        pagesize=A4,
        leftMargin=MARGINE,
        rightMargin=MARGINE,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title=TITOLO,
        author="Casa di Cura Misericordia Navacchio",
        subject="Architettura, database, manutenzione e Fase 2 del Cruscotto Degenze",
    )

    storia = copertina() + indice()
    for parte in (cap1, cap2, cap3, cap4, cap5, cap6, cap7, cap8, cap9, cap10, cap11):
        storia += parte()

    def crea_tela(*args, **kwargs):
        return TelaNumerata(*args, piede=TITOLO, **kwargs)

    documento.build(storia, canvasmaker=crea_tela)
    return USCITA


if __name__ == "__main__":
    percorso = genera()
    print(f"Creato: {percorso}")
