# Changelog

All notable changes to the STIM Rev 1 channel KiCad project. Format: [Keep a Changelog](https://keepachangelog.com); versions follow semantic versioning applied to hardware (nguyen-v KDT_Hierarchical_KiBot README, maskset.net "Semantic Versioning for Hardware", 2023-02-26): see the project README.

## [Unreleased] (next: 2.1.0, PRELIMINARY)

Review `SPICE_SIM/02_rev1_channel/REVIEW_2026-10-27.md` §4 applied 2026-10-28 (decision D-H). Netlist checked against the 2.0.0-dev capture: only the nets listed here change.

### Changed (2.1.0-dev, 2026-11-04)

- J3 [5] re-pinned for the SPI path: 2x8 IDC (Conn_02x08_Odd_Even, IDC-Header_2x08 footprint and STEP added to the project libraries; LCSC part still to pick, C225520 was the 2x5). 1 +3V3_FPGA, 3 SPI_SCLK, 5 SPI_MOSI, 7 SPI_MISO, 9 SPI_CS_DAC, 11 SPI_CS_ADC, 13 ENABLE, 15 spare GPIO (NC), even pins GND_FPGA. The analog pins (DAC_CMD, I_RETURN_ADC, V_ELEC_ADC, VMID_REF) are gone from J3: [11] drives DAC_CMD, [12] reads the [9] outputs. [ASSUME] isolator side 1 is powered from the FPGA over J3 (ICD_J3 said no power on J3: open decision). New power symbols +3V3_FPGA and GND_FPGA (FPGA side of the barrier); PWR_FLAGs on both at J3.
- [10] SPI isolator placeholder: ENABLE in (FPGA side) / ISO_ENABLE out (board side) added; ISO_ENABLE drives the PhotoMOS sheet [8] (its ENABLE port is unchanged). Six channels now.
- Power sheets [3] and [4] export their rails as hierarchical ports (+HV, -HV, +12V, -12V, +9V, -9V); the global power symbols for those rails sit on the cover. Other sheets still use the power symbols directly; GND stays global everywhere.
- Cover re-laid: row 1 power ([3], [4] with the rail symbols), row 2 FPGA [5] -> isolator [10] -> DAC [11], row 3 clamp [6] -> pump [7] -> limiter [8] -> sense [9] -> ADC [12]; isolation barrier drawn through [10]. Sheets 10-12 were off the A3 page. Every sheet pin is wired to a stub with a net label; same-name labels join the long nets (ISO_*, DAC_CMD, ISO_ENABLE).
- J3 photo removed from [5] (it showed the 2x5 part). PCB not yet updated: run Update PCB from Schematic (J3 footprint 2x5 -> 2x8).

### Added (2.1.0-dev, 2026-11-03)

- Sheets [10] Interface - SPI Isolator, [11] Interface - DAC Command, [12] Interface - ADC Read-back: ports only, no parts yet (hierarchical labels and a design note each; parts to be selected). Isolator: SPI_SCLK / SPI_MOSI / SPI_CS_DAC / SPI_CS_ADC in, SPI_MISO out on the FPGA side; ISO_SCLK / ISO_MOSI / ISO_CS_DAC / ISO_CS_ADC out, ISO_MISO in on the isolated side. DAC: ISO_SCLK / ISO_MOSI / ISO_CS_DAC in, DAC_CMD out. ADC: I_RETURN_ADC / V_ELEC_ADC / VMID_REF and ISO_SCLK / ISO_MOSI / ISO_CS_ADC in, ISO_MISO out. Placed as a third row on the cover (mounting holes and the note legend moved down to make room). J3 on [5] keeps its analog pinout until the parts are placed, so DAC_CMD has two sheet outputs until then.

### Removed (2.1.0-dev, 2026-11-03)

- Sheet 7 Darlington driver stage (D-05): QD2 MMBTA42 / QD1 MMBTA92 and the second-VBE diodes D1B1 / D2B1. Q2 / Q1 bases now sit directly on the R2-R3 / R4-R5 bias-string nodes with one BAS16 (D1 / D2) between each node's divider and PUMP_OUT. Nets QD2_BASE / QD1_BASE merge into Q2_BASE / Q1_BASE; BIAS_D1_D1B and BIAS_D2_D2B are gone; BIAS_D2B_R4 renamed BIAS_D2_R4. 122 references (89 parts) now. Footprints QD1, QD2, D1B1, D2B1 remain on the PCB until the next Update PCB from Schematic.

### Added (2.1.0-dev, 2026-10-28)

- R23, R24 200k 1 % 200 V 1206 HV bleeders across C2 and C3 (ELE-02): tau = 0.2 s, 50 mW at 100 V. These are the bleeders the 2.0.0 entry below credited to R60/R61; R60/R61 and D7 HV LIVE were never captured, and D7 stays out (the bleeders are the safety item).
- RF3 40.2k 0.1 % / RG3 10.0k 0.1 % (0603): U3 becomes a non-inverting stage, G = 1 + RF3/RG3 = 5.02 with RG3 fitted (Red Pitaya OUT1/OUT2 are +/-1 V, so +/-1 V -> +/-5 mA), unity with RG3 DNP (+/-5 V DAC). New net DAC_BUF_FB. RF3 LCSC C723489 (YAGEO RT0603BRD0740K2L).
- JP4 limiter bypass (I_SENSE to LIM_OUT), JP5 across U4 (LIM_OUT to ELECTRODE_STIM), JP6 across U5 (ELECTRODE_RET to RET_SHUNT): 2-pin headers. JP5/JP6 OFF by default; with ENABLE low an ammeter across JP5 is the stimulating-line current loop.
- TP13 on DAC_CMD (the sheet 6 probe note referenced it; it was missing from the capture). 29 test loops now.

### Changed (2.1.0-dev, 2026-10-28)

- F1, F2: Littelfuse 0451.500MRL (NANO2 451, 500 mA fast, 125 VAC/VDC, LCSC C142836), replacing the SST0500 placeholder (no DC rating). 125 VDC covers a rail-to-GND fault; a +HV to -HV short at +/-100 V can put 220 V across one fuse (open item, sheet 3 note D1). Check the 451 land pattern against Fuse_2410.
- M1, M2 and RLIM1 DNP at assembly: the DN2540s are paired and RLIM1 selected from an E96 kit at bring-up (R2). JP4 stays ON until then.
- Sheet 6 notes D1/D2 and the U3 note: with G = 5 the D3/D4 clamp no longer sets the command ceiling; U3 saturating at ~+/-9 V (~9 mA) does, with the limiter behind it.
- Field notes on R23, R24, JP4-JP6, M1, M2, RLIM1 corrected (they were copied from other parts). JP4 note: OPEN AT HV, never bypassed at +/-100 V. RG3 note: caution on the G = 5 command ceiling.
- Stale "BoM update: P4 row has ..." suffixes removed from 30 Note fields on all sheets (leftovers of the 156-part capture; TP13/TP15/TP16 named RAILOK/GATE). R21 note now points at R23/R24, not R60/R61.

### Removed (2.1.0-dev, 2026-10-28)

- JP3 current-loop header in series with the stimulating line (ELECTRODE_SW net). Its job moves to JP5 with ENABLE low.

### Changed (2.0.0-dev, 2026-10-25)

- Rev 1 cut to the analog path for bench bring-up (rev1-minimal-design-definition.md): HV input and fusing, clamp, buffer on the +/-9 V LDOs, Howland pump, DN2540 limiter, two PhotoMOS switches driven by ENABLE, TVS, current and electrode-voltage read-back for the FPGA ADC. 115 parts (was 156) at capture; 126 references at 2.1.0-dev (93 parts, 29 test loops, 4 mounting holes).
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
- Passives resized: 0603 by default; 0805 for R3/R4 (54 mW), R7/R70 (precision current set), RLIM1 (select on test) and the 10 uF 25 V MLCCs; 1206/2512 only for voltage or power (bias string, HV dividers, RLED1, rail shunts). One part per value spec, larger size wins (R21 -> 1206, same part as the R23/R24 bleeders). Every passive now has an LCSC part.

### Added (2.0.0-dev)

- Bench bias jumpers JP1/JP2 (41.2k across each half of the bias string) for +/-15..30 V bench supplies; current-loop header JP3 in the stimulating line (removed in 2.1.0-dev); 28 test loops (TP13 added in 2.1.0-dev); M3 mounting holes H1-H4; read-back stage (OPA4192: x20.1 on the return shunt, VMID adder, divider buffer, VMID buffer); CHANGELOG.md; Report/; U32 A1212S-2WR3 isolated DC-DC (12 V -> +/-12 V) with input capacitor C38 and its SIP-6 footprint; red indicator LEDs D6 OUT EN (PhotoMOS on) and D8 PWR (R62 15k), with LABEL fields printed on the silkscreen (D7 HV LIVE was planned but never captured).

### Removed (2.0.0-dev)

- +5 V rail and the -12 V / +5 V pins of J2.
- Over-current sense, return-mismatch trip, trip comparators, fault latch, POR, rail monitors, enable logic, parking switch U6, threshold ladders (all stay simulated in 03_sim/rev1.py for Rev 2).

## [1.0.0] - 2026-10-23

### Added

- Initial capture of the full Rev 1 channel (P5) from expected_netlist.csv and BOM.csv (P4): 14 sheets, 156 parts, 0 netlist differences, ERC clean.
