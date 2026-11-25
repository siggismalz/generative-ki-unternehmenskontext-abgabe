"""Erzeugt die bearbeitbare Fassung des zweiseitigen Abstracts."""
from pathlib import Path
import json
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor

folder = Path(__file__).resolve().parent
pages = json.loads((folder / "text.json").read_text(encoding="utf-8"))
doc = Document()
section = doc.sections[0]
section.page_width, section.page_height = Cm(21), Cm(29.7)
section.top_margin = section.left_margin = section.right_margin = section.bottom_margin = Cm(2)
section.footer_distance = Cm(0.95)
doc.core_properties.title = "KI-gestützte Textübersetzung im Kundenservice eines kleinen Onlinehändlers"
doc.core_properties.author = "Leon Stolz"
style = doc.styles["Normal"]
style.font.name, style.font.size = "Arial", Pt(11)
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
rpr = style.element.get_or_add_rPr()
lang = OxmlElement("w:lang")
lang.set(qn("w:val"), "de-DE")
rpr.append(lang)
hyphen = OxmlElement("w:autoHyphenation")
hyphen.set(qn("w:val"), "true")
doc.settings.element.append(hyphen)
title = doc.styles["Title"]
title.base_style = style
title.font.name, title.font.size, title.font.bold = "Arial",Pt(12),True
title.font.color.rgb = RGBColor(0,0,0)
fonts = title.element.find(".//"+qn("w:rFonts"))
for key in list(fonts.attrib):
    if "theme" in key.lower():
        del fonts.attrib[key]
for key in ("ascii", "hAnsi", "eastAsia", "cs"):
    fonts.set(qn("w:"+key), "Arial")
title.paragraph_format.space_before, title.paragraph_format.space_after = Pt(0),Pt(6)
title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
title.paragraph_format.line_spacing = 1.5
border = title.element.find(".//"+qn("w:pBdr"))
if border is not None:
    border.getparent().remove(border)
for idx, page in enumerate(pages):
    p = doc.add_paragraph(page["titel"], style=title)
    if idx:
        p.paragraph_format.page_break_before = True
    for text in page["absaetze"]:
        doc.add_paragraph(text)
    if "projektlink" in page:
        projekt = page["projektlink"]
        p = doc.paragraphs[-1]
        p.add_run(" ")
        link = OxmlElement("w:hyperlink")
        link.set(qn("r:id"), p.part.relate_to(projekt["url"], RT.HYPERLINK, is_external=True))
        run = p.add_run(projekt["text"])
        run.underline = True
        link.append(run._r)
        p._p.append(link)
        p.add_run(".")
    if page.get("literatur"):
        doc.add_paragraph("Literaturverzeichnis", style=title)
        for quelle in page["literatur"]:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.left_indent = Cm(1.27)
            p.paragraph_format.first_line_indent = Cm(-1.27)
            p.add_run(quelle["autor"])
            p.add_run(quelle["titel"]).italic = True
            p.add_run(quelle["zusatz"])
            link = OxmlElement("w:hyperlink")
            link.set(qn("r:id"), p.part.relate_to(quelle["url"], RT.HYPERLINK, is_external=True))
            run = p.add_run(quelle["url"])
            link.append(run._r)
            p._p.append(link)
footer = section.footer.paragraphs[0]
footer.style = style
footer.paragraph_format.space_after = Pt(0)
footer.paragraph_format.line_spacing = 1
footer.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
footer.paragraph_format.tab_stops.add_tab_stop(Cm(8.5), WD_TAB_ALIGNMENT.CENTER)
run = footer.add_run("Leon Stolz  ·  DLBFMPGKIU01  ·  Phase 3\t")
run.font.size = Pt(9)
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
footer._p.append(field)
doc.save(folder / "Abstract.docx")

