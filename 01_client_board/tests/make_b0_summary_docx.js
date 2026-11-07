// B0 bench summary — as-built bring-up of the inherited client board (bench 2026-11-06). Same look as BENCH-SESSION_30V.docx:
// helpers below are copied verbatim from make_bench_session_docx.js (do not edit that script); B0-only helpers are marked NEW.
// Build:  cd 01_client_board/tests && NODE_PATH=<dir with node_modules> node make_b0_summary_docx.js && py fix_docx_jpg.py ../BENCH-B0-SUMMARY.docx
// Writes ../BENCH-B0-SUMMARY.docx. Figures: B0-bringup/bench/*.png (scope runs), B0-bringup/figs/*.png (schematic crops),
// B0-bringup/photos/*.jpg (bench photos). fix_docx_jpg.py renames the JPEG media parts docx 8.5 stores as .png.
const fs = require("fs"), path = require("path");
const D = require("docx");
const { LineRuleType, Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ImageRun, PageBreak, HeadingLevel,
  AlignmentType, ShadingType, Header, Footer, PageNumber, BorderStyle, HeightRule, VerticalAlign } = D;
const IMG = path.join(__dirname, "B0-bringup") + "/";
const OUT = path.join(__dirname, "..", "BENCH-B0-SUMMARY.docx");
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
const img = (name, wIn, ratio, base) => { const p = (base || IMG) + name; if (!fs.existsSync(p)) return P(`[figure ${name} missing]`, { it: true, color: "C00000" }); const b = fs.readFileSync(p); const w = wIn || 6.2; return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80, line: 240, lineRule: LineRuleType.AUTO }, keepNext: true, children: [new ImageRun({ type: /\.jpe?g$/i.test(name) ? "jpg" : "png", data: b, transformation: { width: w * 96, height: w * 96 * (ratio || 1.11) } })] }); };
// NEW: bench photos (tests/B0-bringup/photos/, JPEG, EXIF-rotated, ≤ 2400 px) and Word equations (OMML, editable in Word's equation editor)
const { Math: OM, MathRun, MathFraction, MathSubScript, MathSuperScript, MathRoundBrackets, Tab, TabStopType } = D;
const P4R = 1.018;  // height/width of photos/P4_board_closeup.jpg
// no literal spaces around operators: Word and LibreOffice add their own operator spacing. Runs containing a digit are
// set upright (numbers + units) by fix_docx_jpg.py; letter-only runs stay italic (variables), so keep variables in their own run.
const mr = (t) => new MathRun(t.replace(/\s*([=+−≈·])\s*/g, "$1"));
const ms = (b, s) => new MathSubScript({ children: [mr(b)], subScript: [mr(s)] });
const msup = (b, s) => new MathSuperScript({ children: [mr(b)], superScript: [mr(s)] });
const mfr = (n, d) => new MathFraction({ numerator: n, denominator: d });
const mbr = (c) => new MathRoundBrackets({ children: c });
// display equation, journal style: centred on a centre tab, equation number flush right on a right tab
const EQ = (children, n) => new Paragraph({
  tabStops: [{ type: TabStopType.CENTER, position: Math.round(W / 2) }, { type: TabStopType.RIGHT, position: W }],
  spacing: { before: 120, after: 160, line: 276 },
  children: [new TextRun({ children: [new Tab()] }), new OM({ children }), ...(n ? [new TextRun({ children: [new Tab()] }), f(`(${n})`)] : [])] });
const brk = () => new Paragraph({ children: [new PageBreak()] });
const line = (label) => P([f(label + "  ", { size: BODY }), f("_".repeat(Math.max(10, 80 - label.length)), { size: BODY, color: "808080" })], { after: 120, align: AlignmentType.LEFT });
const bul = (t) => new Paragraph({ children: [f("•  " + t)], spacing: { after: 40, line: LINE }, indent: { left: 360, hanging: 360 }, alignment: AlignmentType.JUSTIFIED });
const chk = (t) => new Paragraph({ children: [f("☐  " + t)], spacing: { after: 40, line: LINE }, indent: { left: 360, hanging: 360 } });
const mono = (t) => new Paragraph({ spacing: { after: 0, line: 276 }, indent: { left: 360 }, children: [new TextRun({ text: t, font: "Courier New", size: 18 })] });
const cmd = (t) => new Paragraph({ spacing: { before: 60, after: 160, line: 276 }, indent: { left: 360 }, shading: sh("F2F2F2"), children: [f("Script:  ", { bold: true, size: SMALL }), new TextRun({ text: t, font: "Courier New", size: 18 })] });
const cap = (t) => { fig++; return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240, line: 276 }, children: [f(`Figure ${fig}. `, { bold: true, size: SMALL }), f(t, { size: SMALL })] }); };
const T = (...a) => table(...a);

