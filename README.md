# STIM Rev 1 Channel (KiCad project)

+/-100 V INA149 Howland current-pump stimulator channel: the minimal analog path for bench bring-up (Rev 1), trips and
latch return in Rev 2. UBC ELEC 491, JY063. Status: **PRELIMINARY** (rev 2.0.0-dev, 2026-10-25), for design review.
Bench prototype, dummy loads only, not a safety sign-off.

**The KiCad files in this repository are the source.** The first capture was generated from the simulation
repository (SPICE_SIM, `4-rev1-design/05_schematic/tools/gen_schematic.py`), but the schematic has since been edited
by hand in KiCad. Do not re-run the generator over this folder.

Part selection and comparison (PhotoMOS, op amps, DC-DC module, connectors, LED, passive sizing):
`Documentation/STIM_Rev1_Parts_Selection.xlsx`, one sheet per part with a summary and charts above the comparison table.

## Specifications

| Parameter | Rev 1 |
|---|---|
| Output | +/-5 mA, 1 mA/V from the DAC (+/-5 V) |
| Compliance | 5 mA into >= 13 kOhm at a 90 V rail, worst case (13.15 kOhm simulated) |
| Rails | +/-100 V nominal (90-110 V) on J1; one +12 V on J2, isolated +/-12 V from the on-board DC-DC module U32 |
| Bench supplies | two 30 V supplies in series (or one split to +/-15 V) with the bias jumpers JP1/JP2 closed |
| Limiter | DN2540 pair, 6.4-8.8 mA |
| Switches | two AQY214S PhotoMOS (stimulating and return side) driven by ENABLE |
| Read-back to the FPGA ADC | I_RETURN_ADC = VMID + 0.2 V/mA; V_ELEC_ADC = VMID + V_elec/101; VMID_REF 1.66 V |
| Board | JLCPCB 4-layer JLC04161H-7628, 1.6 mm, Economic PCBA (top side) |
| Parts | 115 references |

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
├── Computations     # hand calculations (PDF)
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
