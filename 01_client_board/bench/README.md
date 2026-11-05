# Bench rig — client STIM board at ±30 V (MCLD 3042 bench + what Weymen brings)

One script runs each acceptance test, prints bench vs expected with pass/fail, writes CSV + overlay PNG into
`../tests/<ID>/bench/`, and appends every number to `session_log.csv`. The printed sheet
(`../BENCH-SESSION_30V.docx`, harness/kit page included; figures in `figs/`) has the same quantities in the same order — copy the script's numbers onto it.

## Equipment (no equipment-pool loan needed)

| Role | Instrument | Where | Control | Why this one |
|---|---|---|---|---|
| Rails | **Xantrex XPH 35-4T** (2 × 0–35 V, floating, own ON/OFF per output, I-limit down to 10 mA) | 3rd-year bench | front panel | two isolated outputs on one chassis → ±30 V (or ±35 V) series stack, mid-point = GND |
| Rails, backup / A7 scripted | Korad KA3005P (bring) | — | USB-serial | only ever as the **+** rail with (−) on GND: its USB ground may be bonded to the output (−) |
| Scope | **Rigol DHO804** (bring), 4 × 10× probes | — | USB (pyvisa) | 4 ch + 12 bit; lab's TBS2104B is 4 ch too but no script |
| Generator | **Rigol DG1022** | bench | USB (pyvisa) | HiZ setting, ~10 ns edges, scripted sweeps; FG085 is the fallback (`--gen manual`) |
| DMM, precision | **Fluke 45** (5-digit slow mode: 0.025 % + 2 d DCV, 0.05 % Ω, 1 µA on 30 mA range) | bench | type readings | resolves the ±1 % A2 call with 25× margin; BM235 (0.3 %) cannot |
| DMM, second | Brymen BM235 (bring) | — | type readings | second rail current in A1 |

Rail current: Xantrex meter resolves 10 mA, useless at 5 mA → Fluke 45 in series with VCC+, BM235 in series with VCC−.
Both rails together: the Xantrex has no master switch. Preset 30.0 V / 50 mA on both outputs with the outputs OFF,
then turn both ON with two fingers and OFF the same way (A7 SEQ 3 measures what that stagger does; A7 sim says
+6.6 mA for the ~100 ms one-rail state at ±30 V, not destructive into 1 kΩ with 50 mA limits). If the board's
J3 mating plug (Molex Micro-Fit 3) is available, make a 3-wire pigtail and plug/unplug with both outputs live instead.

## Setup on the Mac (before the session, 10 min)

```
pip3 install -r requirements.txt          # pyvisa pyvisa-py pyusb pyserial numpy matplotlib
brew install libusb                       # USB-TMC backend for pyvisa-py
python3 bench_rig.py check                # must list a DHO8xx and (at the bench) a DG1022
```
DHO804 over LAN works too (`--scope TCPIP::<ip>::INSTR`, Utility → IO → LAN on the scope). The DG1022 is USB only.
If the DG1022 does not enumerate, `--gen manual` prints every setting (Vpp and Vpk) and waits for Enter — the FG085 works the same way.

## Running order (≈ 2 h with the script, 3 h by hand)

| # | Command | Prompts you for | Time |
|---|---|---|---|
| 0 | `preflight` | probe on probe-comp, then generator → CH1 direct. Checks the waveform decode and records the generator's own flatness and edge time. **Do this at home**, no board. | 10 min |
| 1 | `a1 --onset --rails 35` | rails on; rail currents (two DMMs); VCC±; Q2/Q1 base voltages; move CH2 OUT→REF→OUT. `--rails 35 40 50` only if a second dual supply (TTI EX354RT) is on the bench. | 40 min |
| 2 | `a2` | Fluke 45 on INPUT then LOAD at six DC commands | 10 min |
| 3 | `a5b` | Fluke 45 in series, one RL swap | 5 min |
| 4 | `a4 --extra` | nothing (CH2 on INPUT) | 3 min |
| 5 | `a3` | nothing | 5 min |
| 6 | `a7` | + output OFF / ON; both OFF / both ON (or `--korad /dev/tty.usbserial-*` for a scripted + rail) | 10 min |

Always: `--rl <measured RL1>` (Fluke 45 Ω, leads zeroed), `--rl2 <RL2>`. If A1 says 2 mA is a few % low, add `--cmd-scale 0.5` to 2–6.

## What the script does that the sheet cannot
- A1: reads VP/VN/OUT/LOAD as waveform means, cursors at the current peak, REF−VN and VP−REF minima from the arrays (no scope math), plateau fraction at 5 mA, onset sweep 2→4 mA in 0.25 mA steps (1 min).
- A4: sine-fit of LOAD and INPUT at each frequency → ratio and phase, immune to noise; 11 points in 3 min.
- A3: single-shot, edge time of the generator, overshoot, last exit from the ±1 % band, ring frequency, both timebases.
- Overlays: sim dashed [L] from the `.raw` files, bench solid [B], same axes (A1, A3, A4).

## Not automated (and why)
- Supplies: Xantrex has no interface. Korad is scriptable but single, used only for the A7 + rail drop.
- Fluke 45: RS-232 only (needs USB-serial + DB9 cable; `--dmm-port` if you have one, untested). Typing six readings is faster than finding the cable.
- Rail-current meters: none of them talk.
