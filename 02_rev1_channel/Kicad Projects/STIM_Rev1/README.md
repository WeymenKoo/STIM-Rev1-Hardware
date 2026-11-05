# STIM Rev 1 Channel (KiCad project)

+/-100 V INA149 Howland current-pump stimulator channel: the minimal analog path for bench bring-up (Rev 1), trips and
latch return in Rev 2. UBC ELEC 491, JY063. Status: **PRELIMINARY** (rev 2.1.0-dev, 2026-10-28), schematic edits from
`SPICE_SIM/02_rev1_channel/REVIEW_2026-10-27.md` applied (D-H); PCB placed, not routed. Bench prototype, dummy loads
only, not a safety sign-off.

**The KiCad files in this repository are the source.** The first capture was generated from the simulation
repository (SPICE_SIM, `4-rev1-design/05_schematic/tools/gen_schematic.py`), but the schematic has been edited
by hand in KiCad since 2.0.0. Do not re-run the generator over this folder.

Part selection and comparison (PhotoMOS, op amps, DC-DC module, connectors, LED, passive sizing):
`Documentation/STIM_Rev1_Parts_Selection.xlsx`, one sheet per part with a summary and charts above the comparison table.
FPGA interface (J3) contract: `SPICE_SIM/02_rev1_channel/ICD_J3.md` (draft until CPEN signs it; **out of date since 2026-11-04**: J3 is now SPI + ENABLE + 3.3 V, see CHANGELOG).

## Specifications

Tags: [N] ngspice, [L] LTspice, [H] hand calc, [DS] datasheet, [B] bench (none yet).

| Parameter | Rev 1 |
|---|---|
| Output | +/-5 mA, 1 mA/V at DAC_BUF (R7 1.00k). U3 gain = 1 + RF3/RG3: **5.02 with RG3 fitted** (Red Pitaya OUT1/OUT2, +/-1 V), 1 with RG3 DNP (+/-5 V DAC) |
| Command ceiling | G = 1: D3/D4 clamp, ~6.3-7.4 mA. G = 5: U3 output saturation at the +/-9 V LDO rails, ~9 mA. DN2540 limiter behind both |
| Compliance | 5 mA into >= 13 kOhm at a 90 V rail, worst case: 13.15 kOhm [N, model-dependent, archive WS1; margin ~1 %, not yet measured] |
| Rails | +/-100 V nominal (90-110 V) on J1; one +12 V on J2; +/-12 V from U32 (A1212S module). U32 is an isolated part but its COM is GND: **Rev 1 has no isolation**; FPGA-to-electrode isolation is deferred to Rev 2 |
| HV input | F1/F2 0451.500MRL 500 mA 125 VDC (rail-to-rail short at +/-100 V exceeds the rating: open item); RSP/RSN 10 Ohm shunts; C2/C3 1 uF 400 V with R23/R24 200k bleeders (tau 0.2 s) |
| Bench supplies | two 30 V supplies in series, midpoint to GND, bias jumpers JP1/JP2 closed (`02_rev1_channel/rev1-minimal-design-definition.md` §5 [N]) |
| Limiter | DN2540 pair + RLIM1, 6.4-8.8 mA [N]. **M1/M2/RLIM1 DNP at assembly**, paired and fitted at bring-up (R2); JP4 bypasses the limiter until then, never at +/-100 V |
| Switches | two AQY214S PhotoMOS (stimulating U4, return U5) driven by ENABLE (R22 100k pull-down = open). JP5/JP6 bypass them (OFF by default); with ENABLE low an ammeter across JP5 measures the stimulating-line current |
| Read-back | I_RETURN_ADC = VMID + 0.2 V/mA; V_ELEC_ADC = VMID + V_elec/101; VMID_REF 1.66 V; sized for a 0-3.3 V ADC on sheet 12 (part pending) |
| FPGA connector J3 | 2x8 IDC: +3V3_FPGA, SPI (SCLK, MOSI, MISO, CS_DAC, CS_ADC), ENABLE, one spare GPIO, even pins GND_FPGA. FPGA side of the isolator (sheet 10); no analog on J3 since 2026-11-04. ICD_J3.md still describes the old analog pinout |
| Board | JLCPCB 4-layer JLC04161H-7628, 1.6 mm, Economic PCBA (top side). Target outline <= 100 x 100 mm (4-layer promo tier) |
| Parts | 122 references: 89 parts (M1, M2, RLIM1 DNP), 29 test loops TP1-TP29, 4 mounting holes. Sheets 10-12 (SPI isolator, DAC, ADC) are ports only, parts pending. Power sheets 3-4 export their rails as ports; the rail symbols sit on the cover |

