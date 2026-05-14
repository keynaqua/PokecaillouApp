import ctypes

from config import BYTES_PER_GIB, JAVA_RAM_MAX_GB, JAVA_RAM_MIN_GB, JAVA_RAM_RATIO


def get_total_ram_gb():
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

    # 🔥 IMPORTANT : division FLOAT + round
    return round(memory_status.ullTotalPhys / BYTES_PER_GIB)


def get_recommended_ram_gb():
    total = get_total_ram_gb()

    ram = int(total * JAVA_RAM_RATIO)

    if ram < JAVA_RAM_MIN_GB:
        return JAVA_RAM_MIN_GB
    if ram > JAVA_RAM_MAX_GB:
        return JAVA_RAM_MAX_GB

    return ram


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
