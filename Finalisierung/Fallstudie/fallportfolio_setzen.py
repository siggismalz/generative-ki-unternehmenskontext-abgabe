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

def score(v):
    return f'{sum(v["punkte"])}/8'
def v(i,pr):
    return assess[i][pr]

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

chapters = [
    ("1 Versuch und Bewertung", ["Welche Texte wurden übersetzt?", "Wie wurden die Entwürfe geprüft?"], 1),
    ("2 Ergebnisse für den Kundenservice", ["Was gelingt?", "Wo muss der Kundenservice eingreifen?", "Wie lange dauert eine Übersetzung?"], 2),
    ("Literaturverzeichnis", [], 3),
    ("Anhangsverzeichnis", [], 4),
    ("Anhang A  Normalfälle", [], 5),
    ("Anhang B  Grenzfälle", [], 13),
]
y=H-X
h("Inhaltsverzeichnis")
for title,subtitles,number in chapters:
    y-=4
    c.setFont("ArialB",11);c.drawString(X,y-11,title);c.drawRightString(W-X,y-11,str(number));y-=18
    for i,t in enumerate(subtitles,1):
        c.setFont("Arial",11);c.drawString(X+15,y-11,f"{title[0]}.{i} {t}");c.drawRightString(W-X,y-11,str(number));y-=16.5
c.drawCentredString(W/2,cm,"II")
c.showPage()

page();h(chapters[0][0])
body("Ein Kunde fragt nach einer Rückgabe. Der englische Entwurf nennt dieselbe Frist von 14 Tagen wie die deutsche Antwort. Bei einer Pflegeanleitung für eine Glasschüssel wird daraus jedoch ein Glasbecher. Wie gut lässt sich der Übersetzer im Alltag eines kleinen Haushaltswarenhändlers einsetzen?")
sub("1.1 Welche Texte wurden übersetzt?")
body("Vor dem Test wurden 24 fiktive Kundenanfragen, Serviceantworten und Produkttexte mit ihrem erwarteten Inhalt festgelegt. 16 bilden typische Anliegen ab. Die acht Grenzfälle enthalten zum Beispiel eine mehrdeutige Formulierung oder eine Anweisung auf einem Verpackungsaufdruck. In beiden Gruppen ging je die Hälfte der Texte vom Deutschen ins Englische, die andere Hälfte vom Englischen ins Deutsche.")
body("Alle Texte wurden zweimal mit demselben lokalen Übersetzer bearbeitet. Handel v2 gibt unter anderem Regeln für Shopbegriffe und die Sie-Anrede vor. Basis v1 enthält einen allgemeinen Übersetzungsauftrag. Weitere Unterschiede in den Einstellungen gab es nicht. Zuerst lief Handel v2, dann Basis v1, jeweils in derselben Fallreihenfolge. Eingesetzt wurden Qwen3-4B Q4_K_M (Qwen, 2025) und llama.cpp b12125 (ggml-org, 2026) auf einem Windows-Rechner mit Intel Core i7-13700.")
sub("1.2 Wie wurden die Entwürfe geprüft?")
body("Für jeden Normalfall zählen Bedeutung, Vollständigkeit, sachliche Details und Verständlichkeit. Je Kriterium gibt es 0 Punkte für verfehlt, 1 für Korrekturbedarf und 2 für erfüllt. Ab 7 von 8 Punkten besteht der Text, sofern kein kritischer Fehler vorliegt. Dazu zählen etwa falsche Mengen, veränderte Produkteigenschaften oder ein erfundenes Lieferversprechen. Das Projektziel liegt bei 14 bestandenen Normalfällen (Stolz, 2026a, S. 5–8). Die Prüfung schließt an die offenen Sprachtests aus Phase 2 an (Stolz, 2026b, S. 6).")
body("OpenAI Codex unterstützte die Erstellung der Fälle und Vergleichsübersetzungen, die Testläufe, die sprachliche Vorbewertung und die Ausarbeitung. Die persönliche Sprachbewertung steht aus. Im Anhang stehen zu jedem Fall das Original, eine mögliche Vergleichsübersetzung, beide unbearbeiteten Ausgaben und die Begründung des Urteils.")
repo = "https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-final/Finalisierung"
y=para(f'Der Ordner Finalisierung enthält die Anwendung und unter Fallstudie die Testdaten. Er liegt in der Abgabe-ZIP und im <link href="{repo}"><u>öffentlichen Projektstand auf GitHub</u></link>.',X,y,align=TA_JUSTIFY,rich=True,hyphenate=True)-6
end()

