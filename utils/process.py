import glob
import os
import select
import signal
import subprocess
import time
from typing import Optional, Tuple

from utils.logger import log_error, log_info

# -------------------------------------------------------------------
# Hot Corner Configuration (640x480 Hardware Target)[cite: 2]
# -------------------------------------------------------------------
SCREEN_W, SCREEN_H = 640, 480  # [cite: 2]
HOT_CORNER_SIZE = 96  # Top-Right 96x96 px touch zone[cite: 2]
HOLD_TIME = 1.2  # Seconds of continuous hold to trigger close[cite: 2]
GRACEFUL_TIMEOUT = (
    2.5  # Seconds to wait for SIGINT before escalating to SIGKILL[cite: 2]
)
DEBUG_TOUCH = os.environ.get("DEBUG_TOUCH", "0") == "1"


def is_in_hot_corner(x: int, y: int) -> bool:
    """Top-Right Corner check: X >= (SCREEN_W - HOT_CORNER_SIZE), Y <= HOT_CORNER_SIZE."""
    return x >= (SCREEN_W - HOT_CORNER_SIZE) and y <= HOT_CORNER_SIZE  # [cite: 2]


def find_touchscreen_device(InputDevice, ecodes) -> Optional[str]:
    """Finds the active touchscreen evdev device path on Linux systems."""
    for env_var in ("TOUCH_DEVICE", "SDL_TOUCH_DEVICE"):
        path = os.environ.get(env_var)
        if path and os.path.exists(path):
            log_info(
                f"Using explicit touchscreen device from {env_var}: {path}"
            )  # [cite: 2]
            return path

    if os.path.exists("/dev/input/touchscreen"):
        log_info(
            "Using touchscreen device symlink: /dev/input/touchscreen"
        )  # [cite: 2]
        return "/dev/input/touchscreen"

    if os.path.exists("/dev/input/event2"):
        log_info("Using hardware touchscreen device: /dev/input/event2")  # [cite: 2]
        return "/dev/input/event2"

    try:
        event_paths = sorted(glob.glob("/dev/input/event*"))  # [cite: 2]
        for path in event_paths:
            try:
                dev = InputDevice(path)  # [cite: 2]
                caps = dev.capabilities()  # [cite: 2]
                dev_name = (dev.name or "").lower()  # [cite: 2]

                if ecodes.EV_ABS in caps:
                    abs_codes = caps[ecodes.EV_ABS]  # [cite: 2]
                    codes = [
                        c[0] if isinstance(c, tuple) else c for c in abs_codes
                    ]  # [cite: 2]
                    has_mt_x = ecodes.ABS_MT_POSITION_X in codes  # [cite: 2]
                    has_abs_x = ecodes.ABS_X in codes  # [cite: 2]

                    if has_mt_x or has_abs_x:
                        has_touch_key = False
                        if ecodes.EV_KEY in caps:
                            key_codes = [
                                k[0] if isinstance(k, tuple) else k
                                for k in caps[ecodes.EV_KEY]  # [cite: 2]
                            ]
                            has_touch_key = ecodes.BTN_TOUCH in key_codes  # [cite: 2]

                        keywords = (
                            "touch",
                            "ft5406",
                            "goodix",
                            "waveshare",
                            "edt",
                            "ili9",
                            "raspberry",
                        )  # [cite: 2]
                        is_touch_name = any(
                            kw in dev_name for kw in keywords
                        )  # [cite: 2]

                        if has_touch_key or is_touch_name:
                            log_info(
                                f"Auto-discovered touchscreen device: {path} ({dev.name})"
                            )  # [cite: 2]
                            dev.close()  # [cite: 2]
                            return path
                dev.close()  # [cite: 2]
            except Exception:
                pass
    except Exception as e:
        log_error(f"Error during touchscreen auto-discovery: {e}")  # [cite: 2]

    return "/dev/input/event0"  # [cite: 2]


