# ICD: Rev 1 analog board J3 <-> FPGA (Red Pitaya)

> **OUT OF DATE (2026-11-04):** the schematic now has J3 as a 2x8 IDC carrying SPI (SCLK, MOSI, MISO, CS_DAC, CS_ADC), ENABLE, one spare GPIO and +3V3_FPGA / GND_FPGA, with the DAC and ADC on the board behind an isolator (sheets 10-12). The analog pinout below is the 2.1.0-dev state before that change. Rewrite once the isolator/DAC/ADC parts are chosen.

JY063 · draft 2026-10-28 (Weymen) · **status: proposal, not agreed** · to CPEN1/CPEN2 by Oct 31, sign-off at the
Oct 31 review. Source of the board side: `Kicad Projects/STIM_Rev1` rev 2.1.0-dev, sheets 5, 6, 8, 9.

## Connector
J3, 2 x 5 shrouded IDC header, 2.54 mm (C225520). Odd pins = signals, even pins = GND. No power on J3.

| Pin | Signal | Direction | Range | Source Z / load | Board side (Rev 1) |
|---|---|---|---|---|---|
| 1 | DAC_CMD | FPGA -> board | **+/-1 V** (Red Pitaya OUT1/OUT2) with RG3 fitted, or +/-5 V (future DAC) with RG3 DNP | source <= 50 Ω; board input = RS1 1k + D3/D4 clamp to GND (~+/-6.9 V) + OPA192 (high Z) | U3 gain 5.02 (RG3 fitted) or 1; then 1 mA/V at DAC_BUF (R7 1.00k). **+/-1 V -> +/-5 mA** |
| 3 | ENABLE | FPGA -> board | 3.3 V CMOS; high = electrodes connected | R22 100k pull-down; drives Q20 2N7002 gate | low or open = both PhotoMOS open |
| 5 | I_RETURN_ADC | board -> FPGA | VMID + 0.2 V/mA: 0.66-2.66 V at -/+5 mA | 1k series (R54); ADC input >= 100 kΩ assumed | slow analog input, 0-3.5 V |
| 7 | V_ELEC_ADC | board -> FPGA | VMID + V_elec / 101: 0.57-2.75 V at +/-110 V | 1k series (R55) | slow analog input |
| 9 | VMID_REF | board -> FPGA | 1.658 V (LM4040 4.096 V x 10.0k / 24.7k) | 1k series (R53) | slow analog input; subtract in software from pins 5 and 7 |
| 2, 4, 6, 8, 10 | GND | common | | | board GND = HV midpoint = FPGA GND. **No isolation on Rev 1** (Rev 2 item) |

## Red Pitaya resources this assumes (STEMlab 125-14) — CPEN to confirm
- Fast analog outputs OUT1/OUT2: +/-1 V, 50 Ω, 14-bit, 125 MS/s: the only stimulus source for DR1, so DR1 is two
  channels (source + sink) without a DAC board.
- Slow analog inputs AI0-AI3 on extension header E2: 0-3.5 V, 12-bit; enough for 1 kHz telemetry of pins 5, 7, 9.
  The fast inputs (+/-1 V / +/-20 V) do not suit 0.66-2.66 V signals.
- 3.3 V GPIO for ENABLE.
- Ground: the Red Pitaya GND is tied to the board GND through J3. The lab supplies' midpoint is also GND: one ground
  point, no loops through the scope.

## Software contract
1. Command: i_mA = 5.02 x V_OUT (G = 5) or V_OUT (G = 1). Clip |i| <= 5 mA in software; the board ceiling is ~9 mA
   (U3 rails) at G = 5, limiter 6.4-8.8 mA behind it.
2. ENABLE high only while a waveform runs; OUT at 0 V when ENABLE is low; ENABLE low on any FPGA reset.
3. Read-back: I_mA = (V5 - V9) / 0.2; V_elec = (V7 - V9) x 101. Calibrate both once against a DMM (R4).
4. Two boards (source + sink) share GND and the return electrode (D-C).

## Questions for CPEN (answer by Oct 31)
1. Can DR1 use OUT1/OUT2 directly (two channels, +/-1 V)? If a DAC board is planned, what range and when?
2. Are AI0-AI3 usable at 1 kHz from your firmware, or do you need a different ADC range? (R51/R52 set VMID if so.)
3. Cable: ribbon IDC 2 x 5 from J3 to the Red Pitaya E1/E2 headers via an adapter — who makes the adapter?

## Change control
Changing a range here changes RG3, R51/R52 or the silk on J3. File the change in `SPICE_SIM/DECISIONS.md`.
