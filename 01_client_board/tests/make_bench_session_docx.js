// Bench session sheet v2 — equipment-specific (MCLD 3042 bench + DHO804/DG1022/Fluke 45), paired with bench_rig.py.
// Build:  cd 01_client_board/tests && NODE_PATH=<dir with node_modules> node make_bench_session_docx.js
// Writes ../BENCH-SESSION_30V.docx (the only sheet; v1 deleted 2026-11-04). Images come from the test folders next to this script.
const fs = require("fs"), path = require("path");
const D = require("docx");
const { LineRuleType, Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ImageRun, PageBreak, HeadingLevel,
  AlignmentType, ShadingType, Header, Footer, PageNumber } = D;
const IMG = __dirname + "/"; const FIG = path.join(__dirname, "..", "bench", "figs") + "/";
const OUT = path.join(__dirname, "..", "BENCH-SESSION_30V.docx");
const W = 9360;
const BODY = 22, SMALL = 20, LINE = 360;  // 11 pt body, 10 pt tables, 1.5 line spacing
const f = (t, o = {}) => new TextRun({ text: t, font: "Arial", size: o.size || BODY, bold: o.bold, italics: o.it, color: o.color });
const P = (t, o = {}) => new Paragraph({ children: Array.isArray(t) ? t : [f(t, o)], spacing: { lineRule: LineRuleType.AUTO, line: o.line || LINE, after: o.after ?? 160, before: o.before ?? 0 }, alignment: o.align || AlignmentType.JUSTIFIED });
let sec = 0, sub = 0, fig = 0;
const H1 = (t) => { sec++; sub = 0; return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: `${sec}. ${t}`, font: "Arial", size: 28, bold: true, color: "000000" })], spacing: { before: 360, after: 200, line: LINE }, keepNext: true }); };
const H2 = (t) => { sub++; return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: `${sec}.${sub} ${t}`, font: "Arial", size: 24, bold: true, color: "000000" })], spacing: { before: 280, after: 140, line: LINE }, keepNext: true }); };
const sh = (fill) => ({ type: ShadingType.CLEAR, fill, color: "auto" });
const cell = (t, w, o = {}) => new TableCell({ width: { size: w, type: WidthType.DXA }, shading: o.fill ? sh(o.fill) : undefined, margins: { top: 50, bottom: 50, left: 100, right: 100 },
  children: (Array.isArray(t) ? t : [t]).map(x => new Paragraph({ spacing: { after: 0, line: 276 }, children: [f(x, { bold: o.bold, size: o.size || SMALL, it: o.it, color: o.color })] })) });
