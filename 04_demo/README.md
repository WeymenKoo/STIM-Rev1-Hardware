# DR1 demo (Dec 1): one stimulus, two tracks, same plots

Hardware track: FPGA (Red Pitaya Z7020) OUT1/OUT2 (±1 V) → DAC_CMD (Rev 1 U3 at G = 5.02: 5.02 mA/V; contract in
`02_rev1_channel/ICD_J3.md`) + ENABLE → Rev 1 board (or the client board at
±30 V if Rev 1 slips past the Nov 12 cutoff) → foam-head phantom (client's: two Al plates + 4.7 kΩ 1 %; at ±30 V use
1 kΩ) → scope on the electrode BNC and on I_RETURN_ADC.
Software track: the same CSVs → PWL sources → `01_client_board/client-board-model.asc` (or the Rev 1 netlist) →
4-channel current plots. Overlay bench and sim on the same axes.

## What CPEN1/CPEN2 deliver (by Nov 14)
1. **CSV format** (one file per channel, as the client's pipeline already does): header `t_s,i_mA`, 1 kHz rows,
   starts and ends at 0 mA, |i| ≤ 5 mA, and `sum over channels = 0` at every row. Plus `make_waveforms.py`:
   sine 1–25 Hz, square 1 Hz, and a 300 Hz burst, 4 channels (3 source + 1 return, or 2+2).
2. `csv_to_pwl.py`: CSV → LTspice PWL text file (`t i`), so the sim track reads the same files.
3. FPGA output verified on a scope at ±1 V full scale (= ±5 mA through U3 at G = 5), 1 kHz update, before Nov 20
   (bench twin of the CSV). The client board has no U3 gain: on it ±1 V gives only ±1 mA.
4. ENABLE line: high only while the waveform runs; DAC at 0 V when ENABLE is low.

## What Weymen delivers
- `demo_single_channel.asc`: client-board model with a PWL source and the phantom load, ready to run on CSV.
- Bench setup sheet and the overlay plots.

## Demo script (5 min)
1. Show the CSV sum-to-zero check. 2. Run the sim, show 4 currents. 3. Same file on the FPGA into the phantom,
scope trace next to the sim. 4. Load step (unplug the 4.7 kΩ → 10 kΩ): compliance visible on V_ELEC_ADC.
