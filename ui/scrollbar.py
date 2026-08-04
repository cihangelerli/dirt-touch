# ui/scrollbar.py
import pygame
from ui.colors import COLOR_SCROLLBAR_BG, COLOR_SCROLLBAR_THUMB

class Scrollbar:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface):
        # Decorative track
        surface.fill(COLOR_SCROLLBAR_BG, self.rect)
        
        # Thumb indicator matching mockup position
        thumb_height = 40
        thumb_rect = pygame.Rect(
            self.rect.x,
            self.rect.y + 50,
            self.rect.width,
            thumb_height
        )
        surface.fill(COLOR_SCROLLBAR_THUMB, thumb_rect)