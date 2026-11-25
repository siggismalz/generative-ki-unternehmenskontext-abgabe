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

def absatz(txt, size=11, leading=16.5, gap=6, bold=False, eingabe=False):
    global y
    style = ParagraphStyle("Text", fontName="Arial-Bold" if bold else "Arial", fontSize=size,
                           leading=leading, textColor=HexColor("#000000"),
                           alignment=TA_LEFT if bold or eingabe else TA_JUSTIFY,
                           hyphenationLang=None if eingabe else "de_DE", leftIndent=12 if eingabe else 0)
    par = Paragraph(txt, style)
    _, height = par.wrap(line, h)
    par.drawOn(c, x, y-height)
    y -= height+gap

absatz("Leon Stolz · DLBFMPGKIU01 · Phase 3", 10, 15, 9)
absatz("Zwei Übersetzungen zum Ausprobieren", 16, 20, 10, True)
absatz('Die Projekt-ZIP vollständig entpacken. Unter Windows (64 Bit) im Ordner „Finalisierung/Anwendung“ einmal Einrichten.cmd und danach Starten.cmd öffnen. Die Einrichtung lädt rund 2,53 GB. Die Dateien stehen auch im <link href="https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-projektstand/Finalisierung"><u>Projektordner auf GitHub</u></link>.', gap=10)

absatz("Rücksendung · Stimmt die Frist?", 12, 17, 4, True)
absatz("Deutsch → Englisch und „Serviceantwort“ einstellen. Unter „Optionen“ den Prompt „Handel v2“ wählen und ins Glossar die Zeile „Rücksendeetikett = return label“ eintragen. Diesen Text in das Eingabefeld kopieren:", gap=4)
absatz("Das Rücksendeetikett für {{ORDER_ID}} ist ab heute 14 Tage gültig. Bitte legen Sie keinen Kaufbeleg bei.", gap=6, eingabe=True)
absatz("Im Test (N02) stand im ersten Satz „valid for 14 days starting today“. Der zweite begann mit „Please do not include“. Das kleine Wort „not“ ist hier ebenso wichtig wie die Zahl 14. Vor der Freigabe auch den Platzhalter {{ORDER_ID}} im Entwurf prüfen.", gap=12)

absatz("Geschirrtuch · Passt der Name zum Sortiment?", 12, 17, 4, True)
absatz("Die Sprachrichtung beibehalten, als Textsorte „Produktkurztext“ wählen und den Glossareintrag durch „Geschirrtuch = tea towel“ ersetzen. Dann folgenden Pflegehinweis übersetzen:", gap=4)
absatz("Dieses Geschirrtuch besteht aus Baumwolle. Waschen Sie es bei höchstens 40 °C und verwenden Sie keinen Weichspüler.", gap=6, eingabe=True)
absatz("In N03 schrieb das Modell „dish towel“. Der Pflegehinweis ist verständlich, aber auf der Produktseite heißt der Artikel „tea towel“. Falls dieser Unterschied im Entwurf erscheint, den Artikelnamen im Feld „Übersetzung“ ändern. Material, Höchsttemperatur und Pflegehinweis am Original prüfen. Erst danach „Sprache und Inhalt geprüft“ und „Freigeben“ wählen.", gap=10)
absatz("Über „JSON exportieren“ lassen sich der ursprüngliche Entwurf und die Korrektur als getrennte Felder speichern. Die beiden aufgezeichneten Testläufe stehen in der Beispielsammlung unter N02 und N03.", gap=0)

assert y >= 2*cm, y
c.setFont("Arial", 11)
c.drawCentredString(w / 2, cm, "1")
c.showPage()
c.save()

