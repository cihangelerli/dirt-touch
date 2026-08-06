# utils/process.py
import os
import time
import select
import signal
import subprocess
from typing import Tuple
from utils.logger import log_info, log_error

# -------------------------------------------------------------------
# Hot Corner Configuration (640x480 Hardware Target)
# -------------------------------------------------------------------
SCREEN_W, SCREEN_H   = 640, 480
HOT_CORNER_SIZE      = 96     # Top-Right 96x96 px touch zone
HOLD_TIME            = 1.2    # Seconds of continuous hold to trigger close
GRACEFUL_TIMEOUT     = 2.5    # Seconds to wait for SIGINT before escalating to SIGKILL


def get_touch_device_path() -> str:
    """
    Resolves the active touchscreen device path in priority order:
    1. TOUCH_DEVICE env var (explicitly set by systemd or operator)
    2. SDL_TOUCH_DEVICE env var (shared with main.py SDL2 config)
    3. /dev/input/touchscreen stable symlink (udev rule recommended)
    4. Fallback: /dev/input/event0
    """
    if os.environ.get("TOUCH_DEVICE"):
        return os.environ["TOUCH_DEVICE"]
    if os.environ.get("SDL_TOUCH_DEVICE"):
        return os.environ["SDL_TOUCH_DEVICE"]
    if os.path.exists("/dev/input/touchscreen"):
        return "/dev/input/touchscreen"
    return "/dev/input/event0"


def is_in_hot_corner(x: int, y: int) -> bool:
    """Top-Right Corner check: X >= (SCREEN_W - HOT_CORNER_SIZE), Y <= HOT_CORNER_SIZE."""
    return x >= (SCREEN_W - HOT_CORNER_SIZE) and y <= HOT_CORNER_SIZE


def run_application(script_path: str) -> Tuple[bool, str, int]:
    """
    Executes child app script in an isolated process group with active hot corner monitoring.

    While the child process runs, touch events are monitored via evdev on a 50ms select loop.
    A 1.2-second hold in the top-right 96x96px corner sends SIGINT to the child process group.
    If the process does not exit within 2.5 seconds, SIGKILL is escalated.

    Falls back gracefully to standard blocking execution if evdev is unavailable (e.g. on
    macOS or any environment without a Linux input device).
    """
    log_info(f"Launching application wrapper: {script_path}")

    if not os.path.exists(script_path):
        return False, "File Not Found", 404

    if not os.access(script_path, os.X_OK):
        return False, "Permission Denied (EACCES)", 126

    # --- Attempt evdev hot corner monitoring ---
    try:
        from evdev import InputDevice, ecodes
        device_path = get_touch_device_path()
        dev = InputDevice(device_path)
        log_info(f"Hot corner monitor active on {device_path} (top-right {HOT_CORNER_SIZE}x{HOT_CORNER_SIZE}px, hold {HOLD_TIME}s)")
        use_hot_corner = True
    except (ImportError, PermissionError, FileNotFoundError, OSError) as e:
        log_error(f"Hot corner unavailable ({e}). Falling back to standard blocking execution.")
        dev = None
        use_hot_corner = False

    proc = None
    try:
        # start_new_session=True creates a new process group for the child
        proc = subprocess.Popen(
            [script_path],
            stdout=None,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        log_info(f"Child process started (PID {proc.pid})")

        if not use_hot_corner:
            # --- Standard blocking path (no evdev) ---
            _, stderr = proc.communicate()
            exit_code = proc.returncode
        else:
            # --- Hot corner monitoring loop ---
            x, y             = 0, 0
            touch_down       = False
            started_in_corner = False
            press_start      = 0.0
            terminating      = False
            stderr_chunks    = []

            try:
                fd = dev.fd

                # Read stderr without blocking (we will drain it at the end)
                import fcntl
                flags = fcntl.fcntl(proc.stderr.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(proc.stderr.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)

                while proc.poll() is None:
                    # 50ms select: monitors both touch device and child stderr
                    fds_to_watch = [fd, proc.stderr.fileno()]
                    r, _, _ = select.select(fds_to_watch, [], [], 0.05)

                    if proc.stderr.fileno() in r:
                        try:
                            chunk = proc.stderr.read()
                            if chunk:
                                stderr_chunks.append(chunk)
                        except (IOError, OSError):
                            pass

                    if fd in r:
                        for event in dev.read():
                            if event.type == ecodes.EV_ABS:
                                if event.code in (ecodes.ABS_X, ecodes.ABS_MT_POSITION_X):
                                    x = event.value
                                elif event.code in (ecodes.ABS_Y, ecodes.ABS_MT_POSITION_Y):
                                    y = event.value

                            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                                if event.value == 1:    # Finger down
                                    touch_down = True
                                    if is_in_hot_corner(x, y):
                                        started_in_corner = True
                                        press_start = time.monotonic()
                                        log_info(f"Hot corner touch started at ({x}, {y})")
                                elif event.value == 0:  # Finger up
                                    touch_down = False
                                    started_in_corner = False

                    # Hold verification & termination sequence
                    if touch_down and started_in_corner and not terminating:
                        if not is_in_hot_corner(x, y):
                            started_in_corner = False  # Finger drifted out of zone
                        elif time.monotonic() - press_start >= HOLD_TIME:
                            log_info(f"Hot corner hold triggered. Sending SIGINT to process group {proc.pid}...")
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
                                log_error(f"Graceful timeout ({GRACEFUL_TIMEOUT}s) reached. Escalating to SIGKILL...")
                                try:
                                    pgid = os.getpgid(proc.pid)
                                    os.killpg(pgid, signal.SIGKILL)
                                    proc.wait(timeout=1.0)
                                except (ProcessLookupError, subprocess.TimeoutExpired):
                                    pass
                            break

            finally:
                dev.close()

            # Drain any remaining stderr and collect exit code
            proc.wait()
            try:
                remaining = proc.stderr.read()
                if remaining:
                    stderr_chunks.append(remaining)
            except (IOError, OSError):
                pass

            stderr_bytes = b"".join(stderr_chunks)
            exit_code = proc.returncode

        # --- Evaluate exit status ---
        # SIGINT (exit code -2 or 130) from hot corner is not an error
        if exit_code in (-signal.SIGINT, 130):
            log_info(f"Application exited cleanly via hot corner close (code {exit_code}).")
            return True, "Success", 0

        if exit_code != 0:
            if use_hot_corner:
                err_msg = stderr_bytes.decode("utf-8", errors="ignore").strip() if stderr_bytes else f"Exit code {exit_code}"
            else:
                err_msg = locals().get("stderr", b"").decode("utf-8", errors="ignore").strip() if locals().get("stderr") else f"Exit code {exit_code}"
            log_error(f"App {script_path} failed with code {exit_code}: {err_msg}")
            return False, err_msg, exit_code

        return True, "Success", 0

    except KeyboardInterrupt:
        # Catches Ctrl+C pressed in terminal; kills only child group, keeps launcher alive
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