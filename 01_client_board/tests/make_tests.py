# Writes the A1-A7 acceptance schematics from the archived step schematics. Run from 01_client_board/: python3 tests/make_tests.py
import re, pathlib
A="../_archive_2026-10/2-pump-characterization"
BASE={"s1":f"{A}/1-bootstrap/bootstrap-floating-supply.asc","s3":f"{A}/3-dac-step-response/dac-step-response.asc",
      "s5":f"{A}/5-power-sequencing/supply-sequencing-faults.asc","s8":f"{A}/8-output-impedance/output-impedance.asc"}
def load(p): return open(p,encoding="utf-8",errors="replace").read().splitlines()
def build(base, folder, fname, title, subtitle, src_value, src_value2, directives, notes):
    out=[]
    for L in load(BASE[base]):
        if L.startswith("SYMBOL "): L=re.sub(r"SYMBOL \.\.\\(\w+)", r"SYMBOL ..\\..\\model\\\1", L)
        elif L.startswith("TEXT"):
            m=re.match(r"TEXT (-?\d+) (-?\d+) (\w+) (\d+) (.*)",L); x,y,body=int(m.group(1)),int(m.group(2)),m.group(5)
            if y>=896: continue
            if body.startswith("S01  STIM stage"): L=f"TEXT {x} {y} Left 3 {title}"
            elif body.startswith("I_load = V(INPUT)"): L=f"TEXT {x} {y} Left 2 {subtitle}"
        out.append(L)
    txt="\n".join(out)
    pat=re.compile(r"(SYMATTR InstName Vwg\n)SYMATTR Value [^\n]*(\nSYMATTR Value2 [^\n]*)?")
    rep=lambda m: m.group(1)+"SYMATTR Value "+src_value+(("\nSYMATTR Value2 "+src_value2) if src_value2 else "")
    txt,n=pat.subn(rep,txt); assert n==1,fname
    txt+="\n"+"\n".join(f"TEXT -64 {896+40*k} Left 2 !{d}" for k,d in enumerate(directives))
    txt+="\n"+"\n".join(f"TEXT 720 {896+28*k} Left 1 {n}" for k,n in enumerate(notes))
    d=pathlib.Path("tests")/folder; d.mkdir(parents=True,exist_ok=True)
    (d/fname).write_text(txt+"\n",encoding="utf-8"); print("wrote",d/fname)
INC=".include ../../model/client-board-models.lib"; RAIL=".step param Vrail list 30 100"
build("s1","A1-bias-bootstrap","A1-bias-bootstrap.asc",
 "A1  Bias point and bootstrap window, client board model, rails stepped 30 V and 100 V",
 "2 mA and 5 mA 300 Hz into 1 kOhm. Bench twin: DMM on VP, VN, OUT vs GND; rail current on the supply readout. Numbers land in the .log (View > SPICE Error Log).",
 "SINE(0 {Ipk*1k} {fsig} {Tset})",None,
 [INC,".param RL=1k Ipk=5m fsig=300 Tset=1m",RAIL,".step param Ipk list 2m 5m",".tran 0 8m 0 1u",
  ".meas tran Ipk_load MAX I(RLOAD) FROM 4m TO 8m",".meas tran Ierr_pct PARAM (Ipk_load-Ipk)/Ipk*100",
  ".meas tran VP_minus_OUT AVG V(VP)-V(OUT) FROM 4m TO 8m",
  ".meas tran VN_minus_OUT AVG V(VN)-V(OUT) FROM 4m TO 8m",".meas tran window_VP_VN AVG V(VP)-V(VN) FROM 4m TO 8m",
  ".meas tran window_min MIN V(VP)-V(VN) FROM 4m TO 8m",
  ".meas tran REF_VN_min MIN V(REF)-V(VN) FROM 4m TO 8m",".meas tran VP_OUT_min MIN V(VP)-V(OUT) FROM 4m TO 8m",
  ".meas tran Irail_pos_mA AVG -1000*I(Vpos) FROM 4m TO 8m",".meas tran Irail_neg_mA AVG 1000*I(Vneg) FROM 4m TO 8m",
  ".meas tran Vout_max MAX V(OUT) FROM 4m TO 8m"],
 ["Acceptance A1 (archive step 1). Four runs, log step order: 1 = 30 V/2 mA, 2 = 100 V/2 mA, 3 = 30 V/5 mA, 4 = 100 V/5 mA (Vrail is the inner loop).",
  "Plot 1: I(RLOAD) and V(INPUT)/1k.  Plot 2: V(OUT), V(LOAD), V(VP), V(VN), V(VCCP), V(VCCN).  Plot 3: V(VP)-V(VN).",
  "Question for the 30 V run: does the floating window still form (expect ~19.5 V at 100 V), and does OUT clear the rails with 5 V swing?",
  "U1 low-side headroom = (OUT-VN) - I*R7: ~0.4 V at 2 mA, negative at 5 mA on +/-30 V. REF_VN_min is the number to compare with the bench.",
  "Bench: +/-30 V from two 30 V supplies in series, 50 mA current limit, mid-point to GND; RL = 1.00 k 1 %; Vwg = function generator 50 ohm."])
