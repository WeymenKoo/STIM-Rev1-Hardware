# Changelog

All notable changes to the STIM Rev 1 channel KiCad project. Format: [Keep a Changelog](https://keepachangelog.com); versions follow semantic versioning applied to hardware (nguyen-v KDT_Hierarchical_KiBot README, maskset.net "Semantic Versioning for Hardware", 2023-02-26): see the project README.

## [Unreleased]

### Changed

- Rev 1 cut to the analog path for bench bring-up (rev1-minimal-design-definition.md): HV input and fusing, clamp, buffer on the +/-9 V LDOs, Howland pump, DN2540 limiter, two PhotoMOS switches driven by ENABLE, TVS, current and electrode-voltage read-back for the FPGA ADC. 115 parts (was 156).
- FPGA connector J3 pinout: DAC_CMD, ENABLE, I_RETURN_ADC, V_ELEC_ADC, VMID_REF and grounds; no power.
- Rail shunts RSP/RSN 10 Ohm (current measurement; were 47 Ohm for the removed over-current trip).
- Descriptive net names (BLOCK_FUNCTION), values with tolerance / rating / size, every symbol and footprint in the project libraries, op amps drawn with their supply pins, power rails as power symbols, sheets left-to-right in stage order, top sheet unwired (sheet pins only).
- PCB: 4-layer JLCPCB JLC04161H-7628 stackup and cited HV design rules.
- Low-voltage input J2: one +12 V (+12V_IN) on a 2P 5.08 mm screw terminal; +/-12 V now made on the board (U32); +5 V removed, R50 (LM4040 bias) fed from +9 V and re-valued 5.1k (D-20).
- U1, U3: OPA171 -> OPA192 (KPI 1 passes without the zero calibration; D-21).
- AQY214S symbol: pins visible (they were hidden), datasheet link to LCSC C719755.
- 3D models stored in lib/3d_models and referenced through ${KIPRJMOD}; every footprint except the mounting holes has a body.
- Document formatting after the FoC Motor Controller and EPFL Xplore AMULET schematics: cover page with page index, view frames and notes; grey block frames with captions on every circuit sheet; Revision History page in dated columns. Root sheet UUID realigned so page numbers follow the [n] sheet titles.
- PCB and footprint text in JetBrains Mono (silkscreen bold); board set to embed its fonts.
- RLED1 931 -> 750 Ohm (D6 in series with the PhotoMOS LED string).
- Passives resized: 0603 by default; 0805 for R3/R4 (54 mW), R7/R70 (precision current set), RLIM1 (select on test) and the 10 uF 25 V MLCCs; 1206/2512 only for voltage or power (bias string, HV dividers, RLED1, rail shunts). One part per value spec, larger size wins (R21 -> 1206 with R60/R61). Every passive now has an LCSC part.

### Added

- Bench bias jumpers JP1/JP2 (41.2k across each half of the bias string) for +/-15..30 V bench supplies; current-loop header JP3 in the stimulating line; 29 test loops; M3 mounting holes H1-H4; read-back stage (OPA4192: x20.1 on the return shunt, VMID adder, divider buffer, VMID buffer); CHANGELOG.md; Report/; U32 A1212S-2WR3 isolated DC-DC (12 V -> +/-12 V) with input capacitor C38 and its SIP-6 footprint; red indicator LEDs D6 OUT EN (PhotoMOS on), D7 HV LIVE (R60/R61 200k), D8 PWR (R62 15k), with LABEL fields printed on the silkscreen.

### Removed

- +5 V rail and the -12 V / +5 V pins of J2.
- Over-current sense, return-mismatch trip, trip comparators, fault latch, POR, rail monitors, enable logic, parking switch U6, threshold ladders (all stay simulated in 03_sim/rev1.py for Rev 2).

## [1.0.0] - 2026-10-23

### Added

- Initial capture of the full Rev 1 channel (P5) from expected_netlist.csv and BOM.csv (P4): 14 sheets, 156 parts, 0 netlist differences, ERC clean.
