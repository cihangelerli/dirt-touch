# screens/system_info.py
import pygame

from screens.base_screen import BaseScreen
from ui.button import Button
from ui.colors import COLOR_BACKGROUND, COLOR_MUTED_BROWN, COLOR_TEXT_ORANGE
from ui.fonts import get_font_large
from ui.footer import Footer
from utils.network import get_ip_address
from utils.system import (
    get_cpu_temp,
    get_disk_usage,
    get_hostname,
    get_mac_address,
    get_os_kernel,
    get_pi_model,
    get_ram_usage,
    get_uptime,
)


class SystemInfoScreen(BaseScreen):
    def __init__(self, app_state_manager):
        super().__init__(app_state_manager)
        self.footer = Footer(pygame.Rect(0, 444, 640, 36))

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

    def update(self, dt: float):
        self.footer.update(dt)

    def handle_event(self, event: pygame.event.Event):
        self.btn_back.handle_event(event)

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND)
        font = get_font_large()

        # 1. Top-right header title: "// SYSTEM INFO" in #FF7700 orange
        header_surf = font.render("// SYSTEM INFO", True, COLOR_TEXT_ORANGE)
        surface.blit(header_surf, (597 - header_surf.get_width(), 42))

        # 2. Orange horizontal divider line at y = 100
        pygame.draw.line(surface, COLOR_TEXT_ORANGE, (43, 100), (597, 100), 2)

        # 3. System info data fields
        fields = [
            ("HOSTNAME", get_hostname().upper()),
            ("PI MODEL", get_pi_model().upper()),
            ("OS / KERNEL", get_os_kernel().upper()),
            ("MAC ADDRESS", get_mac_address().upper()),
            ("IP", get_ip_address().upper()),
            ("UPTIME", get_uptime().upper()),
            ("DISK USAGE", get_disk_usage().upper()),
            ("CPU TEMP", get_cpu_temp().upper()),
            ("RAM USAGE", get_ram_usage().upper()),
        ]

        start_y = 115
        row_gap = 24

        for i, (label, val) in enumerate(fields):
            curr_y = start_y + i * row_gap
            # Left key label in #FF7700 orange
            lbl_surf = font.render(label, True, COLOR_TEXT_ORANGE)
            surface.blit(lbl_surf, (43, curr_y))

            # Right value in #A55412 muted brown
            val_surf = font.render(val, True, COLOR_MUTED_BROWN)
            surface.blit(val_surf, (597 - val_surf.get_width(), curr_y))

        # 4. Bottom-right BACK button & footer
        self.btn_back.draw(surface)
        self.footer.draw(surface)
