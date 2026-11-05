#!/usr/bin/env python3
"""Generate 03_safety_plan/kicad/safety-loop.kicad_sch: a one-sheet block schematic of the JY063 safety loop.

KiCad 7 file format (version 20230121) so it renders with kicad-cli 7 and opens (and upgrades) in KiCad 8-10.
All coordinates in mm, A3 landscape (420 x 297). Signal flow left -> right, PC side left of the isolation barrier.
"""
import uuid, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else "safety-loop.kicad_sch"

def U():
    return str(uuid.uuid4())

def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

items = []

def snap(v):
    return round(round(v / 1.27) * 1.27, 2)

# ---------- colours (r g b a) ----------
C_PATH = "(color 170 20 20 1)"     # stimulating current path: red
C_TRIP = "(color 190 110 0 1)"     # detectors / trips: amber
C_LOGIC = "(color 20 70 170 1)"    # latch / enable chain: blue
C_ISO = "(color 0 120 60 1)"       # isolation: green
C_PASS = "(color 110 40 140 1)"    # passive, no-supply layers: purple
C_NOTE = "(color 60 60 60 1)"
C_BLK = "(color 0 0 0 0)"

class Box:
    def __init__(self, name, x, y, w, h, title, body="", color=C_BLK, fs=1.6, lw=0.35, dashed=False):
        self.name, self.x, self.y, self.w, self.h = name, x, y, w, h
        self.title, self.body, self.color, self.fs, self.lw, self.dashed = title, body, color, fs, lw, dashed
        boxes[name] = self
    # port helpers (absolute coordinates on the edge, snapped to 1.27)
    def L(self, f=0.5): return (round(self.x, 2), snap(self.y + self.h * f))
    def R(self, f=0.5): return (round(self.x + self.w, 2), snap(self.y + self.h * f))
    def T(self, f=0.5): return (snap(self.x + self.w * f), round(self.y, 2))
    def B(self, f=0.5): return (snap(self.x + self.w * f), round(self.y + self.h, 2))
    def emit(self):
        text = self.title.upper() + ("\n" + self.body if self.body else "")
        t = "dash" if self.dashed else "solid"
        return (f'(text_box "{esc(text)}" (at {self.x} {self.y} 0) (size {self.w} {self.h})\n'
                f'  (stroke (width {self.lw}) (type {t}) {self.color}) (fill (type none))\n'
                f'  (effects (font (size {self.fs} {self.fs}) {self.color}) (justify left top))\n'
                f'  (uuid "{U()}"))')

boxes = {}


def wire(pts, width=0.25, color=C_BLK, dashed=False):
    t = "dash" if dashed else "default"
    pts = [(round(x, 2), round(y, 2)) for x, y in pts]
    full = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        if a[0] != b[0] and a[1] != b[1]:   # dogleg: horizontal to the midpoint, vertical, horizontal
            xm = snap((a[0] + b[0]) / 2)
            full += [(xm, a[1]), (xm, b[1])]
        full.append(b)
    for a, b in zip(full, full[1:]):
        if a == b: continue
        p = f"(xy {a[0]} {a[1]}) (xy {b[0]} {b[1]})"
        items.append(f'(wire (pts {p}) (stroke (width {width}) (type {t}) {color}) (uuid "{U()}"))')

def path(pts):  # orthogonal polyline helper: list of (x,y); consecutive points must share x or y
    for a, b in zip(pts, pts[1:]):
        assert a[0] == b[0] or a[1] == b[1], (a, b)

def junction(x, y, color=C_BLK):
    items.append(f'(junction (at {x} {y}) (diameter 1.0) {color} (uuid "{U()}"))')

def label(name, x, y, rot=0, just="left bottom"):
    items.append(f'(label "{esc(name)}" (at {x} {y} {rot}) (fields_autoplaced)\n'
                 f'  (effects (font (size 1.4 1.4)) (justify {just})) (uuid "{U()}"))')

def text(s, x, y, size=1.6, rot=0, bold=False, color=C_NOTE, just="left bottom"):
    b = " bold" if bold else ""
    items.append(f'(text "{esc(s)}" (at {x} {y} {rot})\n'
                 f'  (effects (font (size {size} {size}){b} {color}) (justify {just})) (uuid "{U()}"))')

