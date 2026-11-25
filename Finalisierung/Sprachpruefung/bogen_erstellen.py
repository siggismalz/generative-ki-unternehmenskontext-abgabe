"""Baut einen lokalen Bewertungsbogen mit den 16 unveränderten Rohübersetzungen."""
from html import escape
import json
from pathlib import Path

folder = Path(__file__).resolve().parent
studie = folder.parent / "Fallstudie"
def read(name):
    return json.loads((studie / name).read_text(encoding="utf-8"))

cases = [f for f in read("Faelle_vorab.json")["faelle"] if f["id"].startswith("N")]
outputs = {r["fall_id"]: r for r in read("Rohdaten.json") if r["prompt"] == "handel-v2"}
assert len(cases) == 16
def select(label, choices):
    options = '<option value="">Offen</option>' + ''.join(f'<option value="{v}">{v}</option>' for v in choices)
    return f'<label>{label}<select>{options}</select></label>'
sections = []
for case in cases:
    result = outputs[case["id"]]
    assert result["text"] == case["text"] and result["status"] == "Entwurf"
    fields = [("Ausgangstext",case["text"]), ("Rohübersetzung",result["rohuebersetzung"]), ("Erwarteter Inhalt",case["soll"]), ("Mögliche Übersetzung aus dem Fallplan",case["referenz"])]
    if case["glossar"]:
        fields += [("Vorgegebenes Glossar",", ".join(f'{g["quelle"]} → {g["ziel"]}' for g in case["glossar"]))]
    texts = ''.join(f'<dt>{label}</dt><dd>{escape(value)}</dd>' for label,value in fields)
    scores = ''.join(select(label,[0,1,2]) for label in ("Bedeutung","Vollständigkeit","Sachliche Details","Verständlichkeit"))
    scores += select("Kritischer Fehler",["nein","ja"])
    sections.append(f'<article id="{case["id"]}"><div class="tag">{case["id"]} · {case["richtung"]} · {case["textsorte"]}</div><h2>{escape(case["titel"])}</h2><dl>{texts}</dl><div class="scores">{scores}</div><label class="note">Begründung und ggf. Korrektur<textarea rows="2"></textarea><span class="printnote"></span></label><p class="verdict"></p></article>')
template = (folder / "formular.vorlage").read_text(encoding="utf-8")
(folder / "Sprachpruefung.html").write_text(template.replace("@@CASES@@","\n".join(sections)),encoding="utf-8")

