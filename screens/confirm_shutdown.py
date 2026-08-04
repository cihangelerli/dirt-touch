# screens/confirm_shutdown.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.fonts import get_font_large
from ui.colors import COLOR_APP_TEXT, COLOR_BORDER

class ConfirmShutdownScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        
        # Bottom action bar (Row 4: Y=355.2 to Y=444)
        col_w = 300
        row_h = 88.8
        btn_y = int(4 * row_h)
        btn_height = int(row_h)

        self.btn_cancel = Button(
            rect=pygame.Rect(0, btn_y, col_w, btn_height),
            text="CANCEL",
            style="CANCEL",
            callback=lambda: self.app.switch_screen("home")
        )
        self.btn_confirm = Button(
            rect=pygame.Rect(col_w, btn_y, col_w, btn_height),
            text="SHUTDOWN",
            style="SYS",
            callback=lambda: self.app.system_shutdown()
        )
        self.buttons = [self.btn_cancel, self.btn_confirm]

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float):
        self.footer.update(dt)

    def draw(self, surface: pygame.Surface):
        font = get_font_large()

        # Top-right header title
        header_surf = font.render("CONFIRM SHUTDOWN", True, COLOR_APP_TEXT)
        surface.blit(header_surf, (640 - header_surf.get_width() - 43, 40))

        # Horizontal accent line
        pygame.draw.line(surface, COLOR_APP_TEXT, (43, 100), (597, 100), 2)

        # Body prompt lines
        line1_surf = font.render("> THE DEVICE WILL BE SHUTDOWN,", True, COLOR_APP_TEXT)
        line2_surf = font.render("> DO YOU WANT TO PROCEED?", True, COLOR_APP_TEXT)
        
        surface.blit(line1_surf, (68, 200))
        surface.blit(line2_surf, (68, 242))

        # Bottom buttons & footer
        for btn in self.buttons:
            btn.draw(surface)
            
        self.footer.draw(surface)