def line(pts, width=0.3, color=C_BLK, dashed=False):
    p = " ".join(f"(xy {x} {y})" for x, y in pts)
    t = "dash" if dashed else "default"
    items.append(f'(polyline (pts {p}) (stroke (width {width}) (type {t}) {color}) (uuid "{U()}"))')

def rect(x1, y1, x2, y2, width=0.25, color=C_BLK, dashed=False):
    t = "dash" if dashed else "default"
    items.append(f'(rectangle (start {x1} {y1}) (end {x2} {y2}) (stroke (width {width}) (type {t}) {color}) (fill (type none)) (uuid "{U()}"))')

# =====================================================================================================
# LAYOUT
# =====================================================================================================
XB = 66.04            # isolation barrier x
Y1 = 40.64            # row 1: stimulating path
Y2 = 101.6            # row 2: detectors
Y3 = 162.56           # row 3: latch + enable chain
Y4 = 215.9            # row 4: human inputs / indicators
H = 27.94

# ---- header
text("JY063 EVS stimulator: SAFETY LOOP (planning sheet, Rev 2 target)", 15.24, 22.86, size=3.2, bold=True, color=C_BLK)
text("Block level, no part values are final. Numbers: [DS] datasheet, [H] hand calc, [N] ngspice (archive 4-rev1-design), [DS5] Digitimer DS5 manual, [ASSUME]. "
     "Bench prototype, dummy loads only. Companion text: 03_safety_plan/SAFETY_LOOP.md", 15.24, 27.94, size=1.5)

# ---- isolation barrier (vertical dashed line)
line([(XB, 33.02), (XB, 256.54)], width=0.5, color=C_ISO, dashed=True)
text("ISOLATION BARRIER (Rev 2: >= 1 MOPP reference)", XB - 1.5, 250.19, size=1.5, rot=90, color=C_ISO, just="left bottom")
text("PC / FPGA GROUND", XB - 3.0, 36.0, size=1.5, color=C_ISO, just="right bottom")
text("STIMULATOR (floating) GROUND", XB + 3.0, 36.0, size=1.5, color=C_ISO, just="left bottom")

# ---- Row 1: stimulating path ------------------------------------------------------------------------
Box("fpga", 15.24, Y1, 40.64, H, "FPGA / PC",
    "Red Pitaya Z7020\nDAC_CMD, ENREQ,\nHEARTBEAT out;\nFAULT_N, RAILOK,\nENABLE status in.\nSoftware limits:\nsum = 0, |I| <= 5 mA,\nmax DC duration", color=C_BLK)
Box("iso1", XB - 8.89, Y1, 17.78, H, "ISO",
    "digital\nisolator\nSPI -> DAC\nstatus <-", color=C_ISO, fs=1.4)
Box("dac", 86.36, Y1, 35.56, H, "DAC + clamp",
    "command ceiling\nD3/D4 zener clamp\n+ buffer rails:\n~7 mA (G=1),\n~9 mA (G=5) [N]\nfirst current bound", color=C_PASS)
Box("pump", 129.54, Y1, 38.1, H, "Current pump",
    "INA149 Howland\n+/-100 V rails\n1 mA/V\nrail shunts RSP/RSN\n(OC sense taps)", color=C_PATH)
Box("lim", 175.26, Y1, 38.1, H, "Series limiter",
    "DN2540 pair + RLIM\n6.4-8.8 mA [N]\npassive, no supply,\nboth polarities\n< 10 mA hard limit", color=C_PASS)
Box("s1", 220.98, Y1, 30.48, H, "S1 stim switch",
    "PhotoMOS AQY214S\n400 V, Toff 0.2 ms\n[DS]\nopens with LED off\n(no HV-side supply)", color=C_PATH)
Box("head", 259.08, Y1, 38.1, H, "Participant",
    "(bench: dummy load\n1k-13k, R||C)\nSTIM electrode ->\n<- RET electrode\nTVS SMBJ100CA\nacross each line", color=C_BLK)