build("s1","A2-accuracy-vs-command","A2-accuracy-vs-command.asc",
 "A2  DC accuracy vs command, client board model, rails stepped 30 V and 100 V",
 "DC command Icmd into 1 kOhm; err_pct = (Iload - Icmd)/Icmd. Bench twin: DMM across the 1 kOhm 0.1 % load at each command.",
 "{Icmd*1k}",None,
 [INC,".param RL=1k Icmd=1m",RAIL,".step param Icmd list 0.5m 1m 2m 5m -2m -5m",".tran 0 2m 0 1u",
  ".meas tran Iload AVG I(RLOAD) FROM 1.2m TO 2m",".meas tran err_pct PARAM (Iload-Icmd)/Icmd*100",".meas tran Vload AVG V(LOAD) FROM 1.2m TO 2m"],
 ["Acceptance A2 (archive step 8 accuracy, DC version). 12 runs: 6 commands x 2 rails. Pass: |err_pct| <= 1 at every point except +/-5 mA on 30 V (A1: clips at +4.0 / -3.4 mA).",
  "The log lists Iload and err_pct per run. Model-dependent: the generic op-amp models carry no offset; the bench will show the uA-class offset.",
  "Bench: same six commands from the generator DC offset (0.5, 1, 2, 5, -2, -5 V). 6.5-digit DMM on V(LOAD)."])
build("s3","A3-step-settling","A3-step-settling.asc",
 "A3  DAC step response and settling, client board model, rails stepped 30 V and 100 V",
 "0 -> +Istep at 100 us, +Istep -> -Istep at 600 us, 1 us edges, 1 kOhm. Istep stepped 2 mA (30 V bench twin) and 5 mA. Bench: generator square 0/2 V, 1 us edge, scope across RLOAD.",
 "PWL(0 0 100u 0 101u {Istep*1k} 600u {Istep*1k} 601u {-Istep*1k} 1.1m {-Istep*1k})",None,
 [INC,".param RL=1k Istep=2m",RAIL,".step param Istep list 2m 5m",".tran 0 1.2m 0 20n",
  ".meas tran Ifin AVG I(RLOAD) FROM 300u TO 500u",".meas tran Ipk MAX I(RLOAD) FROM 100u TO 300u",".meas tran OS_pct PARAM (Ipk-Ifin)/Ifin*100",
  ".meas tran t_enter_1pct FIND time WHEN I(RLOAD)=0.99*Istep RISE=1 TD=100u",".meas tran t_last_above FIND time WHEN I(RLOAD)=1.01*Istep FALL=1 TD=100u",
  ".meas tran tset_us_approx PARAM (t_last_above-101u)*1e6"],
 ["Acceptance A3 (archive step 3). Four runs, log order: 30V/2m, 100V/2m, 30V/5m, 100V/5m. Overshoot is stated vs final value, not vs the full swing. 30V/5m clips (A1); ignore its settling numbers.",
  "tset_us_approx = last exit from the +1 % band on the rising step; if the current never exceeds 1.01*Istep that measure fails (harmless) and t_enter_1pct is the settling time.",
  "Confirm on the plot (zoom 98-115 us) that nothing re-enters the band later. Plot: I(RLOAD) and V(INPUT)/1k.",
  "Bench edge rate matters: do not infer damping from a 1 us edge the DAC will never produce."])
build("s1","A4-frequency-response","A4-frequency-response.asc",
 "A4  Small-signal frequency response I(load)/V(command), client board model, rails stepped 30 V and 100 V",
 "AC 1 V at the generator into 1 kOhm; 0 dB = 1 mA/V. Bench twin: 2 mA pk sine at 1, 10, 100, 300, 1k, 10k Hz, amplitude read on the scope (small-signal, so amplitude is free; 2 mA keeps 30 V out of clipping).",
 "SINE(0 0 300)","AC 1",
 [INC,".param RL=1k",RAIL,".ac dec 100 1 10Meg",
  ".meas ac m_1Hz FIND mag(1000*I(RLOAD)) AT 1",".meas ac m_10Hz FIND mag(1000*I(RLOAD)) AT 10",".meas ac m_100Hz FIND mag(1000*I(RLOAD)) AT 100",
  ".meas ac m_300Hz FIND mag(1000*I(RLOAD)) AT 300",".meas ac m_1kHz FIND mag(1000*I(RLOAD)) AT 1k",".meas ac m_10kHz FIND mag(1000*I(RLOAD)) AT 10k",
  ".meas ac dB_10k_vs_1 PARAM 20*log10(m_10kHz/m_1Hz)",".meas ac ph_300Hz FIND ph(1000*I(RLOAD)) AT 300",
  ".meas ac pk MAX mag(1000*I(RLOAD))"],
 ["Acceptance A4 (archive step 4). Two runs. Pass: within +/-0.5 dB of the 1 Hz value up to 10 kHz.",
  "Plot: 1000*I(RLOAD) in dB with phase; right-click the axis -> Linear for the mA/V view. The 0.3-1 MHz peak is the loop; mark it, it sets the flyback f_sw keep-out.",
  "pk reports the loop peak magnitude and its frequency. AC analysis linearises at the DC operating point (command = 0)."])
