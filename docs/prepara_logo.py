"""Ricava dal logo originale le due immagini usate dal programma.

Si lancia una volta sola, o quando l'ufficio comunicazione consegna un logo
nuovo:

    python docs/prepara_logo.py

Perché non usare direttamente il file originale? Perché pesa 2,1 MB. Su un PC
di reparto collegato in rete significa un'attesa inutile a ogni accesso, e il
browser lo rimpicciolirebbe comunque a 190 pixel. Meglio consegnargli
un'immagine già della misura giusta.

Le due immagini prodotte:

  logo-casa-cura.png   marchio completo (stemma + nome), per la pagina di accesso
  logo-emblema.png     solo lo stemma, per la barra laterale

Sono generate al doppio della misura a cui vengono mostrate, così restano
nitide anche sugli schermi ad alta densità.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms

RADICE = Path(__file__).resolve().parent.parent
ORIGINALE = RADICE / "PromptIA" / "LOGO CASA verticale.jpg"
DESTINAZIONE = RADICE / "app" / "static" / "img"

# Larghezze in pixel: il doppio di come vengono mostrate nella pagina.
LARGHEZZA_COMPLETO = 380
LARGHEZZA_EMBLEMA = 160

# Sotto questa riga inizia la scritta «CASA DI CURA»: l'abbiamo trovata
# cercando le fasce di pixel bianchi che separano le parti del logo.
FINE_EMBLEMA = 645

SOGLIA_BIANCO = 245

# Il logo usa poche tinte piatte: 64 sono più che sufficienti e fanno crollare
# il peso del file. Vedi riduci_colori() per il motivo.
COLORI_TAVOLOZZA = 64


def converti_in_srgb(img: Image.Image) -> Image.Image:
    """Converte i colori in sRGB e butta via il profilo colore.

    Il file originale arriva dalla grafica e porta con sé un profilo colore
    ICC da 1,8 MB: una tabella che descrive esattamente come vanno resi i
    colori in stampa. In tipografia è prezioso, sul web è zavorra — pesa
    cinque volte l'immagine stessa e i browser assumono comunque sRGB.

    Non basta però cancellarlo: i colori sono espressi <i>secondo quel
    profilo</i>, quindi buttandolo via e basta le tinte si sposterebbero.
    Prima li traduciamo in sRGB, poi il profilo non serve più.
    """
    profilo_originale = img.info.get("icc_profile")
    if not profilo_originale:
        return img

    origine = ImageCms.ImageCmsProfile(BytesIO(profilo_originale))
    destinazione = ImageCms.createProfile("sRGB")
    convertita = ImageCms.profileToProfile(
        img, origine, destinazione, outputMode="RGB"
    )
    convertita.info.pop("icc_profile", None)
    return convertita


def ritaglia_bordi_bianchi(img: Image.Image) -> Image.Image:
    """Toglie la cornice bianca attorno al disegno.

    Senza, l'immagine porterebbe con sé un margine invisibile e allinearla
    accanto a un testo diventerebbe una lotta di pixel.
    """
    grigi = img.convert("L")
    # point() trasforma ogni pixel: bianco -> 0, tutto il resto -> 255.
    # getbbox() restituisce poi il rettangolo che contiene i pixel non nulli.
    maschera = grigi.point(lambda valore: 0 if valore >= SOGLIA_BIANCO else 255)
    riquadro = maschera.getbbox()
    return img.crop(riquadro) if riquadro else img


def ridimensiona(img: Image.Image, larghezza: int) -> Image.Image:
    """Porta l'immagine alla larghezza voluta, mantenendo le proporzioni."""
    altezza = round(img.height * larghezza / img.width)
    # LANCZOS è il metodo che conserva meglio i bordi netti di un logo.
    return img.resize((larghezza, altezza), Image.LANCZOS)


def riduci_colori(img: Image.Image, colori: int = COLORI_TAVOLOZZA) -> Image.Image:
    """Riduce l'immagine a una tavolozza di pochi colori.

    Serve a rimediare al formato di partenza. Il logo usa una manciata di
    colori piatti, ma è stato consegnato in JPG, un formato pensato per le
    fotografie: comprimendo ha sparso attorno a ogni contorno migliaia di
    sfumature quasi identiche, invisibili a occhio nudo.

    Il PNG comprime bene le tinte piatte e malissimo quelle sfumature: senza
    questo passaggio un'immagine da 380 pixel pesava 1,3 MB. Rimettendo i
    colori a 64, il disegno resta identico e il file scende sotto i 30 KB.
    """
    return img.quantize(colors=colori, method=Image.MEDIANCUT, dither=Image.NONE)


def salva(img: Image.Image, nome: str) -> Path:
    percorso = DESTINAZIONE / nome
    finale = riduci_colori(img)
    # Ripulire info evita che metadati dell'originale (profilo colore, dati
    # Photoshop, EXIF della macchina fotografica) si riaffaccino nel PNG.
    finale.info = {}
    # optimize=True fa provare a Pillow più strategie di compressione e
    # tenere la migliore: su un disegno a tinte piatte fa molta differenza.
    finale.save(percorso, "PNG", optimize=True)
    return percorso


def main() -> None:
    if not ORIGINALE.exists():
        raise SystemExit(f"Logo originale non trovato: {ORIGINALE}")

    DESTINAZIONE.mkdir(parents=True, exist_ok=True)
    originale = converti_in_srgb(Image.open(ORIGINALE)).convert("RGB")

    completo = ridimensiona(ritaglia_bordi_bianchi(originale), LARGHEZZA_COMPLETO)
    percorso_completo = salva(completo, "logo-casa-cura.png")

    solo_stemma = originale.crop((0, 0, originale.width, FINE_EMBLEMA))
    emblema = ridimensiona(ritaglia_bordi_bianchi(solo_stemma), LARGHEZZA_EMBLEMA)
    percorso_emblema = salva(emblema, "logo-emblema.png")

    for percorso, immagine in (
        (percorso_completo, completo),
        (percorso_emblema, emblema),
    ):
        peso = percorso.stat().st_size / 1024
        print(f"{percorso.name:<22} {immagine.width}x{immagine.height} px   {peso:.0f} KB")


if __name__ == "__main__":
    main()