Box("s2", 304.8, Y1, 30.48, H, "S2 return switch",
    "PhotoMOS AQY214S\nsecond, independent\ndisconnect means\n(F07: one welded\nstill breaks loop)", color=C_PATH)
Box("rsh", 342.9, Y1, 30.48, H, "Return shunt",
    "RSHR + INA\nI_RET = 0.2 V/mA\nto mismatch, DC\ntrip and ADC", color=C_TRIP)
Box("park", 175.26 + 5.08, Y1 + H + 8.89, 27.94, 15.24, "S3 parking",
    "Form B PhotoMOS\n100k to GND when\nENABLE low: no\ncharge dump at\nswitch-on [N]", color=C_PATH, fs=1.3)

# thick stimulating path (red)
PW = 0.6
wire([boxes["fpga"].R(0.3), boxes["iso1"].L(0.4)], 0.35, C_ISO)
wire([boxes["iso1"].R(0.4), boxes["dac"].L(0.3)], 0.35, C_ISO)
label("DAC_CMD", boxes["iso1"].R(0.4)[0] + 1.27, boxes["iso1"].R(0.4)[1] - 0.8)
wire([boxes["dac"].R(), boxes["pump"].L()], PW, C_PATH)
p_out = boxes["pump"].R()
l_in = boxes["lim"].L()
wire([p_out, l_in], PW, C_PATH)
# parking tap
xpark = snap((p_out[0] + l_in[0]) / 2)
junction(xpark, p_out[1], C_PATH)
wire([(xpark, p_out[1]), (xpark, boxes["park"].T()[1])], 0.35, C_PATH)
# re-position park box so its top-centre is xpark: emit later with x adjusted
boxes["park"].x = xpark - boxes["park"].w / 2
wire([boxes["lim"].R(), boxes["s1"].L()], PW, C_PATH)
wire([boxes["s1"].R(), boxes["head"].L()], PW, C_PATH)
label("STIM", boxes["s1"].R()[0] + 1.0, boxes["s1"].R()[1] - 0.8)
wire([boxes["head"].R(), boxes["s2"].L()], PW, C_PATH)
label("RET", boxes["head"].R()[0] + 1.0, boxes["head"].R()[1] - 0.8)
wire([boxes["s2"].R(), boxes["rsh"].L()], PW, C_PATH)
# shunt to GND
g = boxes["rsh"].R()
wire([g, (g[0] + 7.62, g[1]), (g[0] + 7.62, g[1] + 7.62)], PW, C_PATH)
line([(g[0] + 4.0, g[1] + 7.62), (g[0] + 11.24, g[1] + 7.62)], 0.5)
line([(g[0] + 5.5, g[1] + 9.0), (g[0] + 9.74, g[1] + 9.0)], 0.5)
line([(g[0] + 7.0, g[1] + 10.4), (g[0] + 8.24, g[1] + 10.4)], 0.5)
text("GND (floating)", g[0] + 12.5, g[1] + 9.5, size=1.4)

# ---- Row 2: detectors (amber) ------------------------------------------------------------------------
Box("rail", 86.36, Y2, 35.56, H, "Rail supervision",
    "+/-HV UV/OV window\n+ symmetry [H]\naux +/-12, +/-9 V\nPOR 20 ms [DS]\n-> RAILOK", color=C_TRIP)
Box("oc", 129.54, Y2, 38.1, H, "Over-current trip",
    "rail shunts -> 2x INA149\n-> TLV1704 window\nItrip ~5.7 mA [N]\ncatches Q1/Q2 short\nto a rail (F03)", color=C_TRIP)
Box("ov", 175.26, Y2, 38.1, H, "Compliance / OV trip",
    "V_elec via 20M/200k\ndivider, 77-83 V [N]\nlifted electrode,\nstage saturation\n(F05/F06)", color=C_TRIP)
Box("dc", 220.98, Y2, 38.1, H, "DC / charge trip",
    "integrator on I_RET\nbaseline > 50 uA avg\nor |Q| > Q_max\n[DS5 AvL, ASSUME]\nskin burn (F08/F09)", color=C_TRIP)
