# launcher.py
import os
import sys
import pygame
from screens.home import HomeScreen
from screens.confirm_restart import ConfirmRestartScreen
from screens.confirm_shutdown import ConfirmShutdownScreen
from screens.error_screen import ErrorScreen
from ui.fonts import reset_fonts
from utils.logger import log_info
from utils.process import run_application, run_terminal_session

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
            "error": ErrorScreen(self)
        }
        
        self.active_screen_name = "home"
        self.active_screen = self.screens[self.active_screen_name]
        self.active_screen.enter()

    def reinit_display(self):
        """Re-initializes display surface, font cache, and hides cursor."""
        pygame.display.init()
        pygame.font.init()
        reset_fonts()
        
        flags = 0
        if os.environ.get("SDL_VIDEODRIVER") == "kmsdrm":
            flags |= pygame.FULLSCREEN

        self.screen = pygame.display.set_mode((640, 480), flags)
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("DIRT-TOUCH Launcher")

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
                    kwargs.get("code", 0)
                )
                
            self.active_screen.enter()

    def launch_app(self, script_path: str):
        """Single-owner process launch handling DRM release, execution, font rebuild, and error routing."""
        log_info(f"Launcher managing execution for: {script_path}")

        # 1. Relinquish DRM Master / shut down Pygame completely
        pygame.display.quit()
        pygame.quit()

        # 2. Run application via utils.process
        success, err_msg, exit_code = run_application(script_path)

        # 3. Re-acquire DRM Master and rebuild display + font cache
        pygame.init()
        self.reinit_display()

        # 4. Route state
        if not success:
            self.switch_screen("error", script=script_path, status=err_msg, code=exit_code)
        else:
            self.active_screen.enter()

    def launch_terminal(self):
        """Single-owner terminal launcher handling DRM release and terminal session."""
        pygame.display.quit()
        pygame.quit()

        run_terminal_session()

        pygame.init()
        self.reinit_display()
        self.active_screen.enter()

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
            self.active_screen.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)