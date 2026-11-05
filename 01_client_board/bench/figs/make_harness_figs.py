#!/usr/bin/env python3
"""Bench wiring + harness figures for the bench session sheet.
python3 make_harness_figs.py  → bench_wiring.svg/.png, harnesses.svg/.png (print, light theme) and *_widget.svg (theme classes only)."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))

PRINT_CSS = """<style>
text{font-family:Arial,Helvetica,sans-serif}
.t{font-size:14px;fill:#2C2C2A}.ts{font-size:12px;fill:#5F5E5A}.th{font-size:14px;font-weight:bold;fill:#2C2C2A}
.box{fill:#F1EFE8;stroke:#888780}.arr{stroke:#5F5E5A;stroke-width:1.5;fill:none}.leader{stroke:#888780;stroke-width:0.5;stroke-dasharray:3 3;fill:none}
.c-coral>rect,rect.c-coral{fill:#FAECE7;stroke:#993C1D}.c-coral>.th{fill:#712B13}.c-coral>.ts{fill:#993C1D}
.c-teal>rect,rect.c-teal{fill:#E1F5EE;stroke:#0F6E56}.c-teal>.th{fill:#085041}.c-teal>.ts{fill:#0F6E56}
.c-gray>rect,rect.c-gray{fill:#F1EFE8;stroke:#5F5E5A}.c-gray>.th{fill:#444441}.c-gray>.ts{fill:#5F5E5A}
</style>"""
DEFS = '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></marker></defs>'

def node(ramp, x, y, w, h, title, sub=None):
    cx = x + w / 2
    if sub:
        return (f'<g class="c-{ramp}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" stroke-width="0.5"/>'
                f'<text class="th" x="{cx}" y="{y+h/2-9}" text-anchor="middle" dominant-baseline="central">{title}</text>'
                f'<text class="ts" x="{cx}" y="{y+h/2+10}" text-anchor="middle" dominant-baseline="central">{sub}</text></g>')
    return (f'<g class="c-{ramp}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" stroke-width="0.5"/>'
            f'<text class="th" x="{cx}" y="{y+h/2}" text-anchor="middle" dominant-baseline="central">{title}</text></g>')

def svg(w, h, title, desc, body, mode):
    css = PRINT_CSS if mode == "print" else ""
    bg = '<rect x="0" y="0" width="100%" height="100%" fill="#FFFFFF"/>' if mode == "print" else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {w} {h}" role="img"><title>{title}</title><desc>{desc}</desc>'
            f'{css}{DEFS}{bg}{body}</svg>')

# ------------------------------------------------------------------ figure 1: bench wiring
def wiring():
    b = []
    # Xantrex
    b.append('<g class="c-coral"><rect x="30" y="30" width="150" height="160" rx="6" stroke-width="0.5"/>'
             '<text class="th" x="105" y="48" text-anchor="middle" dominant-baseline="central">Xantrex XPH 35-4T</text>'
             '<text class="ts" x="170" y="70" text-anchor="end" dominant-baseline="central">out1 +</text>'
             '<text class="ts" x="170" y="106" text-anchor="end" dominant-baseline="central">out1 − / out2 +</text>'
             '<text class="ts" x="170" y="142" text-anchor="end" dominant-baseline="central">out2 −</text>'
             '<text class="ts" x="105" y="174" text-anchor="middle" dominant-baseline="central">2 × 30.0 V, 50 mA</text></g>')
    b.append(node("coral", 210, 48, 120, 44, "Fluke 45", "mA, in series"))
    b.append(node("coral", 210, 120, 120, 44, "BM235", "mA, in series"))
    # board container
    b.append('<rect x="370" y="20" width="270" height="300" rx="16" fill="none" stroke="var(--border-strong, #888780)" stroke-width="0.8" stroke-dasharray="5 4"/>'
             '<text class="th" x="384" y="38" dominant-baseline="central">Client STIM board</text>')
    b.append(node("coral", 380, 56, 100, 100, "J3 power", "Micro-Fit 1/2/3"))
    b.append(node("teal", 380, 186, 100, 44, "J4 input", "BNC"))
    b.append(node("gray", 380, 250, 100, 44, "J1 / J2", "electrode conn."))
    # test loops
    tl = [("VP", "C2 hot end"), ("VN", "C3 hot end"), ("OUT", "R7 top"), ("LOAD", "R7 bottom"), ("REF", "U1 pin 6")]
    s = '<g class="c-teal"><rect x="505" y="56" width="125" height="238" rx="6" stroke-width="0.5"/><text class="th" x="567" y="74" text-anchor="middle" dominant-baseline="central">Test loops</text>'
    for k, (n, w) in enumerate(tl):
        y = 104 + k * 40
        s += f'<text class="th" x="517" y="{y}" dominant-baseline="central">{n}</text><text class="ts" x="517" y="{y+16}" dominant-baseline="central">{w}</text>'
    b.append(s + "</g>")
    b.append(node("teal", 210, 186, 120, 44, "DG1022", "BNC, HiZ"))
    b.append(node("teal", 30, 350, 150, 56, "Laptop", "bench_rig.py, USB"))
    b.append(node("gray", 380, 350, 110, 56, "Load fixture", "RL, link, GND"))
    b.append(node("teal", 510, 350, 130, 56, "DHO804", "4 × 10× probes"))
    # power lines
    b.append('<line x1="180" y1="70" x2="208" y2="70" stroke="#E24B4A" stroke-width="1.5"/><line x1="330" y1="70" x2="378" y2="70" stroke="#E24B4A" stroke-width="1.5" marker-end="url(#arrow)"/>')
    b.append('<line x1="180" y1="106" x2="378" y2="106" stroke="#888780" stroke-width="1.5" marker-end="url(#arrow)"/>')
    b.append('<line x1="180" y1="142" x2="208" y2="142" stroke="#378ADD" stroke-width="1.5"/><line x1="330" y1="142" x2="378" y2="142" stroke="#378ADD" stroke-width="1.5" marker-end="url(#arrow)"/>')
    # signal
    b.append('<line x1="330" y1="208" x2="378" y2="208" class="arr" marker-end="url(#arrow)"/>')
    b.append('<path d="M105 350 L105 262 L270 262 L270 232" class="arr" fill="none" marker-end="url(#arrow)"/>')
    b.append('<path d="M105 406 L105 436 L575 436 L575 408" class="arr" fill="none" marker-end="url(#arrow)"/>')
    b.append('<line x1="430" y1="296" x2="430" y2="348" class="arr" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
    b.append('<line x1="575" y1="348" x2="575" y2="296" class="arr" marker-end="url(#arrow)"/>')
    b.append('<text class="ts" x="30" y="468" dominant-baseline="central">Coral = power path (red +30 V, grey GND, blue −30 V). Teal = signal and measurement. Probe grounds on the fixture GND post.</text>')
    return 680, 490, "Bench wiring for the client STIM board session", "Xantrex rails through two ammeters to J3, DG1022 to J4, load fixture on J1/J2, DHO804 probes on five test loops, laptop on USB to scope and generator.", "".join(b)

# ------------------------------------------------------------------ figure 2: harness details
def harnesses():
    b = []
    # ---- A power harness
    b.append('<text class="th" x="30" y="30" dominant-baseline="central">A  Power harness: J3 → Xantrex (make 1)</text>')
    b.append('<g class="c-gray"><rect x="50" y="62" width="70" height="92" rx="4" stroke-width="0.5"/></g>')
    b.append('<text class="ts" x="85" y="52" text-anchor="middle" dominant-baseline="central">Micro-Fit plug</text>')
    wires = [(84, "#E24B4A", "1  VCC+  red", "out1 +  (via Fluke 45)"), (108, "#444441", "2  GND  black", "out1 − + out2 + link"), (132, "#378ADD", "3  VCC−  blue", "out2 −  (via BM235)")]
    for y, col, lab, dest in wires:
        b.append(f'<circle cx="104" cy="{y}" r="5" fill="none" stroke="{col}" stroke-width="1.5"/>')
        b.append(f'<line x1="109" y1="{y}" x2="470" y2="{y}" stroke="{col}" stroke-width="2"/>')
        b.append(f'<text class="ts" x="140" y="{y-9}" dominant-baseline="central">{lab}</text>')
        b.append(f'<rect x="470" y="{y-6}" width="38" height="12" rx="2" fill="{col}" opacity="0.85"/><line x1="508" y1="{y}" x2="528" y2="{y}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>')
        b.append(f'<text class="ts" x="538" y="{y}" dominant-baseline="central">{dest}</text>')
    b.append('<text class="ts" x="62" y="84" dominant-baseline="central">1</text><text class="ts" x="62" y="108" dominant-baseline="central">2</text><text class="ts" x="62" y="132" dominant-baseline="central">3</text>')
    b.append('<path d="M300 70 q10 14 20 0 q10 -14 20 0 q10 14 20 0" fill="none" stroke="#888780" stroke-width="0.8"/>')
    b.append('<text class="ts" x="372" y="62" dominant-baseline="central">~60 cm, twisted</text>')
    b.append('<text class="ts" x="50" y="176" dominant-baseline="central">4 mm banana plugs, GND one stackable. Ammeters sit between the Xantrex posts and the bananas, not in the harness.</text>')
    b.append('<text class="ts" x="50" y="194" dominant-baseline="central">Pinout from STIM.SchDoc: confirm by continuity J3 pin → F1 / F2 pad before first power. Or borrow the client\'s cable.</text>')
    # ---- B load fixture
    y0 = 230
    b.append(f'<text class="th" x="30" y="{y0}" dominant-baseline="central">B  Load fixture: J1 / J2 (make 2: 1.00 kΩ and 2.2 kΩ, 0.1 %)</text>')
    yl = y0 + 64
    b.append(node("gray", 50, yl - 22, 64, 44, "J1 mate"))
    b.append(f'<line x1="114" y1="{yl}" x2="170" y2="{yl}" stroke="#444441" stroke-width="1.5"/>')
    b.append(f'<rect x="170" y="{yl-12}" width="44" height="24" rx="3" fill="#FAC775" stroke="#854F0B" stroke-width="0.8"/><circle cx="182" cy="{yl}" r="3" fill="#412402"/><circle cx="202" cy="{yl}" r="3" fill="#412402"/>')
    b.append(f'<text class="ts" x="192" y="{yl-24}" text-anchor="middle" dominant-baseline="central">link</text>')
    b.append(f'<line x1="214" y1="{yl}" x2="270" y2="{yl}" stroke="#444441" stroke-width="1.5"/>')
    zz = " ".join(f"l 8 {(-10 if i % 2 == 0 else 10) if 0 < i < 9 else (-5 if i == 0 else 5)}" for i in range(10))
    b.append(f'<path d="M270 {yl} {zz}" fill="none" stroke="#444441" stroke-width="1.5"/>')
    b.append(f'<text class="ts" x="310" y="{yl-24}" text-anchor="middle" dominant-baseline="central">RL</text>')
    b.append(f'<line x1="350" y1="{yl}" x2="450" y2="{yl}" stroke="#444441" stroke-width="1.5"/>')
    b.append(node("gray", 450, yl - 22, 64, 44, "J2 mate"))
    b.append(f'<line x1="410" y1="{yl}" x2="410" y2="{yl+30}" stroke="#444441" stroke-width="1.5"/><circle cx="410" cy="{yl+37}" r="7" fill="none" stroke="#444441" stroke-width="1.5"/>')
    b.append(f'<text class="ts" x="424" y="{yl+40}" dominant-baseline="central">GND post: 4 probe grounds + generator ground</text>')
    b.append(f'<line x1="242" y1="{yl}" x2="242" y2="{yl-26}" stroke="#444441" stroke-width="1.5"/><circle cx="242" cy="{yl-33}" r="6" fill="none" stroke="#444441" stroke-width="1.5"/>')
    b.append(f'<text class="ts" x="252" y="{yl-44}" dominant-baseline="central">LOAD tip (CH1)</text>')
    b.append(f'<text class="ts" x="192" y="{yl+30}" text-anchor="middle" dominant-baseline="central">pull → Fluke 45 in series (A5b)</text>')
    b.append(f'<text class="ts" x="50" y="{yl+70}" dominant-baseline="central">≥ 0.25 W. Write the measured RL on each fixture (--rl / --rl2). J1/J2 connector type: confirm with the client.</text>')
    # ---- C test loops
    y1 = yl + 110
    b.append(f'<text class="th" x="30" y="{y1}" dominant-baseline="central">C  Test loops: 30 AWG, tacked at home, only with the client\'s OK</text>')
    tl = [("VP", "C2 hot end"), ("VN", "C3 hot end"), ("OUT", "R7 top"), ("LOAD", "R7 bottom"), ("REF", "U1 pin 6")]
    for k, (n, w) in enumerate(tl):
        x = 90 + k * 120; yy = y1 + 46
        b.append(f'<rect x="{x-16}" y="{yy+14}" width="32" height="7" rx="1" fill="#B4B2A9"/><line x1="{x}" y1="{yy+14}" x2="{x}" y2="{yy}" stroke="#444441" stroke-width="1.5"/><circle cx="{x}" cy="{yy-7}" r="7" fill="none" stroke="#444441" stroke-width="1.5"/>')
        b.append(f'<text class="th" x="{x}" y="{yy+38}" text-anchor="middle" dominant-baseline="central">{n}</text><text class="ts" x="{x}" y="{yy+56}" text-anchor="middle" dominant-baseline="central">{w}</text>')
    b.append(f'<text class="ts" x="50" y="{y1+128}" dominant-baseline="central">No permission → Pomona micro-grabbers on component ends, never on SOIC pins; tape the probe leads down.</text>')
    return 680, y1 + 150, "Harness and fixture mockups", "Power harness from Micro-Fit plug to three banana plugs, load fixture with series link and ground post, and five test loop locations.", "".join(b)

def render(name, fn):
    w, h, title, desc, body = fn()
    for mode in ("print", "widget"):
        p = os.path.join(HERE, f"{name}{'' if mode == 'print' else '_widget'}.svg")
        open(p, "w").write(svg(w, h, title, desc, body, mode))
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=3)
        pg.set_content(f'<html><body style="margin:0;background:#fff">{svg(w, h, title, desc, body, "print").replace("width=\"100%\"", f"width=\"{w}\" height=\"{h}\"")}</body></html>')
        pg.screenshot(path=os.path.join(HERE, f"{name}.png"), clip={"x": 0, "y": 0, "width": w, "height": h}); br.close()
    print("wrote", name, w, h)

if __name__ == "__main__":
    render("bench_wiring", wiring); render("harnesses", harnesses)
