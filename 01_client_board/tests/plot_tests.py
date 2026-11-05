#!/usr/bin/env python3
"""Figures + numbers for A2..A7 from the LTspice .raw files. Run in tests/: python3 plot_tests.py [A2 A3 ...]
Each test writes PNGs into its own folder and prints the numbers that go in RECORD.md."""
import sys, numpy as np, ltraw
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
VR = (30, 100); OUT = {}
def fig(n, h): f, ax = plt.subplots(n, 1, figsize=(9, h), sharex=True); return f, (ax if n > 1 else [ax])
def done(f, path): f.tight_layout(); f.savefig(path, dpi=130); plt.close(f); print("wrote", path)

def A2():
    d = "A2-accuracy-vs-command/"; r = ltraw.Raw(d+"A2-accuracy-vs-command.raw")
    cmds = [-5, -2, 0.5, 1, 2, 5]   # log order: Vrail inner
    res = {v: [] for v in VR}
    for k, c in enumerate(cmds):
        for j, v in enumerate(VR):
            w = r.win(2*k+j, 0.2e-3, 1e-3) if r.x[r.steps[0]].max() < 1.5e-3 else r.win(2*k+j, 1.2e-3, 2e-3); i = r.sig("I(RLOAD)", w).mean()*1e3
            res[v].append((c, i, (i-c)/c*100))
    OUT["A2"] = res
    print("A2  cmd mA | 30V: I, err% | 100V: I, err%")
    for a, b in zip(res[30], res[100]): print(f"  {a[0]:5.1f} | {a[1]:8.4f} {a[2]:8.3f} | {b[1]:8.4f} {b[2]:8.3f}")
    for v in VR:
        f, ax = fig(2, 7); c = np.array([x[0] for x in res[v]]); i = np.array([x[1] for x in res[v]]); e = np.array([x[2] for x in res[v]])
        ax[0].plot(c, c, "k--", lw=0.8, label="ideal 1 mA/V"); ax[0].plot(c, i, "o-", label="I_load (sim)")
        ax[0].set_ylabel("I_load (mA)"); ax[0].legend(); ax[0].set_title(f"A2 DC accuracy vs command [L], rails ±{v} V, RL = 1 kΩ")
        ax[1].axhspan(-1, 1, color="g", alpha=.12, label="±1 % pass band"); ax[1].plot(c, e, "o-"); ax[1].set_ylabel("error (%)"); ax[1].set_xlabel("command (mA)")
        lim = max(2, min(25, abs(e).max()*1.2)); ax[1].set_ylim(-lim, lim); ax[1].legend()
        for a in ax: a.grid(alpha=.3)
        done(f, d+f"A2_{v}V.png")

def A3():
    d = "A3-step-settling/"; r = ltraw.Raw(d+"A3-step-settling.raw")
    labs = [(30, 2), (100, 2), (30, 5), (100, 5)]; res = {}
    print("A3  rail/Istep | Ifin mA | Ipk mA | OS % | t enter 1% (us after edge end) | last exit 1% (us)")
    for s, (v, ist) in enumerate(labs):
        w = r.win(s); t = r.x[w]; i = r.sig("I(RLOAD)", w)
        fin = i[(t >= 300e-6) & (t <= 500e-6)].mean(); seg = (t >= 100e-6) & (t <= 300e-6); pk = i[seg].max()
        band = np.abs(i - fin) <= 0.01*abs(fin); tt = t[seg]; bb = band[seg]
        t_in = tt[np.argmax(bb)] if bb.any() else np.nan
        out = np.where(~bb)[0]; t_last = tt[out[-1]] if len(out) and tt[out[-1]] < 290e-6 else np.nan
        res[(v, ist)] = dict(Ifin=fin*1e3, Ipk=pk*1e3, OS=(pk-fin)/fin*100, t_in=(t_in-101e-6)*1e6, t_last=(t_last-101e-6)*1e6)
        x = res[(v, ist)]; print(f"  {v}V/{ist}mA | {x['Ifin']:.4f} | {x['Ipk']:.4f} | {x['OS']:.1f} | {x['t_in']:.2f} | {x['t_last']:.2f}")
        f, ax = plt.subplots(2, 1, figsize=(9, 7))
        ax[0].plot(t*1e6, r.sig("V(INPUT)", w), "--", label="command V(INPUT)/1k [mA]"); ax[0].plot(t*1e6, i*1e3, label="I(RLOAD) [mA]")
        ax[0].set_ylabel("mA"); ax[0].legend(); ax[0].set_title(f"A3 step response [L], rails ±{v} V, 0 → +{ist} → −{ist} mA, 1 µs edges, RL = 1 kΩ")
        z = (t >= 95e-6) & (t <= 130e-6)
        ax[1].plot(t[z]*1e6, r.sig("V(INPUT)", w)[z], "--", label="command"); ax[1].plot(t[z]*1e6, i[z]*1e3, label="I(RLOAD)")
        ax[1].axhspan(fin*1e3*0.99, fin*1e3*1.01, color="g", alpha=.15, label="±1 % of final"); ax[1].set_xlim(95, 130)
        ax[1].set_ylabel("mA"); ax[1].set_xlabel("time (µs)   [lower pane: zoom on the rising edge]"); ax[1].legend(fontsize=8)
        ax[0].set_xlim(0, 1200); ax[0].set_xlabel("time (µs)   [full record]")
        for a in ax: a.grid(alpha=.3)
        done(f, d+f"A3_{v}V_{ist}mA.png")
    OUT["A3"] = {f"{k[0]}V_{k[1]}mA": v for k, v in res.items()}