def create_hot_corner_monitor():
    """
    Initializes Goodix touch device, maps raw Y axis (0..639) to Screen X (0..639)
    and raw X axis (0..479) to Screen Y (0..479).
    """
    try:
        from evdev import InputDevice, ecodes  # type: ignore

        device_path = find_touchscreen_device(InputDevice, ecodes)
        dev = InputDevice(device_path)

        raw_x_min, raw_x_max = 0, 479
        raw_y_min, raw_y_max = 0, 639

        try:
            # Query driver capabilities (python-evdev populates AbsInfo automatically)
            caps = dev.capabilities()
            log_info(f"[INPUT DEV] Connected to {dev.name} ({device_path})")

            if ecodes.EV_ABS in caps:
                abs_caps = {
                    item[0]: item[1]
                    for item in caps[ecodes.EV_ABS]
                    if isinstance(item, tuple) and len(item) == 2
                }

                x_info = abs_caps.get(ecodes.ABS_MT_POSITION_X) or abs_caps.get(
                    ecodes.ABS_X
                )
                y_info = abs_caps.get(ecodes.ABS_MT_POSITION_Y) or abs_caps.get(
                    ecodes.ABS_Y
                )

                if x_info and hasattr(x_info, "max") and x_info.max > x_info.min:
                    raw_x_min, raw_x_max = x_info.min, x_info.max
                if y_info and hasattr(y_info, "max") and y_info.max > y_info.min:
                    raw_y_min, raw_y_max = y_info.min, y_info.max

        except Exception as e:
            log_error(f"Error reading touch device capabilities: {e}")

        # Map digitizer Y (0..639) to Screen X (0..639)
        def scale_x(raw_y_val: int) -> int:
            if raw_y_max > raw_y_min:
                scaled = int(
                    (raw_y_val - raw_y_min) * (SCREEN_W - 1) / (raw_y_max - raw_y_min)
                )
                return max(0, min(SCREEN_W - 1, scaled))
            return max(0, min(SCREEN_W - 1, raw_y_val))

        # Map digitizer X (0..479) to Screen Y (0..479)
        def scale_y(raw_x_val: int) -> int:
            if raw_x_max > raw_x_min:
                scaled = int(
                    (raw_x_val - raw_x_min) * (SCREEN_H - 1) / (raw_x_max - raw_x_min)
                )
                return max(0, min(SCREEN_H - 1, scaled))
            return max(0, min(SCREEN_H - 1, raw_x_val))

        log_info(
            f"Hot corner monitor active on {device_path} ({dev.name}) "
            f"[Raw X: {raw_x_min}..{raw_x_max} -> Screen Y, Raw Y: {raw_y_min}..{raw_y_max} -> Screen X]"
        )
        return dev, ecodes, scale_x, scale_y

    except Exception as e:
        log_error(f"Hot corner monitor initialization unavailable: {e}")
        return None, None, None, None


