# utils/process.py
import os
import glob
import time
import select
import signal
import subprocess
from typing import Tuple, Optional, Callable
from utils.logger import log_info, log_error

# -------------------------------------------------------------------
# Hot Corner Configuration (640x480 Hardware Target)
# -------------------------------------------------------------------
SCREEN_W, SCREEN_H   = 640, 480
HOT_CORNER_SIZE      = 96     # Top-Right 96x96 px touch zone
HOLD_TIME            = 1.2    # Seconds of continuous hold to trigger close
GRACEFUL_TIMEOUT     = 2.5    # Seconds to wait for SIGINT before escalating to SIGKILL


def is_in_hot_corner(x: int, y: int) -> bool:
    """Top-Right Corner check: X >= (SCREEN_W - HOT_CORNER_SIZE), Y <= HOT_CORNER_SIZE."""
    return x >= (SCREEN_W - HOT_CORNER_SIZE) and y <= HOT_CORNER_SIZE


def find_touchscreen_device(InputDevice, ecodes) -> Optional[str]:
    """
    Finds the active touchscreen evdev device path on Linux systems.
    Priority:
    1. TOUCH_DEVICE environment variable
    2. SDL_TOUCH_DEVICE environment variable
    3. /dev/input/touchscreen stable symlink
    4. Auto-discovery across /dev/input/event* for touchscreen capabilities
    5. Fallback: /dev/input/event0
    """
    for env_var in ("TOUCH_DEVICE", "SDL_TOUCH_DEVICE"):
        path = os.environ.get(env_var)
        if path and os.path.exists(path):
            log_info(f"Using explicit touchscreen device from {env_var}: {path}")
            return path

    if os.path.exists("/dev/input/touchscreen"):
        log_info("Using touchscreen device symlink: /dev/input/touchscreen")
        return "/dev/input/touchscreen"

    # Auto-discover among /dev/input/event*
    try:
        event_paths = sorted(glob.glob("/dev/input/event*"))
        for path in event_paths:
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                dev_name = (dev.name or "").lower()

                # Check for ABS events (ABS_X or ABS_MT_POSITION_X)
                if ecodes.EV_ABS in caps:
                    abs_codes = caps[ecodes.EV_ABS]
                    codes = [c[0] if isinstance(c, tuple) else c for c in abs_codes]
                    has_mt_x = ecodes.ABS_MT_POSITION_X in codes
                    has_abs_x = ecodes.ABS_X in codes

                    if has_mt_x or has_abs_x:
                        has_touch_key = False
                        if ecodes.EV_KEY in caps:
                            key_codes = [k[0] if isinstance(k, tuple) else k for k in caps[ecodes.EV_KEY]]
                            has_touch_key = ecodes.BTN_TOUCH in key_codes

                        keywords = ("touch", "ft5406", "goodix", "waveshare", "edt", "ili9", "raspberry")
                        is_touch_name = any(kw in dev_name for kw in keywords)

                        if has_touch_key or is_touch_name:
                            log_info(f"Auto-discovered touchscreen device: {path} ({dev.name})")
                            dev.close()
                            return path
                dev.close()
            except Exception:
                pass
    except Exception as e:
        log_error(f"Error during touchscreen auto-discovery: {e}")

    return "/dev/input/event0"


def create_hot_corner_monitor():
    """
    Attempts to initialize evdev InputDevice and compute coordinate scale factors.
    Returns (dev, ecodes, scale_x_fn, scale_y_fn) or (None, None, None, None).
    """
    try:
        from evdev import InputDevice, ecodes
        device_path = find_touchscreen_device(InputDevice, ecodes)
        dev = InputDevice(device_path)

        # Determine coordinate axis bounds for normalization to 640x480
        abs_x_min, abs_x_max = 0, 0
        abs_y_min, abs_y_max = 0, 0

        try:
            abs_info_dict = dev.absinfo
            if abs_info_dict:
                x_info = abs_info_dict.get(ecodes.ABS_MT_POSITION_X) or abs_info_dict.get(ecodes.ABS_X)
                y_info = abs_info_dict.get(ecodes.ABS_MT_POSITION_Y) or abs_info_dict.get(ecodes.ABS_Y)

                if x_info and x_info.max > x_info.min:
                    abs_x_min, abs_x_max = x_info.min, x_info.max
                if y_info and y_info.max > y_info.min:
                    abs_y_min, abs_y_max = y_info.min, y_info.max
        except Exception:
            pass

        def scale_x(val: int) -> int:
            if abs_x_max > abs_x_min:
                return int((val - abs_x_min) * SCREEN_W / (abs_x_max - abs_x_min))
            return val

        def scale_y(val: int) -> int:
            if abs_y_max > abs_y_min:
                return int((val - abs_y_min) * SCREEN_H / (abs_y_max - abs_y_min))
            return val

        log_info(f"Hot corner monitor active on {device_path} ({dev.name}) [X-range: {abs_x_min}..{abs_x_max}, Y-range: {abs_y_min}..{abs_y_max}]")
        return dev, ecodes, scale_x, scale_y

    except Exception as e:
        log_error(f"Hot corner monitor initialization unavailable: {e}")
        return None, None, None, None