// ---------------------------------------------------------------- NEW (B0 only)
const B = (t) => f(t, { bold: true });
const PB = (label, text) => P([B(label + " "), f(text)]);
// photo placeholder: dashed, shaded box the user pastes a picture into, followed by a numbered caption
const dash = { style: BorderStyle.DASHED, size: 8, color: "808080" };
const photo = (what, capText, hIn = 2.6) => [
  new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ height: { value: Math.round(hIn * 1440), rule: HeightRule.ATLEAST }, cantSplit: true, children: [
    new TableCell({ width: { size: W, type: WidthType.DXA }, shading: sh("F7F7F7"), verticalAlign: VerticalAlign.CENTER, borders: { top: dash, bottom: dash, left: dash, right: dash },
      children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60, line: 276 }, children: [f("PHOTO PLACEHOLDER", { bold: true, size: SMALL, color: "808080" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0, line: 276 }, children: [f("Insert photo: " + what, { it: true, size: SMALL, color: "808080" })] })] })] })] }),
  cap(capText + "  [photo, B]"),
];
// shaded single-cell note (pending items, verdict)
const box = (label, text, fill = "FFF2CC") => new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [W], rows: [new TableRow({ cantSplit: true, children: [
  new TableCell({ width: { size: W, type: WidthType.DXA }, shading: sh(fill), margins: { top: 100, bottom: 100, left: 160, right: 160 },
    children: [new Paragraph({ spacing: { after: 0, line: 300 }, children: [f(label + "  ", { bold: true, size: SMALL }), f(text, { size: SMALL })] })] })] })] });