## Pages

1. Doc - Cover (`STIM_Rev1.kicad_sch`)
2. Doc - Revision History (`revision-history.kicad_sch`)
3. Power - HV Input & Fusing (`power-hv-input.kicad_sch`)
4. Power - Aux Input & +/-9 V LDOs (`power-aux-input.kicad_sch`)
5. Interface - FPGA (`interface-fpga.kicad_sch`)
6. Analog - Input Clamp & Buffer (`analog-clamp-buffer.kicad_sch`)
7. Analog - Howland Current Pump (`analog-current-pump.kicad_sch`)
8. Output - Limiter & PhotoMOS (`output-limiter-photomos.kicad_sch`)
9. Sense - Feedback to ADC (`sense-feedback-adc.kicad_sch`)
10. Interface - SPI Isolator (`interface-spi-isolator.kicad_sch`) - ports only, parts pending
11. Interface - DAC Command (`interface-dac-command.kicad_sch`) - ports only, parts pending
12. Interface - ADC Read-back (`interface-adc-readback.kicad_sch`) - ports only, parts pending

## Directory structure

```
STIM_Rev1
├── CHANGELOG.md     # Keep a Changelog; the Revision History page is generated from it
├── Templates        # KDT_Template_GIT.kicad_wks title block (nguyen-v/KDT_Hierarchical_KiBot, MIT)
├── Report           # ERC report (DRC after layout)
├── Testing/Testpoints   # test-point tables (after layout)
├── lib
│   ├── lib_sym      # STIM_Rev1.kicad_sym: every symbol of the design
│   ├── lib_fp       # STIM_Rev1.pretty: every footprint of the design
│   └── 3d_models    # STEP models
├── Simulation
│   ├── models       # SPICE models used by the symbols' simulation fields
│   └── figures      # simulation figures
├── Computations     # rev1_hand_calcs.md (the Oct 24 PDF is in _archive/)
├── Documentation    # parts selection workbook (xlsx)
├── Schematic        # PDF of the schematic
├── Manufacturing
│   ├── Assembly     # BoM, CPL (after layout, Fabrication Toolkit)
│   └── Fabrication  # Gerbers, drill (after layout)
└── Images           # renders
```

## Design rules

4-layer JLCPCB stackup and HV rules in `STIM_Rev1.kicad_dru`, with sources: SPICE_SIM `4-rev1-design/07_pcb/design-rules-research.md`.

## Format and versioning

Layout follows the EPFL Xplore AMULET controller schematics and the KDT_Hierarchical_KiBot template by the same
author (https://github.com/nguyen-v/KDT_Hierarchical_KiBot): folder tree, title block (`Templates/`, MIT licence
alongside), text variables (`PROJECT_NAME`, `BOARD_NAME`, `COMPANY`, `DESIGNER`, `VARIANT`, `REVISION`,
`RELEASE_DATE`, `SHEET_NAME_n`, `RELEASE_TITLE_x` / `RELEASE_BODY_x`), `CHANGELOG.md` with an `[Unreleased]`
section, and the variant vocabulary DRAFT / PRELIMINARY / CHECKED / RELEASED. Versions are semantic versioning
applied to hardware (https://www.maskset.net/blog/2023/02/26/semantic-versioning-for-hardware/): MAJOR incompatible
interface or form factor, MINOR compatible circuit / BoM / stackup change, PATCH documentation only. KiBot CI from the
template is not set up here.
