<#
.SYNOPSIS
    Prüft die Bibliothek und baut die Release-Dateien nach dist\.

.DESCRIPTION
    Prüfungen:
      - VERSION hat das Format X.Y.Z (und passt zum Tag, falls -Tag angegeben)
      - CHANGELOG.md hat einen Abschnitt "## X.Y.Z"
      - jede Grafik, auf die die .pgl verweist, liegt in vg\
      - jedes Bild, auf das eine .bg-Grafik verweist, liegt in image\

    Ergebnis in dist\:
      spstiger-free-DTools-components.zip   – nur die Bibliothek (Ordner für usrlib)
      spstiger-Bibliothek-Updater.zip       – Update-Skript für Kunden
      release-notes.md                      – Abschnitt aus CHANGELOG.md

    Läuft lokal und im GitHub-Workflow (.github\workflows\release.yml).

.EXAMPLE
    pwsh tools\Build-Release.ps1
.EXAMPLE
    pwsh tools\Build-Release.ps1 -Tag v1.1.0
#>
[CmdletBinding()]
param([string]$Tag)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = Split-Path $PSScriptRoot -Parent
$name = 'spstiger-free-DTools-components'
$fehler = [Collections.Generic.List[string]]::new()

# --- Version ----------------------------------------------------------------------
$version = (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') { $fehler.Add("VERSION '$version' hat nicht das Format X.Y.Z") }
if ($Tag -and $Tag.TrimStart('v') -ne $version) { $fehler.Add("Tag '$Tag' passt nicht zu VERSION '$version'") }

$changelog = Get-Content -LiteralPath (Join-Path $root 'CHANGELOG.md')
$start = [array]::IndexOf($changelog, "## $version")
if ($start -lt 0) { $fehler.Add("CHANGELOG.md hat keinen Abschnitt '## $version'") }

# --- Verweise -----------------------------------------------------------------------
$pgl = Join-Path $root "$name.pgl"
$pglText = Get-Content -LiteralPath $pgl -Raw
try { [xml]$pglText | Out-Null } catch { $fehler.Add("$name.pgl ist kein gültiges XML: $($_.Exception.Message)") }

$grafiken = [regex]::Matches($pglText, 'URL="\.\\vg\\([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique
foreach ($g in $grafiken) {
    $datei = Join-Path $root "vg\$g"
    if (-not (Test-Path -LiteralPath $datei)) { $fehler.Add("vg\$g fehlt (verwendet in $name.pgl)"); continue }
    $bilder = [regex]::Matches((Get-Content -LiteralPath $datei -Raw), 'src="\.\.\\image\\([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    foreach ($b in $bilder) {
        if (-not (Test-Path -LiteralPath (Join-Path $root "image\$b"))) { $fehler.Add("image\$b fehlt (verwendet in vg\$g)") }
    }
}

if ($fehler.Count) {
    $fehler | ForEach-Object { Write-Host "FEHLER: $_" -ForegroundColor Red }
    exit 1
}
Write-Host "Prüfung ok: Version $version, $($grafiken.Count) Grafiken" -ForegroundColor Green

# --- Bauen ------------------------------------------------------------------------
$dist = Join-Path $root 'dist'
if (Test-Path -LiteralPath $dist) { Remove-Item -LiteralPath $dist -Recurse -Force }
$lib = Join-Path $dist "staging\$name"
New-Item -ItemType Directory -Path $lib | Out-Null
Copy-Item -LiteralPath $pgl, (Join-Path $root 'VERSION'), (Join-Path $root 'LICENSE') -Destination $lib
Copy-Item -LiteralPath (Join-Path $root 'vg'), (Join-Path $root 'image') -Destination $lib -Recurse
[IO.Compression.ZipFile]::CreateFromDirectory($lib, (Join-Path $dist "$name.zip"), 'Optimal', $true)

$upd = Join-Path $dist 'staging\updater'
New-Item -ItemType Directory -Path $upd | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Update-spstigerBibliothek.ps1'), (Join-Path $PSScriptRoot 'spstiger-Bibliothek-aktualisieren.cmd'), (Join-Path $root 'LICENSE') -Destination $upd
[IO.Compression.ZipFile]::CreateFromDirectory($upd, (Join-Path $dist 'spstiger-Bibliothek-Updater.zip'), 'Optimal', $false)

$ende = $start + 1
while ($ende -lt $changelog.Count -and $changelog[$ende] -notmatch '^## ') { $ende++ }
($changelog[($start + 1)..($ende - 1)] -join "`n").Trim() | Set-Content -LiteralPath (Join-Path $dist 'release-notes.md') -Encoding utf8

Remove-Item -LiteralPath (Join-Path $dist 'staging') -Recurse -Force
Get-ChildItem -LiteralPath $dist | ForEach-Object { Write-Host ("  {0,-40} {1,8:N0} Byte" -f $_.Name, $_.Length) }
