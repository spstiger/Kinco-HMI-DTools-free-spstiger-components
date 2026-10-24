<#
.SYNOPSIS
    Installiert oder aktualisiert die kostenlose spstiger-Komponentenbibliothek
    in allen installierten Kinco DTools V4.

.DESCRIPTION
    Lädt das aktuelle Release von GitHub, sucht alle Ordner "Kinco DTools V4*"
    unter C:\Kinco und ersetzt dort usrlib\spstiger-free-DTools-components.
    Die vorherige Fassung wird vorher gesichert nach
    %LOCALAPPDATA%\spstiger\DTools-Bibliothek\Sicherung.

    Ordner, die per Git (GitHub Desktop) oder Junction eingebunden sind,
    werden nicht angefasst – die aktualisiert man über GitHub Desktop.

.PARAMETER Quelle
    URL oder lokaler Pfad zur Release-ZIP (oder zu einem entpackten Ordner).
    Standard: neuestes Release auf GitHub.

.PARAMETER KincoOrdner
    Wo die DTools-Installationen liegen. Standard: C:\Kinco

.PARAMETER Usrlib
    Einzelne usrlib-Ordner direkt angeben statt zu suchen.

.PARAMETER Erzwingen
    Auch installieren, wenn dieselbe Version schon vorhanden ist.

.PARAMETER NurPruefen
    Nur anzeigen, was installiert ist und was passieren würde.

.EXAMPLE
    .\Update-spstigerBibliothek.ps1
.EXAMPLE
    .\Update-spstigerBibliothek.ps1 -KincoOrdner "D:\Programme\Kinco" -NurPruefen
#>
[CmdletBinding()]
param(
    [string]$Quelle = 'https://github.com/spstiger/Kinco-HMI-DTools-free-spstiger-components/releases/latest/download/spstiger-free-DTools-components.zip',
    [string]$KincoOrdner = 'C:\Kinco',
    [string[]]$Usrlib,
    [switch]$Erzwingen,
    [switch]$NurPruefen
)

$ErrorActionPreference = 'Stop'
$Name = 'spstiger-free-DTools-components'
$SicherungsOrdner = Join-Path $env:LOCALAPPDATA 'spstiger\DTools-Bibliothek\Sicherung'

function Schreibe([string]$Text, [string]$Farbe = 'Gray') { Write-Host $Text -ForegroundColor $Farbe }

function Lies-Version([string]$Ordner) {
    $datei = Join-Path $Ordner 'VERSION'
    if (Test-Path -LiteralPath $datei) { return (Get-Content -LiteralPath $datei -Raw).Trim() }
    return $null
}

function Ist-Verknuepfung([string]$Ordner) {
    $item = Get-Item -LiteralPath $Ordner -Force
    return [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
}

Schreibe ''
Schreibe 'spstiger-Komponentenbibliothek für Kinco DTools V4' 'Cyan'
Schreibe '=================================================' 'Cyan'

# --- 1. DTools darf nicht laufen ------------------------------------------------
if (-not $NurPruefen) {
    $laufend = Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like 'Kinco DTools*' }
    if ($laufend) {
        Schreibe 'Kinco DTools ist geöffnet. Bitte DTools schließen und das Skript erneut starten.' 'Yellow'
        exit 2
    }
}

# --- 2. usrlib-Ordner finden ----------------------------------------------------
if (-not $Usrlib) {
    if (-not (Test-Path -LiteralPath $KincoOrdner)) {
        Schreibe "Ordner $KincoOrdner nicht gefunden. Pfad mit -KincoOrdner angeben." 'Red'
        exit 1
    }
    $Usrlib = Get-ChildItem -LiteralPath $KincoOrdner -Directory |
        Where-Object { $_.Name -like 'Kinco DTools V4*' } |
        ForEach-Object { Join-Path $_.FullName 'usrlib' } |
        Where-Object { Test-Path -LiteralPath $_ }
}
if (-not $Usrlib) {
    Schreibe "Keine Installation 'Kinco DTools V4*' mit usrlib-Ordner unter $KincoOrdner gefunden." 'Red'
    exit 1
}

