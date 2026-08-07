# DIRT-TOUCH v1.0 Development Roadmap

_Lightweight Touchscreen Launcher for Raspberry Pi Zero 2 W_

---

## 1. Project Overview

DIRT-TOUCH is a lightweight touchscreen launcher designed specifically for Raspberry Pi systems running Debian/Raspberry Pi OS Lite without any desktop environment.

The goal is not to create another desktop shell, but instead a dedicated appliance-like interface that boots directly into a fullscreen launcher. The launcher should feel closer to an industrial controller, arcade cabinet, kiosk, or embedded device than a traditional Linux computer.

The launcher will be responsible for:

- launching local applications

- launching shell wrappers

- launching Cog-based web applications

- basic system administration

- displaying system information

- providing visual feedback

- acting as the permanent "home screen"

The launcher should consume minimal CPU and RAM and remain perfectly usable on a Raspberry Pi Zero 2 W.

---

## 2. Design Philosophy

DIRT-TOUCH should always prioritize:

- simplicity

- responsiveness

- clarity

- readability

- reliability

- minimal resource usage

It should never attempt to imitate Windows, Android, or KDE.

The interface should instead resemble:

- industrial control software

- arcade machine launchers

- embedded firmware

- CNC interfaces

- laboratory equipment

The UI should appear as though it belongs to the hardware itself.

---

## 3. Technical Requirements

### Platform

- Raspberry Pi Zero 2 W

- Raspberry Pi OS Lite / Debian Lite

- No desktop environment (no LXDE, XFCE, KDE, GNOME, X11 session, or window manager)

The launcher itself becomes the operating interface.

### Display

- $640 \times 480$ resolution

- Capacitive touchscreen

- Landscape orientation

- Touch events only (a physical keyboard should never be required for normal operation of interface)

### Rendering Library

The launcher shall be implemented entirely using **Pygame**.

Reasons:

- No Qt, No Electron, No browser UI, No HTML frontend.

- Lightweight, excellent SDL support, direct input handling, simple rendering API, easy deployment, adequate performance on Pi Zero 2 W.

---

## 4. Application Lifecycle & State Machine

### Launcher State Machine

The launcher operates as a central state machine managing screen navigation rather than having screens create or instantiate each other directly.

```text
[ HOME ] ──> [ SETTINGS ] ──> [ SYSTEM INFO ]
   ▲              │
   └──────────────┴── [ BACK ]

```

### Application Execution Lifecycle

Child processes (wrapper scripts) are executed cleanly via Python's `subprocess` library:

1. **User presses Application Button**
2. **Suspend Input Processing:** Launcher pauses input event processing while the child process runs.
3. **Execute Wrapper:** `process = subprocess.Popen(['/home/user/run_app.sh'])`
4. **Wait for Completion:** `process.wait()` blocks until child process terminates.
5. **Resume Launcher:** Input processing is re-enabled, `on_resume()` is called on the active screen, and the Home screen is redrawn automatically.

On boot, `systemd` starts DIRT-TOUCH, which remains resident until a system reboot or shutdown is requested.

---

## 5. Screen System Architecture & Interface

Every screen in DIRT-TOUCH must inherit from a common `BaseScreen` interface to enforce consistent behavior across the application.

```python
class BaseScreen:
    def enter(self):
        """Called when navigating to this screen."""
        pass

    def exit(self):
        """Called when navigating away from this screen."""
        pass

    def update(self, dt):
        """Called every frame to update state/animations."""
        pass

    def draw(self, surface):
        """Render screen elements to the target surface."""
        pass

    def handle_event(self, event):
        """Process touch/input events."""
        pass

    def on_resume(self):
        """Called when returning to launcher after child app exits."""
        pass

```

No screen should know how another screen draws itself.

---

## 6. Core Application Architecture & Automatic Discovery

DIRT-TOUCH **never** contains a hardcoded list of user applications. The application grid is dynamically generated from discovered wrapper scripts in the user's home directory (`$HOME`).

