# KI-gestützte Textübersetzung für einen kleinen Onlinehändler

Dieses Repository enthält die drei PDFs zur Finalisierung und das Material, mit dem die 48 Übersetzungen erzeugt und verglichen wurden. Der [Abgabestand](https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-abgabe) ist über den Tag `phase3-abgabe` festgehalten.

| Dokument | Inhalt |
|---|---|
| [Abstract](Stolz_Leon_IU14173388_DLBFMPGKIU01_P3_A01.pdf) | Konzept, technische Umsetzung und wichtigste Ergebnisse |
| [Beispielübersetzungen und Diskussion](Stolz_Leon_IU14173388_DLBFMPGKIU01_P3_A02.pdf) | 16 Normalfälle und acht Grenzfälle, jeweils mit beiden Promptvarianten |
| [Vorführanleitung](Stolz_Leon_IU14173388_DLBFMPGKIU01_P3_A03.pdf) | Zwei Beispiele zum Ausprobieren im Kundenservice |

## Demonstrator starten

Unter Windows x64 den Abgabestand mit `git clone --branch phase3-abgabe https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe.git` herunterladen. Im Ordner [Finalisierung/Anwendung](Finalisierung/Anwendung) zuerst `Einrichten.cmd`, danach `Starten.cmd` öffnen. Die Ersteinrichtung lädt rund 2,53 GB Modell und Laufzeitkomponenten aus den festgelegten Originalquellen und prüft die SHA-256-Werte. Anschließend öffnet sich die lokale Bedienoberfläche. Die [Anleitung zur Wiederholung der Versuche](Finalisierung/Anleitung.md) enthält die genauen Befehle.

## Ergebnisse nachvollziehen

- [Fallplan, Rohübersetzungen und Vorbewertung](Finalisierung/Fallstudie) – zu jeder Fall-ID sind Eingabe, beide Modelltexte und die Beurteilung nachvollziehbar.
- [Technische Prüfungen](Finalisierung/Nachweise) und [Abgleich der 22 Anforderungen](Finalisierung/Anforderungsabgleich.pdf).
- [Bogen für die persönliche Sprachprüfung](Finalisierung/Sprachpruefung/Sprachpruefung.html) – die HTML-Datei herunterladen und lokal im Browser öffnen.
- [Konzeption](Konzeption) und [Erarbeitung](Erarbeitung) enthalten die Ergebnisse der ersten beiden Meilensteine. [Konzeption_final](Konzeption_final) und [Erarbeitung_final](Erarbeitung_final) ergänzen sie um die Ergebnisse der abschließenden Prüfung.
