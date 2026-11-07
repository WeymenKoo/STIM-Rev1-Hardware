#!/usr/bin/env python3
"""One documentation figure per B0 run: power-up single shot (left) + steady-state trend (right).
  python b0_figure.py <base> <rail_V> <I_mA> [--note "..."]     e.g. B0_pm05p75V_heat2_noRL 5.75 57.79
Reads ../tests/B0-bringup/bench/<base>_startup.csv and <base>_trend.csv, writes <base>.png (replaces the separate
startup png). Every number on it is [B]."""
import argparse, csv, os
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests", "B0-bringup", "bench")


def main():
    p = argparse.ArgumentParser(); p.add_argument("base"); p.add_argument("rail", type=float); p.add_argument("i_ma", type=float)
    p.add_argument("--note", default=""); a = p.parse_args()
    st = np.array(list(csv.reader(open(os.path.join(D, a.base + "_startup.csv"))))[1:], dtype=float)
    tr = np.array(list(csv.reader(open(os.path.join(D, a.base + "_trend.csv"))))[1:], dtype=float)
    on = tr[tr[:, 1] > 1.0]                                   # captures with the rails on
    vpvn = float(np.median(on[:, 3])); r = vpvn / (a.i_ma * 1e-3)
    lim = 1.25 * a.rail
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(12, 4.4))
    a0.plot(st[:, 0] * 1e3, st[:, 1], label="V+ (Q2 tab)"); a0.plot(st[:, 0] * 1e3, st[:, 2], label="V− (Q1 pin 3)")
    for v, s in ((a.rail, "VCC+"), (-a.rail, "VCC−"), (0, "GND")):
        a0.axhline(v, ls=":", lw=0.8, color="grey"); a0.text(st[0, 0] * 1e3, v, " " + s, va="bottom", fontsize=8, color="grey")
    a0.axvline(0, ls="--", lw=0.8, color="grey"); a0.set_ylim(-lim, lim)
    a0.set_xlabel("t (ms) from trigger (V+ rising through 1 V)"); a0.set_ylabel("V"); a0.grid(alpha=0.3); a0.legend(loc="lower right")
    a0.set_title("power-up, single shot 50 ms/div")
    a1.plot(tr[:, 0], tr[:, 1], "o-", ms=4, label="V+"); a1.plot(tr[:, 0], tr[:, 2], "o-", ms=4, label="V−")
    a1.plot(tr[:, 0], tr[:, 3], "s--", ms=4, label="V+ − V− (across ICs)")
    a1.set_ylim(-lim, lim); a1.set_xlabel("time since rails on (s)"); a1.grid(alpha=0.3); a1.legend(loc="lower right")
    a1.set_title("steady state, 16-avg mean per capture (last point: turn-off)")
    fig.suptitle(f"{a.base}  [B]  TBS1102C 2 V/div · I = {a.i_ma:g} mA (Fluke 45) · short = {vpvn:.3f} V / {a.i_ma:g} mA = {r:.1f} Ω"
                 + (f"\n{a.note}" if a.note else ""), fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(D, a.base + ".png"), dpi=130); plt.close(fig)
    sp = os.path.join(D, a.base + "_startup.png")
    if os.path.exists(sp): os.remove(sp)
    print(f"  wrote {a.base}.png   V+-V- {vpvn:.3f} V  R {r:.1f} Ω  ({len(on)} captures with rails on)")


if __name__ == "__main__": main()
