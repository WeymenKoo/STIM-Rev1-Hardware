# Client-board characterisation: the eight steps and their figures

**The deck:** [Current-pump characterization](../presentations/02_current-pump-characterization.pptx) (54 slides, 25 figures, plus an empty LTspice schematic page and LTspice plot page per step for your own screenshots). To use it in Google Slides, upload it to Drive and choose *Open with → Google Slides*. It also opens in PowerPoint and Keynote. The deck holds pasted LTspice screenshots, so edit it directly (it has no generator).

Each `<N>-<step>/` folder holds that step's figures (PNG and SVG), the LTspice netlists that produce them, a `make_figures.py` script, and a README with the same captions as the slides and instructions for recreating the plots in LTspice. The step numbers match the deck.

| Step | Question | Headline | Figures |
|---|---|---|---|
| 1 | Does the bootstrapped current pump work? | 5.001 mA delivered for a 5.000 mA command into 10 kΩ; op-amps held at ≈19.5 V while the output swings ±55 V | 1–4 |
| 2 | What load can it drive at 5 mA? | Up to 13.75 kΩ at ±100 V; ±120 V reaches 17.75 kΩ, ±150 V 23.5 kΩ | 5–7 |
| 3 | Is it fast enough for 1 kHz DAC updates? | Within 1 % of a new value in ≤5.4 µs: ≈0.5 % of each 1 ms interval | 8–10 |
| 4 | Is it accurate across the stimulation band? | Error ≤0.15 % from 1 Hz to 10 kHz; +6.5 dB peaking at 741 kHz | 11–12 |
| 5 | What happens when the supplies misbehave? | Out-of-order power-up: 22 mA pulse; a lost rail: continuous 9.7 mA | 13–15 |
| 6 | Does converter ripple leak into the load? | 34 µA per volt at 150 kHz, peaking near 0.8 MHz; ≤42 mVpp allowed at the client flyback's 950 kHz | 16–18 |
| 7 | How stable is the loop? | Stable (Nyquist) for six loads and for 0.33×–3× loop gain, but lightly damped; Bode margins do not apply | 19–22 |
| 8 | Output impedance and accuracy | Z_out 251 MΩ near DC (8 MΩ with the 50 Ω generator), 4.4 MΩ at 1 kHz; ±1 % from 0.5 to 5 mA, worst case and Monte Carlo | 23–25 |

Steps 7 and 8 use the test library's injection points and error terms (`client-board-channel-subcircuit.lib`); the underlying benches were the Monte Carlo and loop-gain tests of the original verification suite (Git history before commit 102f7f5).

## Ready-to-run LTspice schematics

Each step folder has a copy of `client-board-model.asc` with that step's sources and directives already set, plus a matching `.plt` file, so opening it and pressing **Run** brings up the step's plots:

| Step | Schematic | What Run shows |
|---|---|---|
| 1 | `1-bootstrap/bootstrap-floating-supply.asc` | Load current vs command; OUT, LOAD, VP, VN and the rails; VP − VN |
| 2 | `2-load-reach/client-board-load-reach.asc` | Load current for 5/10/15/20 kΩ; headroom VP − OUT and OUT − VN |
| 3 | `3-dac-step-response/dac-step-response.asc` | Load current and command for the DAC steps, 1k and 10k |
| 4 | `4-frequency-response/frequency-response.asc` | 1000·I(RLOAD) in dB and phase (0 dB = 1 mA/V), 1k and 10k |
| 5 | `5-power-sequencing/supply-sequencing-faults.asc` | Load current and rails for cases A, B, C (SEQ 1, 2, 3) |
| 6 | `6-converter-ripple/converter-ripple-into-load.asc`, `6-converter-ripple/converter-ripple-vs-frequency.asc` | Ripple current at 150 kHz; leakage vs frequency |
| 7 | `7-loop-stability/loop-gain.asc` | Double-injection loop gain T (dB, phase); U2 swapped for INA149GL |
| 8 | `8-output-impedance/output-impedance.asc` | Output impedance V(load) for a 1 A AC test current, 50 Ω and ideal source |

The schematics reference the symbols and `client-board-models.lib` in the project root (`..\..\`), so keep the folder structure. Figures that need the test library's error terms or injection points (step 2's reach sweep, step 7's Nyquist, perturbation, kick and RC tests, step 8's source comparison, floor and Monte Carlo) still run from the `.cir` files in those folders. If you change a plot layout and want to keep it, use *Plot Settings → Save Plot Settings* in LTspice; it overwrites the `.plt`. After editing `client-board-model.asc`, run `python3 make_schematics.py` to regenerate all of them (`--run` also test-simulates each one).

## Shared files
- `figlib.py`: plotting helpers used by steps 2–8 (plain Python, no libraries).
- `deck/fig01_schematic.png`: the LTspice schematic screenshot used on slide 2.
- PNGs are 3200×1800 (16:9). SVGs scale cleanly in PowerPoint, Keynote and Google Slides.

## Still to add by hand
The reviewers asked for native LTspice screenshots to back up the script-generated plots. The deck has an empty "LTspice schematic" and "LTspice plot" page after each step's figures: open that step's `.asc`, press Run, and paste the two screenshots there.

The captions in each step's README follow the deck text; edit both together.
