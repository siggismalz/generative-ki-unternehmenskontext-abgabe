from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

BASIS = Path(__file__).resolve().parent
for name, file in (("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(Path("C:/Windows/Fonts") / file)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")
DATEI = BASIS / "Stolz_Leon_IU14173388_DLBFMPGKIU01_P3_A03.pdf"
c = canvas.Canvas(str(DATEI), pagesize=A4, pageCompression=1)
c.setTitle("Vorführung des Übersetzungsdemonstrators")
c.setAuthor("Leon Stolz")
w, h = A4
x = 2 * cm
line = w - 2*x
y = h - 2*cm

def absatz(txt, size=11, leading=16.5, gap=6, bold=False):
    global y
    style = ParagraphStyle("Text", fontName="Arial-Bold" if bold else "Arial", fontSize=size,
                           leading=leading, textColor=HexColor("#000000"),
                           alignment=TA_LEFT if bold else TA_JUSTIFY,
                           hyphenationLang="de_DE")
    par = Paragraph(txt, style)
    _, height = par.wrap(line, h)
    par.drawOn(c, x, y-height)
    y -= height+gap

absatz("Leon Stolz · IU14173388 · DLBFMPGKIU01 · Phase 3", 11, 16.5, 12)
absatz("Vorführung des Übersetzungsdemonstrators", 16, 20, 12, True)
absatz("Zwei Beispiele aus dem Kundenservice zeigen, welche Angaben der lokale Assistent zuverlässig übernimmt und wann die Person, die den Entwurf prüft, eingreifen muss.", gap=12)
absatz("Demonstrator starten", 14, 18, 6, True)
absatz('Den <link href="https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-abgabe/Finalisierung"><u>Projektstand auf GitHub</u></link> auf einen Windows-x64-Rechner herunterladen. In Finalisierung/Anwendung zuerst Einrichten.cmd und dann Starten.cmd öffnen. Die Ersteinrichtung lädt rund 2,53 GB. Für beide Proben Deutsch nach Englisch und unter „Optionen“ den Prompt „Handel v2“ wählen.', gap=12)
absatz("Eine Rücksendung erklären", 14, 18, 6, True)
absatz("Für Fall N02 „Serviceantwort“ wählen. Im Glossar „Rücksendeetikett = return label“ eintragen und folgenden Text übersetzen lassen.")
absatz("„Das Rücksendeetikett für {{ORDER_ID}} ist ab heute 14 Tage gültig. Bitte legen Sie keinen Kaufbeleg bei.“")
absatz("Der Entwurf übernimmt {{ORDER_ID}}, die Frist von 14 Tagen ab heute und die Bitte, keinen Kaufbeleg beizulegen. Alle drei Angaben lassen sich direkt am Original prüfen.", gap=12)
absatz("Einen Pflegehinweis prüfen", 14, 18, 6, True)
absatz("Für Fall N03 „Produktkurztext“ wählen und im Glossar „Geschirrtuch = tea towel“ eintragen.")
absatz("„Dieses Geschirrtuch besteht aus Baumwolle. Waschen Sie es bei höchstens 40 °C und verwenden Sie keinen Weichspüler.“")
absatz("Material, Höchsttemperatur und Verzicht auf Weichspüler bleiben erhalten. Als Artikelbezeichnung liefert Handel v2 „dish towel“. Vor der Freigabe kann die zuständige Person den vereinbarten Begriff „tea towel“ einsetzen. Der Export erhält auch den Rohtext.", gap=12)
absatz("Grenzen der automatischen Hinweise", 14, 18, 6, True)
absatz("Die Warnfunktion erkannte fünf von sechs gezielten Änderungen. Aus zwei Schalen und fünf Deckeln wurden unbemerkt fünf Schalen und zwei Deckel (Prüffall Z06). Unter vier korrekten Kontrollen löste „1.250 Stück“ zu „1250 units“ einen Fehlalarm aus (K03).")
absatz("Die eigenen Ausgangstexte und die vollständigen Modellausgaben für N02 und N03 stehen im Anhang von P3_A02. Die zehn Kontrollfälle dokumentiert die Datei technik_ergebnis.json im Unterordner Nachweise.", gap=0)
assert y >= 2*cm, y
c.setFont("Arial", 11)
c.drawCentredString(w / 2, cm, "1")
c.showPage()
c.save()

