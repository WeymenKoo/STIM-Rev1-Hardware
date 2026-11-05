# A1 Bias point and bootstrap window — record

**Question.** Does the client board's floating op-amp supply (the bootstrap window) form at the rails we can actually put on the bench, and can it deliver the command?
**Status.** sim done 2026-10-27 (LTspice 26.0.2, Weymen) · bench pending Nov 3

## Setup
| | Sim [L] | Bench [B] |
|---|---|---|
| Circuit | `A1-bias-bootstrap.asc`, client-board model (generic op-amp macromodels) | client STIM board, as received |
| Rails | ±30 V and ±100 V, ideal | two 30 V supplies in series, 50 mA limit (±45 V if a third supply is available) |
| Stimulus | 2 mA and 5 mA pk, 300 Hz sine, 50 Ω source | function generator, 2 and 5 V pk |
| Load | 1 kΩ | 1.00 kΩ 0.1 % |
| Measured | VP−VN window; VP, VN, REF, OUT at current peak; rail current; I_load | DMM on VP/VN/REF/OUT test points; supply current readout; scope across load |

## Result
| Quantity | Sim ±30 V | Bench ±30 V | Sim ±100 V | Bench ±100 V | Tol. | Pass |
|---|---|---|---|---|---|---|
| Window VP−VN (avg / min) | 4.97 / 4.95 V | | 19.4 / 19.4 V | | ±2 V | |
| VP−OUT / VN−OUT at idle | +2.55 / −2.42 V | | +9.78 / −9.62 V | | ±1 V | |
| I_load at 2 mA cmd (+ / −) | 2.000 / −2.000 mA | | 2.000 / −2.000 mA | | ±1 % | |
| REF−VN min at 2 mA (U1 low-side headroom) | **0.92 V** | | 8.1 V | | — (the model-validation number) | |
| VP−REF min at 2 mA (U1 high-side headroom) | 1.05 V | | 8.3 V | | — | |
| I_load at 5 mA cmd (+ / −) | **+4.01 / −3.38 mA (clips)** | | 4.995 / −4.995 mA | | ±1 % (100 V only) | |
| REF−VN / VP−REF during the 5 mA plateaus | 0.20 V / 1.00 V | | 5.8 / 6.0 V | | — | |
| Rail current (2 mA / 5 mA) | 5.2 / 6.0 mA | | 5.9 / 6.8 mA | | ±20 % | |

Figures: `A1_30V_2mA.png`, `A1_30V_5mA.png`, `A1_100V_2mA.png`, `A1_100V_5mA.png` — three panes: I_load vs command; OUT/LOAD/VP/VN/REF with the rails; window and U1 headroom (REF−VN, VP−REF). Bench traces overlay on the same axes (`plot_a1.py`, from the `.raw`; bench CSV overlay to add).

## Verdict
At ±100 V the model reproduces the archive (19.4 V window, 5 mA delivered). At ±30 V the window scales with the rail, as the R1–R4 divider predicts, down to ~5 V (±2.4 V around OUT) — inside the INA149's ±2 V minimum supply [DS] but with 0.9 V of headroom, so 2 mA is clean and 5 mA is not. The limiter is not the INA149 but U1: it must hold REF = OUT − I·R7 (R7 = 1 kΩ sense) inside a window centred near OUT, so the low-side headroom is ~2.9 V − I·1 kΩ. The 5 mA command plateaus at +4.01 mA (REF−VN pinned at 0.20 V) and −3.38 mA (VP−REF pinned at 1.00 V) — the asymmetry is the model's op-amp swing limits. The ±30 V bench session is therefore a bootstrap-headroom test at 5 mA and a pump test only at 2 mA.

## What it changes
- Nov 3 session: A2–A5, A7 run at 2 mA; A1 itself at 2 and 5 mA (the clip is the thing to see).
- Book a third supply if possible (±45 V ≈ 7.5 V window).
- Full-current tests wait for the HV module (PLAN.md, Oct 31 purchase request).

## Caveats
- Op-amp headroom near a 4.8 V total supply is where macromodels are least trustworthy; the bench number for REF−VN at 2 mA is the one to believe. The 5 mA plateau levels (+4.0 / −3.4 mA) calibrate the model's swing limits directly.
- Smaller RL does not help at ±30 V: the headroom is I·R7 across the on-board sense resistor, not across the load.
- Rev 1 parking lot: any change to R7 or the bias divider must re-check window ≥ 2·(I·R7 + swing headroom) at the lowest specified rail (10 mA → 10 V across R7).
