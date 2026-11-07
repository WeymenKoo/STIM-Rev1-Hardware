#!/usr/bin/env python3
"""JY063 client STIM board — bench rig for a Tektronix TBS1000C (2 channels) when the DHO804 is not there.
Same tests, same prompts, same session_log.csv and ../tests/<ID>/bench/ files as bench_rig.py. Run from this folder.

  python bench_tbs.py check                       # VISA resources, *IDN?, which command forms this TBS firmware takes
  python bench_tbs.py preflight                   # no board: CH1 and CH2 on PROBE COMP (5 V → catches 1X/10X), gen sweep + edge
  python bench_tbs.py a1  --rl <RL1> --onset      # CH1 stays on LOAD; CH2 walks OUT → VP → VN → REF, one capture each
  python bench_tbs.py a2  --rl <RL1>              # same as bench_rig (Fluke 45 does the work, scope unused)
  python bench_tbs.py a5b --rl <RL1> --rl2 <RL2>  # same as bench_rig
  python bench_tbs.py a4  --rl <RL1> --extra      # adds a 20 s channel-gain cal first (CH1 also clipped on INPUT)
  python bench_tbs.py a3  --rl <RL1>              # same captures as bench_rig, but 16 averages instead of single-shot
  python bench_tbs.py a7  --rl <RL1>              # CH1 LOAD, CH2 VCC+ (free channel: shows when the + rail goes)

Options as bench_rig.py, plus  --visa auto|ivi|py  (auto: NI/Tek VISA if installed, else pyvisa-py).

What changes with 2 channels
- A1 needs LOAD, OUT, VP, VN, REF at the same instant. Here CH1 never leaves LOAD and every capture triggers on LOAD
  rising through 0 V, so the captures share a time base. Each CH2 trace is additionally shifted by the LOAD 300 Hz
  phase difference between captures (printed; expect < 1 µs on a 3333 µs period), then VP−VN, REF−VN, VP−REF are
  formed exactly as on the DHO. 4 probe moves per amplitude instead of 1.
- 8 bit (25 counts/div) instead of 12: every capture is averaged 16× and re-scaled until the trace fills > 1/3 of
  the screen without clipping. Even so, 1 count at 1 V/div ≈ 2 % of 2 V: the A1 "±1 %" and A4 "absolute gain ±1 %"
  rows are indicative only. A2 (Fluke 45) is the ±1 % arbiter, as on the sheet.
- TBS channel gain is ±3 % [DS] per channel, so A4 measures CH1/CH2 on the same node first and divides it out.
"""
import argparse, csv, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bench_rig as R          # log / within / EXP / PROBE / outdir / save_csv / sine_fit / overlays / a2 / a5b / a3
import instruments as I        # DG1022, ManualGen, ManualDMM, Fluke45, Korad
try: sys.stdout.reconfigure(errors="replace")
except Exception: pass

ask, banner, log, within, nice = R.ask, R.banner, R.log, R.within, R.nice
NAN = float("nan")

# ------------------------------------------------------------------------------------------------- VISA
_RM = None
def make_rm(backend="auto"):
    """auto: system VISA (NI-VISA / TekVISA) if present, else pyvisa-py. instruments._rm is pointed here so the
    DG1022 opens through the same manager."""
    global _RM
    import pyvisa
    if backend in ("auto", "ivi"):
        try:
            _RM = pyvisa.ResourceManager(); _RM.list_resources(); return _RM
        except Exception as e:
            if backend == "ivi": raise
            print(f"  (no system VISA: {e.__class__.__name__}; using pyvisa-py)")
    _RM = pyvisa.ResourceManager("@py"); return _RM
I._rm = lambda: _RM or make_rm()

def find(verbose=True):
    rm = I._rm(); found = {}
    for r in rm.list_resources():
        if not r.startswith(("USB", "TCPIP")): continue          # never poke serial ports (Korad, Fluke) with *IDN?
        try:
            inst = rm.open_resource(r, timeout=3000)
            inst.read_termination = "\n"; inst.write_termination = "\n"   # DG1022 times out without these
            inst.write("*IDN?"); time.sleep(0.3); idn = inst.read().strip(); inst.close()
        except Exception as e:
            idn = f"(no reply: {e})"
        if verbose: print(f"  {r:60s} {idn}")
        if "TBS1" in idn.upper(): found["scope"] = r
        if "DG1022" in idn or "DG1000" in idn: found["gen"] = r
    return found


