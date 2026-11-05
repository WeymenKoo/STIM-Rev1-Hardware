<!-- Claude: before every commit or push to this repo, update this README first (status line and date, folder table, anything that moved or was added). It is the only project-level document the team and the client read here; keep it short and factual. -->

# STIM Rev 1 hardware (JY063)

UBC ELEC 491 capstone, project JY063. One channel of a four-channel electrical vestibular stimulator:
a ±100 V bootstrapped Howland current pump (the client's STIM board) and our Rev 1 bench prototype of it.

**Status 2026-11-04.** Client-board LTspice model and acceptance tests A1–A7 simulated; bench measurements at ±30 V in
progress. Rev 1 schematic at 2.1.0-dev (PRELIMINARY): PCB placed, not routed. Safety protection is planned for Rev 2;
Rev 1 is a bench prototype for dummy loads only, not a safety sign-off.

| Folder | What is in it |
|---|---|
| `01_client_board/` | LTspice model of the client's STIM board (`model/`), acceptance tests A1–A7, one folder each (`tests/`), bench rig script and wiring (`bench/`), the sim-vs-bench table (`acceptance-tests.md`), deck 2 (`deck/`) |
| `02_rev1_channel/` | Rev 1 analog channel: KiCad project `Kicad Projects/STIM_Rev1/` (own README and CHANGELOG), design definition, FPGA interface contract `ICD_J3.md`, gate simulations G1/G2 (`tests/`) |
| `03_safety_plan/` | Safety planning for Rev 2: FMEA table, safety-loop architecture and its KiCad sketch, deck 1 |
| `04_demo/` | DR1 demo (Dec 1): FPGA waveform CSV → bench and → simulation, same plots |

**Running a simulation.** Open the `.asc` in LTspice 26.x and run it. Every directive is on the sheet; results are
written to the SPICE error log by `.meas` (View → SPICE Error Log). `.raw` and `.log` outputs are not committed;
rerun to regenerate them. Each test folder has a `RECORD.md` with the question, setup and the sim and bench values.

**Number tags.** [DS] datasheet, [H] hand calculation, [L] LTspice, [N] ngspice, [B] bench, [ASSUME] assumption.

Owner: Weymen Koo. Earlier simulation work (Oct 19–25, 2026) is kept offline and is not part of this repository.
