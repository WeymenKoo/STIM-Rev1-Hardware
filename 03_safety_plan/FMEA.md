# Safety plan: FMEA table (skeleton, to be filled by EE2/EE3 with Weymen)

Scope: bench prototype, dummy loads, no human subjects in this project. The table is the planning artefact the
client and Prof. Yan asked for; it becomes the Rev 2 requirement list. No circuits are designed here.
Architecture reference: `01_system-architecture-and-fault-protection.pptx` slides 1–~15 (A1–A5). The behavioural
simulations of each fault exist in `_archive_2026-10/1-safety-model/12-fault-injection/` (IDs T12.x) — cite them,
do not extend them until Rev 1 is on the bench.

Severity S 1–5 (5 = > 10 mA or DC into a participant), Occurrence O 1–5, Detection D 1–5 (5 = undetectable), RPN = S·O·D.

| ID | Failure mode | Effect at electrode | Current cause(s) | Rev 1 protection (bench) | Rev 2 mitigation (planned) | Detection | S | O | D | RPN | Archive sim | Owner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 | DAC command runaway / stuck full scale | sustained 5 mA → DC exposure | FPGA fault, link fault | G = 1: input clamp 6.2 V zener (~7 mA). G = 5 (Rev 1 default, RG3 fitted): clamp inert, U3 ±9 V rails (~9 mA) + DN2540 limiter (6.4–8.8 mA, once fitted) | watchdog → DAC clear; OC trip | | | | | | T12.1, T12.2 | |
| F02 | Input clamp zener open | command > 5 mA possible | component | buffer supply ±9 V limits (~9 mA); at G = 5 this is already the primary bound | second clamp / buffer rails | | | | | | T9.2 | |
| F03 | Output stage shorted to a rail (Q1/Q2 fail) | up to rail / R_load | component, thermal | fuse, limiter, TVS | rail-shunt OC trip + disconnect | | | | | | T12.3 | |
| F04 | One HV rail lost / asymmetric ramp | pump drives ~10 mA (model est.) | supply fault, power-up order | fuses; limiter | per-rail UV/OV + symmetry window → disconnect | | | | | | step 5, T12.x | |
| F05 | Return electrode detached | electrode voltage rises to compliance | mechanical | TVS, limiter | compliance warning, V_elec read-back | | | | | | T12.5 | |
| F06 | Stim electrode lifting / high impedance | current not delivered (experiment invalid) | gel, skin | read-back V_ELEC_ADC | compliance flag to operator | | | | | | T12.4 | |
| F07 | PhotoMOS welded / stuck on | no disconnect path | component | second switch in series (U4+U5) | independent relay | | | | | | T12.7 | |
| F08 | ENABLE lost / FPGA reset mid-stim | abrupt stop (charge imbalance) | firmware | PhotoMOS opens | controlled ramp-down | | | | | | T12.6 | |
| F09 | Channel sum ≠ 0 (shared return) | net DC through the return | waveform error | none | mismatch trip (per-channel vs system, D-19) | | | | | | shared-return | |
| F10 | Rail ripple / converter noise into load | µA ripple at f_sw | flyback design | none | f_sw placement, post-regulation | | | | | | step 6 | |
| F11 | Bench: ±100 V exposure to the operator | shock | open board | covered loads, bleeders, labelled TPs | enclosure, interlock | | | | | | — | |
| F12 | Thermal: Q1/Q2 at 10 mA fault | part failure → F03 | fault current | copper pour sized (archive) | OC trip time limit | | | | | | 3-compliance | |

## Decisions to make with the client (not before Rev 1 bench data)
1. Where safety lives: on the analog board (Rev 2) or a separate safety daughter board inline in the stimulating line (JP3 was removed in Rev 1 2.1.0-dev; JP5 across U4 is the break point).
2. Trip philosophy: per-channel vs system-level mismatch (D-19 in the archive).
3. Which standard to design toward for leakage/isolation (IEC 60601-1 MOPP as a reference, no certification).

## parking-lot.md
Rev 2 questions that come up during Rev 1 go in `parking-lot.md`, one line each, dated. Not here.
