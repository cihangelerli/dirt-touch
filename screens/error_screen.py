# screens/error_screen.py
import pygame

from screens.base_screen import BaseScreen
from ui.button import Button
from ui.colors import COLOR_BACKGROUND, COLOR_MUTED_BROWN, COLOR_TEXT_ORANGE
from ui.fonts import get_font_large
from ui.footer import Footer


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
            callback=lambda: self.app.switch_screen("home"),
        )

    def set_error_details(self, script: str, status: str, code: int):
        self.script_path = script.upper() if script else "N/A"
        self.status = status.upper() if status else "UNKNOWN FAILURE"
        self.exit_code = str(code).upper()

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.btn_back.handle_event(event)

    def _render_wrapped_right(
        self,
        surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        right_x: int,
        start_y: int,
        max_width: int = 554,
    ) -> int:
        """Word-wraps and right-aligns text to fit within max_width (x=43 to x=597)."""
        current_y = start_y
        raw_lines = str(text).split("\n")
        for raw_line in raw_lines:
            words = raw_line.split(" ")
            curr_line = ""
            for word in words:
                test_line = f"{curr_line} {word}".strip()
                if font.size(test_line)[0] > max_width and curr_line:
                    surf = font.render(curr_line, True, COLOR_MUTED_BROWN)
                    surface.blit(surf, (right_x - surf.get_width(), current_y))
                    current_y += surf.get_height() + 2
                    curr_line = word
                else:
                    curr_line = test_line
            if curr_line:
                surf = font.render(curr_line, True, COLOR_MUTED_BROWN)
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
        lbl_code = font.render("EXIT CODE", True, COLOR_TEXT_ORANGE)

        curr_y = 125

        # surface.blit(lbl_script, (43, 140))
        # A. Script section
        surface.blit(lbl_script, (43, curr_y))
        curr_y = (
            self._render_wrapped_right(surface, self.script_path, font, 597, curr_y)
            + 12
        )

        # surface.blit(lbl_status, (43, 215))
        # B. Status section
        surface.blit(lbl_status, (43, curr_y))
        curr_y = (
            self._render_wrapped_right(surface, self.status, font, 597, curr_y) + 12
        )

        # surface.blit(lbl_code, (43, 290))
        # C. Exit code section
        surface.blit(lbl_code, (43, curr_y))
        curr_y = (
            self._render_wrapped_right(surface, self.exit_code, font, 597, curr_y) + 24
        )


        # 5. Bottom-right BACK button & footer
        self.btn_back.draw(surface)
        self.footer.draw(surface)
