# B0 — as-built bring-up of the inherited client board (bench 2026-11-06)

Not an acceptance test. Added at the bench because the board is not the circuit the LTspice model (and A1–A7) describe.
Sources: `STIM.NET` (Altium netlist, user's Downloads), `../../Client_Prototype_HowlandPump.pdf`, continuity + part
markings on the board, MJD340/350 pinout [DS]: 1 = B, 3 = E, 4 (tab) = C.

## Board vs intended design

| | Intended (LTspice model, bootstrapped followers) | As built (schematic symbol / part attribute / fitted) |
|---|---|---|
| Q2, + side | **NPN** MJD340: C → fused VCC+, E = V+, B ← R2/R3 | PNP symbol, E → fused VCC+, C (tab) = V+ / MJD350 / MJD350 fitted |
| Q1, − side | **PNP** MJD350: E = V−, C → fused VCC−, B ← R4/R5 | PNP symbol (arrow toward base), E (pad 3) = V− = U2 pin 4, C (tab) → fused VCC− / **MJD340** / MJD340 fitted |
| op-amp supply | floats ≈ ±2.5 V around OUT; ICs see ≈ 5 V at any rail [L] | V+ ≈ VCC+ (PNP on), V− ≈ VCC− + ~8 V (NPN upside down: B-C forward + E-B breakdown); ICs see ≈ 2·rail − 8.5 V [H] |

- **Q1 = part-attribute error.** Symbol, nets and pads are a correct PNP follower; part is NPN. Fix: fit MJD350.
- **Q2 = design error.** Symbol and part agree (PNP) but the follower needs an NPN with C on VCC+. On a DPAK that swaps
  which pad gets VCC+ vs V+ → bodge or re-spin, not a part swap.
- Likely origin [H]: Q1/Q2 part numbers swapped and Q2 drawn with the wrong polarity. Client to confirm intent.
- Everything else matches the schematic and our model: R1–R6, D1/D2 (BAS16, pin 1 A / 3 K), C1, R7, U1 = LOAD→REF follower,
  U2 = INA149 (+IN INPUT, −IN GND, REF_A/B = REF, VOUT = OUT), D3/D4 input clamp, C2/C3 on fused VCC±, J1–J5.
- Consequence [H]: the client's "worked to ±50 V" puts ≈ 92 V across ICs rated 36–44 V. Likely cause of the short below.

## Measured [B]

| | Value |
|---|---|
| Unpowered, U2 pin 7 (V+) to pin 4 (V−) | 44 Ω |
| Unpowered, R7 in circuit | 189 Ω (1 kΩ part: parallel path through a damaged IC [H]) |
| Unpowered, J3 VCC+ / VCC− to GND | 305 kΩ / 563 kΩ (no rail short) |
| ±5 V run 2: V+ / V− / I+ | +4.49 V / +3.05 V / 32.58 mA, flat over 20 s (`bench/B0_pm05p0V_run2*`) |
| short under power (V+ − V−) / I+ | 1.44 V / 32.58 mA = **44.1 Ω** = unpowered value |

Napkin loop [H]: 10 V = 0.5 V (Q2 E-C) + I·44 Ω + ≈ 8 V (Q1 E-B breakdown + B-C diode) → I ≈ 33 mA. Matches all four numbers.
At higher rails I ≈ (2·rail − 8.5)/44 Ω → do not raise the rails on this board.

Touch test at ±5 V found nothing: the short dissipates only ≈ 47 mW; Q1 takes ≈ 0.26 W.

### B0.3 — node map at ±5 V, Fluke 45 as voltmeter, Fluke out of the rail (Xantrex 0.04 A on both outputs)

| Node (to J2 GND) | V [B] |
|---|---|
| VCC+ after F1 = Q2 pin 3 (E) | +4.970 |
| Q2 base (R2/R3) | +4.961 |
| V+: Q2 tab / U1 pin 7 / U2 pin 7 | +4.908 / +4.907 / +4.907 |
| V−: Q1 pin 3 / U1 pin 4 / U2 pin 4 | +3.1332 / +3.1345 / +3.1355 |
| Q1 base (R4/R5) | −4.288 |
| VCC− after F2 = Q1 tab (C) | −4.950 |

- KVL: 0.063 (Q2 E→C) + 1.773 (short) + 8.083 (Q1) = 9.919 V = rail to rail ✓. Short = 1.773 V / 0.04 A ≈ 44 Ω ✓.
- **Q2 shorted E–C** [B + H]: V_EB = 9 mV (needs ≈ 0.6–0.7 V to conduct) while 40 mA flows E→C with 63 mV (≈ 1.6 Ω).
- **Q1**: B-C forward 0.66 V, E-B in reverse breakdown at 7.42 V (rated 3 V [DS]) → β probably degraded.
- **Which IC: U1 (TLE2141), moderate confidence.** µV readings (lowest range, slow): U2 p4 − U1 p4 = −0.04 mV,
  U1 p4 − Q1 p3 = +0.14 mV, U2 p4 − Q1 p3 = +0.09 mV (self-consistent to 0.01 mV) → U1 pin 4 highest → U1 sources the
  current into V−. U1 p7 − U2 p7 = 0. Trace routing not known (no PCB file checked).

### Unpowered confirmation (Fluke 45 Ω)
| E → C | Ω [B] |
|---|---|
| Q2 on the client board | **1.74** (= the ≈ 1.6 Ω from 63 mV / 40 mA powered) |
| spare MJD350, out of circuit | 43.5 M (healthy reference) |
| Q1 on the client board | MΩ range (not shorted) |

No other path from Q2 E to C is below tens of kΩ (bias chain, junctions) → **Q2 shorted E–C, confirmed.**

### B0.4 — heat test, RL removed (Xantrex set "5.75 V"; V+ ≈ 4.89 V says the + output stayed ≈ 5.0 V, − output ≈ 5.8 V)

| Run | on | I (Fluke 45) | V+ / V− | short | P in short | touch U1 / U2 |
|---|---|---|---|---|---|---|
| `B0_pm05p75V_heat_noRL` | ≈ 17 s | 51.63 mA | +4.97 / +2.73 V | 43.3 Ω | 0.12 W | not done |
| `B0_pm05p75V_heat2_noRL` | ≈ 41 s | 57.79 mA | +4.89 / +2.41 V | 42.9 Ω | 0.14 W | no warmth on either |

- Short is the same ≈ 43–44 Ω at 33, 40, 52 and 58 mA → resistive, not changing with current or time.
- V− rose ≈ 70 mV over the first 15 s of heat2 then held: Q1's E-B breakdown voltage warming up [H].
- Touch is a weak test at 0.14 W: SOIC-8 ≈ 100–160 °C/W [ASSUME] → +14–23 °C, near what a fingertip can tell from skin
  temperature. "No warmth" does not clear either IC.
- Each figure: power-up single shot (left) + 16-avg trend (right); raw CURVe? counts in `*_raw.csv`, `*_startup_raw.csv`.

## Verdict
Board dead as built: IC supply short 44 Ω (U1 likely) + **Q2 shorted E–C (confirmed)** + Q1 E-B overstressed (not
shorted) + Q1/Q2 design errors.
Acceptance tests A1–A7 cannot run on it. To make it testable: Q1 → MJD350, Q2 → NPN on bodged pads, replace U1
(and U2 if damaged) — user + client decision.

## Open
- Definitive IC identification: Altium PCB routing of V+/V−, or lift U1 pin 7 and re-measure V+–V− unpowered (rework).
- Step 0 1 Hz / 10 Hz flatness + edge time to redo (scope byte-order bug, fixed 2026-11-06), needed only for A3/A4.

## Files
- `bench/` — scope runs: `*_startup.csv` / `*_startup_raw.csv` (power-up single shot), `*_wave.csv` / `*_raw.csv` (16-avg captures, raw CURVe? counts), `*_trend.csv`, `*.png`.
- `photos/` — bench photos used in `../../BENCH-B0-SUMMARY.docx` (JPEG, EXIF-rotated, ≤ 2400 px; originals on the phone): P1 bench, P2 Xantrex + Fluke at ±5 V, P4 board close-up, P4a pre-power meter readings, P5 harness, P6 probe points, P7 heat-run panels, P8 Q2 E–C vs spare.
- `figs/B0_schematic_compare.png` — client reference circuit vs Altium schematic, annotated.
- Report: `../../BENCH-B0-SUMMARY.docx`, generator `../make_b0_summary_docx.js` (needs Node + the `docx` package).
