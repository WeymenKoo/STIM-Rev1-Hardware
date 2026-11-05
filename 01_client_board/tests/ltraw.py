"""Minimal LTspice .raw reader (binary, stepped, tran or ac). import ltraw; r = ltraw.Raw(path); r.sig("V(OUT)-V(VN)", step)"""
import numpy as np, re, pathlib
class Raw:
    def __init__(self, path):
        b = pathlib.Path(path).read_bytes()
        enc = "utf-16-le" if b[1:2] == b"\x00" else "latin-1"
        key = "Binary:\n".encode(enc); i = b.index(key); hdr = b[:i].decode(enc); data = b[i+len(key):]
        nv = int(re.search(r"No\. Variables:\s*(\d+)", hdr).group(1)); npts = int(re.search(r"No\. Points:\s*(\d+)", hdr).group(1))
        self.names = [l.split("\t")[2] for l in hdr.split("Variables:")[-1].strip().splitlines()]
        flags = re.search(r"Flags:(.*)", hdr).group(1)
        self.complex = "complex" in flags
        if self.complex:
            arr = np.frombuffer(data, dtype="<c16", count=npts*nv).reshape(npts, nv); x = arr[:,0].real; self.v = arr
        elif "double" in flags:
            arr = np.frombuffer(data, dtype="<f8", count=npts*nv).reshape(npts, nv); x = arr[:,0]; self.v = arr
        else:
            rec = np.dtype([("t","<f8"),("v","<f4",(nv-1,))]); arr = np.frombuffer(data, dtype=rec, count=npts)
            x = arr["t"]; self.v = np.column_stack([x, arr["v"]])
        self.x = np.abs(x)
        cuts = np.where(np.diff(self.x) < 0)[0] + 1; self.steps = np.split(np.arange(npts), cuts)
        self.col = {n.lower(): k for k, n in enumerate(self.names)}
    def sig(self, expr, idx):
        e = re.sub(r"(v\([^)]+\)|i\([^)]+\))", lambda m: f"self.v[idx,{self.col[m.group(1)]}]", expr.lower())
        return eval(e, {"self": self, "idx": idx, "np": np})
    def win(self, step, lo=None, hi=None):
        idx = self.steps[step]; x = self.x[idx]; m = np.ones(len(idx), bool)
        if lo is not None: m &= x >= lo
        if hi is not None: m &= x <= hi
        return idx[m]
