#!/usr/bin/env python3
"""JY063 client STIM board — bench session rig.  Run from this folder (01_client_board/bench/).

  python3 bench_rig.py check                      # list instruments, *IDN?
  python3 bench_rig.py preflight                  # no board: scope decode check on probe-comp, generator flatness + edge
  python3 bench_rig.py a1   [--amp 2 5] [--onset] [--rails]   # bias / bootstrap window (+ optional onset sweep, rail sweep)
  python3 bench_rig.py a2                         # DC accuracy (you type the Fluke 45 readings)
  python3 bench_rig.py a5b                        # output impedance by load change (Fluke 45 in series)
  python3 bench_rig.py a4                         # frequency response, fully scripted with the DG1022
  python3 bench_rig.py a3                         # step response, single-shot
  python3 bench_rig.py a7   [--korad /dev/tty.usbserial-xxx]  # rail loss (manual switch or scripted Korad)

Common options:  --rl 1000.0  (measured RL, Ω)   --rl2 2200.0   --gen manual  (FG085 / front panel)
                 --scope <VISA resource>  --gen-res <VISA resource>  --dmm-port /dev/tty...  (Fluke 45 RS-232)
                 --tag 30V   (goes into file names: A1_30V_2mA_bench.csv)

Outputs:  ../tests/<ID>/bench/<NAME>.csv (+ .png overlay with the sim, sim dashed / bench solid)
          session_log.csv (one row per quantity: bench value, expected [L], tolerance, pass)
Every number printed here is [B]; the expected column is [L] from the 2026-10-27 model runs.
"""
import argparse, csv, os, sys, time, datetime
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); TESTS = os.path.join(HERE, "..", "tests")
sys.path.insert(0, HERE); sys.path.insert(0, TESTS)
import instruments as I
try: import ltraw
except Exception: ltraw = None

# ------------------------------------------------------------------ expected values [L], ±30 V, 2026-10-27 model
EXP = {
  "A1": dict(VP_idle=2.5, VN_idle=-2.4, window=4.97, I_pk=2.0, OUT_pk=4.0, VP_pk=6.0, VN_pk=1.1, REFVN_min=0.92, VPREF_min=1.05,
             Irail=5.2, I_plateau_pos=4.01, I_plateau_neg=-3.38, Irail5=6.0, window5=4.84),
  "A2": {0.5: 0.5, 1: 1.0, 2: 2.0, -2: -2.0, 5: 3.837, -5: -3.188},
  "A5b": dict(dI_pct=0.015, Zout_M=8.1),
  "A4": {1: 0.0, 10: 0.0, 100: 0.0, 300: 0.0, 1000: 0.0, 10000: 0.002},
  "A3": dict(OS_pct=18.4, t_settle_us=2.75, f_ring_MHz=0.7, I_final=2.0),
  "A7": dict(I_cont=-5.9, I_peak=-6.3, I_restored=2.0, I_seq3_peak=2.02),
}
PROBE = {  # where to clip, from Client_Prototype_HowlandPump.pdf (STIM.SchDoc 2026-10-16)
  "VCC+": "F1 (board side) or J3 pin 1", "VCC-": "F2 (board side) or J3 pin 3", "GND": "J3 pin 2 / J2 / J5 GND",
  # bench 2026-11-06: on the board C2/C3 sit on fused VCC+/VCC− (STIM.SchDoc), NOT on V+/V−. Probe the IC pins.
  "VP (V+)": "U2 pin 7 (= U1 pin 7 = Q2 tab)", "VN (V-)": "U2 pin 4 (= U1 pin 4 = Q1 pin 3)",
  "OUT": "D1/D2 junction = top of R7 (U2 pin 6)", "LOAD": "J1 = bottom of R7 (U1 pin 3)", "REF": "U1 pin 6 (also U2 pins 1, 5)",
  "INPUT": "J4 BNC centre (D3/D4 junction, U2 pin 3)", "Q2 base": "R2/R3 junction", "Q1 base": "R4/R5 junction",
}

LOG = os.path.join(HERE, "session_log.csv")
def log(test, qty, bench, expected="", tol="", ok=""):
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f); new and w.writerow(["time", "test", "quantity", "bench [B]", "expected [L]", "tol", "pass"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), test, qty, bench, expected, tol, ok])
    flag = "" if ok == "" else ("  PASS" if ok else "  FAIL")
    print(f"  {qty:48s} {str(bench):>14s}   exp {str(expected):>10s}  {tol}{flag}")

def within(x, exp, tol):  # tol: ('pct', 1) | ('abs', 2) | ('pts', 10)
    if np.isnan(x): return ""
    k, v = tol
    return abs(x - exp) <= (abs(exp) * v / 100 if k == "pct" else v)

def outdir(tid):
    d = os.path.join(TESTS, {"A1": "A1-bias-bootstrap", "A2": "A2-accuracy-vs-command", "A3": "A3-step-settling", "A4": "A4-frequency-response",
                             "A5b": "A5b-output-impedance-dc", "A7": "A7-rail-loss", "PRE": "."}[tid], "bench")
    os.makedirs(d, exist_ok=True); return d

def save_csv(path, t, cols):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["t_s"] + list(cols)); w.writerows(zip(t, *cols.values()))
    print("  wrote", os.path.relpath(path, HERE))

def nice(x):  # nearest 1-2-5 at or above x
    e = 10 ** np.floor(np.log10(x)); m = x / e
    return e * (1 if m <= 1 else 2 if m <= 2 else 5 if m <= 5 else 10)