Box("mm", 304.8, Y2, 38.1, H, "Mismatch trip",
    "|I_RET - I_CMD|\n> 0.4 mA, 47 us [N]\ndetached return\n(F05); D-19 open for\nshared return", color=C_TRIP)
Box("wd", 93.98, Y4, 40.64, 22.86, "Watchdog",
    "HEARTBEAT from FPGA\n-> missing-pulse\ndetector -> WD_OK\n(F01: FPGA hung or\nlink lost)", color=C_TRIP, fs=1.4)

# taps from the path into detectors
def tap_down(src_box, dst_box, f_src=0.5, f_dst=0.5, color=C_TRIP, lbl=None):
    a = src_box.B(f_src); b = dst_box.T(f_dst)
    if a[0] == b[0]:
        wire([a, b], 0.25, color)
    else:
        ym = snap((a[1] + b[1]) / 2)
        wire([a, (a[0], ym), (b[0], ym), b], 0.25, color)
    if lbl:
        label(lbl, b[0] + 1.0, b[1] - 1.5)

tap_down(boxes["pump"], boxes["oc"], 0.5, 0.5, lbl="I_SENSE(+/-)")
# OV tap from the ELECTRODE_STIM node (between s1 and head)
xo = snap(boxes["s1"].R()[0] + 4.0)
junction(xo, boxes["s1"].R()[1], C_PATH)
yov = snap(Y1 + H + 1.27)
wire([(xo, boxes["s1"].R()[1]), (xo, yov), (boxes["ov"].T(0.5)[0], yov), boxes["ov"].T(0.5)], 0.25, C_TRIP)
label("V_ELEC_DIV", boxes["ov"].T(0.5)[0] + 1.0, boxes["ov"].T(0.5)[1] - 1.5)
# RET_SHUNT to dc and mm
r = boxes["rsh"].B(0.5)
ymid = snap(r[1] + 6.35)
wire([r, (r[0], ymid)], 0.25, C_TRIP)
junction(r[0], ymid, C_TRIP)
wire([(r[0], ymid), (boxes["mm"].T(0.7)[0], ymid), boxes["mm"].T(0.7)], 0.25, C_TRIP)
wire([(r[0], ymid), (boxes["dc"].T(0.5)[0], ymid), boxes["dc"].T(0.5)], 0.25, C_TRIP)
label("RET_SHUNT", boxes["dc"].T(0.5)[0] + 1.0, boxes["dc"].T(0.5)[1] - 1.5)
# command reference into mismatch (from DAC node, delayed)
d = boxes["dac"].B(0.8)
yc = snap(Y1 + H + 4.0)
wire([d, (d[0], yc), (boxes["mm"].T(0.3)[0], yc), boxes["mm"].T(0.3)], 0.25, C_TRIP, dashed=True)
label("I_CMD (delayed reference)", d[0] + 2.0, yc - 0.8)
# HV rails into rail supervision (from the left: rails enter the board on sheet 3)
hv = boxes["rail"].L(0.4)
wire([(hv[0] - 10.16, hv[1]), hv], 0.35, C_PATH)
label("+HV / -HV / aux", hv[0] - 1.0, hv[1] - 0.8, just="right bottom")
text("(from power board J1)", hv[0] - 1.0, hv[1] + 3.0, size=1.3, just="right bottom")
# heartbeat from FPGA to watchdog: route along a corridor between row 1 and row 2
wire([boxes["fpga"].R(0.7), boxes["iso1"].L(0.8)], 0.35, C_ISO)

# ---- Row 3: latch + enable chain (blue) ---------------------------------------------------------------
Box("or", 129.54, Y3, 35.56, H, "Trip OR",
    "open-drain wired-OR\nTRIP_N = OC | OV |\nDC | MM | !RAILOK\nany one trips", color=C_LOGIC)
Box("latch", 175.26, Y3, 40.64, H, "Fault latch",
    "SR, set-dominant\n(74LVC1G74, D-10)\nPOR sets at power-up\nRESET accepted only if\nENREQ=0 & RAILOK=1\n-> FAULT_N (latched)", color=C_LOGIC)