### Shell Wrapper Public API Contract

Every launchable application provides a shell wrapper script in `$HOME` named following the pattern `run_<application>.sh`.

Examples:

- `~/run_badhabits.sh`

- `~/run_magnetik.sh`

- `~/run_alchemy.sh`

- `~/run_glitchbooth_slideshow.sh`

Whether operating on `dirtzero`, `dirtcloud`, or any other hostname, the launcher targets `$HOME` for wrapper discovery.

```text
dirtzero@dirtzero:~ $
dirtcloud@dirtcloud:~ $

```

**Key Advantages:**

- Shell wrappers act as the application's public contract.

- Wrappers handle virtual environments, environment variables, working directories, or browser invocations (e.g., Cog).

- Applications can still be executed manually from the terminal.

- Portability across systems without code modifications.

### Wrapper Discovery & Lifecycle

Rediscovery happens strictly at launcher startup:

```text
Launcher Starts
      │
      ▼
Discover run_*.sh in $HOME
      │
      ▼
Parse Metadata & Sort Buttons
      │
      ▼
Grid Populated & Remains Fixed
      │
      ▼
(Launcher Restart required for new apps)

```

### Metadata Tagging Format

Wrappers may specify display metadata via comment lines near the top of the file:

```bash
#!/bin/bash
# DIRT_TITLE=Glitchbooth Slideshow
# DIRT_CATEGORY=Art
# DIRT_ORDER=1
# DIRT_COLOR=APP

exec cog https://glitchbooth.online/slideshow

```

- **`DIRT_TITLE`**: Custom button label (supports newline characters or automatic fallback formatting).

- **`DIRT_CATEGORY`**: Categorization tag (for future filtering).
- **`DIRT_ORDER`**: Priority integer for explicit ordering.
- **`DIRT_COLOR`**: Style identifier.

> **Extensibility:** Unrecognized metadata tags are safely ignored by the metadata parser, ensuring future-proof forward compatibility.

### Application Ordering Logic

1. **Primary:** Sort applications numerically by `# DIRT_ORDER=<number>` (ascending).
2. **Secondary:** If no `DIRT_ORDER` tag exists, sort alphabetically by formatted title/filename.

If no `DIRT_TITLE` is present, `run_glitchbooth_slideshow.sh` automatically formats to `GLITCHBOOTH SLIDESHOW`.

---

## 7. Button System & Touch Input Model

### Button State Mechanics

Buttons are object instances (`Button` class) with distinct state representation:

- **Normal:** Default state.

- **Pressed:** Active touch state.

- **Disabled:** Inactive state.

- **Unavailable / Placeholder:** Muted placeholder visually indicating unassigned or unconfigured features.

### Touch Gesture Interaction Flow

To prevent accidental triggers, button activation requires strict bounding-box validation:

```text
Touch Down (on button) ──> Visual Highlight State
                                │
                                ▼
                           Touch Dragged?
                          /              \
                        (Inside)       (Outside)
                          /                  \
                         ▼                    ▼
                   Touch Released      Cancel Action
                         │             (Return Normal)
                         ▼
                  Execute Callback

```

If the user drags their finger off the button before releasing, the action is cancelled and the button reverts to its normal state.

---

## 8. Color Palette & Centralized Styling

To maintain visual consistency and simplify theme updates, **no hex values may be hardcoded** within screen code. All styling must reference constant definitions from `ui/colors.py`:

```python
# ui/colors.py
COLOR_BACKGROUND   = (0x15, 0x16, 0x16) # #151616
COLOR_APP_BUTTON   = (0x5B, 0x34, 0x14) # #5B3414
COLOR_SYS_BUTTON   = (0xFF, 0x77, 0x00) # #FF7700
COLOR_PRESSED_BG   = (0x11, 0x11, 0x11) # #111111
COLOR_TEXT         = (0xFF, 0x77, 0x00) # #FF7700
COLOR_PRESSED_TEXT = (0xFF, 0x99, 0x00) # #FF9900
COLOR_DISABLED_TXT = (0xA5, 0x54, 0x12) # #A55412
COLOR_BORDER       = (0x11, 0x11, 0x11) # #111111

```

