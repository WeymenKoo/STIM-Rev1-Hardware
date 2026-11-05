# A5a Output impedance (AC injection) — record

**Question.** What is Z_out of the pump vs frequency, i.e. how much does the load (electrodes, 1–10 kΩ, variable) modulate the current?
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · no bench twin (A5b is the bench test)

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A5a-output-impedance-ac.asc`: 1 A AC current into LOAD, command 0, RL = 1 GΩ; V(LOAD) = Z_out. Generator source resistance stepped 50 Ω / ideal | — |
| Rails | ±30 V and ±100 V | — |

## Result
| Frequency | Sim ±30 V, 50 Ω gen | Sim ±30 V, ideal | Sim ±100 V, 50 Ω gen | Sim ±100 V, ideal |
|---|---|---|---|---|
| 1 Hz | 8.2 MΩ | 300 MΩ | 8.2 MΩ | 303 MΩ |
| 100 Hz | 8.1 MΩ | 43 MΩ | 8.1 MΩ | 44 MΩ |
| 1 kHz | 3.9 MΩ | 4.4 MΩ | 3.9 MΩ | 4.4 MΩ |
| 10 kHz | 435 kΩ → C_out 36.6 pF | 437 kΩ → 36.5 pF | 442 kΩ → 36.0 pF | 443 kΩ → 35.9 pF |

Archive (100 V): 8.2 MΩ (50 Ω gen), 251 MΩ ideal, ~36 pF. Figures: `A5a_30V.png`, `A5a_100V.png`.

## Verdict
Rail-independent. Near DC the 50 Ω generator unbalances the Howland bridge and sets Z_out at 8 MΩ — the source impedance, not the pump, is the limit. Above ~100 Hz Z_out is the ~36 pF output capacitance. For a 10 kΩ electrode at 1 kHz, 36 pF is 4.4 MΩ: a 0.2 % current change for the full load range — well inside 1 %.

## What it changes
- Rev 1 DAC/buffer: the command source must present ≪ 50 Ω (or be inside the loop) or Z_out is capped at a few MΩ at DC. Already a derived requirement in the STIM sim deck; this is the record for it.
- A5b is the bench statement of this: "no measurable current change 1 k → 2.2 k".

## Caveats
- Sign: at DC the 50 Ω case gives a slightly *negative* Z_out (current rises with load, A5b) — classic Howland mismatch, harmless at this magnitude.
