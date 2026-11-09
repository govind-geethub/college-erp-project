"""
Generates a valid, beautifully formatted Microsoft Word (.docx) document
from the Technical Design Document without requiring external third-party dependencies.
Uses the standard OpenXML (ECMA-376) standard package structure.
"""

import os
import zipfile
import html
from xml.sax.saxutils import escape

DOCX_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

DOCX_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCX_WORD_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

DOCX_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:color w:val="1E293B"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>"""


def build_docx_from_markdown(md_path: str, docx_path: str):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    body_xml_parts = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        if line_str.startswith("# "):
            title_text = escape(line_str[2:])
            body_xml_parts.append(f"""
            <w:p>
              <w:pPr><w:jc w:val="left"/><w:spacing w:before="240" w:after="120"/></w:pPr>
              <w:r><w:rPr><w:b/><w:sz w:val="40"/><w:color w:val="0F172A"/></w:rPr><w:t>{title_text}</w:t></w:r>
            </w:p>""")
        elif line_str.startswith("## "):
            h2_text = escape(line_str[3:])
            body_xml_parts.append(f"""
            <w:p>
              <w:pPr><w:spacing w:before="200" w:after="80"/></w:pPr>
              <w:r><w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="1E3A8A"/></w:rPr><w:t>{h2_text}</w:t></w:r>
            </w:p>""")
        elif line_str.startswith("### "):
            h3_text = escape(line_str[4:])
            body_xml_parts.append(f"""
            <w:p>
              <w:pPr><w:spacing w:before="160" w:after="60"/></w:pPr>
              <w:r><w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="2563EB"/></w:rPr><w:t>{h3_text}</w:t></w:r>
            </w:p>""")
        elif line_str.startswith("- ") or line_str.startswith("* "):
            bullet_text = escape(line_str[2:])
            body_xml_parts.append(f"""
            <w:p>
              <w:pPr><w:ind w:left="360"/><w:spacing w:before="40" w:after="40"/></w:pPr>
              <w:r><w:t>&bull;  {bullet_text}</w:t></w:r>
            </w:p>""")
        else:
            p_text = escape(line_str)
            body_xml_parts.append(f"""
            <w:p>
              <w:pPr><w:spacing w:before="60" w:after="60"/></w:pPr>
              <w:r><w:t>{p_text}</w:t></w:r>
            </w:p>""")

    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {''.join(body_xml_parts)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        z.writestr("_rels/.rels", DOCX_RELS)
        z.writestr("word/_rels/document.xml.rels", DOCX_WORD_RELS)
        z.writestr("word/document.xml", doc_xml)
        z.writestr("word/styles.xml", DOCX_STYLES)

    print(f"Successfully generated DOCX: {docx_path}")


if __name__ == "__main__":
    src_md = os.path.join(os.path.dirname(__file__), "..", "docs", "TDD.md")
    dest_docx = os.path.join(os.path.dirname(__file__), "..", "Technical_Design_Document.docx")
    build_docx_from_markdown(src_md, dest_docx)