function table(cols, rows, opts = {}) {
  const k = W / cols.reduce((a, c) => a + c[1], 0); cols = cols.map(c => [c[0], Math.round(c[1] * k)]);
  const hdr = new TableRow({ tableHeader: true, children: cols.map((c) => cell(c[0], c[1], { bold: true, fill: "E7E6E6" })) });
  const body = rows.map(r => new TableRow({ cantSplit: true, children: r.map((x, i) => cell(x, cols[i][1], { fill: (opts.blank && opts.blank.includes(i)) ? "FFFFFF" : (opts.simcol && opts.simcol.includes(i) ? "F2F2F2" : undefined), it: opts.simcol && opts.simcol.includes(i) })) }));
  return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: cols.map(c => c[1]), rows: [hdr, ...body] });
}
const spacer = () => new Paragraph({ spacing: { after: 120 }, children: [] });
const img = (name, wIn, ratio, base) => { const p = (base || IMG) + name; if (!fs.existsSync(p)) return P(`[figure ${name} missing]`, { it: true, color: "C00000" }); const b = fs.readFileSync(p); const w = wIn || 6.2; return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80, line: 240, lineRule: LineRuleType.AUTO }, keepNext: true, children: [new ImageRun({ type: "png", data: b, transformation: { width: w * 96, height: w * 96 * (ratio || 1.11) } })] }); };
const brk = () => new Paragraph({ children: [new PageBreak()] });
const line = (label) => P([f(label + "  ", { size: BODY }), f("_".repeat(Math.max(10, 80 - label.length)), { size: BODY, color: "808080" })], { after: 120, align: AlignmentType.LEFT });
const bul = (t) => new Paragraph({ children: [f("•  " + t)], spacing: { after: 40, line: LINE }, indent: { left: 360, hanging: 360 }, alignment: AlignmentType.JUSTIFIED });
const chk = (t) => new Paragraph({ children: [f("☐  " + t)], spacing: { after: 40, line: LINE }, indent: { left: 360, hanging: 360 } });
const mono = (t) => new Paragraph({ spacing: { after: 0, line: 276 }, indent: { left: 360 }, children: [new TextRun({ text: t, font: "Courier New", size: 18 })] });
const cmd = (t) => new Paragraph({ spacing: { before: 60, after: 160, line: 276 }, indent: { left: 360 }, shading: sh("F2F2F2"), children: [f("Script:  ", { bold: true, size: SMALL }), new TextRun({ text: t, font: "Courier New", size: 18 })] });
const cap = (t) => { fig++; return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240, line: 276 }, children: [f(`Figure ${fig}. `, { bold: true, size: SMALL }), f(t, { size: SMALL })] }); };
const RC = [["Quantity", 3300], ["Expected [L] ±30 V", 2500], ["Bench [B] (write here)", 3040], ["Tol. / Pass ☐", 1600]];
const rt = (rows) => table(RC, rows, { simcol: [1], blank: [2] });
const T = (...a) => table(...a);