Box("and", 228.6, Y3, 55.88, H, "Enable AND (hardwired)",
    "ENABLE = ENREQ & FAULT_N & RAILOK\n& WD_OK & ARM & ENGAGE\n74LVC gates, no firmware in the path\nloss of any term: de-energise, not latched\n(FPGA clears DAC first, then ramps)", color=C_LOGIC)
Box("drv", 297.18, Y3, 38.1, H, "Switch driver",
    "LEDs of S1, S2, S3 in\nseries from +12 V\nENABLE high: S1, S2\nclosed, S3 open\nENABLE low: S1, S2\nopen, S3 parks", color=C_LOGIC)
Box("ind", 342.9 + 7.62, Y3, 30.48, H, "Indicators",
    "ARMED  (yellow)\nENABLED (green)\nFAULT (red, latched)\nmonitor BNC I, V\n(iso amp, PC gnd)", color=C_BLK, fs=1.4)

# detectors -> OR
for nm, f in (("oc", 0.5), ("ov", 0.4), ("dc", 0.4), ("mm", 0.4)):
    a = boxes[nm].B(0.5)
    ycol = snap(Y2 + H + 7.62) if nm == "oc" else snap(Y2 + H + 5.08 + {"ov": 0, "dc": 2.54, "mm": 5.08}[nm])
    b = boxes["or"].T(f) if nm == "oc" else boxes["or"].R({"ov": 0.25, "dc": 0.5, "mm": 0.75}[nm])
    if nm == "oc":
        wire([a, b], 0.25, C_TRIP)
    else:
        wire([a, (a[0], ycol), (b[0] + 5.08 + {"ov": 0, "dc": 2.54, "mm": 5.08}[nm], ycol), (b[0] + 5.08 + {"ov": 0, "dc": 2.54, "mm": 5.08}[nm], b[1]), b], 0.25, C_TRIP)
label("OC", boxes["oc"].B(0.5)[0] + 1.0, boxes["oc"].B(0.5)[1] + 4.0)
label("OV", boxes["ov"].B(0.5)[0] + 1.0, boxes["ov"].B(0.5)[1] + 4.0)
label("DC", boxes["dc"].B(0.5)[0] + 1.0, boxes["dc"].B(0.5)[1] + 4.0)
label("MM", boxes["mm"].B(0.5)[0] + 1.0, boxes["mm"].B(0.5)[1] + 4.0)
# RAILOK: rail -> OR (as !RAILOK) and -> AND and -> latch reset gate
rk = boxes["rail"].B(0.5)
yrk = snap(Y3 + H * 0.85)
wire([rk, (rk[0], yrk), (boxes["or"].L(0.85)[0], yrk)], 0.25, C_TRIP)
label("RAILOK", rk[0] + 1.0, yrk - 0.8)
# OR -> latch
wire([boxes["or"].R(0.5) if False else boxes["or"].R(0.1), boxes["latch"].L(0.1)], 0.35, C_LOGIC)
label("TRIP_N", boxes["or"].R(0.1)[0] + 0.8, boxes["or"].R(0.1)[1] - 0.8)
# latch -> AND
wire([boxes["latch"].R(0.3), boxes["and"].L(0.3)], 0.35, C_LOGIC)
label("FAULT_N", boxes["latch"].R(0.3)[0] + 0.8, boxes["latch"].R(0.3)[1] - 0.8)
# RAILOK -> AND (corridor under row 3)
yk2 = snap(Y3 + H + 5.08)
wire([(rk[0], yrk), (rk[0], yk2), (boxes["and"].B(0.15)[0], yk2), boxes["and"].B(0.15)], 0.25, C_TRIP)
junction(rk[0], yrk, C_TRIP)
label("RAILOK", boxes["and"].B(0.15)[0] + 1.0, yk2 - 0.8)
# WD_OK -> AND (from watchdog, down the right side then along corridor yk2)
w = boxes["wd"].R(0.3)
ywd = snap(Y3 + H + 17.78)
wire([w, (w[0] + 7.62, w[1]), (w[0] + 7.62, ywd), (boxes["and"].B(0.35)[0], ywd), boxes["and"].B(0.35)], 0.25, C_TRIP)
label("WD_OK", w[0] + 9.0, ywd - 0.8)
# AND -> driver
wire([boxes["and"].R(0.3), boxes["drv"].L(0.3)], 0.35, C_LOGIC)
label("ENABLE", boxes["and"].R(0.3)[0] + 0.8, boxes["and"].R(0.3)[1] - 0.8)
# driver -> S1, S2, S3 (up the right side, corridor between row 1 and row 2)
dr = boxes["drv"].T(0.5)
ydrv = snap(Y2 - 6.35)        # corridor above row 2
xr = 386.08                   # riser on the far right
y3c = snap(Y3 - 6.35)
wire([dr, (dr[0], y3c), (xr, y3c), (xr, ydrv)], 0.25, C_LOGIC)
pk = boxes["park"].R(0.5)
xl = snap(pk[0] + 5.08)
wire([(xr, ydrv), (xl, ydrv), (xl, pk[1]), pk], 0.25, C_LOGIC)
for nm in ("s1", "s2"):
    b = boxes[nm].B(0.5)
    wire([(b[0], ydrv), b], 0.25, C_LOGIC)
    junction(b[0], ydrv, C_LOGIC)
