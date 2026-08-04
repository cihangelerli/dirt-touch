# ui/footer.py
import time
import pygame
from ui.colors import COLOR_BACKGROUND, COLOR_BORDER, COLOR_TEXT_ORANGE
from ui.fonts import get_font_small
from utils.network import get_ip_address, get_wifi_signal

class Footer:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.last_clock_update = 0.0
        self.last_telemetry_update = 0.0
        
        self.clock_str = ""
        self.wifi_str = "WiFi IIIII"
        self.ip_str = get_ip_address()
        self.version_str = "DIRT-TOUCH-v1.0"

    def update(self, dt: float):
        now = time.time()
        
        # Clock updates every 1.0 second
        if now - self.last_clock_update >= 1.0:
            self.clock_str = time.strftime("%H:%M")
            self.last_clock_update = now
            
        # Network telemetry (WiFi signal & IP) updates every 10.0 seconds
        if now - self.last_telemetry_update >= 10.0:
            self.wifi_str = get_wifi_signal()
            self.ip_str = get_ip_address()
            self.last_telemetry_update = now

    def draw(self, surface: pygame.Surface):
        surface.fill(COLOR_BACKGROUND, self.rect)
        pygame.draw.line(surface, COLOR_TEXT_ORANGE, (self.rect.left, self.rect.top), (self.rect.right, self.rect.top), 1)

        font = get_font_small()
        padding = 10

        # Version string (Left)
        ver_surf = font.render(self.version_str, True, COLOR_TEXT_ORANGE)
        surface.blit(ver_surf, (self.rect.left + padding, self.rect.centery - ver_surf.get_height() // 2))

        # WiFi string (Left-Center)
        wifi_surf = font.render(self.wifi_str, True, COLOR_TEXT_ORANGE)
        surface.blit(wifi_surf, (self.rect.left + 160, self.rect.centery - wifi_surf.get_height() // 2))

        # IP Address (Right-Center)
        ip_surf = font.render(self.ip_str, True, COLOR_TEXT_ORANGE)
        surface.blit(ip_surf, (self.rect.right - 180, self.rect.centery - ip_surf.get_height() // 2))

        # Clock (Right)
        clock_surf = font.render(self.clock_str, True, COLOR_TEXT_ORANGE)
        surface.blit(clock_surf, (self.rect.right - clock_surf.get_width() - padding, self.rect.centery - clock_surf.get_height() // 2))
