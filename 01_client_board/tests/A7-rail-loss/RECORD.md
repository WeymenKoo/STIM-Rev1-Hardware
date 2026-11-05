# A7 Supply sequencing and single-rail loss — record

**Question.** What current reaches the load when one rail is missing — at power-up with staggered supplies, or if a rail fails mid-stimulus? (FMEA input: is the 10 mA hard limit exceeded?)
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench: SEQ 2 and 3 only, Weymen's call, Nov 3 if time

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A7-rail-loss.asc`, client-board model, 2 mA DC command | client STIM board |
| Rails | ±30 V and ±100 V; SEQ 1: +rail ramps 0.5–1.5 ms, −rail 4.5 ms later. SEQ 2: both up, +rail collapses at 10–11 ms. SEQ 3: both ramp together | ±30 V, supply output-enable buttons, 50 mA limit |
| Load | 1 kΩ | 1.00 kΩ |
| Measured | I(RLOAD) max, min, final (40–60 ms) | scope across the load, single-shot on the enable event; DMM for the final value |

## Result
| Case | Sim ±30 V | Bench ±30 V | Sim ±100 V | Tol. | Pass |
|---|---|---|---|---|---|
| SEQ 1, +rail alone for 4.5 ms: I peak | **+6.6 mA** (plateau while −rail absent) | (not safe by hand — seconds, not ms) | **+23.4 mA** | ±50 % | |
| SEQ 2, +rail lost, continuous | **−5.9 mA** | | **−9.7 mA** | ±50 % | |
| SEQ 3, together: I peak | 2.02 mA (2 mA cmd) | | 2.07 mA | — | |

Archive (100 V, command 0): −9.7 mA continuous after +rail loss. Figures: `A7_30V.png`, `A7_100V.png` — three sequences per rail with the ±10 mA lines.

## Verdict
Losing the positive rail drives the load with a continuous negative current set by the remaining rail: −5.9 mA at ±30 V, −9.7 mA at ±100 V — at the 10 mA hard limit with the client board and nothing in the way. Staggered power-up is worse: +23 mA while only the +rail is present at 100 V. Simultaneous ramp is clean. These are macromodel numbers for op-amps operated outside their supply range; the direction and order of magnitude are what to trust, not the decimals.

## What it changes
- FMEA row: single-rail loss → up to 10 mA DC into the patient. Rev 1 needs either the DN2540 limiter in that path, rail-presence sensing that opens the PhotoMOS, or both. Decision record needed.
- Power board: both rails must come up together (SEQ 3) and the bootstrap/flyback design must not allow one rail to collapse alone.

## Caveats
- SEQ 1 cannot be reproduced by hand (ms stagger); only SEQ 2 and 3 are bench twins. At ±30 V with the 50 mA supply limit and a 1 kΩ resistor the board sees 6 mA × 30 V — safe for the parts; it is still the client's only prototype.
