# Rev 1 minimal channel: design definition for the schematic capture

> **Status 2026-10-28: changed since approval** (rev 2.1.0-dev, D-H): JP3 removed (JP5 across U4 is the current loop with ENABLE low); added R23/R24 HV bleeders, RF3/RG3 U3 gain option, JP4 limiter bypass, JP5/JP6 PhotoMOS bypasses, TP13; M1/M2/RLIM1 DNP. Q4.2: the only DR1 source in hand is the Red Pitaya at +/-1 V, so U3 runs at G = 5 until CPEN signs `ICD_J3.md`. 126 references (93 parts + 29 test loops + 4 holes), not ~95.

JY063 · 2026-10-25 · status: **approved 2026-10-25 and captured** (`Kicad Projects/STIM_Rev1/`, see
`handoff-context.md` §10; the questions marked **Q** were answered with the proposed defaults). Decided with the
user on 2026-10-25 (answers A1-F1 in the chat); supersedes the "capture the full 156-part netlist" rule of
`kicad-capture-brief.md`. The full safety chain stays in `03_sim/rev1.py` and returns in Rev 2.

## 1. What Rev 1 is

A bench prototype of the analog path only, built to be probed: HV input and fusing, input clamp, input buffer on
±9 V LDOs, INA149 Howland current pump with the Darlington output stage, DN2540 current limiter, two PhotoMOS
switches driven straight from an ENABLE line, TVS, current and voltage read-back for the FPGA's ADC, and a
power / signal interface to the power-electronics board and the FPGA board. No trips, latch, enable logic, rail
monitors or parking switch.

## 2. Kept, removed, added (against `expected_parts.csv`)

| Block | Kept (designators unchanged) | Removed | Added |
|---|---|---|---|
| HV input | J1, F1, F2, C2, C3; RSP, RSN become **10 Ω 1 % 2512** (current-measurement shunts; was 47 Ω for the OC trip) | | TP on both sides of each shunt |
| Aux input | J2 (+12 V, −12 V, +5 V, GND from the power board), U30/U31 ±9 V LDOs with R30-R33, C32-C37 | | |
| Interface | J3 (FPGA) | FLT, RESET, RAILOK, PMON, DAC_CLR_N pins; R40 (ENREQ pull-down) becomes the ENABLE pull-down R22 | pins I_RETURN_ADC, V_ELEC_ADC, VMID_REF (§4) |
| Clamp + buffer | RS1, D3, D4, U3, C30, C31 | | |
| Pump | U2, U1, R7, R1-R6, D1, D1B, D2, D2B, Q1, Q2, QD1, QD2, C1, C40 | | **bench bias jumpers** JP1/JP2 with RB1/RB2 41.2 kΩ (§5) |
| Limiter | M1, M2, RLIM (select on test) | RPARK, U6 (parking) | |
| Output | U4, U5 (AQY214S), D5 (SMBJ100CA), R20A, R20B, R21, C21 (electrode-voltage divider), J4, RSHR 10 Ω 0.1 % | | **current-loop header** JP3 in series with the stimulating electrode line |
| LED drive | RLED, Q20 (2N7002), R22 (gate pull-down) | U27, U32, R23 | |
| Read-back (new sheet) | U22 OPA4192 (all four units), R70/R71 (re-valued), R72-R75 (difference amp 4 × 10 k), U29 LM4040A41, R50, R51, R52 | U23 (its job moves to U22D) | |
| Removed outright | | U20, U21, R60-R63, C62, C63, ROC*; R76, R77, C76, C77, RCMD, CCMD, RMIS*; U24, U25, U26, U28, R80, ROV*; U33, RUV*, R81; C9x decoupling of removed ICs | |
| Mechanical | | | H1-H4 M3 mounting holes (§7) |

Rough count: 156 → about 95 parts.

## 3. Sheets (top sheet left unwired; sheet pins ready)

| Page | Sheet | Contents |
|---|---|---|
| 1 | Cover | sheet symbols only (you wire it), H1-H4 |
| 2 | Revision History | from CHANGELOG.md |
| 3 | Power – HV Input & Fusing | J1, F1/F2, RSP/RSN, C2/C3, +HV_IN/−HV_IN → +HV/−HV |
| 4 | Power – Aux Input | J2, U30/U31 LDOs, +12V/−12V/+5V → +9V/−9V |
| 5 | Interface – FPGA | J3, ENABLE pull-down |
| 6 | Analog – Input Clamp & Buffer | RS1, D3/D4, U3 |
| 7 | Analog – Howland Current Pump | U2, R7, U1, bias string, Darlington stage, JP1/JP2 |
| 8 | Output – Limiter & PhotoMOS | M1/M2/RLIM, U4, D5, JP3, J4, U5, RSHR, RLED/Q20/R22 |
| 9 | Sense – Feedback to ADC | U22A-D, LM4040 reference, divider |