def A4():
    d = "A4-frequency-response/"; r = ltraw.Raw(d+"A4-frequency-response.raw"); fm = [1, 10, 100, 300, 1e3, 10e3]; res = {}
    print("A4  rail | mag dB at 1,10,100,300,1k,10k Hz | phase deg at 300 Hz, 1 kHz | peak dB @ Hz")
    for s, v in enumerate(VR):
        w = r.win(s); fr = r.x[w]; h = r.sig("I(RLOAD)", w)*1e3; mag = 20*np.log10(np.abs(h)); ph = np.degrees(np.angle(h))
        at = lambda x, f0: x[np.argmin(np.abs(fr-f0))]
        m = [at(mag, f0) for f0 in fm]; p300, p1k = at(ph, 300), at(ph, 1e3); kp = np.argmax(mag)
        res[v] = dict(mag=m, ph300=p300, ph1k=p1k, pk_dB=mag[kp], f_pk=fr[kp], dB10k_vs_1=m[5]-m[0])
        print(f"  {v}V | " + " ".join(f"{x:+.3f}" for x in m) + f" | {p300:.2f}, {p1k:.2f} | {mag[kp]:+.2f} @ {fr[kp]:.3g}")
        f, ax = fig(2, 7)
        ax[0].semilogx(fr, mag); ax[0].plot(fm, m, "o"); ax[0].set_ylabel("|I_load / V_cmd|  (dB re 1 mA/V)")
        ax[0].set_title(f"A4 small-signal frequency response [L], rails ±{v} V, RL = 1 kΩ"); ax[0].set_ylim(min(-6, mag.min()-1), max(6, mag.max()+1))
        ax[1].semilogx(fr, ph); ax[1].set_ylabel("phase (°)"); ax[1].set_xlabel("frequency (Hz)")
        for a in ax: a.grid(alpha=.3, which="both")
        done(f, d+f"A4_{v}V.png")
    OUT["A4"] = res

def A5a():
    d = "A5a-output-impedance-ac/"; r = ltraw.Raw(d+"A5a-output-impedance-ac.raw"); fm = [1, 100, 1e3, 10e3]; res = {}
    labs = [(30, "50 Ω"), (100, "50 Ω"), (30, "ideal"), (100, "ideal")]
    print("A5a rail/RS | Z at 1, 100, 1k, 10k Hz (ohm) | C_out pF at 10k")
    for s, (v, rs) in enumerate(labs):
        w = r.win(s); fr = r.x[w]; z = np.abs(r.sig("V(LOAD)", w)); zz = [z[np.argmin(np.abs(fr-f0))] for f0 in fm]
        res[f"{v}V_{rs}"] = dict(Z=zz, C_pF=1e12/(2*np.pi*10e3*zz[3])); print(f"  {v}V/{rs} | " + " ".join(f"{x:.3g}" for x in zz) + f" | {res[f'{v}V_{rs}']['C_pF']:.1f}")
    for v in VR:
        f, ax = fig(1, 4.5)
        for s, (vv, rs) in enumerate(labs):
            if vv != v: continue
            w = r.win(s); ax[0].loglog(r.x[w], np.abs(r.sig("V(LOAD)", w)), label=f"|Z_out|, generator {rs}")
        ax[0].set_ylabel("|Z_out| (Ω)"); ax[0].set_xlabel("frequency (Hz)"); ax[0].legend(); ax[0].grid(alpha=.3, which="both")
        ax[0].set_title(f"A5a output impedance (AC injection, command 0) [L], rails ±{v} V")
        done(f, d+f"A5a_{v}V.png")
    OUT["A5a"] = res

