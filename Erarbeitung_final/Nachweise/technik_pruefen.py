"""Technische Wiederholungsprüfung der lokalen Übersetzungsanwendung.

Aufruf mit dem beiliegenden Python: python.exe -B -X utf8 technik_pruefen.py
    <Ordner mit app.py> <Pfad für das neue Ergebnis-JSON>
Eine bestehende Ergebnisdatei wird nicht überschrieben.
"""

import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest


# Vier Klassen von Warnungen: Betrag und Menge (Zahl), ID und Platzhalter.
# Z06 prüft außerdem, ob das Programm die Zuordnung von Zahlen beachtet.
# K01–K04 sind sinngemäß korrekte Übersetzungen mit zulässiger Schreibweise.
FAELLE = [
    ("Z01", "Falscher Preis", "Der Topf kostet 19,90 EUR.",
     "The pot costs EUR 29.90.", True),
    ("Z02", "Falsche Menge", "Der Satz enthält 4 Haken.",
     "The set contains 3 hooks.", True),
    ("Z03", "Fehlende zweite Mengenangabe", "Sie erhalten 2 Schalen und 2 Deckel.",
     "You will receive 2 bowls and lids.", True),
    ("Z04", "Anderes Produkt", "Das Ersatzteil passt zu AB-42.",
     "The spare part fits AC-42.", True),
    ("Z05", "Anderer Platzhalter", "Ihre Referenz lautet {{ORDER_ID}}.",
     "Your reference is {{ITEM_ID}}.", True),
    ("Z06", "Vertauschte Mengen", "Wir liefern 2 Schalen und 5 Deckel.",
     "We will deliver 5 bowls and 2 lids.", True),
    ("K01", "Dezimaltrennzeichen und Währung", "Der Topf kostet 19,90 EUR.",
     "The pot costs EUR 19.90.", False),
    ("K02", "Tausender- und Dezimaltrennzeichen", "Die Lieferung kostet 1.249,50 EUR.",
     "The shipment costs EUR 1,249.50.", False),
    ("K03", "Tausendertrennzeichen entfällt", "Wir liefern 1.250 Stück.",
     "We will deliver 1250 units.", False),
    ("K04", "Kennung und Platzhalter bleiben erhalten", "Liefern Sie AB-42 an {{ADDRESS}}.",
     "Please deliver AB-42 to {{ADDRESS}}.", False),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("demonstrator", type=Path)
    parser.add_argument("ergebnis", type=Path)
    args = parser.parse_args()
    root = args.demonstrator.resolve(strict=True)
    sys.path[:0] = [str(root), str(Path(__file__).resolve().parent)]
    import tests_technik
    import uebersetzer

    assert Path(uebersetzer.__file__).parent == root
    tests = unittest.defaultTestLoader.loadTestsFromModule(tests_technik)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(tests)
    faelle = []
    for nummer, zweck, original, uebersetzung, fehler in FAELLE:
        hinweise = uebersetzer.auffaelligkeiten(original, uebersetzung)
        faelle.append({
            "id": nummer, "zweck": zweck, "original": original,
            "kontrollierte_uebersetzung": uebersetzung,
            "warnung_erwartet": fehler, "angezeigte_hinweise": hinweise,
            "entspricht_erwartung": bool(hinweise) == fehler,
        })
    daten = {
        "zeitpunkt_utc": datetime.now(timezone.utc).isoformat(),
        "anwendungsversion": json.loads((root / "konfiguration.json").read_text())["version"],
        "quellstand_sha256": {
            f: hashlib.sha256((root / f).read_bytes()).hexdigest()
            for f in ("app.py", "uebersetzer.py", "konfiguration.json", "prompts.json")
        },
        "tests_technik_sha256": hashlib.sha256(Path(tests_technik.__file__).read_bytes()).hexdigest(),
        "python": sys.version, "unittests": result.testsRun,
        "unittests_ok": result.wasSuccessful(), "protokoll": log.getvalue().splitlines(),
        "a16_methode": "Unveränderte Funktion auffaelligkeiten; kontrolliert formulierte Testausgaben, ohne Modellaufruf.",
        "a16_faelle": faelle,
        "a16_erkannt_von_sechs": sum(bool(f["angezeigte_hinweise"]) for f in faelle if f["warnung_erwartet"]),
        "a16_fehlalarme_von_vier": sum(bool(f["angezeigte_hinweise"]) for f in faelle if not f["warnung_erwartet"]),
    }
    with args.ergebnis.open("x", encoding="utf-8") as datei:
        json.dump(daten, datei, indent=2, ensure_ascii=False)
        datei.write("\n")
    print(f"{result.testsRun} technische Tests, bestanden: {result.wasSuccessful()}")
    print(f"A16: {daten['a16_erkannt_von_sechs']}/6 erkannt; {daten['a16_fehlalarme_von_vier']}/4 Fehlalarme")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

