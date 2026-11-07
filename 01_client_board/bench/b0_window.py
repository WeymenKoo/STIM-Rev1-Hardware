#!/usr/bin/env python3
"""B0 timed window: arm, wait for the rails (CH1 = V+ > 1 V), capture V+/V- repeatedly until the rails go off.
  python b0_window.py <rail_V> [--tag run2]     CH1 = V+ (Q2 tab), CH2 = V- (Q1 pin 3), grounds J2. Generator held OFF.
Saves ../tests/B0-bringup/bench/B0_pmXXV_<tag>_wave.csv (every capture) + _trend.csv + .png; logs to session_log.csv."""
import argparse, csv, os, sys, time
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bench_tbs as T, bench_rig as R, instruments as I

OUT = os.path.join(HERE, "..", "tests", "B0-bringup", "bench")


def main():
    p = argparse.ArgumentParser(); p.add_argument("rail", type=float); p.add_argument("--tag", default="run2")
    p.add_argument("--wait", type=float, default=180); p.add_argument("--window", type=float, default=25, help="max s of captures")
    p.add_argument("--transient", type=float, default=0, help="s/div: single-shot the power-up edge first (e.g. 0.05)")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True); base = f"B0_pm{a.rail:05.2f}V".replace(".", "p") + f"_{a.tag}"
    T.make_rm("ivi"); f = T.find(verbose=False)
    sc = T.TBS1000C(f["scope"])
    if "gen" in f:
        g = I.DG1022(f["gen"]); g.zero(); g.off(); print("  generator: 0 V, output OFF (verified)")
    sc.timebase(1e-3); sc.trigger_edge(1, 0.0, "POS", "AUTO")
    sc.channel(1, 2.0); sc.channel(2, 2.0)
    if a.transient:
        # single shot on CH1 rising through 1 V: captures the power-up edge of V+ and V- and is itself the "rails on" detector
        tb = a.transient; sc.timebase(tb); sc.acquire("NORM")
        sc.trigger_edge(1, 1.0, "POS", "NORM"); sc.arm()
        print(f"READY: single-shot armed, CH1 rising through 1 V, {tb*1e3:g} ms/div ({10*tb*1e3:g} ms record, trigger mid-screen)", flush=True)
        t0 = time.time()
        while True:
            while not sc.done():
                if time.time() - t0 > a.wait: sys.exit("  no trigger within the wait time; nothing captured")
                time.sleep(0.2)
            tt, wt = sc.waveforms([1, 2]); raw_t = {c: sc.last_raw.get(c) for c in (1, 2)}
            if np.mean(wt[1][-50:]) > 1.0: break
            # glitch (probe clip, touch) crossed 1 V but V+ is not up at the end of the record: not a power-up (2026-11-06)
            print(f"  false trigger (V+ ends at {np.mean(wt[1][-50:]):+.2f} V): re-armed", flush=True); sc.arm()
        t_on = time.time()
        print(f"RAILS ON: triggered. V+ {wt[1][0]:+.2f} -> {wt[1][-1]:+.2f} V, V- {wt[2][0]:+.2f} -> {wt[2][-1]:+.2f} V over the record", flush=True)
        R.save_csv(os.path.join(OUT, base + "_startup.csv"), tt, {"V+ (CH1)": wt[1], "V- (CH2)": wt[2]})
        with open(os.path.join(OUT, base + "_startup_raw.csv"), "w", newline="") as fh:
            cw = csv.writer(fh); cw.writerow(["# TBS1102C CURVe? counts; V = (counts - YOFF) * YMULT + YZERO; t = XZERO + (n - PT_OFF) * XINCR"])
            for c, r in raw_t.items():
                cw.writerow([f"# CH{c}"] + [f"{p}={r[p]}" for p in ("YMULT", "YOFF", "YZERO", "XINCR", "XZERO", "PT_OFF", "width", "byte_order")])
            cw.writerow(["n", "CH1 counts", "CH2 counts"]); cw.writerows(zip(range(len(raw_t[1]["counts"])), raw_t[1]["counts"].astype(int), raw_t[2]["counts"].astype(int)))
        fig, ax = plt.subplots(figsize=(9, 4.5))
        ax.plot(tt * 1e3, wt[1], label="V+ (Q2 tab)"); ax.plot(tt * 1e3, wt[2], label="V− (Q1 pin 3)")
        for v, s in ((a.rail, "VCC+"), (-a.rail, "VCC−"), (0, "GND")): ax.axhline(v, ls=":", lw=0.8, color="grey"); ax.text(tt[0] * 1e3, v, f" {s}", va="bottom", fontsize=8, color="grey")
        ax.axvline(0, ls="--", lw=0.8, color="grey"); ax.text(0, 1.1 * a.rail, " trigger: V+ rising through 1 V", fontsize=8, color="grey")
        ax.set_ylim(-1.25 * a.rail, 1.25 * a.rail); ax.set_xlabel("t (ms) from trigger"); ax.set_ylabel("V"); ax.grid(alpha=0.3); ax.legend(loc="lower right")
        ax.set_title(f"B0 as-built power-up, rails ±{a.rail:g} V  [B] TBS1102C single shot, 2 V/div, {tb*1e3:g} ms/div")
        fig.tight_layout(); fig.savefig(os.path.join(OUT, base + "_startup.png"), dpi=130); plt.close(fig)
        print("  wrote startup csv / raw / png", flush=True)
        sc.timebase(1e-3); sc.trigger_edge(1, 0.0, "POS", "AUTO")
    else:
        sc.acquire("NORM"); sc.run(); time.sleep(0.5)
    # MEASUrement:IMMed:VALue? returned the PREVIOUS run's value (bench 2026-11-06) -> detect on fresh CH1 records,
    # and require 2 consecutive records > 1 V after first seeing one < 0.5 V (rails really off at arm time).
    seen_off, ready, hits, t0 = False, False, 0, time.time()
    while not a.transient:
        # CURVe? while RUNning in SAMple mode returned a frozen record (missed a 3.9 V step, 2026-11-06): stop, read, run
        sc.stop(); time.sleep(0.05); v = float(sc.waveform(1)[1].mean()); sc.run(); time.sleep(0.15)
        if v < 0.5: seen_off, hits = True, 0
        elif v > 1.0 and seen_off: hits += 1
        if seen_off and not ready:
            ready = True; print(f"READY: rails read {v:+.2f} V (off). Waiting for V+ > 1 V", flush=True)
        if hits >= 2:
            t_on = time.time(); print(f"RAILS ON detected (V+ = {v:+.2f} V), capturing", flush=True); break
        if time.time() - t0 > a.wait: sys.exit("  no rails seen within the wait time; nothing captured")
        time.sleep(0.1)

    trend, waves, raws = [], {}, {}
    sc.acquire("AVER", 16)
    while time.time() - t_on < a.window:
        sc.run(); time.sleep(0.9); sc.stop(); time.sleep(0.1)
        t, w = sc.waveforms([1, 2]); el = time.time() - t_on
        vp, vn = float(w[1].mean()), float(w[2].mean())
        if vp < 1.0 and trend: print(f"  {el:5.1f} s  rails OFF detected", flush=True); break
        trend.append((round(el, 2), vp, vn, vp - vn, float(np.ptp(w[1])), float(np.ptp(w[2]))))
        waves[f"V+ @{el:.1f}s"] = w[1]; waves[f"V- @{el:.1f}s"] = w[2]
        for ch in (1, 2): raws[f"CH{ch} @{el:.1f}s"] = getattr(sc, "last_raw", {}).get(ch)
        print(f"  {el:5.1f} s   V+ {vp:+.3f}   V- {vn:+.3f}   V+-V- {vp - vn:.3f} V", flush=True)
    sc.acquire("NORM"); sc.run()
    if not trend: sys.exit("  no capture while the rails were on")

    R.save_csv(os.path.join(OUT, base + "_wave.csv"), t, waves)
    # raw scope data: ADC counts exactly as sent by CURVe?, plus the preamble needed to convert them (V = (counts - YOFF) * YMULT + YZERO)
    raws = {k: v for k, v in raws.items() if v is not None}
    if raws:
        with open(os.path.join(OUT, base + "_raw.csv"), "w", newline="") as fh:
            cw = csv.writer(fh)
            cw.writerow(["# TBS1102C CURVe? counts; V = (counts - YOFF) * YMULT + YZERO; t = XZERO + (n - PT_OFF) * XINCR"])
            for k, r in raws.items():
                cw.writerow([f"# {k}"] + [f"{p}={r[p]}" for p in ("YMULT", "YOFF", "YZERO", "XINCR", "XZERO", "PT_OFF", "width", "byte_order")])
            cw.writerow(["n"] + list(raws))
            cw.writerows(zip(range(len(next(iter(raws.values()))["counts"])), *[r["counts"].astype(int) for r in raws.values()]))
        print("  wrote", os.path.relpath(os.path.join(OUT, base + "_raw.csv"), HERE))
    with open(os.path.join(OUT, base + "_trend.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["t_since_on_s", "Vplus_V", "Vminus_V", "Vplus_minus_Vminus_V", "ptp_Vplus_V", "ptp_Vminus_V"]); cw.writerows(trend)
    tr = np.array(trend)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(tr[:, 0], tr[:, 1], "o-", label="V+ (Q2 tab)"); a1.plot(tr[:, 0], tr[:, 2], "o-", label="V− (Q1 pin 3)")
    a1.plot(tr[:, 0], tr[:, 3], "s--", label="V+ − V− (across ICs)")
    a1.set_xlabel("time since rails on (s)"); a1.set_ylabel("V (16-avg mean)"); a1.grid(alpha=0.3); a1.legend(); a1.set_title("trend over the window")
    k1, k2 = list(waves)[0], list(waves)[1]
    a2.plot(t * 1e3, waves[k1], label=k1); a2.plot(t * 1e3, waves[k2], label=k2)
    for v, s in ((a.rail, "VCC+"), (-a.rail, "VCC−"), (0, "GND")): a2.axhline(v, ls=":", lw=0.8, color="grey"); a2.text(t[0] * 1e3, v, f" {s}", va="bottom", fontsize=8, color="grey")
    a2.set_ylim(-1.25 * a.rail, 1.25 * a.rail); a2.set_xlabel("t (ms)"); a2.grid(alpha=0.3); a2.legend(loc="center right"); a2.set_title("first capture")
    fig.suptitle(f"B0 as-built, rails ±{a.rail:g} V, {a.tag}  [B] TBS1102C 16 avg, 2 V/div"); fig.tight_layout()
    png = os.path.join(OUT, base + ".png"); fig.savefig(png, dpi=130); plt.close(fig); print("  wrote", os.path.relpath(png, HERE))

    R.log("B0", f"±{a.rail:g} V {a.tag}  V+ first / last (V)", f"{tr[0,1]:+.3f} / {tr[-1,1]:+.3f}")
    R.log("B0", f"±{a.rail:g} V {a.tag}  V- first / last (V)", f"{tr[0,2]:+.3f} / {tr[-1,2]:+.3f}")
    R.log("B0", f"±{a.rail:g} V {a.tag}  V+ - V- first / last (V)", f"{tr[0,3]:.3f} / {tr[-1,3]:.3f}", "short: ~1.26 (run 1)")
    print(f"DONE  {len(trend)} captures over {tr[-1,0]:.1f} s", flush=True)


if __name__ == "__main__": main()
