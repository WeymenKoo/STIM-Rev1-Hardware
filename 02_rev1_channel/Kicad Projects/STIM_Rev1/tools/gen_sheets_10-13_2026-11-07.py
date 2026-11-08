#!/usr/bin/env python3
"""ONE-SHOT generator that drew sheets 10-13 of STIM_Rev1 (2026-11-07, revised 2026-11-08: two ISO7741, two ADCs, decoupling at the pins).
Kept for the record only. DO NOT RE-RUN: the .kicad_sch files are the source; re-running would restore the
pre-2026-11-07 cover / FPGA sheet / library from a backup folder that no longer exists. Needs sx.py next to it."""
import sys, os, re, uuid, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sx import parse, dump, find, first

PROJ = sys.argv[1]
ROOT_UUID = "801725e5-e50b-4629-8dff-f10f88598334"
SHEET_UUID = {
    5: "187439ae-9d02-51ae-8afd-618db504358e",
    10: "114e91be-7f72-4d1b-af60-80afd734c29a",
    11: "7c14932f-2e34-4ecb-ac99-994f2f04620f",
    12: "4b7c7ece-13b3-4546-8c13-c3483238e92d",
    13: "5d3b7a1e-2f44-4c0e-9a61-13c0f0e3a0d1",
}
FILE_UUID = {  # file-level uuid of the sheet file (kept for 10-12)
    10: "114e91be-7f72-4d1b-af60-80afd734c29a",
    11: "187439ae-9d02-51ae-8afd-618db504358e".replace("187439ae", "2b7e4c11"),
    12: "4b7c7ece-13b3-4546-8c13-c3483238e92d",
    13: SHEET_UUID[13],
}

def U(): return str(uuid.uuid4())
def f(n):
    s = ("%.4f" % n).rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"
def q(s): return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'

# --------------------------------------------------------------------------- symbols
# lib coords (y up). pins: number -> (name, type, x, y, angle, length)
SYMS = {}

def add_sym(name, body, pins, extra_graphics="", pin_names_offset=0.762, hide_pin_names=False,
            ref_at=None, val_at=None, footprint="", datasheet="", desc="", keywords="", power=False,
            ref="U"):
    SYMS[name] = dict(body=body, pins=pins, extra=extra_graphics, off=pin_names_offset, hidenames=hide_pin_names,
                      ref_at=ref_at, val_at=val_at, fp=footprint, ds=datasheet, desc=desc, kw=keywords,
                      power=power, ref=ref)

def sym_text(name, prefix=""):
    s = SYMS[name]
    bx1, by1, bx2, by2 = s["body"]
    out = []
    out.append(f'\t(symbol "{prefix}{name}"')
    if s["power"]:
        out.append('\t\t(power global)')
        out.append('\t\t(pin_numbers\n\t\t\t(hide yes)\n\t\t)')
        out.append('\t\t(pin_names\n\t\t\t(offset 0)\n\t\t\t(hide yes)\n\t\t)')
    else:
        pn = f'\t\t(pin_names\n\t\t\t(offset {f(s["off"])})' + ('\n\t\t\t(hide yes)' if s["hidenames"] else '') + '\n\t\t)'
        out.append(pn)
    out.append('\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(duplicate_pin_numbers_are_jumpers no)')
    ra = s["ref_at"] or (bx1, by2 + 2.54)
    va = s["val_at"] or (bx1, by1 - 2.54)
    def prop(k, v, at, hide=False, just="left"):
        j = f'\n\t\t\t\t(justify {just})' if just else ''
        return (f'\t\t(property "{k}" {q(v)}\n\t\t\t(at {f(at[0])} {f(at[1])} 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)'
                + ('\n\t\t\t(hide yes)' if hide else '') + f'\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}\n\t\t\t)\n\t\t)')
    if s["power"]:
        out.append(prop("Reference", "#PWR", (0, -3.81), hide=True, just=None))
        out.append(prop("Value", name, (0, 3.556), just=None))
    else:
        out.append(prop("Reference", s["ref"], ra))
        out.append(prop("Value", name, va))
    out.append(prop("Footprint", s["fp"], (0, 0), hide=True, just=None))
    out.append(prop("Datasheet", s["ds"], (0, 0), hide=True, just=None))
    out.append(prop("Description", s["desc"], (0, 0), hide=True, just=None))
    if s["kw"]:
        out.append(prop("ki_keywords", s["kw"], (0, 0), hide=True, just=None))
    # graphics unit
    out.append(f'\t\t(symbol "{name}_0_1"')
    if s["power"]:
        out.append(s["extra"])
    else:
        out.append(f'\t\t\t(rectangle\n\t\t\t\t(start {f(bx1)} {f(by2)})\n\t\t\t\t(end {f(bx2)} {f(by1)})\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)')
        if s["extra"]:
            out.append(s["extra"])
    out.append('\t\t)')
    out.append(f'\t\t(symbol "{name}_1_1"')
    for num, (pname, ptype, px, py, ang, ln) in s["pins"].items():
        out.append(f'\t\t\t(pin {ptype} line\n\t\t\t\t(at {f(px)} {f(py)} {ang})\n\t\t\t\t(length {f(ln)})\n'
                   f'\t\t\t\t(name {q(pname)}\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
                   f'\t\t\t\t(number "{num}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)')
    out.append('\t\t)')
    out.append('\t\t(embedded_fonts no)')
    out.append('\t)')
    return "\n".join(out)

TSSOP16 = "STIM_Rev1:TSSOP-16_4.4x5mm_P0.65mm"
SOIC16W = "STIM_Rev1:SOIC-16W_7.5x10.3mm_P1.27mm"

# AD5761R TSSOP-16
add_sym("AD5761R", (-12.7, -15.24, 12.7, 15.24), {
    "13": ("~{SYNC}", "input", -15.24, 10.16, 0, 2.54),
    "14": ("SCLK", "input", -15.24, 7.62, 0, 2.54),
    "12": ("SDI", "input", -15.24, 5.08, 0, 2.54),
    "10": ("SDO", "tri_state", -15.24, 2.54, 0, 2.54),
    "11": ("~{LDAC}", "input", -15.24, -2.54, 0, 2.54),
    "2": ("~{CLEAR}", "input", -15.24, -5.08, 0, 2.54),
    "3": ("~{RESET}", "input", -15.24, -7.62, 0, 2.54),
    "1": ("~{ALERT}", "open_collector", -15.24, -10.16, 0, 2.54),
    "7": ("VOUT", "output", 15.24, 7.62, 180, 2.54),
    "4": ("VREFIN/VREFOUT", "passive", 15.24, 0, 180, 2.54),
    "9": ("DNC", "no_connect", 15.24, -10.16, 180, 2.54),
    "8": ("VDD", "power_in", -2.54, 17.78, 270, 2.54),
    "15": ("DVCC", "power_in", 2.54, 17.78, 270, 2.54),
    "6": ("VSS", "power_in", -5.08, -17.78, 90, 2.54),
    "5": ("AGND", "power_in", 0, -17.78, 90, 2.54),
    "16": ("DGND", "power_in", 5.08, -17.78, 90, 2.54),
}, footprint=TSSOP16, datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/AD5761R_5721R.pdf",
   desc="16-bit multi-range voltage-output DAC, 2.5 V 2 ppm/C reference, SPI, TSSOP-16", keywords="dac spi")

# ADS8689 TSSOP-16 (PW)
add_sym("ADS8689", (-15.24, -15.24, 15.24, 15.24), {
    "7": ("AIN_P", "input", -17.78, 10.16, 0, 2.54),
    "8": ("AIN_GND", "input", -17.78, 7.62, 0, 2.54),
    "9": ("~{RST}", "input", -17.78, 5.08, 0, 2.54),
    "4": ("REFIO", "passive", -17.78, 0, 0, 2.54),
    "6": ("REFCAP", "passive", -17.78, -2.54, 0, 2.54),
    "5": ("REFGND", "passive", -17.78, -5.08, 0, 2.54),
    "12": ("SCLK", "input", 17.78, 10.16, 180, 2.54),
    "10": ("SDI", "input", 17.78, 7.62, 180, 2.54),
    "11": ("~{CS}/CONVST", "input", 17.78, 5.08, 180, 2.54),
    "13": ("SDO-0", "tri_state", 17.78, 2.54, 180, 2.54),
    "14": ("ALARM/SDO-1/GPO", "output", 17.78, -2.54, 180, 2.54),
    "15": ("RVS", "output", 17.78, -5.08, 180, 2.54),
    "2": ("AVDD", "power_in", -2.54, 17.78, 270, 2.54),
    "16": ("DVDD", "power_in", 2.54, 17.78, 270, 2.54),
    "3": ("AGND", "power_in", -2.54, -17.78, 90, 2.54),
    "1": ("DGND", "power_in", 2.54, -17.78, 90, 2.54),
}, footprint=TSSOP16, datasheet="https://www.ti.com/lit/ds/symlink/ads8689.pdf",
   desc="16-bit 100 kSPS SAR ADC, programmable bipolar/unipolar input ranges, 4.096 V reference, SPI, TSSOP-16", keywords="adc sar spi")

ISO_BARRIER = ('\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy 0 15.24) (xy 0 -15.24)\n\t\t\t\t)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type dash)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)')
add_sym("ISO7742", (-10.16, -15.24, 10.16, 15.24), {
    "3": ("INA", "input", -12.7, 7.62, 0, 2.54),
    "4": ("INB", "input", -12.7, 5.08, 0, 2.54),
    "5": ("OUTC", "output", -12.7, 0, 0, 2.54),
    "6": ("OUTD", "output", -12.7, -2.54, 0, 2.54),
    "7": ("EN1", "input", -12.7, -7.62, 0, 2.54),
    "14": ("OUTA", "output", 12.7, 7.62, 180, 2.54),
    "13": ("OUTB", "output", 12.7, 5.08, 180, 2.54),
    "12": ("INC", "input", 12.7, 0, 180, 2.54),
    "11": ("IND", "input", 12.7, -2.54, 180, 2.54),
    "10": ("EN2", "input", 12.7, -7.62, 180, 2.54),
    "1": ("VCC1", "power_in", -5.08, 17.78, 270, 2.54),
    "16": ("VCC2", "power_in", 5.08, 17.78, 270, 2.54),
    "2": ("GND1", "power_in", -7.62, -17.78, 90, 2.54),
    "8": ("GND1", "power_in", -2.54, -17.78, 90, 2.54),
    "9": ("GND2", "power_in", 2.54, -17.78, 90, 2.54),
    "15": ("GND2", "power_in", 7.62, -17.78, 90, 2.54),
}, extra_graphics=ISO_BARRIER, footprint=SOIC16W, datasheet="https://www.ti.com/lit/ds/symlink/iso7742.pdf",
   desc="4-channel 2/2 reinforced digital isolator, 5 kVrms, 100 Mbps, output enables, SOIC-16 DW", keywords="isolator")

