"""Read-only: which CUDA runtime does CuPy load? Prints CuPy's reported versions and every cudart/nvrtc DLL in the process."""
import ctypes
import ctypes.wintypes as wt
import cupy

a = cupy.arange(4, dtype=cupy.float32).sum()  # bring the context up
print("cupy", cupy.__version__, "| sum", float(a))
print("runtimeGetVersion", cupy.cuda.runtime.runtimeGetVersion(), "| driverGetVersion", cupy.cuda.runtime.driverGetVersion())
psapi, k32 = ctypes.WinDLL("psapi"), ctypes.WinDLL("kernel32")
k32.GetCurrentProcess.restype = wt.HANDLE
psapi.EnumProcessModules.argtypes = [wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD, ctypes.POINTER(wt.DWORD)]
psapi.GetModuleFileNameExW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
h = k32.GetCurrentProcess()
mods = (wt.HMODULE * 4096)(); need = wt.DWORD()
ok = psapi.EnumProcessModules(h, mods, ctypes.sizeof(mods), ctypes.byref(need))
print("modules", need.value // ctypes.sizeof(wt.HMODULE), "ok", ok)
buf = ctypes.create_unicode_buffer(1024)
for m in mods[: need.value // ctypes.sizeof(wt.HMODULE)]:
    psapi.GetModuleFileNameExW(h, m, buf, 1024)
    low = buf.value.lower()
    if any(x in low for x in ("cuda", "nvrtc", "cublas", "cupy")):
        print("loaded", buf.value)
