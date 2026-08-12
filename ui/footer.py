# ui/footer.py
import time

import pygame

from ui.colors import COLOR_FOOTER_BG, COLOR_MUTED_BROWN, COLOR_TEXT_ORANGE
from ui.fonts import get_font_small
from utils.network import get_ip_address, get_wifi_signal


class Footer:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.last_clock_update = 0.0
        self.last_telemetry_update = 0.0

        self.clock_str = ""
        self.wifi_raw = "WiFi _____"
        self.ip_str = get_ip_address()
        self.version_prefix = "DIRT-TOUCH"
        self.version_suffix = "-v1.2"

    def update(self, dt: float):
        now = time.time()

        # Clock updates every 1.0 second
        if now - self.last_clock_update >= 1.0:
            self.clock_str = time.strftime("%H:%M")
            self.last_clock_update = now

        # Network telemetry (WiFi signal & IP) updates every 10.0 seconds
        if now - self.last_telemetry_update >= 10.0:
            self.wifi_raw = get_wifi_signal()
            self.ip_str = get_ip_address()
            self.last_telemetry_update = now

    def _get_active_wifi_count(self) -> int:
        if "????? " in self.wifi_raw or "?" in self.wifi_raw:
            return 0  # Return 0 bars on error/unknown state
        if "IIIII" in self.wifi_raw:
            return 5
        if "IIII" in self.wifi_raw:
            return 4
        if "III" in self.wifi_raw:
            return 3
        if "II" in self.wifi_raw:
            return 2
        if "I" in self.wifi_raw:
            return 1
        return 0  # Default to 0 if no known pattern is found

    def draw(self, surface: pygame.Surface):
        # Dark brown footer fill (#28160A)
        surface.fill(COLOR_FOOTER_BG, self.rect)

        # Orange top divider line (#FF7700)
        pygame.draw.line(
            surface,
            COLOR_TEXT_ORANGE,
            (self.rect.left, self.rect.top),
            (self.rect.right, self.rect.top),
            1,
        )

        font = get_font_small()
        padding = 10
        cy = self.rect.centery

        # 1. Version String (Left): "DIRT-TOUCH" in orange, "-v0.3" in muted brown
        prefix_surf = font.render(self.version_prefix, True, COLOR_TEXT_ORANGE)
        suffix_surf = font.render(self.version_suffix, True, COLOR_MUTED_BROWN)

        x_pos = self.rect.left + padding + 40
        surface.blit(prefix_surf, (x_pos, cy - prefix_surf.get_height() // 2))
        x_pos += prefix_surf.get_width()
        surface.blit(suffix_surf, (x_pos, cy - suffix_surf.get_height() // 2))

        # 2. WiFi signal section (Middle Left)
        wifi_lbl = font.render("WiFi ", True, COLOR_MUTED_BROWN)
        wifi_x = self.rect.left + 170 + 40
        surface.blit(wifi_lbl, (wifi_x, cy - wifi_lbl.get_height() // 2))

        bars_start_x = wifi_x + wifi_lbl.get_width()
        active_count = self._get_active_wifi_count()
        bar_w, bar_h, bar_gap = 4, 11, 2

        for i in range(5):
            bx = bars_start_x + i * (bar_w + bar_gap)
            by = cy - bar_h // 2
            bar_rect = pygame.Rect(bx, by, bar_w, bar_h)
            if i < active_count:
                surface.fill(COLOR_TEXT_ORANGE, bar_rect)
            else:
                pygame.draw.rect(surface, COLOR_MUTED_BROWN, bar_rect, width=1)

        # 3. IP Address (Middle Right in #A55412 muted brown)
        ip_surf = font.render(self.ip_str, True, COLOR_MUTED_BROWN)
        ip_x = self.rect.right - 180 - 50
        surface.blit(ip_surf, (ip_x, cy - ip_surf.get_height() // 2))

        # 4. Clock (Right in #A55412 muted brown)
        clock_surf = font.render(self.clock_str, True, COLOR_MUTED_BROWN)
        surface.blit(
            clock_surf,
            (
                self.rect.right - clock_surf.get_width() - padding - 50,
                cy - clock_surf.get_height() // 2,
            ),
        )
