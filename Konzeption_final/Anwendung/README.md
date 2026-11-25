# Lokaler Übersetzungsdemonstrator

Ein kleiner Übersetzungsassistent für synthetische Kundenanfragen, Serviceantworten und Produktkurztexte zwischen Deutsch und Englisch. Er verwendet Qwen3-4B mit llama.cpp auf der CPU. Die Oberfläche läuft lokal im Browser.

## Einrichten und starten

1. Den [festgelegten Stand vom 13.11.2026](https://github.com/siggismalz/ki-uebersetzungsdemonstrator/tree/phase2-2026-11-13) über **Code → Download ZIP** herunterladen und vollständig entpacken.
2. **Einrichten.cmd** öffnen. Die Ersteinrichtung benötigt Internetzugang und lädt etwa 2,53 GB von Hugging Face, GitHub und python.org. Alle Downloads werden anhand festgelegter SHA256-Werte geprüft. Python und llama.cpp werden ausschließlich in diesem Ordner eingerichtet; Administratorrechte sind nicht nötig.
3. **Starten.cmd** öffnen. Die Oberfläche erscheint unter **http://127.0.0.1:8767**. Ein Benutzerkonto oder Passwort ist nicht erforderlich.
4. Über **Beenden** in der Oberfläche oder **Strg+C** im gestarteten Konsolenfenster beenden. Das Schließen des Browser-Tabs allein beendet die Anwendung nicht.

Nach der Einrichtung benötigt die Übersetzung keinen Internetzugang. Modell und Laufzeiten liegen unter `modelle/` und `laufzeit/`. Der Modellserver verwendet ausschließlich `127.0.0.1:8768`.

Benötigt wird Windows x64 mit einer geeigneten CPU und genügend freiem Speicher. Geprüft wurde Windows 11 mit Intel Core i7-13700 und rund 64 GiB RAM. Ein fremder Rechner mit 16 GiB wurde nicht geprüft. Für Downloads und entpackte Dateien sollten mindestens 6 GB freier Festplattenspeicher verfügbar sein.

## Bedienung

Sprachrichtung und Textsorte wählen, einen synthetischen Text mit höchstens 2.000 Zeichen eingeben und die Übersetzung starten. Optional sind bis zu 20 Glossareinträge möglich. Ein geladenes Beispiel startet noch keine Verarbeitung.

Original, Rohübersetzung und bearbeitbare Korrektur bleiben getrennt. Ergebnisse beginnen als Entwurf. Eine Freigabe erfordert die bewusste Prüfbestätigung; Änderungen widerrufen sie. JSON-Dateien werden nur durch einen bewussten Export gespeichert.

Übersetzungen können sprachlich oder inhaltlich falsch sein. Zahlenhinweise und Glossar ersetzen keine menschliche Prüfung. Die fachliche Qualitätsbewertung ist noch offen. Der Demonstrator ist für synthetische Beispiele vorgesehen; eine produktive Shop- oder E-Mail-Anbindung ist nicht enthalten.

## Programmteile

- `app.py`: lokale HTTP-Anwendung, Sitzung und Lebenszyklus des Modellservers.
- `uebersetzer.py`: Eingabeprüfung, Modellaufruf, Hinweise und Freigabestatus.
- `oberflaeche/`: HTML, CSS und JavaScript ohne externe Browserressourcen.
- `konfiguration.json` und `prompts.json`: Parameter und zwei Promptvarianten.
- `komponenten.json`: feste Versionen, Originalquellen, Größen und SHA256-Werte.
- `Einrichten.ps1`: lokale Ersteinrichtung der drei benötigten Komponenten.

Die Anwendung nutzt nur die Python-Standardbibliothek. Inhalte werden nicht in eine Cloud übertragen. Exporte sowie mögliche Betriebssystem- und Browserreste werden nicht automatisch gelöscht.

## Komponenten und Lizenzhinweise

| Komponente | Festgelegter Stand | Lizenz |
|---|---|---|
| Qwen3-4B Q4_K_M | Revision `bc640142c66e1fdd12af0bd68f40445458f3869b` | Apache 2.0 |
| llama.cpp CPU x64 | `b12125`, Commit `7d516e25ead4653169236b3f90d13f7bd8629724` | MIT und Hinweise zu Drittkomponenten |
| Python | 3.12.10, Windows x64 embeddable | PSF und Hinweise zu Drittkomponenten |

Die Originalhinweise für diese Drittkomponenten stehen unter `lizenzen/` und in den heruntergeladenen Laufzeiten. Sie beziehen sich auf die jeweiligen Drittkomponenten und sind keine pauschale Lizenz für den eigenen Anwendungscode.

Das Repository enthält Quellcode und Einrichtung, aber keine Modellgewichte, Laufzeit-Binärdateien, Prüfungsunterlagen oder PDF-Generatoren. Der veröffentlichte Versionsstand ist über den oben verlinkten Tag festgelegt.