label("LED_DRV (S1, S2, S3)", xl + 1.0, ydrv - 0.8)
label("LED_DRV", xr - 1.0, y3c - 0.8, just="right bottom")
# driver -> indicators
wire([boxes["drv"].R(0.5), boxes["ind"].L(0.5)], 0.25, C_LOGIC)
# ENREQ from FPGA via isolator to AND (route along the corridor yk2 from the left)
Box("iso2", XB - 8.89, Y3, 17.78, H, "ISO",
    "digital\nisolator\nENREQ ->\nHEARTBEAT ->\nFAULT_N <-\nRAILOK <-", color=C_ISO, fs=1.4)
e = boxes["iso2"].R(0.3)
wire([e, (boxes["and"].B(0.55)[0], e[1]) if False else (e[0] + 5.08, e[1])], 0.35, C_ISO)
yen = snap(Y3 + H + 10.16)
wire([(e[0] + 5.08, e[1]), (e[0] + 5.08, yen), (boxes["and"].B(0.55)[0], yen), boxes["and"].B(0.55)], 0.35, C_ISO)
label("ENREQ", e[0] + 6.0, yen - 0.8)
hb = boxes["iso2"].B(0.8)
wire([hb, (hb[0], boxes["wd"].L(0.3)[1]), boxes["wd"].L(0.3)], 0.25, C_ISO)
label("HEARTBEAT", hb[0] + 1.0, boxes["wd"].L(0.3)[1] - 0.8)
# status back to FPGA: FAULT_N and ENABLE to iso2 (dashed, logic colour)
st = boxes["iso2"].R(0.75)
yst = snap(Y3 + H + 12.7)
wire([boxes["latch"].B(0.3), (boxes["latch"].B(0.3)[0], yst), (st[0] + 2.54, yst), (st[0] + 2.54, st[1]), st], 0.25, C_LOGIC, dashed=True)
label("FAULT_N, RAILOK, ENABLE -> FPGA (status, read-only)", st[0] + 3.5, yst + 2.8)
wire([boxes["fpga"].B(0.95), (boxes["fpga"].B(0.95)[0], boxes["iso2"].L(0.5)[1]), boxes["iso2"].L(0.5)], 0.35, C_ISO)

# ---- Row 4: human inputs ------------------------------------------------------------------------------
Box("reset", 175.26, Y4, 45.72, 22.86, "RESET push-button",
    "on the enclosure, hardware\nonly; clears the latch; no\nsoftware reset path\n(DS5: toggle down = reset)", color=C_LOGIC, fs=1.4)
Box("arm", 228.6, Y4, 27.94, 22.86, "ARM",
    "operator key\nswitch, latching\n(DS5 'Output\nOn/Off-Reset')", color=C_LOGIC, fs=1.4)
