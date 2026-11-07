#!/usr/bin/env python3
"""B0 — staged low-rail bring-up of the AS-BUILT client board (bench 2026-11-06).

Why: STIM.NET shows Q2 = MJD350 PNP (E on VCC+, C on V+) and Q1 = MJD340 NPN (E on V−, C on VCC−), not the
NPN/PNP emitter followers of the LTspice model. Hypothesis [H]: V+ ≈ VCC+ and V− ≈ VCC− (no bootstrap).
Client says the board worked to ±50 V. This step tells the two apart without exceeding IC supply ratings.

  python bringup.py <rail_V> <I_plus_mA> [--note "..."] [--visa ivi]
      CH1 = V+ (Q2 tab), CH2 = V− (Q1 pin 3), grounds on J2, Fluke 45 in series with VCC+.

Saves ../tests/B0-bringup/bench/B0_pmXXV.csv + .png (scope, 16 avg), logs every number to session_log.csv.
"""
import argparse, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bench_tbs as T, bench_rig as R

OUT = os.path.join(HERE, "..", "tests", "B0-bringup", "bench")


def main():
    p = argparse.ArgumentParser(); p.add_argument("rail", type=float); p.add_argument("i_plus", type=float)
    p.add_argument("--note", default=""); p.add_argument("--visa", default="ivi"); a = p.parse_args()
    os.makedirs(OUT, exist_ok=True); tag = f"pm{a.rail:04.1f}V".replace(".", "p")
    T.make_rm(a.visa); f = T.find(verbose=False)
    if "scope" not in f: sys.exit("no TBS found")
    sc = T.TBS1000C(f["scope"])
    sc.timebase(1e-3); sc.trigger_edge(1, 0.0, "POS", "AUTO")
    sc.channel(1, R.nice(a.rail / 3)); sc.channel(2, R.nice(a.rail / 3))
    t, w = T.grab(sc)
    vp, vn = float(np.mean(w[1])), float(np.mean(w[2]))
    rp, rn = float(np.ptp(w[1])), float(np.ptp(w[2]))
    mp, mn = sc.meas("VAVG", 1), sc.meas("VAVG", 2)

    # verdict
    asbuilt = vp > 0.8 * a.rail and vn < -0.8 * a.rail
    follows = abs(vp) < 0.5 * a.rail and abs(vn) < 0.5 * a.rail
    verdict = "AS-BUILT [H] confirmed: V+/V- sit on the rails (no bootstrap)" if asbuilt else \
              "FOLLOWS: V+/V- near OUT (bootstrap works, client right)" if follows else "NEITHER: send me this, stop here"
    stop = a.i_plus > 15 or (vp - vn) > 36

    R.log("B0", f"±{a.rail:g} V  rail current + (mA, Fluke 45)", a.i_plus, "4–5 (ICs alive)", "> 15 → OFF", a.i_plus <= 15)
    R.log("B0", f"±{a.rail:g} V  V+ (Q2 tab) mean (V)", round(vp, 3), f"[H] ≈ +{a.rail:g}")
    R.log("B0", f"±{a.rail:g} V  V- (Q1 pin 3) mean (V)", round(vn, 3), f"[H] ≈ -{a.rail:g}")
    R.log("B0", f"±{a.rail:g} V  V+ - V- across ICs (V)", round(vp - vn, 3), "≤ 36 (INA149)", "", (vp - vn) <= 36)
    R.log("B0", f"±{a.rail:g} V  ripple pk-pk V+ / V- (V)", f"{rp:.3f} / {rn:.3f}")
    R.log("B0", f"±{a.rail:g} V  verdict", verdict + (f"  note: {a.note}" if a.note else ""))

    R.save_csv(os.path.join(OUT, f"B0_{tag}.csv"), t, {"V+ (CH1)": w[1], "V- (CH2)": w[2]})
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(t * 1e3, w[1], label=f"V+ (Q2 tab)  mean {vp:+.3f} V"); ax.plot(t * 1e3, w[2], label=f"V− (Q1 pin 3)  mean {vn:+.3f} V")
    for v, s in ((a.rail, "VCC+"), (-a.rail, "VCC−"), (0, "GND")):
        ax.axhline(v, ls=":", lw=0.8, color="grey"); ax.text(t[0] * 1e3, v, f" {s}", va="bottom", fontsize=8, color="grey")
    ax.set_xlabel("t (ms)"); ax.set_ylabel("V"); ax.set_ylim(-1.25 * a.rail, 1.25 * a.rail); ax.grid(alpha=0.3); ax.legend(loc="center right")
    ax.set_title(f"B0 as-built bring-up, rails ±{a.rail:g} V, I+ = {a.i_plus:g} mA  [B], TBS1102C 16 avg")
    fig.tight_layout(); png = os.path.join(OUT, f"B0_{tag}.png"); fig.savefig(png, dpi=130); plt.close(fig)
    print("  wrote", os.path.relpath(png, HERE))

    print(f"\n  rails ±{a.rail:g} V   I+ = {a.i_plus:g} mA")
    print(f"  V+ = {vp:+.3f} V (scope MEAN {mp:+.3f})   V- = {vn:+.3f} V (scope MEAN {mn:+.3f})   V+ - V- = {vp - vn:.2f} V")
    print(f"  {verdict}")
    if stop: print("  !! STOP: both outputs OFF (current > 15 mA or > 36 V across the ICs)")


if __name__ == "__main__": main()