page();h(chapters[1][0])
sub("2.1 Was gelingt?")
body("Mit Handel v2 bestanden in der Vorbewertung 9 von 16 Normalfällen, mit Basis v1 waren es 8. Das Ziel von 14 erreichte keine Variante. Beide übertragen in N02 die Rücksendefrist und den Bestellplatzhalter korrekt. Bei N07 bleiben der Erstattungsbetrag und der Ausschluss der Versandkosten erhalten. Beide treffen in 9 von 10 Fällen den vorgegebenen Shopbegriff. Nur N03 gibt „Geschirrtuch“ als „dish towel“ wieder. Das ist verständlich, im Sortiment heißt der Artikel aber „tea towel“. In vier von sechs gesondert geprüften Texten passten bei Handel v2 auch Ansprache, Stil und Inhalt.")
sub("2.2 Wo muss der Kundenservice eingreifen?")
body("Drei Entwürfe von Handel v2 enthielten kritische Artikelfehler (N06, N11, N14). So macht der Pflegehinweis N11 aus der Glasschüssel einen Glasbecher und aus Bambus schlicht Holz. In vier weiteren Fällen reichten die Punkte für Sprache und Bedeutung nicht aus (N10, N12, N13, N16). Bei N13 wird der Paketdienst zum „Versender“. Basis v1 machte in N15 aus dem erhaltenen Schneebesen „Wisper“ und verfehlte damit einen weiteren Fall. Bei sieben der 24 Fallpaare war der Wortlaut beider Varianten gleich. Handel v2 bestand sieben von acht Fällen mit deutschem und zwei von acht mit englischem Ausgangstext. Die Fälle waren unterschiedlich schwierig.")
body("In den vier Grenzfällen G01–G04 blieben zitierte Aufforderungen bei beiden Varianten Teil der Übersetzung. Andere Schwierigkeiten brauchten mehr Kontext. Bei „Der Absatz ist beschädigt“ (G05) wählt Handel v2 „product“, Basis v1 „sale“. Vor der Antwort muss geklärt werden, welcher Gegenstand beschädigt ist. Bei keinem der 48 Entwürfe erschien ein Zahlen-, ID- oder Platzhalterhinweis. Der Kundenservice sollte daher auch bei einem unauffälligen Text jeden Artikel, jede Bedingung und jede Zusage am Original prüfen.")
sub("2.3 Wie lange dauert eine Übersetzung?")
body("Bei Handel v2 dauerte der erste Aufruf mit Modellstart 4,67 Sekunden. Die nächsten zehn kurzen Texte lagen zwischen 2,47 und 3,39 Sekunden (Median 2,77). Alle blieben unter dem Ziel von 30 Sekunden. Basis v1 benötigte für dieselben zehn Fälle im Median 2,31 Sekunden. Über alle 24 Aufrufe lag der Median bei 2,84 bzw. 2,30 Sekunden. Die Reihenfolge war fest, die Zeit für die persönliche Prüfung kommt hinzu.")
body("Für die Vorführung fiel die Wahl auf Handel v2. Im Test war ein weiterer Entwurf brauchbar und bei N12 gelang die gewünschte Sie-Anrede. Die Ergebnisse gelten für diese ausgewählten Texte. Für eine Kundenantwort braucht es weiterhin die Freigabe durch eine Person mit Sprach- und Produktkenntnis.")
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
page();h("Anhangsverzeichnis")
for start,stop,group in ((0,16,"Anhang A  Normalfälle"),(16,24,"Anhang B  Grenzfälle")):
    sub(group)
    for n in range(start,stop,2):
        first,second=cases[n:n+2]
        y=para(f'{first["id"]} {first["titel"]} · {second["id"]} {second["titel"]}',X,y,WD-50)-6
        c.setFillColor(colors.black);c.setFont("Arial",11);c.drawRightString(W-X,y+10,str(5+n//2))
end()
def card(case):
    global y
    i=case["id"];a=results[(i,"handel-v2")];b=results[(i,"basis-v1")]
    y=para(i+"   "+case["titel"],X,y,WD,14,17,"ArialB")-2
    des={"DE-EN":"Deutsch → Englisch","EN-DE":"Englisch → Deutsch"}[case["richtung"]]
    y=para(des+"   ·   "+case["textsorte"],X,y,WD,9.5,12,"Arial")-7
    row("Ausgangstext",case["text"],True)
    if case["glossar"]:
        entry=case["glossar"][0]
        row("Shopglossar",entry["quelle"]+" → "+entry["ziel"],True)
    row("Vergleichstext",case["referenz"],True)
    row("Handel v2",a.get("rohuebersetzung",a.get("fehlermeldung","")),True)
    row("Basis v1",b.get("rohuebersetzung",b.get("fehlermeldung","")),True)
    row("Beurteilung",assess[i]["analyse"],True)
    if i.startswith("N"):
        parts=[]
        for key,title in (("handel-v2","Handel"),("basis-v1","Basis")):
            sv=v(i,key)
            parts.append(title+" "+" / ".join(map(str,sv["punkte"]))+" = "+score(sv)+(" · kritisch" if sv["kritisch"] else ""))
        row("Punkte","     |     ".join(parts),True)

for n in range(0,len(cases),2):
    page("Anhang A  Normalfälle" if n<16 else "Anhang B  Grenzfälle")
    for i in (n,n+1):
        if i==n+1:rule(y-4);y-=17
        card(cases[i])
    if n<16:
        y-=5
        y=para("Die vier Werte stehen für Bedeutung, Vollständigkeit, sachliche Details und Verständlichkeit (je 0–2 Punkte). Ein kritischer Fehler schließt das Bestehen aus.",X,y,WD,10,15,"Arial",TA_JUSTIFY)
    end()
c.save()
