# Den Übersetzer ausprobieren

1. Das Abgabe-ZIP `P3_A04.zip` vollständig entpacken. Im Hauptordner `Finalisierung/Anwendung` öffnen.
2. Unter Windows x64 einmal `Einrichten.cmd` starten. Das Skript lädt Modell und Laufzeiten (rund 2,53 GB) und prüft ihre Prüfsummen. Dafür rund 6 GB freien Speicher einplanen.
3. `Starten.cmd` öffnen. Die zwei Texte aus P3_A03 eingeben und die Ergebnisse mit dem Original vergleichen. Über **Beenden** die Anwendung schließen.

Die gleichen Dateien sind [auf GitHub](https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-final/Finalisierung) einzeln zugänglich.

## Ergebnisse nachlesen

Im [Fallplan](Fallstudie/Faelle_vorab.json) stehen die 24 Texte und die vorab festgelegten Kriterien. Die [Rohdaten](Fallstudie/Rohdaten.json) enthalten die 48 unbearbeiteten Antworten. Die [Vorbewertung](Fallstudie/Vorbewertung.json) erläutert die Einstufungen. Der [Bewertungsbogen](Sprachpruefung/Sprachpruefung.html) dient der persönlichen Sprachprüfung.

## Versuche wiederholen

Nach der Einrichtung in der Adressleiste des entpackten Ordners `Finalisierung` den Befehl `cmd` eingeben. Für einen neuen Durchgang folgende Befehle ausführen. Bei weiteren Durchgängen neue Ergebnisnamen wählen.

```bat
Anwendung\laufzeit\python\python.exe -B -X utf8 Fallstudie\laeufe.py Anwendung Wiederholung
Anwendung\laufzeit\python\python.exe -B -X utf8 Nachweise\technik_pruefen.py Anwendung Wiederholung_Technik.json
```

Die erste Zeile wiederholt die Übersetzungen, die zweite die technischen Prüfungen. Den Vergleich mit den ursprünglichen Anforderungen enthält der [Anforderungsabgleich](Anforderungsabgleich.pdf).
