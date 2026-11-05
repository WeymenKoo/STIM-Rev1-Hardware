# JY063 safety loop: plan (Rev 2 target)

Status: DRAFT 0.1, 2026-11-04, Weymen. Companion diagram: `kicad/safety-loop.kicad_sch` (open in KiCad; it is a
block schematic on one A3 sheet, no netlist) and `kicad/safety-loop.pdf`. Regenerate with
`python3 kicad/gen_safety_loop.py kicad/safety-loop.kicad_sch`. Scope: bench prototype on dummy loads; this plan
exists because the client lab will put the design on people after hand-over. Not a safety sign-off.

Tags: [DS] datasheet, [H] hand calc, [N] ngspice (archive `4-rev1-design/DECISIONS.md`), [DS5] Digitimer DS5
operator's manual, [ASSUME] to be decided.

## 1. What the client asked for, and what the DS5 actually does

The client wants a concrete safety logic, and pointed to a commercial EVS unit "where the participant controls an
engage switch, like the Digitimer DS5". Checked against the DS5 manual and data sheet [DS5]:

| DS5 feature | What it is | Our equivalent on the sheet |
|---|---|---|
| Output On/Off-Reset | operator momentary toggle on the front panel: up = enable, down = disable **and** reset after a limit trip | ARM (key switch) + RESET (push-button); both hardware, on the enclosure |
| Autozero gate | output cannot be enabled until the input offset is zeroed and while a voltage is present at the input | FPGA holds DAC = 0 for ~3 ms after ENABLE (D-08); RESET accepted only with ENREQ = 0 |
| Four output limits | AvL 50 µA average idle current, AvH 10 mA average pulse current, PD 1 s pulse duration, PE 50 mJ pulse energy; exceeding an enabled limit disables the output, amber LED, beep | DC/charge trip (AvL), OC trip (AvH), software max-DC-duration (PD); PE not needed at ≤ 10 mA / 100 V |
| Isolation | Class I, Type BF applied part; monitor BNCs "ground referenced and isolated from the patient" | isolation barrier; monitor BNC through an isolation amplifier on the PC-ground side |
| Compliance flag | "out of compliance" icon when the commanded current is not delivered | OV/compliance trip + V_ELEC_ADC read-back |
| Participant switch | **none.** The DS5 has no subject-operated switch or interlock connector. | ENGAGE (added by us, see §4) |

So the DS5 is the precedent for operator arming, automatic disable on a limit, and a manual reset, not for
participant control. The participant switch is our addition; it needs the client to say what they actually want (§4).

## 2. The loop in one paragraph

Current can only reach the electrodes when three things are true at once: the passive limiter and clamp bound it
(no supply, no logic needed), the two PhotoMOS switches S1 and S2 are closed, and the switches are only closed while
ENABLE is high. ENABLE is a hardwired AND of six terms: the FPGA request (ENREQ), no latched fault (FAULT_N), rails
inside their window (RAILOK), a live FPGA heartbeat (WD_OK), the operator key (ARM) and the participant switch
(ENGAGE). Four analog detectors (over-current, compliance/over-voltage, DC/charge, mismatch) set a latch that drops
FAULT_N; only a human pressing RESET at the box clears it, and only when the FPGA has released ENREQ and the rails are
good. Losing any other term de-energises without latching. The FPGA sees FAULT_N, RAILOK and ENABLE as read-only
status; it never sits in the enable path.

States: OFF (no ARM) → ARMED (ARM, rails good, no fault; yellow LED) → ENABLED (ENREQ and ENGAGE both present; green)
→ FAULT (any trip; red, latched) → ARMED after RESET. ENGAGE released: ENABLED → ARMED, no latch.

## 3. Layers, outer to inner

| Layer | Block on the sheet | What it bounds | Rev 1 board | Rev 2 |
|---|---|---|---|---|
| L0 passive | DAC clamp D3/D4 + buffer rails; DN2540 series limiter; TVS SMBJ100CA; rail fuses F1/F2 | command ceiling ~7-9 mA [N]; loop current 6.4-8.8 mA either polarity [N]; electrode voltage ≤ ~111 V | present (limiter DNP, fitted at bring-up) | keep; limiter pair selected on test (D-02) |
| L1 disconnect | S1 stim PhotoMOS, S2 return PhotoMOS, S3 parking Form-B | two independent breaks in the loop; output parked at 0.4 V when disabled [N] | S1, S2 present, S3 absent | add S3 (D-08); consider a relay as the second means if PhotoMOS leakage at 200 V matters |
| L2 detect | OC (rail shunts), OV (electrode divider), DC/charge (integrator on I_RET), mismatch (I_RET vs delayed I_CMD), rail supervision, watchdog | see trip table | read-back only (RSHR, V_ELEC_DIV to ADC) | all new; comparators TLV1704 (D-13) |
| L3 latch + enable | trip OR → SR latch (74LVC1G74, set-dominant, POR sets) → enable AND → LED driver | FAULT_N latched; ENABLE hardwired | ENABLE pin direct from FPGA to U4/U5 LEDs | new |
| L4 human | ARM key, ENGAGE hand switch, RESET button, LEDs, monitor BNCs | operator and participant authority | none | new, on the enclosure |
| L5 firmware | DAC clear on FAULT_N or ENABLE low, heartbeat, software limits (sum = 0, ≤ 5 mA, max DC duration), controlled ramp-down | second, independent bound; never the only one | partial (ICD_J3) | CPEN |
| L6 isolation | digital isolator for SPI/ENREQ/HEARTBEAT/status; isolated DC-DC; monitor BNC via iso amp | PC ground never touches the electrode loop | **none** (U32 COM = GND) | reinforced barrier, ≥ 1 MOPP as a reference (IEC 60601-1), no certification |