// ---------------------------------------------------------------- front + identification
const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 600, after: 120 }, children: [new TextRun({ text: "Client STIM Board Bench Session Record — B0", font: "Arial", size: 36, bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80, line: LINE }, children: [f("As-built bring-up of the inherited client board at ±5 V to ±6 V — why acceptance tests A1–A7 were not run", { size: 24 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80, line: LINE }, children: [f("JY063 Multi-Channel Neural Interface for Immersive VR · UBC ELEC 491 · Team JY · Weymen Koo", { size: SMALL, color: "444444" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480, line: LINE }, children: [f("Revision 2026-11-06 · MCLD 3042 bench · Tektronix TBS1102C + Rigol DG1022 + Fluke 45 + Xantrex XPH 35-4T · companion scripts bench/bench_tbs.py, b0_window.py, b0_figure.py", { size: SMALL, color: "444444" })] }),
  H1("Session identification"),
  P("Every number in this record is a bench value [B] unless tagged otherwise: [H] hand calculation, [DS] datasheet, [L] LTspice model (2026-10-27 runs), [ASSUME] stated assumption. All raw scope data, the per-quantity log and the figures are listed in Appendix A."),
  table([["Field", 2600], ["", 7840]], [
    ["Date / location", "2026-11-06   MCLD 3042 (3rd-year lab), bench no. ____"],
    ["Operator(s)", "Weymen Koo. Scope and generator driven from the laptop over USB (bench_tbs.py / b0_window.py); DMM, supply and board handled by hand"],
    ["Board", "client STIM board, Altium STIM.SchDoc 2026-10-16 (netlist STIM.NET), S/N: ______   fitted DPAKs (markings read on the board): Q2 (+ side) = MJD350, Q1 (− side) = MJD340"],
    ["Rails", "Xantrex XPH 35-4T, bench unit S/N ______: two floating outputs in series, out1(−) joined to out2(+) = GND → J3 pin 2. Set points ±5.0, ±5.75 and ±6.0 V; current limit 50–100 mA (one run at 200 mA by mistake, noted)"],
    ["Generator", "Rigol DG1022 S/N DG1D181601807 via USB (NI-VISA). BNC on J4, held at 0 V with the output OFF for every powered run (verified by the script before each run)"],
    ["Scope / probes", "Tektronix TBS1102C S/N C031285 (FV v1.29.38) via USB (NI-VISA), 2 × 10× probes. CH1 = V+ at the Q2 tab, CH2 = V− at Q1 pin 3, both grounds on J2"],
    ["DMM", "Fluke 45 (bench) S/N ______, the only DMM this session (no BM235): mA in series with VCC+, or V / Ω / mV with the rail jumpered"],
    ["Load", "RL1 1.0168 kΩ between J1 and J2 for B0.1–B0.3; removed for the heat runs B0.4–B0.5"],
    ["Laptop", "Windows 11, NI-VISA, Python bench scripts; every number appended to bench/session_log.csv"],
  ], { blank: [1] }),
  spacer(),
  img("photos/P1_bench.jpg", 6.2, 0.75),
  cap("Bench setup, MCLD 3042, 2026-11-06: Xantrex XPH 35-4T (left), Fluke 45 in series with VCC+, TBS1102C, DG1022, and the board on its anti-static bag.  [photo, B]"),
  img("photos/P2_xantrex_fluke_5V.jpg", 6.5, 0.374),
  cap("±5 V run: Xantrex at 4.9 / 5.0 V, 0.03 A on each output (10 mA resolution), and the Fluke 45 in series with VCC+ reading 32.51 mA.  [photo, B]"),
];

// ---------------------------------------------------------------- purpose
const purpose = [
  brk(),
  H1("Why B0 replaced A1–A7"),
  P("The session was planned to run acceptance tests A1–A7 at ±30 V against the 2026-10-27 LTspice model (BENCH-SESSION_30V.docx). Before power was applied, the unpowered checks (section 4) found 44 Ω between the op-amp supply nodes V+ and V−, and tracing the copper against the Altium netlist showed that the board is not the circuit that was simulated (section 3)."),
  P("B0 replaced A1–A7 with a low-rail bring-up that asks only three questions: is the board as built consistent with its netlist, is it damaged, and where. It is due diligence on inherited hardware. It does not validate or invalidate the LTspice model, which describes a different circuit — the client's reference circuit."),
  P([B("Client claim. "), f("The client reports that the prototype worked up to ±50 V. Section 8 shows why that is not consistent with this PCB as built. One possible reading [H] is that the claim refers to the breadboard prototype in STIM CIRCUIT.pdf, which uses the intended topology (Figure 3, left). This is for the client to confirm.")]),
  H2("Questions and answers at a glance"),
  table([["Question", 3400], ["Answer [B / H]", 6040]], [
    ["Is the board the simulated circuit?", "No. Q2 is the wrong device type (design error), Q1 carries the wrong part number (part error). Everything else matches (section 3)."],
    ["Is it damaged?", "Yes. 43–44 Ω supply short across the ICs at every current tried (33–67 mA), and Q2 shorted emitter–collector (1.74 Ω vs 43.5 MΩ for a spare)."],
    ["Do the bench voltages make sense?", "Yes. One series loop, Q2 → short → Q1 in emitter–base breakdown, closes KVL to 1 mV (section 8)."],
    ["Which IC is shorted?", "U1 (TLE2141) likely, moderate confidence; a shared fault in both ICs is not excluded (section 9). Not pursued further; it does not change the verdict."],
    ["Can A1–A7 run on this board?", "No, not without rework. Recommendation and the decisions it needs are in section 10."],
  ]),
];

// ---------------------------------------------------------------- PCB error
const pcb = [
  brk(),
  H1("The PCB error: board vs intended design"),
  P("Sources: Altium schematic PDF and netlist STIM.NET (as built), the client's reference circuit and breadboard in STIM CIRCUIT.pdf (intended), the part markings on the board, continuity tracing, and the MJD340 / MJD350 pinout [DS]: pin 1 = base, pin 3 = emitter, pin 4 (tab) = collector. Note the designators differ: the reference circuit calls the INA149 U1 and the TLE2141 U2; the Altium board calls the TLE2141 U1 and the INA149 U2. This record uses the Altium designators."),
  img("figs/B0_schematic_compare.png", 6.5, 1036 / 1927),
  cap("Left: client reference circuit — NPN on the + side and PNP on the − side, both emitter followers, so the op-amp supplies float around OUT. Right: Altium schematic the PCB was made from — Q2 drawn as a PNP with its emitter on VCC+, Q1 drawn correctly but given an NPN part number."),
  table([["Item", 1500], ["Intended (reference = LTspice model) [L]", 3000], ["As built (Altium + fitted part)", 3200], ["Error type", 1740]], [
    ["Q2, + side", "NPN MJD340: C → fused VCC+, E = V+, B ← R2/R3 (emitter follower)", "PNP symbol, part MJD350 fitted; E (pad 3) → fused VCC+, C (tab) = V+", "design error: symbol and footprint"],
    ["Q1, − side", "PNP MJD350: E = V−, C → fused VCC−, B ← R4/R5 (emitter follower)", "PNP symbol, E (pad 3) = V− = U2 pin 4, C (tab) → fused VCC−; part attribute and fitted part MJD340 (NPN)", "part-attribute error"],
    ["Op-amp supply", "floats ≈ ±2.5 V around OUT; ICs see ≈ 5 V at any rail [L]", "V+ ≈ VCC+, V− ≈ VCC− + ≈ 8 V; ICs see ≈ 2·rail − 8.5 V [H]", "consequence"],
    ["Everything else", "R1–R6, D1/D2 (BAS16), C1, R7, U1 = LOAD→REF follower, U2 = INA149 pinout, D3/D4 clamp, C2/C3, J1–J5", "matches (STIM.NET checked pin by pin)", "none"],
  ]),
  spacer(),
  bul("Q1: symbol, nets and pads already form a correct PNP follower. Only the part is wrong: an MJD350 on the existing pads matches the intended design."),
  bul("Q2: symbol and part agree with each other (both PNP), but the follower needs an NPN with its collector on VCC+. On a DPAK the collector is the tab, so the fix swaps which pad carries VCC+ and which carries V+ — a bodge or a re-spin, not a part swap."),
  bul("Likely origin [H]: the Q1 / Q2 part numbers were swapped and Q2 was then drawn to match its PNP part. The client should confirm the intended design before any rework."),
  bul("C2 / C3 (1 µF) sit on the fused rails in both the reference and the board, not on V+ / V−. The probe table in BENCH-SESSION_30V.docx (VP / VN = C2 / C3 lead) is wrong for this board; section 6 has the corrected probe points."),
  spacer(),
  img("photos/P4_board_closeup.jpg", 5.2, P4R),
  cap("Board close-up: Q2 (DPAK, + side, next to U1) and Q1 (DPAK, − side, next to C3); U1 = TLE2141 and U2 = INA149, both SOIC soldered to the board; J3 Micro-Fit plug at left. Part markings read on the bench: Q2 = MJD350 (PNP), Q1 = MJD340 (NPN).  [photo, B]"),
];

// ---------------------------------------------------------------- pre-power
const prepower = [
  brk(),
  H1("Pre-power checks (unpowered, Fluke 45 Ω)"),
  table([["Quantity", 3300], ["Expected", 2100], ["Bench [B]", 1700], ["Note", 2340]], [
    ["Fluke lead resistance (probes touching)", "≈ 0 Ω", "0.34 Ω", "subtracted: RL1 = 1016.5 Ω used"],
    ["RL1", "1.00 kΩ", "1.0168 kΩ", "+1.7 %: not a 0.1 % part; usable at the measured value"],
    ["RL2", "2.2 kΩ", "2.3526 kΩ", "+6.9 %: outside 5 %, probably a 2.4 kΩ part — check the colour code"],
    ["J3 VCC+ (pin 1) → GND (pin 2)", "no short", "305 kΩ", "pass"],
    ["J3 VCC− (pin 3) → GND (pin 2)", "no short", "563 kΩ", "pass (asymmetry: different junctions forward-biased)"],
    ["J1 → J2 with the RL1 fixture", "≈ 1016 Ω", "1.01 kΩ", "pass"],
    ["R7 (1 kΩ) in circuit, OUT → LOAD", "≈ 1 kΩ", "189 Ω", "parallel path through a damaged IC [H]"],
    ["U2 pin 7 (V+) → U2 pin 4 (V−)", "high: no part between them", "44 Ω", "supply short → do not power at ±30 V"],
  ], { simcol: [1] }),
  spacer(),
  img("photos/P4a_prepower.jpg", 6.5, 0.698),
  cap("Fluke 45 readings for the pre-power checks: (a) lead resistance, (b) RL1, (c) RL2, (d) J3 VCC+ to GND, (e) J3 VCC− to GND, (f) V+ to V− at U2 pins 7–4.  [photo, B]"),
  img("photos/P5_harness.jpg", 5.6, 0.75),
  cap("Power harness: Micro-Fit plug in J3 (pin 1 = VCC+, pin 2 = GND, pin 3 = VCC−), twisted triple to the Fluke 45 (VCC+) and the Xantrex posts; scope probes already on the board.  [photo, B]"),
];

// ---------------------------------------------------------------- instruments
const instr = [
  H1("Instrument check (Step 0, no board)"),
  table([["Check", 4200], ["Result [B]", 5240]], [
    ["VISA enumeration (NI-VISA)", "TBS1102C and DG1022 both reply to *IDN?"],
    ["Probe attenuation CH1 / CH2", "10X / 10X"],
    ["CH1 on PROBE COMP: decoded vs scope Pk-Pk", "5.247 V vs 5.311 V — OK"],
    ["CH2 on PROBE COMP: decoded vs scope Pk-Pk", "5.209 V vs 5.309 V — OK"],
    ["Generator 2 Vpk sine into CH1: 100 Hz / 300 Hz / 1 kHz / 10 kHz / 100 kHz", "1.9928 / 1.9941 / 1.9976 / 2.0104 / 2.0261 Vpk  (−0.4 % … +1.3 %)"],
    ["1 Hz and 10 Hz flatness; generator 10–90 % edge", "invalid (byte-order bug, below) — redo before A3 / A4"],
    ["Byte-order self-test (`bench_tbs.py check`): CH1 moved 2 div between acquisitions", "decoded shift +0.010 V, raw count shift −12 733 → OK"],
  ]),
  spacer(),
  P([B("Software findings (fixed this session). "), f("(1) The DG1022 times out on a plain *IDN? query over NI-VISA; it needs explicit line terminators and a write–wait–read. One 'output ON' command was silently dropped, so the driver now reads the output state back after every command. (2) The TBS1102C (FV v1.29.38) sends waveform bytes least-significant first while WFMOutpre:BYT_Or reports MSB. Decoding is now fixed to LSB-first and `check` re-verifies it with the position-shift test above. (3) The first ±5 V capture (run 1: 3.919 / 2.659 V) was decoded before this fix and kept no raw data; run 2 supersedes it.")]),
];

// ---------------------------------------------------------------- setup
const setup = [
  H1("Bench setup for B0"),
  H2("Wiring"),
  mono("Xantrex out1 (+) -- Fluke 45 mA (B0.1, B0.2, B0.4, B0.5)"),
  mono("                    or banana jumper (B0.3) ------- J3.1 VCC+"),
  mono("Xantrex out1 (-) ---+"),
  mono("Xantrex out2 (+) ---+-- GND -- J3.2 / J2"),
  mono("Xantrex out2 (-) ------------------------------- J3.3 VCC-"),
  mono("DG1022 -- BNC -- J4 (0 V, output OFF)"),
  mono("RL1 1.0168 k: J1 -- J2 (removed for B0.4, B0.5)"),
  mono("TBS CH1 = V+ at Q2 tab, CH2 = V- at Q1 pin 3, grounds on J2"),
  mono("Laptop USB -> TBS1102C + DG1022 (NI-VISA)"),
  spacer(),
  H2("Probe points (corrected for this board, STIM.NET)"),
  table([["Node", 2200], ["Where (DPAK: pin 1 = B, pin 3 = E, tab = C)", 7240]], [
    ["V+", "Q2 tab (collector) = U1 pin 7 = U2 pin 7"],
    ["V−", "Q1 pin 3 (emitter, right lead) = U1 pin 4 = U2 pin 4"],
    ["VCC+ after F1", "Q2 pin 3 (emitter, right lead) = C2 + lead"],
    ["VCC− after F2", "Q1 tab (collector) = C3 − lead"],
    ["Q2 base / Q1 base", "R2–R3 junction (Q2 pin 1) / R4–R5 junction (Q1 pin 1)"],
    ["GND", "J2 (all probe grounds), J3 pin 2"],
  ]),
  H2("Power-on procedure (every run)"),
  bul("Supply set with both outputs OFF; generator verified at 0 V, output OFF by the script."),
  bul("Script arms a single shot on CH1 rising through 1 V (50 ms/div, 500 ms record, trigger mid-screen) and reports READY; then the operator gets GO and turns both outputs on together (two fingers)."),
  bul("The trigger captures the power-up edge of V+ and V−; the script then takes 16-average captures about every 1.25 s until it sees the rails go off. A trigger whose record does not end with V+ above 1 V (probe-clip glitch) is rejected and re-armed."),
  bul("Stop rule: current above 15 mA with healthy ICs, or any surprise → both outputs OFF. With the short present, current was bounded by the loop (section 8) and each run lasted 15–75 s."),
  spacer(),
  img("photos/P6_probes.jpg", 5.6, 0.75),
  cap("Scope probe points for all B0 runs: CH1 hook on the Q2 tab (V+), CH2 hook on Q1 pin 3 (V−), both ground clips on J2.  [photo, B]"),
];

// ---------------------------------------------------------------- results
const results = [
  H1("Results"),
  H2("B0.1–B0.2  ±5 V, Fluke 45 in series with VCC+"),
  img("bench/B0_pm05p0V_run2.png", 6.5, 572 / 1560),
  cap("±5 V run 2 [B]. Left: power-up, V+ and V− rise together in ≈ 15 ms (the Xantrex ramp) and V− goes positive. Right: 17 captures over 20 s, flat."),
  table([["Quantity", 3600], ["Expected", 2500], ["Bench [B]", 1900], ["Note", 1440]], [
    ["Loop current (Fluke 45 at ≈ 10 s)", "4–5 mA if the ICs were healthy", "32.58 mA", "> 15 mA"],
    ["V+ (Q2 tab), 17 captures", "≈ VCC+ [H]", "+4.485 … +4.490 V", ""],
    ["V− (Q1 pin 3), 17 captures", "≈ −5 V if ICs healthy", "+3.047 … +3.053 V", "positive"],
    ["V+ − V− across the ICs", "", "1.437 V", ""],
    ["Short = (V+ − V−) / I", "44 Ω (unpowered DMM)", "44.1 Ω", "same short"],
    ["Power-up single shot, end values", "= steady state", "+4.48 / +3.04 V", ""],
  ], { simcol: [1] }),
  spacer(),
  P("Run 1 (same conditions, 32.4 mA; current limit accidentally at 200 mA) is superseded by run 2 (software finding 3, section 5). A touch test at ±5 V found nothing: the short dissipates only ≈ 47 mW [H]."),

  H2("B0.3  Node map at ±5 V, Fluke as voltmeter (rail jumpered), Xantrex 0.04 A on both outputs"),
  table([["Node (to J2 GND)", 5200], ["V [B]", 4240]], [
    ["VCC+ after F1 = Q2 pin 3 (E)", "+4.970"],
    ["Q2 base (R2/R3)", "+4.961"],
    ["V+: Q2 tab / U1 pin 7 / U2 pin 7", "+4.908 / +4.907 / +4.907"],
    ["V−: Q1 pin 3 / U1 pin 4 / U2 pin 4", "+3.1332 / +3.1345 / +3.1355"],
    ["Q1 base (R4/R5)", "−4.288"],
    ["VCC− after F2 = Q1 tab (C)", "−4.950"],
  ]),
  spacer(),
  bul("KVL around the loop: 0.063 V (Q2 E→C) + 1.773 V (short) + 8.083 V (Q1) = 9.919 V = rail to rail 9.920 V ✓. Short = 1.773 V / 0.04 A ≈ 44 Ω (Xantrex meter, 10 mA resolution)."),
  bul("Q2: emitter–base voltage 9 mV, far below the ≈ 0.6–0.7 V a conducting PNP needs, while 40 mA flows E→C with 63 mV (≈ 1.6 Ω): Q2 behaves as a short, not a transistor."),
  bul("Q1: base–collector forward 0.66 V; emitter–base in reverse breakdown at 7.42 V (rated 3 V [DS]) — gain probably degraded."),
  bul("Both supply nets are intact: the three V+ pins agree within 1 mV, the three V− pins within 2.3 mV."),
  P("The two Q1 junction voltages follow directly from the node map:"),
  EQ([ms("V", "EB(br),Q1"), mr(" = "), ms("V", "−"), mr(" − "), ms("V", "B,Q1"), mr(" = 3.133 V − (−4.288 V) = 7.42 V")], 1),
  EQ([ms("V", "BC,Q1"), mr(" = "), ms("V", "B,Q1"), mr(" − "), ms("V", "CC−"), mr(" = −4.288 V − (−4.950 V) = 0.66 V")], 2),
  P("Equation (1) is the emitter–base junction in reverse breakdown (rated 3 V [DS]); (2) is the base–collector junction, forward-biased. Q1 is conducting upside down."),

  H2("Q2 confirmation (unpowered, Fluke 45 Ω)"),
  table([["Emitter → collector", 5200], ["Ω [B]", 4240]], [
    ["Q2 on the client board", "1.74 Ω (= the ≈ 1.6 Ω from 63 mV / 40 mA powered)"],
    ["Spare MJD350, out of circuit", "43.5 MΩ (healthy reference)"],
    ["Q1 on the client board", "MΩ range (not shorted)"],
  ]),
  spacer(),
  P("No other path from the Q2 emitter to its collector is below tens of kΩ (bias chain, junctions), so the 1.74 Ω is Q2 itself: Q2 is shorted emitter–collector, confirmed."),
  img("photos/P8_q2_ec.jpg", 4.8, 1.042),
  cap("Q2 emitter–collector resistance: (a) probing Q2 on the client board, (b) 1.74 Ω; (c) spare MJD350 out of circuit, (d) 43.5 MΩ.  [photo, B]"),

  H2("B0.4–B0.5  Heat runs to locate the shorted IC (RL removed)"),
  table([["Run", 2100], ["Rails set", 900], ["On", 700], ["I (Fluke)", 1200], ["V+ / V−", 1500], ["Short", 900], ["P short", 900], ["Touch U1 / U2", 1240]], [
    ["heat_noRL", "±5.75 V", "≈ 17 s", "51.63 mA", "+4.97 / +2.73 V", "43.3 Ω", "0.12 W", "not done"],
    ["heat2_noRL", "±5.75 V", "≈ 41 s", "57.79 mA", "+4.89 / +2.41 V", "42.9 Ω", "0.14 W", "no warmth"],
    ["heat3_noRL", "±6.0 V (measured 6.0 V both outputs)", "≈ 75 s", "67.0 → 64.7 mA", "+4.966 → +5.001 / +2.093 → +2.175 V", "43.0 → 43.6 Ω", "≈ 0.18 W", "no warmth"],
  ]),
  img("bench/B0_pm05p75V_heat2_noRL.png", 6.5, 572 / 1560),
  cap("Heat run 2, ±5.75 V set [B]. V− rises ≈ 70 mV over the first 15 s as Q1's emitter–base breakdown voltage warms up, then holds."),
  img("bench/B0_pm06p00V_heat3_noRL.png", 6.5, 572 / 1560),
  cap("Heat run 3, ±6.0 V set, 75 s [B]. Current falls 67.0 → 64.7 mA as Q1 warms; the short stays at 43–44 Ω."),
  img("photos/P7_heat_panels.jpg", 6.5, 0.263),
  cap("Xantrex and Fluke 45 during the heat runs: 51.63 mA (run 1), 57.79 mA (run 2), 66.89 mA (run 3, 0.07 A on the Xantrex meters).  [photo, B]"),
  bul("The short is 43–44 Ω at 33, 40, 52, 58 and 65–67 mA: resistive, not changing with current or time."),
  bul("Fluke 45 burden: V+ was 4.486 V with the Fluke in series (run 2, 32.6 mA) and 4.908 V without it (B0.3, 40 mA) → ≈ 0.42 V at 32.6 mA, ≈ 13 Ω on the mA input [B]. At 65 mA it drops ≈ 0.85 V, which is why V+ stayed near 5.0 V with the Xantrex at 6.0 V (confirmed with the Fluke at the Xantrex terminals) and why the heat runs reached only 0.12–0.18 W."),
  bul("Touch is a weak test at these powers: an SOIC-8 at ≈ 100–160 °C/W [ASSUME] rises only ≈ 14–29 °C at 0.14–0.18 W. 'No warmth' does not clear either IC."),
];

// ---------------------------------------------------------------- analysis
const analysis = [
  H1("Napkin analysis: is it what the PCB error predicts? [H]"),
  P("With the short present, all of the current flows in one series loop from VCC+ to VCC−. Using only the netlist, the node map of section 7.2 and datasheet ratings:"),
  mono("VCC+ -Q2 (shorted)-> V+ -44 ohm short-> V- -Q1 (upside down)-> VCC-"),
  mono("+4.970   0.063 V    +4.907    1.773 V    +3.133  7.42 + 0.66 V  -4.950"),
  spacer(),
  P("Kirchhoff's voltage law around that loop gives (3); with the B0.3 node voltages in it, (4) closes to 1 mV [B]:"),
  EQ([ms("V", "CC+"), mr(" − "), ms("V", "CC−"), mr(" = "), ms("V", "EC,Q2"), mr(" + I · "), ms("R", "short"), mr(" + "), ms("V", "EB(br),Q1"), mr(" + "), ms("V", "BC,Q1")], 3),
  EQ([mr("9.920 V = 0.063 V + 1.773 V + 7.42 V + 0.66 V = 9.919 V")], 4),
  P("The resistance of the short under power, (5), equals the 44 Ω measured unpowered:"),
  EQ([ms("R", "short"), mr(" = "), mfr([ms("V", "+"), mr(" − "), ms("V", "−")], [mr("I")]), mr(" = "), mfr([mr("1.773 V")], [mr("40 mA")]), mr(" ≈ 44 Ω")], 5),
  P("Solving (3) for the current, with Q2 shorted (its drop is a few tens of mV) and Q1's drop lumped as ≈ 8.2 V (it rises slightly with current and temperature):"),
  EQ([mr("I ≈ "), mfr([mr("2 · "), ms("V", "rail"), mr(" − "), ms("V", "Q1"), mr(" − "), ms("V", "EC,Q2")], [ms("R", "short")]), mr(" ≈ "), mfr([mr("2 · "), ms("V", "rail"), mr(" − 8.2 V")], [mr("44 Ω")])], 6),
  P("The power splits between the short and Q1 as"),
  EQ([ms("P", "short"), mr(" = "), msup("I", "2"), mr(" · "), ms("R", "short"), mr(", "), ms("P", "Q1"), mr(" ≈ "), mr("I"), mr(" · 8.2 V")], 7),
  P("so at 57.8 mA (heat run 2) the short dissipates 0.14 W and Q1 0.47 W, which is why Q1, not the IC, is the warm part."),
  bul("Q2 (PNP, emitter on VCC+): would be switched fully on by the bias chain anyway; on this board it is shorted, so V+ ≈ VCC+ either way."),
  bul("Q1 (NPN, collector on VCC−): the base–collector junction conducts to VCC− (base at −4.29 V) and the emitter–base junction breaks down like an ≈ 7.4 V zener, so V− sits ≈ 8.1 V above VCC−. This is why V− is positive at ±5 V."),
  bul("The current is set by what is left over, equation (6). Predicted against measured:"),
  table([["Rails", 1800], ["Loop current [H]", 2600], ["Bench [B]", 2400], ["Note", 2640]], [
    ["±5 V", "≈ 33–40 mA", "32.6 mA (Fluke in series), 40 mA (jumpered)", "matches"],
    ["±6 V (VCC+ ≈ 5.1 V after the Fluke)", "≈ 65 mA", "67.0 → 64.7 mA", "matches"],
    ["±10 V", "≈ 260 mA", "not run", "do not raise the rails"],
    ["±30 V", "≈ 1.2 A (limit would cap it)", "not run", "do not raise the rails"],
  ], { simcol: [1] }),
  spacer(),
  P([B("Client's ±50 V test. "), f("With healthy ICs on this PCB there is no short, so no loop current: V+ sits at VCC+ (Q2 fully on) and V− at VCC− + ≈ 8 V (Q1 in breakdown), and the ICs see")]),
  EQ([ms("V", "+"), mr(" − "), ms("V", "−"), mr(" ≈ 2 · "), ms("V", "rail"), mr(" − 8 V = 2 · 50 V − 8 V ≈ 92 V")], 8),
  P("against ≈ 36 V for the INA149 and 44 V for the TLE2141 [DS, confirm the exact limits]. That is consistent with the ICs (and Q2) having been destroyed by that test [H]. The ±5–6 V B0 runs did not cause the short: the 44 Ω was measured before any power was applied this session."),
];

// ---------------------------------------------------------------- which IC
const whichic = [
  H1("Which IC is shorted"),
  P("At ±5 V with the Fluke on its lowest range in slow mode, the voltage drops along the supply traces were read pin to pin. On the V− side, the pin that drains the short sits highest."),
  table([["Reading (red → black)", 4600], ["Bench [B]", 1800], ["Meaning", 3040]], [
    ["U1 pin 7 → U2 pin 7 (V+ side)", "0 V", "no difference on V+"],
    ["U2 pin 4 → U1 pin 4 (V− side)", "−0.04 mV", "U1 pin 4 higher than U2 pin 4"],
    ["U1 pin 4 → Q1 pin 3", "+0.14 mV", ""],
    ["U2 pin 4 → Q1 pin 3", "+0.09 mV", "0.14 − 0.09 = 0.05 mV ≈ row 2 ✓"],
  ]),
  spacer(),
  bul("Result: U1 (TLE2141) likely, moderate confidence. U1 pin 4 is the highest point on V− (+0.14 mV above Q1 pin 3, U2 pin 4 +0.09 mV; U2 pin 4 − U1 pin 4 = −0.04 mV), so U1 sources the current. The three readings agree to 0.01 mV, but the differences are tens of µV."),
  bul("A shared fault is not excluded: both ICs partly damaged (e.g. ≈ 88 Ω each in parallel ≈ 44 Ω). Both V− branches carried current, which fits that reading too."),
  bul("Layout (Altium PCB, top and bottom layers, viewed as screenshots): V+ and V− are copper pours, not discrete traces, so a current split cannot be computed reliably from them. The µV-level drops are consistent with a few mΩ of pour at 40 mA."),
  bul("Heat tests (section 7.4): 0.12–0.18 W in the short for up to 75 s, no warmth felt on U1 or U2. This is a weak test at that power; ≈ 1 V was lost in the Fluke 45 mA input (≈ 13 Ω burden: V+ 4.486 V with the Fluke in series vs 4.908 V without it at ±5 V)."),
  spacer(),
  box("Closed — not pursued further (user's decision).", "The definitive check was not done. U1 is an SOIC soldered to the board (Figure 4; the layout's DIP-8 pads are unused), so isolating it means lifting its pin 7 or removing it — rework on the client's board: measure U2 pin 7 → pin 4 unpowered with U1 isolated (44 Ω disappears → U1; stays → U2; ≈ 88 Ω → both). Listed as open / optional for the client (section 10). Effect on the verdict: none — Q2 shorted emitter–collector (confirmed) and the 44 Ω supply short already stop A1–A7; identifying the IC only changes the rework list (replace U1, U2 or both).", "E7E6E6"),
];

// ---------------------------------------------------------------- verdict
const verdict = [
  H1("Verdict and decisions"),
  box("Verdict [B].", "The board is dead as built: 43–44 Ω supply short across the ICs (U1 most likely), Q2 shorted emitter–collector (confirmed), Q1 overstressed in emitter–base breakdown (not shorted), on top of the Q1 / Q2 design errors. Acceptance tests A1–A7 cannot run on it.", "E2EFDA"),
  spacer(),
  P([B("Recommendation. "), f("Stop A1–A7 on this board. This record is the due-diligence deliverable on the inherited hardware. The decisions below belong to the team and the client; none of them has been taken.")]),
  table([["Decision", 2600], ["Options", 4840], ["Who", 2000]], [
    ["Make this board testable?", "Rework: Q1 → MJD350 on the existing pads; Q2 → NPN (MJD340) on bodged pads (collector to VCC+); replace U1, and U2 if it proves damaged. Or keep it as a documented failed prototype.", "Weymen + client"],
    ["Intended design", "Client confirms the intended topology is the reference circuit (Figure 3, left) = the LTspice model.", "client"],
    ["±50 V claim", "Which hardware was tested at ±50 V: breadboard or this PCB?", "client"],
    ["Which IC (open / optional)", "Lift U1 pin 7 (SOIC, soldered — rework) and measure U2 pin 7 → pin 4 unpowered (section 9). Only changes the rework list.", "client"],
    ["Rev 2 PCB", "Fix Q2 symbol / footprint and Q1 part attribute; re-check every polarised part against the reference before fab.", "team"],
    ["RL2", "Check the marking (2.3526 kΩ measured vs 2.2 kΩ nominal); replace if it is the wrong part.", "Weymen"],
  ]),
];

// ---------------------------------------------------------------- appendix
const appx = [
  brk(),
  H1("Appendix A — files"),
  P("All bench files are in 01_client_board/tests/B0-bringup/bench/ unless stated. Each run has a figure (.png), the converted waveforms (_wave.csv, _startup.csv), the raw scope counts with the preamble needed to convert them (_raw.csv, _startup_raw.csv: V = (counts − YOFF) · YMULT + YZERO) and the per-capture means (_trend.csv)."),
  table([["File(s)", 4700], ["Content", 4740]], [
    ["B0_pm05p0V_run2.*", "±5 V, Fluke in series: power-up + 17 captures"],
    ["B0_pm05p75V_heat_noRL.*", "heat run 1, ±5.75 V set, ≈ 17 s"],
    ["B0_pm05p75V_heat2_noRL.*", "heat run 2, ±5.75 V set, ≈ 41 s"],
    ["B0_pm06p00V_heat3_noRL.*", "heat run 3, ±6.0 V set, 75 s"],
    ["B0_pm05p0V.csv / .png", "run 1 (superseded, no raw data)"],
    ["../figs/B0_schematic_compare.png", "Figure 3 (client reference vs Altium schematic)"],
    ["../README.md", "B0 findings in text form"],
    ["01_client_board/bench/session_log.csv", "every number with expected value, tolerance and pass flag"],
    ["01_client_board/tests/make_b0_summary_docx.js", "generator of this document"],
  ]),
  H1("Appendix B — scripts and fixes"),
  table([["Script (01_client_board/bench/)", 3400], ["Purpose", 6040]], [
    ["bench_tbs.py check", "VISA list, probe attenuation, byte-order self-test, decode check against the scope's own MEAN"],
    ["bench_tbs.py preflight", "Step 0: probe comp on CH1 / CH2, generator flatness and edge"],
    ["b0_window.py <rail> --tag … --transient 0.05 --window <s>", "single-shot power-up capture, then 16-average captures until the rails go off; CSV + raw + trend + log"],
    ["b0_figure.py <base> <rail> <I_mA>", "one figure per run: power-up (left) + trend (right)"],
    ["bringup.py", "first single-capture version (run 1)"],
    ["relay.py", "runs a bench script with its prompts answered from a file (agent-in-the-loop)"],
  ]),
  spacer(),
  bul("instruments.py: DG1022 *IDN? by write–wait–read; output state read back after every command and re-sent if dropped."),
  bul("bench_tbs.py: DG1022 search with terminators; TBS waveform byte order fixed to LSB-first (FV v1.29.38), verified by `check`; probe attenuation read from CH<n>:PRObe:GAIn; raw counts and preamble kept for every capture."),
  bul("bench_rig.py: probe table VP / VN corrected to the IC pins (C2 / C3 are on the fused rails)."),
  bul("To redo before A3 / A4 on a working board: Step 0 1 Hz / 10 Hz flatness and the generator edge time."),
];

const children = [...front, ...purpose, ...pcb, ...prepower, ...instr, ...setup, ...results, ...analysis, ...whichic, ...verdict, ...appx];
const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: BODY }, paragraph: { spacing: { line: LINE, lineRule: LineRuleType.AUTO, after: 160 } } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "JY063 · Client STIM board bench session record · B0 as-built bring-up", font: "Arial", size: 18, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: "808080" }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "808080" }), new TextRun({ text: " of ", font: "Arial", size: 18, color: "808080" }), new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 18, color: "808080" })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log("ok", OUT, b.length); });