Signal flows left to right on every sheet in stage order; op amps drawn as one unit with V+/V− on the body; the
INA149 drawn as a difference amplifier (triangle, +IN/−IN left, OUT right, REF A/REF B below, V+ above, V− below);
every symbol and footprint in the local libraries. Power rails are power symbols; cross-sheet signals are hierarchical
sheet pins; everything else is a local net label. No notes, figures or frames in this pass.

## 4. Feedback to the FPGA's ADC (proposal, **Q**)

The FPGA team asked how current and voltage reach their ADC. Proposal: two analog voltages, both centred on a local
mid-rail reference so they fit a single-ended ADC of any range, plus the reference itself so the FPGA can subtract it:

| Signal | Source | Scale | Parts (one OPA4192, U22) |
|---|---|---|---|
| `I_RETURN_ADC` | return shunt RSHR 10 Ω (10 mV/mA) | VMID + 0.2 V/mA → ±1.0 V at ±5 mA | U22A non-inverting ×20 (R70 1.00 k, R71 19.1 k 0.1 %), U22B unity difference amp adds VMID (R72-R75 10 k 0.1 %) |
| `V_ELEC_ADC` | electrode divider R20A+R20B 20 M / R21 200 k returned to VMID | VMID + V_elec/101 → ±1.09 V at ±110 V | U22C unity buffer (20 pA bias) |
| `VMID_REF` | LM4040A41 4.096 V (U29, R50) divided by R51/R52, buffered | 1.65 V default (half of a 3.3 V ADC range); R51/R52 "select to ADC" | U22D buffer |

**Q4.1** ADC input range (0-3.3 V? 0-5 V? bipolar?). Default 0-3.3 V → VMID 1.65 V. **Q4.2** DAC command still
±5 V = ±5 mA (brief)? If the FPGA DAC is unipolar the command needs a level shift on their side or ours. **Q4.3**
ENABLE logic level (3.3 V assumed; 2N7002 is fine with either).

J3 (2 × 5, 2.54 mm): 1 DAC_CMD, 2 GND, 3 ENABLE, 4 GND, 5 I_RETURN_ADC, 6 GND, 7 V_ELEC_ADC, 8 GND, 9 VMID_REF, 10 GND.
No power on J3 (A7).

## 5. Bench testing from a small supply [N] (`03_sim/bench_feasibility.py`, `results/rev1/bench-feasibility.csv`)

| Supply | Change on the board | Result (±5 mA sine, 300 Hz) |
|---|---|---|
| ±100 V (client) | none | ±4.99 mA into 10 kΩ (sanity) |
| **one +30 V, −HV tied to GND** | none | **does not work**: the pump's floating negative rail cannot go below ground; the loop saturates and the limiter sets ~6.8 mA whatever the command |
| ±30 V dual (two single supplies in series, mid-point = GND) | none | ±5 mA into 1 kΩ; clips at 3 kΩ (compliance ±11.5 V) |
| ±30 V dual + bias jumpers closed | JP1/JP2 | ±5 mA into 3 kΩ (compliance ±15 V) |
| one 30 V split to ±15 V by a rail splitter + bias jumpers | JP1/JP2 + splitter | ±4.7 mA into 500 Ω, ±3.7 mA into 1 kΩ |
| ±12 V aux as pump rails + bias jumpers | | ±3.7 mA into 200 Ω: not worth it |

Why: the bias string (2 × 88.4 kΩ + 2 × 14.3 kΩ) is sized for ±100 V. Below ±30 V it passes too little current to
open the pump's floating supply (span 2.7 V at ±12 V, 6.9 V at ±15 V; the INA149 needs ≥ 4.5 V). JP1/JP2 put
41.2 kΩ in parallel with R1+R2 and with R5+R6 and restore ~0.3 mA.

