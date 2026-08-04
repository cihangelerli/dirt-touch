# launcher.py
import pygame
import sys
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
        """Re-creates the SDL surface after terminal/console drops."""
        pygame.display.init()
        self.screen = pygame.display.set_mode((640, 480))
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
                else:
                    self.active_screen.handle_event(event)
            
            self.active_screen.update(dt)
            self.active_screen.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit(0)