build("s8","A5a-output-impedance-ac","A5a-output-impedance-ac.asc",
 "A5a  Output impedance (AC injection), client board model, rails stepped 30 V and 100 V",
 "1 A AC test current into LOAD, command at zero, dummy head removed (RL = 1 G). V(LOAD) = Z_out in ohms. Generator source resistance stepped 50 ohm / ideal.",
 "SINE(0 0 300)",None,
 [INC,".param RL=1G RS=50",RAIL,".step param RS list 50 1u",".ac dec 20 1 1Meg",
  ".meas ac Z_1Hz FIND mag(V(LOAD)) AT 1",".meas ac Z_100Hz FIND mag(V(LOAD)) AT 100",".meas ac Z_1kHz FIND mag(V(LOAD)) AT 1k",".meas ac Z_10kHz FIND mag(V(LOAD)) AT 10k",
  ".meas ac C_out_pF_at_10k PARAM 1e12/(2*pi*10k*Z_10kHz)"],
 ["Acceptance A5a (archive step 8). Four runs: RS 50 / 1u x Vrail 30 / 100. Archive: 8.2 MOhm with the 50 ohm generator, 251 MOhm ideal, ~36 pF above ~100 Hz.",
  "Plot: V(LOAD) in dB re 1 ohm. Not directly measurable on the bench at these values; A5b is the bench twin."])
build("s1","A5b-output-impedance-dc","A5b-output-impedance-dc.asc",
 "A5b  Output impedance by load change (bench twin), client board model, rails stepped 30 V and 100 V",
 "2 mA DC command; load 1.0 k then 2.2 k. Z_out = dV(LOAD) / dI(RLOAD) between the two runs, by hand from the log. Bench: same two loads, DMM.",
 "{Icmd*1k}",None,
 [INC,".param Icmd=2m RL=1k",RAIL,".step param RL list 1k 2.2k",".tran 0 2m 0 1u",
  ".meas tran Iload AVG I(RLOAD) FROM 1.2m TO 2m",".meas tran Vload AVG V(LOAD) FROM 1.2m TO 2m"],
 ["Acceptance A5b. Four runs. Z_out = (Vload_2k2 - Vload_1k) / (Iload_1k - Iload_2k2). The sim gives a number the bench DMM cannot resolve; the bench test is 'no measurable drop'.",
  "Bench pass: current change < 0.1 % between loads (DMM floor), i.e. Z_out > 1.2 MOhm."])
build("s5","A7-rail-loss","A7-rail-loss.asc",
 "A7  Supply sequencing and single-rail loss, client board model, rails stepped 30 V and 100 V",
 "2 mA DC command into 1 kOhm (bench twin: switch one supply off mid-run, scope the load current). Three sequences, both rail values.",
 "{Icmd*1k}",None,
 [INC,".param RL=1k Icmd=2m SEQ=1",RAIL,".step param SEQ list 1 2 3",
  ".param VP0={if(SEQ==2,Vrail,0)} VPE={if(SEQ==2,0,Vrail)} VN0={if(SEQ==2,-Vrail,0)} TN={if(SEQ==1,5m,0.5m)}",
  ".tran 0 60m 0 1u",".meas tran I_max_mA MAX 1000*I(RLOAD)",".meas tran I_min_mA MIN 1000*I(RLOAD)",
  ".meas tran I_end_mA AVG 1000*I(RLOAD) FROM 40m TO 60m",".meas tran Vload_max MAX V(LOAD)",".meas tran Vload_min MIN V(LOAD)"],
 ["Acceptance A7 (archive step 5, with a 2 mA command instead of zero). Six runs.",
  "SEQ 1 = +rail at 0.5-1.5 ms, -rail 4.5 ms later.  SEQ 2 = both up, +rail fails at 10-11 ms.  SEQ 3 = both rails together.",
  "Plot: I(RLOAD), V(VCCP), V(VCCN). Archive at 100 V, command 0: -9.7 mA continuous after +rail loss (macromodel estimate outside supply range: label it so).",
  "Bench: only SEQ 2 and 3 are safe to reproduce by hand; use the supply output-enable buttons, 50 mA limit."])
