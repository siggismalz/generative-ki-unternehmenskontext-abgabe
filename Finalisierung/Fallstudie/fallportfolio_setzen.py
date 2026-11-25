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

chapters=[
    ("1 Ziel und Ergebnis",["Untersuchung","Ergebnis für den Händler","Primärmaterial und Hilfsmittel"],1),
    ("2 Methode",["Fallauswahl und Sollinhalt","Ein Modell, zwei Anweisungen","Bewertung der unveränderten Ausgabe"],2),
    ("3 Ergebnisse",["Normalfälle und Zielwert","Glossar und Ansprache","Verarbeitungszeit","Bedeutung der Fallzahlen"],3),
    ("4 Diskussion",[t for t,_ in assess["_diskussion"]],4),
    ("Literaturverzeichnis",[],5),
    ("Anhangsverzeichnis",[],6),
    ("Anhang A  Normalfälle",[],7),
    ("Anhang B  Grenzfälle",[],15),
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
body("Ein Kunde möchte nur den Deckel einer Dose nachbestellen. Ein anderer wartet auf einen Ersatzbecher, für den der Shop keine Gutschrift ausgestellt hat. Welche Teile solcher Nachrichten kann der lokale Übersetzungsassistent übernehmen, und wann muss der Kundenservice eingreifen?")
sub("1.1 Untersuchung")
body("Für einen fiktiven Haushaltswarenhändler wurden 24 neue deutsch- und englischsprachige Texte jeweils mit zwei Promptvarianten übersetzt. Alle 48 Aufrufe verwendeten dieselbe lokale Installation. Anhang A enthält alle Normalfälle, Anhang B alle Grenzfälle, jeweils mit Vergleichsübersetzungen und Einschätzung.")
sub("1.2 Ergebnis für den Händler")
body(assess["_fazit"][0]); body(assess["_fazit"][1])
sub("1.3 Primärmaterial und Hilfsmittel")
body("Alle Ausgangstexte sind synthetische Projektbeispiele. Die Anhänge dokumentieren die Ausgaben des untersuchten Qwen-Modells wörtlich. OpenAI Codex unterstützte die Formulierung der Testfälle, Arbeitsreferenzen und Prüfaussagen sowie die Automatisierung, Vorbewertung und Ausarbeitung. Arbeitsreferenzen und Korrekturvorschläge sind keine im Demonstrator freigegebenen Kundenantworten.")
repo = "https://github.com/siggismalz/generative-ki-unternehmenskontext-abgabe/tree/phase3-abgabe/Finalisierung"
y=para(f'Im <link href="{repo}"><u>öffentlichen GitHub-Repository zum dritten Meilenstein</u></link> enthält der Ordner Anwendung den Demonstrator. Im Ordner Fallstudie liegen der Fallkatalog (Faelle_vorab.json), die 48 Exporte (Rohdaten.json), die Einzelurteile (Vorbewertung.json) und die Prüfsummen (Provenienz.json). Mit laeufe.py lässt sich die Erhebung wiederholen.',X,y,align=TA_JUSTIFY,rich=True,hyphenate=True)-6
body("Für den Satz diente ReportLab 4.4.4 (Robinson et al., 2025), für die Sichtprüfung Poppler 25.07.0 (The Poppler Developers, 2025).")
end()

page();h(chapters[1][0])
sub("2.1 Fallauswahl und Sollinhalt")
body("Grundlage sind die Abnahmekriterien aus Phase 1 und die in Phase 2 offenen Sprachtests (Stolz, 2026a, S. 5–8; Stolz, 2026b, S. 6). Vor dem ersten Aufruf wurden 16 Normalfälle und acht Grenzfälle samt Arbeitsreferenz, Prüfaussagen und Glossar festgelegt. Beide Gruppen sind jeweils zur Hälfte deutsch- und englischsprachig. Kundenanfragen prüfen Fragen und Höflichkeit, Serviceantworten prüfen Fristen und Zusagen, Produkttexte prüfen Eigenschaften und Pflegehinweise.")
sub("2.2 Ein Modell, zwei Anweisungen")
body("Qwen3-4B Q4_K_M (Qwen, 2025) lief am 25.11.2026 über llama.cpp b12125 (ggml-org, 2026) auf einem Intel Core i7-13700 mit acht CPU-Threads. App-Version 2.2.0, Seed 42, Temperatur 0,2, top_p 0,8, top_k 20, Kontext 4.096 Tokens, maximal 1.024 Ausgabetokens. Der erste Durchgang nutzte Handel v2 mit Regeln für Zusagen, Platzhalter, Glossar und Sie-Ansprache. Danach übersetzte Basis v1 die gleichen Eingaben in gleicher Reihenfolge mit allgemeinem Übersetzungsauftrag. Zwischen den Aufrufen wurde kein Gesprächsverlauf übergeben.")
body("Die Anwendungs-API erzeugte und exportierte jeden Entwurf. Der Fallkatalog wurde vorab per SHA256 festgehalten. Modellhash und sieben Dateien aus Anwendung und Oberfläche wurden mit dem eingereichten Stand aus Phase 2 abgeglichen. Laufzeiten stammen aus dem App-Export und umfassen beim ersten Aufruf auch den Modellstart.")
sub("2.3 Bewertung der unveränderten Ausgabe")
body("Jede Normalfallausgabe erhält in den Kategorien Bedeutung, Vollständigkeit, sachliche Details und Verständlichkeit je 2 Punkte für erfüllt, 1 für Korrektur nötig oder 0 für nicht erfüllt. Ab 7/8 Punkten und ohne kritischen Fehler gilt der Fall im Raster als bestanden. Kritisch sind u. a. geänderte Mengen, IDs, Negationen, Produktmerkmale und Zusagen. Gleichbedeutende Formulierungen sind zulässig. Eine Abweichung vom gewünschten Glossarwort kann bei gleicher Bedeutung allein A13 betreffen.")
body("Codex erstellte Arbeitsreferenzen und Vorbewertungen. Die Referenzen wurden unabhängig von den späteren Rohtexten formuliert. Das Urteil einer sprachkundigen Person nach A02 steht aus. Für Grenzfälle wird die Bedeutung des Fehlers qualitativ erklärt.")
end()

page();h(chapters[2][0])
sub("3.1 Normalfälle und Zielwert")
body(assess["_zahlen"][0])
sub("3.2 Glossar und Ansprache")
body(assess["_zahlen"][1]); body(assess["_zahlen"][2])
sub("3.3 Verarbeitungszeit")
body(assess["_zahlen"][3])
body("Für dieselben zehn kurzen Texte N02–N11 dauerte ein Aufruf mit Basis v1 im Median 2,313 s (2,063–3,141 s). Der Modellprozess lief bereits. Die feste Reihenfolge lässt Einflüsse des Zwischenspeichers zu.")
sub("3.4 Bedeutung der Fallzahlen")
body("Die 24 Fälle wurden gezielt für typische Abläufe und bekannte Schwierigkeiten des fiktiven Händlers entworfen. Das Ergebnis beschreibt diese kurzen Texte bei einem Lauf je Prompt. Weder die Häufigkeit der Fehler in Kundenpost noch die Arbeitszeit für Prüfung und Nachbearbeitung lässt sich daraus schätzen. Für den Verkauf zählt bei einem falschen Artikel bereits ein einzelner Fehler.")
end()
page();h(chapters[3][0])
for i,(t,x) in enumerate(assess["_diskussion"],1):
    sub(f"4.{i} {t}");body(x)
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
ref("Robinson, A., Becker, R., the ReportLab team & the community. (2025).","ReportLab","(Version 4.4.4) [Software].","https://pypi.org/project/reportlab/4.4.4/")
ref("Stolz, L. (2026a).","KI-gestützte Textübersetzung für einen kleinen Onlinehändler: Konzeptvorstellung und priorisierter Anforderungskatalog","[unveröffentlichtes Kursportfolio, Phase 1]. IU Internationale Hochschule.")
ref("Stolz, L. (2026b).","KI-gestützte Textübersetzung für einen kleinen Onlinehändler: Modellvergleich, Softwaredesign und Implementierung","[unveröffentlichtes Kursportfolio, Phase 2]. IU Internationale Hochschule.")
ref("The Poppler Developers. (2025).","Poppler","(Version 25.07.0) [Software].","https://poppler.freedesktop.org/poppler-25.07.0.tar.xz")
end()
page();h("Anhangsverzeichnis")
for start,stop,group in ((0,16,"Anhang A  Normalfälle"),(16,24,"Anhang B  Grenzfälle")):
    sub(group)
    for n in range(start,stop,2):
        first,second=cases[n:n+2]
        y=para(f'{first["id"]} {first["titel"]} · {second["id"]} {second["titel"]}',X,y,WD-50)-6
        c.setFillColor(colors.black);c.setFont("Arial",11);c.drawRightString(W-X,y+10,str(7+n//2))
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
    row("Arbeitsreferenz",case["referenz"],True)
    row("Handel v2",a.get("rohuebersetzung",a.get("fehlermeldung","")),True)
    row("Basis v1",b.get("rohuebersetzung",b.get("fehlermeldung","")),True)
    row("Vergleich",assess[i]["analyse"],True)
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
