# launcher.py
import os
import sys
import pygame
from screens.home import HomeScreen
from screens.confirm_restart import ConfirmRestartScreen
from screens.confirm_shutdown import ConfirmShutdownScreen
from screens.error_screen import ErrorScreen
from utils.logger import log_info

class Launcher:
    def __init__(self):
        pygame.init()
        self.screen = None
        self.reinit_display()
        self.clock = pygame.time.Clock()
        self.running = True

        # Register screen states
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
        """Re-initializes display surface and hides cursor for appliance kiosk mode."""
        pygame.display.init()
        
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

    def run(self):
        log_info("DIRT-TOUCH launcher started.")
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Target 60 FPS
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # Keyboard shortcuts to exit safely during testing
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