**Recommendation:** add JP1/JP2 (two 2-pin headers, two 1206 resistors). For your room, **two single 30 V supplies
in series** (or a dual supply) with the mid-point as GND give ±30 V and a full ±5 mA into 3 kΩ with no other
hardware. **Q5.1** Do you want the on-board rail-splitter option too (one 30 V supply → ±15 V, TLE2426 + 2 caps +
jumper; ±4.7 mA into 500 Ω)? The splitter must carry the ground-referenced currents (stim return, LED string,
LDO loads: ~20 mA), and the 30 V supply must be floating. **Q5.2** The aux rails (±12 V, +5 V) are needed in the
room in any case: a triple-output bench supply, or a ±12 V / 5 V module? (The LDOs accept up to 36 V in, so in
split mode ±15 V could feed them directly through a second jumper pair if you want everything from one supply.)

## 6. Test points (loops only, one line item; HV loops spaced ≥ 1.5 mm from LV copper)

DAC_CMD, DAC_CLAMP, DAC_BUF, PUMP_OUT, PUMP_REF, PUMP_V+, PUMP_V−, I_SENSE, LIM_OUT, ELECTRODE_STIM, ELECTRODE_RET,
RET_SHUNT, I_RETURN_ADC, V_ELEC_ADC, VMID_REF, +HV_IN, +HV, −HV_IN, −HV, +12V, −12V, +9V, −9V, +5V, ENABLE,
PMOS_LED_K, GND × 3. JP3 (current loop) in the stimulating line. **Q6.1** Keystone 5001-style loops are 2.54 mm
pitch THT; fine?

## 7. Mounting holes (**Q**)

H1-H4: M3, 3.4 mm non-plated hole, copper keep-out as you specified (Ø 5 mm). **Q7.1** An M3 pan head is 5.5 mm
and a washer 7 mm; a 5 mm keep-out leaves copper under the head unless the mask is relied on. Keep 5 mm (nylon
standoffs?) or go to 6.5 mm? **Q7.2** Four holes, or one as written?

## 8. Net names (descriptive, pattern BLOCK_FUNCTION)

| Old (simulated) | New | Old | New |
|---|---|---|---|
| HV_P / HV_N | +HV_IN / −HV_IN (power) | VCCPS / VCCNS | +HV_FUSED / −HV_FUSED |
| VCCP / VCCN | +HV / −HV (power) | BUFP / BUFN | +9V / −9V (power) |
| NR30, FB30 / NR31, FB31 | LDO_P_NR, LDO_P_FB / LDO_N_NR, LDO_N_FB | DAC_OUT | DAC_CMD |
| CLAMP / ZMID / BUF | DAC_CLAMP / CLAMP_MID / DAC_BUF | ENREQ | ENABLE |
| OUT / REF / SENSE | PUMP_OUT / PUMP_REF / I_SENSE | VP / VN | PUMP_V+ / PUMP_V− |
| NR12 / NA / ND1 / ND1B | BIAS_R1_R2 / QD2_BASE / BIAS_R3_D1 / BIAS_D1_D1B | NBQ2 / NBQ1 | Q2_BASE / Q1_BASE |
| ND2B / ND2 / NB / NR56 | BIAS_D2_D2B / BIAS_D2B_R4 / QD1_BASE / BIAS_R5_R6 | LIMA / LIMB / LIMO | LIM_SRC_A / LIM_SRC_B / LIM_OUT |
| ELEC / RETE / RETS | ELECTRODE_STIM / ELECTRODE_RET / RET_SHUNT | NOV1 / OVS | VDIV_MID / V_ELEC_DIV |
| LEDA / LED1 / LED2 | PMOS_LED_A / PMOS_LED_1 / PMOS_LED_K | GATE | ENABLE (same net) |
| FBR / VRET1 | IRET_FB / I_RETURN_X20 | VMIDD / VMID / VREF | VMID_DIV / VMID / VREF_4V096 |

## 9. Checks that stay

`check_netlist.py` runs against a new `expected_netlist_rev1min.csv`, derived by script from the full list (blocks
removed, additions listed explicitly) with the name map above, so every pin is still checked independently of the
drawing. ERC must be clean. The bench cases above are the regression for the pump at low rails.

## 10. What I need from you to start the capture

Q4.1-4.3 (ADC range, DAC range, ENABLE level), Q5.1-5.2 (splitter option, aux supply in the room), Q6.1, Q7.1-7.2,
and a yes on §2-§4 and §8.