add_sym("ISO7741", (-10.16, -15.24, 10.16, 15.24), {
    "3": ("INA", "input", -12.7, 7.62, 0, 2.54),
    "4": ("INB", "input", -12.7, 5.08, 0, 2.54),
    "5": ("INC", "input", -12.7, 2.54, 0, 2.54),
    "6": ("OUTD", "output", -12.7, -2.54, 0, 2.54),
    "7": ("EN1", "input", -12.7, -7.62, 0, 2.54),
    "14": ("OUTA", "output", 12.7, 7.62, 180, 2.54),
    "13": ("OUTB", "output", 12.7, 5.08, 180, 2.54),
    "12": ("OUTC", "output", 12.7, 2.54, 180, 2.54),
    "11": ("IND", "input", 12.7, -2.54, 180, 2.54),
    "10": ("EN2", "input", 12.7, -7.62, 180, 2.54),
    "1": ("VCC1", "power_in", -5.08, 17.78, 270, 2.54),
    "16": ("VCC2", "power_in", 5.08, 17.78, 270, 2.54),
    "2": ("GND1", "power_in", -7.62, -17.78, 90, 2.54),
    "8": ("GND1", "power_in", -2.54, -17.78, 90, 2.54),
    "9": ("GND2", "power_in", 2.54, -17.78, 90, 2.54),
    "15": ("GND2", "power_in", 7.62, -17.78, 90, 2.54),
}, extra_graphics=ISO_BARRIER, footprint=SOIC16W, datasheet="https://www.ti.com/lit/ds/symlink/iso7741.pdf",
   desc="4-channel 3/1 reinforced digital isolator, 5 kVrms, 100 Mbps, output enables, SOIC-16 DW", keywords="isolator")

add_sym("CD74HC4052", (-10.16, -15.24, 10.16, 15.24), {
    "12": ("A0", "passive", -12.7, 10.16, 0, 2.54),
    "14": ("A1", "passive", -12.7, 7.62, 0, 2.54),
    "15": ("A2", "passive", -12.7, 5.08, 0, 2.54),
    "11": ("A3", "passive", -12.7, 2.54, 0, 2.54),
    "1": ("B0", "passive", -12.7, -2.54, 0, 2.54),
    "5": ("B1", "passive", -12.7, -5.08, 0, 2.54),
    "2": ("B2", "passive", -12.7, -7.62, 0, 2.54),
    "4": ("B3", "passive", -12.7, -10.16, 0, 2.54),
    "13": ("COM_A", "passive", 12.7, 10.16, 180, 2.54),
    "10": ("S0", "input", 12.7, 2.54, 180, 2.54),
    "9": ("S1", "input", 12.7, 0, 180, 2.54),
    "6": ("~{E}", "input", 12.7, -2.54, 180, 2.54),
    "3": ("COM_B", "passive", 12.7, -7.62, 180, 2.54),
    "16": ("VCC", "power_in", 0, 17.78, 270, 2.54),
    "7": ("VEE", "power_in", -2.54, -17.78, 90, 2.54),
    "8": ("GND", "power_in", 2.54, -17.78, 90, 2.54),
}, footprint=TSSOP16, datasheet="https://www.ti.com/lit/ds/symlink/cd74hc4052.pdf",
   desc="Dual 4:1 analog multiplexer, 2-6 V, TSSOP-16", keywords="mux analog switch")

PWR_GRAPHIC = ('\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy -0.762 1.27) (xy 0 2.54)\n\t\t\t\t)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)\n'
               '\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy 0 2.54) (xy 0.762 1.27)\n\t\t\t\t)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)\n'
               '\t\t\t(polyline\n\t\t\t\t(pts\n\t\t\t\t\t(xy 0 0) (xy 0 2.54)\n\t\t\t\t)\n\t\t\t\t(stroke\n\t\t\t\t\t(width 0)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type none)\n\t\t\t\t)\n\t\t\t)')
for rail, d in (("+5V", "Power symbol creates a global label with name \"+5V\": ADC AVDD rail from U46 [13]"),
                ("+3V3", "Power symbol creates a global label with name \"+3V3\": board-side logic rail from U47 [13]")):
    add_sym(rail, (0, 0, 0, 0), {"1": ("", "power_in", 0, 0, 90, 0)}, extra_graphics=PWR_GRAPHIC, desc=d,
            keywords="global power", power=True)

# ---- existing library symbols we reuse: load from the project lib
LIB_PATH = os.path.join(PROJ, "lib", "lib_sym", "STIM_Rev1.kicad_sym")
lib_text = open(LIB_PATH).read()
lib_doc = parse(lib_text)[0]
EXISTING = {}
for s in find(lib_doc, "symbol"):
    EXISTING[s[1]] = s

def existing_pins(name):
    s = EXISTING[name]
    pins = {}
    for sub in find(s, "symbol"):
        for p in find(sub, "pin"):
            at = first(p, "at")
            pins[first(p, "number")[1]] = (first(p, "name")[1], p[1], float(at[1]), float(at[2]), int(float(at[3])), float(first(p, "length")[1]))
    return pins

def existing_cache_text(name):
    import copy
    s = copy.deepcopy(EXISTING[name])
    s[1] = "STIM_Rev1:" + name
    return dump(s, 1)

def new_cache_text(name):
    return sym_text(name, "STIM_Rev1:")

def pin_lib(name, num):
    if name in SYMS:
        return SYMS[name]["pins"][num]
    return existing_pins(name)[num]

# --------------------------------------------------------------------------- sheet builder
def xform(X, Y, rot, lx, ly):
    if rot == 0: return (X + lx, Y - ly)
    if rot == 90: return (X - ly, Y - lx)
    if rot == 180: return (X - lx, Y + ly)
    if rot == 270: return (X + ly, Y + lx)
    raise ValueError(rot)