def A5b():
    d = "A5b-output-impedance-dc/"; r = ltraw.Raw(d+"A5b-output-impedance-dc.raw"); labs = [(30, 1000), (100, 1000), (30, 2200), (100, 2200)]; res = {}
    for s, (v, rl) in enumerate(labs):
        w = (r.win(s, 0.2e-3, 1e-3) if r.x[r.steps[0]].max() < 1.5e-3 else r.win(s, 1.2e-3, 2e-3)); res[(v, rl)] = (r.sig("I(RLOAD)", w).mean(), r.sig("V(LOAD)", w).mean())
    print("A5b rail | I 1k, V 1k | I 2.2k, V 2.2k | dI % | Z_out")
    out = {}
    for v in VR:
        i1, v1 = res[(v, 1000)]; i2, v2 = res[(v, 2200)]; z = (v2-v1)/(i1-i2) if i1 != i2 else np.inf
        out[v] = dict(I1=i1*1e3, V1=v1, I2=i2*1e3, V2=v2, dI_pct=(i2-i1)/i1*100, Z=z)
        print(f"  {v}V | {i1*1e3:.5f} mA, {v1:.4f} V | {i2*1e3:.5f} mA, {v2:.4f} V | {(i2-i1)/i1*100:+.4f} | {z:.3g} Ω")
    f, ax = fig(1, 4)
    x = np.arange(2); wdt = .35
    ax[0].bar(x-wdt/2, [out[30]["I1"], out[30]["I2"]], wdt, label="±30 V"); ax[0].bar(x+wdt/2, [out[100]["I1"], out[100]["I2"]], wdt, label="±100 V")
    ax[0].set_xticks(x); ax[0].set_xticklabels(["RL = 1.0 kΩ", "RL = 2.2 kΩ"]); ax[0].set_ylabel("I_load (mA)"); ax[0].set_ylim(1.99, 2.01); ax[0].legend(); ax[0].grid(alpha=.3, axis="y")
    ax[0].set_title("A5b output impedance by load change [L], 2 mA command — bench pass = no visible change")
    done(f, d+"A5b.png"); OUT["A5b"] = out

def A7():
    d = "A7-rail-loss/"; r = ltraw.Raw(d+"A7-rail-loss.raw"); seqn = {1: "SEQ 1: +rail first, −rail 4.5 ms later", 2: "SEQ 2: both up, +rail lost at 10 ms", 3: "SEQ 3: both rails together"}
    res = {}; print("A7 rail/SEQ | I max mA | I min mA | I end mA")
    for v_i, v in enumerate(VR):
        f, ax = fig(3, 10)
        for q in (1, 2, 3):
            s = 2*(q-1)+v_i; w = r.win(s); t = r.x[w]*1e3; i = r.sig("I(RLOAD)", w)*1e3
            res[f"{v}V_SEQ{q}"] = dict(Imax=i.max(), Imin=i.min(), Iend=i[t >= 40].mean()); x = res[f"{v}V_SEQ{q}"]
            print(f"  {v}V/SEQ{q} | {x['Imax']:.2f} | {x['Imin']:.2f} | {x['Iend']:.3f}")
            a = ax[q-1]; a.plot(t, i, label="I(RLOAD) [mA]"); a2 = a.twinx()
            a2.plot(t, r.sig("V(VCCP)", w), "g--", lw=.8, label="VCC+"); a2.plot(t, r.sig("V(VCCN)", w), "r--", lw=.8, label="VCC−"); a2.set_ylabel("rails (V)")
            a.axhline(10, color="k", lw=.6); a.axhline(-10, color="k", lw=.6); a.set_ylabel("mA"); a.set_title(seqn[q], fontsize=10); a.grid(alpha=.3)
            a.legend(loc="upper left", fontsize=8); a2.legend(loc="upper right", fontsize=8)
        ax[2].set_xlabel("time (ms)"); ax[0].set_title(f"A7 rail sequencing / single-rail loss [L], rails ±{v} V, 2 mA command, RL = 1 kΩ — black lines = ±10 mA limit\n" + seqn[1], fontsize=10)
        done(f, d+f"A7_{v}V.png")
    OUT["A7"] = res

tests = sys.argv[1:] or ["A2", "A3", "A4", "A5a", "A5b", "A7"]
for t in tests: globals()[t]()

