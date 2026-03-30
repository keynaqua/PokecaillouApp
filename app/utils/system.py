import os
import sys
import subprocess


def get_total_ram_gb():
    if sys.platform.startswith("linux"):
        with open("/proc/meminfo", "r", encoding="utf-8") as file:
            for line in file:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return kb // (1024 * 1024)

    elif sys.platform == "darwin":
        output = subprocess.check_output(
            ["sysctl", "-n", "hw.memsize"],
            text=True
        ).strip()
        return int(output) // (1024 ** 3)

    elif os.name == "nt":
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        memory_status = MEMORYSTATUSEX()
        memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
        return memory_status.ullTotalPhys // (1024 ** 3)

    raise RuntimeError("Impossible de détecter la RAM totale du PC.")


def get_recommended_ram_gb():
    total_ram_gb = get_total_ram_gb()
    recommended_ram_gb = total_ram_gb // 2

    if recommended_ram_gb < 2:
        return 2
    if recommended_ram_gb > 17:
        return 16

    return recommended_ram_gb


def build_java_args():
    ram_gb = get_recommended_ram_gb()

    return (
        f"-Xmx{ram_gb}G "
        "-XX:+UnlockExperimentalVMOptions "
        "-XX:+UseG1GC "
        "-XX:G1NewSizePercent=20 "
        "-XX:G1ReservePercent=20 "
        "-XX:MaxGCPauseMillis=50 "
        "-XX:G1HeapRegionSize=32M"
    )