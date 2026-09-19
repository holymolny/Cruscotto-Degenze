<#
    Ricava dal logo della struttura le immagini che servono all'installer:

      cruscotto.ico        icona del setup, del collegamento e della finestra
      wizard-grande.bmp    banner laterale della prima e dell'ultima pagina
      wizard-piccolo.bmp   logo in alto a destra nelle pagine intermedie

    Va rilanciato solo se cambia il logo in app\static\img. I file che
    produce sono versionati insieme al resto, così per ricompilare il setup
    basta Compila.ps1.

    Inno Setup accetta per le due immagini della procedura guidata solo il
    formato BMP, non il PNG: per questo le convertiamo qui invece di puntare
    direttamente ai file del programma.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$Risorse  = $PSScriptRoot
$Radice   = Split-Path -Parent (Split-Path -Parent $Risorse)
$Emblema  = Join-Path $Radice 'app\static\img\logo-emblema.png'
$Completo = Join-Path $Radice 'app\static\img\logo-casa-cura.png'

foreach ($f in @($Emblema, $Completo)) {
    if (-not (Test-Path $f)) { throw "Manca il file del logo: $f" }
}

# --------------------------------------------------------------------------
# Funzioni di appoggio
# --------------------------------------------------------------------------

function New-TelaQuadrata {
    <#  Mette l'immagine, che è più larga che alta, al centro di una tela
        quadrata trasparente: un'icona di Windows deve essere quadrata, e
        senza questo passaggio il logo risulterebbe schiacciato. #>
    param([System.Drawing.Image]$Immagine)

    $lato = [Math]::Max($Immagine.Width, $Immagine.Height)
    $tela = New-Object System.Drawing.Bitmap($lato, $lato, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($tela)
    try {
        $g.Clear([System.Drawing.Color]::Transparent)
        $g.InterpolationMode = 'HighQualityBicubic'
        $g.DrawImage($Immagine, [int](($lato - $Immagine.Width) / 2), [int](($lato - $Immagine.Height) / 2),
                     $Immagine.Width, $Immagine.Height)
    } finally { $g.Dispose() }
    return $tela
}

function New-Ridimensionata {
    param([System.Drawing.Image]$Immagine, [int]$Lato)

    $piccola = New-Object System.Drawing.Bitmap($Lato, $Lato, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($piccola)
    try {
        $g.Clear([System.Drawing.Color]::Transparent)
        $g.InterpolationMode  = 'HighQualityBicubic'
        $g.SmoothingMode      = 'HighQuality'
        $g.PixelOffsetMode    = 'HighQuality'
        $g.DrawImage($Immagine, 0, 0, $Lato, $Lato)
    } finally { $g.Dispose() }
    return $piccola
}

function Get-PixelBgraCapovolti {
    <#  Restituisce i pixel in formato BGRA partendo dall'ultima riga.

        Un'icona classica di Windows contiene una "DIB", e le DIB si leggono
        dal basso verso l'alto: la prima riga del file è l'ultima riga
        dell'immagine. Se non capovolgessimo, l'icona apparirebbe a testa in
        giù. #>
    param([System.Drawing.Bitmap]$Bitmap)

    $rett = New-Object System.Drawing.Rectangle(0, 0, $Bitmap.Width, $Bitmap.Height)
    $dati = $Bitmap.LockBits($rett, [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
                             [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    try {
        $passo  = $dati.Stride
        $buffer = New-Object byte[] ($passo * $Bitmap.Height)
        [System.Runtime.InteropServices.Marshal]::Copy($dati.Scan0, $buffer, 0, $buffer.Length)
    } finally { $Bitmap.UnlockBits($dati) }

    $utili       = $Bitmap.Width * 4
    $capovolti   = New-Object byte[] ($utili * $Bitmap.Height)
    for ($riga = 0; $riga -lt $Bitmap.Height; $riga++) {
        $origine    = ($Bitmap.Height - 1 - $riga) * $passo
        $destinazione = $riga * $utili
        [Array]::Copy($buffer, $origine, $capovolti, $destinazione, $utili)
    }
    # La virgola non è un errore di battitura: senza, PowerShell srotolerebbe
    # l'array in tanti singoli byte e chi riceve il risultato si troverebbe un
    # elenco di oggetti al posto dei dati grezzi.
    return , $capovolti
}

function Save-Icona {
    <#  Scrive un .ico con più misure dentro, in formato DIB a 32 bit.

        Usiamo la forma classica e non i riquadri compressi in PNG perché è
        quella che capiscono proprio tutti, compresi il compilatore di Inno
        Setup e le finestre di dialogo più vecchie di Windows. #>
    param([System.Drawing.Bitmap]$Quadrata, [string]$Destinazione, [int[]]$Misure)

    $riquadri = @()
    foreach ($lato in $Misure) {
        $bmp = New-Ridimensionata -Immagine $Quadrata -Lato $lato
        try {
            $pixel = Get-PixelBgraCapovolti -Bitmap $bmp

            # La maschera di trasparenza in bianco e nero: non serve, perché
            # la trasparenza vera sta già nel canale alfa dei pixel, ma il
            # formato la pretende lo stesso. La lasciamo tutta a zero.
            $bytePerRiga  = [int][Math]::Ceiling($lato / 8)
            $bytePerRiga  = [int]([Math]::Ceiling($bytePerRiga / 4) * 4)   # righe allineate a 4 byte
            $maschera     = New-Object byte[] ($bytePerRiga * $lato)

            $flusso   = New-Object System.IO.MemoryStream
            $scrittore = New-Object System.IO.BinaryWriter($flusso)
            $scrittore.Write([int]40)              # dimensione dell'intestazione
            $scrittore.Write([int]$lato)           # larghezza
            $scrittore.Write([int]($lato * 2))     # altezza: immagine + maschera
            $scrittore.Write([int16]1)             # piani
            $scrittore.Write([int16]32)            # bit per pixel
            $scrittore.Write([int]0)               # nessuna compressione
            $scrittore.Write([int]($pixel.Length + $maschera.Length))
            $scrittore.Write([int]0); $scrittore.Write([int]0)   # risoluzione
            $scrittore.Write([int]0); $scrittore.Write([int]0)   # tavolozza
            $scrittore.Write($pixel)
            $scrittore.Write($maschera)
            $scrittore.Flush()

            $riquadri += [pscustomobject]@{ Lato = $lato; Dati = $flusso.ToArray() }
            $scrittore.Dispose(); $flusso.Dispose()
        } finally { $bmp.Dispose() }
    }

    $flusso    = New-Object System.IO.MemoryStream
    $scrittore = New-Object System.IO.BinaryWriter($flusso)
    $scrittore.Write([int16]0)                    # riservato
    $scrittore.Write([int16]1)                    # 1 = icona
    $scrittore.Write([int16]$riquadri.Count)

    # 6 byte di intestazione + 16 per ogni voce dell'indice.
    $scarto = 6 + (16 * $riquadri.Count)
    foreach ($r in $riquadri) {
        # 256 non entra in un byte: il formato vuole 0 per indicare 256.
        $misura = if ($r.Lato -ge 256) { 0 } else { $r.Lato }
        $scrittore.Write([byte]$misura)           # larghezza
        $scrittore.Write([byte]$misura)           # altezza
        $scrittore.Write([byte]0)                 # colori della tavolozza
        $scrittore.Write([byte]0)                 # riservato
        $scrittore.Write([int16]1)                # piani
        $scrittore.Write([int16]32)               # bit per pixel
        $scrittore.Write([int]$r.Dati.Length)
        $scrittore.Write([int]$scarto)
        $scarto += $r.Dati.Length
    }
    foreach ($r in $riquadri) { $scrittore.Write($r.Dati) }
    $scrittore.Flush()

    [System.IO.File]::WriteAllBytes($Destinazione, $flusso.ToArray())
    $scrittore.Dispose(); $flusso.Dispose()
}

function Save-BmpProcedura {
    <#  Un BMP a 24 bit della misura esatta che vuole Inno Setup, con il logo
        centrato su fondo bianco e un margine attorno. #>
    param([string]$Origine, [string]$Destinazione, [int]$Larghezza, [int]$Altezza, [int]$Margine)

    $logo = [System.Drawing.Image]::FromFile($Origine)
    try {
        $tela = New-Object System.Drawing.Bitmap($Larghezza, $Altezza, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        $g = [System.Drawing.Graphics]::FromImage($tela)
        try {
            $g.Clear([System.Drawing.Color]::White)
            $g.InterpolationMode = 'HighQualityBicubic'
            $g.SmoothingMode     = 'HighQuality'
            $g.PixelOffsetMode   = 'HighQuality'

            # Il logo entra per intero nello spazio disponibile senza deformarsi.
            $spazioL = $Larghezza - (2 * $Margine)
            $spazioA = $Altezza   - (2 * $Margine)
            $scala   = [Math]::Min($spazioL / $logo.Width, $spazioA / $logo.Height)
            $l = [int]($logo.Width  * $scala)
            $a = [int]($logo.Height * $scala)
            $g.DrawImage($logo, [int](($Larghezza - $l) / 2), [int](($Altezza - $a) / 2), $l, $a)
        } finally { $g.Dispose() }

        $tela.Save($Destinazione, [System.Drawing.Imaging.ImageFormat]::Bmp)
        $tela.Dispose()
    } finally { $logo.Dispose() }
}

# --------------------------------------------------------------------------
# Produzione dei file
# --------------------------------------------------------------------------

$sorgente = [System.Drawing.Image]::FromFile($Emblema)
try {
    $quadrata = New-TelaQuadrata -Immagine $sorgente
    try {
        Save-Icona -Quadrata $quadrata -Destinazione (Join-Path $Risorse 'cruscotto.ico') `
                   -Misure @(16, 24, 32, 48, 64, 128, 256)
    } finally { $quadrata.Dispose() }
} finally { $sorgente.Dispose() }

# Le misure sono quelle previste da Inno Setup con lo stile "modern".
Save-BmpProcedura -Origine $Completo -Destinazione (Join-Path $Risorse 'wizard-grande.bmp') `
                  -Larghezza 164 -Altezza 314 -Margine 14
Save-BmpProcedura -Origine $Emblema -Destinazione (Join-Path $Risorse 'wizard-piccolo.bmp') `
                  -Larghezza 138 -Altezza 140 -Margine 10

Get-ChildItem -Path (Join-Path $Risorse '*') -Include '*.ico', '*.bmp' -File | ForEach-Object {
    '{0,-22} {1,9:N0} byte' -f $_.Name, $_.Length
}
