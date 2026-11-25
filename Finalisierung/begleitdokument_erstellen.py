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
absatz("Übersetzung für den Kundenservice ausprobieren", 16, 20, 12, True)
absatz("1. Programm öffnen", 14, 18, 6, True)
absatz('Entpacken Sie die Abgabe-ZIP auf einem Windows-Rechner (64 Bit). Öffnen Sie im Projekt den Ordner „Finalisierung/Anwendung“. Starten Sie zuerst Einrichten.cmd und danach Starten.cmd. Die Einrichtung lädt einmalig rund 2,53 GB. Dieselben Dateien finden Sie auf <link href="https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-final/Finalisierung"><u>GitHub</u></link>.', gap=12)
absatz("2. Ein Rücksendeetikett erklären", 14, 18, 6, True)
absatz('Wählen Sie Deutsch nach Englisch und „Serviceantwort“. Wählen Sie unter „Optionen“ die Variante „Handel v2“ und tragen Sie „Rücksendeetikett = return label“ ins Glossar ein. Übersetzen Sie diesen Text (N02).')
absatz("„Das Rücksendeetikett für {{ORDER_ID}} ist ab heute 14 Tage gültig. Bitte legen Sie keinen Kaufbeleg bei.“")
absatz("Vergleichen Sie die Übersetzung mit dem Original. Im Test blieben {{ORDER_ID}}, die Frist von 14 Tagen ab heute und die Bitte, keinen Kaufbeleg beizulegen, erhalten.", gap=12)
absatz("3. Einen Artikelnamen korrigieren", 14, 18, 6, True)
absatz('Wechseln Sie zu „Produktkurztext“. Ersetzen Sie den Glossareintrag durch „Geschirrtuch = tea towel“ und übersetzen Sie den zweiten Text (N03).')
absatz("„Dieses Geschirrtuch besteht aus Baumwolle. Waschen Sie es bei höchstens 40 °C und verwenden Sie keinen Weichspüler.“")
absatz("Der getestete Entwurf lautete an der entscheidenden Stelle „dish towel“. Ersetzen Sie den Begriff durch „tea towel“. Prüfen Sie auch Material, Temperatur und Pflegehinweis. Geben Sie erst dann den Entwurf frei. Im Export können Sie beide Fassungen vergleichen.", gap=12)
absatz("Worauf es bei der Freigabe ankommt", 14, 18, 6, True)
absatz("Kontrollieren Sie auch Texte ohne Warnhinweis. Beim Test Z06 wurden aus zwei Schalen und fünf Deckeln fünf Schalen und zwei Deckel. Die Anwendung erkannte den Tausch nicht. Die vollständigen Beispielübersetzungen stehen im Anhang der Beispielsammlung P3_A02.", gap=0)

assert y >= 2*cm, y
c.setFont("Arial", 11)
c.drawCentredString(w / 2, cm, "1")
c.showPage()
c.save()

