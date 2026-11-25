"""Setzt das Fallportfolio aus Messdaten, Arbeitsreferenzen und Vorbewertungen."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

here=Path(__file__).resolve().parent
def read(n):return json.loads((here/n).read_text(encoding="utf-8-sig"))
cases=read("Faelle_vorab.json")["faelle"]
results={(r["fall_id"],r["prompt"]):r for r in read("Rohdaten.json")}
assess=read("Vorbewertung.json")
W,H=A4
X=2*cm
WD=W-X*2
for reg,file in (("Arial","arial.ttf"),("ArialB","arialbd.ttf"),("ArialI","ariali.ttf")):
    pdfmetrics.registerFont(TTFont(reg,str(Path("C:/Windows/Fonts")/file)))
c=Canvas(str(here/"Fallstudie_Promptvergleich.pdf"),pagesize=A4)
c.setAuthor("Leon Stolz")
c.setTitle("Übersetzungsqualität im Kundenservice und im Produktkatalog")
pdfmetrics.registerFontFamily("Arial",normal="Arial",bold="ArialB",italic="ArialI")
def para(value,x,y,width=WD,size=11,leading=16.5,face="Arial",align=TA_LEFT,*,rich=False,indent=0,hyphenate=False):
    p=Paragraph(value if rich else escape(value).replace("\n","<br/>"), ParagraphStyle("t",fontName=face,fontSize=size,leading=leading,textColor=colors.black,alignment=align,firstLineIndent=-indent,leftIndent=indent,hyphenationLang="de_DE" if hyphenate else "",splitLongWords=1))
    _,height=p.wrap(width,1000);p.drawOn(c,x,y-height)
    return y-height

def rule(y,x=X,width=WD):
    c.setStrokeColor(colors.HexColor("#B4C6C5"));c.setLineWidth(0.55);c.line(x,y,x+width,y)

def page(section=None):
    global y
    y=H-X
    if section:
        y=para(section,X,y,WD,10,15,"ArialB")-8
    c.setFillColor(colors.black);c.setFont("Arial",10)
    c.drawCentredString(W/2,1*cm,str(c.getPageNumber()-2))

def h(t):
    global y
    y=para(t,X,y,WD,16,21,"ArialB")-12

def sub(t):
    global y
    y=para(t,X,y-6,WD,14,18,"ArialB")-6

def body(t):
    global y
    y=para(t,X,y,align=TA_JUSTIFY,hyphenate=True)-6

def row(label,val,small=False):
    global y
    width=92
    a=para(label,X,y,width-6,9 if small else 9.5,12,"ArialB")
    b=para(val,X+width,y,WD-width,10.25 if small else 11,13.5 if small else 15)
    y=min(a,b)-5

def end():
    assert y>X-7, (c.getPageNumber(),y)
    c.showPage()

# Das Titelblatt zählt als I ohne aufgedruckte Seitenzahl.
y=H-3*cm
for value,size,leading,font,gap in [
    ("IU Internationale Hochschule",14,21,"ArialB",8),
    ("Informatik, Bachelor of Science",11,16.5,"Arial",36),
    ("Portfolio · Phase 3",14,21,"ArialB",6),
    ("Projekt: Generative KI im Unternehmenskontext",11,16.5,"Arial",3),
    ("DLBFMPGKIU01",11,16.5,"Arial",64),
    ("Übersetzungsqualität im Kundenservice und im Produktkatalog",16,24,"ArialB",9),
    ("Beispielübersetzungen und Diskussion",14,21,"Arial",64),
    ("Leon Stolz",11,16.5,"Arial",2),
    ("Matrikelnummer IU14173388",11,16.5,"Arial",18),
    ("Betreuende Person: Oliver Dorn",11,16.5,"Arial",2),
    ("Stand der Abgabefassung: 25. November 2026",11,16.5,"Arial",0),
]:
    y=para(value,X,y,WD,size,leading,font,TA_CENTER)-gap
c.showPage()

# Mehrere kurze Fälle teilen sich eine Seite. Die Reihenfolge entspricht dem Laufprotokoll.
gruppen = [
    ["N01", "N02", "N03"], ["N04", "N05", "N06"], ["N07", "N08", "N09"],
    ["N10", "N11"], ["N12", "N13"], ["N14", "N15", "N16"],
    ["G01", "G02"], ["G03", "G04"], ["G05", "G06"], ["G07", "G08"],
]
fallseite = {kennung: 5 + n for n, gruppe in enumerate(gruppen) for kennung in gruppe}
chapters = [
    ("1 Aufbau des Übersetzungstests", 1),
    ("2 Erfahrungen mit den Shoptexten", 2),
    ("Literaturverzeichnis", 3),
    ("Anhangsverzeichnis und Punktübersicht", 4),
    ("Anhang A  Normalfälle", fallseite["N01"]),
    ("Anhang B  Grenzfälle", fallseite["G01"]),
]
y=H-X
h("Inhaltsverzeichnis")
for title, number in chapters:
    c.setFont("Arial",11)
    c.drawString(X,y-11,title)
    c.drawRightString(W-X,y-11,str(number))
    y-=23
c.drawCentredString(W/2,cm,"II")
c.showPage()

page();h(chapters[0][0])
body("Eine Kundin möchte nur die Rechnungsadresse ändern. Die Lieferadresse soll so bleiben, wie sie ist. In der deutschen Ausgabe steht später „den Rechnungsadresse nur ändern“ (N12). Die Bestellnummer stimmt, doch die Einschränkung ist im Englischen klarer. An solchen Stellen entscheidet sich, ob der Kundenservice einen Entwurf übernehmen kann.")
sub("Texte und Einstellungen")
body("Der Fallplan enthält 24 erfundene Anfragen, Serviceantworten und Produkttexte. Für jeden Text standen der erwartete Inhalt und eine mögliche Übersetzung bereits vor dem Test fest. Die 16 Normalfälle behandeln typische Fragen zu Artikeln, Versand und Rückgabe. Die übrigen acht Fälle enthalten unter anderem mehrdeutige Wörter, ungewohnte Zahlenformate und zitierte Anweisungen. In beiden Gruppen ist je die Hälfte der Ausgangstexte deutsch und englisch.")
body("Jeder Text lief zweimal durch die Anwendung. Im ersten Durchgang erhielt das Modell die Anweisung Handel v2 mit zusätzlichen Regeln für Shopbegriffe und die deutsche Sie-Anrede. Im zweiten Durchgang galt der kurze Übersetzungsauftrag Basis v1. Die Reihenfolge der Texte, das mitgegebene Glossar und die Modelleinstellungen waren gleich. Verwendet wurden Qwen3-4B Q4_K_M (Qwen, 2025) und llama.cpp b12125 (ggml-org, 2026) auf einem Windows-Rechner mit Intel Core i7-13700.")
sub("Auswertung")
body("Bei den Normalfällen zählen Bedeutung, Vollständigkeit, sachliche Details und Verständlichkeit. Je Kriterium gibt es 0 Punkte für verfehlt, 1 für Korrekturbedarf oder 2 für erfüllt. Ein Fall besteht ab 7 von 8 Punkten, sofern kein kritischer Fehler vorliegt. Ein anderer Preis, eine falsche Produkteigenschaft oder eine erfundene Zusage sind solche Fehler. Der Zielwert von 14 bestandenen Fällen stammt aus dem Konzept (Stolz, 2026a, S. 5–8). Der Test greift die in Phase 2 offenen Fragen zur Sprachqualität auf (Stolz, 2026b, S. 6).")
body("OpenAI Codex unterstützte die Erstellung der Fälle und Vergleichsübersetzungen, die Testläufe, die sprachliche Vorbewertung und die Ausarbeitung. Die persönliche Sprachbewertung steht aus. Im Anhang sind die Punkte und die unbearbeiteten Modelltexte nach Fallnummer geordnet.")
repo = "https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-projektstand/Finalisierung"
y=para(f'Anwendung und Versuchsdaten liegen im Ordner Finalisierung der Abgabe-ZIP. Dieselben Materialien stehen im <link href="{repo}"><u>Projekt auf GitHub</u></link>.',X,y,align=TA_JUSTIFY,rich=True,hyphenate=True)-6
end()

page();h(chapters[1][0])
body("Von 16 Normalfällen bestanden in der Vorbewertung neun mit Handel v2 und acht mit Basis v1. Beide Varianten verfehlten damit den Zielwert von 14. Sieben der insgesamt 24 Textpaare waren sogar wortgleich. Aufschlussreicher als der kleine Punkteunterschied ist, welches Detail bei der Übersetzung verloren geht.")
sub("Fristen, Beträge und Shopbegriffe")
body("Beim Rücksendeetikett (N02) bleibt alles erhalten, was die Kundschaft wissen muss. Die 14 Tage laufen ab heute. Der Kaufbeleg soll draußen bleiben, der Bestellplatzhalter steht noch an der richtigen Stelle. Auch beim Erstattungsbetrag von 18,50 EUR (N07) bleibt klar, dass die Versandkosten darin fehlen. In neun von zehn Glossarfällen treffen beide Varianten die vorgegebene Bezeichnung. Beim Geschirrtuch (N03) ist „dish towel“ zwar verständlich, im Shop heißt derselbe Artikel aber „tea towel“. Hier reicht es, den Namen an das Sortiment anzupassen.")
sub("Fehler mit Folgen für die Bestellung")
body("In N06 trifft Handel v2 den Glossarbegriff „replacement filter“ und übernimmt K-17 korrekt. Aus der Kanne wird aber eine Dose, bei Basis v1 sogar ein Tank. Ähnliches passiert mit der Glasschüssel (N11) und der Kanne mit Messskala (N14). Alle drei Fälle enthalten kritische Fehler beim Artikel. In vier weiteren Fällen reichen die Punkte für Sprache und Bedeutung nicht (N10, N12, N13, N16). So nennt N13 den Versender, obwohl laut Ausgangstext der Paketdienst die Sendung scannt. Bei keinem der 48 Entwürfe erschien ein Zahlen-, Kennungs- oder Platzhalterhinweis.")
body("Zur Vorführung eignet sich der fehlende Mixerhaken (N15). Handel v2 benennt den gelieferten Schneebesen richtig. Bei Basis v1 steht dafür „Wisper“. Dieser eine Fall macht den Unterschied zwischen neun und acht bestandenen Normalfällen aus. Bei Handel v2 passten in vier der sechs eigens geprüften Stilfälle Ansprache, Stil und Inhalt. Für die Vorführung bleibt daher Handel v2 eingestellt.")
body("In den vier Grenzfällen mit zitierten Aufforderungen (G01–G04) übersetzten beide Varianten die Nachricht. Bei „Der Absatz ist beschädigt“ (G05) fehlt dagegen schon im Original der Artikelbezug. Handel v2 schreibt „product“, Basis v1 „sale“. Der Kundenservice müsste hier zurückfragen, bevor er Ersatz anbietet.")
sub("Wartezeit am Einzelplatz")
body("Der erste Aufruf mit Modellstart dauerte 4,67 Sekunden. Bei den folgenden zehn kurzen Texten brauchte Handel v2 zwischen 2,47 und 3,39 Sekunden (Median 2,77), Basis v1 bei denselben Texten im Median 2,31 Sekunden. Die Zeit fürs Gegenlesen kommt hinzu. Gerade bei Artikelbezeichnungen und Lieferzusagen ist sie für eine brauchbare Antwort entscheidend.")
end()
page();h("Literaturverzeichnis")
def ref(author, title, rest, url=None):
    global y
    entry=escape(author)+" <i>"+escape(title)+"</i> "+escape(rest)
    if url:
        label=escape(url).replace("/tree/","/tree/<br/>")
        entry+=f'<br/><link href="{url}">{label}</link>'
    y=para(entry,X,y,rich=True,indent=1.27*cm)-6
ref("ggml-org. (2026).","llama.cpp","(Build b12125) [Software für Windows x64]. GitHub.","https://github.com/ggml-org/llama.cpp/releases/tag/b12125")
ref("Qwen. (2025).","Qwen3-4B-GGUF","(Q4_K_M, Revision bc64014) [Sprachmodell]. Hugging Face.","https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/bc640142c66e1fdd12af0bd68f40445458f3869b")
ref("Stolz, L. (2026a).","KI-gestützte Textübersetzung für einen kleinen Onlinehändler: Konzeptvorstellung und priorisierter Anforderungskatalog","[unveröffentlichtes Kursportfolio, Phase 1]. IU Internationale Hochschule.")
ref("Stolz, L. (2026b).","KI-gestützte Textübersetzung für einen kleinen Onlinehändler: Modellvergleich, Softwaredesign und Implementierung","[unveröffentlichtes Kursportfolio, Phase 2]. IU Internationale Hochschule.")
end()
page();h("Anhangsverzeichnis und Punktübersicht")
sub("Anhang A  Normalfälle")
body("Die vier Einzelwerte stehen in der Reihenfolge Bedeutung, Vollständigkeit, sachliche Details und Verständlichkeit. Jede Spalte nennt die vier Werte und die Summe. Ein Stern kennzeichnet einen kritischen Fehler.")
x_title=X+28
x_h=X+213
x_b=X+333
def zeile(text, x_pos, baseline, *, bold=False):
    c.setFont("ArialB" if bold else "Arial",10)
    c.drawString(x_pos, baseline, text)
for text,pos in (("Fall",X),("Thema",x_title),("Handel v2",x_h),("Basis v1",x_b)):
    zeile(text,pos,y-12,bold=True)
c.setFont("ArialB",10);c.drawRightString(W-X,y-12,"Seite")
y-=18;rule(y)
for case in cases[:16]:
    i=case["id"]
    baseline=y-14
    zeile(i,X,baseline);zeile(case["titel"],x_title,baseline)
    for prompt,pos in (("handel-v2",x_h),("basis-v1",x_b)):
        entry=assess[i][prompt]
        punkte=entry["punkte"]
        text=" · ".join(str(x) for x in punkte)+"  =  "+str(sum(punkte))+"/8"
        if entry["kritisch"]:text+=" *"
        zeile(text,pos,baseline)
    c.setFont("Arial",10);c.drawRightString(W-X,baseline,str(fallseite[i]))
    y-=18
rule(y-2);y-=15
sub("Anhang B  Grenzfälle")
body("Diese Fälle werden am Wortlaut besprochen. Eine Punktzahl war für sie im Fallplan nicht vorgesehen.")
for gruppe in [group for group in gruppen if group[0].startswith("G")]:
    first=gruppe[0]
    titel=" · ".join(f'{i} {next(c["titel"] for c in cases if c["id"]==i)}' for i in gruppe)
    y=para(titel,X,y,WD-40,size=10.5,leading=14)-5
    c.setFont("Arial",10);c.drawRightString(W-X,y+7,str(fallseite[first]))
end()

def fall(case):
    global y
    i=case["id"]
    y=para(i+"   "+case["titel"],X,y,WD,13,17,"ArialB")-3
    richtung={"DE-EN":"Deutsch → Englisch","EN-DE":"Englisch → Deutsch"}[case["richtung"]]
    meta=richtung+"   ·   "+case["textsorte"]
    if case["glossar"]:
        g=case["glossar"][0]
        meta+="   ·   Shopglossar: "+g["quelle"]+" → "+g["ziel"]
    y=para(meta,X,y,WD,9.5,12,"Arial")-7
    row("Original",case["text"],True)
    row("Vergleichstext",case["referenz"],True)
    handel=results[(i,"handel-v2")]["rohuebersetzung"]
    basis=results[(i,"basis-v1")]["rohuebersetzung"]
    if handel==basis:
        row("Beide Varianten",handel,True)
    else:
        row("Handel v2",handel,True)
        row("Basis v1",basis,True)
    y=para(assess[i]["analyse"],X,y-3,WD,10.5,14.5,align=TA_JUSTIFY,hyphenate=True)-7

by_id={case["id"]:case for case in cases}
for gruppe in gruppen:
    page("Anhang A  Normalfälle" if gruppe[0].startswith("N") else "Anhang B  Grenzfälle")
    for n,i in enumerate(gruppe):
        if n:
            rule(y-4);y-=18
        fall(by_id[i])
    end()
c.save()
