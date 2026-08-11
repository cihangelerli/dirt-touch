import glob
import os
import select
import signal
import subprocess
import time
from typing import Optional, Tuple  # type: ignore

from utils.logger import log_error, log_info

# -------------------------------------------------------------------
# Hot Corner Configuration (640x480 Hardware Target)
# -------------------------------------------------------------------
SCREEN_W, SCREEN_H = 640, 480
HOT_CORNER_SIZE = 96  # Top-Right 96x96 px touch zone
HOLD_TIME = 1.2  # Seconds of continuous hold to trigger close
GRACEFUL_TIMEOUT = 2.5  # Seconds to wait for SIGINT before escalating to SIGKILL
DEBUG_TOUCH = os.environ.get("DEBUG_TOUCH", "0") == "1"


def is_in_hot_corner(x: int, y: int) -> bool:
    """Top-Right Corner check: X >= (SCREEN_W - HOT_CORNER_SIZE), Y <= HOT_CORNER_SIZE."""
    return x >= (SCREEN_W - HOT_CORNER_SIZE) and y <= HOT_CORNER_SIZE


def find_touchscreen_device(InputDevice, ecodes) -> Optional[str]:
    """Finds the active touchscreen evdev device path on Linux systems."""
    for env_var in ("TOUCH_DEVICE", "SDL_TOUCH_DEVICE"):
        path = os.environ.get(env_var)
        if path and os.path.exists(path):
            log_info(f"Using explicit touchscreen device from {env_var}: {path}")
            return path

    if os.path.exists("/dev/input/touchscreen"):
        log_info("Using touchscreen device symlink: /dev/input/touchscreen")
        return "/dev/input/touchscreen"

    try:
        event_paths = sorted(glob.glob("/dev/input/event*"))
        for path in event_paths:
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                dev_name = (dev.name or "").lower()

                if ecodes.EV_ABS in caps:
                    abs_codes = caps[ecodes.EV_ABS]
                    codes = [c[0] if isinstance(c, tuple) else c for c in abs_codes]
                    has_mt_x = ecodes.ABS_MT_POSITION_X in codes
                    has_abs_x = ecodes.ABS_X in codes

                    if has_mt_x or has_abs_x:
                        has_touch_key = False
                        if ecodes.EV_KEY in caps:
                            key_codes = [
                                k[0] if isinstance(k, tuple) else k
                                for k in caps[ecodes.EV_KEY]
                            ]
                            has_touch_key = ecodes.BTN_TOUCH in key_codes

                        keywords = (
                            "touch",
                            "ft5406",
                            "goodix",
                            "waveshare",
                            "edt",
                            "ili9",
                            "raspberry",
                        )
                        is_touch_name = any(kw in dev_name for kw in keywords)

                        if has_touch_key or is_touch_name:
                            log_info(
                                f"Auto-discovered touchscreen device: {path} ({dev.name})"
                            )
                            dev.close()
                            return path
                dev.close()
            except Exception as e:
                log_error(f"Unexpected error during touchscreen auto-discovery: {e}")
    except Exception as e:
        log_error(f"Error during touchscreen auto-discovery: {e}")

    return "/dev/input/event0"


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

        def scale_x(raw_y_val: int) -> int:
            if raw_y_max > raw_y_min:
                scaled = int(
                    (raw_y_val - raw_y_min) * (SCREEN_W - 1) / (raw_y_max - raw_y_min)
                )
                # Invert X axis so low raw_y maps to top-right (screen_x near 639)
                return max(0, min(SCREEN_W - 1, (SCREEN_W - 1) - scaled))
            return max(0, min(SCREEN_W - 1, raw_y_val))

        def scale_y(raw_x_val: int) -> int:
            if raw_x_max > raw_x_min:
                scaled = int(
                    (raw_x_val - raw_x_min) * (SCREEN_H - 1) / (raw_x_max - raw_x_min)
                )
                # Invert Y axis so high raw_x maps to top edge (screen_y near 0)
                return max(0, min(SCREEN_H - 1, (SCREEN_H - 1) - scaled))
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
    log_info(f"Launching application wrapper: {script_path}")

    if not os.path.exists(script_path):
        return False, "File Not Found", 404

    if not os.access(script_path, os.X_OK):
        return False, "Permission Denied (EACCES)", 126

    dev, ecodes, scale_x, scale_y = create_hot_corner_monitor()
    use_hot_corner = dev is not None

    proc = None
    user_requested_close = False

    try:
        proc = subprocess.Popen(
            [script_path], stdout=None, stderr=subprocess.PIPE, start_new_session=True
        )
        log_info(f"Child process started (PID {proc.pid})")

        if use_hot_corner:
            x, y = 0, 0
            touch_down = False
            started_in_corner = False
            press_start = 0.0
            terminating = False

            try:
                fd = dev.fd
                while proc.poll() is None:
                    r, _, _ = select.select([fd], [], [], 0.05)

                    if r:
                        try:
                            events = dev.read()
                        except (IOError, OSError):
                            events = []

                        for event in events:
                            if event.type == ecodes.EV_ABS:
                                if event.code in (
                                    ecodes.ABS_Y,
                                    ecodes.ABS_MT_POSITION_Y,
                                ):
                                    x = scale_x(event.value)
                                    touch_down = True
                                    if DEBUG_TOUCH:
                                        log_info(
                                            f"[TOUCH] raw_y={event.value} -> screen_x={x}"
                                        )
                                elif event.code in (
                                    ecodes.ABS_X,
                                    ecodes.ABS_MT_POSITION_X,
                                ):
                                    y = scale_y(event.value)
                                    touch_down = True
                                    if DEBUG_TOUCH:
                                        log_info(
                                            f"[TOUCH] raw_x={event.value} -> screen_y={y}"
                                        )
                                elif event.code == ecodes.ABS_MT_TRACKING_ID:
                                    if event.value == -1:
                                        touch_down = False
                                        started_in_corner = False
                                    else:
                                        touch_down = True

                            elif (
                                event.type == ecodes.EV_KEY
                                and event.code == ecodes.BTN_TOUCH
                            ):
                                touch_down = bool(event.value)
                                if not touch_down:
                                    started_in_corner = False

                    # Hot corner timer logic (evaluated on every loop tick even during stationary hold)
                    if touch_down:
                        if is_in_hot_corner(x, y):
                            if not started_in_corner:
                                started_in_corner = True
                                press_start = time.monotonic()
                                log_info(f"Hot corner hold started at pixel ({x}, {y})")
                            elif (
                                time.monotonic() - press_start >= HOLD_TIME
                                and not terminating
                            ):
                                log_info(
                                    f"Hot corner hold detected (>= {HOLD_TIME}s). Closing process group {proc.pid}..."
                                )
                                user_requested_close = True
                                terminating = True

                                try:
                                    pgid = os.getpgid(proc.pid)
                                    os.killpg(pgid, signal.SIGINT)
                                except ProcessLookupError:
                                    log_info(
                                        "Process exited before SIGINT could be delivered."
                                    )
                                    break

                                try:
                                    proc.wait(timeout=GRACEFUL_TIMEOUT)
                                    log_info(
                                        "Application shut down gracefully after hot corner close."
                                    )
                                except subprocess.TimeoutExpired:
                                    log_error(
                                        "Graceful timeout reached! Escalating to SIGKILL..."
                                    )
                                    try:
                                        pgid = os.getpgid(proc.pid)
                                        os.killpg(pgid, signal.SIGKILL)
                                        proc.wait(timeout=1.0)
                                    except (
                                        ProcessLookupError,
                                        subprocess.TimeoutExpired,
                                    ):
                                        pass
                                break
                        else:
                            started_in_corner = False
                    else:
                        started_in_corner = False

            finally:
                try:
                    dev.close()
                except Exception as e:
                    log_error(f"Unexpected error while closing touchscreen device: {e}")

        # Drain process output
        stderr = b""
        if proc.poll() is None:
            _, stderr = proc.communicate()
        else:
            try:
                stderr = proc.stderr.read() if proc.stderr else b""
            except Exception as e:
                log_error(f"Unexpected error while reading process stderr: {e}")
                stderr = b""

        exit_code = proc.returncode

        # Exit code evaluation
        clean_signals = {-signal.SIGINT, 130}
        if user_requested_close:
            clean_signals.update({-signal.SIGKILL, 137, 9})

        if exit_code in clean_signals or exit_code == 0:
            log_info(f"Application exited cleanly (code {exit_code}).")
            return True, "Success", 0

        if exit_code != 0:
            err_msg = (
                stderr.decode("utf-8", errors="ignore").strip()
                if stderr
                else f"Exit code {exit_code}"
            )
            log_error(f"App {script_path} failed with code {exit_code}: {err_msg}")
            return False, err_msg, exit_code

        return True, "Success", 0

    except KeyboardInterrupt:
        log_info("Ctrl+C detected. Terminating child process group...")
        if proc and proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=2)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
        return False, "Interrupted by user", 130

    except Exception as e:
        log_error(f"Execution error for {script_path}: {str(e)}")
        return False, str(e), 1

    finally:
        if proc and proc.poll() is None:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
        log_info("Control returned to launcher.")


def run_terminal_session():
    """Launches interactive bash shell session with console cleanup."""
    log_info("Executing interactive Terminal session")
    try:
        # Restore terminal driver to canonical mode BEFORE starting bash
        os.system("stty sane")
        os.system("setterm -cursor on 2>/dev/null")
        os.system("clear")

        # Execute interactive login shell
        os.system("bash --login")

        # Clean up screen when user exits bash (via 'exit' or Ctrl+D)
        os.system("stty sane")
        os.system("clear")
    except Exception as e:
        log_error(f"Terminal session error: {str(e)}")