# --- 3. Neue Fassung holen --------------------------------------------------------
$arbeit = Join-Path ([IO.Path]::GetTempPath()) ("spstiger-dtools-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $arbeit | Out-Null
try {
    if ($Quelle -match '^https?://') {
        Schreibe "Lade $Quelle"
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $zip = Join-Path $arbeit 'bibliothek.zip'
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $Quelle -OutFile $zip -UseBasicParsing
    } else {
        $zip = $Quelle
    }

    if (Test-Path -LiteralPath $zip -PathType Container) {
        $entpackt = $zip
    } else {
        $entpackt = Join-Path $arbeit 'entpackt'
        Expand-Archive -LiteralPath $zip -DestinationPath $entpackt
    }

    $pgl = Get-ChildItem -LiteralPath $entpackt -Recurse -Depth 1 -Filter "$Name.pgl" | Select-Object -First 1
    if (-not $pgl) { throw "In der Quelle fehlt $Name.pgl – ist das die richtige ZIP-Datei?" }
    $neu = $pgl.DirectoryName
    $neueVersion = Lies-Version $neu
    if (-not $neueVersion) { throw 'In der Quelle fehlt die Datei VERSION.' }
    Schreibe "Neue Version: $neueVersion" 'Green'
    Schreibe ''

    # --- 4. Je DTools-Installation ersetzen ---------------------------------------
    $fehler = 0
    $zeit = Get-Date -Format 'yyyy-MM-dd_HHmmss'
    foreach ($u in $Usrlib) {
        $dtools = Split-Path (Split-Path $u -Parent) -Leaf
        Schreibe "[$dtools]" 'Cyan'

        # Alle vorhandenen Kopien dieser Bibliothek (auch alte ZIP-Ordner wie "...-main")
        $vorhanden = @(Get-ChildItem -LiteralPath $u -Directory -Force |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "$Name.pgl") })

        $git = $vorhanden | Where-Object { (Ist-Verknuepfung $_.FullName) -or (Test-Path -LiteralPath (Join-Path $_.FullName '.git')) }
        if ($git) {
            Schreibe "  Übersprungen: '$($git[0].Name)' ist per Git/Junction eingebunden – bitte über GitHub Desktop aktualisieren (Fetch/Pull)." 'Yellow'
            continue
        }

        $ziel = Join-Path $u $Name
        $alt = if ($vorhanden.Count -gt 0) { Lies-Version $vorhanden[0].FullName } else { $null }
        $altText = if ($vorhanden.Count -eq 0) { 'nicht installiert' } elseif ($alt) { $alt } else { 'unbekannt (vor 1.0.0)' }
        Schreibe "  Installiert: $altText"

        $nurZiel = ($vorhanden.Count -eq 1) -and ($vorhanden[0].Name -eq $Name)
        if ($nurZiel -and $alt -eq $neueVersion -and -not $Erzwingen) {
            Schreibe '  Bereits aktuell.' 'Green'
            continue
        }
        if ($NurPruefen) {
            Schreibe "  Würde aktualisieren auf $neueVersion." 'Yellow'
            continue
        }

        try {
            foreach ($v in $vorhanden) {
                $sicherung = Join-Path $SicherungsOrdner (Join-Path $dtools (Join-Path $zeit $v.Name))
                New-Item -ItemType Directory -Path (Split-Path $sicherung -Parent) -Force | Out-Null
                Copy-Item -LiteralPath $v.FullName -Destination $sicherung -Recurse
                Remove-Item -LiteralPath $v.FullName -Recurse -Force
                Schreibe "  Gesichert: $sicherung"
            }
            Copy-Item -LiteralPath $neu -Destination $ziel -Recurse
            Schreibe "  Aktualisiert auf $neueVersion." 'Green'
        } catch [UnauthorizedAccessException] {
            $fehler++
            Schreibe "  Keine Schreibrechte in $u – Skript bitte als Administrator ausführen." 'Red'
        } catch {
            $fehler++
            Schreibe "  Fehler: $($_.Exception.Message)" 'Red'
        }
    }

    Schreibe ''
    if ($fehler) {
        Schreibe "Fertig mit $fehler Fehler(n)." 'Red'
        exit 1
    }
    Schreibe 'Fertig. In DTools: Rechtsklick > Eigene Komponenten > Eigene Komponenten nutzen.' 'Green'
    Schreibe 'Hinweis: Schon eingefügte Komponenten in bestehenden Projekten ändern sich nicht.'
    Schreibe ''
    Schreibe 'Für künftige Updates dieses Skript einfach erneut starten – es holt immer die neueste Version.' 'Cyan'
    exit 0
}
catch {
    Schreibe "Abbruch: $($_.Exception.Message)" 'Red'
    exit 1
}
finally {
    Remove-Item -LiteralPath $arbeit -Recurse -Force -ErrorAction SilentlyContinue
}
