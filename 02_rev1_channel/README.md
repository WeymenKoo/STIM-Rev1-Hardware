# Rev 1 analog channel

KiCad source: `Kicad Projects/STIM_Rev1/` (rev **2.1.0-dev**, 13 sheets, 175 references = 133 parts incl. 3 DNP
+ 38 test loops + 4 holes; placed, **unrouted**; PCB not yet updated from the 2026-11-08 schematic). Review and action plan: `REVIEW_2026-10-27.md` (decision D-H).
Design definition: `rev1-minimal-design-definition.md` (approved 2026-10-25; changed since, see below).
FPGA interface: `ICD_J3.md` (rewritten 2026-11-07 for the SPI pinout; to CPEN for sign-off). Requirements background: `design_brief.md` (archive-era).

## Decision 2026-10-27/28: configurable, not stripped (D-D, D-H)

Rev 1 keeps the OPA192 + Darlington pump, the DN2540 limiter and the PhotoMOS switches. The limiter and the switches
can be jumpered out on the bench; the Darlington cannot (no footprints), and the fallback is the rework recipe below.
The "client pump as built" reference is the client's own board, measured on Nov 3, not a jumper position on Rev 1.

## Schematic edits — status 2026-10-28

| # | Block | Edit | Status |
|---|---|---|---|
| 1 | HV input (sheet 3) | R23/R24 200k 1206 bleeders across C2/C3 (ELE-02) | done (review called them R60/R61) |
| 2 | Clamp + buffer (sheet 6) | U3 non-inverting, RF3 40.2k / RG3 10.0k 0.1 %, G = 5.02 fitted, unity with RG3 DNP; TP13 on DAC_CMD | done; RF3 LCSC number open |
| 3 | Limiter (sheet 8) | JP4 header across the limiter (I_SENSE to LIM_OUT); M1/M2/RLIM1 DNP, hand-fit at bring-up | done (header instead of the review's 0 Ω DNP) |
| 4 | PhotoMOS (sheet 8) | JP5 across U4, JP6 across U5, open by default | done; JP3 removed (JP5 with ENABLE low is the current loop) |
| 5 | Fuses (sheet 3) | F1/F2 0451.500MRL 500 mA 125 VDC | done; **open:** 125 VDC does not cover a +HV to -HV short at +/-100 V |
| 6 | ERC, Update PCB from Schematic, schematic PDF | | **Weymen, in KiCad** (not runnable from here) |
| 7 | J3 silk labels with the ICD ranges | layout | at layout |

Then: BoM 100 % LCSC (RF3, U30/U31 have no LCSC number), extended-type count (~35), DRC, pre-order checklist
(archive deck 5 part A), order Nov 10.

## Rework recipe: if the Darlington pump rings at bring-up (replaces old "bypass edit #1")

DNP QD1 and QD2 (or lift them) and bridge each one's B-E pads with a solder blob, so the bias string drives the Q1/Q2
bases directly; swap R3/R4 14.3k -> 10k 0805. The pump is then the client's topology with an OPA192 for U1.
Decided by G1 before the order: if G1 shows ringing, ship the recipe pre-applied (DNP QD1/QD2 + 0 Ω / 10k in the BoM).

## Gate sims before the order (tests/, same RECORD template as 01_client_board)

| ID | Question | Build from | Bench twin | Decides | Due |
|---|---|---|---|---|---|
| G1 | Does the Rev 1 pump (OPA192 + Darlington + 14.3k) ring on a 0 -> 5 mA step at +/-30 V (JP1/JP2 closed) and +/-100 V? | archive `3-compliance-and-limiter/2-load-reach/load-reach-rev1-pump.asc` + A3 PWL + A4 `.ac` | A3/A4 on Rev 1 (R1) | keep Darlington or pre-apply the rework | Oct 30 |
| G2 | With the limiter in (RLIM for 7.6 mA), what reaches the load in A7's sequences at +/-100 V? | A7 + archive `1-safety-model/current-limiter-fixture.asc` | A7 SEQ 2/3 on Rev 1 | D-A7 | Nov 5 |

Stop there: no Monte Carlo, corners or thermal; those are read off the board. Built by the sim chat.

## Acceptance
Same table as `../01_client_board/acceptance-tests.md`: A1-A5 at +/-30 V (JP1/JP2 closed), A6 only with the HV
module, plus R1-R5 and the G rows. Bring-up order (review §6): aux rails and read-back first (R5, R4, R3), then HV
with the limiter jumpered (JP4 ON), then fit the DN2540 pair and RLIM1 (R2) and repeat with the limiter in.

## Interface (2026-11-07)
J3 carries SPI (three chip selects) + ENABLE + 3.3 V from the FPGA; on-board DAC (U40 AD5761R), two ADCs (U41 I, U42 V, ADS8689) and
two ISO7741 isolators (U43 = default-low F part for ENABLE / SCLK / MOSI, U44 default-high for the chip selects and MISO). J5 / JP7 bypass the isolators without rework. +5V / +3V3
LDOs on sheet 13. Decisions still open for Weymen: DAC range vs RG3 (G = 1 with +/-5 V, or +/-3 V range with G = 5);
LCSC numbers for TPS7A4901, 32.4k / 17.8k 0603, 1 uF 0603 and the 2x8 IDC
header. The Red Pitaya OUT1/OUT2 +/-1 V path (RG3 fitted, G = 5) stays as the DR1 fallback. See `ICD_J3.md`.
