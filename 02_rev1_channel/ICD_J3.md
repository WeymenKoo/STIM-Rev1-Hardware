# ICD: Rev 1 analog board J3 <-> FPGA (Red Pitaya)

JY063 · rewritten 2026-11-07 (Weymen, from the 2.1.0-dev schematic sheets 5, 10, 11, 12, 13) · **status: proposal,
not agreed** · to CPEN1/CPEN2 for sign-off. Replaces the 2026-10-28 analog pinout (DAC_CMD / read-back on J3), which
no longer exists: the DAC and ADC are on the board behind digital isolators.

## Connector
J3, 2 x 8 shrouded IDC header, 2.54 mm (same part as J5; LCSC number still to pick). Odd pins = signals, even pins =
GND_FPGA. **J3 is the isolation barrier:** everything on it is referenced to the FPGA ground, nothing on it touches the
board ground or the electrodes. Pin 1 carries the FPGA's 3.3 V to power the FPGA side of the isolators.

| Pin | Signal | Direction | Level | Board side (Rev 1) |
|---|---|---|---|---|
| 1 | +3V3_FPGA | FPGA -> board | 3.3 V, ~8 mA [ASSUME: two ISO7741 side-1 supplies, low toggle rate] | VCC1 of U43 / U44 only; never connected to the board's +3V3 |
| 3 | SPI_SCLK | FPGA -> board | 3.3 V CMOS | U43 (default low) -> ISO_SCLK -> U40 SCLK, U41 SCLK |
| 5 | SPI_MOSI | FPGA -> board | 3.3 V CMOS | U43 -> ISO_MOSI -> U40 SDI, U41 SDI |
| 7 | SPI_MISO | board -> FPGA | 3.3 V CMOS | U40 SDO and U41 SDO-0 (both tri-state when their CS is high) -> U44 reverse channel -> J3 |
| 9 | SPI_CS_DAC | FPGA -> board | 3.3 V, active low | U44 -> ISO_CS_DAC -> U40 SYNC |
| 11 | SPI_CS_ADC | FPGA -> board | 3.3 V, active low | U44 -> ISO_CS_ADC -> U41 CS/CONVST (ADC 1, I_RETURN) |
| 13 | ENABLE | FPGA -> board | 3.3 V, high = electrodes connected | U43 (default-LOW part) -> ISO_ENABLE -> Q20 / PhotoMOS [8]; R22 100k pull-down |
| 15 | SPI_CS_ADC2 | FPGA -> board | 3.3 V, active low | U44 (default HIGH) -> ISO_CS_ADC2 -> U42 CS/CONVST (ADC 2, V_ELEC) |
| 2 ... 16 | GND_FPGA | common | | FPGA ground = isolator side-1 ground. Not board GND |

Default states with J3 unplugged or the FPGA unpowered [DS ISO7741 / ISO7741F]: CS_DAC, CS_ADC, CS_ADC2 HIGH (all three
converters deselected), ENABLE, SCLK, MOSI LOW (PhotoMOS open). A spare board -> FPGA channel
(FAULT_N, active low, default low = asserted when the board is off) exists on U43 but has no J3 pin yet (TP38).

## Devices on the bus (one SPI bus, three chip selects)

| Device | Mode | Frame | Max SCLK | Notes |
|---|---|---|---|---|
| U40 AD5761R DAC (CS_DAC = SYNC) | CPOL 0 / CPHA 1 style: data clocked in on SCLK falling edge, latched on SYNC rising | 24 bit: 4 don't care, 4 register address, 16 data | 50 MHz [DS] | write control register first: range 001 = +/-5 V (or 100 = +/-3 V), CLR select, overrange off; then input register 0x8000 = 0 V. LDAC is tied low: output updates when SYNC rises. Read-back available (SDO) |
| U41 ADS8689 ADC 1 (CS_ADC) and U42 ADS8689 ADC 2 (CS_ADC2) | CS low = device holds SDO; conversion on CS falling edge; 32-bit frame, result in the top 16 bits | 32 bit | 66 MHz class [DS], 100 kSPS | after reset write RANGE_SEL_REG = 0b1011 (0 to 1.25 x VREF = 0-5.12 V) to each; identical driver, two chip selects, never both low |

Isolator propagation delay 11 ns typ [DS]; keep SCLK <= 10 MHz for DR1 (round trip through two isolators plus
converter setup is then uncritical).

## Read-back channels (two ADCs)

| ADC | CS | Signal | Scale |
|---|---|---|---|
| U41 | SPI_CS_ADC (pin 11) | I_RETURN_ADC | VMID + 0.201 V/mA (0.66-2.66 V at -/+5 mA) |
| U42 | SPI_CS_ADC2 (pin 15) | V_ELEC_ADC | VMID + V_elec / 101 (0.57-2.75 V at +/-110 V) |

ADC range 0-5.12 V, 78 uV/LSB = 0.39 uA/LSB on I_RETURN [H]. VMID (1.658 V nominal) is a DC constant: measure it once
per board on TP29 and store it. Software: I_mA = (code_I x 78.1 uV - VMID) / 0.201 V/mA; V_elec = (code_V x 78.1 uV - VMID) x 101.
Both conversions can be started back to back (< 10 us apart). Calibrate both once against a DMM (R4 in the acceptance table).

## Command scaling
DAC_CMD = DAC output, +/-5 V at range 001. On [6] with RG3 DNP (G = 1) that is 1 mA/V -> +/-5 mA. **Open decision
(Weymen):** RG3 DNP and +/-5 V range, or RG3 fitted (G = 5.02, the Red Pitaya +/-1 V configuration) and DAC range
+/-3 V (001 -> 100) with |code| limited in software to +/-1 V. Clip |i| <= 5 mA in software either way; the board
ceiling is ~9 mA (U3 rails) at G = 5, limiter 6.4-8.8 mA behind it.

## Software contract
1. ENABLE high only while a waveform runs; DAC at mid-scale (0 V) before ENABLE rises and when it falls; ENABLE low on
   any FPGA reset. Hold the DAC at 0 for 3 ms after ENABLE (D-08).
2. One SPI bus, two chip selects, never both low. MISO is shared; both devices tri-state it when deselected.
3. Read-back: convert both ADCs at >= 1 kHz; VMID from the stored TP29 value.
4. Two boards (source + sink) need two J3 cables; their FPGA grounds are common at the Red Pitaya, their board grounds
   are common through the return electrode (D-C). The isolators carry the difference.

## Bypass (bench only)
JP7 closed + ribbon moved from J3 to J5 on the board side: the FPGA drives the converters directly, 3.3 V logic on both
sides, and GND_FPGA = board GND through the cable (no isolation). J5 pin 1 is not connected (the board makes its own
3.3 V). Never plug J3 and J5 at the same time with JP7 open.

## Questions for CPEN
1. Can the Red Pitaya E1/E2 headers supply the 3.3 V on pin 1 (~8 mA) and 8 GPIO / SPI lines? If the SPI is bit-banged,
   what rate?
2. Three chip selects (DAC, ADC 1, ADC 2) on one bus: confirm the firmware can hold two of them high while the third
   is framed.
3. Cable: ribbon IDC 2 x 8 from J3 to the Red Pitaya via an adapter: who makes the adapter?

## Change control
Changing a pin, a range or a scale here changes sheets 5, 10, 11, 12 or RG3 / R51 / R52. File the change in
`DECISIONS.md` and the KiCad `CHANGELOG.md`.
