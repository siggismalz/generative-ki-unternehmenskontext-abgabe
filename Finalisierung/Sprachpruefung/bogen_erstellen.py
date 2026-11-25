"""Setzt das Arbeitsblatt aus den festgelegten Fällen und den Originalausgaben."""
from html import escape
import json
from pathlib import Path


ordner = Path(__file__).resolve().parent
fallstudie = ordner.parent / "Fallstudie"


def lesen(name):
    return json.loads((fallstudie / name).read_text(encoding="utf-8"))


def auswahl(titel, werte):
    optionen = ['<option value="">Offen</option>']
    optionen.extend(f'<option value="{wert}">{wert}</option>' for wert in werte)
    return f'<label>{titel}<select>{"".join(optionen)}</select></label>'


def fallblatt(fall, ausgabe):
    if ausgabe["text"] != fall["text"] or ausgabe["status"] != "Entwurf":
        raise ValueError(f'Unpassende Rohübersetzung für {fall["id"]}')
    quelle, ziel = fall["richtung"].split("-")
    sprache = {"EN": "Englisch", "DE": "Deutsch"}
    begriffe = ", ".join(f'{wort["quelle"]} → {wort["ziel"]}' for wort in fall["glossar"])
    glossar = f'<p><b>Glossar</b> {escape(begriffe)}</p>' if begriffe else ""
    fragen = [
        auswahl(kriterium, (0, 1, 2))
        for kriterium in ("Bedeutung", "Vollständigkeit", "Sachliche Details", "Verständlichkeit")
    ]
    fragen.append(auswahl("Kritischer Fehler", ("nein", "ja")))
    return f"""
<article id="{fall["id"]}">
  <h2>{fall["id"]} · {escape(fall["titel"])}</h2>
  <p class="textsorte">{escape(fall["textsorte"])}</p>
  <div class="vergleich">
    <div><h3>Original · {sprache[quelle]}</h3><p lang="{quelle.lower()}">{escape(fall["text"])}</p></div>
    <div><h3>Handel v2 · {sprache[ziel]}</h3><p lang="{ziel.lower()}">{escape(ausgabe["rohuebersetzung"])}</p></div>
  </div>
  <details>
    <summary>Vergleich mit dem Fallplan</summary>
    <p><b>Erwarteter Inhalt</b> {escape(fall["soll"])}</p>
    <p><b>Mögliche Übersetzung</b> <span lang="{ziel.lower()}">{escape(fall["referenz"])}</span></p>
    {glossar}
  </details>
  <div class="punkte">{"".join(fragen)}</div>
  <label class="notiz">Begründung oder Korrektur
    <textarea rows="2"></textarea><span class="drucknotiz"></span>
  </label>
  <p class="urteil"></p>
</article>"""


faelle = [f for f in lesen("Faelle_vorab.json")["faelle"] if f["id"].startswith("N")]
ausgaben = {r["fall_id"]: r for r in lesen("Rohdaten.json") if r["prompt"] == "handel-v2"}
if [f["id"] for f in faelle] != [f"N{i:02d}" for i in range(1, 17)]:
    raise ValueError("Erwartet werden die 16 Normalfälle aus dem Fallplan.")
blaetter = [fallblatt(fall, ausgaben[fall["id"]]) for fall in faelle]
vorlage = (ordner / "formular.vorlage").read_text(encoding="utf-8")
(ordner / "Sprachpruefung.html").write_text(vorlage.replace("@@FAELLE@@", "\n".join(blaetter)), encoding="utf-8")

