<!-- Claude: before every commit or push to this repo, update this README first (status line and date, folder table, anything that moved or was added). It is the only project-level document the team and the client read here; keep it short and factual. -->

# STIM Rev 1 hardware (JY063)

UBC ELEC 491 capstone, project JY063. One channel of a four-channel electrical vestibular stimulator:
a ±100 V bootstrapped Howland current pump (the client's STIM board) and our Rev 1 bench prototype of it.

**Status 2026-11-08.** Client-board LTspice model and acceptance tests A1–A7 simulated; bench measurements at ±30 V in
progress. Rev 1 schematic at 2.1.0-dev (PRELIMINARY): DAC (AD5761R), two ADCs (ADS8689), two ISO7741 isolators
with a bypass header and +5 V / +3.3 V rails added 2026-11-07/08 (sheets 10–13); PCB placed, not routed, not yet updated
from the schematic. Safety protection is planned for Rev 2;
Rev 1 is a bench prototype for dummy loads only, not a safety sign-off.

**Handover note (2026-11-08, Weymen away until about Nov 11).** Everything is in this repository; nothing is pending on a
local machine. If you pick this up:
1. Schematic: `02_rev1_channel/Kicad Projects/STIM_Rev1/` (KiCad 10). Read its `README.md` and the `[Unreleased]`
   block of `CHANGELOG.md` first; `Schematic/STIM_Rev1.pdf` is the current plot, `Report/STIM_Rev1-erc.txt` the
   current ERC (0 errors, 7 known warnings). Next KiCad steps: ERC in the GUI, Update PCB from Schematic, then layout.
2. Open decisions (owner Weymen, do not close without him): DAC range vs RG3 on sheet 6; LCSC numbers still TBD
   (TPS7A4901, 32.4k / 17.8k 0603, 1 uF 0603, 2x8 IDC header); ISO7741FDWR is LCSC/JLCPCB-only stock.
3. FPGA interface for CPEN: `02_rev1_channel/ICD_J3.md` (J3 pinout, three chip selects, read-back scaling).
4. Part sourcing snapshot: `.../STIM_Rev1/Documentation/sourcing_converters_isolators_2026-11-07.csv`.
5. Bench: client-board B0 bring-up records under `01_client_board/tests/B0-bringup/` and `01_client_board/bench/`.
Dates that matter: Rev 1 order target Mon Nov 10, hard cutoff Wed Nov 12 (DR1 Dec 1).

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
