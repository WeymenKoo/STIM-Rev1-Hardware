# G2 Rail loss with the DN2540 limiter in — record

**Question.** With the limiter fitted (RLIM for 7.6 mA), what current reaches the load in A7's sequences at +/-100 V?
Is the limiter alone enough for Rev 1 (stays < 10 mA), or does Rev 1 need rail-presence -> ENABLE? Decides **D-A7**.
**Status.** not built · due Nov 5 (D-A7 filed with the schematic freeze)

## Setup
| | Sim [L] | Bench [B] (twin = A7 SEQ 2/3 on Rev 1, ±30 V first, ±100 V with the HV module) |
|---|---|---|
| Circuit | A7 schematic (`01_client_board/tests/A7-rail-loss/`) + limiter block from archive `1-safety-model/current-limiter-fixture.asc`; DN2540 Vgs(off) at both ends of the spread | Rev 1 #1, M1/M2/RLIM1 fitted (after R2), JP4 OFF |
| Rails | ±30 V, ±100 V | ±30 V, later ±100 V |
| Stimulus | A7 SEQ 1-3: 2 mA DC, one rail off/on | same, supply output-enable |
| Load | 1.00 kΩ | 1.00 kΩ |
| Measured | I_load peak and duration | scope across the load |

## Result
| Quantity | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|

Pass = |I_load| < 10 mA after the first µs in every sequence, both Vgs(off) corners.

## Verdict

## What it changes
- D-A7 (DECISIONS.md): limiter only, or add rail-presence -> ENABLE (Rev 2 if it misses the Nov 5 freeze).