---

## 9. Typography Rules

DIRT-TOUCH uses **one single font family** across the entire UI to preserve its industrial visual language.

To prevent visual clutter, only **two font sizes** are permitted:

- **Large Font:** Used for button labels, titles, primary headers.
- **Small Font:** Used for footer status metrics, subtitles, metadata details.

Uppercase text formatting is enforced across all titles and labels.

---

## 10. Screen Layout & Dynamic Grid

### Home Screen

- Top area: $2 \times 3$ or $2 \times 4$ dynamic application grid (filled by discovered wrappers, empty slots marked `[EMPTY]`).

- System actions: `SETTINGS`, `TERMINAL`, `RESTART`, `SHUTDOWN`.

- Bottom area: Persistent Footer Bar.

### Settings Screen

- System options: `SYSTEM INFO`, `WiFi`, `CONFIG`, `HTOP`, `ABOUT`, `RESTART DIRT-TOUCH`, `BACK`.

---

## 11. Navigation & Transitions

- **No Modal Dialogs or Floating Windows:** Screen changes completely replace the active view.

- **Transition Animation:** Horizontal slide duration set to **150 ms**.

- **Rendering Target:** **60 FPS** linear interpolation (`lerp`).
- **Motion Profile:** Strict linear motion—no bounce, no easing overshoot, no decorative flourishes.

---

## 12. Footer Information Bar & Refresh Logic

The persistent footer bar provides system telemetry across all screens:

`DIRT-TOUCH | WiFi | 192.168.1.47 | 10:42`

### Telemetry Update Intervals

To minimize CPU usage on the Pi Zero 2 W:

- **Clock:** Refreshed every **1 second**.
- **WiFi Signal:** Refreshed every **5 seconds**.
- **IP Address:** Refreshed **only on network state change**.

---

## 13. Interactive Terminal & HTOP Execution

When launching interactive CLI environments (`Terminal` or `HTOP`):

1. Pause Pygame display loop and input handler.
2. Execute terminal shell session or target process (`htop`).

3. Upon process exit:

- Perform explicit console cleanup (`clear`).
- Restore tty state (`stty sane` / `termios`).
- Re-initialize Pygame surface and redraw the active screen cleanly.

---

## 14. Error Handling & Recovery Screen

If an application script fails to launch, crashes, or returns a non-zero exit code, DIRT-TOUCH must not crash or fail silently.

### Error Workflow

1. Intercept `subprocess` execution errors (e.g., file not found, permission denied `EACCES`, non-zero exit state).
2. Write error details to launcher log.
3. Push the **Application Error Screen** to the state machine.

### Error Screen Layout

```text
┌─────────────────────────────────────────┐
│           APPLICATION FAILED            │
│                                         │
│   Script: run_badhabits.sh              │
│   Status: Permission Denied (EACCES)    │
│   Exit Code: 126                        │
│                                         │
│               [  BACK  ]                │
└─────────────────────────────────────────┘

```

Selecting `[ BACK ]` returns the user to the Home screen state safely.

---

## 15. Logging Infrastructure

All runtime activities and exceptions are logged to `logs/launcher.log`.

### Log Record Categories

- **System Lifecycle:** Launcher start, initializations, shutdown/restart events.
- **Discovery Events:** Identified wrapper scripts, parsed metadata, ignored items.
- **Execution Events:** Application process spawn, PID, exit codes.
- **Errors & Exceptions:** Process launch failures, missing execution permissions, network interface drops.

---

## 16. Screen Specifications

### Settings Screen

Exposes administrative diagnostic functions: System Info, WiFi, Config, HTOP, About, Restart Launcher, Back.

