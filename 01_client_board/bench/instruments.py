"""Instrument wrappers for the JY063 client-board bench session.

Scope      Rigol DHO804 (USB or LAN, pyvisa).           Required.
Gen        Rigol DG1022 at the lab bench (USB, pyvisa)  or  ManualGen (prints what to dial on the FG085/DG1022).
DMM        ManualDMM (you type what the Fluke 45 / BM235 shows)  or  Fluke45 over RS-232 if you have an adapter.
Korad      KA3005P over USB-serial (optional, scripted +rail drop for A7 only).

Every SCPI string here is from the Rigol DHO800 / DG1022 programming guides, but the DHO800 waveform transfer
has firmware quirks: run `python3 bench_rig.py preflight` with the probe on the scope's probe-comp output
before the board is powered. preflight compares the decoded waveform against the scope's own VPP measurement.
"""
import time, sys, struct
import numpy as np

try:
    import pyvisa
except ImportError:
    pyvisa = None


def _rm():
    if pyvisa is None:
        sys.exit("pyvisa missing: pip install pyvisa pyvisa-py pyusb   (macOS also: brew install libusb)")
    return pyvisa.ResourceManager("@py")


def find_instruments(verbose=True):
    """Open every VISA resource, read *IDN?, return {'scope': res, 'gen': res} by name match."""
    rm = _rm(); found = {}
    for r in rm.list_resources():
        try:
            inst = rm.open_resource(r, timeout=3000)
            idn = inst.query("*IDN?").strip(); inst.close()
        except Exception as e:  # noqa
            idn = f"(no reply: {e})"
        if verbose: print(f"  {r:60s} {idn}")
        if "DHO8" in idn: found["scope"] = r
        if "DG1022" in idn or "DG1000" in idn: found["gen"] = r
    return found


