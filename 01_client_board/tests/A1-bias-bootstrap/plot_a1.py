#!/usr/bin/env python3
"""A1 plots from the LTspice .raw. Run in this folder: python3 plot_a1.py
Writes A1_<rail>V_<cmd>mA.png, one per step (3 panes each) and prints the peak-time headroom numbers."""
import numpy as np, re, sys, pathlib
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

def read_raw(path):
    b = pathlib.Path(path).read_bytes()
    enc = "utf-16-le" if b[1:2] == b"\x00" else "latin-1"
    key = "Binary:\n".encode(enc); i = b.index(key); hdr = b[:i].decode(enc); data = b[i+len(key):]
    nv = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1)); npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
    names = [l.split("\t")[2] for l in hdr.split("Variables:")[-1].strip().splitlines()]
    dbl = "double" in re.search(r"Flags:(.*)", hdr).group(1)
    if dbl: arr = np.frombuffer(data, dtype="<f8", count=npts*nv).reshape(npts, nv); t = arr[:,0]; v = arr
    else:
        rec = np.dtype([("t","<f8"),("v","<f4",(nv-1,))]); arr = np.frombuffer(data, dtype=rec, count=npts)
        t = arr["t"]; v = np.column_stack([t, arr["v"]])
    t = np.abs(t)  # LTspice marks compression points with negative time
    cuts = np.where(np.diff(t) < 0)[0] + 1; steps = np.split(np.arange(npts), cuts)
    return names, t, v, steps

names, t, v, steps = read_raw("A1-bias-bootstrap.raw")
col = {n.lower(): k for k, n in enumerate(names)}
def sig(expr, idx):
    e = expr.lower()
    e = re.sub(r"(v\([^)]+\)|i\([^)]+\))", lambda m: f"v[idx,{col[m.group(1)]}]", e)
    return eval(e)
# step order from the .log: Vrail inner loop
labels = ["30 V / 2 mA", "100 V / 2 mA", "30 V / 5 mA", "100 V / 5 mA"]
assert len(steps) == 4, f"expected 4 steps, got {len(steps)}"
print(f"{'step':12s} {'Ipk+ mA':>8s} {'Ipk- mA':>8s} {'win avg':>8s} {'win min':>8s} {'REF-VN min':>11s} {'VP-REF min':>11s} {'VN-OUT@pk+':>11s}")
rows = []
for lab, idx in zip(labels, steps):
    tt = t[idx]; w = idx[tt >= 4e-3]
    il = sig("I(RLOAD)", w); win = sig("V(VP)-V(VN)", w); rv = sig("V(REF)-V(VN)", w); pr = sig("V(VP)-V(REF)", w); no = sig("V(VN)-V(OUT)", w)
    k = np.argmax(il)
    r = (lab, il.max()*1e3, il.min()*1e3, win.mean(), win.min(), rv.min(), pr.min(), no[k])
    rows.append(r); print(f"{lab:12s} {r[1]:8.3f} {r[2]:8.3f} {r[3]:8.2f} {r[4]:8.2f} {r[5]:11.2f} {r[6]:11.2f} {r[7]:11.2f}")

for si, lab in enumerate(labels):
    vr = lab.split(" V")[0]; ia = lab.split("/ ")[1].split(" ")[0]; vcc = float(vr)
    idx = steps[si]; tt = t[idx]; w = idx[(tt >= 4e-3)]; tm = t[w]*1e3
    fig, ax = plt.subplots(3, 1, figsize=(9, 10), sharex=True)
    ax[0].plot(tm, sig("I(RLOAD)", w)*1e3, label="I(RLOAD) [mA]")
    ax[0].plot(tm, sig("V(INPUT)", w), "--", label="V(INPUT)/1k = command [mA]")
    for n in ("OUT", "LOAD", "VP", "VN", "REF"): ax[1].plot(tm, sig(f"V({n})", w), label=f"V({n})")
    ax[1].axhline(vcc, color="k", lw=0.6); ax[1].axhline(-vcc, color="k", lw=0.6)
    ax[2].plot(tm, sig("V(VP)-V(VN)", w), label="VP-VN  (floating window)")
    ax[2].plot(tm, sig("V(REF)-V(VN)", w), label="REF-VN  (U1 low-side headroom)")
    ax[2].plot(tm, sig("V(VP)-V(REF)", w), label="VP-REF  (U1 high-side headroom)")
    ax[0].set_ylabel("mA"); ax[1].set_ylabel("V"); ax[2].set_ylabel("V"); ax[2].set_xlabel("time (ms)")
    ax[0].set_title(f"A1 bias & bootstrap window [L], rails ±{vr} V, command {ia} mA pk, RL = 1 kΩ, 300 Hz")
    for a in ax: a.grid(alpha=.3)
    ax[1].set_ylim(-vcc*1.15, vcc*1.15); ax[2].set_ylim(0, ax[2].get_ylim()[1]*1.3)
    ax[0].legend(fontsize=8, loc="upper right"); ax[1].legend(fontsize=8, ncol=5, loc="upper center"); ax[2].legend(fontsize=8, ncol=3, loc="upper center")
    out = f"A1_{vr}V_{ia}mA.png"; fig.tight_layout(); fig.savefig(out, dpi=130); plt.close(fig); print("wrote", out)
