# screens/confirm_restart.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.fonts import get_font_large
from ui.colors import COLOR_SYS_BG

class ConfirmRestartScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        
        # Grid placement matching design specs
        col_w = 300
        row_h = 88.8
        
        self.btn_confirm = Button(
            rect=pygame.Rect(0, int(3 * row_h), col_w, int(row_h)),
            text="CONFIRM RESTART",
            style="SYS",
            callback=lambda: self.app.system_restart()
        )
        self.btn_cancel = Button(
            rect=pygame.Rect(col_w, int(3 * row_h), col_w, int(row_h)),
            text="CANCEL",
            style="CANCEL",
            callback=lambda: self.app.switch_screen("home")
        )
        self.buttons = [self.btn_confirm, self.btn_cancel]

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float):
        self.footer.update(dt)

    def draw(self, surface: pygame.Surface):
        # Draw system warning prompt text
        font = get_font_large()
        text_surf = font.render("RESTART SYSTEM?", True, COLOR_SYS_BG)
        surface.blit(text_surf, (40, 100))
        
        for btn in self.buttons:
            btn.draw(surface)
            
        self.footer.draw(surface)