# ----------------------------------------------------------------------------------------------------- scope
class DHO804:
    """Minimal DHO800 driver. Waveforms are read in NORMal mode (the screen record, 1000 pts) in WORD format."""
    def __init__(self, resource):
        rm = _rm()
        self.v = rm.open_resource(resource, timeout=15000, chunk_size=1 << 20)
        self.v.read_termination = "\n"; self.v.write_termination = "\n"
        self.idn = self.v.query("*IDN?").strip()

    def w(self, cmd): self.v.write(cmd); time.sleep(0.03)
    def q(self, cmd): return self.v.query(cmd).strip()

    # --- setup
    def channel(self, ch, scale, offset=0.0, probe=10, coupling="DC", on=True, bwl=False):
        self.w(f":CHAN{ch}:DISP {'ON' if on else 'OFF'}")
        if not on: return
        self.w(f":CHAN{ch}:PROB {probe}")
        self.w(f":CHAN{ch}:COUP {coupling}")
        self.w(f":CHAN{ch}:BWL {'20M' if bwl else 'OFF'}")
        self.w(f":CHAN{ch}:SCAL {scale}")
        self.w(f":CHAN{ch}:OFFS {offset}")

    def timebase(self, s_per_div, pos=0.0):
        self.w(f":TIM:MAIN:SCAL {s_per_div}"); self.w(f":TIM:MAIN:OFFS {pos}")

    def acquire(self, mode="NORM", averages=None, mdepth="10k"):
        """mode NORM | AVER | HRES. averages used for AVER."""
        self.w(f":ACQ:MDEP {mdepth}")
        if mode == "AVER":
            self.w(":ACQ:TYPE AVER"); self.w(f":ACQ:AVER {averages or 16}")
        else:
            self.w(f":ACQ:TYPE {'HRES' if mode == 'HRES' else 'NORM'}")

    def trigger_edge(self, ch, level, slope="POS", sweep="SING"):
        self.w(":TRIG:MODE EDGE"); self.w(f":TRIG:EDGE:SOUR CHAN{ch}")
        self.w(f":TRIG:EDGE:SLOP {slope}"); self.w(f":TRIG:EDGE:LEV {level}")
        self.w(f":TRIG:SWE {'SING' if sweep == 'SING' else 'AUTO' if sweep == 'AUTO' else 'NORM'}")

    def run(self): self.w(":RUN")
    def stop(self): self.w(":STOP")

    def single(self, timeout=30.0):
        """Arm single-shot and wait until the scope reports STOP (triggered + acquired). Returns True on trigger."""
        self.w(":SING"); t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.q(":TRIG:STAT?")
            if st.startswith("STOP"): return True
            time.sleep(0.05)
        return False

    def settle(self, seconds):
        """Let the display/averaging settle, then STOP so the record is frozen for readout."""
        self.run(); time.sleep(seconds); self.stop(); time.sleep(0.2)

    # --- measurements (scope's own numbers; used as sanity checks on the decoded waveform)
    def meas(self, item, ch):
        try:
            x = float(self.q(f":MEAS:ITEM? {item},CHAN{ch}"))
            return x if abs(x) < 9e36 else float("nan")
        except Exception:
            return float("nan")

    # --- waveform
    def waveform(self, ch, mode="NORM"):
        """Return (t, v) numpy arrays for channel ch from the current (stopped) acquisition."""
        self.w(f":WAV:SOUR CHAN{ch}"); self.w(f":WAV:MODE {mode}"); self.w(f":WAV:FORM WORD")
        pre = self.q(":WAV:PRE?").split(",")
        # format,type,points,count,xinc,xorig,xref,yinc,yorig,yref
        npts = int(pre[2]); xinc, xorig, xref = float(pre[4]), float(pre[5]), float(pre[6])
        yinc, yorig, yref = float(pre[7]), float(pre[8]), float(pre[9])
        raw = np.empty(0, dtype="<u2"); start = 1; CH = 250_000
        while start <= npts:
            stop = min(npts, start + CH - 1)
            self.w(f":WAV:STAR {start}"); self.w(f":WAV:STOP {stop}")
            self.v.write(":WAV:DATA?"); blk = self.v.read_raw()
            # TMC block header: '#' + N + N digits of length
            if blk[:1] != b"#": raise RuntimeError(f"bad waveform header: {blk[:20]!r}")
            n = int(blk[1:2]); ln = int(blk[2:2 + n]); data = blk[2 + n:2 + n + ln]
            raw = np.concatenate([raw, np.frombuffer(data, dtype="<u2")])
            start = stop + 1
        v = (raw.astype(float) - yorig - yref) * yinc
        t = xorig + np.arange(len(v)) * xinc
        return t, v

    def waveforms(self, chans, mode="NORM"):
        out = {}
        for c in chans:
            t, v = self.waveform(c, mode); out[c] = v
        return t, out

    def screenshot(self, path):
        """PNG of the display, for the record."""
        try:
            self.v.write(":DISP:DATA? PNG"); blk = self.v.read_raw()
            n = int(blk[1:2]); ln = int(blk[2:2 + n]); open(path, "wb").write(blk[2 + n:2 + n + ln]); return True
        except Exception as e:
            print("  (screenshot failed:", e, ")"); return False


# ------------------------------------------------------------------------------------------------- generator
class DG1022:
    """Rigol DG1022 (bench unit). Amplitude commands are Vpp. Output set to HiZ so the display reads what the
    board sees (the board's INPUT is high-Z; the generator's 50 Ω series resistor drops ~nothing)."""
    DELAY = 0.25  # the DG1022 USB stack is slow; back-to-back commands get dropped

    def __init__(self, resource):
        rm = _rm(); self.v = rm.open_resource(resource, timeout=5000)
        self.v.read_termination = "\n"; self.v.write_termination = "\n"
        self.idn = self.v.query("*IDN?").strip(); time.sleep(self.DELAY)
        self.w("OUTP OFF"); self.w("OUTP:LOAD INF"); self.w("VOLT:UNIT VPP")

    def w(self, cmd):
        for attempt in range(3):
            try: self.v.write(cmd); time.sleep(self.DELAY); return
            except Exception as e:
                print(f"  gen retry {attempt+1} on {cmd!r}: {e}"); time.sleep(0.5)
        raise RuntimeError("generator not responding")

    def sine(self, f, vpk, offset=0.0): self.w(f"APPL:SIN {f},{2*vpk:.4f},{offset:.4f}")
    def square(self, f, lo, hi): self.w(f"APPL:SQU {f},{(hi-lo):.4f},{(hi+lo)/2:.4f}")
    def dc(self, volts): self.w(f"APPL:DC DEF,DEF,{volts:.4f}")
    def on(self): self.w("OUTP ON")
    def off(self): self.w("OUTP OFF")
    def zero(self): self.dc(0.0)
    def describe(self): return self.idn


