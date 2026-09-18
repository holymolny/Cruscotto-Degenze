"""Genera il PDF del diario di sviluppo del Cruscotto Degenze.

Uso, dalla cartella del progetto con l'ambiente virtuale attivo:

    python docs/genera_diario.py

Il testo sta in contenuto_diario.py: questo file si occupa solo di
impaginarlo. È anche un'anteprima del passo 7, dove con la stessa libreria
(ReportLab) genereremo il foglio paziente da stampare.

Come ragiona ReportLab, in breve: si prepara una lista di "flowable", cioè
pezzi di contenuto che sanno disegnarsi da soli (un paragrafo, una tabella,
uno spazio). La lista si chiama per tradizione "storia". Poi si consegna la
storia al documento, che la impagina scorrendo dall'alto e andando a capo
pagina da solo quando lo spazio finisce.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# contenuto_diario.py sta accanto a questo file. Aggiungendo la sua cartella
# ai percorsi di ricerca, lo script funziona sia lanciato da docs/ sia dalla
# radice del progetto con "python docs/genera_diario.py".
sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfgen import canvas as tela_reportlab  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from contenuto_diario import CONTENUTO, SOTTOTITOLO, VERSIONE  # noqa: E402

# --------------------------------------------------------------------------
# Colori e misure. Sono gli stessi del prototipo: il diario e il programma
# devono sembrare due parti della stessa cosa.
# --------------------------------------------------------------------------
ACCENTO = colors.HexColor("#0E5A55")
ACCENTO_TENUE = colors.HexColor("#E3EFEE")
INCHIOSTRO = colors.HexColor("#1B211F")
TENUE = colors.HexColor("#5C6763")
BORDO = colors.HexColor("#D5DAD7")
PAGINA = colors.HexColor("#EEF0EE")

MARGINE = 22 * mm
LARGHEZZA_UTILE = A4[0] - 2 * MARGINE

TITOLO_DOCUMENTO = "Cruscotto Degenze — Diario di sviluppo"
NOME_FILE = "Diario_Cruscotto_Degenze.pdf"

MESI = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]


# --------------------------------------------------------------------------
# Stili di testo
# --------------------------------------------------------------------------
def crea_stili() -> dict[str, ParagraphStyle]:
    """Definisce una volta sola l'aspetto di ogni tipo di testo."""
    corpo = ParagraphStyle(
        "corpo",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.5,
        textColor=INCHIOSTRO,
        alignment=TA_JUSTIFY,
        spaceAfter=7,
    )
    return {
        "corpo": corpo,
        "cella": ParagraphStyle("cella", parent=corpo, fontSize=8.5, leading=12,
                                alignment=0, spaceAfter=0),
        "cella_forte": ParagraphStyle("cella_forte", parent=corpo, fontSize=8.5,
                                      leading=12, alignment=0, spaceAfter=0,
                                      fontName="Helvetica-Bold"),
        "cella_testa": ParagraphStyle("cella_testa", parent=corpo, fontSize=8.5,
                                      leading=12, alignment=0, spaceAfter=0,
                                      fontName="Helvetica-Bold",
                                      textColor=colors.white),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16,
                             leading=20, textColor=ACCENTO,
                             spaceBefore=20, spaceAfter=9),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12,
                             leading=16, textColor=INCHIOSTRO,
                             spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5,
                             leading=14, textColor=ACCENTO,
                             spaceBefore=11, spaceAfter=4),
        "codice": ParagraphStyle("codice", fontName="Courier", fontSize=8.5,
                                 leading=12, textColor=INCHIOSTRO),
        "albero": ParagraphStyle("albero", fontName="Courier", fontSize=7.4,
                                 leading=10, textColor=INCHIOSTRO),
        "riquadro_titolo": ParagraphStyle("riquadro_titolo",
                                          fontName="Helvetica-Bold", fontSize=9,
                                          leading=13, textColor=ACCENTO,
                                          spaceAfter=3),
        "riquadro_testo": ParagraphStyle("riquadro_testo", parent=corpo,
                                         fontSize=9, leading=13,
                                         alignment=0, spaceAfter=0),
        "cop_ente": ParagraphStyle("cop_ente", fontName="Helvetica", fontSize=9.5,
                                   leading=14, textColor=TENUE, spaceAfter=10),
        "cop_titolo": ParagraphStyle("cop_titolo", fontName="Helvetica-Bold",
                                     fontSize=31, leading=36, textColor=ACCENTO,
                                     spaceAfter=4),
        "cop_sotto": ParagraphStyle("cop_sotto", fontName="Helvetica", fontSize=15,
                                    leading=20, textColor=INCHIOSTRO,
                                    spaceAfter=30),
    }