## 4. The participant ENGAGE switch: what to agree with the client

Proposed: a normally-open momentary hand switch, held by the participant, in series in the enable AND. Release =
stimulation stops within the PhotoMOS Toff (0.2 ms max [DS]) plus the DAC clear; not latched, so the experiment can
resume without an operator reset. This is a dead-man design.

Questions the client must answer before it is designed (none of these are ours to decide):
1. Dead-man (must hold to stimulate) or abort (press to stop, latched)? A dead-man switch stops on any slip of the
   hand; an abort button needs a deliberate press and should latch like a fault.
2. The lab's standing-balance protocols: can the participant hold a switch without changing posture or sway? If not,
   where does it go (foot pedal, thumb switch on a harness, operator-only)?
3. Does the participant switch gate the stimulus, or also the experiment clock on the PC? If the FPGA keeps streaming
   while ENGAGE is open, the waveform resumes mid-stream; charge balance of the cycle is lost (F08).
4. Must a release be logged with a timestamp for the protocol? If so, ENABLE status to the FPGA is enough.
5. Is the hand switch an applied part? If it touches the participant it sits on the floating side or is isolated.

## 5. Trip table (targets; every number to be confirmed on the Rev 1 bench)

| Trip | Signal | Threshold | Response | Latched | FMEA | Source |
|---|---|---|---|---|---|---|
| OC | rail shunts via 2× INA149, ×4, two 22 µs poles | ~5.7 mA (window 5.3-6.1 mA after errors) | open S1/S2, park, FAULT_N | yes | F01, F03 | D-03, D-06 [N] |
| OV / compliance | V_elec via 2×10 M + 200 k to VMID, 47 pF | 77-83 V (normal max 65 V, TVS 111 V) | same | yes | F05, F06 | D-09 [N] |
| DC / charge | integrator on I_RET (RSHR ×100) | avg idle current > 50 µA [DS5 AvL]; Q_max per event [ASSUME] | same | yes | F08, F09 | new, needs a number from the client's protocol |
| Mismatch | I_RET vs delayed I_CMD (3.92 k + 1 nF), two 47 µs poles | ±0.40 mA | same, ~25 µs for a detached return | yes | F05 | D-07 [N]; D-19 open for a shared return |
| Rail supervision | ±HV dividers, aux rails, POR | 90-110 V window, symmetry, 20 ms POR | RAILOK low: disable; also sets the latch via the OR (not a fault once rails return? decide) | no | F04 | D-10, D-15 [H] |
| Watchdog | HEARTBEAT edge from FPGA | > 10 ms without an edge [ASSUME] | WD_OK low: disable | no | F01 | new |
| ENREQ / ARM / ENGAGE | logic | released | disable | no | F08 | — |

Rail supervision is listed twice on the sheet (in the OR and in the AND). Decide one: if a rail glitch should need a
human reset, keep it in the OR; if the bench supplies are expected to brown out, keep it only in the AND.

## 6. Decisions still open (owner, when)

| # | Decision | Owner | By |
|---|---|---|---|
| S1 | Participant switch semantics (§4) | client, via EE2/EE3 | before the Nov 14 power-board review |
| S2 | Safety on the analog board or on a daughter board inline in the stim line (JP5 is the break point) | Weymen + Jeff | Rev 2 schematic start |
| S3 | Mismatch trip per channel vs system level with a shared return (D-19) | team | before the 4-channel design |
| S4 | DC/charge limits: 50 µA idle [DS5] is a reference; Q_max and max DC duration need the client's protocol | client | with S1 |
| S5 | Rail supervision latched or not | Weymen | Rev 2 |
| S6 | Isolation target and leakage test method (reference only, no certification) | EE2/EE3 research brief item 2 | DR1 slides |
| S7 | Second disconnect means: two PhotoMOS (as drawn) vs PhotoMOS + mechanical relay | EE2/EE3 research brief item 3 | DR1 slides |

## 7. How this feeds DR1

- FMEA.md: the "Rev 2 mitigation" column now maps onto named blocks on this sheet (F01 → watchdog + OC; F03 → OC;
  F04 → rail supervision; F05 → OV + mismatch; F07 → S1/S2 independent; F08 → ENGAGE not latched + DAC clear;
  F09 → DC/charge + mismatch).
- Safety architecture slides (EE2/EE3, 5-8 slides): this sheet is slide 1; the DS5 comparison (§1) is slide 2;
  the trip table (§5) slide 3; open decisions (§6) the last slide.
- Nothing here changes the Rev 1 order (Nov 10). Rev 1 gives the bench numbers that replace every [N] above.

## Sources

- Digitimer DS5 operator's manual (Leiden copy):
  https://www.staff.universiteitleiden.nl/binaries/content/assets/sociale-wetenschappen/faculteitsbureau/solo/research-support-website/equipment/manual-digitimer-ds5_23122019.pdf
- Digitimer DS5 data sheet: https://www.digitimer.com/wp-content/uploads/2019/09/ds5.pdf
- Archive decision log: `SPICE_SIM/_archive_2026-10/4-rev1-design/DECISIONS.md` (D-02 … D-19)
- `SPICE_SIM/03_safety_plan/FMEA.md`, `research-brief.md`, `01_system-architecture-and-fault-protection.pptx` (A4, A5)