class ManualGen:
    """Fallback: prints the setting (both Vpp and Vpk) and waits for Enter. Works for the FG085 or a DG1022 by hand.
    FG085 note: its amplitude field is Vpp, its output is a fixed 50 Ω, there is no HiZ setting, and it remembers
    the last setting at power-up — set 0 V before plugging the BNC into the board."""
    def _ask(self, msg): input(f"  >>> GENERATOR: {msg}   [Enter when set] ")
    def sine(self, f, vpk, offset=0.0): self._ask(f"SINE  f = {f:g} Hz,  {2*vpk:.3f} Vpp ({vpk:.3f} Vpk),  offset {offset:+.3f} V")
    def square(self, f, lo, hi): self._ask(f"SQUARE  f = {f:g} Hz,  low {lo:+.3f} V / high {hi:+.3f} V  ({hi-lo:.3f} Vpp, offset {(hi+lo)/2:+.3f} V)")
    def dc(self, volts): self._ask(f"DC only (amplitude 0):  offset {volts:+.4f} V")
    def on(self): self._ask("output ON")
    def off(self): self._ask("output OFF")
    def zero(self): self.dc(0.0)
    def describe(self): return "manual (FG085 or front panel)"


# ------------------------------------------------------------------------------------------------------ DMM
class ManualDMM:
    """You read the Fluke 45 / BM235 and type the number. Accepts '2.0013', '2.0013V', '-1.998e-3', 'skip'."""
    def __init__(self, name="Fluke 45"): self.name = name
    def read(self, what, unit="V"):
        while True:
            s = input(f"  >>> {self.name}: {what}  [{unit}] = ").strip().lower().replace(unit.lower(), "").replace(",", "")
            if s in ("skip", "s", ""): return float("nan")
            try: return float(s)
            except ValueError: print("      not a number, again (or 'skip')")
    def describe(self): return f"{self.name} (manual entry)"


class Fluke45:
    """Fluke 45 over RS-232 (9600 8N1, DB9 straight cable + USB-serial). Untested here — only if you have the cable.
    Commands: 'VDC', 'ADC', 'OHMS', 'RATE S' (slow = 5 digits), 'VAL1?' returns the primary display."""
    def __init__(self, port, name="Fluke 45 (RS-232)"):
        import serial
        self.s = serial.Serial(port, 9600, timeout=2); self.name = name
        self._cmd("RATE S")
    def _cmd(self, c):
        self.s.write((c + "\r").encode()); time.sleep(0.3); return self.s.read_all().decode(errors="ignore")
    def mode(self, m): self._cmd({"V": "VDC", "A": "ADC", "R": "OHMS"}[m])
    def read(self, what, unit="V"):
        self.mode({"V": "V", "A": "A", "Ω": "R", "ohm": "R"}.get(unit, "V"))
        for _ in range(3):
            r = self._cmd("VAL1?")
            for tok in r.replace("=>", " ").split():
                try: val = float(tok); print(f"  {self.name}: {what} = {val:g} {unit}"); return val
                except ValueError: pass
        return float("nan")
    def describe(self): return self.name


# ---------------------------------------------------------------------------------------------------- Korad
class Korad:
    """KA3005P over USB-serial (9600 8N1, commands without terminator, ~60 ms between commands).
    Use ONLY as the + rail with its (−) terminal on GND (J2): its USB ground may be bonded to the output (−)."""
    def __init__(self, port):
        import serial
        self.s = serial.Serial(port, 9600, timeout=0.5)
        self.idn = self._q("*IDN?")
    def _w(self, c): self.s.write(c.encode()); time.sleep(0.08)
    def _q(self, c): self._w(c); return self.s.read(64).decode(errors="ignore").strip()
    def set(self, volts, amps): self._w(f"VSET1:{volts:05.2f}"); self._w(f"ISET1:{amps:05.3f}")
    def on(self): self._w("OUT1")
    def off(self): self._w("OUT0")
    def vout(self): return float(self._q("VOUT1?") or "nan")
    def iout(self): return float(self._q("IOUT1?") or "nan")   # 1 mA resolution: not good enough for the 5 mA rail check
