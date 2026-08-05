# utils/system.py
import os
import socket
import subprocess

def execute_restart():
    """Triggers system reboot."""
    subprocess.Popen(["sudo", "reboot"])

def execute_shutdown():
    """Triggers system shutdown."""
    subprocess.Popen(["sudo", "shutdown", "-h", "now"])

def get_hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "HOST"

def get_pi_model() -> str:
    try:
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model", "r") as f:
                return f.read().strip("\x00\n")
    except Exception:
        pass
    return "ZERO 2 W"

def get_os_kernel() -> str:
    try:
        return subprocess.check_output(["uname", "-sr"]).decode("utf-8").strip()
    except Exception:
        return "PI OS LITE"

def get_mac_address() -> str:
    try:
        res = subprocess.check_output(["cat", "/sys/class/net/wlan0/address"]).decode("utf-8").strip()
        return res.upper()
    except Exception:
        return "AA : BB : CC : DD : EE : FF : GG"

def get_uptime() -> str:
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.readline().split()[0])
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours} H {mins} M"
    except Exception:
        return "22 H 41 M"

def get_disk_usage() -> str:
    try:
        st = os.statvfs("/")
        free_mb = (st.f_bavail * st.f_frsize) // (1024 * 1024)
        total_mb = (st.f_blocks * st.f_frsize) // (1024 * 1024)
        used_mb = total_mb - free_mb
        return f"{used_mb} MB OF {total_mb} MB"
    except Exception:
        return "147 MB OF 64000 MB"

def get_cpu_temp() -> str:
    try:
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_c = int(f.read().strip()) // 1000
                return f"{temp_c} ° C"
    except Exception:
        pass
    return "57 ° C"

def get_ram_usage() -> str:
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
            mem_total = 0
            mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1]) // 1024
            mem_used = mem_total - mem_available
            return f"{mem_used} MB OF {mem_total} MB"
    except Exception:
        return "117 MB OF 512 MB"