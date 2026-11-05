# A2 DC accuracy vs command — record

**Question.** Is I_load = V(INPUT)/1 kΩ within 1 % at every command the stimulator will use, at the rails we can bench?
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench pending Nov 3

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A2-accuracy-vs-command.asc`, client-board model (generic op-amp macromodels, no offset, exact 44.2 k / 10 k ratios) | client STIM board, as received |
| Rails | ±30 V and ±100 V, ideal | two 30 V supplies in series, 50 mA limit |
| Stimulus | DC command 0.5, 1, 2, 5, −2, −5 mA (V(INPUT) = 1 V/mA), 50 Ω source | generator DC offset 0.5, 1, 2, 5, −2, −5 V |
| Load | 1 kΩ | 1.00 kΩ 0.1 % |
| Measured | I(RLOAD) avg 1.2–2 ms | 6½-digit DMM across the load, I = V/R |

## Result
| Command | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|
| 0.5 mA | 0.5000 mA (−0.000 %) | | 0.5000 mA | | ±1 % | |
| 1 mA | 1.0000 mA | | 1.0000 mA | | ±1 % | |
| 2 mA | 2.0000 mA | | 2.0000 mA | | ±1 % | |
| −2 mA | −2.0000 mA | | −2.0000 mA | | ±1 % | |
| 5 mA | **3.837 mA (−23 %, clips)** | | 4.9955 mA (−0.09 %) | | ±1 % (100 V only) | |
| −5 mA | **−3.188 mA (−36 %, clips)** | | −4.9955 mA (−0.09 %) | | ±1 % (100 V only) | |

Figures: `A2_30V.png`, `A2_100V.png` — I_load vs command with the ±1 % band. Bench points go on the same axes.

## Verdict
Within the usable range the model is perfect to the µA, which is the model talking, not the board: the generic op-amps carry no offset and the Howland resistors have no tolerance. The 100 V 5 mA point shows −0.09 % from the clamp / finite loop gain. At ±30 V, ±5 mA clips (DC: +3.84 / −3.19 mA; A1 saw +4.01 / −3.38 at 300 Hz) — the A1 headroom limit, not an accuracy result.

## What it changes
- Bench pass band is set by the DMM and the 0.1 % resistor, not by the sim; expect a µA-class offset and a gain error from the real 44.2 k / 10 k mismatch. Those two numbers are what A2 produces.
- The ±30 V ±5 mA rows are recorded as the clip plateau, not graded.

## Caveats
- No resistor tolerance or op-amp offset in the model: the sim column is a zero-error reference, not a prediction.
