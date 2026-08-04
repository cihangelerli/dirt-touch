# screens/confirm_shutdown.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.colors import COLOR_BACKGROUND, COLOR_TEXT_ORANGE
from ui.fonts import get_font_large
from utils.system import execute_shutdown

class ConfirmShutdownScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        
        self.btn_cancel = Button(
            rect=pygame.Rect(42, 360, 276, 84),
            text="CANCEL",
            style="CANCEL",
            callback=lambda: self.app.switch_screen("home")
        )
        self.btn_confirm = Button(
            rect=pygame.Rect(321, 360, 276, 84),
            text="SHUTDOWN",
            style="SYS",
            callback=execute_shutdown
        )

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.btn_cancel.handle_event(event)
        self.btn_confirm.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font = get_font_large()

        # Header right-aligned
        hdr_surf = font.render("CONFIRM SHUTDOWN", True, COLOR_TEXT_ORANGE)
        surface.blit(hdr_surf, (640 - hdr_surf.get_width() - 42, 30))

        # Divider line
        pygame.draw.line(surface, COLOR_TEXT_ORANGE, (42, 70), (597, 70), 2)

        # Prompts
        line1 = font.render("> THE DEVICE WILL BE SHUTDOWN,", True, COLOR_TEXT_ORANGE)
        line2 = font.render("> DO YOU WANT TO PROCEED?", True, COLOR_TEXT_ORANGE)
        surface.blit(line1, (68, 170))
        surface.blit(line2, (68, 210))

        # Action Buttons
        self.btn_cancel.draw(surface)
        self.btn_confirm.draw(surface)
        
        self.footer.draw(surface)