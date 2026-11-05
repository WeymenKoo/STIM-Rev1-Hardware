# G1 Rev 1 pump step response (OPA192 + Darlington + 14.3k) — record

**Question.** Does the Rev 1 pump ring on a 0 -> 5 mA step at +/-30 V (JP1/JP2 closed) and at +/-100 V, and is it
worse than the client pump (A3/A4)? Decides: keep the Darlington, or pre-apply the rework recipe (README) before the order.
**Status.** not built · due Oct 30 (sim chat) · decision needed before the Nov 5 freeze

## Setup
| | Sim [L] | Bench [B] (twin = R1 with A3/A4 on Rev 1 #1) |
|---|---|---|
| Circuit | from archive `3-compliance-and-limiter/2-load-reach/load-reach-rev1-pump.asc`; U1 = OPA192 model; JP1/JP2 RB1/RB2 41.2k switchable by `.step` | Rev 1 #1, JP4 ON (limiter out), JP5/JP6 ON |
| Rails | +/-30 V (bias jumpers closed), +/-100 V | +/-30 V |
| Stimulus | A3 PWL: 0 -> 5 mA step, 1 µs edge, 50 Ω source; A4 `.ac` for the loop peak | function generator, same edge |
| Load | 1.00 kΩ (and 1 kΩ ‖ 100 nF electrode case) | 1.00 kΩ 0.1 % |
| Measured | overshoot %, t to 1 %, `.ac` peak dB and frequency | scope, diff probe across the load |

## Result
| Quantity | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Client A3/A4 (same rails) | Pass |
|---|---|---|---|---|---|---|

Pass = overshoot and loop peak no worse than the client pump by more than [Weymen sets the margin before running].

## Verdict

## What it changes
- BoM: QD1/QD2 fitted, or DNP + B-E bridges + R3/R4 10k.