def run_application(script_path: str) -> Tuple[bool, str, int]:
    """
    Executes child app script in an isolated process group with active hot corner monitoring.
    """
    log_info(f"Launching application wrapper: {script_path}")  # [cite: 2]

    if not os.path.exists(script_path):
        return False, "File Not Found", 404  # [cite: 2]

    if not os.access(script_path, os.X_OK):
        return False, "Permission Denied (EACCES)", 126  # [cite: 2]

    dev, ecodes, scale_x, scale_y = create_hot_corner_monitor()  # [cite: 2]
    use_hot_corner = dev is not None  # [cite: 2]

    proc = None
    user_requested_close = False

    try:
        proc = subprocess.Popen(
            [script_path], stdout=None, stderr=subprocess.PIPE, start_new_session=True
        )  # [cite: 2]
        log_info(f"Child process started (PID {proc.pid})")  # [cite: 2]

        if use_hot_corner:
            x, y = 0, 0  # [cite: 2]
            touch_down = False  # [cite: 2]
            started_in_corner = False  # [cite: 2]
            press_start = 0.0  # [cite: 2]
            terminating = False  # [cite: 2]

            try:
                fd = dev.fd  # [cite: 2]
                while proc.poll() is None:  # [cite: 2]
                    r, _, _ = select.select([fd], [], [], 0.05)  # [cite: 2]

                    if r:
                        try:
                            events = dev.read()  # [cite: 2]
                        except (IOError, OSError):
                            events = []  # [cite: 2]

                        for event in events:
                            if event.type == ecodes.EV_ABS:  # [cite: 2]
                                # Raw Y code (1 or 54) maps to Screen X
                                if event.code in (
                                    ecodes.ABS_Y,
                                    ecodes.ABS_MT_POSITION_Y,
                                ):  # [cite: 2]
                                    x = scale_x(event.value)
                                    if DEBUG_TOUCH:
                                        log_info(
                                            f"[TOUCH] raw_y={event.value} -> screen_x={x}"
                                        )
                                # Raw X code (0 or 53) maps to Screen Y
                                elif event.code in (
                                    ecodes.ABS_X,
                                    ecodes.ABS_MT_POSITION_X,
                                ):  # [cite: 2]
                                    y = scale_y(event.value)
                                    if DEBUG_TOUCH:
                                        log_info(
                                            f"[TOUCH] raw_x={event.value} -> screen_y={y}"
                                        )
                                elif (
                                    event.code == ecodes.ABS_MT_TRACKING_ID
                                ):  # [cite: 2]
                                    if event.value == -1:
                                        touch_down = False
                                        started_in_corner = False  # [cite: 2]
                                    else:
                                        touch_down = True

                            elif (
                                event.type == ecodes.EV_KEY
                                and event.code == ecodes.BTN_TOUCH
                            ):  # [cite: 2]
                                touch_down = bool(event.value)
                                if not touch_down:
                                    started_in_corner = False  # [cite: 2]

                    # Hot corner detection
                    if touch_down:  # [cite: 2]
                        if is_in_hot_corner(x, y):  # [cite: 2]
                            if not started_in_corner:
                                started_in_corner = True  # [cite: 2]
                                press_start = time.monotonic()  # [cite: 2]
                                log_info(
                                    f"Hot corner hold started at pixel ({x}, {y})"
                                )  # [cite: 2]
                            elif (
                                time.monotonic() - press_start >= HOLD_TIME  # [cite: 2]
                                and not terminating
                            ):
                                log_info(
                                    f"Hot corner hold detected (>= {HOLD_TIME}s). Closing process group {proc.pid}..."
                                )  # [cite: 2]
                                user_requested_close = True
                                terminating = True  # [cite: 2]

                                try:
                                    pgid = os.getpgid(proc.pid)  # [cite: 2]
                                    os.killpg(pgid, signal.SIGINT)  # [cite: 2]
                                except ProcessLookupError:
                                    log_info(
                                        "Process exited before SIGINT could be delivered."
                                    )  # [cite: 2]
                                    break

                                try:
                                    proc.wait(timeout=GRACEFUL_TIMEOUT)  # [cite: 2]
                                    log_info(
                                        "Application shut down gracefully after hot corner close."
                                    )  # [cite: 2]
                                except subprocess.TimeoutExpired:  # [cite: 2]
                                    log_error(
                                        "Graceful timeout reached! Escalating to SIGKILL..."
                                    )  # [cite: 2]
                                    try:
                                        pgid = os.getpgid(proc.pid)  # [cite: 2]
                                        os.killpg(pgid, signal.SIGKILL)  # [cite: 2]
                                        proc.wait(timeout=1.0)  # [cite: 2]
                                    except (
                                        ProcessLookupError,
                                        subprocess.TimeoutExpired,
                                    ):
                                        pass
                                break
                        else:
                            started_in_corner = False  # [cite: 2]
                    else:
                        started_in_corner = False  # [cite: 2]

            finally:
                try:
                    dev.close()  # [cite: 2]
                except Exception:
                    pass

        # Drain process output
        stderr = b""
        if proc.poll() is None:
            _, stderr = proc.communicate()  # [cite: 2]
        else:
            try:
                stderr = proc.stderr.read() if proc.stderr else b""
            except Exception:
                stderr = b""

        exit_code = proc.returncode  # [cite: 2]

        # Exit code evaluation
        clean_signals = {-signal.SIGINT, 130}
        if user_requested_close:
            clean_signals.update({-signal.SIGKILL, 137, 9})

        if exit_code in clean_signals or exit_code == 0:
            log_info(f"Application exited cleanly (code {exit_code}).")
            return True, "Success", 0

        if exit_code != 0:  # [cite: 2]
            err_msg = (
                stderr.decode("utf-8", errors="ignore").strip()
                if stderr
                else f"Exit code {exit_code}"
            )  # [cite: 2]
            log_error(
                f"App {script_path} failed with code {exit_code}: {err_msg}"
            )  # [cite: 2]
            return False, err_msg, exit_code  # [cite: 2]

        return True, "Success", 0  # [cite: 2]

    except KeyboardInterrupt:
        log_info("Ctrl+C detected. Terminating child process group...")  # [cite: 2]
        if proc and proc.poll() is None:  # [cite: 2]
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # [cite: 2]
                proc.wait(timeout=2)  # [cite: 2]
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)  # [cite: 2]
                except ProcessLookupError:
                    pass
        return False, "Interrupted by user", 130  # [cite: 2]

    except Exception as e:
        log_error(f"Execution error for {script_path}: {str(e)}")  # [cite: 2]
        return False, str(e), 1  # [cite: 2]

    finally:
        if proc and proc.poll() is None:  # [cite: 2]
            try:
                pgid = os.getpgid(proc.pid)  # [cite: 2]
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # [cite: 2]
            except ProcessLookupError:
                pass
        log_info("Control returned to launcher.")  # [cite: 2]


def run_terminal_session():
    """Launches interactive bash shell session with console cleanup."""
    log_info("Executing interactive Terminal session")  # [cite: 2]
    try:
        os.system("clear")  # [cite: 2]
        os.system("bash")  # [cite: 2]
        os.system("stty sane")  # [cite: 2]
        os.system("clear")  # [cite: 2]
    except Exception as e:
        log_error(f"Terminal session error: {str(e)}")  # [cite: 2]
