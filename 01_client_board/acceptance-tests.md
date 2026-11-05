# Acceptance tests: client STIM board (and Rev 1), sim ↔ bench

Schematics: `tests/<ID>-…/` (see `tests/README.md`). Model: `model/client-board-model.asc`.

Each row is one simulation with one bench measurement that uses the same stimulus and reads the same quantity.
Fill the Sim and Bench columns as numbers; Pass = within the stated tolerance. Tag values [L] LTspice, [B] bench.
Bench session (slipped from Nov 3; sheet `BENCH-SESSION_30V.docx`, rig `bench/bench_rig.py`): **±30 V** from the MCLD 3042 Xantrex XPH 35-4T (two floating 35 V outputs in series, mid-point = GND, 50 mA limits). Scope DHO804 (4 ch, scripted), generator bench DG1022 (scripted; FG085 fallback), DMM Fluke 45 5-digit (A2/A5b), BM235 rail current. Probe points per `Client_Prototype_HowlandPump.pdf` are listed on the sheet. A1 adds the Q1/Q2 Vbe rows and an optional window-vs-rail sweep (±35 V; ±50 V with a second dual supply) for the transistor question.
±100 V rows wait for the HV module. Load for ±30 V rows: 1.00 kΩ 1 % (and 2.2 kΩ where stated). Source: function
generator, 50 Ω, or the FPGA DAC once available (1 mA/V).

| ID | Test (archive step) | Stimulus | Measure | Sim ±30 V [L] | Bench ±30 V [B] | Sim ±100 V [L] | Bench ±100 V [B] | Tol. | Pass |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Bias point / bootstrap window (step 1) | 2 mA and 5 mA pk, 300 Hz sine into 1 kΩ | VP−VN window; VP, VN, REF, OUT vs GND at the current peak; rail current; I_load peak | window 4.97 V; REF−VN 0.92 V min at 2 mA; I = 2.000 mA; **5 mA cmd clips at +4.01 / −3.38 mA** (REF−VN 0.20 V); 5.2–6.0 mA/rail | | window 19.4 V; REF−VN 8.1 V (2 mA) / 5.75 V (5 mA); I = 2.000 / 4.995 mA; 5.9–6.8 mA/rail | | ±2 V window, ±20 % I | |
| A2 | Accuracy vs command (step 8) | DC 0.5, 1, 2, −2, 5, −5 mA into 1 kΩ | I_load = V(R_load)/R; error % | 0.000 % at 0.5–2 mA (no offset/tolerance in model); ±5 mA clips +3.84/−3.19 mA | | −0.000 % at 0.5–2 mA; −0.09 % at ±5 mA | | ±1 % of reading | |
| A3 | Step settling (step 3) | 0→2 mA step (5 mA at 100 V), 1 µs edge, 1 kΩ | t to 1 % of final; overshoot % | 2.75 µs; 18.4 % (2 mA) | | 1.65 µs; 10.7 % (2 mA); 1.61 µs; 10.3 % (5 mA) | | ±50 % t, ±10 pts | |
| A4 | Frequency response (step 4) | 2 mA pk sine, 1 Hz–10 kHz, 1 kΩ | I_load magnitude at 1, 10, 100, 300, 1 k, 10 k Hz | 0.000 dB to 1 kHz, +0.002 dB at 10 kHz; loop peak +6.0 dB at 603 kHz | | 0.000 dB; +0.001 dB at 10 kHz; peak +6.5 dB at 741 kHz | | ±0.5 dB | |
| A5 | Output impedance (step 8) | 2 mA DC; load 1.0 kΩ → 2.2 kΩ | ΔI / ΔV → Z_out | ΔI +0.015 %, |Z| 8.1 MΩ (50 Ω gen); A5a: 300 MΩ ideal, 36 pF | | same (rail-independent) | | order of magnitude; bench ΔI < 0.1 % | |
| A6 | Load reach / compliance (step 2) | 5 mA DC; sweep R_load | R at which I drops 1 % | n/a at ±30 V (bench: use 2.2 k, 3.3 k, expect clipping) | | 13.75 kΩ sink, 14.3 kΩ source (archive) | | ±10 % | |
| A7 | Power-up / single-rail loss (step 5) | 2 mA DC into 1 kΩ; switch one rail off, then on | I_load peak and duration during the event | +rail lost: −5.9 mA cont.; +rail first: +6.6 mA while alone | (SEQ 2, 3 only; Weymen's call) | +rail lost: −9.7 mA cont.; +rail first: +23.4 mA (model est.) | | ±50 % | |
| A8 | Rail ripple → load (step 6) | 100 mVpp at f_sw on one rail | I_load ripple | deferred to power board | | 0.29 Vpp→5 µA @150 kHz (archive) | | | |

## Rev 1 additions (only on the Rev 1 board)

| ID | Test | Stimulus | Measure | Sim [L] | Bench [B] | Tol. | Pass |
|---|---|---|---|---|---|---|---|
| R1 | Rev 1 pump vs client board (G1 bench twin) | A2, A3, A4 on Rev 1 (JP4 ON, limiter out), compared with the client-board A rows | same as A2/A3/A4 | G1 | | same | |
| R2 | Limiter I–V | DN2540 pair + RLIM1 hand-fitted, JP4 OFF; load 0 Ω; command 0→10 mA | I_out plateau (expect 6.4–8.8 mA before trim) | | | ±10 % | |
| R3 | PhotoMOS on/off | ENABLE 0→1→0, 2 mA into 1 kΩ | t_on, t_off, any current transient | | | < 1 ms, no overshoot > 10 % | |
| R4 | Read-back scaling | A2 currents; 10, 20, 50 V on electrode | I_RETURN_ADC, V_ELEC_ADC vs DMM | | | ±1 % | |
| R5 | ±9 V LDO / ±12 V DC-DC rails | +12 V in | rail values, ripple; U32 pinout check first | | | ±5 % | |

Gate sims for the Rev 1 order (G1 pump ringing, G2 limiter + rail loss = D-A7) live in `../02_rev1_channel/tests/`.

## Method notes
- Bench current: measure V across the 1 kΩ 0.1 % load with a 6½-digit DMM (DC) or scope differential probe (AC).
  Never a series ammeter in the loop above 1 kHz.
- Sim stimulus must be the bench stimulus: 50 Ω source, same edge time, same load value and tolerance.
- Same figure for both: overlay sim (dashed) and bench (solid) on one plot per row. That overlay is the DR1
  "simulation suite" evidence and the V&V plan's method.

## Deck 2 must-fix before it is shown again (from the Oct 20 review)
1. Nyquist/loop-gain slides (Figs 19–20) contradict closed-loop data: lead with closed-loop evidence, mark
   Figs 19–20 "not yet reconciled", delete the "RHP pole explains the 10 kΩ mismatch" sentence.
2. "0.23 % at 1 kHz" is phase lag (~0.36 µs), not amplitude error; reword Fig 23 and the Step 8 summary.
3. Wording: overshoot is vs final value; "settling adds ≤ ~3 µs variation"; "300 Hz: KPI upper band";
   fault currents are macromodel estimates; "300 boards × 2 loads"; remove the 16 placeholder slides.
