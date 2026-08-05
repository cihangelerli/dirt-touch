# screens/error_screen.py
import pygame
from screens.base_screen import BaseScreen
from ui.button import Button
from ui.footer import Footer
from ui.colors import COLOR_BACKGROUND, COLOR_TEXT_ORANGE, COLOR_MUTED_BROWN
from ui.fonts import get_font_large

class ErrorScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        self.script_path = "EXAMPLE SCRIPT NAME\nEXAMPLE SCRIPT NAME CONTINUED"
        self.status = "SOME STATUS MESSAGE\nSOME STATUS MESSAGE CONTINUED"
        self.exit_code = "CODE\nCODE CONTINUED"
        
        # Bottom-right cell button (X=313, Y=355, W=270, H=89)
        margin_x = 43
        col_w = 270
        btn_y = 355
        btn_height = 89
        
        self.btn_back = Button(
            rect=pygame.Rect(margin_x + col_w, btn_y, col_w, btn_height),
            text="BACK",
            style="SYS",
            callback=lambda: self.app.switch_screen("home")
        )

    def set_error_details(self, script: str, status: str, code: int):
        self.script_path = script.upper() if script else "N/A"
        self.status = status.upper() if status else "UNKNOWN FAILURE"
        self.exit_code = str(code).upper()

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.btn_back.handle_event(event)

    def _render_multiline_right(self, surface: pygame.Surface, text: str, font: pygame.font.Font, right_x: int, start_y: int) -> int:
        """Renders multi-line text right-aligned at right_x in #A55412 muted brown."""
        lines = str(text).split("\n")
        current_y = start_y
        for line in lines:
            if not line:
                continue
            surf = font.render(line, True, COLOR_MUTED_BROWN)
            surface.blit(surf, (right_x - surf.get_width(), current_y))
            current_y += surf.get_height() + 2
        return current_y

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font = get_font_large()

        # 1. Top-right header title: "!! APPLICATION FAILED" in #FF7700 orange
        header_surf = font.render("!! APPLICATION FAILED", True, COLOR_TEXT_ORANGE)
        surface.blit(header_surf, (597 - header_surf.get_width(), 42))

        # 2. Orange horizontal divider line at y = 100
        pygame.draw.line(surface, COLOR_TEXT_ORANGE, (43, 100), (597, 100), 2)

        # 3. Diagnostic Key Labels (Left-aligned at x=43 in #FF7700 orange)
        lbl_script = font.render("SCRIPT", True, COLOR_TEXT_ORANGE)
        lbl_status = font.render("STATUS", True, COLOR_TEXT_ORANGE)
        lbl_code   = font.render("EXIT CODE", True, COLOR_TEXT_ORANGE)

        surface.blit(lbl_script, (43, 140))
        surface.blit(lbl_status, (43, 215))
        surface.blit(lbl_code,   (43, 290))

        # 4. Diagnostic Values (Right-aligned at x=597 in #A55412 muted brown)
        self._render_multiline_right(surface, self.script_path, font, 597, 140)
        self._render_multiline_right(surface, self.status, font, 597, 215)
        self._render_multiline_right(surface, self.exit_code, font, 597, 290)

        # 5. Bottom-right BACK button & footer
        self.btn_back.draw(surface)
        self.footer.draw(surface)