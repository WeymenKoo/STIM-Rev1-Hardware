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
| Scope, fallback | **Tektronix TBS1000C** (bench), 2 × 10× probes | bench | USB (pyvisa) → `bench_tbs.py` | 2 ch, 8 bit: A1 walks CH2 across nodes, A4 adds a channel-gain cal |
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

## No DHO804: `bench_tbs.py` (TBS1000C, 2 channels)

Same commands, options, prompts, CSV/PNG names and `session_log.csv` as `bench_rig.py` (it imports it).
```
python bench_tbs.py check        # lists TBS1xxxC + DG1022, prints which TBS command forms the firmware took, probe attenuation
python bench_tbs.py preflight    # both probes on PROBE COMP in turn: must read ≈5 V (catches 1X/10X), then gen → CH1
python bench_tbs.py a1 --rl <RL1> --onset    # CH1 LOAD fixed, CH2 walks OUT → VP → VN → REF (prompted)
python bench_tbs.py a2 / a5b / a4 --extra / a3 / a7 --rl <RL1> ...
```
- A1: every capture triggers on LOAD; captures are aligned on the LOAD 300 Hz phase before VP−VN, REF−VN, VP−REF are formed.
- 8 bit: 16× averaging + auto V/div. A1 1b ±1 % and A4 absolute gain are indicative; A2 (Fluke 45) is the ±1 % arbiter.
- A4: CH1 also clipped on INPUT for 20 s first; CH1/CH2 gain (±3 % each [DS]) is divided out. A3: 16 averages per capture.
- A7: CH2 on VCC+ (free channel) shows when the + rail leaves and returns.
- Press Default Setup on the scope first (trigger mid-screen), set CH1/CH2 probe menus to 10X.
- Windows: `py -m pip install -r requirements.txt`. If `check` lists nothing, either install TekVISA / NI-VISA
  (then `--visa ivi`), or Zadig → WinUSB driver on the TBS and DG1022 + `py -m pip install libusb-package` (`--visa py`).
- Verified on a TBS1102C, FV v1.29.38, over NI-VISA (`--visa ivi`) on 2026-11-06. Two firmware quirks are handled in
  code: CURVe? data arrives LSB-first although BYT_Or reports MSB (fixed order, `check` re-verifies it with a 2-div
  position-shift test), and MEASUrement:IMMed:VALue? can return the previous acquisition's value (never used to detect
  a change). The DG1022 needs `\n` terminators and a write → wait → read instead of query(); `OUTP ON` is read back
  and re-sent (one was dropped silently). Preflight 1 Hz / 10 Hz and the edge time were taken before the byte-order
  fix and must be redone before A3/A4.
- Fluke 45 on its mA input drops ≈ 13 Ω × I (≈ 0.4 V at 33 mA [B]). For a rail-voltage-sensitive measurement jumper
  it out and use the Xantrex meter for current.

## Agent-driven session (prompts answered from chat)
`relay.py <answer_file> <script> <args>` runs any script with its `input()` prompts answered from a file, so the
scripts can run while someone else reads the meters: `py relay.py C:\...\ans.txt bench_tbs.py a1 --rl 1016.5 --visa ivi`.

## B0 — as-built bring-up (added 2026-11-06, see ../tests/B0-bringup/README.md)
The inherited board is not the modelled circuit (Q1/Q2 polarity and pads). These scripts record it without exceeding
IC ratings; CH1 on the Q2 tab (V+), CH2 on Q1 pin 3 (V−), grounds on J2, generator held at 0 V / OFF.
```
py b0_window.py <rail_V> --tag <name> --transient 0.05 --window 60    # arm, print READY, say GO; single-shot power-up edge, then 16-avg captures until the rails go off
py b0_figure.py <base> <rail_V> <I_mA> --note "..."                   # one figure per run: power-up (left) + trend (right); raw CURVe? counts in *_raw.csv
py bringup.py <rail_V> <I_plus_mA>                                     # one-shot capture + pass/fail against the as-built prediction
```

## What the script does that the sheet cannot
- A1: reads VP/VN/OUT/LOAD as waveform means, cursors at the current peak, REF−VN and VP−REF minima from the arrays (no scope math), plateau fraction at 5 mA, onset sweep 2→4 mA in 0.25 mA steps (1 min).
- A4: sine-fit of LOAD and INPUT at each frequency → ratio and phase, immune to noise; 11 points in 3 min.
- A3: single-shot, edge time of the generator, overshoot, last exit from the ±1 % band, ring frequency, both timebases.
- Overlays: sim dashed [L] from the `.raw` files, bench solid [B], same axes (A1, A3, A4).

## Not automated (and why)
- Supplies: Xantrex has no interface. Korad is scriptable but single, used only for the A7 + rail drop.
- Fluke 45: RS-232 only (needs USB-serial + DB9 cable; `--dmm-port` if you have one, untested). Typing six readings is faster than finding the cable.
- Rail-current meters: none of them talk.