const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 120 }, children: [new TextRun({ text: "Client STIM Board Bench Session Record", font: "Arial", size: 36, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80, line: LINE }, children: [f("Acceptance tests A1, A2, A5b, A4, A3 and A7 at ±30 V — simulation versus bench", { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80, line: LINE }, children: [f("JY063 Multi-Channel Neural Interface for Immersive VR · UBC ELEC 491 · Team JY · Weymen Koo", { size: SMALL, color: "444444" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480, line: LINE }, children: [f("Revision 2026-11-04 · MCLD 3042 bench equipment with a Rigol DHO804 · companion script bench/bench_rig.py", { size: SMALL, color: "444444" })] }),
  H1("Session identification"),
  P("Fill in before power is applied. Every number written in this record is a bench value [B]; grey italic values are LTspice predictions [L] from the 2026-10-27 model runs and are provided for comparison only."),
  table([["Field", 2600], ["", 7840]], [
    ["Date / location", "____________   MCLD 3042 (3rd-year lab), bench no. ____"],
    ["Operator(s)", ""],
    ["Board", "client STIM board (STIM.SchDoc 2026-10-16), S/N: ______   DPAK markings: Q2 top = ________  Q1 bottom = ________"],
    ["Rails", "Xantrex XPH 35-4T, bench unit S/N ______: output 1 = +30.0 V, output 2 = −30.0 V, both I-limit 50 mA (set with output OFF, read on the right meter), outputs floating, out1(−) joined to out2(+) = GND → J3 pin 2"],
    ["Generator", "Rigol DG1022 (bench) via USB, HiZ, Vpp ☐   —or—  FG085 ☐ (Vpp field, fixed 50 Ω, set 0 V before connecting)"],
    ["Scope / probes", "Rigol DHO804 S/N ______ via USB ☐ / LAN ☐, 4 × 10× probes, all grounds on J2. preflight run on ______ (date)"],
    ["DMM precision", "Fluke 45 (bench) S/N ______, RATE S (5 digits), leads zeroed ☐"],
    ["DMM second", "Brymen BM235 (rail current −)"],
    ["Load resistors", "RL1 nominal 1.00 kΩ, measured: ________ Ω     RL2 nominal 2.2 kΩ, measured: ________ Ω   (Fluke 45 Ω)"],
    ["Laptop", "bench_rig.py check ☐ lists DHO8 + DG1022      session_log.csv started ☐"],
  ], { blank: [1] }),
  H2("Probe points (STIM.SchDoc)"),
  table([["Node", 1500], ["Where to clip (never bare tips on SOIC pins — clips or soldered wires)", 8940]], [
    ["VCC+ / VCC−", "F1 / F2 board side, or J3 pins 1 / 3 (3-pos Micro-Fit: 1 = VCC+, 2 = GND, 3 = VCC−)"],
    ["GND", "J3 pin 2, J2, J5 GND — all scope grounds on J2"],
    ["VP (V+)", "C2 1 µF lead that is NOT on GND  (= Q2 emitter, U2 pin 7, U1 pin 7)"],
    ["VN (V−)", "C3 1 µF lead that is NOT on GND  (= Q1 emitter, U2 pin 4, U1 pin 4)"],
    ["OUT", "D1–D2 junction = top end of R7 1 k  (U2 INA149 pin 6)"],
    ["LOAD", "J1 electrode connector = bottom end of R7  (U1 pin 3)"],
    ["REF", "U1 pin 6 (op-amp output; also U2 pins 1 and 5)"],
    ["INPUT", "J4 BNC centre (generator goes here) = D3/D4 junction = U2 pin 3. J5 screw terminal is the same net"],
    ["Q2 / Q1 base", "R2–R3 junction / R4–R5 junction (DMM only, test 1a)"],
  ]),
  H2("Before power (tick all)"),
  chk("Laptop: `python3 bench_rig.py check` shows the DHO804 and the DG1022. preflight was run at home (decode OK, generator edge written on sheet 5)."),
  chk("Xantrex: both outputs OFF; output 1 preset 30.0 V, output 2 preset 30.0 V; both current limits 50 mA; out1(−) wired to out2(+) and to J3 pin 2."),
  chk("Fluke 45 in series with the VCC+ lead (mA, 300 mA range for power-up), BM235 in series with the VCC− lead (mA)."),
  chk("RL1 between J1 and J2. Generator BNC on J4, generator output OFF / 0 V. No electrodes, no humans in the loop."),
  chk("Scope probes on LOAD, OUT, VP, VN; grounds on J2 only. Probe clips not touching anything else; check with the DMM that VP–VN clips are not shorted."),
  chk("This sheet printed. tests/bench/ folder empty or from a previous run renamed."),
  H2("Rules"),
  bul("Both rails on and off together: two fingers on the two Xantrex output buttons. Never one rail alone for more than the press (A7 sim: ~6.6 mA while one rail is missing at ±30 V — test 6 does it on purpose, nothing else should)."),
  bul("Generator to 0 V before changing the load or the wiring — the script does this at every swap. OUT swings to a rail if the load opens with a command applied."),
  bul("Rail current > 15 mA at idle → both outputs OFF, do not debug live. The script stops itself if you type > 15."),
  bul("The Fluke 45 is the only meter that resolves ±1 %. The BM235 is for rail current only. The Xantrex meters (10 mA) are not readings."),
  bul("Every number written here is tagged [B]. Grey italic numbers are [L] from generic op-amp macromodels; the ones marked “validates the model” are the ones that matter."),
  H2("Wiring"),
  mono("Xantrex out1 (+30 V) -- Fluke 45 mA -- J3.1 VCC+"),
  mono("Xantrex out1 (-) ---+"),
  mono("Xantrex out2 (+) ---+-- GND -- J3.2 / J2 (fixture GND post)"),
  mono("Xantrex out2 (-30 V) -- BM235 mA -- J3.3 VCC-"),
  mono("DG1022 -- BNC -- J4 INPUT          RL fixture: J1 (LOAD) -- J2 (GND)"),
  mono("Scope CH1 LOAD  CH2 OUT->REF  CH3 VP  CH4 VN   grounds on the GND post"),
  mono("Laptop USB -> DHO804 + DG1022  (USB ground = earth = scope ground = J2)"),
  spacer(),
  H2("Running order and time (script commands on each sheet)"),
  table([["#", 500], ["Test", 3000], ["Changes from previous", 4700], ["Time", 1100], ["Done ☐", 1140]],
    [["0", "preflight (at home)", "no board: probe-comp decode check, generator flatness + edge", "10 min", ""],
     ["1", "A1 bias / bootstrap window", "— (1d onset sweep and 1e rail sweep inside)", "40 min", ""],
     ["2", "A2 DC accuracy", "generator to DC; Fluke 45 to INPUT / LOAD", "10 min", ""],
     ["3", "A5b load change", "pull fixture link, Fluke 45 in series; swap fixture once", "5 min", ""],
     ["4", "A4 frequency response", "CH2 to INPUT; scripted sweep", "3 min", ""],
     ["5", "A3 step response", "scripted single-shot, square 0 / 2 V", "5 min", ""],
     ["6", "A7 rail loss (optional)", "Xantrex output buttons on prompt", "10 min", ""]], { blank: [4] }),
];


const kit = [
  brk(),
  H1("Harnesses, fixtures and kit (made and checked at home)"),
  img("bench_wiring.png", 6.0, 490/680, FIG),
  cap("Bench wiring. Coral = power path, teal = signal and measurement. Rail ammeters sit at the Xantrex posts. All probe grounds on the fixture GND post."),
  img("harnesses.png", 6.0, 554/680, FIG),
  cap("Harness and fixture mockups. A: J3 → Xantrex. B: load fixture, one per resistor, with the series link for A5b. C: test loops at the five probe nodes."),
  H2("A. Power harness (make 1)"),
  P("3-pin Molex Micro-Fit plug on J3 (1 = VCC+, 2 = GND, 3 = VCC−, from STIM.SchDoc) → ~60 cm twisted triple → 4 mm bananas red / black / blue, GND banana stackable. Short banana jumper out1(−) ↔ out2(+). The Fluke 45 and BM235 go between the Xantrex posts and the red / blue bananas, not inside the harness. Micro-Fit needs a crimp tool: ask the client for the cable they already use, or pre-crimped Micro-Fit leads + housing (Digi-Key, next day)."),
  H2("B. Load fixtures (make 2)"),
  P("J1 mate → 2-pin link → RL → J2 mate, with a GND post (wire loop or turret) at the J2 end and a LOAD loop at the J1 end. RL = 1.00 kΩ and 2.2 kΩ, 0.1 %, ≥ 0.25 W. Pull the link to put the Fluke 45 in series (A5b). Swapping loads = unplug one fixture, plug the other. Write the measured RL on each fixture; those are --rl / --rl2. Confirm the J1/J2 connector type with the client and get two mates."),
  H2("C. Test loops (with the client's OK)"),
  P("30 AWG loops tacked at VP (C2 lead not on GND), VN (C3 lead not on GND), OUT (R7 top), LOAD (R7 bottom), REF (U1 pin 6). INPUT is J4. If no permission: Pomona micro-grabbers on component ends only, never SOIC pins, probe leads taped down."),
  H2("Bring"),
  table([["Item", 3600], ["Note", 6840]], [
    ["DHO804 + adapter + 4 × 10× probes + USB cable", "preflight run at home with this exact cable"],
    ["Laptop + charger + USB-B cable for the DG1022", "small USB hub if short on ports"],
    ["BM235", "optional: rail currents are equal when the load current averages to zero; Fluke 45 on VCC+ is enough"],
    ["Board, 2 load fixtures, power harness, GND jumper", ""],
    ["4 banana–banana leads, 2 banana–minigrabber leads", "do not count on the lab's"],
    ["Spare F1 / F2 fuses", "read the marking on the board first"],
    ["ESD strap, screwdriver, Kapton, zip ties, this sheet, pen", ""],
    ["From the lab", "Xantrex XPH 35-4T, Fluke 45, DG1022, BNC–BNC cable"],
  ]),
  H2("At home before the session (~30 min, tick all)"),
  chk("Continuity: each harness end to end; J3 pin 1 → F1 pad, pin 3 → F2 pad, pin 2 → J2 on the board (unpowered)."),
  chk("Unpowered resistance with the Fluke: VCC+ → GND ______ Ω, VCC− → GND ______ Ω, VCC+ → VCC− ______ Ω. Very low or a short → do not power."),
  chk("RL1 measured ______ Ω, RL2 measured ______ Ω, written on the fixtures."),
  chk("python3 bench_rig.py preflight passed (decode OK, generator edge noted) with the DHO804 and FG085 --gen manual."),
  chk("Client emailed: J3 cable loan, J1/J2 connector part / two mates, permission to tack test loops."),
];

const tests = [];
// ---------------- A1
tests.push([
  H1("Test 1 — A1  Bias point and bootstrap window"),
  P([f("Question. ", { bold: true }), f("Does the floating op-amp supply (VP–VN window) form at ±30 V, and can the pump deliver 2 mA and 5 mA? Decides the working current for every test after it, and measures the Q1/Q2 emitter-follower drops (the transistor question).")]),
  P([f("Probes. ", { bold: true }), f("CH1 LOAD (J1 / bottom of R7) · CH2 OUT (D1–D2 junction / top of R7) · CH3 VP (C2 lead that is not GND) · CH4 VN (C3 lead that is not GND) · all probe grounds on J2. Fluke 45 in series with the VCC+ lead (mA), BM235 in series with the VCC− lead (mA). ~40 min.")]),
  cmd("python3 bench_rig.py a1 --rl <RL1> --onset   (add --rails 35 for a ±35 V point; --rails 35 40 50 only with a second dual supply)"),
  H2("1a. Power-up, no signal (generator OFF) — script prompts for the DMM values, reads the scope itself"),
  rt([
    ["Rail current + / − (Fluke 45 / BM235 in series)", "~3.5–5 mA each", "", "> 15 mA → OFF"],
    ["VCC+ / VCC− vs GND (Fluke 45, J3 pins 1 / 3)", "+30.0 / −30.0 V", "", "—"],
    ["VP / VN vs GND (scope mean)", "+2.5 / −2.4 V", "", "±1 V"],
    ["OUT / LOAD vs GND", "≈ 0 / 0 V", "", "—"],
    ["Window VP − VN", "4.97 V", "", "±2 V  ☐"],
    ["Q2 Vbase (R2/R3 junction) − VP", "+0.65 V (NPN follower, as modelled)", "", "record"],
    ["Q1 Vbase (R4/R5 junction) − VN", "−0.65 V (PNP follower, as modelled)", "", "record"],
    ["LOAD ripple (AC, 50 mV/div, 1 µs/div): Vpp / f", "none [L]; TI models ~1 MHz", "", "record"],
  ]),
  P("Sign of Vbase − Vemitter wrong, or |Vbe| ≫ 0.7 V → the fitted transistor is not what the model assumes. Write the DPAK markings here and carry on; the window numbers decide, not the part.", { it: true }),
  line("Q2 marking / Q1 marking"),
  H2("1b. 2 mA run (2 Vpk 300 Hz) — script reads at the positive current peak; CH2 moves OUT → REF (U1 pin 6) when prompted"),
  rt([
    ["I_load pk+ / pk−  (V(LOAD) ÷ RL)", "2.000 / −2.000 mA", "", "±1 %  ☐"],
    ["OUT at I pk+", "4.00 V", "", "±0.2 V"],
    ["VP / VN at I pk+", "+6.0 / +1.1 V", "", "±1 V"],
    ["REF − VN  min  (CH2 on REF)", "0.92 V  ← validates the model", "", "record"],
    ["VP − REF  min", "1.05 V", "", "record"],
    ["Window VP − VN  avg", "4.97 V", "", "±2 V  ☐"],
    ["Rail current + / −", "5.2 / 5.2 mA", "", "±20 %  ☐"],
  ]),
  img("A1-bias-bootstrap/A1_30V_2mA.png", 3.5),
  cap("Expected 2 mA waveforms [L]. Script saves A1_30V_2mA_bench.csv / _ref.csv and the overlay PNG."),
  H2("1c. 5 mA run (5 Vpk) — the sim says the current clips; look at the LOAD trace shape first"),
  rt([
    ["Plateau present? flat or sloped? (script: fraction of period on plateau)", "yes, flat (> 0.1)", "", "record"],
    ["I_load plateau + / −", "+4.01 / −3.38 mA", "", "±0.5 mA  ☐"],
    ["REF − VN during the + plateau", "0.20 V", "", "record"],
    ["VP − REF during the − plateau", "1.00 V", "", "record"],
    ["Window VP − VN  avg", "4.84 V", "", "±2 V  ☐"],
    ["Rail current + / −", "6.0 / 5.9 mA", "", "±20 %  ☐"],
  ]),
  P("D3/D4 (5 V zeners) start to conduct near 5 V: the INPUT the board sees may be below the generator setting. The script uses the measured LOAD, not the setting.", { it: true }),
  img("A1-bias-bootstrap/A1_30V_5mA.png", 3.5),
  H2("1d. Plateau onset (scripted, 1 min): 2.0 → 4.0 mA in 0.25 mA steps"),
  line("Sourcing onset (mA cmd where pk+ < 98 %)      Sinking onset (mA)"),
  H2("1e. Optional — window vs rail (the ±50 V claim). Generator OFF, ramp both rails together, DMM/scope only"),
  table([["Rails", 1200], ["VP / VN (V)", 2200], ["Window (V)", 1600], ["Window [L] scaling", 2000], ["I rail + (mA)", 1500], ["2 mA pk+ / pk− (mA)", 1940]],
    [["±30 V", "", "", "4.97", "", ""], ["±35 V (Xantrex max)", "", "", "~5.8", "", ""], ["±40 V (2 supplies)", "", "", "~6.6", "", ""], ["±50 V (2 supplies)", "", "", "~8.2", "", ""]], { simcol: [3], blank: [1, 2, 4, 5] }),
  P("Stop if rail current > 15 mA or window > 30 V (INA149 abs max ±18 V). ±40/±50 V = Xantrex 35 V + TTI EX354RT 5–15 V in series on each side, both units' outputs floating.", { it: true }),
  H2("Decision after A1 (circle one)"),
  chk("Window within ±2 V and 2 mA within 1 %  →  model OK at ±30 V; run tests 2–6 at 2 mA (as printed)."),
  chk("Window OK but 2 mA a few % low  →  real op-amp swing worse than model; run tests 2–6 at 1 mA (script: --cmd-scale 0.5)."),
  chk("Window off by > 2 V  →  write the DPAK markings; stop, fix the model before test 2."),
  line("Notes"),
]);
// ---------------- A2
tests.push([
  H1("Test 2 — A2  DC accuracy vs command"),
  P([f("Question. ", { bold: true }), f("Is I_load = V(INPUT) / 1 kΩ within 1 %? Sim column is a zero-error reference; the bench produces the real offset and gain error.")]),
  P([f("Method. ", { bold: true }), f("Fluke 45, RATE S (5 digits), 3 V range for INPUT and LOAD, 30 V range only where the reading exceeds 3 V. At each command the script sets the generator (DC, no AC) and asks for V(INPUT) then V(LOAD); it computes I = V(LOAD)/RL against V(INPUT)/1 kΩ, so the generator's offset accuracy drops out. RL1 measured first with the Fluke 45 (Ω, leads zeroed). ~10 min.")]),
  cmd("python3 bench_rig.py a2 --rl <RL1>"),
  line("RL1 measured (Ω, Fluke 45)"),
  table([["Command", 1300], ["Expected I [L]", 1800], ["V(INPUT) bench", 1900], ["V(LOAD) bench", 1900], ["I = V/RL  ·  error %", 2240], ["Pass ☐", 1300]],
    [["+0.5 V", "0.5000 mA", "", "", "", "±1 %"], ["+1 V", "1.0000 mA", "", "", "", "±1 %"], ["+2 V", "2.0000 mA", "", "", "", "±1 %"], ["−2 V", "−2.0000 mA", "", "", "", "±1 %"],
     ["+5 V", "3.837 mA (clips)", "", "", "", "record"], ["−5 V", "−3.188 mA (clips)", "", "", "", "record"]], { simcol: [1], blank: [2, 3, 4] }),
  P("Uncertainty budget: Fluke 45 0.025 % + 2 d on each reading, RL 0.05 % → ≈ ±0.1 % on the error figure; the ±1 % line is resolved. (BM235 would be ±0.7 %: do not use it here.)", { it: true }),
  img("A2-accuracy-vs-command/A2_30V.png", 4.6, 0.78),
  line("Offset (µA) / gain error (%)  — script prints from the 0.5…2 mA fit"), line("Notes"),
]);
// ---------------- A5b
tests.push([
  H1("Test 3 — A5b  Output impedance by load change"),
  P([f("Question. ", { bold: true }), f("Does the current move when RL goes 1.0 → 2.2 kΩ at 2 mA? Pass = ΔI/I < 0.1 %.")]),
  P([f("Method. ", { bold: true }), f("Fluke 45 IN SERIES with RL (A input, mA DC, manual range 30 mA, RATE S → 1 µA = 0.05 % at 2 mA). Same range for both loads so the meter's gain error cancels; the resistor values only enter Z_out, not ΔI/I. Generator DC 2 V; script takes it to 0 V for the swap. ~5 min.")]),
  cmd("python3 bench_rig.py a5b --rl <RL1> --rl2 <RL2>"),
  line("RL1 measured (Ω)                                   RL2 measured (Ω)"),
  rt([["I at RL1 (1.0 kΩ)", "2.0000 mA", "", "—"], ["I at RL2 (2.2 kΩ)", "2.0003 mA", "", "—"],
      ["ΔI / I", "+0.015 %", "", "< 0.1 %  ☐  (meter floor 0.05 %)"], ["Z_out = ΔV / ΔI", "|8.1 MΩ|", "", "> 1.2 MΩ  ☐"]]),
  img("A5b-output-impedance-dc/A5b.png", 4.6, 0.445),
  line("Notes"),
]);
// ---------------- A4
tests.push([
  H1("Test 4 — A4  Frequency response (scripted)"),
  P([f("Question. ", { bold: true }), f("Is the current flat to 10 kHz? Expected dead flat; ±0.5 dB is the measurement's tolerance, not the circuit's.")]),
  P([f("Method. ", { bold: true }), f("CH1 LOAD, CH2 INPUT (J4 BNC centre). Script sets the DG1022 to 2 Vpk at each frequency, sine-fits both channels and takes the ratio I_load / V(INPUT), so generator flatness and scope gain drop out. 1 and 10 Hz use single acquisitions (slow), the rest average 8. ~3 min. With FG085 / --gen manual: dial each frequency when prompted.")]),
  cmd("python3 bench_rig.py a4 --rl <RL1> --extra"),
  table([["f (Hz)", 1100], ["Expected [L]", 1900], ["mA/V bench", 1900], ["dB vs 10 Hz", 1700], ["phase °", 1400], ["Pass ☐ (±0.5 dB)", 2440]],
    [["1", "0.000 dB", "", "", "", ""], ["10", "0.000 dB (ref)", "", "0 (ref)", "", ""], ["100", "0.000 dB", "", "", "", ""], ["300", "0.000 dB", "", "", "", ""], ["1 k", "0.000 dB (−0.02°)", "", "", "", ""], ["10 k", "+0.002 dB", "", "", "", ""],
     ["extra: 3 / 30 / 3 k / 30 k / 100 k", "flat; loop peak +6 dB at ~600 kHz, not reached", "", "", "", "record"]], { simcol: [1], blank: [2, 3, 4] }),
  img("A4-frequency-response/A4_30V.png", 4.6, 0.78),
  cap("Expected [L]: flat to 10 kHz. Script writes A4_30V_bench.csv/.png with the sim overlaid."),
  line("Absolute gain at 10 Hz (mA/V, expect 1.000 ±1 %)"), line("Notes"),
]);
// ---------------- A3
tests.push([
  H1("Test 5 — A3  Step response and settling (scripted single-shot)"),
  P([f("Question. ", { bold: true }), f("How fast does the pump settle to 1 % after a 0 → 2 mA step, and how much does it overshoot?")]),
  P([f("Method. ", { bold: true }), f("CH1 LOAD (0.5 V/div), CH2 INPUT. DG1022 square 0 / 2 V, 500 Hz (edge ~10 ns [DS] — much faster than the 1 µs sim stimulus, so expect MORE overshoot than [L], not less). Script triggers on CH2 rising, captures 5 µs/div then 100 µs/div, computes everything. ~5 min.")]),
  cmd("python3 bench_rig.py a3 --rl <RL1>"),
  line("Generator edge 10–90 % (ns) — from preflight / script"),
  rt([["Overshoot vs final  (pk − 2 mA) / 2 mA", "18.4 % (1 µs edge)", "", "±10 pts  ☐"], ["Last exit from ±1 % band (µs after edge end)", "2.75 µs", "", "±50 %  ☐"],
      ["Ring frequency (MHz)", "~0.7 MHz", "", "record"], ["Final value", "2.000 mA", "", "±1 %"]]),
  img("A3-step-settling/A3_30V_2mA.png", 4.8, 0.78),
  cap("Expected [L] with a 1 µs edge. If the overshoot is much larger with the 10 ns edge, re-run the sim with the measured edge before calling it a mismatch."),
  line("Notes"),
]);
// ---------------- A7
tests.push([
  H1("Test 6 — A7  Single-rail loss (optional; the client's only prototype)"),
  P([f("Question. ", { bold: true }), f("What current reaches the load when the + rail drops out mid-stimulus? FMEA input for the 10 mA hard limit.")]),
  P([f("Method. ", { bold: true }), f("Generator DC 2 V, RL 1 kΩ, CH1 LOAD, 10 ms/div single-shot (script arms the trigger each time). SEQ 2: Xantrex output 1 (+ rail) OFF when prompted, then ON. SEQ 3: both outputs OFF, then both ON with two fingers — this also measures the stagger of the two-finger power-up used all session. SEQ 1 (one rail for seconds) is NOT done. 50 mA limit on both outputs. Alternative: Korad as the + rail, scripted (--korad), its (−) on GND only. ~10 min.")]),
  cmd("python3 bench_rig.py a7 --rl <RL1>   [--korad /dev/tty.usbserial-XXXX]"),
  rt([["SEQ 2: I_load after + rail lost (continuous)", "−5.9 mA", "", "±50 %  ☐"], ["SEQ 2: transient peak during the drop", "−6.3 mA", "", "record"],
      ["SEQ 2: I_load after + rail restored", "2.000 mA", "", "±1 %"], ["SEQ 3: peak during two-finger enable", "2.02 mA (ideal simultaneous)", "", "< 3 mA  ☐"], ["SEQ 3: stagger between the two outputs (ms, from the trace)", "0", "", "record"]]),
  img("A7-rail-loss/A7_30V.png", 4.4),
  line("Notes"),
]);

const children = [...front, ...kit];
for (const t of tests) { children.push(brk(), ...t); }
children.push(brk(), H1("After the session"),
  P("session_log.csv has every number with its expected value and pass flag — paste the [B] columns into tests/<ID>/RECORD.md and acceptance-tests.md from it; the overlay PNGs (sim dashed, bench solid) are already in tests/<ID>/bench/. Decide the A2–A5 working current from the test-1 decision box. A3: if the 10 ns edge gives much more overshoot than [L], re-run A3-step-settling.asc with the measured edge before calling it a mismatch. One line per Rev-2 thought to 03_safety_plan/parking-lot.md. Transistor finding (1a Vbe rows, 1e window law) → DECISIONS.md."));
const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: BODY }, paragraph: { spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: 160 } } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "JY063 · Client STIM board bench session record · ±30 V", font: "Arial", size: 18, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: "808080" }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "808080" }), new TextRun({ text: " of ", font: "Arial", size: 18, color: "808080" }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 18, color: "808080" })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("ok", OUT, b.length); });
