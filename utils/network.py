# utils/network.py
import socket
import subprocess

def get_ip_address() -> str:
    """Returns local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_wifi_signal() -> str:
    """Returns WiFi signal strength representation for footer."""
    try:
        res = subprocess.check_output(["iwconfig"], stderr=subprocess.DEVNULL).decode("utf-8")
        if "Link Quality=" in res:
            part = res.split("Link Quality=")[1].split(" ")[0]
            num, denom = map(int, part.split("/"))
            ratio = num / denom
            if ratio > 0.8: return "WiFi IIIII"
            elif ratio > 0.6: return "WiFi IIII_"
            elif ratio > 0.4: return "WiFi III__"
            elif ratio > 0.2: return "WiFi II___"
            else: return "WiFi I____"
    except Exception:
        pass
    return "WiFi ?????"  # if iwconfig is unavailable