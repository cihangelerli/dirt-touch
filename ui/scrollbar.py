# ui/scrollbar.py
import pygame
from ui.colors import (
    COLOR_SCROLLBAR_BG,
    COLOR_SCROLLBAR_THUMB,
    COLOR_SCROLLBAR_INACTIVE,
    COLOR_BORDER
)

class Scrollbar:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.active = False
        self.thumb_ratio = 0.25
        self.scroll_ratio = 0.0  # 0.0 to 1.0

    def set_scroll_state(self, total_items: int, max_visible: int, current_offset: float):
        if total_items > max_visible:
            self.active = True
            self.thumb_ratio = max(0.15, min(1.0, max_visible / float(total_items)))
            max_scroll = total_items - max_visible
            self.scroll_ratio = max(0.0, min(1.0, current_offset / float(max_scroll)))
        else:
            self.active = False
            self.thumb_ratio = 1.0
            self.scroll_ratio = 0.0

    def draw(self, surface: pygame.Surface):
        # 1. Dark track background (#28160A)
        surface.fill(COLOR_SCROLLBAR_BG, self.rect)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=1)
        
        # 2. Compute thumb position
        track_h = self.rect.height
        thumb_h = int(track_h * self.thumb_ratio)
        available_travel = track_h - thumb_h
        thumb_y = self.rect.y + int(available_travel * self.scroll_ratio)
        
        thumb_rect = pygame.Rect(
            self.rect.x,
            thumb_y,
            self.rect.width,
            thumb_h
        )
        
        # 3. Thumb color: bright orange (#FF7700) when active, dark brown (#381A08) when inactive
        thumb_color = COLOR_SCROLLBAR_THUMB if self.active else COLOR_SCROLLBAR_INACTIVE
        surface.fill(thumb_color, thumb_rect)
        pygame.draw.rect(surface, COLOR_BORDER, thumb_rect, width=1)