# A4 Small-signal frequency response — record

**Question.** Is I_load / V_cmd flat to 10 kHz, and where is the loop peak that the flyback switching frequency must avoid?
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench pending Nov 3

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A4-frequency-response.asc`, client-board model, AC analysis at command = 0 | client STIM board |
| Rails | ±30 V and ±100 V | ±30 V |
| Stimulus | AC 1 V, 1 Hz – 10 MHz, 50 Ω source | 2 mA pk sine at 1, 10, 100, 300, 1 k, 10 kHz |
| Load | 1 kΩ | 1.00 kΩ |
| Measured | mag and phase of 1000·I(RLOAD) (0 dB = 1 mA/V); peak | scope amplitude across the load (pk–pk ÷ 2 ÷ 1 kΩ) at each frequency, relative to the 1 Hz (or 10 Hz) value |

## Result
| Frequency | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|
| 1 Hz | 0.000 dB (ref) | | 0.000 dB | | ref | |
| 10 Hz | 0.000 dB | | 0.000 dB | | ±0.5 dB | |
| 100 Hz | 0.000 dB | | 0.000 dB | | ±0.5 dB | |
| 300 Hz | 0.000 dB, −0.01° | | 0.000 dB | | ±0.5 dB | |
| 1 kHz | 0.000 dB, −0.02° | | 0.000 dB | | ±0.5 dB | |
| 10 kHz | +0.002 dB | | +0.001 dB | | ±0.5 dB | |
| Loop peak | +6.0 dB at 603 kHz | (not measurable at 2 mA) | +6.5 dB at 741 kHz | | — | |

Figures: `A4_30V.png`, `A4_100V.png` — magnitude (dB re 1 mA/V) and phase, 1 Hz – 10 MHz, bench points as markers.

## Verdict
Flat to 10 kHz to within 2 mdB in the model, with 0.02° of phase at 1 kHz — the stimulation band is not where this circuit has any dynamics. The loop peak (+6 dB, 0.6–0.7 MHz) is the number that matters: it is where the Rev 1 flyback's switching frequency and harmonics must not sit, and it moves down with the smaller ±30 V window.

## What it changes
- Deck-2 must-fix: "0.23 % at 1 kHz" was a phase-lag figure; the current model gives 0.02° at 1 kHz. Restate from this record once the bench confirms flatness.
- Flyback f_sw keep-out: stay well below ~500 kHz or above ~1 MHz; A8 (rail ripple → load) tests this once the power board exists.

## Caveats
- Small-signal at command 0: amplitude-independent in the sim; the bench runs at 2 mA so ±30 V stays out of clipping.
- The peak frequency and height are macromodel GBW/phase-margin numbers; expect the bench to differ by a factor of ~2.
