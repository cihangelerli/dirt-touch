# screens/confirm_restart.py
import pygame

from screens.base_screen import BaseScreen
from ui.button import Button
from ui.colors import COLOR_APP_TEXT, COLOR_BACKGROUND
from ui.fonts import get_font_large
from ui.footer import Footer


class ConfirmRestartScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))

        # Bottom action bar aligned with grid bounds (X=43..583, Y=355..444)
        margin_x = 43
        col_w = 270
        btn_y = 355
        btn_height = 89

        self.btn_cancel = Button(
            rect=pygame.Rect(margin_x, btn_y, col_w, btn_height),
            text="CANCEL",
            style="CANCEL",
            callback=lambda: self.app.switch_screen("home"),
        )
        self.btn_confirm = Button(
            rect=pygame.Rect(margin_x + col_w, btn_y, col_w, btn_height),
            text="RESTART",
            style="SYS",
            callback=lambda: self.app.system_restart(),
        )
        self.buttons = [self.btn_cancel, self.btn_confirm]

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def update(self, dt: float):
        self.footer.update(dt)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font = get_font_large()

        # Top-right header title
        header_surf = font.render("CONFIRM RESTART", True, COLOR_APP_TEXT)
        surface.blit(header_surf, (597 - header_surf.get_width(), 42))

        # Horizontal accent line (line_y = 100)
        pygame.draw.line(surface, COLOR_APP_TEXT, (43, 100), (597, 100), 2)

        # Body prompt lines
        line1_surf = font.render(
            "> THE DEVICE WILL BE RESTARTED,", True, COLOR_APP_TEXT
        )
        line2_surf = font.render("> DO YOU WANT TO PROCEED?", True, COLOR_APP_TEXT)

        surface.blit(line1_surf, (68, 200))
        surface.blit(line2_surf, (68, 242))

        # Bottom buttons & footer
        for btn in self.buttons:
            btn.draw(surface)

        self.footer.draw(surface)
