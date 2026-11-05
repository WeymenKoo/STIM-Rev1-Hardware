# A3 Step response and settling — record

**Question.** How fast does the pump settle to 1 % after a DAC-sized step, and how much does it overshoot? (Sets the 1 kHz update feasibility and the A4 loop-peak expectation.)
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench pending Nov 3

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A3-step-settling.asc`, client-board model | client STIM board |
| Rails | ±30 V and ±100 V | ±30 V |
| Stimulus | 0 → +Istep at 100 µs, +Istep → −Istep at 600 µs, 1 µs edges; Istep = 2 mA and 5 mA | generator square 0 / 2 V, fastest edge (note the actual edge time) |
| Load | 1 kΩ | 1.00 kΩ |
| Measured | I(RLOAD): final (300–500 µs), peak (100–300 µs), overshoot vs final, last exit from the ±1 % band after the edge end (101 µs) | scope across the load, single-shot, 2 µs/div on the edge; cursor peak and last exit from ±1 % |

## Result
| Quantity | Sim ±30 V (2 mA) | Bench ±30 V | Sim ±100 V (2 mA) | Bench ±100 V | Sim ±100 V (5 mA) | Tol. | Pass |
|---|---|---|---|---|---|---|---|
| Overshoot vs final | 18.4 % | | 10.7 % | | 10.3 % | ±10 pts | |
| Settles to ±1 % (after edge end) | 2.75 µs | | 1.65 µs | | 1.61 µs | ±50 % | |
| Final value | 2.000 mA | | 2.000 mA | | 4.996 mA | — | |

30 V / 5 mA clips at 4.30 mA (A1) — not graded. Archive (100 V, 5 mA, 1 µs edge): 2.6–5.4 µs, ~26 % overshoot.
Figures: `A3_30V_2mA.png`, `A3_100V_2mA.png` (+ 5 mA versions). Lower pane is the edge zoom with the ±1 % band.

## Verdict
The model rings once and is inside 1 % within 3 µs — far faster than a 1 kHz update needs, and faster than the archive's 2.6–5.4 µs, so the model has changed in a way the bench must arbitrate. The overshoot is larger at ±30 V (18 % vs 11 %) — less loop headroom near the small window — which is a prediction the bench can check directly.

## What it changes
- Nothing in the requirement: 1 kHz update (1 ms) vs ~3 µs settling leaves 300× margin either way.
- A4: expect a loop peak around 0.6–0.7 MHz (see A4). The overshoot and peak are the same physics.

## Caveats
- The 1 µs edge is the generator's, not the DAC's; do not read damping from it (sheet note). Record the bench edge time.
- Overshoot in a macromodel with no PSRR and ideal C2/C3 is indicative only.