def run_application(script_path: str) -> Tuple[bool, str, int]:
    """
    Executes child app script in an isolated process group with active hot corner monitoring.

    While the child process runs, touch events are monitored via evdev on a 50ms select loop.
    A 1.2-second hold in the top-right 96x96px corner sends SIGINT to the child process group.
    If the process does not exit within 2.5 seconds, SIGKILL is escalated.
    """
    log_info(f"Launching application wrapper: {script_path}")

    if not os.path.exists(script_path):
        return False, "File Not Found", 404

    if not os.access(script_path, os.X_OK):
        return False, "Permission Denied (EACCES)", 126

    # Initialize touchscreen monitor if available
    dev, ecodes, scale_x, scale_y = create_hot_corner_monitor()
    use_hot_corner = dev is not None

    proc = None
    try:
        # start_new_session=True detaches child process group for clean signal handling
        proc = subprocess.Popen(
            [script_path],
            stdout=None,
            stderr=subprocess.PIPE,
            start_new_session=True
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
                    # 50ms select block to keep CPU usage near 0%
                    r, _, _ = select.select([fd], [], [], 0.05)

                    if r:
                        try:
                            events = dev.read()
                        except (IOError, OSError):
                            events = []

                        for event in events:
                            if event.type == ecodes.EV_ABS:
                                if event.code in (ecodes.ABS_X, ecodes.ABS_MT_POSITION_X):
                                    x = scale_x(event.value)
                                elif event.code in (ecodes.ABS_Y, ecodes.ABS_MT_POSITION_Y):
                                    y = scale_y(event.value)
                                elif event.code == ecodes.ABS_MT_TRACKING_ID:
                                    if event.value != -1:
                                        touch_down = True
                                    else:
                                        touch_down = False
                                        started_in_corner = False

                            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                                if event.value == 1:
                                    touch_down = True
                                elif event.value == 0:
                                    touch_down = False
                                    started_in_corner = False

                    # Check touch state & hot corner tracking
                    if touch_down:
                        if is_in_hot_corner(x, y):
                            if not started_in_corner:
                                started_in_corner = True
                                press_start = time.monotonic()
                                log_info(f"Hot corner hold started at ({x}, {y})")
                            elif time.monotonic() - press_start >= HOLD_TIME and not terminating:
                                log_info(f"Hot corner hold detected (>= {HOLD_TIME}s). Closing process group {proc.pid}...")
                                terminating = True

                                try:
                                    pgid = os.getpgid(proc.pid)
                                    os.killpg(pgid, signal.SIGINT)
                                except ProcessLookupError:
                                    log_info("Process exited before SIGINT could be delivered.")
                                    break

                                # Graceful exit runway
                                try:
                                    proc.wait(timeout=GRACEFUL_TIMEOUT)
                                    log_info("Application shut down gracefully after hot corner close.")
                                except subprocess.TimeoutExpired:
                                    log_error(f"Graceful timeout ({GRACEFUL_TIMEOUT}s) reached! Escalating to SIGKILL...")
                                    try:
                                        pgid = os.getpgid(proc.pid)
                                        os.killpg(pgid, signal.SIGKILL)
                                        proc.wait(timeout=1.0)
                                    except (ProcessLookupError, subprocess.TimeoutExpired):
                                        pass
                                break
                        else:
                            # Finger drifted out of top-right 96x96 box
                            started_in_corner = False
                    else:
                        started_in_corner = False

            finally:
                try:
                    dev.close()
                except Exception:
                    pass

        # Drain process output and obtain returncode
        _, stderr = proc.communicate()
        exit_code = proc.returncode

        # --- Evaluate exit status ---
        # SIGINT (exit code -2 or 130) from hot corner is treated as clean user exit
        if exit_code in (-signal.SIGINT, 130):
            log_info(f"Application exited cleanly via hot corner close (code {exit_code}).")
            return True, "Success", 0

        if exit_code != 0:
            err_msg = stderr.decode("utf-8", errors="ignore").strip() if stderr else f"Exit code {exit_code}"
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
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        log_info("Control returned to launcher.")


def run_terminal_session():
    """Launches interactive bash shell session with console cleanup."""
    log_info("Executing interactive Terminal session")
    try:
        os.system("clear")
        os.system("bash")
        os.system("stty sane")
        os.system("clear")
    except Exception as e:
        log_error(f"Terminal session error: {str(e)}")