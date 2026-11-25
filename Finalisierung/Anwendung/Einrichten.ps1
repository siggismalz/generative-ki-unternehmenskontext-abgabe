param(
    [string]$DownloadOrdner = ""
)

# Einmaliger Bezug der festgelegten Originaldateien. Keine globale Installation.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression

$Projektordner = [IO.Path]::GetFullPath($PSScriptRoot)
$Zwischenordner = Join-Path $Projektordner '.downloads'

function Pruefe-Datei([string]$Pfad, [string]$SollHash) {
    if (-not (Test-Path -LiteralPath $Pfad -PathType Leaf)) { return $false }
    return (Get-FileHash -LiteralPath $Pfad -Algorithm SHA256).Hash -eq $SollHash
}

function Hole-Datei([string]$Url, [string]$Dateiname, [string]$Ziel, [string]$SollHash) {
    $Ziel = [IO.Path]::GetFullPath($Ziel)
    if (-not $Ziel.StartsWith($Projektordner.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Das Downloadziel liegt ausserhalb des Projektordners.'
    }
    if (Pruefe-Datei $Ziel $SollHash) {
        Write-Host "Bereits vorhanden und geprueft: $Dateiname"
        return
    }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Ziel)) | Out-Null
    $Teil = $Ziel + '.part'
    if (-not (Pruefe-Datei $Teil $SollHash)) {
        $Vorhanden = if ($DownloadOrdner) { Join-Path $DownloadOrdner $Dateiname } else { $null }
        if ($Vorhanden -and (Test-Path -LiteralPath $Vorhanden -PathType Leaf)) {
            if (-not (Pruefe-Datei $Vorhanden $SollHash)) {
                throw "Pruefsumme der lokalen Originaldatei stimmt nicht: $Vorhanden"
            }
            Write-Host "Uebernehme gepruefte Originaldatei: $Dateiname"
            Copy-Item -LiteralPath $Vorhanden -Destination $Teil -Force
        } else {
            Write-Host "Lade $Dateiname von der Originalquelle ..."
            try {
                Invoke-WebRequest -Uri $Url -UseBasicParsing -OutFile $Teil
            } catch {
                throw "Download fehlgeschlagen: $Dateiname. Die Teildatei bleibt unter $Teil erhalten. Einrichten.cmd kann erneut gestartet werden. Ursache: $($_.Exception.Message)"
            }
        }
    }
    if (-not (Pruefe-Datei $Teil $SollHash)) {
        throw "SHA256-Pruefung fehlgeschlagen: $Dateiname. Die Datei wurde nicht verwendet. Teildatei: $Teil"
    }
    # Nur die einzelne gepruefte Datei wird innerhalb des Projektordners umbenannt.
    Move-Item -LiteralPath $Teil -Destination $Ziel -Force
    Write-Host "SHA256 bestaetigt: $Dateiname"
}

function Entpacke-Archiv([string]$Archivpfad, [string]$Zielordner, [bool]$NurLlama) {
    $Zielwurzel = [IO.Path]::GetFullPath($Zielordner).TrimEnd('\') + '\'
    [IO.Directory]::CreateDirectory($Zielwurzel) | Out-Null
    $Archiv = [IO.Compression.ZipFile]::OpenRead($Archivpfad)
    try {
        foreach ($Eintrag in $Archiv.Entries) {
            if (-not $Eintrag.Name) { continue }
            $Relativ = $Eintrag.FullName.Replace('/', '\')
            $Ziel = [IO.Path]::GetFullPath((Join-Path $Zielwurzel $Relativ))
            if (-not $Ziel.StartsWith($Zielwurzel, [StringComparison]::OrdinalIgnoreCase)) {
                throw "Unsicherer Pfad im Originalarchiv: $($Eintrag.FullName)"
            }
            if ($NurLlama) {
                # Der festgelegte Release enthaelt seine Laufzeitdateien flach.
                # Keine Benchmarks oder sonstigen EXE-Werkzeuge installieren.
                $Name = $Eintrag.Name
                if ($Name -ne 'llama-server.exe' -and $Name -notlike '*.dll' -and $Name -notlike 'LICENSE*') { continue }
                if ($Relativ -ne $Name) { throw "Unerwartete Ordnerstruktur im llama.cpp-Archiv: $Relativ" }
            }
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Ziel)) | Out-Null
            [IO.Compression.ZipFileExtensions]::ExtractToFile($Eintrag, $Ziel, $true)
        }
    } finally {
        $Archiv.Dispose()
    }
}