Box("engage", 259.08 + 1.27, Y4, 27.94, 22.86, "ENGAGE",
    "participant hand\nswitch, NO,\nmomentary\n(dead-man)", color=C_LOGIC, fs=1.4)
wire([boxes["reset"].T(0.5), boxes["latch"].B(0.6)], 0.25, C_LOGIC)
label("RESET", boxes["reset"].T(0.5)[0] + 1.0, boxes["reset"].T(0.5)[1] - 1.5)
wire([boxes["arm"].T(0.5), boxes["and"].B(0.75)], 0.25, C_LOGIC)
label("ARM", boxes["arm"].T(0.5)[0] + 1.0, boxes["arm"].T(0.5)[1] - 1.5)
wire([boxes["engage"].T(0.5), boxes["and"].B(0.9)], 0.25, C_LOGIC)
label("ENGAGE", boxes["engage"].T(0.5)[0] + 1.0, boxes["engage"].T(0.5)[1] - 1.5)

# ---- Notes (left column, PC side is fine: it is text) --------------------------------------------------
Box("principles", 15.24, Y2, 35.56, 73.66, "Principles",
    "1. Single fault safe: no one\n   failure puts > 10 mA or\n   sustained DC into the\n   participant (client rule:\n   imagine everything shorted).\n"
    "2. Passive first: limiter and\n   clamp need no supply, no\n   logic (purple).\n"
    "3. De-energise to safe: the\n   switches need the LED lit to\n   conduct; any lost term opens.\n"
    "4. Two independent disconnect\n   means in the loop (S1, S2).\n"
    "5. Trips are analog hardware;\n   firmware only requests,\n   never enables.\n"
    "6. Latched faults need a human\n   at the box to clear.", color=C_NOTE, fs=1.3, lw=0.25)
Box("legend", 15.24, Y3 + 20.32, 35.56, 50.8, "Legend",
    "red     stimulating path\npurple  passive limit (no supply)\namber   detector / trip\nblue    latch + enable chain\ngreen   isolation crossing\nthick   current path\ndashed  reference / status\n\nRev 1 board has: clamp, pump,\nlimiter (DNP), S1, S2, RSHR,\nread-back. Everything else on\nthis sheet is Rev 2.", color=C_NOTE, fs=1.3, lw=0.25)

# ---- Trip table (right of row 4) ----------------------------------------------------------------------
Box("table", 297.18, Y4 - 2.54, 83.82, 33.02, "Trip summary (targets, to be confirmed on the bench)",
    "OC   |I_rail| > ~5.7 mA, ~22 us            latched\n"
    "OV   |V_elec| > 77-83 V                     latched\n"
    "DC   avg I_RET > 50 uA (idle) / Q > Q_max   latched\n"
    "MM   |I_RET - I_CMD| > 0.4 mA, ~47 us       latched\n"
    "RAIL +/-HV out of 90-110 V or asymmetric    not latched\n"
    "WD   no HEARTBEAT edge for > 10 ms [ASSUME]  not latched\n"
    "ENGAGE / ARM / ENREQ released               not latched", color=C_NOTE, fs=1.3, lw=0.25)

# emit boxes
for b in boxes.values():
    items.append(b.emit())

# =====================================================================================================
sheet = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid "{U()}")
  (paper "A3")
  (title_block
    (title "Safety loop: block schematic (planning)")
    (date "2026-11-04")
    (rev "0.1 DRAFT")
    (company "UBC ELEC 491 JY063")
    (comment 1 "DRAFT: planning sheet, not for fabrication")
    (comment 2 "Author: Weymen Koo. Text: 03_safety_plan/SAFETY_LOOP.md")
    (comment 3 "Bench prototype, dummy loads only; not a safety sign-off")
    (comment 4 "Sources: archive 4-rev1-design/DECISIONS.md, FMEA.md, DS5 manual")
  )
  (lib_symbols)
''' + "\n".join("  " + it.replace("\n", "\n  ") for it in items) + '''
  (sheet_instances (path "/" (page "1")))
)
'''
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
with open(OUT, "w") as f:
    f.write(sheet)
print("wrote", OUT, len(items), "items")