def sine_fit(t, v, f):
    """Least-squares fit v = A sin(2πft) + B cos(2πft) + C → (amplitude, phase_deg, offset)."""
    w = 2 * np.pi * f; M = np.column_stack([np.sin(w * t), np.cos(w * t), np.ones_like(t)])
    a, b, c = np.linalg.lstsq(M, v, rcond=None)[0]
    return float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a))), float(c)

def banner(s): print("\n" + "=" * 100 + f"\n {s}\n" + "=" * 100)
def ask(msg): input(f"  >>> {msg}   [Enter] ")
def probes(*names):
    print("  probe points:"); [print(f"    {n:9s} {PROBE[n]}") for n in names]

# ------------------------------------------------------------------------------------------------- setup
def connect(a, need_gen=True):
    found = I.find_instruments(verbose=False)
    sc = a.scope or found.get("scope")
    if not sc: sys.exit("no DHO8xx found. `python3 bench_rig.py check`, or pass --scope")
    scope = I.DHO804(sc); print("  scope:", scope.idn)
    gen = None
    if need_gen:
        if a.gen == "manual": gen = I.ManualGen()
        else:
            g = a.gen_res or found.get("gen")
            gen = I.DG1022(g) if g else I.ManualGen()
        print("  gen:  ", gen.describe())
    dmm = I.Fluke45(a.dmm_port) if a.dmm_port else I.ManualDMM("Fluke 45")
    print("  dmm:  ", dmm.describe())
    return scope, gen, dmm

def scope_a1_layout(scope, i_scale):
    """CH1 LOAD, CH2 OUT (later REF), CH3 VP, CH4 VN. i_scale = V/div for CH1 (2 Vpk → 1 V/div, 5 Vpk → 2 V/div)."""
    scope.channel(1, i_scale); scope.channel(2, 2); scope.channel(3, 2); scope.channel(4, 2)
    scope.trigger_edge(1, 0.0, "POS", "AUTO")

def capture(scope, chans, settle=1.0, mode="AVER", averages=8, tb=None):
    if tb: scope.timebase(tb)
    scope.acquire(mode, averages); scope.settle(settle)
    return scope.waveforms(chans)

# ------------------------------------------------------------------------------------------------- CHECK
def cmd_check(a):
    banner("VISA resources"); I.find_instruments(verbose=True)

