"""Which CUDA driver API does this process see, and does it expose 13.4's locality domains?
Talks to libcuda directly (ctypes), so it needs no toolkit. One JSON line to stdout."""
import ctypes, json, os

ATTR = {"locality_domain_count": 149, "locality_domain_sm_count": 157, "sm_count": 16, "cc_major": 75}
cu = ctypes.CDLL("libcuda.so.1")
out = {"LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", "")}
out["cuInit"] = cu.cuInit(0)
v = ctypes.c_int()
out["cuDriverGetVersion"] = (cu.cuDriverGetVersion(ctypes.byref(v)), v.value)
dev = ctypes.c_int()
cu.cuDeviceGet(ctypes.byref(dev), 0)
name = ctypes.create_string_buffer(128)
cu.cuDeviceGetName(name, 128, dev)
out["device"] = name.value.decode()
for k, a in ATTR.items():
    val = ctypes.c_int(-1)
    rc = cu.cuDeviceGetAttribute(ctypes.byref(val), a, dev)
    out[k] = {"rc": rc, "value": val.value if rc == 0 else None}
# A symbol that exists only in a 13.4+ driver library tells which libcuda was loaded.
for sym in ("cuMemGetLocationInfo", "cuGreenCtxCreate", "cuDeviceGetDevResource"):
    out["has_" + sym] = hasattr(cu, sym)
print("COMPAT-JSON " + json.dumps(out))
