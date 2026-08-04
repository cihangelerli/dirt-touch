# screens/error_screen.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.colors import COLOR_BACKGROUND, COLOR_TEXT_ORANGE
from ui.fonts import get_font_large, get_font_small

class ErrorScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        self.script_path = ""
        self.status = ""
        self.exit_code = 0
        
        self.btn_back = Button(
            rect=pygame.Rect(220, 340, 200, 60),
            text="BACK",
            style="SYS",
            callback=lambda: self.app.switch_screen("home")
        )

    def set_error_details(self, script: str, status: str, code: int):
        self.script_path = script
        self.status = status
        self.exit_code = code

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.btn_back.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font_large = get_font_large()
        font_small = get_font_small()

        # Title
        title_surf = font_large.render("APPLICATION FAILED", True, COLOR_TEXT_ORANGE)
        surface.blit(title_surf, (320 - title_surf.get_width() // 2, 50))

        # Error diagnostics block
        t_script = font_small.render(f"Script: {self.script_path}", True, COLOR_TEXT_ORANGE)
        t_status = font_small.render(f"Status: {self.status}", True, COLOR_TEXT_ORANGE)
        t_code   = font_small.render(f"Exit Code: {self.exit_code}", True, COLOR_TEXT_ORANGE)

        surface.blit(t_script, (80, 150))
        surface.blit(t_status, (80, 190))
        surface.blit(t_code,   (80, 230))

        self.btn_back.draw(surface)
        self.footer.draw(surface)