# ------------------------------------------------------------------------------------------------- PREFLIGHT
def cmd_preflight(a):
    banner("PREFLIGHT — no board. 1) CH1 probe on the scope's probe-comp terminal. 2) generator BNC → CH1 (BNC–BNC or probe)")
    scope, gen, _ = connect(a); d = outdir("PRE")
    ask("CH1 probe on probe-comp (3 Vpp 1 kHz square), probe set 10×")
    scope.channel(1, 1.0); scope.timebase(500e-6); scope.trigger_edge(1, 1.5, "POS", "AUTO")
    t, w = capture(scope, [1], 1.0, "NORM")
    vpp_dec = w[1].max() - w[1].min(); vpp_meas = scope.meas("VPP", 1)
    print(f"  decoded Vpp {vpp_dec:.3f} V   scope VPP {vpp_meas:.3f} V   points {len(t)}   dt {np.median(np.diff(t))*1e6:.2f} µs")
    if not (0.9 < vpp_dec / vpp_meas < 1.1): print("  !! waveform decode disagrees with the scope's VPP — fix instruments.DHO804.waveform before the session")
    else: print("  waveform decode OK")
    save_csv(os.path.join(d, "preflight_probecomp.csv"), t, {"CH1": w[1]})

    ask("generator output → CH1 directly (no board). Press Enter to sweep")
    gen.on(); rows = []
    for f in [1, 10, 100, 300, 1e3, 10e3, 100e3]:
        gen.sine(f, 2.0); tb = nice(4 / f / 10); scope.timebase(tb); scope.channel(1, 1.0); scope.trigger_edge(1, 0.0, "POS", "AUTO")
        t, w = capture(scope, [1], max(1.0, 12 * tb), "NORM" if f < 100 else "AVER")
        amp, ph, off = sine_fit(t, w[1], f); rows.append((f, amp, scope.meas("VPP", 1))); print(f"  {f:>8g} Hz  fit {amp:.4f} Vpk  scope Vpp {rows[-1][2]:.4f}")
    ref = rows[1][1]
    with open(os.path.join(d, "preflight_gen_flatness.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["f_Hz", "Vpk_fit", "Vpp_scope", "dB_vs_10Hz"]); [cw.writerow([f, amp, vpp, 20*np.log10(amp/ref)]) for f, amp, vpp in rows]
    gen.square(500, 0, 2); scope.timebase(200e-9); scope.channel(1, 0.5, -1.0); scope.trigger_edge(1, 1.0, "POS", "SING")
    gen.on()
    if scope.single(10): t, w = scope.waveforms([1]); print(f"  generator edge 10–90 %: {edge_time(t, w[1])*1e9:.0f} ns  ← write on the A3 sheet")
    gen.zero(); gen.off(); print("  preflight done. Files in tests/bench/.")

def edge_time(t, v):
    lo, hi = np.percentile(v, 2), np.percentile(v, 98); a = lo + 0.1 * (hi - lo); b = lo + 0.9 * (hi - lo)
    i0 = np.argmax(v > a); i1 = i0 + np.argmax(v[i0:] > b); return t[i1] - t[i0]

# ------------------------------------------------------------------------------------------------- A1
def cmd_a1(a):
    banner("A1 — bias point and bootstrap window  (CH1 LOAD, CH2 OUT, CH3 VP, CH4 VN; all grounds on J2)")
    probes("LOAD", "OUT", "VP (V+)", "VN (V-)", "REF", "INPUT", "VCC+", "VCC-")
    scope, gen, dmm = connect(a); d = outdir("A1"); RL = a.rl; E = EXP["A1"]; T = a.tag
    gen.zero(); gen.off()
    # ---- 1a idle
    banner("1a  power-up, no signal (generator off).  Fluke 45 in series with VCC+ (mA), BM235 in series with VCC− (mA)")
    ask("rails up (both ramped together), generator OFF")
    ip = dmm.read("rail current +  (Fluke 45 in series with VCC+)", "mA"); im = I.ManualDMM("BM235").read("rail current −  (BM235 in series with VCC−)", "mA")
    log("A1", "1a rail current + (mA)", ip, "3.5–5", "> 15 → OFF", ""); log("A1", "1a rail current − (mA)", im, "3.5–5", "", "")
    if max(abs(ip), abs(im)) > 15: sys.exit("  !! rail current > 15 mA: POWER OFF. Do not debug live.")
    vccp = dmm.read("VCC+ vs GND (J3 pin 1)"); vccm = dmm.read("VCC− vs GND (J3 pin 3)")
    log("A1", "1a VCC+ / VCC− (V)", f"{vccp:+.2f} / {vccm:+.2f}", f"+{T[:-1]} / -{T[:-1]}")
    scope_a1_layout(scope, 1); t, w = capture(scope, [1, 2, 3, 4], 1.0, "AVER", 16, tb=1e-3)
    vp, vn, out, load = w[3].mean(), w[4].mean(), w[2].mean(), w[1].mean()
    log("A1", "1a VP vs GND (V, scope mean)", round(vp, 3), E["VP_idle"], "±1 V", within(vp, E["VP_idle"], ("abs", 1)))
    log("A1", "1a VN vs GND (V)", round(vn, 3), E["VN_idle"], "±1 V", within(vn, E["VN_idle"], ("abs", 1)))
    log("A1", "1a OUT / LOAD vs GND (V)", f"{out:+.3f} / {load:+.3f}", "≈0 / 0")
    log("A1", "1a window VP−VN (V)", round(vp - vn, 3), E["window"], "±2 V", within(vp - vn, E["window"], ("abs", 2)))
    qb2 = dmm.read("Q2 base (R2/R3 junction) vs GND"); qb1 = dmm.read("Q1 base (R4/R5 junction) vs GND")
    log("A1", "1a Q2 Vbase − V+ (V)  [NPN emitter follower → ≈ +0.65]", round(qb2 - vp, 3), "+0.65", "record")
    log("A1", "1a Q1 Vbase − V− (V)  [PNP emitter follower → ≈ −0.65]", round(qb1 - vn, 3), "−0.65", "record")
    # ripple
    scope.channel(1, 0.05, 0, coupling="AC"); scope.timebase(1e-6); scope.trigger_edge(1, 0.0, "POS", "AUTO")
    t, w = capture(scope, [1], 1.0, "NORM"); rip = w[1].max() - w[1].min()
    sp = np.abs(np.fft.rfft(w[1] - w[1].mean())); fr = np.fft.rfftfreq(len(w[1]), np.median(np.diff(t))); fdom = fr[np.argmax(sp[1:]) + 1]
    log("A1", "1a LOAD ripple Vpp (mV) / dominant f (MHz)", f"{rip*1e3:.1f} / {fdom/1e6:.2f}", "none [L]; TI models ~1 MHz", "record")
    save_csv(os.path.join(d, f"A1_{T}_idle_ripple_bench.csv"), t, {"LOAD_AC": w[1]})
    scope.channel(1, 1, coupling="DC")
    # ---- 1b / 1c runs
    for amp in a.amp:
        banner(f"1{'b' if amp <= 2 else 'c'}  {amp:g} Vpk 300 Hz sine  (I = {amp:g} mA command)")
        sc = 1 if amp <= 2.5 else 2; scope_a1_layout(scope, sc)
        ask(f"CH2 on OUT. Generator will be set to {amp:g} Vpk")
        gen.sine(300, amp); gen.on()
        t, w = capture(scope, [1, 2, 3, 4], 1.5, "AVER", 8, tb=1e-3)
        il = w[1] / RL * 1e3; k = np.argmax(il); kn = np.argmin(il)
        name = f"A1_{T}_{amp:g}mA_bench"; save_csv(os.path.join(d, name + ".csv"), t, {"LOAD": w[1], "OUT": w[2], "VP": w[3], "VN": w[4]})
        if amp <= 2.5:
            log("A1", "1b I_load pk+ / pk− (mA)", f"{il[k]:.4f} / {il[kn]:.4f}", "2.000 / −2.000", "±1 %", within(il[k], amp, ("pct", 1)) and within(il[kn], -amp, ("pct", 1)))
            log("A1", "1b OUT at I pk+ (V)", round(w[2][k], 3), E["OUT_pk"], "±0.2 V", within(w[2][k], E["OUT_pk"], ("abs", 0.2)))
            log("A1", "1b VP / VN at I pk+ (V)", f"{w[3][k]:+.3f} / {w[4][k]:+.3f}", "+6.0 / +1.1", "±1 V", within(w[3][k], E["VP_pk"], ("abs", 1)) and within(w[4][k], E["VN_pk"], ("abs", 1)))
            win = (w[3] - w[4]).mean(); log("A1", "1b window VP−VN avg (V)", round(win, 3), E["window"], "±2 V", within(win, E["window"], ("abs", 2)))
        else:
            top = np.percentile(il, 97); bot = np.percentile(il, 3); flat_hi = np.mean(il > 0.98 * top); flat_lo = np.mean(il < 0.98 * bot)
            log("A1", "1c I_load plateau + / − (mA)", f"{top:.3f} / {bot:.3f}", "+4.01 / −3.38", "±0.5 mA", within(top, E["I_plateau_pos"], ("abs", .5)) and within(bot, E["I_plateau_neg"], ("abs", .5)))
            log("A1", "1c fraction of period on the plateau (+ / −)  [flat sine would be ~0.06]", f"{flat_hi:.2f} / {flat_lo:.2f}", "> 0.1 if clipping", "record")
            win = (w[3] - w[4]).mean(); log("A1", "1c window VP−VN avg (V)", round(win, 3), E["window5"], "±2 V", within(win, E["window5"], ("abs", 2)))
        ask("move CH2 probe from OUT to REF (U1 pin 6); leave the generator running")
        t2, w2 = capture(scope, [1, 2, 3, 4], 1.5, "AVER", 8)
        refvn = w2[2] - w2[4]; vpref = w2[3] - w2[2]
        save_csv(os.path.join(d, name + "_ref.csv"), t2, {"LOAD": w2[1], "REF": w2[2], "VP": w2[3], "VN": w2[4]})
        if amp <= 2.5:
            log("A1", "1b REF−VN min (V)   ← validates the model", round(refvn.min(), 3), E["REFVN_min"], "record")
            log("A1", "1b VP−REF min (V)", round(vpref.min(), 3), E["VPREF_min"], "record")
        else:
            kp = np.argmax(w2[1]); km = np.argmin(w2[1])
            log("A1", "1c REF−VN during the + plateau (V)", round(refvn[kp], 3), 0.20, "record"); log("A1", "1c VP−REF during the − plateau (V)", round(vpref[km], 3), 1.00, "record")
        ipr = dmm.read("rail current + (mA, Fluke 45)", "mA"); imr = I.ManualDMM("BM235").read("rail current − (mA, BM235)", "mA")
        ex = E["Irail"] if amp <= 2.5 else E["Irail5"]
        log("A1", f"1{'b' if amp<=2.5 else 'c'} rail current + / − (mA)", f"{ipr:.2f} / {imr:.2f}", f"{ex} / {ex}", "±20 %", within(ipr, ex, ("pct", 20)) and within(imr, ex, ("pct", 20)))
        overlay_a1(d, name, amp, t, w, t2, w2, RL, T)
        ask("move CH2 back to OUT")
    # ---- 1d onset sweep (free with the DG1022)
    if a.onset:
        banner("1d  plateau onset: command 2.0 → 4.0 Vpk in 0.25 V steps, peak current vs command")
        scope_a1_layout(scope, 2); rows = []
        for amp in np.arange(2.0, 4.01, 0.25):
            gen.sine(300, amp); t, w = capture(scope, [1], 1.0, "AVER", 4, tb=1e-3); il = w[1] / RL * 1e3
            rows.append((amp, il.max(), il.min())); print(f"    {amp:.2f} mA cmd → pk+ {il.max():.3f}   pk− {il.min():.3f}")
        with open(os.path.join(d, f"A1_{T}_onset_bench.csv"), "w", newline="") as fh:
            cw = csv.writer(fh); cw.writerow(["cmd_mA", "Ipk_pos_mA", "Ipk_neg_mA"]); cw.writerows(rows)
        r = np.array(rows); on_p = r[np.argmax(r[:, 1] < 0.98 * r[:, 0]), 0] if (r[:, 1] < 0.98 * r[:, 0]).any() else np.nan
        on_n = r[np.argmax(-r[:, 2] < 0.98 * r[:, 0]), 0] if (-r[:, 2] < 0.98 * r[:, 0]).any() else np.nan
        log("A1", "1d sourcing onset (mA cmd where pk+ < 98 %)", on_p, "~4.0", "record"); log("A1", "1d sinking onset (mA)", on_n, "~3.4", "record")
    gen.zero(); gen.off()
    # ---- 1e rail sweep (window law; the transistor question)
    if a.rails:
        banner("1e  window vs rail: generator OFF, DMM/scope DC only. Ramp BOTH rails together to each value.")
        print("  model [L]: window ≈ 0.16·(V+ − V−)/2 ... 4.97 V at ±30, ~8.2 V at ±50, 19.4 V at ±100. INA149 abs max ±18 V = 36 V window.")
        for vr in a.rails:
            ask(f"rails at ±{vr:g} V (both), generator OFF, rail currents < 15 mA")
            scope_a1_layout(scope, 1); t, w = capture(scope, [1, 2, 3, 4], 1.0, "AVER", 16, tb=1e-3)
            ip = dmm.read("rail current + (mA)", "mA"); vp, vn = w[3].mean(), w[4].mean()
            log("A1", f"1e ±{vr:g} V: VP / VN / window (V), I+ (mA)", f"{vp:+.2f} / {vn:+.2f} / {vp-vn:.2f}, {ip:.1f}", f"window ~{0.163*vr+0.1:.1f} [L scaling]", "record")
            if vp - vn > 30: print("  !! window above 30 V — INA149 abs max is 36 V. Stop here."); break
            gen.sine(300, 2.0); gen.on(); t, w = capture(scope, [1, 2, 3, 4], 1.5, "AVER", 8); il = w[1] / RL * 1e3
            log("A1", f"1e ±{vr:g} V: I pk+ / pk− at 2 mA (mA)", f"{il.max():.4f} / {il.min():.4f}", "2.000 / −2.000", "±1 %", within(il.max(), 2, ("pct", 1)) and within(il.min(), -2, ("pct", 1)))
            save_csv(os.path.join(d, f"A1_{vr:g}V_2mA_bench.csv"), t, {"LOAD": w[1], "OUT": w[2], "VP": w[3], "VN": w[4]}); gen.zero(); gen.off()
    banner("DECISION after A1 (circle on the sheet)")
    print("  window within ±2 V and 2 mA within 1 %  → run A2…A7 at 2 mA as printed\n  window OK, 2 mA a few % low → run at 1 mA (halve commands: --cmd-scale 0.5)\n  window off by > 2 V → check DPAK markings; stop, fix the model first")

def overlay_a1(d, name, amp, t, w, t2, w2, RL, T):
    f, ax = plt.subplots(3, 1, figsize=(9, 10), sharex=True); tm = (t - t[0]) * 1e3
    ax[0].plot(tm, w[1] / RL * 1e3, label="I_load [B]"); ax[1].plot(tm, w[2], label="OUT"); ax[1].plot(tm, w[1], label="LOAD"); ax[1].plot(tm, w[3], label="VP"); ax[1].plot(tm, w[4], label="VN"); ax[1].plot((t2 - t2[0]) * 1e3, w2[2], label="REF")
    ax[2].plot(tm, w[3] - w[4], label="VP−VN"); ax[2].plot((t2 - t2[0]) * 1e3, w2[2] - w2[4], label="REF−VN"); ax[2].plot((t2 - t2[0]) * 1e3, w2[3] - w2[2], label="VP−REF")
    if ltraw and T == "30V":
        try:
            r = ltraw.Raw(os.path.join(TESTS, "A1-bias-bootstrap", "A1-bias-bootstrap.raw")); s = 0 if amp <= 2.5 else 2; idx = r.win(s, 4e-3, 4e-3 + (t[-1] - t[0]))
            ts = (r.x[idx] - 4e-3) * 1e3; ax[0].plot(ts, r.sig("I(RLOAD)", idx) * 1e3, "k--", lw=0.8, label="I_load [L]")
            for n in ("OUT", "VP", "VN", "REF"): ax[1].plot(ts, r.sig(f"V({n})", idx), "--", lw=0.7)
            ax[2].plot(ts, r.sig("V(VP)-V(VN)", idx), "--", lw=0.7); ax[2].plot(ts, r.sig("V(REF)-V(VN)", idx), "--", lw=0.7); ax[2].plot(ts, r.sig("V(VP)-V(REF)", idx), "--", lw=0.7)
        except Exception as e: print("  (sim overlay skipped:", e, ")")
    for x in ax: x.grid(alpha=.3); x.legend(fontsize=8, ncol=3)
    ax[0].set_title(f"A1 {T}, {amp:g} mA cmd, RL={RL:.1f} Ω — bench solid [B], sim dashed [L]"); ax[2].set_xlabel("ms")
    f.tight_layout(); f.savefig(os.path.join(d, name + ".png"), dpi=130); plt.close(f); print("  wrote", name + ".png")

# ------------------------------------------------------------------------------------------------- A2
def cmd_a2(a):
    banner("A2 — DC accuracy. Fluke 45 (5-digit, RATE S) reads INPUT then LOAD at each point. Generator DC only.")
    probes("INPUT", "LOAD"); scope, gen, dmm = connect(a); d = outdir("A2"); RL = a.rl; T = a.tag
    print(f"  RL = {RL:.2f} Ω (measured, Fluke 45 Ω with leads zeroed). Commands scaled ×{a.cmd_scale:g}")
    rows = []
    for c in [0.5, 1, 2, -2, 5, -5]:
        v = c * a.cmd_scale; gen.dc(v); gen.on(); time.sleep(0.5)
        vin = dmm.read(f"cmd {v:+.2f} V:  V(INPUT) vs GND"); vl = dmm.read(f"cmd {v:+.2f} V:  V(LOAD) vs GND (across RL)")
        i = vl / RL * 1e3; icmd = vin / 1000 * 1e3; err = (i - icmd) / icmd * 100 if icmd else np.nan
        exp = EXP["A2"][c] * a.cmd_scale; clip = abs(c) >= 5
        log("A2", f"cmd {v:+.2f} V: I = {i:.4f} mA vs V(INPUT)/1k = {icmd:.4f} mA → err %", round(err, 3), f"{exp:.3f} mA" + (" (clips)" if clip else ""), "±1 %" if not clip else "record plateau", "" if clip else within(err, 0, ("abs", 1)))
        rows.append((v, vin, vl, i, icmd, err))
    gen.zero(); gen.off()
    with open(os.path.join(d, f"A2_{T}_bench.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["cmd_V", "V_INPUT", "V_LOAD", "I_mA", "Icmd_mA", "err_pct"]); cw.writerows(rows)
    r = np.array([x for x in rows if abs(x[0]) <= 2.01 * a.cmd_scale and not np.isnan(x[3])])
    if len(r) >= 3:
        b, a0 = np.polyfit(r[:, 4], r[:, 3], 1)
        log("A2", "offset (µA) / gain error (%) from the 0.5…2 mA points", f"{a0*1e3:+.1f} / {(b-1)*100:+.3f}", "0 / 0", "record")
    f, ax = plt.subplots(2, 1, figsize=(8, 7)); R = np.array(rows)
    ax[0].plot(R[:, 4], R[:, 3], "o-", label="I_load [B]"); ax[0].plot(R[:, 4], R[:, 4], "k--", lw=0.8, label="ideal"); ax[0].set_ylabel("mA"); ax[0].legend()
    ax[1].axhspan(-1, 1, color="g", alpha=.12); ax[1].plot(R[:, 4], R[:, 5], "o-"); ax[1].set_ylabel("error %"); ax[1].set_xlabel("command (mA, from V(INPUT))")
    for x in ax: x.grid(alpha=.3)
    f.tight_layout(); f.savefig(os.path.join(d, f"A2_{T}_bench.png"), dpi=130); plt.close(f)

# ------------------------------------------------------------------------------------------------- A5b
def cmd_a5b(a):
    banner("A5b — output impedance by load change. Fluke 45 IN SERIES with RL (mA, FIXED 30 mA range, RATE S).")
    probes("LOAD"); scope, gen, dmm = connect(a); d = outdir("A5b"); T = a.tag; v = 2.0 * a.cmd_scale
    print(f"  RL1 = {a.rl:.2f} Ω, RL2 = {a.rl2:.2f} Ω. The meter stays on one range for both readings so its gain error cancels.")
    gen.dc(v); gen.on(); time.sleep(0.5); i1 = dmm.read(f"I through RL1 ({a.rl:.0f} Ω)", "mA")
    gen.zero(); ask(f"generator is at 0 V — swap RL1 → RL2 ({a.rl2:.0f} Ω), meter still in series"); gen.dc(v); time.sleep(0.5)
    i2 = dmm.read(f"I through RL2 ({a.rl2:.0f} Ω)", "mA"); gen.zero(); gen.off()
    dv = i2 * 1e-3 * a.rl2 - i1 * 1e-3 * a.rl; di = (i2 - i1) * 1e-3; dpct = (i2 - i1) / i1 * 100; z = abs(dv / di) / 1e6 if di else np.inf
    log("A5b", "I at RL1 / RL2 (mA)", f"{i1:.4f} / {i2:.4f}", "2.0000 / 2.0003", "—")
    log("A5b", "ΔI / I (%)", round(dpct, 4), EXP["A5b"]["dI_pct"], "< 0.1 %", abs(dpct) < 0.1)
    log("A5b", "Z_out = ΔV/ΔI (MΩ)", round(z, 2) if np.isfinite(z) else "> meter floor", EXP["A5b"]["Zout_M"], "> 1.2 MΩ", (z > 1.2) if np.isfinite(z) else True)
    print("  meter floor: 1 µA on 30 mA range = 0.05 % at 2 mA → a 2-count change is the smallest ΔI/I the Fluke can show.")

# ------------------------------------------------------------------------------------------------- A4
def cmd_a4(a):
    banner("A4 — frequency response, scripted. CH1 LOAD, CH2 INPUT. Ratio I_load/V_INPUT by sine fit (immune to noise).")
    probes("LOAD", "INPUT"); scope, gen, dmm = connect(a); d = outdir("A4"); RL = a.rl; T = a.tag; amp = 2.0 * a.cmd_scale
    freqs = [1, 10, 100, 300, 1e3, 10e3] + ([3, 30, 3e3, 30e3, 100e3] if a.extra else [])
    scope.channel(1, 1); scope.channel(2, 1); scope.channel(3, 2, on=False); scope.channel(4, 2, on=False)
    gen.on(); rows = []
    for f in sorted(freqs):
        gen.sine(f, amp); tb = nice(4 / f / 10); scope.timebase(tb); scope.trigger_edge(2, 0.0, "POS", "AUTO")
        t, w = capture(scope, [1, 2], max(1.0, 12 * tb), "NORM" if f < 100 else "AVER", 8)
        al, pl, _ = sine_fit(t, w[1], f); ai, pi, _ = sine_fit(t, w[2], f)
        g = (al / RL * 1e3) / ai; ph = (pl - pi + 180) % 360 - 180
        rows.append((f, ai, al, g, ph, scope.meas("VPP", 1))); print(f"  {f:>8g} Hz  INPUT {ai:.4f} Vpk  LOAD {al:.4f} Vpk  {g:.4f} mA/V  phase {ph:+.2f}°")
        save_csv(os.path.join(d, f"A4_{T}_{f:g}Hz_bench.csv"), t, {"LOAD": w[1], "INPUT": w[2]})
    gen.zero(); gen.off()
    ref = [r for r in rows if r[0] == 10][0][3]
    with open(os.path.join(d, f"A4_{T}_bench.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["f_Hz", "Vin_pk", "Vload_pk", "mA_per_V", "phase_deg", "Vpp_scope", "dB_vs_10Hz"])
        for r in rows:
            db = 20 * np.log10(r[3] / ref); cw.writerow(list(r) + [db])
            if r[0] in EXP["A4"]: log("A4", f"{r[0]:g} Hz: dB vs 10 Hz (phase {r[4]:+.2f}°)", round(db, 3), EXP["A4"][r[0]], "±0.5 dB", abs(db - EXP["A4"][r[0]]) <= 0.5)
            else: log("A4", f"{r[0]:g} Hz (extra): dB vs 10 Hz", round(db, 3), "", "record")
    log("A4", "absolute gain at 10 Hz (mA/V)", round(ref, 4), 1.000, "±1 %", within(ref, 1, ("pct", 1)))
    f, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True); R = np.array(rows)
    ax[0].semilogx(R[:, 0], 20 * np.log10(R[:, 3] / ref), "o-", label="[B]"); ax[1].semilogx(R[:, 0], R[:, 4], "o-")
    if ltraw and T == "30V":
        try:
            r = ltraw.Raw(os.path.join(TESTS, "A4-frequency-response", "A4-frequency-response.raw")); idx = r.win(0); fr = r.x[idx]; h = r.sig("I(RLOAD)", idx) * 1e3
            m = fr <= 2e5; ax[0].semilogx(fr[m], 20 * np.log10(np.abs(h[m])), "k--", lw=0.8, label="[L]"); ax[1].semilogx(fr[m], np.degrees(np.angle(h[m])), "k--", lw=0.8)
        except Exception as e: print("  (sim overlay skipped:", e, ")")
    ax[0].axhspan(-0.5, 0.5, color="g", alpha=.1); ax[0].set_ylabel("dB vs 10 Hz"); ax[1].set_ylabel("phase °"); ax[1].set_xlabel("Hz"); ax[0].legend(); ax[0].set_title(f"A4 {T}, {amp:g} mA pk, RL={RL:.0f} Ω")
    for x in ax: x.grid(alpha=.3, which="both")
    f.tight_layout(); f.savefig(os.path.join(d, f"A4_{T}_bench.png"), dpi=130); plt.close(f)

# ------------------------------------------------------------------------------------------------- A3
def cmd_a3(a):
    banner("A3 — step response, single-shot. CH1 LOAD, CH2 INPUT. Square 0 / 2 V, 500 Hz, fastest edge.")
    probes("LOAD", "INPUT"); scope, gen, dmm = connect(a); d = outdir("A3"); RL = a.rl; T = a.tag; hi = 2.0 * a.cmd_scale; E = EXP["A3"]
    scope.channel(1, 0.5, -hi / 2); scope.channel(2, 0.5, -hi / 2); scope.channel(3, 2, on=False); scope.channel(4, 2, on=False)
    gen.square(500, 0, hi); gen.on(); res = {}
    for tb, tag in [(5e-6, "edge"), (100e-6, "full")]:
        scope.timebase(tb); scope.acquire("NORM"); scope.trigger_edge(2, hi / 2, "POS", "SING")
        if not scope.single(10): print("  !! no trigger"); continue
        t, w = scope.waveforms([1, 2]); il = w[1] / RL * 1e3; cmd = w[2]
        save_csv(os.path.join(d, f"A3_{T}_{hi:g}mA_{tag}_bench.csv"), t, {"LOAD": w[1], "INPUT": w[2]}); res[tag] = (t, il, cmd)
    if "edge" in res:
        t, il, cmd = res["edge"]; te = edge_time(t, cmd); lo, hi_ = np.percentile(cmd, 2), np.percentile(cmd, 98)
        i_end = np.argmax(cmd > lo + 0.9 * (hi_ - lo)); t_end = t[i_end]
        post = t > t_end; fin = il[t > t_end + 0.6 * (t[-1] - t_end)].mean(); pk = il[post].max(); os_ = (pk - fin) / fin * 100
        outside = post & (np.abs(il - fin) > 0.01 * abs(fin)); t_last = (t[np.where(outside)[0][-1]] - t_end) * 1e6 if outside.any() else 0.0
        seg = il[post][: max(10, int(len(il[post]) * 0.5))]; sp = np.abs(np.fft.rfft(seg - seg.mean())); fr = np.fft.rfftfreq(len(seg), np.median(np.diff(t))); fring = fr[np.argmax(sp[1:]) + 1] / 1e6
        log("A3", "generator edge 10–90 % (ns)", round(te * 1e9), "1000 [L stimulus]", "record")
        log("A3", "overshoot vs final (%)", round(os_, 1), E["OS_pct"], "±10 pts", within(os_, E["OS_pct"], ("abs", 10)))
        log("A3", "last exit from ±1 % band (µs after edge end)", round(t_last, 2), E["t_settle_us"], "±50 %", within(t_last, E["t_settle_us"], ("pct", 50)))
        log("A3", "ring frequency (MHz, FFT of first half after the edge)", round(fring, 2), E["f_ring_MHz"], "record")
        log("A3", "final value (mA)", round(fin, 4), E["I_final"] * a.cmd_scale, "±1 %", within(fin, E["I_final"] * a.cmd_scale, ("pct", 1)))
        f, ax = plt.subplots(2, 1, figsize=(9, 7))
        for k, tag in enumerate(["full", "edge"]):
            if tag not in res: continue
            tt, ii, cc = res[tag]; ax[k].plot((tt - t_end) * 1e6, ii, label="I_load [B]"); ax[k].plot((tt - t_end) * 1e6, cc / 1000 * 1e3, "--", lw=0.8, label="cmd [B]")
            if ltraw and T == "30V":
                try:
                    r = ltraw.Raw(os.path.join(TESTS, "A3-step-settling", "A3-step-settling.raw")); idx = r.win(0, 95e-6, 101e-6 + (tt[-1] - t_end)); ax[k].plot((r.x[idx] - 101e-6) * 1e6, r.sig("I(RLOAD)", idx) * 1e3, "k--", lw=0.8, label="I_load [L]")
                except Exception as e: print("  (sim overlay skipped:", e, ")")
            ax[k].axhspan(fin * 0.99, fin * 1.01, color="g", alpha=.15); ax[k].grid(alpha=.3); ax[k].legend(fontsize=8); ax[k].set_ylabel("mA")
        ax[1].set_xlabel("µs after edge end"); ax[0].set_title(f"A3 {T}, 0 → {hi:g} mA, gen edge {te*1e9:.0f} ns, RL={RL:.0f} Ω")
        f.tight_layout(); f.savefig(os.path.join(d, f"A3_{T}_{hi:g}mA_bench.png"), dpi=130); plt.close(f)
    gen.zero(); gen.off()

# ------------------------------------------------------------------------------------------------- A7
def cmd_a7(a):
    banner("A7 — single-rail loss (client's only prototype: SEQ 2 and 3 only, 50 mA limits). CH1 LOAD, 10 ms/div, single-shot.")
    probes("LOAD"); scope, gen, dmm = connect(a); d = outdir("A7"); RL = a.rl; T = a.tag; E = EXP["A7"]; v = 2.0 * a.cmd_scale
    korad = I.Korad(a.korad) if a.korad else None
    if korad: print("  Korad is the + rail: its (−) on GND/J2 ONLY. Scripted OUT0/OUT1.")
    scope.channel(1, 2, 0); scope.channel(2, 2, on=False); scope.channel(3, 2, on=False); scope.channel(4, 2, on=False); scope.timebase(10e-3); scope.acquire("NORM")
    gen.dc(v); gen.on(); time.sleep(0.5)
    # SEQ 2 drop
    scope.trigger_edge(1, v * 0.5, "NEG", "SING"); scope.w(":SING"); time.sleep(0.5)
    if korad: korad.off()
    else: ask("SEQ 2: switch the + rail output OFF now (Xantrex output 1 button)")
    if _wait_stop(scope, 15):
        t, w = scope.waveforms([1]); il = w[1] / RL * 1e3; save_csv(os.path.join(d, f"A7_{T}_seq2_drop_bench.csv"), t, {"LOAD": w[1]})
        cont = il[t > t[-1] - 0.3 * (t[-1] - t[0])].mean(); pk = il[np.argmax(np.abs(il))]
        log("A7", "SEQ 2: I_load after + rail lost, continuous (mA)", round(cont, 3), E["I_cont"], "±50 %", within(cont, E["I_cont"], ("pct", 50)))
        log("A7", "SEQ 2: transient peak during the drop (mA)", round(pk, 3), E["I_peak"], "record")
    scope.trigger_edge(1, 0.0, "POS", "SING"); scope.w(":SING"); time.sleep(0.5)
    if korad: korad.on()
    else: ask("SEQ 2: switch the + rail output back ON")
    if _wait_stop(scope, 15):
        t, w = scope.waveforms([1]); il = w[1] / RL * 1e3; save_csv(os.path.join(d, f"A7_{T}_seq2_restore_bench.csv"), t, {"LOAD": w[1]})
        fin = il[t > t[-1] - 0.3 * (t[-1] - t[0])].mean(); log("A7", "SEQ 2: I_load after + rail restored (mA)", round(fin, 4), E["I_restored"] * a.cmd_scale, "±1 %", within(fin, v, ("pct", 1)))
        log("A7", "SEQ 2: peak during restore (mA)", round(il[np.argmax(np.abs(il))], 3), "", "record")
    # SEQ 3 together
    ask("SEQ 3: switch BOTH rail outputs OFF (together). Generator stays at 2 V DC")
    scope.trigger_edge(1, v * 0.5, "POS", "SING"); scope.w(":SING"); time.sleep(0.5)
    ask("press both output buttons ON together now")
    if _wait_stop(scope, 20):
        t, w = scope.waveforms([1]); il = w[1] / RL * 1e3; save_csv(os.path.join(d, f"A7_{T}_seq3_bench.csv"), t, {"LOAD": w[1]})
        log("A7", "SEQ 3: peak during simultaneous enable (mA)", round(il[np.argmax(np.abs(il))], 3), E["I_seq3_peak"], "< 3 mA", abs(il).max() < 3)
    gen.zero(); gen.off()

def _wait_stop(scope, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if scope.q(":TRIG:STAT?").startswith("STOP"): return True
        time.sleep(0.05)
    print("  !! no trigger"); return False

# ------------------------------------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["check", "preflight", "a1", "a2", "a5b", "a4", "a3", "a7"])
    p.add_argument("--rl", type=float, default=1000.0, help="measured RL1 (Ω)"); p.add_argument("--rl2", type=float, default=2200.0)
    p.add_argument("--tag", default="30V"); p.add_argument("--scope"); p.add_argument("--gen", default="auto", help="auto | manual"); p.add_argument("--gen-res")
    p.add_argument("--dmm-port"); p.add_argument("--korad"); p.add_argument("--cmd-scale", type=float, default=1.0, help="0.5 if A1 says run at 1 mA")
    p.add_argument("--amp", type=float, nargs="+", default=[2, 5]); p.add_argument("--onset", action="store_true"); p.add_argument("--rails", type=float, nargs="*")
    p.add_argument("--extra", action="store_true", help="A4: add 3, 30, 3k, 30k, 100k Hz")
    a = p.parse_args(); globals()["cmd_" + a.cmd](a)

if __name__ == "__main__": main()
