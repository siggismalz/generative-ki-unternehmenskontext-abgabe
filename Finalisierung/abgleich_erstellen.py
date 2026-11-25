"""Erzeugt die lesbare Fassung aus dem maschinenlesbaren Anforderungsabgleich."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

basis = Path(__file__).resolve().parent
daten = json.loads((basis / "Nachweise/Anforderungsabgleich.json").read_text(encoding="utf-8-sig"))
out = basis / "Nachweise/Anforderungsabgleich.pdf"
for name, file in (("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / file)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")
w, h = A4
x = 2 * cm
breite = w - 2*x
c = canvas.Canvas(str(out), pagesize=A4, pageCompression=1)
c.setTitle("Abgleich der 22 Anforderungen an den Übersetzungsdemonstrator")
c.setAuthor("Leon Stolz")

def absatz(text, y, size, leading, font="Arial", farbe="#202020"):
    stil = ParagraphStyle("absatz", fontName=font, fontSize=size, leading=leading, textColor=HexColor(farbe))
    p = Paragraph(escape(text), stil)
    _, ph = p.wrap(breite, h)
    p.drawOn(c, x, y-ph)
    return y-ph

def titel(t, seite, untertitel):
    y = absatz("Leon Stolz  ·  IU14173388  ·  DLBFMPGKIU01  ·  Finalisierung", h-2*cm, 9, 12)
    y = absatz(t, y-13, 16, 20, "Arial-Bold")
    y = absatz(untertitel, y-6, 10.5, 14.5)
    c.setFont("Arial", 9)
    c.drawCentredString(w/2, 1.25*cm, str(seite))
    return y-10

def zeile(f, y):
    c.setStrokeColor(HexColor("#C0C5C8"))
    c.line(x, y, w-x, y)
    y = absatz(f["id"]+"   "+f["anforderung"], y-6, 11, 14, "Arial-Bold")
    y = absatz(f["prioritaet"]+"  ·  "+f["status"], y-1, 9.5, 12, "Arial-Bold", "#344C5B")
    y = absatz(f["befund"], y-3, 10, 13)
    y = absatz(f["nachweise"], y-2, 8.6, 11, farbe="#48535B")
    return y-9

seiten = [
    (0, 6, "Funktionsanforderungen", "Abgleich mit dem Katalog aus Phase 1, S. 5–8, am Stand vom 25. November 2026. Beurteilt wird der lokale Demonstrator für synthetische deutsch- und englischsprachige Handelstexte."),
    (6, 12, "Betriebliche Anforderungen", "Die Nachweise gelten für den eingerichteten Einzelplatz. Beobachtungen am Entwicklungsrechner und offene Prüfungen sind jeweils angegeben."),
    (12, 17, "Erweiterungen im Vergleichstest", "Die folgenden Ergebnisse beziehen sich auf die vorab festgelegten Texte. Für die Vorführung ist Handel v2 eingestellt."),
    (17, 22, "Optionale und ausgeschlossene Funktionen", "Phase 1 legt den Umfang fest. Französisch und die Verarbeitung mehrerer Texte bleiben mögliche Erweiterungen."),
]
for seite,(lo,hi,t,sub) in enumerate(seiten,1):
    y=titel(t,seite,sub)
    for f in daten["anforderungen"][lo:hi]:
        y=zeile(f,y)
    if seite == 4:
        y = absatz("Quellen der Anforderungsprüfung", y-9, 11, 14, "Arial-Bold")
        y = absatz("Die Kürzel in den Nachweiszeilen bezeichnen die Prüfungsdokumente von Leon Stolz für den Kurs DLBFMPGKIU01. Seitenangaben für Phase 1 und Phase 2 beziehen sich auf die gedruckten Seitenzahlen.", y-4, 10, 13)
        y = absatz("P1_A01 (15.10.2026) · KI-gestützte Textübersetzung für einen kleinen Onlinehändler. Konzeptvorstellung und priorisierter Anforderungskatalog.", y-4, 10, 13)
        y = absatz("P2_A02 (13.11.2026) · KI-gestützte Textübersetzung für einen kleinen Onlinehändler. Modellvergleich, Softwaredesign und Implementierung.", y-4, 10, 13)
        y = absatz("P3_A02 (25.11.2026) · Übersetzungsqualität im Kundenservice und im Produktkatalog. Die Fallnummern führen zu den dort abgedruckten Originalen und Rohübersetzungen.", y-4, 10, 13)
    assert y>=1.7*cm, (seite,y)
    c.showPage()
c.save()

