import os
import sys

import pygame
from pygame._sdl2.video import Renderer, Texture, Window

from screens.confirm_keyboard import ConfirmKeyboardScreen
from screens.confirm_restart import ConfirmRestartScreen
from screens.confirm_shutdown import ConfirmShutdownScreen
from screens.error_screen import ErrorScreen
from screens.home import HomeScreen
from screens.system_info import SystemInfoScreen
from screens.system_settings import SystemSettingsScreen
from ui.colors import COLOR_BACKGROUND
from ui.fonts import reset_fonts
from utils.logger import log_info
from utils.process import run_application

# KMSDRM display positioning masks
POS_DISPLAY_0 = (0x1FFF0000 | 0, 0x1FFF0000 | 0)
POS_DISPLAY_1 = (0x1FFF0000 | 1, 0x1FFF0000 | 1)


class Launcher:
    def __init__(self):
        pygame.init()
        self.screen = None
        self.reinit_display()
        self.clock = pygame.time.Clock()
        self.running = True

        self.screens = {
            "home": HomeScreen(self),
            "confirm_restart": ConfirmRestartScreen(self),
            "confirm_shutdown": ConfirmShutdownScreen(self),
            "confirm_keyboard": ConfirmKeyboardScreen(self),
            "error": ErrorScreen(self),
            "system_info": SystemInfoScreen(self),
            "system_settings": SystemSettingsScreen(self),
        }

        self.active_screen_name = "home"
        self.active_screen = self.screens[self.active_screen_name]
        self.active_screen.enter()

    def destroy_windows(self):
        """Explicitly destroys SDL2 windows to free DRM Master on /dev/dri/card0."""
        if hasattr(self, "win_hdmi") and self.win_hdmi:
            try:
                self.win_hdmi.destroy()
            except Exception:
                pass
            self.win_hdmi = None
            self.renderer_hdmi = None
            self.tex_hdmi = None

        if hasattr(self, "win_dpi") and self.win_dpi:
            try:
                self.win_dpi.destroy()
            except Exception:
                pass
            self.win_dpi = None
            self.renderer_dpi = None
            self.tex_dpi = None

    def reinit_display(self):
        """Re-initializes display windows, renderers, canvas, font cache, and flushes event queue."""
        pygame.display.init()
        pygame.font.init()
        reset_fonts()
        self.clock = pygame.time.Clock()

        # Canvas surface for screens to draw onto
        self.canvas = pygame.Surface((640, 480))
        self.screen = self.canvas  # Maintains 100% compatibility with screen classes
        self.src_rect = pygame.Rect(0, 0, 640, 480)

        # 1. Primary DPI Display (Index 0)
        self.win_dpi = Window(
            "DIRT-TOUCH Launcher",
            size=(640, 480),
            position=POS_DISPLAY_0,
            fullscreen=True,
        )
        self.renderer_dpi = Renderer(self.win_dpi)
        self.tex_dpi = Texture(self.renderer_dpi, (640, 480), streaming=True)

        # 2. Secondary HDMI Display Probe & Full-Bleed Setup (Index 1)
        self.win_hdmi = None
        self.renderer_hdmi = None
        self.tex_hdmi = None
        self.hdmi_dst_rect = None
        self.hdmi_active = False

        try:
            sizes = pygame.display.get_desktop_sizes()
            if len(sizes) > 1:
                hdmi_w, hdmi_h = sizes[1]
                self.win_hdmi = Window(
                    "HDMI-Mirror",
                    size=(hdmi_w, hdmi_h),
                    position=POS_DISPLAY_1,
                    fullscreen=True,
                )
                self.renderer_hdmi = Renderer(self.win_hdmi)
                self.tex_hdmi = Texture(self.renderer_hdmi, (640, 480), streaming=True)
                self.hdmi_dst_rect = pygame.Rect(0, 0, hdmi_w, hdmi_h)
                self.hdmi_active = True
                log_info(
                    f"HDMI mirror initialized: Stretching 640x480 -> {hdmi_w}x{hdmi_h}"
                )
            else:
                log_info("Single display detected (DPI only)")
        except Exception as e:
            log_info(f"HDMI mirror initialization failed: {e}")
            self.hdmi_active = False

        pygame.mouse.set_visible(False)

        # Flush buffered events accrued during launch or initialization
        pygame.event.pump()
        pygame.event.clear()

    def render_displays(self):
        """Streams canvas contents out to DPI and HDMI displays."""
        # Render Primary (DPI)
        self.tex_dpi.update(self.canvas)
        self.renderer_dpi.clear()
        self.renderer_dpi.blit(self.tex_dpi, self.src_rect, self.src_rect)
        self.renderer_dpi.present()

        # Render Secondary (HDMI Full-Bleed)
        if self.hdmi_active and self.renderer_hdmi and self.tex_hdmi:
            try:
                self.tex_hdmi.update(self.canvas)
                self.renderer_hdmi.clear()
                self.renderer_hdmi.blit(
                    self.tex_hdmi, self.src_rect, self.hdmi_dst_rect
                )
                self.renderer_hdmi.present()
            except Exception as e:
                log_info(f"HDMI frame render error, disabling HDMI output: {e}")
                self.hdmi_active = False

    def switch_screen(self, screen_name: str, **kwargs):
        if screen_name in self.screens:
            log_info(f"Navigating to screen: {screen_name}")
            self.active_screen.exit()
            self.active_screen_name = screen_name
            self.active_screen = self.screens[screen_name]

            if screen_name == "error" and kwargs:
                self.active_screen.set_error_details(
                    kwargs.get("script", ""),
                    kwargs.get("status", ""),
                    kwargs.get("code", 0),
                )
            elif screen_name == "confirm_keyboard" and kwargs:
                self.active_screen.set_target_script(kwargs.get("script", ""))

            self.active_screen.enter()
            pygame.event.clear()

    def launch_app(self, script_path: str):
        """Single-owner process launch handling DRM release, execution, font rebuild, and error routing."""
        log_info(f"Launcher managing execution for: {script_path}")

        # 1. Relinquish DRM Master / shut down Pygame completely
        self.destroy_windows()
        pygame.display.quit()
        pygame.quit()

        # 2. Run application via utils.process
        success, err_msg, exit_code = run_application(script_path)

        # 3. Re-acquire DRM Master and rebuild display + font cache
        pygame.init()
        self.reinit_display()

        # 4. Route state
        if not success:
            self.switch_screen(
                "error", script=script_path, status=err_msg, code=exit_code
            )
        else:
            self.active_screen.enter()

    def launch_terminal(self):
        """Single-owner terminal launcher handling DRM release and terminal session."""
        log_info("Releasing DRM/VT for Terminal session...")

        script_path = os.path.expanduser("~/terminal.sh")
        self.launch_app(script_path)

    def release_display_for_app(self):
        """Rebinds fbcon and restores tty1 state BEFORE launching external terminal tools."""
        self.destroy_windows()
        pygame.display.quit()
        pygame.quit()

        os.system("echo 1 | sudo tee /sys/class/vtconsole/vtcon1/bind >/dev/null 2>&1")
        os.system("sudo kbd_mode -a -C /dev/tty1 2>/dev/null")
        os.system("sudo chvt 1 2>/dev/null")
        os.system(
            "export TERM=linux; setterm -reset -blank 0 -powerdown 0 -clear all > /dev/tty1 2>&1"
        )

    def restart_dirt_touch_service(self):
        """Cleanly quits Pygame KMSDRM and schedules an asynchronous service restart."""
        log_info("Restarting dirt-touch service...")

        # 1. Release KMSDRM framebuffer lock cleanly without forcing fbcon rebind
        self.destroy_windows()
        pygame.display.quit()
        pygame.quit()

        # 2. Issue an asynchronous systemd restart request
        os.system(
            "sudo systemctl daemon-reload && sudo systemctl restart --no-block dirt-touch.service"
        )

        # 3. Exit process cleanly
        sys.exit(0)

    def system_restart(self):
        """Rebinds fbcon to DRM plane via VT switch, cleanly exits Python, and reboots."""
        log_info("System restart initiated. Rebinding fbcon to DRM pipeline...")

        # 1. Shut down Pygame subsystems
        self.destroy_windows()
        pygame.display.quit()
        pygame.quit()

        # 2. Re-attach kernel framebuffer console to VT1 and restore text mode
        os.system("sudo chvt 1 2>/dev/null")
        os.system("sudo kbd_mode -a 2>/dev/null")
        os.system("setterm -blank 0 -powerdown 0 -clear all > /dev/tty1 2>&1")

        # 3. Trigger clean system reboot and exit launcher process
        os.system("sudo systemctl reboot")
        sys.exit(0)

    def system_shutdown(self):
        """Rebinds fbcon to DRM plane via VT switch, cleanly exits Python, and powers off."""
        log_info("System shutdown initiated. Rebinding fbcon to DRM pipeline...")

        self.destroy_windows()
        pygame.display.quit()
        pygame.quit()

        os.system("sudo chvt 1 2>/dev/null")
        os.system("sudo kbd_mode -a 2>/dev/null")
        os.system("setterm -blank 0 -powerdown 0 -clear all > /dev/tty1 2>&1")

        os.system("sudo systemctl poweroff")
        sys.exit(0)

    def run(self):
        log_info("DIRT-TOUCH launcher started.")
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        log_info("Exit keyboard shortcut pressed.")
                        self.running = False
                    elif event.key == pygame.K_c and (event.mod & pygame.KMOD_CTRL):
                        self.running = False
                else:
                    self.active_screen.handle_event(event)

            self.active_screen.update(dt)

            # Clear background every frame onto shared canvas
            self.canvas.fill(COLOR_BACKGROUND)
            self.active_screen.draw(self.canvas)

            # Stream canvas out to active DPI & HDMI renderers
            self.render_displays()

        self.destroy_windows()
        pygame.quit()
        sys.exit(0)