# ------------------------------------------------------------------------------------------------- scope
class TBS1000C:
    """Same method names as instruments.DHO804, so bench_rig's a3 / capture() run unchanged.
    channel() keeps the Rigol meaning of `offset` (V; screen centre = −offset) and converts to Tek POSition (div).
    Command forms that differ between TBS firmware generations are tried in order; the first one the scope does not
    flag as a command error (*ESR? bit 5) is remembered. `check` prints which were chosen."""
    AVG = (4, 16, 64, 128)

    def __init__(self, resource):
        self.v = I._rm().open_resource(resource, timeout=15000)
        self.v.read_termination = "\n"; self.v.write_termination = "\n"
        self.v.write("*CLS"); self.v.write("HEADer OFF")
        self.idn = self.v.query("*IDN?").strip()
        self._form = {}; self._pre_prefix = None
        self.scale = {1: 1.0, 2: 1.0}; self.offs = {1: 0.0, 2: 0.0}; self.tb = 1e-3; self.navg = 1
        self.norm_as_avg = None          # A3: average even where bench_rig asks for a plain acquisition
        self.byte_order = "little"       # what this firmware actually sends with DATa:WIDth 2 (see waveform())
        self.w("DATa:ENCdg RIBinary"); self.w("DATa:WIDth 2"); self.w("DATa:STARt 1"); self.w("DATa:STOP 20000")

    def w(self, cmd): self.v.write(cmd); time.sleep(0.02)
    def q(self, cmd): return self.v.query(cmd).strip()

    def accepted(self, cmd):
        self.v.write("*CLS"); self.v.write(cmd)
        try: return not (int(self.q("*ESR?")) & 0x20)
        except Exception: return False

    def wf(self, key, forms, *args):
        """Write the first of `forms` (format strings) the scope accepts; remember the choice under `key`."""
        if key in self._form: self.w(self._form[key].format(*args)); return True
        for form in forms:
            if self.accepted(form.format(*args)): self._form[key] = form; return True
        print(f"  !! scope rejected every form of {key}: {forms}"); return False

    def qsafe(self, cmd, timeout=2500):
        t = self.v.timeout; self.v.timeout = timeout
        try: return self.q(cmd)
        except Exception: self.v.write("*CLS"); return None
        finally: self.v.timeout = t

    # --- setup
    def channel(self, ch, scale, offset=0.0, probe=10, coupling="DC", on=True, bwl=False):
        if ch > 2:
            if on: raise RuntimeError(f"TBS1000C has 2 channels (asked for CH{ch})")
            return
        self.w(f"SELect:CH{ch} {'ON' if on else 'OFF'}")
        if not on: return
        self.w(f"CH{ch}:COUPling {coupling}"); self.w(f"CH{ch}:SCAle {scale:g}")
        got = self.qsafe(f"CH{ch}:SCAle?")
        s = float(got) if got else scale
        self.w(f"CH{ch}:POSition {offset / s:g}")
        self.scale[ch] = s; self.offs[ch] = offset

    def timebase(self, s_per_div, pos=0.0):   # pos ignored: trigger stays where Default Setup put it (centre)
        self.wf("hscale", ["HORizontal:MAIn:SCAle {:g}", "HORizontal:SCAle {:g}"], s_per_div)
        got = self.qsafe("HORizontal:MAIn:SCAle?") or self.qsafe("HORizontal:SCAle?")
        self.tb = float(got) if got else s_per_div

    def acquire(self, mode="NORM", averages=None, mdepth=None):
        if mode != "AVER" and self.norm_as_avg: mode, averages = "AVER", self.norm_as_avg
        if mode == "AVER":
            a = averages or 16; n = 4 if a <= 4 else 16 if a <= 16 else 64
            self.w("ACQuire:MODe AVErage"); self.w(f"ACQuire:NUMAVg {n}"); self.navg = n
        else:
            self.w("ACQuire:MODe SAMple"); self.navg = 1

    def trigger_edge(self, ch, level, slope="POS", sweep="SING"):
        self.w(f"TRIGger:A:EDGE:SOUrce CH{ch}"); self.w("TRIGger:A:EDGE:COUPling DC")
        self.w(f"TRIGger:A:EDGE:SLOpe {'RISe' if slope == 'POS' else 'FALL'}")
        self.wf("tlevel", ["TRIGger:A:LEVel:CH{0} {1:g}", "TRIGger:A:LEVel {1:g}"], ch, level)
        self.w(f"TRIGger:A:MODe {'AUTO' if sweep == 'AUTO' else 'NORMal'}")

    # --- acquisition
    def run(self): self.w("ACQuire:STOPAfter RUNSTop"); self.w("ACQuire:STATE RUN")
    def stop(self): self.w("ACQuire:STATE STOP")
    def arm(self): self.w("ACQuire:STOPAfter SEQuence"); self.w("ACQuire:STATE RUN"); time.sleep(0.1)
    def done(self): return (self.qsafe("ACQuire:STATE?") or "1").strip() in ("0", "STOP", "OFF")

    def wait(self, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.done(): return True
            time.sleep(0.1)
        return False

    def single(self, timeout=30.0):
        self.arm(); return self.wait(timeout)

    def settle(self, seconds):
        """One complete record (all averages) then stopped. Forces a trigger if none came."""
        rec = 12 * self.tb * self.navg
        self.arm()
        if self.wait(max(seconds, rec) + 3): return
        print("  (no trigger: forcing)"); self.w("TRIGger FORCe")
        for _ in range(self.navg): self.wait(12 * self.tb + 2) or self.w("TRIGger FORCe")
        self.wait(rec + 3)

    # --- measurement
    def meas(self, item, ch):
        typ = {"VPP": "PK2pk", "VAVG": "MEAN", "VRMS": "RMS", "FREQ": "FREQuency"}.get(item, item)
        self.wf("msrc", ["MEASUrement:IMMed:SOUrce1 CH{}", "MEASUrement:IMMed:SOUrce CH{}"], ch)
        self.w(f"MEASUrement:IMMed:TYPe {typ}")
        x = self.qsafe("MEASUrement:IMMed:VALue?")
        try: x = float(x); return x if abs(x) < 9e36 else NAN
        except Exception: return NAN

    def _pre(self, field):
        for p in ([self._pre_prefix] if self._pre_prefix else ["WFMOutpre", "WFMPre"]):
            x = self.qsafe(f"{p}:{field}?")
            if x is not None:
                try: self._pre_prefix = p; return float(x)
                except ValueError: pass
        raise RuntimeError(f"waveform preamble {field} not readable")

    def waveform(self, ch, mode="NORM"):
        self.w(f"DATa:SOUrce CH{ch}")
        width = int(float(self.qsafe("DATa:WIDth?") or 1))
        if width == 2:
            # TBS1102C FV v1.29.38 sends the opposite byte order to what WFMOutpre:BYT_Or reports (bench, 2026-11-06).
            # Decode both; the swapped one has the noisy low byte on top, so it is the one with the larger point-to-point jumps.
            be = np.array(self.v.query_binary_values("CURVe?", datatype="h", is_big_endian=True, container=list), float)
            le = np.frombuffer(be.astype(">i2").tobytes(), "<i2").astype(float)
            # FIXED order, no guessing: every verified read on FV v1.29.38 (sample, average, single-shot; position-shift test
            # 2026-11-06) is LSB-first while BYT_Or reports MSB. Guessing by smoothness/zero low byte failed on flat DC.
            # `python bench_tbs.py check` re-verifies this with the position-shift test.
            raw = be if self.byte_order == "big" else le
        else:
            raw = np.array(self.v.query_binary_values("CURVe?", datatype="b", container=list), float)
        ymult, yoff, yzero = self._pre("YMUlt"), self._pre("YOFf"), self._pre("YZEro")
        xinc, xzero = self._pre("XINcr"), self._pre("XZEro")
        try: ptoff = self._pre("PT_Off")
        except RuntimeError: ptoff = 0.0
        if not hasattr(self, "last_raw"): self.last_raw = {}
        self.last_raw[ch] = dict(counts=raw.copy(), YMULT=ymult, YOFF=yoff, YZERO=yzero, XINCR=xinc, XZERO=xzero,
                                 PT_OFF=ptoff, width=width, byte_order=getattr(self, "byte_order", "?"))
        return xzero + (np.arange(len(raw)) - ptoff) * xinc, (raw - yoff) * ymult + yzero

    def waveforms(self, chans, mode="NORM"):
        out = {}
        for c in chans: t, out[c] = self.waveform(c, mode)
        return t, out

    def clipped(self, ch, v): return np.max(np.abs(v + self.offs[ch])) > 3.9 * self.scale[ch]
    def screenshot(self, path): return False

    def selftest(self):
        def att(c):
            g = self.qsafe(f"CH{c}:PRObe:GAIn?")
            try: return f"{1 / float(g):g}X"
            except Exception: return self.qsafe(f"CH{c}:PRObe:ATTENuation?") or "?"
        print("  probe attenuation:", *[f"CH{c} {att(c)}" for c in (1, 2)], "   ← both must say 10X")
        # byte-order self-test: move CH1 by 2 div between two sample-mode acquisitions. Right order: decoded volts unchanged,
        # raw counts shift by ~2*25*256 = 12800. Wrong order: decoded volts jump by 2 div.
        res = []
        for off in (0.0, -2.0):
            self.timebase(1e-3); self.acquire("NORM"); self.channel(1, 1.0, off); self.trigger_edge(1, 0.0, "POS", "AUTO")
            self.run(); time.sleep(1.0); self.stop(); time.sleep(0.2)
            _, w = self.waveforms([1]); res.append((w[1].mean(), self.last_raw[1]["counts"].mean()))
        dv, dc = res[1][0] - res[0][0], res[1][1] - res[0][1]
        ok = abs(dv) < 0.3 and abs(dc) > 5000
        print(f"  byte order {self.byte_order}: CH1 moved 2 div -> decoded shift {dv:+.3f} V, count shift {dc:+.0f}   "
              f"{'OK' if ok else '!! WRONG: set self.byte_order = big in TBS1000C.__init__ and re-run check'}")
        self.channel(1, 1.0, 0.0)
        self.timebase(1e-3); self.trigger_edge(1, 0.0, "POS", "AUTO"); self.channel(1, 1.0); self.channel(2, 1.0)
        print("  hscale form:", self._form.get("hscale"), "  read back", self.tb)
        print("  trig level form:", self._form.get("tlevel"))
        self.acquire("AVER", 16); self.settle(1.0); t, w = self.waveforms([1, 2])
        print(f"  waveform: {len(t)} points, dt {np.median(np.diff(t))*1e9:.1f} ns, preamble {self._pre_prefix}, "
              f"CH1 mean {w[1].mean():+.3f} V, CH2 mean {w[2].mean():+.3f} V, byte order {getattr(self, 'byte_order', '?')}")
        for c in (1, 2):
            m = self.meas("VAVG", c)
            ok = np.isfinite(m) and abs(w[c].mean() - m) < 0.05 * self.scale[c]
            print(f"  CH{c} decode check: decoded mean {w[c].mean():+.4f} V vs scope MEAN {m:+.4f} V   {'OK' if ok else '!! MISMATCH'}")
        print("  CH1 Vpp (scope's own):", self.meas("VPP", 1), "  form:", self._form.get("msrc"))


# ------------------------------------------------------------------------------------------------- setup
def connect(a, need_gen=True):
    make_rm(a.visa); found = find(verbose=False)
    sc = a.scope or found.get("scope")
    if not sc: sys.exit("no TBS1xxxC found. `python bench_tbs.py check`, or pass --scope <VISA resource>")
    scope = TBS1000C(sc); print("  scope:", scope.idn)
    if a.cmd == "a3": scope.norm_as_avg = 16
    gen = None
    if need_gen:
        if a.gen == "manual": gen = I.ManualGen()
        else:
            g = a.gen_res or found.get("gen"); gen = I.DG1022(g) if g else I.ManualGen()
        print("  gen:  ", gen.describe())
    dmm = I.Fluke45(a.dmm_port) if a.dmm_port else I.ManualDMM("Fluke 45")
    print("  dmm:  ", dmm.describe())
    return scope, gen, dmm
R.connect = connect      # bench_rig's a2 / a5b / a3 now open the TBS


class CH2:
    """Where the CH2 probe is. Every move is a prompt; orders a list so the walk starts where the probe already is."""
    def __init__(self, at): self.at = at
    def to(self, node):
        if node != self.at: ask(f"move CH2 probe  {self.at}  →  {node}   ({R.PROBE[node]})"); self.at = node
    def order(self, nodes):
        if self.at not in nodes: return list(nodes)
        k = nodes.index(self.at); return nodes[k:] + nodes[:k]


def grab(scope, avg=16, tries=6):
    """CH1+CH2, averaged. Re-capture at another V/div until neither channel clips and each spans > 1/3 screen."""
    for _ in range(tries):
        scope.acquire("AVER", avg); scope.settle(1.0); t, w = scope.waveforms([1, 2]); again = False
        for ch in (1, 2):
            s = scope.scale[ch]; pk = np.max(np.abs(w[ch] + scope.offs[ch]))
            new = nice(s * 5) if pk > 3.9 * s else max(nice(pk / 3.2), 0.02) if pk < 1.3 * s else s
            if new != s: scope.channel(ch, new, 0.0); again = True
        if not again: return t, w
    print("  !! could not find a V/div without clipping — check the probe is on the right node")
    return t, w


def move(scope, p2, node):
    """CH2 to `node`; restart CH2 at 5 V/div so grab() never starts clipped on a node far from the last one."""
    p2.to(node); scope.channel(2, 5.0, 0.0)


def align(t, load_ref, tp, load_p, sig_p, f=300.0):
    """Put a capture on the reference capture's time base using the phase of LOAD (CH1 in both). Returns (sig, shift_s)."""
    _, ph_r, _ = R.sine_fit(t, load_ref, f); _, ph_p, _ = R.sine_fit(tp, load_p, f)
    dt = ((ph_r - ph_p + 180) % 360 - 180) / 360 / f
    return np.interp(t + dt, tp, sig_p), dt


# ------------------------------------------------------------------------------------------------- CHECK / PREFLIGHT
def cmd_check(a):
    make_rm(a.visa); banner("VISA resources"); f = find(verbose=True)
    if "scope" in f:
        banner("TBS1000C command forms"); TBS1000C(f["scope"]).selftest()
    else:
        print("  no TBS found. Windows: install TekVISA/NI-VISA, or Zadig → WinUSB on the scope + pip install libusb-package")


def cmd_preflight(a):
    banner("PREFLIGHT (TBS) — no board. Both probes on PROBE COMP (≈5 V, 1 kHz) in turn, then generator BNC → CH1")
    scope, gen, _ = connect(a); d = R.outdir("PRE")
    for ch in (1, 2):
        ask(f"CH{ch} probe on PROBE COMP (tip on 5 V tab, clip on ground tab), probe switch 10X, CH{ch} menu Probe 10X")
        scope.channel(1, 2.0); scope.channel(2, 2.0); scope.timebase(500e-6); scope.trigger_edge(ch, 2.5, "POS", "AUTO")
        scope.acquire("AVER", 16); scope.settle(1.0); t, w = scope.waveforms([ch])
        dec = np.percentile(w[ch], 99) - np.percentile(w[ch], 1); meas = scope.meas("VPP", ch)
        print(f"  CH{ch}: decoded {dec:.3f} V (1–99 %)   scope Pk-Pk {meas:.3f} V   {len(t)} points")
        if not 4.0 < dec < 6.0: print(f"  !! expected ≈5 V: probe switch and CH{ch} probe menu are not both 10X — fix before the session")
        elif np.isfinite(meas) and not 0.9 < dec / meas < 1.1: print("  !! decode disagrees with the scope's own Pk-Pk — run `check`, send me the output")
        else: print("  OK")
        R.save_csv(os.path.join(d, f"preflight_tbs_probecomp_ch{ch}.csv"), t, {f"CH{ch}": w[ch]})

    ask("generator output → CH1 directly (BNC tee or probe on the BNC centre). Enter to sweep")
    scope.channel(1, 1.0); gen.on(); rows = []
    for f in [1, 10, 100, 300, 1e3, 10e3, 100e3]:
        gen.sine(f, 2.0); tb = nice(4 / f / 10); scope.timebase(tb); scope.trigger_edge(1, 0.0, "POS", "AUTO")
        t, w = R.capture(scope, [1], max(1.0, 12 * tb), "NORM" if f < 100 else "AVER", 16)
        amp, ph, off = R.sine_fit(t, w[1], f); rows.append((f, amp, scope.meas("VPP", 1)))
        print(f"  {f:>8g} Hz  fit {amp:.4f} Vpk  scope Vpp {rows[-1][2]:.4f}")
    ref = rows[1][1]
    with open(os.path.join(d, "preflight_tbs_gen_flatness.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["f_Hz", "Vpk_fit", "Vpp_scope", "dB_vs_10Hz"])
        for f, amp, vpp in rows: cw.writerow([f, amp, vpp, 20 * np.log10(amp / ref)])
    gen.square(500, 0, 2); scope.timebase(200e-9); scope.channel(1, 0.5, -1.0); scope.trigger_edge(1, 1.0, "POS", "SING"); scope.acquire("NORM")
    if scope.single(10):
        t, w = scope.waveforms([1]); print(f"  generator edge 10–90 %: {R.edge_time(t, w[1])*1e9:.0f} ns  ← write on the A3 sheet (TBS rise time ~3.5 ns at 100 MHz adds a little)")
    gen.zero(); gen.off(); print("  preflight done.")


# ------------------------------------------------------------------------------------------------- A1
A1_NODES = ["OUT", "VP (V+)", "VN (V-)", "REF"]

def cmd_a1(a):
    banner("A1 (TBS, 2 ch) — CH1 on LOAD the whole test; CH2 walks OUT → VP → VN → REF. All grounds on J2")
    R.probes("LOAD", "OUT", "VP (V+)", "VN (V-)", "REF", "INPUT", "VCC+", "VCC-")
    scope, gen, dmm = connect(a); d = R.outdir("A1"); RL = a.rl; E = R.EXP["A1"]; T = a.tag; p2 = CH2("OUT")
    gen.zero(); gen.off()
    # ---- 1a idle
    banner("1a  power-up, no signal (generator off).  Fluke 45 in series with VCC+ (mA), BM235 in series with VCC− (mA)")
    ask("CH1 probe on LOAD, CH2 probe on OUT. Rails up (both together), generator OFF")
    ip = dmm.read("rail current +  (Fluke 45 in series with VCC+)", "mA"); im = I.ManualDMM("BM235").read("rail current −  (BM235 in series with VCC−)", "mA")
    log("A1", "1a rail current + (mA)", ip, "3.5–5", "> 15 → OFF", ""); log("A1", "1a rail current − (mA)", im, "3.5–5", "", "")
    if max(abs(ip), abs(im)) > 15: sys.exit("  !! rail current > 15 mA: POWER OFF. Do not debug live.")
    vccp = dmm.read("VCC+ vs GND (J3 pin 1)"); vccm = dmm.read("VCC− vs GND (J3 pin 3)")
    log("A1", "1a VCC+ / VCC− (V)", f"{vccp:+.2f} / {vccm:+.2f}", f"+{T[:-1]} / -{T[:-1]}")
    scope.channel(1, 1); scope.channel(2, 2); scope.timebase(1e-3); scope.trigger_edge(1, 0.0, "POS", "AUTO")
    m = {}
    for node in p2.order(A1_NODES[:3]):
        move(scope, p2, node); t, w = grab(scope); m[node] = w[2].mean(); m.setdefault("LOAD", w[1].mean())
    vp, vn, out, load = m["VP (V+)"], m["VN (V-)"], m["OUT"], m["LOAD"]
    log("A1", "1a VP vs GND (V, scope mean)", round(vp, 3), E["VP_idle"], "±1 V", within(vp, E["VP_idle"], ("abs", 1)))
    log("A1", "1a VN vs GND (V)", round(vn, 3), E["VN_idle"], "±1 V", within(vn, E["VN_idle"], ("abs", 1)))
    log("A1", "1a OUT / LOAD vs GND (V)", f"{out:+.3f} / {load:+.3f}", "≈0 / 0")
    log("A1", "1a window VP−VN (V)", round(vp - vn, 3), E["window"], "±2 V", within(vp - vn, E["window"], ("abs", 2)))
    qb2 = dmm.read("Q2 base (R2/R3 junction) vs GND"); qb1 = dmm.read("Q1 base (R4/R5 junction) vs GND")
    log("A1", "1a Q2 Vbase − V+ (V)  [NPN emitter follower → ≈ +0.65]", round(qb2 - vp, 3), "+0.65", "record")
    log("A1", "1a Q1 Vbase − V− (V)  [PNP emitter follower → ≈ −0.65]", round(qb1 - vn, 3), "−0.65", "record")
    scope.channel(1, 0.05, 0, coupling="AC"); scope.timebase(1e-6); scope.trigger_edge(1, 0.0, "POS", "AUTO")
    scope.acquire("NORM"); scope.settle(1.0); t, w = scope.waveforms([1]); rip = w[1].max() - w[1].min()
    sp = np.abs(np.fft.rfft(w[1] - w[1].mean())); fr = np.fft.rfftfreq(len(w[1]), np.median(np.diff(t))); fdom = fr[np.argmax(sp[1:]) + 1]
    log("A1", "1a LOAD ripple Vpp (mV) / dominant f (MHz)", f"{rip*1e3:.1f} / {fdom/1e6:.2f}", "none [L]; TI models ~1 MHz", "record")
    R.save_csv(os.path.join(d, f"A1_{T}_idle_ripple_bench.csv"), t, {"LOAD_AC": w[1]})
    scope.channel(1, 1, coupling="DC")
    # ---- 1b / 1c
    for amp in a.amp:
        sub = "1b" if amp <= 2.5 else "1c"
        banner(f"{sub}  {amp:g} Vpk 300 Hz sine (I = {amp:g} mA command) — 4 captures, CH2 moves between them")
        gen.sine(300, amp); gen.on(); time.sleep(0.5)
        scope.timebase(1e-3); scope.trigger_edge(1, 0.0, "POS", "NORM"); caps = {}
        for node in p2.order(A1_NODES):
            move(scope, p2, node); caps[node] = grab(scope); print(f"    captured CH2 = {node}")
        ref = next(iter(caps)); t, wr = caps[ref]; L = wr[1]; sig = {ref: wr[2]}; loads = [L]; dmax = 0.0
        for node, (tp, wp) in caps.items():
            if node == ref: continue
            sig[node], dt = align(t, L, tp, wp[1], wp[2]); loads.append(align(t, L, tp, wp[1], wp[1])[0]); dmax = max(dmax, abs(dt))
        print(f"  captures aligned on LOAD phase: largest shift {dmax*1e6:.1f} µs of a 3333 µs period")
        load = np.mean(loads, axis=0)
        w = {1: load, 2: sig["OUT"], 3: sig["VP (V+)"], 4: sig["VN (V-)"]}
        w2 = {1: load, 2: sig["REF"], 3: sig["VP (V+)"], 4: sig["VN (V-)"]}
        il = w[1] / RL * 1e3; k = np.argmax(il); kn = np.argmin(il)
        name = f"A1_{T}_{amp:g}mA_bench"
        R.save_csv(os.path.join(d, name + ".csv"), t, {"LOAD": w[1], "OUT": w[2], "VP": w[3], "VN": w[4]})
        R.save_csv(os.path.join(d, name + "_ref.csv"), t, {"LOAD": w2[1], "REF": w2[2], "VP": w2[3], "VN": w2[4]})
        refvn = w2[2] - w2[4]; vpref = w2[3] - w2[2]
        if amp <= 2.5:
            log("A1", "1b I_load pk+ / pk− (mA)  [8-bit: indicative, A2 decides ±1 %]", f"{il[k]:.4f} / {il[kn]:.4f}", "2.000 / −2.000", "±1 %", within(il[k], amp, ("pct", 1)) and within(il[kn], -amp, ("pct", 1)))
            log("A1", "1b OUT at I pk+ (V)", round(w[2][k], 3), E["OUT_pk"], "±0.2 V", within(w[2][k], E["OUT_pk"], ("abs", 0.2)))
            log("A1", "1b VP / VN at I pk+ (V)", f"{w[3][k]:+.3f} / {w[4][k]:+.3f}", "+6.0 / +1.1", "±1 V", within(w[3][k], E["VP_pk"], ("abs", 1)) and within(w[4][k], E["VN_pk"], ("abs", 1)))
            win = (w[3] - w[4]).mean(); log("A1", "1b window VP−VN avg (V)", round(win, 3), E["window"], "±2 V", within(win, E["window"], ("abs", 2)))
            log("A1", "1b REF−VN min (V)   ← validates the model", round(refvn.min(), 3), E["REFVN_min"], "record")
            log("A1", "1b VP−REF min (V)", round(vpref.min(), 3), E["VPREF_min"], "record")
        else:
            top = np.percentile(il, 97); bot = np.percentile(il, 3); flat_hi = np.mean(il > 0.98 * top); flat_lo = np.mean(il < 0.98 * bot)
            log("A1", "1c I_load plateau + / − (mA)", f"{top:.3f} / {bot:.3f}", "+4.01 / −3.38", "±0.5 mA", within(top, E["I_plateau_pos"], ("abs", .5)) and within(bot, E["I_plateau_neg"], ("abs", .5)))
            log("A1", "1c fraction of period on the plateau (+ / −)  [flat sine would be ~0.06]", f"{flat_hi:.2f} / {flat_lo:.2f}", "> 0.1 if clipping", "record")
            win = (w[3] - w[4]).mean(); log("A1", "1c window VP−VN avg (V)", round(win, 3), E["window5"], "±2 V", within(win, E["window5"], ("abs", 2)))
            log("A1", "1c REF−VN during the + plateau (V)", round(refvn[k], 3), 0.20, "record"); log("A1", "1c VP−REF during the − plateau (V)", round(vpref[kn], 3), 1.00, "record")
        ipr = dmm.read("rail current + (mA, Fluke 45)", "mA"); imr = I.ManualDMM("BM235").read("rail current − (mA, BM235)", "mA")
        ex = E["Irail"] if amp <= 2.5 else E["Irail5"]
        log("A1", f"{sub} rail current + / − (mA)", f"{ipr:.2f} / {imr:.2f}", f"{ex} / {ex}", "±20 %", within(ipr, ex, ("pct", 20)) and within(imr, ex, ("pct", 20)))
        R.overlay_a1(d, name, amp, t, w, t, w2, RL, T)
    # ---- 1d onset: run twice so 1 V/div covers each peak (pk+ with the trace shifted down, then pk−)
    if a.onset:
        banner("1d  plateau onset: 2.0 → 4.0 mA in 0.25 mA steps, swept twice (pk+ then pk−), CH1 only")
        steps = np.arange(2.0, 4.01, 0.25); rows = {s: [s, NAN, NAN] for s in steps}
        scope.timebase(1e-3); scope.trigger_edge(1, 0.0, "POS", "NORM")
        for col, side in ((1, +1), (2, -1)):
            scope.channel(1, 1.0, -3.0 * side)         # screen −1…+7 V, then −7…+1 V
            for s in steps:
                gen.sine(300, s); scope.acquire("AVER", 16); scope.settle(1.0); _, w = scope.waveforms([1]); il = w[1] / RL * 1e3
                rows[s][col] = il.max() if side > 0 else il.min(); print(f"    {s:.2f} mA cmd → pk{'+' if side > 0 else '−'} {rows[s][col]:.3f}")
        scope.channel(1, 1.0, 0.0)
        with open(os.path.join(d, f"A1_{T}_onset_bench.csv"), "w", newline="") as fh:
            cw = csv.writer(fh); cw.writerow(["cmd_mA", "Ipk_pos_mA", "Ipk_neg_mA"]); cw.writerows(rows.values())
        r = np.array(list(rows.values()))
        on_p = r[np.argmax(r[:, 1] < 0.98 * r[:, 0]), 0] if (r[:, 1] < 0.98 * r[:, 0]).any() else NAN
        on_n = r[np.argmax(-r[:, 2] < 0.98 * r[:, 0]), 0] if (-r[:, 2] < 0.98 * r[:, 0]).any() else NAN
        log("A1", "1d sourcing onset (mA cmd where pk+ < 98 %)", on_p, "~4.0", "record"); log("A1", "1d sinking onset (mA)", on_n, "~3.4", "record")
    gen.zero(); gen.off()
    # ---- 1e rail sweep
    if a.rails:
        banner("1e  window vs rail: generator OFF. Ramp BOTH rails together to each value. CH2 walks VP → VN")
        print("  model [L]: window ≈ 0.16·(V+ − V−)/2 ... 4.97 V at ±30, ~8.2 V at ±50. INA149 abs max ±18 V = 36 V window.")
        for vr in a.rails:
            ask(f"rails at ±{vr:g} V (both), generator OFF, rail currents < 15 mA")
            scope.trigger_edge(1, 0.0, "POS", "AUTO"); m = {}
            for node in p2.order(["VP (V+)", "VN (V-)"]): move(scope, p2, node); m[node] = grab(scope)[1][2].mean()
            ip = dmm.read("rail current + (mA)", "mA"); vp, vn = m["VP (V+)"], m["VN (V-)"]
            log("A1", f"1e ±{vr:g} V: VP / VN / window (V), I+ (mA)", f"{vp:+.2f} / {vn:+.2f} / {vp-vn:.2f}, {ip:.1f}", f"window ~{0.163*vr+0.1:.1f} [L scaling]", "record")
            if vp - vn > 30: print("  !! window above 30 V — INA149 abs max is 36 V. Stop here."); break
            gen.sine(300, 2.0); gen.on(); scope.trigger_edge(1, 0.0, "POS", "NORM"); t, w = grab(scope); il = w[1] / RL * 1e3
            log("A1", f"1e ±{vr:g} V: I pk+ / pk− at 2 mA (mA)", f"{il.max():.4f} / {il.min():.4f}", "2.000 / −2.000", "±1 %", within(il.max(), 2, ("pct", 1)) and within(il.min(), -2, ("pct", 1)))
            R.save_csv(os.path.join(d, f"A1_{vr:g}V_2mA_bench.csv"), t, {"LOAD": w[1]}); gen.zero(); gen.off()
    banner("DECISION after A1 (circle on the sheet)")
    print("  window within ±2 V and 2 mA within ~1 % (TBS: confirm the 1 % in A2)  → run A2…A7 at 2 mA as printed\n"
          "  window OK, 2 mA a few % low → run at 1 mA (halve commands: --cmd-scale 0.5)\n"
          "  window off by > 2 V → check DPAK markings; stop, fix the model first")


# ------------------------------------------------------------------------------------------------- A4
def cmd_a4(a):
    banner("A4 (TBS) — CH1 LOAD, CH2 INPUT. First 20 s: CH1 ALSO on INPUT to measure CH1/CH2 gain (±3 % each [DS])")
    R.probes("LOAD", "INPUT"); scope, gen, dmm = connect(a); d = R.outdir("A4"); RL = a.rl; T = a.tag; amp = 2.0 * a.cmd_scale
    freqs = [1, 10, 100, 300, 1e3, 10e3] + ([3, 30, 3e3, 30e3, 100e3] if a.extra else [])
    s = nice(amp * 1.15 / 3.5); scope.channel(1, s); scope.channel(2, s)      # same V/div for cal and sweep
    gen.sine(1e3, amp); gen.on(); scope.timebase(nice(4 / 1e3 / 10)); scope.trigger_edge(2, 0.0, "POS", "AUTO")
    ask("CAL: clip the CH1 probe on INPUT too (J4 centre, next to CH2)")
    k = []
    for _ in range(3):
        t, w = R.capture(scope, [1, 2], 1.0, "AVER", 16); k.append(R.sine_fit(t, w[1], 1e3)[0] / R.sine_fit(t, w[2], 1e3)[0])
    kc = float(np.mean(k)); log("A4", "channel gain CH1/CH2, both on INPUT (divided out below)", round(kc, 4), "1.000", "±6 % worst [DS]", "record")
    ask("CH1 probe back on LOAD")
    rows = []
    for f in sorted(freqs):
        gen.sine(f, amp); tb = nice(4 / f / 10); scope.timebase(tb); scope.trigger_edge(2, 0.0, "POS", "AUTO")
        t, w = R.capture(scope, [1, 2], max(1.0, 12 * tb), "NORM" if f < 100 else "AVER", 16)
        al, pl, _ = R.sine_fit(t, w[1], f); ai, pi, _ = R.sine_fit(t, w[2], f)
        g = (al / kc / RL * 1e3) / ai; ph = (pl - pi + 180) % 360 - 180
        rows.append((f, ai, al / kc, g, ph, scope.meas("VPP", 1))); print(f"  {f:>8g} Hz  INPUT {ai:.4f} Vpk  LOAD {al/kc:.4f} Vpk  {g:.4f} mA/V  phase {ph:+.2f}°")
        R.save_csv(os.path.join(d, f"A4_{T}_{f:g}Hz_bench.csv"), t, {"LOAD": w[1], "INPUT": w[2]})
    gen.zero(); gen.off()
    ref = [r for r in rows if r[0] == 10][0][3]
    with open(os.path.join(d, f"A4_{T}_bench.csv"), "w", newline="") as fh:
        cw = csv.writer(fh); cw.writerow(["f_Hz", "Vin_pk", "Vload_pk_calibrated", "mA_per_V", "phase_deg", "Vpp_scope", "dB_vs_10Hz"])
        for r in rows:
            db = 20 * np.log10(r[3] / ref); cw.writerow(list(r) + [db])
            if r[0] in R.EXP["A4"]: log("A4", f"{r[0]:g} Hz: dB vs 10 Hz (phase {r[4]:+.2f}°)", round(db, 3), R.EXP["A4"][r[0]], "±0.5 dB", abs(db - R.EXP["A4"][r[0]]) <= 0.5)
            else: log("A4", f"{r[0]:g} Hz (extra): dB vs 10 Hz", round(db, 3), "", "record")
    log("A4", "absolute gain at 10 Hz (mA/V, after CH1/CH2 cal)", round(ref, 4), 1.000, "±1 %", within(ref, 1, ("pct", 1)))
    import matplotlib.pyplot as plt
    f, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True); Rr = np.array(rows)
    ax[0].semilogx(Rr[:, 0], 20 * np.log10(Rr[:, 3] / ref), "o-", label="[B] TBS"); ax[1].semilogx(Rr[:, 0], Rr[:, 4], "o-")
    if R.ltraw and T == "30V":
        try:
            r = R.ltraw.Raw(os.path.join(R.TESTS, "A4-frequency-response", "A4-frequency-response.raw")); idx = r.win(0); fr = r.x[idx]; h = r.sig("I(RLOAD)", idx) * 1e3
            mm = fr <= 2e5; ax[0].semilogx(fr[mm], 20 * np.log10(np.abs(h[mm])), "k--", lw=0.8, label="[L]"); ax[1].semilogx(fr[mm], np.degrees(np.angle(h[mm])), "k--", lw=0.8)
        except Exception as e: print("  (sim overlay skipped:", e, ")")
    ax[0].axhspan(-0.5, 0.5, color="g", alpha=.1); ax[0].set_ylabel("dB vs 10 Hz"); ax[1].set_ylabel("phase °"); ax[1].set_xlabel("Hz"); ax[0].legend()
    ax[0].set_title(f"A4 {T}, {amp:g} mA pk, RL={RL:.0f} Ω, CH1/CH2 cal {kc:.4f}")
    for x in ax: x.grid(alpha=.3, which="both")
    f.tight_layout(); f.savefig(os.path.join(d, f"A4_{T}_bench.png"), dpi=130); plt.close(f)


# ------------------------------------------------------------------------------------------------- A7
def cmd_a7(a):
    banner("A7 (TBS) — single-rail loss, SEQ 2 and 3 only, 50 mA limits. CH1 LOAD, CH2 VCC+ (F1 board side), 10 ms/div")
    R.probes("LOAD", "VCC+"); scope, gen, dmm = connect(a); d = R.outdir("A7"); RL = a.rl; T = a.tag; E = R.EXP["A7"]; v = 2.0 * a.cmd_scale
    korad = I.Korad(a.korad) if a.korad else None
    if korad: print("  Korad is the + rail: its (−) on GND/J2 ONLY. Scripted OUT0/OUT1.")
    ask("CH1 on LOAD, CH2 on VCC+ (F1 board side / J3 pin 1)")
    scope.channel(1, 2, 0); scope.channel(2, 10, 0); scope.timebase(10e-3); scope.acquire("NORM")
    gen.dc(v); gen.on(); time.sleep(0.5)

    def shot(trig_level, slope, prompt, action, timeout=15):
        scope.trigger_edge(1, trig_level, slope, "SING"); scope.arm(); time.sleep(0.5)
        action() if action else ask(prompt)
        if not scope.wait(timeout): print("  !! no trigger"); return None
        t, w = scope.waveforms([1, 2]); return t, w[1] / RL * 1e3, w[2]

    r = shot(v * 0.5, "NEG", "SEQ 2: switch the + rail output OFF now (Xantrex output 1 button)", korad.off if korad else None)
    if r:
        t, il, vcc = r; R.save_csv(os.path.join(d, f"A7_{T}_seq2_drop_bench.csv"), t, {"I_mA": il, "VCCp": vcc})
        cont = il[t > t[-1] - 0.3 * (t[-1] - t[0])].mean(); pk = il[np.argmax(np.abs(il))]
        log("A7", "SEQ 2: I_load after + rail lost, continuous (mA)", round(cont, 3), E["I_cont"], "±50 %", within(cont, E["I_cont"], ("pct", 50)))
        log("A7", "SEQ 2: transient peak during the drop (mA)", round(pk, 3), E["I_peak"], "record")
    r = shot(0.0, "POS", "SEQ 2: switch the + rail output back ON", korad.on if korad else None)
    if r:
        t, il, vcc = r; R.save_csv(os.path.join(d, f"A7_{T}_seq2_restore_bench.csv"), t, {"I_mA": il, "VCCp": vcc})
        fin = il[t > t[-1] - 0.3 * (t[-1] - t[0])].mean()
        log("A7", "SEQ 2: I_load after + rail restored (mA)", round(fin, 4), E["I_restored"] * a.cmd_scale, "±1 %", within(fin, v, ("pct", 1)))
        log("A7", "SEQ 2: peak during restore (mA)", round(il[np.argmax(np.abs(il))], 3), "", "record")
    ask("SEQ 3: switch BOTH rail outputs OFF (together). Generator stays at 2 V DC")
    r = shot(v * 0.5, "POS", "press both output buttons ON together now", None, 20)
    if r:
        t, il, vcc = r; R.save_csv(os.path.join(d, f"A7_{T}_seq3_bench.csv"), t, {"I_mA": il, "VCCp": vcc})
        log("A7", "SEQ 3: peak during simultaneous enable (mA)", round(il[np.argmax(np.abs(il))], 3), E["I_seq3_peak"], "< 3 mA", np.abs(il).max() < 3)
    gen.zero(); gen.off()


# ------------------------------------------------------------------------------------------------- main
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["check", "preflight", "a1", "a2", "a5b", "a4", "a3", "a7"])
    p.add_argument("--rl", type=float, default=1000.0, help="measured RL1 (Ω)"); p.add_argument("--rl2", type=float, default=2200.0)
    p.add_argument("--tag", default="30V"); p.add_argument("--scope"); p.add_argument("--gen", default="auto", help="auto | manual"); p.add_argument("--gen-res")
    p.add_argument("--dmm-port"); p.add_argument("--korad"); p.add_argument("--cmd-scale", type=float, default=1.0, help="0.5 if A1 says run at 1 mA")
    p.add_argument("--amp", type=float, nargs="+", default=[2, 5]); p.add_argument("--onset", action="store_true"); p.add_argument("--rails", type=float, nargs="*")
    p.add_argument("--extra", action="store_true", help="A4: add 3, 30, 3k, 30k, 100k Hz")
    p.add_argument("--visa", default="auto", choices=["auto", "ivi", "py"])
    a = p.parse_args()
    if a.cmd in ("a2", "a5b", "a3"): getattr(R, "cmd_" + a.cmd)(a)
    else: globals()["cmd_" + a.cmd](a)

if __name__ == "__main__": main()