# --------------------------------------------------------------------------
# Numerazione delle pagine
# --------------------------------------------------------------------------
class TelaNumerata(tela_reportlab.Canvas):
    """Tela che sa quante pagine ci sono in totale.

    Il problema: ReportLab disegna una pagina alla volta e, mentre la sta
    disegnando, non sa quante ne verranno dopo. Non può quindi scrivere
    «Pagina 3 di 8», perché l'8 non esiste ancora.

    Il trucco: invece di stampare ogni pagina appena finita, la mettiamo da
    parte. Alla fine, quando il totale è noto, le ripassiamo tutte e solo
    allora ci scriviamo sopra il piè di pagina. È la stessa tecnica che
    useremo al passo 7 per il foglio paziente.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pagine_da_stampare = []

    def showPage(self):  # noqa: N802 - nome imposto da ReportLab
        self._pagine_da_stampare.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        totale = len(self._pagine_da_stampare)
        for stato_pagina in self._pagine_da_stampare:
            self.__dict__.update(stato_pagina)
            # La copertina resta pulita, senza piè di pagina.
            if self._pageNumber > 1:
                self._disegna_piede(totale)
            super().showPage()
        super().save()

    def _disegna_piede(self, totale: int) -> None:
        self.setStrokeColor(BORDO)
        self.setLineWidth(0.5)
        self.line(MARGINE, 15 * mm, A4[0] - MARGINE, 15 * mm)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(TENUE)
        self.drawString(MARGINE, 10.5 * mm, TITOLO_DOCUMENTO)
        self.drawRightString(
            A4[0] - MARGINE, 10.5 * mm, f"Pagina {self._pageNumber} di {totale}"
        )


# --------------------------------------------------------------------------
# Mattoncini riutilizzabili
# --------------------------------------------------------------------------
def scatola(contenuto_interno, sfondo, colore_bordo=None, imbottitura=9):
    """Mette un contenuto dentro un rettangolo colorato.

    ReportLab non ha un flowable «riquadro»: si usa una tabella di una sola
    cella, che sa colorarsi lo sfondo e disegnarsi il bordo.
    """
    tabella = Table([[contenuto_interno]], colWidths=[LARGHEZZA_UTILE])
    stile = [
        ("BACKGROUND", (0, 0), (-1, -1), sfondo),
        ("LEFTPADDING", (0, 0), (-1, -1), imbottitura),
        ("RIGHTPADDING", (0, 0), (-1, -1), imbottitura),
        ("TOPPADDING", (0, 0), (-1, -1), imbottitura),
        ("BOTTOMPADDING", (0, 0), (-1, -1), imbottitura),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    if colore_bordo is not None:
        stile.append(("BOX", (0, 0), (-1, -1), 0.6, colore_bordo))
    tabella.setStyle(TableStyle(stile))
    return tabella


def costruisci_tabella(dati: dict, stili: dict):
    """Costruisce una tabella a partire dalla descrizione nel contenuto."""
    mostra_testa = dati.get("intestazione_visibile", True)
    larghezze = dati["larghezze"]

    righe = []
    if mostra_testa:
        righe.append([Paragraph(t, stili["cella_testa"]) for t in dati["intestazioni"]])

    for riga in dati["righe"]:
        # La prima colonna fa da etichetta: in grassetto si legge meglio.
        celle = [Paragraph(riga[0], stili["cella_forte"])]
        celle += [Paragraph(valore, stili["cella"]) for valore in riga[1:]]
        righe.append(celle)

    tabella = Table(righe, colWidths=larghezze, repeatRows=1 if mostra_testa else 0)

    stile = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, BORDO),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDO),
    ]
    if mostra_testa:
        stile.append(("BACKGROUND", (0, 0), (-1, 0), ACCENTO))
    else:
        stile.append(("BACKGROUND", (0, 0), (0, -1), PAGINA))

    tabella.setStyle(TableStyle(stile))
    return tabella


def costruisci_storia(contenuto, stili) -> list:
    """Traduce la lista (tipo, dato) del contenuto in flowable di ReportLab."""
    storia = []

    for tipo, dato in contenuto:
        if tipo == "titolo1":
            storia.append(Paragraph(dato, stili["h1"]))
        elif tipo == "titolo2":
            storia.append(Paragraph(dato, stili["h2"]))
        elif tipo == "titolo3":
            storia.append(Paragraph(dato, stili["h3"]))
        elif tipo == "paragrafo":
            storia.append(Paragraph(dato, stili["corpo"]))
        elif tipo == "elenco":
            storia.append(
                ListFlowable(
                    [ListItem(Paragraph(voce, stili["corpo"]), leftIndent=14)
                     for voce in dato],
                    bulletType="bullet",
                    bulletColor=ACCENTO,
                    bulletFontSize=7,
                    leftIndent=12,
                )
            )
            storia.append(Spacer(1, 4))
        elif tipo == "codice":
            storia.append(scatola(Preformatted(dato, stili["codice"]), PAGINA))
            storia.append(Spacer(1, 9))
        elif tipo == "albero":
            storia.append(scatola(Preformatted(dato, stili["albero"]), PAGINA))
            storia.append(Spacer(1, 9))
        elif tipo == "riquadro":
            titolo, testo = dato
            interno = [Paragraph(titolo, stili["riquadro_titolo"])]
            for capoverso in testo.split("\n"):
                interno.append(Paragraph(capoverso, stili["riquadro_testo"]))
            # KeepTogether evita che il riquadro si spezzi a metà fra due pagine.
            storia.append(KeepTogether(scatola(interno, ACCENTO_TENUE, ACCENTO)))
            storia.append(Spacer(1, 11))
        elif tipo == "tabella":
            storia.append(costruisci_tabella(dato, stili))
            storia.append(Spacer(1, 11))
        elif tipo == "pagina_nuova":
            storia.append(PageBreak())
        else:
            raise ValueError(f"Tipo di contenuto sconosciuto: {tipo!r}")

    return storia


def conta_passi_completati() -> int:
    """Legge l'avanzamento dalla tabella «Stato di avanzamento» del contenuto.

    Così la copertina non va aggiornata a mano: basta cambiare «da fare» in
    «FATTO» in quella tabella e il conteggio si aggiorna da solo.
    """
    for tipo, dato in CONTENUTO:
        if tipo == "tabella" and dato["intestazioni"][0] == "Passo":
            return sum(1 for riga in dato["righe"] if riga[-1] == "FATTO")
    return 0


def costruisci_copertina(stili, oggi: date) -> list:
    """La prima pagina: titolo grande e scheda riassuntiva."""
    passi_fatti = conta_passi_completati()

    avanzamento = (
        "nessun passo completato"
        if passi_fatti == 0
        else "1 passo completato su 9"
        if passi_fatti == 1
        else f"{passi_fatti} passi completati su 9"
    )

    scheda = [
        ["Documento", "Resoconto dello sviluppo, passo per passo"],
        ["Versione", VERSIONE],
        ["Aggiornato al", f"{oggi.day} {MESI[oggi.month - 1]} {oggi.year}"],
        ["Avanzamento", avanzamento],
        ["Progetto", "Casa di Cura Misericordia Navacchio S.r.l."],
        ["Specifica", "Prompt_Cruscotto_Degenze.pdf, versione 1.0"],
    ]

    return [
        Spacer(1, 62 * mm),
        Paragraph("Casa di Cura Misericordia Navacchio S.r.l. — IT", stili["cop_ente"]),
        Paragraph("Cruscotto Degenze", stili["cop_titolo"]),
        Paragraph(SOTTOTITOLO, stili["cop_sotto"]),
        costruisci_tabella(
            {
                "intestazioni": ["", ""],
                "righe": scheda,
                "larghezze": [110, 360],
                "intestazione_visibile": False,
            },
            stili,
        ),
        PageBreak(),
    ]


def genera(percorso_uscita: Path | None = None) -> Path:
    """Costruisce il PDF e restituisce il percorso del file scritto."""
    percorso_uscita = percorso_uscita or Path(__file__).resolve().parent / NOME_FILE
    oggi = date.today()
    stili = crea_stili()

    documento = SimpleDocTemplate(
        str(percorso_uscita),
        pagesize=A4,
        leftMargin=MARGINE,
        rightMargin=MARGINE,
        topMargin=22 * mm,
        bottomMargin=24 * mm,
        title=TITOLO_DOCUMENTO,
        author="Micky — IT, Casa di Cura Misericordia Navacchio",
        subject="Diario di sviluppo del Cruscotto Degenze",
    )

    storia = costruisci_copertina(stili, oggi) + costruisci_storia(CONTENUTO, stili)
    documento.build(storia, canvasmaker=TelaNumerata)

    return percorso_uscita


if __name__ == "__main__":
    file_scritto = genera()
    print(f"Diario aggiornato: {file_scritto}")
    print(f"Passi completati: {conta_passi_completati()} su 9")