try {
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw 'Der Demonstrator benoetigt Windows x64.'
    }
    if ($DownloadOrdner) {
        $DownloadOrdner = (Resolve-Path -LiteralPath $DownloadOrdner).Path
        if (-not (Test-Path -LiteralPath $DownloadOrdner -PathType Container)) { throw 'DownloadOrdner muss ein Ordner sein.' }
    }
    Write-Host 'Einrichtung des lokalen Uebersetzungsdemonstrators'
    Write-Host 'Einmaliger Download: ca. 2,53 GB. Danach arbeitet die Anwendung lokal.'
    Write-Host 'Bitte mindestens 6 GB freien Speicher vorsehen. Das Sprachmodell wird nicht trainiert.'

    $PythonArchiv = Join-Path $Zwischenordner 'python-3.12.10-embed-amd64.zip'
    Hole-Datei 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' 'python-3.12.10-embed-amd64.zip' $PythonArchiv '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3'
    $PythonOrdner = Join-Path $Projektordner 'laufzeit\python'
    Entpacke-Archiv $PythonArchiv $PythonOrdner $false
    # Der eingebettete Interpreter muss die Anwendung zwei Ordner hoeher finden.
    [IO.File]::WriteAllText((Join-Path $PythonOrdner 'python312._pth'), "python312.zip`r`n.`r`n..\..`r`n", [Text.Encoding]::ASCII)

    $LlamaArchiv = Join-Path $Zwischenordner 'llama-b12125-bin-win-cpu-x64.zip'
    Hole-Datei 'https://github.com/ggml-org/llama.cpp/releases/download/b12125/llama-b12125-bin-win-cpu-x64.zip' 'llama-b12125-bin-win-cpu-x64.zip' $LlamaArchiv '968091ccb8c230e0cf7e0eed386310703bebae4a4fd4375f0c57db53958307d8'
    $LlamaOrdner = Join-Path $Projektordner 'laufzeit\llama'
    Entpacke-Archiv $LlamaArchiv $LlamaOrdner $true

    $Modellpfad = Join-Path $Projektordner 'modelle\Qwen3-4B-Q4_K_M.gguf'
    Hole-Datei 'https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/bc640142c66e1fdd12af0bd68f40445458f3869b/Qwen3-4B-Q4_K_M.gguf' 'Qwen3-4B-Q4_K_M.gguf' $Modellpfad '7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5'

    $PythonProgramm = Join-Path $PythonOrdner 'python.exe'
    & $PythonProgramm -B -X utf8 -c 'import sys, ssl, json; assert sys.version_info[:3] == (3, 12, 10)'
    if ($LASTEXITCODE -ne 0) { throw 'Die portable Python-Laufzeit konnte nicht gestartet werden.' }
    Write-Host 'Python-Laufzeit geprueft.'
    if (-not (Test-Path -LiteralPath (Join-Path $LlamaOrdner 'llama-server.exe') -PathType Leaf)) { throw 'Der Modellserver fehlt nach dem Entpacken.' }
    Write-Host ''
    Write-Host 'Einrichtung abgeschlossen. Die Anwendung jetzt mit Starten.cmd oeffnen.'
    Write-Host 'Fuer Uebersetzungen werden weder Internetzugang noch ein Benutzerkonto benoetigt.'
    exit 0
} catch {
    Write-Host ''
    Write-Host ('Einrichtung abgebrochen: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Bitte Ursache beheben und Einrichten.cmd erneut starten. Gepruefte Downloads werden wiederverwendet.'
    exit 1
}
