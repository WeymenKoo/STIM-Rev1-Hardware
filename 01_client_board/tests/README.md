# Acceptance tests — client STIM board model

One folder per test, one `.asc` each, every directive on the sheet, numbers written to the `.log` by `.meas`
(View → SPICE Error Log). Each test steps `Vrail` 30 and 100 so the two sim columns of
`../acceptance-tests.md` come from one run. Results (`.raw`, `.log`, screenshots) stay in the test's folder.

| Test | File | Runs | What the log gives | Bench twin (±30 V; `../bench/bench_rig.py <id>` writes `<test>/bench/`) |
|---|---|---|---|---|
| A1 | `A1-bias-bootstrap/` | 2 | VP−OUT, VN−OUT, VP−VN window, rail currents, OUT peak | scope means on VP/VN/OUT/LOAD, Fluke 45 + BM235 in series for rail current, Q1/Q2 Vbe rows; `a1 --onset [--rails]` |
| A2 | `A2-accuracy-vs-command/` | 10 | Iload, err_pct per command (0.5…5, −5 mA) | Fluke 45 (5-digit) on INPUT and LOAD at each DC command; `a2` |
| A3 | `A3-step-settling/` | 2 | Ifin, overshoot % vs final, entry to 1 % band, last exit | DHO804 single-shot CH1 LOAD / CH2 INPUT, DG1022 square 0/2 V (~10 ns edge: faster than the 1 µs sim stimulus); `a3` |
| A4 | `A4-frequency-response/` | 2 | mA/V at 1, 10, 100, 300, 1 k, 10 k Hz; 10 k vs 1 Hz in dB; phase at 300 Hz; loop peak freq | sine-fit ratio LOAD/INPUT at the six frequencies (+ extras), DG1022 scripted; `a4 --extra` |
| A5a | `A5a-output-impedance-ac/` | 4 | Z_out at 1, 100, 1 k, 10 k Hz; C_out | — (not bench-measurable) |
| A5b | `A5b-output-impedance-dc/` | 4 | Iload, Vload at 1 k and 2.2 k → Z_out by hand | Fluke 45 in series (30 mA range fixed), two loads, 2 mA; `a5b` |
| A7 | `A7-rail-loss/` | 6 | I max/min, I after the fault, Vload extremes | Xantrex per-output buttons on prompt (or Korad as + rail, scripted), SEQ 2 and 3 only; `a7` |

A6 (load reach) needs ±100 V and lives in the archive (`2-load-reach/`) until the HV module exists. A8 (ripple)
waits for the power board.

**Run order:** A1 first. If the 30 V run shows no floating window or OUT clipping at 5 V swing, stop and say so —
the Nov 3 session then measures A2–A5 at a lower command (2 mA) instead.

**Regenerate:** `python3 tests/make_tests.py` from `01_client_board/` (reads the archived step schematics, rewrites
every test; edit the script, not the copies). Symbols come from `../../model/`, the model library from
`../../model/client-board-models.lib`.

**Tags:** every number from these runs is [L] and model-dependent (generic op-amp macromodels, no offset, no PSRR).
Bench numbers are [B]. The archive's 100 V values are quoted in the sheet notes for comparison.

**Bench session sheet:** `../BENCH-SESSION_30V.docx` (the only one; earlier versions deleted 2026-11-04), built by `make_bench_session_docx.js` (needs `npm i docx`; `NODE_PATH=<node_modules> node make_bench_session_docx.js`). Harness figures: `../bench/figs/make_harness_figs.py`.