class Sheet:
    def __init__(self, num, title, paper, file_uuid):
        self.num, self.ttl, self.paper, self.uuid = num, title, paper, file_uuid
        self.items = []
        self.used = set()
        self.instances = {}  # ref -> (lib, X, Y, rot)
        self.path = f"/{ROOT_UUID}/{SHEET_UUID.get(num, ROOT_UUID)}"

    # ---- primitives
    def wire(self, x1, y1, x2, y2):
        self.items.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def poly(self, pts, color=(255, 0, 0, 1), width=0.5, style="dash"):
        p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
        self.items.append(f'\t(polyline\n\t\t(pts\n\t\t\t{p}\n\t\t)\n\t\t(stroke\n\t\t\t(width {f(width)})\n\t\t\t(type {style})\n\t\t\t(color {color[0]} {color[1]} {color[2]} {color[3]})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def junction(self, x, y):
        self.items.append(f'\t(junction\n\t\t(at {f(x)} {f(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)')
    def nc(self, x, y):
        self.items.append(f'\t(no_connect\n\t\t(at {f(x)} {f(y)})\n\t\t(uuid "{U()}")\n\t)')
    def label(self, name, x, y, rot=0):
        just = "left bottom" if rot == 0 else ("right bottom" if rot == 180 else ("left bottom" if rot == 90 else "right bottom"))
        self.items.append(f'\t(label {q(name)}\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def hlabel(self, name, shape, x, y, rot):
        just = "left" if rot == 0 else "right"
        self.items.append(f'\t(hierarchical_label {q(name)}\n\t\t(shape {shape})\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def rect(self, x1, y1, x2, y2):
        self.items.append(f'\t(rectangle\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n\t\t(stroke\n\t\t\t(width 0.762)\n\t\t\t(type solid)\n\t\t\t(color 200 200 200 1)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def caption(self, text, x, y, w):
        self.items.append(f'\t(text_box {q(text)}\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(size {f(w)} 5.71)\n\t\t(margins 0.9525 0.9525 0.9525 0.9525)\n\t\t(stroke\n\t\t\t(width -0.0001)\n\t\t\t(type default)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(face "Times New Roman")\n\t\t\t\t(size 2.54 2.54)\n\t\t\t\t(thickness 0.508)\n\t\t\t\t(bold yes)\n\t\t\t\t(color 162 22 34 1)\n\t\t\t)\n\t\t\t(justify bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def block(self, x1, y1, x2, y2, caption):
        self.rect(x1, y1, x2, y2)
        self.caption(caption, x1, y2 - 6.35, x2 - x1)
    def title(self):
        w = 385.84 if self.paper == "A3" else 262.84
        self.items.append(f'\t(text_box {q("[%d] %s" % (self.num, self.ttl))}\n\t\t(exclude_from_sim no)\n\t\t(at 17.08 16.51 0)\n\t\t(size {f(w)} 10.16)\n\t\t(margins 0.9525 0.9525 0.9525 0.9525)\n\t\t(stroke\n\t\t\t(width -0.0001)\n\t\t\t(type default)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(face "Times New Roman")\n\t\t\t\t(size 7 7)\n\t\t\t\t(thickness 1.4)\n\t\t\t\t(bold yes)\n\t\t\t\t(color 162 22 34 1)\n\t\t\t)\n\t\t\t(justify top)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def note(self, kind, text, x, y, h, w=62):
        col = {"D": (200, 200, 200, 0.8, (0, 0, 0)), "L": (0, 0, 255, 1, (0, 0, 255)), "M": (255, 165, 0, 0.8, (0, 0, 0))}[kind[0]]
        self.items.append(f'\t(text_box {q(text)}\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(size {f(w)} {f(h)})\n\t\t(margins 1 1 1 1)\n\t\t(stroke\n\t\t\t(width {col[3]})\n\t\t\t(type solid)\n\t\t\t(color {col[0]} {col[1]} {col[2]} 1)\n\t\t)\n\t\t(fill\n\t\t\t(type color)\n\t\t\t(color 255 255 255 1)\n\t\t)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(face "Arial")\n\t\t\t\t(size 1.27 1.27)\n\t\t\t\t(color {col[4][0]} {col[4][1]} {col[4][2]} 1)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def tag(self, tagname, x, y):
        col = (0, 0, 255, 1) if tagname[0] == "L" else (200, 200, 200, 0.8)
        tc = (0, 0, 255) if tagname[0] == "L" else (0, 0, 0)
        self.items.append(f'\t(text_box {q(tagname)}\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(size 4.6 3.4)\n\t\t(margins 0.3 0.3 0.3 0.3)\n\t\t(stroke\n\t\t\t(width {col[3]})\n\t\t\t(type solid)\n\t\t\t(color {col[0]} {col[1]} {col[2]} 1)\n\t\t)\n\t\t(fill\n\t\t\t(type color)\n\t\t\t(color 255 255 255 1)\n\t\t)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(face "Arial")\n\t\t\t\t(size 1.27 1.27)\n\t\t\t\t(thickness 0.254)\n\t\t\t\t(bold yes)\n\t\t\t\t(color {tc[0]} {tc[1]} {tc[2]} 1)\n\t\t\t)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')
    def text_bold(self, text, x, y, w, size=1.905):
        self.items.append(f'\t(text_box {q(text)}\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(size {f(w)} 5.08)\n\t\t(margins 0.9525 0.9525 0.9525 0.9525)\n\t\t(stroke\n\t\t\t(width -0.0001)\n\t\t\t(type default)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(face "Arial")\n\t\t\t\t(size {f(size)} {f(size)})\n\t\t\t\t(thickness 0.254)\n\t\t\t\t(bold yes)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "{U()}")\n\t)')

    # ---- symbols
    def sym(self, lib, ref, value, X, Y, rot=0, props=None, fields=None, dnp=False, hide_value=False):
        """fields: dict name -> (x, y, angle, justify or None) for visible Reference/Value."""
        self.used.add(lib)
        self.instances[ref] = (lib, X, Y, rot)
        props = props or {}
        lines = [f'\t(symbol\n\t\t(lib_id "STIM_Rev1:{lib}")\n\t\t(at {f(X)} {f(Y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(in_pos_files yes)\n\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{U()}")']
        def prop(k, v, at, hide, just):
            j = f'\n\t\t\t\t(justify {just})' if just else ''
            return (f'\t\t(property "{k}" {q(v)}\n\t\t\t(at {f(at[0])} {f(at[1])} {at[2]})' + ('\n\t\t\t(hide yes)' if hide else '')
                    + f'\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t){j}\n\t\t\t)\n\t\t)')
        fields = fields or {}
        hidden_ref = ref.startswith("#")
        ra = fields.get("Reference", (X, Y, 0, None))
        va = fields.get("Value", (X, Y, 0, None))
        lines.append(prop("Reference", ref, ra[:3], hidden_ref, ra[3]))
        lines.append(prop("Value", value, va[:3], hide_value, va[3]))
        if lib in SYMS:
            fp, ds, desc = SYMS[lib]["fp"], SYMS[lib]["ds"], SYMS[lib]["desc"]
        else:
            ep = {p[1]: p[2] for p in find(EXISTING[lib], "property")}
            fp, ds, desc = ep.get("Footprint", ""), ep.get("Datasheet", ""), ep.get("Description", "")
        for k, v in (("Footprint", props.pop("Footprint", fp)), ("Datasheet", props.pop("Datasheet", ds)), ("Description", props.pop("Description", desc))):
            lines.append(prop(k, v, (X, Y, 0), True, None))
        for k, v in props.items():
            lines.append(prop(k, v, (X, Y, 0), True, None))
        pins = SYMS[lib]["pins"] if lib in SYMS else existing_pins(lib)
        for num in pins:
            lines.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{U()}")\n\t\t)')
        lines.append(f'\t\t(instances\n\t\t\t(project "STIM_Rev1"\n\t\t\t\t(path "{self.path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        self.items.append("\n".join(lines))

    def pin(self, ref, num):
        lib, X, Y, rot = self.instances[ref]
        p = pin_lib(lib, num)
        return xform(X, Y, rot, p[2], p[3])

    # ---- compound helpers
    pwr_n = [0]
    def power(self, rail, x, y, rot=0):
        Sheet.pwr_n[0] += 1
        ref = "#PWR%03d" % (300 + Sheet.pwr_n[0])
        # value text position: above for rot 0, below for rot 180, left/right otherwise (KiCad autoplace-like)
        if rot == 0: va = (x, y - 5.08, 0, None)
        elif rot == 180: va = (x, y + 5.08, 0, None)
        elif rot == 90: va = (x - 5.08, y, 90, None)
        else: va = (x + 5.08, y, 90, None)
        self.sym(rail, ref, rail, x, y, rot, fields={"Reference": (x, y, 0, None), "Value": va})
    def gnd(self, x, y, rot=0, name="GND"):
        Sheet.pwr_n[0] += 1
        ref = "#PWR%03d" % (300 + Sheet.pwr_n[0])
        if rot == 0: va = (x, y + 3.81, 0, None)
        elif rot == 180: va = (x, y - 3.81, 0, None)
        elif rot == 270: va = (x - 6.35, y, 90, None)   # graphic extends left; +90 cancels the symbol rotation
        else: va = (x + 6.35, y, 90, None)             # rot 90: graphic extends right
        self.sym(name, ref, name, x, y, rot, fields={"Reference": (x, y, 0, None), "Value": va})
    def flag(self, x, y):
        Sheet.pwr_n[0] += 1
        ref = "#FLG%03d" % (300 + Sheet.pwr_n[0])
        self.sym("PWR_FLAG", ref, "PWR_FLAG", x, y, 0, fields={"Reference": (x, y, 0, None), "Value": (x, y - 5.08, 0, None)})
    def tp(self, ref, name, x, y, rot=0, note="bench probe loop"):
        if rot == 0: fl = {"Reference": (x + 2.54, y - 6.604, 0, "left"), "Value": (x + 2.54, y - 4.064, 0, "left")}
        else: fl = {"Reference": (x + 2.54, y + 2.54, 0, "right"), "Value": (x + 2.54, y + 5.08, 0, "right")}
        self.sym("TestPoint", ref, name, x, y, rot, props={"Note": note}, fields=fl)
    def R(self, ref, value, x, y, rot=0, note="", dnp=False):
        p = RPARTS[value]
        props = {"MPN": p[0], "Manufacturer": p[1], "LCSC": p[2], "JLC": p[3], "Note": note, "Sim.Device": "R", "Sim.Params": "r=%s" % p[4]}
        if rot in (0, 180): fl = {"Reference": (x + 2.54, y - 1.27, 0, "left"), "Value": (x + 2.54, y + 1.27, 0, "left")}
        else: fl = {"Reference": (x, y - 3.302, 90, None), "Value": (x, y + 3.302, 90, None)}
        self.sym("R", ref, value, x, y, rot, props={"Footprint": "STIM_Rev1:R_0603_1608Metric", "Description": "resistor", **props}, fields=fl, dnp=dnp)
    def C(self, ref, value, x, y, rot=0, note="", text="right"):
        p = CPARTS[value]
        props = {"MPN": p[0], "Manufacturer": p[1], "LCSC": p[2], "JLC": p[3], "Note": note, "Sim.Device": "C", "Sim.Params": "c=%s" % p[4]}
        if text == "right": fl = {"Reference": (x + 2.54, y - 1.27, 0, "left"), "Value": (x + 2.54, y + 1.27, 0, "left")}
        else: fl = {"Reference": (x - 2.54, y - 1.27, 0, "right"), "Value": (x - 2.54, y + 1.27, 0, "right")}
        self.sym("C", ref, value, x, y, rot, props={"Footprint": p[5], "Description": "capacitor", **props}, fields=fl)
    def pin_rail(self, ref, pinnum, rail, caps, side, yr, pitch=22.86, gnd="GND"):
        """Decoupling drawn at the supply pin: stub from the pin to a rail at y = yr, caps hanging from the rail in
        order HF (nearest the pin) -> bulk, rail symbol at the far end. side = 'left' or 'right'. Negative rails
        (name starts with '-') hang the caps upwards with the ground on top."""
        x0, y0 = self.pin(ref, pinnum)
        self.wire(x0, y0, x0, yr)
        sgn = -1 if side == "left" else 1
        neg = rail.startswith("-")
        x = x0
        for i, (cref, val, note) in enumerate(caps):
            x = x0 + sgn * (10.16 + pitch * i)
            self.junction(x, yr)
            if neg:
                self.C(cref, val, x, yr - 3.81, note=note, text="right" if side == "right" else "left")
                self.gnd(x, yr - 7.62, 180, gnd)
            else:
                self.C(cref, val, x, yr + 3.81, note=note, text="right" if side == "right" else "left")
                self.gnd(x, yr + 7.62, 0, gnd)
        xend = x + sgn * 7.62
        self.wire(x0, yr, xend, yr)
        self.power(rail, xend, yr, 180 if neg else 0)

    def decap(self, ref, value, x, yc, rail, note=""):
        """vertical cap centred at yc with rail symbol above (y = yc-8.89) and GND below."""
        if rail.startswith("-"):
            self.gnd(x, yc - 8.89, 180)
            self.wire(x, yc - 8.89, x, yc - 3.81)
            self.C(ref, value, x, yc, note=note)
            self.wire(x, yc + 3.81, x, yc + 8.89)
            self.power(rail, x, yc + 8.89, 180)
        else:
            self.power(rail, x, yc - 8.89)
            self.wire(x, yc - 8.89, x, yc - 3.81)
            self.C(ref, value, x, yc, note=note)
            self.gnd(x, yc + 3.81)

    # ---- output
    def write(self, path, title_block_extra=""):
        libs = []
        for name in sorted(self.used):
            libs.append(new_cache_text(name) if name in SYMS else existing_cache_text(name))
        hdr = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{self.uuid}")\n\t(paper "{self.paper}")\n'
               f'\t(title_block\n\t\t(title {q(self.ttl)})\n\t\t(date "${{RELEASE_DATE}}")\n\t\t(rev "${{REVISION}}")\n\t\t(company "${{COMPANY}}")\n'
               '\t\t(comment 1 "PRELIMINARY: not for fabrication")\n\t\t(comment 2 "Edited in KiCad: do not regenerate")\n\t\t(comment 3 "Netlist: expected_netlist_rev1min.csv")\n\t\t(comment 4 "Not a safety sign-off; dummy loads")\n\t\t(comment 9 "${REVIEWER}")\n\t)\n')
        body = "\t(lib_symbols\n" + "\n".join(libs) + "\n\t)\n" + "\n".join(self.items) + "\n\t(embedded_fonts no)\n)\n"
        open(path, "w").write(hdr + body)

# part tables: value -> (MPN, Manufacturer, LCSC, JLC, simvalue[, footprint])
RPARTS = {
    "100k 1% 0603": ("0603WAF1003T5E", "UNI-ROYAL", "C25803", "Basic", "100000"),
    "10.0k 1% 0603": ("0603WAF1002T5E", "UNI-ROYAL", "C25804", "Basic", "10000"),
    "32.4k 1% 0603": ("0603WAF3242T5E", "UNI-ROYAL", "TBD", "Basic", "32400"),
    "17.8k 1% 0603": ("0603WAF1782T5E", "UNI-ROYAL", "TBD", "Basic", "17800"),
}
CPARTS = {
    "100n X7R 50V 0603": ("CL10B104KB8NNNC", "Samsung", "C1591", "Extended", "1e-07", "STIM_Rev1:C_0603_1608Metric"),
    "10n X7R 50V 0603": ("CL10B103KB8NNNC", "Samsung", "C1589", "Extended", "1e-08", "STIM_Rev1:C_0603_1608Metric"),
    "10u X5R 25V 0805": ("CL21A106KAYNNNE", "Samsung", "C15850", "Basic", "1e-05", "STIM_Rev1:C_0805_2012Metric"),
    "1u X5R 50V 0603": ("CL10A105KB8NNNC", "Samsung", "TBD", "Basic", "1e-06", "STIM_Rev1:C_0603_1608Metric"),
}

SRC = "Sourcing checked 2026-11-07 [LCSC API / DigiKey CA web]: "

# =========================================================================== SHEET 10
def sheet10():
    s = Sheet(10, "Interface - SPI Isolator", "A3", FILE_UUID[10])
    s.title()
    s.block(53.34, 40.64, 208.28, 185.42, "Digital isolators: control / safety (U43, default low) and chip selects (U44, default high)")
    s.text_bold("FPGA side: J3, +3V3_FPGA / GND_FPGA", 55.88, 43.18, 60)
    s.text_bold("Board side: +3V3 / GND", 172.72, 43.18, 34)
    XI = 139.7
    chips = [("U43", 71.12, "ISO7741FDWR", "C485810", "Default output LOW (F): ENABLE, SCLK, MOSI -> board; reverse channel D = FAULT_N board -> FPGA (spare, pulled up by R86). With J3 unplugged or the FPGA unpowered ISO_ENABLE is LOW within 0.3 us (PhotoMOS open) and FAULT_N to the FPGA reads LOW = asserted when the board is off. " + SRC + "LCSC C485810 (675 pcs, $1.77); DigiKey CA 0 pcs, backorder to 2027-04 - LCSC / JLCPCB only",
              [("INA", "ENABLE", "input"), ("INB", "SPI_SCLK", "input"), ("INC", "SPI_MOSI", "input")],
              [("OUTA", "ISO_ENABLE", "output"), ("OUTB", "ISO_SCLK", "output"), ("OUTC", "ISO_MOSI", "output")],
              ("FAULT_N", "ISO_FAULT_N")),
             ("U44", 132.08, "ISO7741DWR", "C571196", "Default output HIGH: CS_DAC, CS_ADC, CS_ADC2 -> board (all three converters deselected when the FPGA side is unpowered); reverse channel D = MISO. " + SRC + "LCSC C571196 (9767 pcs, $1.52), DigiKey CA 3906 pcs, C$5.64",
              [("INA", "SPI_CS_DAC", "input"), ("INB", "SPI_CS_ADC", "input"), ("INC", "SPI_CS_ADC2", "input")],
              [("OUTA", "ISO_CS_DAC", "output"), ("OUTB", "ISO_CS_ADC", "output"), ("OUTC", "ISO_CS_ADC2", "output")],
              None)]
    pn = {"INA": "3", "INB": "4", "INC": "5", "OUTD": "6", "EN1": "7", "OUTA": "14", "OUTB": "13", "OUTC": "12", "IND": "11", "EN2": "10"}
    for ref, YI, val, lcsc, note, left, right, fault in chips:
        s.sym("ISO7741", ref, val, XI, YI, 0, props={"MPN": val, "Manufacturer": "Texas Instruments", "LCSC": lcsc, "JLC": "Extended", "Note": note},
              fields={"Reference": (XI - 13.97, YI + 18.415, 0, "right bottom"), "Value": (XI - 13.97, YI + 20.955, 0, "right bottom")})
        for p, net, shape in left:
            x, y = s.pin(ref, pn[p]); s.wire(101.6, y, x, y); s.hlabel(net, shape, 101.6, y, 180)
        for p, net, shape in right:
            x, y = s.pin(ref, pn[p]); s.wire(x, y, 185.42, y); s.hlabel(net, shape, 185.42, y, 0)
        if fault:  # reverse channel D spare: board-side input labelled, FPGA-side output labelled (TP38)
            x, y = s.pin(ref, "6"); s.wire(x, y, 116.84, y); s.label(fault[0], 116.84, y, 180)
            x, y = s.pin(ref, "11"); s.wire(x, y, 160.02, y); s.label(fault[1], 160.02, y, 0)
        else:      # reverse channel D = MISO
            x, y = s.pin(ref, "6"); s.wire(101.6, y, x, y); s.hlabel("SPI_MISO", "output", 101.6, y, 180)
            x, y = s.pin(ref, "11"); s.wire(x, y, 185.42, y); s.hlabel("ISO_MISO", "input", 185.42, y, 0)
        s.nc(*s.pin(ref, "7"))
        x, y = s.pin(ref, "10"); s.wire(x, y, 160.02, y); s.label("ISO_EN2", 160.02, y, 0)
        # supplies: one 100 nF at each VCC pin, rail symbol beyond the cap
        c1, c2 = ("C100", "C101") if ref == "U43" else ("C102", "C103")
        s.pin_rail(ref, "1", "+3V3_FPGA", [(c1, "100n X7R 50V 0603", "at %s VCC1 (pin 1) to GND1" % ref)], "left", YI - 21.59, gnd="GND_FPGA")
        s.pin_rail(ref, "16", "+3V3", [(c2, "100n X7R 50V 0603", "at %s VCC2 (pin 16) to GND2" % ref)], "right", YI - 24.13)
        xa, ya = s.pin(ref, "2"); xb, yb = s.pin(ref, "8")
        s.wire(xa, ya, xa, YI + 20.32); s.wire(xb, yb, xb, YI + 20.32); s.wire(xa, YI + 20.32, xb, YI + 20.32)
        s.gnd((xa + xb) / 2, YI + 20.32, 0, "GND_FPGA"); s.junction((xa + xb) / 2, YI + 20.32)
        xa, ya = s.pin(ref, "9"); xb, yb = s.pin(ref, "15")
        s.wire(xa, ya, xa, YI + 20.32); s.wire(xb, yb, xb, YI + 20.32); s.wire(xa, YI + 20.32, xb, YI + 20.32)
        s.gnd((xa + xb) / 2, YI + 20.32); s.junction((xa + xb) / 2, YI + 20.32)
    for y1, y2 in ((43.18, 55.88), (86.36, 116.84), (147.32, 180.34)):
        s.poly([(XI, y1), (XI, y2)])
    s.tag("D1", 109.22, 85.09); s.tag("L1", 128.27, 43.18); s.tag("M1", 109.22, 162.56)
    # FPGA-side test points
    s.power("+3V3_FPGA", 63.5, 160.02); s.wire(63.5, 160.02, 63.5, 165.1); s.tp("TP34", "+3V3_FPGA", 63.5, 165.1, 180)
    s.tp("TP35", "GND_FPGA", 80.01, 165.1, 0); s.wire(80.01, 165.1, 80.01, 170.18); s.gnd(80.01, 170.18, 0, "GND_FPGA")
    s.label("FAULT_N", 93.98, 160.02, 0); s.wire(93.98, 160.02, 93.98, 165.1); s.tp("TP38", "FAULT_N", 93.98, 165.1, 180, note="FPGA-side spare status line (U43 OUTD, default LOW when the board is off); no J3 pin, see D3")
    s.tag("L2", 55.88, 149.86)
    # ---- Block B: J5 + JP7
    s.block(213.36, 40.64, 297.18, 140.97, "Post-isolation header J5 and bypass jumper JP7")
    JX, JY = 248.92, 73.66
    s.sym("Conn_02x08_Odd_Even", "J5", "ISO_BYPASS 2x8 2.54mm", JX, JY, 0,
          props={"MPN": "A2541WV-2x8P [ASSUME]", "Manufacturer": "CJT(Changjiang Connectors)", "LCSC": "", "JLC": "Extended",
                 "Note": "Same part as J3. Board-side copy of J3 (pins 3-15 = ISO_SCLK, ISO_MOSI, ISO_MISO, ISO_CS_DAC, ISO_CS_ADC, ISO_ENABLE, ISO_CS_ADC2; even pins = board GND; pin 1 NC, never the FPGA 3.3 V). To bypass the isolators: close JP7 (side-2 outputs Hi-Z), move the ribbon from J3 to J5. GND_FPGA is then tied to GND through the cable: no isolation."},
          fields={"Reference": (JX + 1.27, JY - 11.43, 0, None), "Value": (JX + 1.27, JY + 12.7, 0, None)})
    nets = [None, "ISO_SCLK", "ISO_MOSI", "ISO_MISO", "ISO_CS_DAC", "ISO_CS_ADC", "ISO_ENABLE", "ISO_CS_ADC2"]
    for i in range(8):
        x, y = s.pin("J5", str(2 * i + 1))
        if nets[i] is None: s.nc(x, y)
        else: s.wire(x, y, 231.14, y); s.label(nets[i], 231.14, y, 180)
        x, y = s.pin("J5", str(2 * i + 2)); s.wire(x, y, 264.16, y)
        if 0 < i < 7: s.junction(264.16, y)
    y0 = s.pin("J5", "2")[1]; y7 = s.pin("J5", "16")[1]
    s.wire(264.16, y0, 264.16, y7 + 5.08); s.junction(264.16, y7); s.gnd(264.16, y7 + 5.08)
    s.tag("D2", 275.59, 60.96)
    s.sym("Jumper", "JP7", "JP 1x2", 248.92, 109.22, 0, props={"Note": "ISO BYPASS: closed = EN2 of U43 and U44 low = all board-side isolator outputs high-impedance, so the FPGA can drive the bus directly on J5. OPEN for normal (isolated) operation. Open by default."},
          fields={"Reference": (248.92, 105.918, 0, None), "Value": (248.92, 112.522, 0, None)})
    x, y = s.pin("JP7", "1"); s.wire(x, y, 236.22, y); s.label("ISO_EN2", 236.22, y, 180)
    x, y = s.pin("JP7", "2"); s.wire(x, y, 261.62, y); s.wire(261.62, y, 261.62, y + 5.08); s.gnd(261.62, y + 5.08)
    s.text_bold("JP7 OPEN = isolated (normal)", 222.25, 124.46, 60, 1.524)
    s.text_bold("JP7 CLOSED = bypass, ribbon on J5", 222.25, 128.27, 60, 1.524)
    # ---- Block C: FAULT_N pull-up
    s.block(213.36, 146.05, 297.18, 185.42, "Spare reverse channel: FAULT_N pull-up")
    s.power("+3V3", 254.0, 154.94); s.wire(254.0, 154.94, 254.0, 158.75)
    s.R("R86", "100k 1% 0603", 254.0, 162.56, note="ISO_FAULT_N idle high (not faulted) until Rev 2 logic drives it low")
    s.wire(254.0, 166.37, 254.0, 171.45); s.label("ISO_FAULT_N", 254.0, 171.45, 0)
    s.tag("D3", 275.59, 152.4)
    # ---- notes
    s.note("D1", "DESIGN NOTE D1:\nTwo TI ISO7741 (3 forward + 1 reverse channel each, 5 kVrms reinforced, SOIC-16 DW, output enables EN1/EN2). U43 = ISO7741F (default LOW): ENABLE, SCLK, MOSI. U44 = ISO7741 (default HIGH): CS_DAC, CS_ADC, CS_ADC2, MISO back. Six forward lines fit exactly; the CS lines sit on the default-HIGH part so nothing is selected and nothing drives MISO when the FPGA side is unpowered. Side 1 runs from +3V3_FPGA (J3 pin 1), side 2 from +3V3 [13]; both 2.25-5.5 V. One 100 nF at each VCC pin (C100-C103).", 53.34, 193.04, 22)
    s.note("D2", "DESIGN NOTE D2:\nDefault states with J3 unplugged or the FPGA unpowered: ISO_SCLK / ISO_MOSI / ISO_ENABLE LOW (PhotoMOS open), ISO_CS_DAC / ISO_CS_ADC / ISO_CS_ADC2 HIGH. EN1 / EN2 open = outputs enabled (internal pull-up, DS pin table). JP7 pulls both EN2 low for the J5 bypass; the side-1 outputs (MISO, FAULT_N) stay enabled, which is fine because J3 is then unplugged.", 53.34, 217.17, 17)
    s.note("D3", "DESIGN NOTE D3:\nSpare: U43 channel D, board -> FPGA, named FAULT_N. Board-side input ISO_FAULT_N is pulled up by R86 (idle = not faulted); the FPGA-side output goes to TP38 only, because J3 has no free pin (15 = CS_ADC2 since the two-ADC decision of 2026-11-08). Rev 2: J3 2x10 for FAULT_N and any PGOOD / OK lines.", 119.38, 193.04, 17)
    s.note("L1", "LAYOUT NOTE L1:\nIsolation barrier under the two isolators: no copper on any layer across the gap except the isolator bodies; GND_FPGA pour under J3 and side 1 only. Spacing per IEC 60664-1 for the working voltage set by the +/-100 V electrode side (hv-insulation rule in STIM_Rev1.kicad_dru); the DW body gives 8 mm creepage. C100-C103 at the VCC pins, via at the pad.", 119.38, 212.09, 17)
    s.note("L2", "LAYOUT NOTE L2:\nJ5 next to the isolators on the board side; same orientation as J3 (pin 1 marked) so the ribbon moves straight across. J3 and J5 must not be plugged at the same time with JP7 open.", 119.38, 231.14, 9.2)
    s.note("M1", "MISC NOTE M1:\nBring-up: with JP7 OPEN and J3 unplugged, check ISO_ENABLE LOW (TP on [8]) and ISO_CS_* HIGH on J5. Then plug J3: FPGA toggles ENABLE, check ISO_ENABLE follows (DS 11 ns). Fallback if the SPI link misbehaves: JP7 CLOSED, ribbon on J5, FPGA drives the converters directly (3.3 V logic on both sides). Sourcing: ISO7741FDWR is LCSC / JLCPCB only today (DigiKey CA backorder); ISO7742FDWR (C2862403, DigiKey 3352 pcs) is the drop-in if it runs out: same footprint, 2 forward channels, so move SCLK to U44 and MISO to... no: keep U44 as drawn and use ISO7742F for ENABLE + MOSI only if SCLK can share U44's INC with GPIO moved to a jumper. Decide at order time.", 185.42, 193.04, 26)
    s.write(os.path.join(PROJ, "interface-spi-isolator.kicad_sch"))
    return s

# =========================================================================== SHEET 11
def sheet11():
    s = Sheet(11, "Interface - DAC Command", "A3", FILE_UUID[11])
    s.title()
    s.block(139.7, 60.96, 261.62, 154.94, "AD5761R 16-bit DAC, +/-5 V range, internal 2.5 V reference")
    X, Y = 198.12, 109.22
    s.sym("AD5761R", "U40", "AD5761RBRUZ", X, Y, 0,
          props={"MPN": "AD5761RBRUZ-RL7", "Manufacturer": "Analog Devices", "LCSC": "C515877", "JLC": "Extended",
                 "Note": "16-bit DAC, +/-5 V range on VDD/VSS = +/-12 V (bipolar ranges need VDD 4.75-16.5 V, VSS -16.5-0 V [DS]). SDO shared with the ADC on ISO_MISO (tri-state while SYNC high [DS]). LDAC tied low: output updates on the SYNC rising edge. " + SRC + "LCSC C515877 (592 pcs, $13.03; tube C404015 20 pcs), DigiKey AD5761RBRUZ-RL7 (751 pcs, C$25.57)"},
          fields={"Reference": (X - 16.51, Y - 16.51, 0, "right bottom"), "Value": (X - 16.51, Y - 13.97, 0, "right bottom")})
    for num, net, shape in (("13", "ISO_CS_DAC", "input"), ("14", "ISO_SCLK", "input"), ("12", "ISO_MOSI", "input"), ("10", "ISO_MISO", "output")):
        x, y = s.pin("U40", num); s.wire(167.64, y, x, y); s.hlabel(net, shape, 167.64, y, 180)
    x, y = s.pin("U40", "11"); s.wire(x, y, 175.26, y); s.gnd(175.26, y, 270)
    for num, net in (("2", "DAC_CLEAR"), ("3", "DAC_RESET"), ("1", "DAC_ALERT")):
        x, y = s.pin("U40", num); s.wire(x, y, 175.26, y); s.label(net, 175.26, y, 180)
    x, y = s.pin("U40", "7"); s.wire(x, y, 248.92, y); s.hlabel("DAC_CMD", "output", 248.92, y, 0)
    x, y = s.pin("U40", "4"); s.wire(x, y, 243.84, y); s.junction(223.52, y)
    s.C("C106", "10n X7R 50V 0603", 223.52, y + 3.81, note="VREFOUT noise cap, 10 nF per DS pin table; at pin 4")
    s.gnd(223.52, y + 7.62)
    s.tp("TP32", "DAC_VREF", 243.84, y, 180, note="2.500 V internal reference [DS]")
    s.nc(*s.pin("U40", "9"))
    # decoupling at the pins: bulk at the rail end, 100 nF nearest the pin
    s.pin_rail("U40", "8", "+12V", [("C107", "100n X7R 50V 0603", "at U40 VDD (pin 8)"), ("C108", "10u X5R 25V 0805", "VDD bulk")], "left", Y - 33.02)
    s.pin_rail("U40", "15", "+3V3", [("C111", "100n X7R 50V 0603", "at U40 DVCC (pin 15)")], "right", Y - 33.02)
    s.pin_rail("U40", "6", "-12V", [("C109", "100n X7R 50V 0603", "at U40 VSS (pin 6)"), ("C110", "10u X5R 25V 0805", "VSS bulk")], "left", Y + 33.02)
    x, y = s.pin("U40", "5"); s.wire(x, y, x, 132.08); s.gnd(x, 132.08)
    x, y = s.pin("U40", "16"); s.wire(x, y, x, 129.54); s.gnd(x, 129.54)
    s.tag("D1", 143.51, 64.77); s.tag("D2", 254.0, 121.92); s.tag("M1", 254.0, 64.77); s.tag("L1", 254.0, 139.7)
    # Block B: control-pin pull-ups
    s.block(139.7, 160.02, 261.62, 205.74, "Control-pin pull-ups")
    for i, (ref, net) in enumerate((("R80", "DAC_CLEAR"), ("R81", "DAC_RESET"), ("R82", "DAC_ALERT"))):
        x = 149.86 + 20.32 * i
        s.power("+3V3", x, 170.18); s.wire(x, 170.18, x, 173.99)
        s.R(ref, "10.0k 1% 0603", x, 177.8, note="pull-up (pin has an internal pull-up too [DS]); CLEAR/RESET can be driven low by Rev 2 safety logic" if ref != "R82" else "ALERT is open-drain active low: pull-up needed to read it")
        s.wire(x, 181.61, x, 187.96); s.label(net, x, 187.96, 0)
    s.wire(190.5, 187.96, 203.2, 187.96); s.tp("TP33", "DAC_ALERT", 203.2, 187.96, 180, note="low = over-temperature, output short or brown-out [DS]; high after a control-register write")
    s.tag("D3", 215.9, 173.99)
    s.note("D1", "DESIGN NOTE D1:\nAD5761R (16-bit, 8 software ranges, 2.5 V 2 ppm/C reference). Range +/-5 V -> DAC_CMD +/-5 V -> +/-5 mA at G = 1, so RG3 on [6] must be DNP when the DAC drives the channel (RG3 fitted = G = 5 is for the Red Pitaya +/-1 V outputs). Alternative kept in software: range +/-3 V (RA = 100) with RG3 fitted. 1 LSB = 153 uV = 0.15 uA at G = 1 [H]. Output amp drives 2 kOhm / 1 nF [DS]; RS1 1k + D3/D4 on [6] is the load.", 53.34, 60.96, 22)
    s.note("D2", "DESIGN NOTE D2:\nSupplies: VDD = +12V, VSS = -12V (bipolar range needs VDD 4.75-16.5 V, VSS -16.5-0 V) [DS]; DVCC = +3V3 so the logic matches the isolator side 2 and the FPGA in bypass. Decoupling drawn in the order it is laid out: rail -> 10 uF bulk -> 100 nF at the pin. VREFOUT: 10 nF to AGND per the pin table (not more: start-up time 3.5 ms [DS]). TP32 reads 2.500 V.", 53.34, 86.36, 17)
    s.note("D3", "DESIGN NOTE D3:\nControl pins: LDAC tied to DGND (DAC register updates when SYNC rises). CLEAR, RESET pulled to +3V3 (internal pull-ups exist; the 10k make the nets probe-able and let Rev 2 safety logic drive them). CLEAR (falling edge) sets the output to zero / mid / full scale per the control register: a candidate hard-wired clear from ISO_ENABLE low in Rev 2. ALERT open-drain, TP33.", 53.34, 106.68, 17)
    s.note("L1", "LAYOUT NOTE L1:\nC107 / C109 / C111 at pins 8, 6, 15 with the via at the pad, C108 / C110 next to them on the rail side; C106 at pin 4 with a short return to AGND. AGND and DGND on the same ground plane under the part. DAC_CMD short to RS1 on [6].", 53.34, 127.0, 11.4)
    s.note("M1", "MISC NOTE M1:\nSPI: 24-bit frames, SYNC low, data on SCLK falling edge, SCLK <= 50 MHz [DS]; write the control register first (range, CLR mode, overrange off), then input register 0x8000 = 0 V. Read-back: SDO drives ISO_MISO only while SYNC is low. Bring-up (R5 on the acceptance table): code sweep vs DMM on TP13 DAC_CMD. " + SRC + "see U40 field notes.", 53.34, 140.97, 17)
    s.write(os.path.join(PROJ, "interface-dac-command.kicad_sch"))
    return s

# =========================================================================== SHEET 12
def sheet12():
    s = Sheet(12, "Interface - ADC Read-back", "A3", FILE_UUID[12])
    s.title()
    ADC_NOTE = ("16-bit SAR, 100 kSPS, 1 MOhm resistive input (no kickback, +/-20 V tolerant), range set by register: 0-5.12 V (78 uV/LSB). "
                "AVDD = +5V (4.75-5.25 V [DS]), DVDD = +3V3 so the SPI matches the FPGA in bypass. %s " + SRC + "LCSC C135986 (997 pcs, $5.48), DigiKey 296-45226-1-ND (1889 pcs, C$11.49)")
    def adc_block(x0, ref, signal, cs_net, caps, tps, caption, what):
        s.block(x0, 60.96, x0 + 142.24, 152.4, caption)
        AX, AY = x0 + 78.74, 109.22
        s.sym("ADS8689", ref, "ADS8689IPWR", AX, AY, 0,
              props={"MPN": "ADS8689IPWR", "Manufacturer": "Texas Instruments", "LCSC": "C135986", "JLC": "Extended", "Note": ADC_NOTE % what},
              fields={"Reference": (AX - 19.05, AY + 18.415, 0, "right bottom"), "Value": (AX - 19.05, AY + 20.955, 0, "right bottom")})
        c_ain, c_refio, c_refcap10, c_refcap1, c_avdd1, c_avdd10, c_dvdd = caps
        tp_ain, tp_ref = tps
        # analog input: hier label, TP, 10 nF to ground on the way to AIN_P
        xa, ya = s.pin(ref, "7")
        s.wire(x0 + 15.24, ya, xa, ya); s.hlabel(signal, "input", x0 + 15.24, ya, 180)
        s.junction(x0 + 25.4, ya); s.tp(tp_ain, ref + "_AIN", x0 + 25.4, ya, 0, note="ADC input, 0.57-2.75 V normal")
        s.junction(x0 + 38.1, ya); s.C(c_ain, "10n X7R 50V 0603", x0 + 38.1, ya - 3.81, note="AIN_P to AIN_GND at pins 7-8 [DS pin table]", text="right"); s.gnd(x0 + 38.1, ya - 7.62, 180)
        x, y = s.pin(ref, "8"); s.wire(x, y, AX - 22.86, y); s.gnd(AX - 22.86, y, 270)
        x, y = s.pin(ref, "9"); s.wire(x, y, AX - 25.4, y); s.label("ADC_RST", AX - 25.4, y, 180)
        x, y = s.pin(ref, "4"); s.wire(x, y, AX - 73.66, y); s.junction(AX - 63.5, y)
        s.C(c_refio, "10u X5R 25V 0805", AX - 73.66, y + 3.81, note="REFIO: >= 4.7 uF to REFGND [DS]", text="right"); s.gnd(AX - 73.66, y + 7.62)
        s.tp(tp_ref, ref + "_REFIO", AX - 63.5, y, 0, note="4.096 V internal reference [DS]")
        x, y = s.pin(ref, "6"); s.wire(x, y, AX - 43.18, y)
        s.junction(AX - 25.4, y); s.C(c_refcap1, "1u X5R 50V 0603", AX - 25.4, y + 3.81, note="REFCAP: 1 uF closest to pin 6 [DS]", text="left"); s.gnd(AX - 25.4, y + 7.62)
        s.C(c_refcap10, "10u X5R 25V 0805", AX - 43.18, y + 3.81, note="REFCAP: 10 uF, ESR < 0.2 Ohm [DS]", text="left"); s.gnd(AX - 43.18, y + 7.62)
        x, y = s.pin(ref, "5"); s.wire(x, y, AX - 20.32, y); s.gnd(AX - 20.32, y)
        for num, net, shape in (("12", "ISO_SCLK", "input"), ("10", "ISO_MOSI", "input"), ("11", cs_net, "input"), ("13", "ISO_MISO", "output")):
            x, y = s.pin(ref, num); s.wire(x, y, AX + 35.56, y); s.hlabel(net, shape, AX + 35.56, y, 0)
        s.nc(*s.pin(ref, "14")); s.nc(*s.pin(ref, "15"))
        s.pin_rail(ref, "2", "+5V", [(c_avdd1, "1u X5R 50V 0603", "at %s AVDD (pin 2) [DS]" % ref), (c_avdd10, "10u X5R 25V 0805", "AVDD bulk [DS]")], "left", AY - 33.02)
        s.pin_rail(ref, "16", "+3V3", [(c_dvdd, "1u X5R 50V 0603", "at %s DVDD (pin 16) [DS]" % ref)], "right", AY - 33.02)
        x, y = s.pin(ref, "3"); s.wire(x, y, x, 132.08); s.gnd(x, 132.08)
        x, y = s.pin(ref, "1"); s.wire(x, y, x, 129.54); s.gnd(x, 129.54)
    adc_block(40.64, "U41", "I_RETURN_ADC", "ISO_CS_ADC", ("C112", "C113", "C114", "C115", "C116", "C117", "C118"), ("TP30", "TP31"),
              "ADC 1, U41: return current I_RETURN_ADC = VMID + 0.2 V/mA", "Reads I_RETURN_ADC (0.66-2.66 V at -/+5 mA): 0.39 uA/LSB [H].")
    adc_block(190.5, "U42", "V_ELEC_ADC", "ISO_CS_ADC2", ("C119", "C126", "C127", "C128", "C129", "C130", "C131"), ("TP39", "TP40"),
              "ADC 2, U42: electrode voltage V_ELEC_ADC = VMID + V_elec / 101", "Reads V_ELEC_ADC (VMID + V_elec/101, 0.57-2.75 V at +/-110 V): 7.9 mV/LSB on the electrode [H]. Second chip select on J3 pin 15.")
    s.tag("D1", 44.45, 64.77); s.tag("L1", 177.8, 64.77); s.tag("D2", 194.31, 64.77); s.tag("M1", 327.66, 64.77); s.tag("D3", 44.45, 142.24)
    # Block C: shared RST pull-up
    s.block(40.64, 154.94, 182.88, 195.58, "Shared ADC reset pull-up")
    x = 55.88
    s.power("+3V3", x, 162.56); s.wire(x, 162.56, x, 166.37); s.R("R85", "10.0k 1% 0603", x, 170.18, note="RST pull-up for U41 and U42; a probe loop or Rev 2 logic can reset both ADCs")
    s.wire(x, 173.99, x, 180.34); s.label("ADC_RST", x, 180.34, 0)
    s.note("D1", "DESIGN NOTE D1:\nTwo ADS8689, one per read-back signal, on the shared isolated SPI with their own chip selects (ISO_CS_ADC on J3 pin 11, ISO_CS_ADC2 on J3 pin 15, both on the default-HIGH isolator U44). I and V are sampled in the same instant, there is no analog switch in the path and the firmware is the same driver twice (decision 2026-11-08, replaces the single ADC + CD74HC4052 mux). VMID_REF is a DC constant (LM4040 0.1 % x 1 % divider): measure it once on TP29 [9] and subtract in software; it is not digitised.", 40.64, 203.2, 22)
    s.note("D2", "DESIGN NOTE D2:\nRange 0-5.12 V (1.25 x VREF): VMID + 0.2 V/mA uses 13-52 % of full scale, 0.39 uA/LSB, noise-free ~13 bits [DS SNR 92 dB]; V_elec 7.9 mV/LSB. The input is a 1 MOhm resistive divider rated +/-20 V [DS], so a saturated OPA4192 on [9] needs no clamp. Rev 2 option: use the bipolar +/-2.56 V range and drop the VMID adder on [9].", 106.68, 203.2, 17)
    s.note("D3", "DESIGN NOTE D3:\nSupplies drawn at the pins in layout order: +5V -> 10 uF -> 1 uF -> AVDD; +3V3 -> 1 uF -> DVDD [DS 8.3.1]. AVDD must be 4.75-5.25 V; DVDD could be 5 V as well, but 3.3 V keeps the SPI at Red Pitaya levels for the J5 bypass and matches the isolator side 2 and the DAC DVCC. Reference: internal 4.096 V, 10 uF on REFIO, 1 uF nearest REFCAP then 10 uF, returned to REFGND [DS]. RST shared, pulled up by R85; GPO / RVS not used (NC). SDO-0 is tri-state while CS is high, so both ADCs and the DAC share ISO_MISO [DS].", 106.68, 222.25, 22)
    s.note("L1", "LAYOUT NOTE L1:\nPer ADC: 1 uF then 10 uF at REFCAP (pin 6), 10 uF at REFIO (pin 4), returns to REFGND (pin 5) and the plane under the part; 1 uF at AVDD and DVDD, via at the pad; 10 nF across pins 7-8. Keep I_RETURN_ADC / V_ELEC_ADC from [9] away from the SPI traces; route the bus on the digital side of both parts. AGND, DGND, REFGND: one plane.", 172.72, 203.2, 17)
    s.note("M1", "MISC NOTE M1:\nFirmware: after reset write RANGE_SEL_REG = 0b1011 (0-1.25 x VREF) to both; conversions by CS low/high, 32-bit frame, data in the top 16 bits [DS]; never assert both chip selects at once. Read-back check R4: DMM on TP30 / TP39 vs code; TP31 / TP40 = 4.096 V. " + SRC + "see U41 / U42 field notes.", 172.72, 222.25, 17)
    s.write(os.path.join(PROJ, "interface-adc-readback.kicad_sch"))
    return s

# =========================================================================== SHEET 13
def sheet13():
    s = Sheet(13, "Power - Converter Rails", "A4", FILE_UUID[13])
    s.title()
    def branch(x0, uref, rail, rtop, rtop_ref, rbot_ref, cin, cnr, cout, tpref, vout_txt, note):
        UX, UY = x0 + 67.31, 53.34
        s.sym("TPS7A4901", uref, "TPS7A4901", UX, UY, 0,
              props={"Note": note, "MPN": "TPS7A4901DGNR", "Manufacturer": "Texas Instruments", "LCSC": "", "JLC": "Extended", "Description": "TPS7A4901DGNR %s LDO" % vout_txt},
              fields={"Reference": (UX - 10.16, UY - 7.62 - 3.556, 0, "left bottom"), "Value": (UX - 10.16, UY - 7.62 - 1.016, 0, "left bottom")})
        xin, yin = s.pin(uref, "8")
        px = x0 + 12.7
        s.power("+12V_IN", px, yin - 5.08); s.wire(px, yin - 5.08, px, yin); s.wire(px, yin, xin, yin)
        # CIN
        cx = x0 + 25.4
        s.junction(cx, yin); s.wire(cx, yin, cx, yin + 3.81); s.C(cin, "10u X5R 25V 0805", cx, yin + 7.62, note="%s input" % uref); s.gnd(cx, yin + 11.43)
        # EN tied to IN
        xen, yen = s.pin(uref, "5"); s.wire(xen, yen, xen - 7.62, yen); s.wire(xen - 7.62, yen, xen - 7.62, yin); s.junction(xen - 7.62, yin)
        # NR cap
        xnr, ynr = s.pin(uref, "6"); s.wire(xnr, ynr, xnr - 10.16, ynr); s.wire(xnr - 10.16, ynr, xnr - 10.16, ynr + 3.81)
        s.C(cnr, "10n X7R 50V 0603", xnr - 10.16, ynr + 7.62, note="NR/SS, as C34 on U30"); s.gnd(xnr - 10.16, ynr + 11.43)
        # GND + EP
        xg, yg = s.pin(uref, "4"); xe, ye = s.pin(uref, "9")
        s.wire(xg, yg, xg, yg + 2.54); s.wire(xe, ye, xe, ye + 2.54); s.wire(xg, yg + 2.54, xe, ye + 2.54); s.junction((xg + xe) / 2, yg + 2.54); s.gnd((xg + xe) / 2, yg + 2.54)
        # NC pins
        s.nc(*s.pin(uref, "3")); s.nc(*s.pin(uref, "7"))
        # OUT rail
        xo, yo = s.pin(uref, "1"); xend = xo + 33.02
        s.wire(xo, yo, xend, yo); s.hlabel(rail, "passive", xend, yo, 0)
        # divider
        rx = xo + 5.08
        s.junction(rx, yo); s.wire(rx, yo, rx, yo + 3.81); s.R(rtop_ref, rtop, rx, yo + 7.62, note="FB top: Vout = 1.188 V x (1 + R/10.0k) [H, D-01 method]")
        s.wire(rx, yo + 11.43, rx, yo + 16.51); s.R(rbot_ref, "10.0k 1% 0603", rx, yo + 20.32); s.gnd(rx, yo + 24.13)
        xfb, yfb = s.pin(uref, "2"); s.wire(xfb, yfb, xfb + 2.54, yfb); s.wire(xfb + 2.54, yfb, xfb + 2.54, yo + 13.97); s.wire(xfb + 2.54, yo + 13.97, rx, yo + 13.97); s.junction(rx, yo + 13.97)
        # COUT
        cox = xo + 22.86
        s.junction(cox, yo); s.wire(cox, yo, cox, yo + 3.81); s.C(cout, "10u X5R 25V 0805", cox, yo + 7.62, note="%s output, X5R 10 uF (ceramic-stable LDO)" % uref); s.gnd(cox, yo + 11.43)
        # TP
        tx = xo + 27.94
        s.junction(tx, yo); s.tp(tpref, rail, tx, yo, 0)
        return UX
    s.block(19.05, 35.56, 146.05, 96.52, "+5 V LDO U46: ADC AVDD")
    branch(19.05, "U46", "+5V", "32.4k 1% 0603", "R91", "R92", "C120", "C121", "C122", "TP36", "+5 V",
           "1.188 V x (1 + 32.4k/10.0k) = 5.04 V [H]; feeds U41 AVDD (~15 mA) [DS]; from +12V_IN: (12 - 5) x 15 mA = 0.1 W. Same part as U30/U31: no new extended type; LCSC number still open (see U30)")
    s.block(152.4, 35.56, 279.4, 96.52, "+3.3 V LDO U47: isolator side 2, ADC / DAC logic, mux")
    branch(152.4, "U47", "+3V3", "17.8k 1% 0603", "R93", "R94", "C123", "C124", "C125", "TP37", "+3.3 V",
           "1.188 V x (1 + 17.8k/10.0k) = 3.30 V [H]; feeds U43-U45 side 2, U41 DVDD, U40 DVCC, U42 (~25 mA) [DS, ASSUME]; from +12V_IN: (12 - 3.3) x 25 mA = 0.22 W, PowerPAD to GND")
    s.tag("D1", 22.86, 39.37); s.tag("M1", 156.21, 39.37); s.tag("L1", 100.33, 39.37)
    s.note("D1", "DESIGN NOTE D1:\n+5V and +3V3 are new rails for the converters and the isolator board side (added 2026-11-07). Both TPS7A4901 (as U30), fed from +12V_IN (the raw J2 input, same GND) rather than the A1212S +12V so U32's 83 mA budget is untouched [H: existing +12V load ~30 mA + 40 mA would be close]. FB: R91/R92 and R93/R94 by the D-01 method; 10 nF NR/SS, 10 uF X5R in and out as on sheet [4]. LCSC numbers for 32.4k / 17.8k 0603 to confirm (TBD in the fields).", 19.05, 101.6, 20)
    s.note("M1", "MISC NOTE M1:\nBring-up order: these rails before anything digital (R5 in the acceptance table): TP36 = 5.04 +/- 0.1 V, TP37 = 3.30 +/- 0.07 V with J3 unplugged. +12V_IN now carries ~+40 mA extra: check the bench supply limit and D8.", 85.09, 101.6, 13)
    s.note("L1", "LAYOUT NOTE L1:\nSame rules as sheet [4] L1: PowerPAD (pin 9) to GND with vias, CIN / COUT / NR cap at the pins. Place U47 near the isolators (side 2) and U46 near U41.", 85.09, 117.0, 11.4)
    s.write(os.path.join(PROJ, "power-converter-rails.kicad_sch"))
    return s

# =========================================================================== patches
def patch_cover():
    p = os.path.join(PROJ, "STIM_Rev1.kicad_sch")
    t = open(p).read()
    # [5]: grow, add GPIO pin
    t = t.replace('(at 38.1 101.6)\n\t\t(size 45.72 30.48)', '(at 38.1 101.6)\n\t\t(size 45.72 33.02)', 1)
    assert '(size 45.72 33.02)' in t
    pin5 = ('\t\t(pin "SPI_CS_ADC2" output\n\t\t\t(at 83.82 129.54 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify right)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n' % U())
    # insert before the ENABLE pin's closing of sheet [5]: find the ENABLE pin at 83.82 125.73
    m = re.search(r'\t\t\(pin "ENABLE" output\n\t\t\t\(at 83\.82 125\.73 0\).*?\n\t\t\)\n', t, re.S)
    assert m
    t = t[:m.end()] + pin5 + t[m.end():]
    # [10]: grow, add pins
    t = t.replace('(at 99.06 101.6)\n\t\t(size 63.5 30.48)', '(at 99.06 101.6)\n\t\t(size 63.5 33.02)', 1)
    assert '(size 63.5 33.02)' in t
    m = re.search(r'\t\t\(pin "ISO_ENABLE" output\n\t\t\t\(at 162\.56 125\.73 0\).*?\n\t\t\)\n', t, re.S)
    assert m
    pins10 = ('\t\t(pin "SPI_CS_ADC2" input\n\t\t\t(at 99.06 129.54 180)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n' % U()
              + '\t\t(pin "ISO_CS_ADC2" output\n\t\t\t(at 162.56 129.54 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify right)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n' % U())
    t = t[:m.end()] + pins10 + t[m.end():]
    # [12]: add ISO_GPIO pin
    m = re.search(r'\t\t\(pin "ISO_CS_ADC" input\n\t\t\t\(at 309\.88 168\.91 180\).*?\n\t\t\)\n', t, re.S)
    assert m
    pin12 = ('\t\t(pin "ISO_CS_ADC2" input\n\t\t\t(at 309.88 172.72 180)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n' % U())
    t = t[:m.end()] + pin12 + t[m.end():]
    # [11]: add ISO_MISO output pin
    m = re.search(r'\t\t\(pin "DAC_CMD" output\n\t\t\t\(at 233\.68 106\.68 0\).*?\n\t\t\)\n', t, re.S)
    assert m
    pin11 = ('\t\t(pin "ISO_MISO" output\n\t\t\t(at 233.68 110.49 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify right)\n\t\t\t)\n\t\t\t(uuid "%s")\n\t\t)\n' % U())
    t = t[:m.end()] + pin11 + t[m.end():]
    # [12]: VMID_REF no longer enters the ADC sheet (two ADCs read I and V only)
    m = re.search(r'\t\t\(pin "VMID_REF" input\n\t\t\t\(at 309\.88 157\.48 180\).*?\n\t\t\)\n', t, re.S)
    assert m; t = t[:m.start()] + t[m.end():]
    m = re.search(r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy 284\.48 157\.48\) \(xy 309\.88 157\.48\)\n.*?\n\t\)\n', t, re.S)
    assert m; t = t[:m.start()] + t[m.end():]
    m = re.search(r'\t\(label "VMID_REF"\n\t\t\(at 285\.75 157\.48 0\).*?\n\t\)\n', t, re.S)
    assert m; t = t[:m.start()] + t[m.end():]
    nc = Sheet(1, "", "A3", ROOT_UUID); nc.nc(284.48, 157.48); t = t[:t.rindex("\t(sheet_instances")] + "\n".join(nc.items) + "\n" + t[t.rindex("\t(sheet_instances"):]
    # new items: wires, labels, sheet 13, power symbols
    s = Sheet(1, "", "A3", ROOT_UUID); s.path = "/" + ROOT_UUID
    s.wire(83.82, 129.54, 99.06, 129.54); s.label("SPI_CS_ADC2", 85.09, 129.54, 0)
    s.wire(162.56, 129.54, 173.99, 129.54); s.label("ISO_CS_ADC2", 173.99, 129.54, 180)
    s.wire(309.88, 172.72, 298.45, 172.72); s.label("ISO_CS_ADC2", 298.45, 172.72, 0)
    s.wire(233.68, 110.49, 243.84, 110.49); s.label("ISO_MISO", 243.84, 110.49, 180)
    s.wire(271.78, 71.12, 279.4, 71.12); s.power("+5V", 279.4, 71.12)
    s.wire(271.78, 74.93, 289.56, 74.93); s.power("+3V3", 289.56, 74.93)
    sheet13 = ('\t(sheet\n\t\t(at 220.98 66.04)\n\t\t(size 50.8 15.24)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 255 255 194 1)\n\t\t)\n'
               f'\t\t(uuid "{SHEET_UUID[13]}")\n'
               '\t\t(property "Sheetname" "[13] Power - Converter Rails"\n\t\t\t(at 220.98 65.278 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.524 1.524)\n\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
               '\t\t(property "Sheetfile" "power-converter-rails.kicad_sch"\n\t\t\t(at 220.98 81.864 0)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n'
               f'\t\t(pin "+5V" passive\n\t\t\t(at 271.78 71.12 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify right)\n\t\t\t)\n\t\t\t(uuid "{U()}")\n\t\t)\n'
               f'\t\t(pin "+3V3" passive\n\t\t\t(at 271.78 74.93 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify right)\n\t\t\t)\n\t\t\t(uuid "{U()}")\n\t\t)\n'
               f'\t\t(instances\n\t\t\t(project "STIM_Rev1"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(page "13")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
    new = "\n".join(s.items) + "\n" + sheet13 + "\n"
    # lib cache: add +5V, +3V3 to cover lib_symbols
    cache = new_cache_text("+5V") + "\n" + new_cache_text("+3V3") + "\n"
    i = t.index("\t(lib_symbols\n") + len("\t(lib_symbols\n")
    t = t[:i] + cache + t[i:]
    # insert new items before (sheet_instances
    j = t.rindex("\t(sheet_instances")
    t = t[:j] + new + t[j:]
    # power note text
    t = t.replace('POWER: rails leave [3] and [4] as ports;', 'POWER: rails leave [3], [4] and [13] as ports;')
    t = t.replace('isolator [10] -> DAC [11] -> clamp [6] -> pump [7] -> limiter [8] -> sense [9] -> ADC [12] -> back over ISO_MISO.',
                  'isolator [10] -> DAC [11] -> clamp [6] -> pump [7] -> limiter [8] -> sense [9] -> ADCs [12] -> back over ISO_MISO; VMID_REF is read once on TP29.')
    open(p, "w").write(t)

def patch_fpga():
    p = os.path.join(PROJ, "interface-fpga.kicad_sch")
    t = open(p).read()
    m = re.search(r'\t\(no_connect\n\t\t\(at 121\.92 107\.95\)\n\t\t\(uuid "[^"]+"\)\n\t\)\n', t)
    assert m, "no_connect at J3 pin 15 not found"
    s = Sheet(5, "", "A4", SHEET_UUID[5])
    s.wire(121.92, 107.95, 111.76, 107.95); s.hlabel("SPI_CS_ADC2", "output", 111.76, 107.95, 180)
    t = t[:m.start()] + "\n".join(s.items) + "\n" + t[m.end():]
    old = "15 spare GPIO for the safety logic (NC now)"
    assert old in t
    t = t.replace(old, "15 SPI_CS_ADC2 (3.3 V, active low: chip select of the second ADC U42 on [12] through U44 on [10]; no spare pin left, see [10] D3)")
    t = t.replace("(ICD_J3 said no power on J3: decide and update the ICD)", "(ICD_J3 said no power on J3: decide and update the ICD). J5 on [10] is the board-side twin of this header for the isolator bypass")
    t = t.replace("one SPI bus, two chip selects (DAC [11], ADC [12]); subtract VMID_REF from both read-back channels in software.", "one SPI bus, three chip selects (DAC [11], two ADCs [12]); subtract the once-measured VMID_REF (TP29) from both read-back channels in software.")
    open(p, "w").write(t)

def patch_lib():
    t = open(LIB_PATH).read()
    add = "\n".join(sym_text(n) for n in ("AD5761R", "ADS8689", "ISO7741", "CD74HC4052", "+5V", "+3V3"))
    k = t.rstrip().rindex(")")
    t = t[:k] + add + "\n)\n"
    open(LIB_PATH, "w").write(t)

def patch_pro():
    p = os.path.join(PROJ, "STIM_Rev1.kicad_pro")
    t = open(p).read()
    t = t.replace('"SHEET_NAME_13": "......................................"', '"SHEET_NAME_13": "Power - Converter Rails"')
    t = t.replace('      "[12] Interface - ADC Read-back"\n    ]\n  ]', '      "[12] Interface - ADC Read-back"\n    ],\n    [\n      "%s",\n      "[13] Power - Converter Rails"\n    ]\n  ]' % SHEET_UUID[13])
    open(p, "w").write(t)

if __name__ == "__main__":
    # backups
    bk = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backup")
    os.makedirs(bk, exist_ok=True)
    for fn in ("STIM_Rev1.kicad_sch", "interface-fpga.kicad_sch", "STIM_Rev1.kicad_pro", "interface-spi-isolator.kicad_sch",
               "interface-dac-command.kicad_sch", "interface-adc-readback.kicad_sch"):
        if not os.path.exists(os.path.join(bk, fn)):
            shutil.copy(os.path.join(PROJ, fn), os.path.join(bk, fn))
        else:
            shutil.copy(os.path.join(bk, fn), os.path.join(PROJ, fn))  # idempotent: start from the original
    if not os.path.exists(os.path.join(bk, "STIM_Rev1.kicad_sym")):
        shutil.copy(LIB_PATH, os.path.join(bk, "STIM_Rev1.kicad_sym"))
    else:
        shutil.copy(os.path.join(bk, "STIM_Rev1.kicad_sym"), LIB_PATH)
    lib_text = open(LIB_PATH).read()
    sheet10(); sheet11(); sheet12(); sheet13()
    patch_cover(); patch_fpga(); patch_lib(); patch_pro()
    print("done")
