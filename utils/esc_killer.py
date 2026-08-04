# utils/esc_killer.py
import evdev
import os
import signal
import sys

def listen_for_esc(parent_pid):
    # Find all input devices
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    
    # Filter for devices that have keyboard capabilities
    keyboards = [d for d in devices if evdev.ecodes.EV_KEY in d.capabilities()]
    
    if not keyboards:
        sys.exit(1)

    try:
        # Listen to the first detected keyboard
        for event in keyboards[0].read_loop():
            if event.type == evdev.ecodes.EV_KEY and event.value == 1:  # 1 = KeyDown
                if event.code == evdev.ecodes.KEY_ESC:
                    os.kill(parent_pid, signal.SIGTERM)
                    sys.exit(0)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        listen_for_esc(int(sys.argv[1]))