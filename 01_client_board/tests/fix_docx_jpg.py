#!/usr/bin/env python3
"""Post-build fix for docx 8.5: JPEG images are stored as word/media/*.png. Rename those parts to .jpg and
re-point word/_rels/document.xml.rels so the content type is right.   py fix_docx_jpg.py ../BENCH-B0-SUMMARY.docx"""
import re, shutil, sys, zipfile

src = sys.argv[1]; tmp = src + ".tmp"
zin = zipfile.ZipFile(src); names = zin.namelist()
ren = {n: n[:-4] + ".jpg" for n in names if n.startswith("word/media/") and n.endswith(".png") and zin.read(n)[:2] == b"\xff\xd8"}
rels = zin.read("word/_rels/document.xml.rels").decode()
for a, b in ren.items(): rels = rels.replace("media/" + a.split("/")[-1], "media/" + b.split("/")[-1])
# equations: a math run that contains a digit is a number with its unit -> upright (m:sty p); letter-only runs stay italic (variables)
doc = zin.read("word/document.xml").decode()
def upright(m):
    return m.group(0) if not re.search(r"\d", m.group(2)) or "<m:rPr>" in m.group(1) else \
        m.group(1).replace("<m:r>", '<m:r><m:rPr><m:sty m:val="p"/></m:rPr>', 1) + m.group(2) + m.group(3)
doc, n_eq = re.subn(r"(<m:r>(?:<w:rPr>.*?</w:rPr>)?<m:t(?: xml:space=\"preserve\")?>)([^<]*)(</m:t></m:r>)", upright, doc)
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for n in names:
        data = rels if n == "word/_rels/document.xml.rels" else doc if n == "word/document.xml" else zin.read(n)
        zout.writestr(ren.get(n, n), data)
zin.close(); shutil.move(tmp, src)
z = zipfile.ZipFile(src); targets = re.findall(r'Target="(media/[^"]+)"', z.read("word/_rels/document.xml.rels").decode())
missing = [t for t in targets if "word/" + t not in z.namelist()]
print(f"renamed {len(ren)} JPEG parts; {len(targets)} image rels, missing {missing}; math runs seen {n_eq}; zip ok: {z.testzip() is None}")
