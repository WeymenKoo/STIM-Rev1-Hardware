# <ID> <Test name> — record

**Question.** One sentence: what this test decides.
**Status.** sim done / bench done / closed · date · who ran it

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `<file>.asc`, model rev <date> | client board S/N / Rev 1 board #n, jumper config |
| Rails | | |
| Stimulus | | |
| Load | | |
| Measured | | instrument, probe, settings |

## Result
| Quantity | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|

One figure: `fig1.png` — sim dashed, bench solid, same axes. Caption says what to look at.

## Verdict
Two or three sentences. Does the model match the board? What number is now trusted, with which tag?

## What it changes
- Requirement / decision / next test affected, one line each. Nothing else.

## Caveats
Model-dependent? Instrument floor? Edge rate? One line each; skip if none.
