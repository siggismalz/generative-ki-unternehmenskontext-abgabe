# Den Demonstrator und die Ergebnisse nachvollziehen

A01 fasst Konzept, Entwicklung und Ergebnis zusammen. A02 vergleicht alle Beispielübersetzungen. A03 führt durch zwei Fälle am Demonstrator. Die drei PDFs liegen in diesem Ordner und im Hauptverzeichnis des Repositorys. Der Anforderungsabgleich dokumentiert den Stand der 22 Kriterien aus dem Konzept. [Projektstand zur Abgabe](https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-abgabe)

## Unter Windows starten

Die GitHub-Seite des Projektstands öffnen und über **Code → Download ZIP** eine lokale Kopie herunterladen und entpacken. Alternativ mit Git den angegebenen Stand klonen:

```bat
git clone --branch phase3-abgabe --depth 1 https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe.git
```

Im lokalen Projektordner `Finalisierung/Anwendung/Einrichten.cmd` öffnen. Die Ersteinrichtung für Windows x64 lädt rund 2,53 GB und prüft die SHA-256-Werte von Python, llama.cpp und Qwen3-4B. Etwa 6 GB freien Speicher vorsehen. Anschließend im selben Ordner `Starten.cmd` öffnen. Der Browser erreicht die lokale Oberfläche unter http://127.0.0.1:8767. Zum Beenden die Schaltfläche in der Oberfläche nutzen. Eine detaillierte Bedienungsanleitung und die Original-Lizenzen liegen im [Anwendungsordner](Anwendung/).

## Versuche wiederholen

Im Windows-Explorer den lokalen Ordner `Finalisierung` öffnen, in die Adressleiste `cmd` eingeben und mit der Eingabetaste bestätigen. Nach der Einrichtung können folgende Befehle ausgeführt werden. Für jeden Durchgang einen neuen Ergebnisnamen wählen.

```bat
Anwendung\laufzeit\python\python.exe -B -X utf8 Fallstudie\laeufe.py Anwendung Wiederholung
Anwendung\laufzeit\python\python.exe -B -X utf8 Nachweise\technik_pruefen.py Anwendung Wiederholung_Technik.json
```

Das erste Skript verarbeitet beide Prompts in derselben festgelegten Fallreihenfolge. Eingaben, Arbeitsreferenzen und Sollinhalt stehen in [Faelle_vorab.json](Fallstudie/Faelle_vorab.json), die 48 Modellantworten in [Rohdaten.json](Fallstudie/Rohdaten.json). Der verwendete Modell- und Programmstand ist über [Provenienz.json](Fallstudie/Provenienz.json) nachvollziehbar. Die [fallweisen Vorbewertungen](Fallstudie/Vorbewertung.json) sind KI-gestützt. Das zweite Skript prüft Softwarefunktionen und kontrolliert unter anderem die Erkennung geänderter Beträge, Mengen und Kennungen.

[Der Einrichtungsnachweis](Nachweise/isolierter_aufbau.json) dokumentiert den Test mit lokalen, hashgeprüften Originaldateien. Die PDF-Dokumente aus Phase 1 und 2 stehen in der [Dokumentation](Dokumentation/). Der [Bewertungsbogen](Sprachpruefung/Sprachpruefung.html) ist eine lokale HTML-Datei. Zum Ausfüllen die heruntergeladene Datei mit dem Browser öffnen. Eine später veröffentlichte persönliche Sprachbewertung ist im aktuellen [Ordner Sprachpruefung auf main](https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/main/Finalisierung/Sprachpruefung) zu finden.