### System Information Screen

Structured telemetry fields: Hostname, OS/Kernel, Pi Model, CPU Temp, RAM Usage, Disk Usage, Uptime, IP/MAC Addresses.

### About Screen

Displays launcher build information:

- App Name: `DIRT-TOUCH`
- Version: `v1.0.0`
- Python Version
- Pygame Version
- Git Commit Hash (if deployed in git repository)
- Action: `[ BACK ]` button

### Confirmation Screens

`RESTART` and `SHUTDOWN` buttons trigger dedicated full-screen confirmation prompts (`YES` / `NO`) to prevent unintentional touches.

---

## 17. Scrollable Menus

- The scrollbar remains **strictly decorative** until menu elements exceed visible screen space.
- When active, scrolling supports touch dragging/flicks with large targets while keeping scrollbar tracking synchronized.

---

## 18. Code Organization

```text
dirt-touch/
├── main.py
├── launcher.py
├── logs/
│   └── launcher.log
├── screens/
│   ├── base_screen.py
│   ├── home.py
│   ├── settings.py
│   ├── system_info.py
│   ├── wifi.py
│   ├── config.py
│   ├── error_screen.py
│   ├── confirm_restart.py
│   ├── confirm_shutdown.py
│   └── about.py
├── ui/
│   ├── button.py
│   ├── footer.py
│   ├── scrollbar.py
│   ├── colors.py
│   ├── fonts.py
│   └── animations.py
├── utils/
│   ├── discovery.py
│   ├── network.py
│   ├── system.py
│   ├── process.py
│   └── logger.py
└── assets/
    └── fonts/

```

---

## 19. Performance Goals

- Instant boot to launcher home screen.

- Under 150 ms transition latency.

- Low CPU consumption on Raspberry Pi Zero 2 W during idle state.

- Redraw UI elements only when state changes or dynamic clock updates occur.

---

## 20. Future Expansion

- not defined yet...

## 21. NOTES:

- phase 1 implemented main screen, confirmation screens, error screen, app lauch and exit, shutdown, terminal, PLUS hot corner touch exit for running apps which was out of scope of this document.

- run the main.py with "DEBUG_TOUCH=1 python3 main.py" to log all touch events to l0gs/launcher.log file for debugging touch related issues.

- phase 2 goal: system settings and related screens


## Powered by [**Dirtcake Studio**](https://dirtcakestudio.com)

```text

     +$&X:     ;+:    :X$$;   xXXX$$$$&&
     &&&&&&$  $&&&&  &&&   &  &&&&&&&&&&
     &&&;  &$ :      &&&  $&  &&& &&.&&&
     &&&   $& +&&&&  &&&&&+       &&   X
     &&&& x&$  &&&$ x&& &&&&&&&$ x&&X
     &&&&&&    &&&  &&&   &&&&&X &&&&

      &&&&&$  &&&&&  ;&&&  &&&&: &&&&&&
     &&&&&$  &&$ &&&  &&&+&&&&   &&&
    +&&.    &&&&&&&&  &&&&.      &&&&&
     &&x     &$  &&&x &&&&&&&&& .&&&
     $&&&&&&&    +&&&  && &&&&$  X&&&&&&&
       ;X$x:      XXX  x    +x: Xx+++;.

```

- Website: [https://www.dirtcakestudio.com](https://www.dirtcakestudio.com)
- Instagram: [@dirtcakestudio] (https://www.instagram.com/dirtcakestudio/)
- Twitter / X: [@dirtcakestudio] (https://www.x.com/dirtcakestudio/)
- Behance: [dirtcakestudio] (https://www.behance.net/dirtcakestudio)
- Bluesky: [dirtcakestudio.bsky.social] (https://bsky.app/profile/dirtcakestudio.bsky.social)
- Youtube: [@dirtcakestudio] (https://www.youtube.com/@dirtcakestudio)
