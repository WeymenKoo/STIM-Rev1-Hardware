# A5b Output impedance by load change — record

**Question.** Does the current move when the load changes 1.0 → 2.2 kΩ at 2 mA? (Bench statement of A5a.)
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench pending Nov 3

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A5b-output-impedance-dc.asc`, client-board model, 50 Ω source | client STIM board |
| Rails | ±30 V and ±100 V | ±30 V |
| Stimulus | DC 2 mA command | generator DC offset 2 V |
| Load | 1.0 kΩ, then 2.2 kΩ | 1.00 kΩ 0.1 %, then 2.2 kΩ (measure it) |
| Measured | I(RLOAD) avg, V(LOAD) avg | DMM V across each load; I = V/R_measured |

## Result
| Quantity | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|
| I at 1.0 kΩ | 1.99999 mA | | 1.99999 mA | | — | |
| I at 2.2 kΩ | 2.00029 mA | | 2.00029 mA | | — | |
| ΔI / I | +0.015 % | | +0.015 % | | < 0.1 % (DMM floor) | |
| Z_out = ΔV / ΔI | −8.1 MΩ (magnitude 8.1 MΩ) | | −8.1 MΩ | | > 1.2 MΩ | |

Figure: `A5b.png`. Matches A5a's 8.2 MΩ with the 50 Ω generator.

## Verdict
A 2.4 V change in load voltage moves the current by 0.3 µA. On the bench that is below a 6½-digit DMM across 0.1 % resistors, so the pass is "no change resolved"; any resolved change > 0.1 % (2 µA) points at the real source impedance or a Howland resistor mismatch.

## What it changes
- Nothing new; closes the loop on A5a with a measurement that fits in 5 minutes.

## Caveats
- The resistor tolerance (0.1 % × two resistors) is the measurement floor, not the DMM.
