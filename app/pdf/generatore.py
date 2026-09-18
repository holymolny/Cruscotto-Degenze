"""Costruzione del PDF «Scheda paziente e Agenda».

È il foglio che si stampa prima di dimettere qualcuno. Viene generato dal
server con ReportLab: nessuna libreria nel browser, quindi funziona uguale su
Edge, su Chrome e senza connessione.

La tecnica è la stessa del diario di sviluppo (docs/genera_diario.py): si
prepara una lista di «flowable», pezzi di contenuto che sanno disegnarsi da
soli, e la si consegna al documento, che li impagina scorrendo dall'alto.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as tela_reportlab
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.agenda import servizi as servizi_agenda
from app.formati import a_ora_italiana, data_italiana, oggi_italia
from app.models import GRAVITA

# --------------------------------------------------------------------------
# Colori e misure: gli stessi del programma, così il foglio stampato e lo
# schermo sembrano due facce della stessa cosa.
# --------------------------------------------------------------------------
ACCENTO = colors.HexColor("#0E5A55")
INCHIOSTRO = colors.HexColor("#1B211F")
TENUE = colors.HexColor("#5C6763")
BORDO = colors.HexColor("#D5DAD7")
PAGINA = colors.HexColor("#EEF0EE")

COLORI_GRAVITA = {
    "rosso": colors.HexColor("#B3261E"),
    "giallo": colors.HexColor("#C98A12"),
    "verde": colors.HexColor("#2F7D4F"),
    "nv": colors.HexColor("#8B9591"),
}

COLORI_RUOLO = {
    "MEDICO": colors.HexColor("#0E5A55"),
    "INFERMIERE": colors.HexColor("#6B4FA0"),
    "ADMIN": colors.HexColor("#8B9591"),
}

MARGINE = 18 * mm
LARGHEZZA_UTILE = A4[0] - 2 * MARGINE

CARTELLA_FONT = Path(__file__).resolve().parent.parent / "static" / "font"

NORMALE = "DejaVu"
GRASSETTO = "DejaVu-Bold"
CORSIVO = "DejaVu-Oblique"


def registra_font() -> None:
    """Rende disponibili a ReportLab i font DejaVu inclusi nel progetto.

    Perché non usare Helvetica, che ReportLab ha già dentro? Perché Helvetica
    copre solo l'alfabeto occidentale di base: sulle lettere accentate se la
    cava, ma su un carattere fuori elenco stampa un quadratino nero. Con
    DejaVu incluso nel progetto il risultato è identico sul PC di sviluppo e
    sulla macchina virtuale, dove i font installati sono altri.

    La registrazione avviene una volta sola per processo: ReportLab tiene un
    elenco globale, e ripetere la registrazione a ogni PDF sarebbe uno spreco.
    """
    if NORMALE in pdfmetrics.getRegisteredFontNames():
        return

    pdfmetrics.registerFont(TTFont(NORMALE, CARTELLA_FONT / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(GRASSETTO, CARTELLA_FONT / "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont(CORSIVO, CARTELLA_FONT / "DejaVuSans-Oblique.ttf"))

    # Insegna a ReportLab quale font usare per <b> e <i> dentro un paragrafo:
    # senza questa riga il grassetto verrebbe ignorato in silenzio.
    pdfmetrics.registerFontFamily(
        NORMALE, normal=NORMALE, bold=GRASSETTO, italic=CORSIVO, boldItalic=GRASSETTO
    )


# --------------------------------------------------------------------------
# Stili
# --------------------------------------------------------------------------
def crea_stili() -> dict[str, ParagraphStyle]:
    corpo = ParagraphStyle(
        "corpo", fontName=NORMALE, fontSize=9, leading=13, textColor=INCHIOSTRO
    )
    return {
        "corpo": corpo,
        "titolo": ParagraphStyle(
            "titolo", fontName=GRASSETTO, fontSize=16, leading=20,
            textColor=ACCENTO, spaceAfter=2,
        ),
        "struttura": ParagraphStyle(
            "struttura", fontName=NORMALE, fontSize=9, leading=12,
            textColor=TENUE, spaceAfter=14,
        ),
        "sezione": ParagraphStyle(
            "sezione", fontName=GRASSETTO, fontSize=11, leading=15,
            textColor=ACCENTO, spaceBefore=14, spaceAfter=7,
        ),
        "etichetta": ParagraphStyle(
            "etichetta", parent=corpo, fontSize=8.5, textColor=TENUE,
        ),
        "valore": ParagraphStyle("valore", parent=corpo, fontSize=9),
        "valore_forte": ParagraphStyle(
            "valore_forte", parent=corpo, fontSize=9, fontName=GRASSETTO
        ),
        "generato": ParagraphStyle(
            "generato", parent=corpo, fontSize=8, textColor=TENUE, spaceBefore=8
        ),
        "voce": ParagraphStyle("voce", parent=corpo, fontSize=8.5, leading=11),
        "giorno": ParagraphStyle(
            "giorno", fontName=GRASSETTO, fontSize=8.5, leading=12,
            textColor=TENUE, spaceBefore=10, spaceAfter=4,
        ),
        "firma": ParagraphStyle(
            "firma", fontName=GRASSETTO, fontSize=8.5, leading=12
        ),
        "testo_nota": ParagraphStyle(
            "testo_nota", parent=corpo, fontSize=9, leading=12.5,
            alignment=TA_JUSTIFY, spaceBefore=2,
        ),
        "vuoto": ParagraphStyle(
            "vuoto", parent=corpo, fontSize=9, textColor=TENUE, fontName=CORSIVO
        ),
    }


# --------------------------------------------------------------------------
# Mattoncini
# --------------------------------------------------------------------------
class Casella(Flowable):
    """Una casella della checklist, spuntata o vuota.

    È disegnata a mano invece di usare i caratteri ☑ e ☐ perché quei simboli
    non esistono in tutti i font: se un domani si cambiasse font, al posto
    delle caselle comparirebbero dei quadratini vuoti e nessuno capirebbe
    perché. Un rettangolo e due segmenti funzionano sempre.
    """

    def __init__(self, spuntata: bool, lato: float = 8):
        super().__init__()
        self.spuntata = spuntata
        self.lato = lato
        self.width = lato
        self.height = lato

    def draw(self):
        tela = self.canv
        tela.setLineWidth(0.7)
        tela.setStrokeColor(ACCENTO if self.spuntata else BORDO)
        tela.rect(0, 0, self.lato, self.lato, stroke=1, fill=0)

        if self.spuntata:
            tela.setStrokeColor(ACCENTO)
            tela.setLineWidth(1.2)
            percorso = tela.beginPath()
            percorso.moveTo(self.lato * 0.2, self.lato * 0.5)
            percorso.lineTo(self.lato * 0.42, self.lato * 0.24)
            percorso.lineTo(self.lato * 0.82, self.lato * 0.75)
            tela.drawPath(percorso, stroke=1, fill=0)


class Pallino(Flowable):
    """Il pallino della gravità, con gli stessi colori dello schermo."""

    def __init__(self, gravita: str, raggio: float = 3.4):
        super().__init__()
        self.gravita = gravita
        self.raggio = raggio
        self.width = raggio * 2
        self.height = raggio * 2

    def draw(self):
        tela = self.canv
        colore = COLORI_GRAVITA.get(self.gravita, COLORI_GRAVITA["nv"])
        if self.gravita == "nv":
            # Non valutato: cerchio vuoto, come il pallino tratteggiato a video.
            tela.setStrokeColor(colore)
            tela.setLineWidth(0.9)
            tela.circle(self.raggio, self.raggio, self.raggio, stroke=1, fill=0)
        else:
            tela.setFillColor(colore)
            tela.setStrokeColor(colore)
            tela.circle(self.raggio, self.raggio, self.raggio, stroke=0, fill=1)


class TelaNumerata(tela_reportlab.Canvas):
    """Tela che conosce il numero totale di pagine.

    ReportLab disegna una pagina alla volta e, mentre la disegna, non sa
    quante ne verranno dopo: non può quindi scrivere «Pagina 2 di 3». Il
    trucco è mettere da parte le pagine finite e scriverci sopra il piè di
    pagina solo alla fine, quando il totale è noto.

    È la stessa tecnica del diario di sviluppo.
    """

    def __init__(self, *args, piede: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._piede = piede
        self._pagine_da_stampare = []

    def showPage(self):  # noqa: N802 - nome imposto da ReportLab
        self._pagine_da_stampare.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        totale = len(self._pagine_da_stampare)
        for stato_pagina in self._pagine_da_stampare:
            self.__dict__.update(stato_pagina)
            self._disegna_piede(totale)
            super().showPage()
        super().save()

    def _disegna_piede(self, totale: int) -> None:
        self.setStrokeColor(BORDO)
        self.setLineWidth(0.5)
        self.line(MARGINE, 13 * mm, A4[0] - MARGINE, 13 * mm)

        self.setFont(NORMALE, 7.5)
        self.setFillColor(TENUE)
        self.drawString(MARGINE, 9 * mm, self._piede)
        self.drawRightString(
            A4[0] - MARGINE, 9 * mm, f"Pagina {self._pageNumber} di {totale}"
        )


# --------------------------------------------------------------------------
# Le sezioni del foglio
# --------------------------------------------------------------------------
def _intestazione(paziente, utente, stili, nome_struttura: str) -> list:
    return [
        Paragraph("Scheda paziente e Agenda", stili["titolo"]),
        Paragraph(nome_struttura, stili["struttura"]),
    ]


def _dati_paziente(paziente, utente, stili) -> list:
    """La scheda con i dati anagrafici e organizzativi."""
    gravita = Table(
        [[Pallino(paziente.gravita), Paragraph(
            GRAVITA.get(paziente.gravita, paziente.gravita), stili["valore"]
        )]],
        colWidths=[12, None],
    )
    gravita.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    righe = [
        ["Paziente", Paragraph(paziente.etichetta, stili["valore_forte"])],
        ["Reparto", Paragraph(paziente.reparto.nome, stili["valore"])],
        ["Posto letto", Paragraph(paziente.posto_letto, stili["valore"])],
        ["Gravità", gravita],
        ["Data di arrivo", Paragraph(data_italiana(paziente.data_arrivo), stili["valore"])],
        [
            "Dimissione presunta",
            Paragraph(
                data_italiana(paziente.data_dimissione_presunta), stili["valore"]
            ),
        ],
    ]

    tabella = Table(
        [[Paragraph(etichetta, stili["etichetta"]), valore] for etichetta, valore in righe],
        colWidths=[110, LARGHEZZA_UTILE - 110],
    )
    tabella.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("BACKGROUND", (0, 0), (0, -1), PAGINA),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDO),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDO),
            ]
        )
    )

    generato = (
        f"Documento generato il {data_italiana(oggi_italia())} da "
        f"{servizi_agenda.FIRMA_RUOLO.get(utente.ruolo, utente.etichetta_ruolo)}: "
        f"{utente.nome_completo}"
    )

    return [tabella, Paragraph(generato, stili["generato"])]


def _checklist(voci, spuntati, stili) -> list:
    """La checklist su due colonne, con il contatore."""
    fatte = sum(1 for voce in voci if voce.codice in spuntati)

    titolo = Paragraph(
        f"Checklist dimissione &nbsp;&nbsp;<font size=9 color='#5C6763'>"
        f"{fatte}/{len(voci)}</font>",
        stili["sezione"],
    )

    # Le voci si leggono per colonna, non per riga: la prima metà a sinistra
    # e la seconda a destra, come sullo schermo.
    meta = (len(voci) + 1) // 2
    sinistra, destra = voci[:meta], voci[meta:]

    righe = []
    for indice in range(meta):
        riga = []
        for colonna in (sinistra, destra):
            if indice < len(colonna):
                voce = colonna[indice]
                riga += [
                    Casella(voce.codice in spuntati),
                    Paragraph(voce.testo, stili["voce"]),
                ]
            else:
                riga += ["", ""]
        righe.append(riga)

    larghezza_testo = (LARGHEZZA_UTILE - 2 * 16) / 2
    tabella = Table(righe, colWidths=[16, larghezza_testo, 16, larghezza_testo])
    tabella.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#EDF0EE")),
            ]
        )
    )

    return [titolo, tabella]


def _note(gruppi, stili) -> list:
    """Lo storico delle note, nello stesso ordine e con le stesse firme."""
    elementi = [Paragraph("Agenda delle note", stili["sezione"])]

    if not gruppi:
        elementi.append(Paragraph("Nessuna nota per questo paziente.", stili["vuoto"]))
        return elementi

    for giorno, note in gruppi:
        elementi.append(
            Paragraph(servizi_agenda.intestazione_giorno(giorno), stili["giorno"])
        )
        for nota in note:
            elementi.append(_una_nota(nota, stili))

    return elementi


def _una_nota(nota, stili):
    """Una nota: firma, data, eventuale «modificata il», testo."""
    colore = COLORI_RUOLO.get(nota.autore_ruolo, TENUE)
    ruolo = servizi_agenda.FIRMA_RUOLO.get(nota.autore_ruolo, nota.autore_ruolo)

    # hexval() restituisce "0x6b4fa0": serve "#6b4fa0", altrimenti ReportLab
    # non riconosce il colore e la generazione fallisce.
    colore_html = "#" + colore.hexval()[2:]

    riga_firma = (
        f"<font color='{colore_html}'>{ruolo}:</font> {nota.autore_nome}"
        f"<font size=8 color='#5C6763'>&nbsp;&nbsp;{data_italiana(nota.data_nota)}</font>"
    )
    if nota.modificata_il:
        quando = data_italiana(a_ora_italiana(nota.modificata_il).date())
        riga_firma += (
            f"<font size=8 color='#5C6763'><i>&nbsp;&nbsp;modificata il {quando}</i></font>"
        )

    # Gli a capo scritti dall'utente diventano <br/>: ReportLab legge i
    # paragrafi come XML e ignorerebbe gli a capo veri.
    testo = _per_paragrafo(nota.testo)

    contenuto = Table(
        [[Paragraph(riga_firma, stili["firma"])], [Paragraph(testo, stili["testo_nota"])]],
        colWidths=[LARGHEZZA_UTILE - 8],
    )
    contenuto.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (0, 0), 1),
                ("BOTTOMPADDING", (0, 1), (0, 1), 7),
                # La barretta colorata a sinistra, come nell'Agenda a video.
                ("LINEBEFORE", (0, 0), (0, -1), 1.6, colore),
            ]
        )
    )
    # KeepTogether evita che la firma resti in fondo a una pagina e il testo
    # cominci in quella dopo.
    return KeepTogether(contenuto)


def _per_paragrafo(testo: str) -> str:
    """Prepara un testo scritto da una persona per finire in un paragrafo.

    ReportLab interpreta i paragrafi come XML: i caratteri &, < e > vanno
    disinnescati, altrimenti una nota che contiene «PA < 90» farebbe fallire
    la generazione del PDF. L'ordine conta: & va sostituita per prima.
    """
    pulito = (
        testo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return pulito.replace("\n", "<br/>")


# --------------------------------------------------------------------------
# Funzione principale
# --------------------------------------------------------------------------
def nome_file(paziente, giorno: date | None = None) -> str:
    """«Agenda_Rossi_Mario_2026-09-18.pdf»."""
    giorno = giorno or oggi_italia()

    def pulisci(parte: str) -> str:
        # Spazi e caratteri strani nel nome di un file scaricato creano guai
        # su Windows: restano solo lettere, numeri e trattini.
        ammessi = [c if (c.isalnum() or c in "-_") else "_" for c in parte]
        return "".join(ammessi).strip("_") or "paziente"

    return (
        f"Agenda_{pulisci(paziente.cognome)}_{pulisci(paziente.nome)}"
        f"_{giorno.isoformat()}.pdf"
    )


def genera_scheda(paziente, note, voci, spuntati, utente, nome_struttura: str) -> bytes:
    """Costruisce il PDF e restituisce i byte pronti da scaricare."""
    registra_font()
    stili = crea_stili()

    memoria = BytesIO()
    documento = SimpleDocTemplate(
        memoria,
        pagesize=A4,
        leftMargin=MARGINE,
        rightMargin=MARGINE,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title=f"Scheda paziente — {paziente.etichetta}",
        author=nome_struttura,
        subject="Scheda paziente e Agenda",
    )

    storia = []
    storia += _intestazione(paziente, utente, stili, nome_struttura)
    storia += _dati_paziente(paziente, utente, stili)
    storia += _checklist(voci, spuntati, stili)
    storia.append(Spacer(1, 4))
    storia += _note(servizi_agenda.raggruppa_per_giorno(note), stili)

    piede = f"{paziente.etichetta} - letto {paziente.posto_letto}"

    def crea_tela(*args, **kwargs):
        return TelaNumerata(*args, piede=piede, **kwargs)

    documento.build(storia, canvasmaker=crea_tela)

    return memoria.getvalue()
