# ui/button.py
import pygame
from typing import Callable, Optional, Tuple
from ui.colors import (
    COLOR_APP_BG, COLOR_APP_TEXT,
    COLOR_SYS_BG, COLOR_SYS_TEXT,
    COLOR_DISABLED_BG, COLOR_DISABLED_TEXT,
    COLOR_PRESSED_BG, COLOR_PRESSED_TEXT,
    COLOR_BORDER
)
from ui.fonts import get_font_large, get_font_small

class Button:
    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        subtitle: Optional[str] = None,
        style: str = "APP",  # "APP", "SYS", "DISABLED", "CANCEL"
        callback: Optional[Callable[[], None]] = None
    ):
        self.rect = rect
        self.text = text
        self.subtitle = subtitle
        self.style = style
        self.callback = callback
        self.is_pressed = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.style == "DISABLED" or not self.callback:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed:
                self.is_pressed = False
                if self.rect.collidepoint(event.pos):
                    self.callback()
                    return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_pressed and not self.rect.collidepoint(event.pos):
                self.is_pressed = False

        return False

    def draw(self, surface: pygame.Surface):
        # Determine colors based on state and style
        if self.style == "DISABLED":
            bg_color = COLOR_DISABLED_BG
            text_color = COLOR_DISABLED_TEXT
        elif self.is_pressed:
            bg_color = COLOR_PRESSED_BG
            text_color = COLOR_PRESSED_TEXT
        elif self.style == "SYS":
            bg_color = COLOR_SYS_BG
            text_color = COLOR_SYS_TEXT
        elif self.style == "CANCEL":
            bg_color = COLOR_APP_BG
            text_color = COLOR_APP_TEXT
        else:  # APP / Default
            bg_color = COLOR_APP_BG
            text_color = COLOR_APP_TEXT

        # Fill background and draw border
        surface.fill(bg_color, self.rect)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=1)

        # Render Text
        font_large = get_font_large()
        font_small = get_font_small()

        lines = self.text.split("\n")
        total_height = sum(font_large.size(line)[1] for line in lines)
        if self.subtitle:
            total_height += font_small.size(self.subtitle)[1] + 4

        start_y = self.rect.centery - (total_height // 2)

        current_y = start_y
        for line in lines:
            txt_surf = font_large.render(line, True, text_color)
            txt_rect = txt_surf.get_rect(centerx=self.rect.centerx, top=current_y)
            surface.blit(txt_surf, txt_rect)
            current_y += txt_surf.get_height()

        if self.subtitle:
            sub_surf = font_small.render(self.subtitle, True, text_color)
            sub_rect = sub_surf.get_rect(centerx=self.rect.centerx, top=current_y + 4)
            surface.blit(sub_surf, sub_rect)