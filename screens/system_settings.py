import os

import pygame

from screens.base_screen import BaseScreen
from ui.button import Button
from ui.colors import COLOR_BACKGROUND, COLOR_TEXT_ORANGE
from ui.fonts import get_font_large
from ui.footer import Footer


class SystemSettingsScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))
        self.buttons = []
        self.build_grid()

    def build_grid(self):
        self.buttons.clear()
        margin_x = 43
        col_w = 277
        start_y = 108
        row_h = 84

        shortcuts_dir = os.path.expanduser("~/dirt-touch/system_screen_shortcuts")

        items = [
            # Row 0
            # ("SYSTEM INFO", "APP", lambda: self.app.switch_screen("system_info")),
            (
                "WiFi",
                "APP",
                lambda: self.app.launch_app(os.path.join(shortcuts_dir, "wifi.sh")),
            ),
            (
                "GIT PULL",
                "APP",
                lambda: self.app.launch_app(os.path.join(shortcuts_dir, "git_pull.sh")),
            ),
            # Row 1
            (
                "CONFIG.TXT",
                "APP",
                lambda: self.app.switch_screen(
                    "confirm_keyboard",
                    script=os.path.join(shortcuts_dir, "config.sh"),
                ),
            ),
            (
                "CMNDLINE.TXT",
                "APP",
                lambda: self.app.switch_screen(
                    "confirm_keyboard",
                    script=os.path.join(shortcuts_dir, "cmdline.sh"),
                ),
            ),
            # Row 2
            (
                "HTOP",
                "APP",
                lambda: self.app.launch_app(os.path.join(shortcuts_dir, "htop.sh")),
            ),
            (
                "UPDATE ALL",
                "APP",
                lambda: self.app.launch_app(
                    os.path.join(shortcuts_dir, "update_all.sh")
                ),
            ),
            # Row 3
            (
                "RESTART\nDIRT-TOUCH",
                "APP",
                lambda: self.app.restart_dirt_touch_service(),
            ),
            ("BACK", "SYS", lambda: self.app.switch_screen("home")),
        ]

        for i, (text, style, cb) in enumerate(items):
            r = i // 2
            c = i % 2
            rect = pygame.Rect(margin_x + c * col_w, start_y + r * row_h, col_w, row_h)
            btn = Button(rect=rect, text=text, style=style, callback=cb)
            self.buttons.append(btn)

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buttons:
            if btn.handle_event(event):
                break

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font = get_font_large()

        # 1. Top-right header title: "// SYSTEM SETTINGS"
        header_surf = font.render("// SYSTEM SETTINGS", True, COLOR_TEXT_ORANGE)
        surface.blit(header_surf, (597 - header_surf.get_width(), 42))

        # 2. Orange horizontal divider line at y = 100
        pygame.draw.line(surface, COLOR_TEXT_ORANGE, (43, 100), (597, 100), 2)

        # 3. Draw grid buttons & footer
        for btn in self.buttons:
            btn.draw(surface)

        self.footer.draw(surface)
