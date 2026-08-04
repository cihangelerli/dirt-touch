# ui/button.py
import pygame
from typing import Callable, Optional, Tuple, Union
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
        self.active_pointer_id: Optional[Union[int, str]] = None  # Tracks active finger_id or "mouse"

    def _get_display_size(self) -> Tuple[int, int]:
        """Dynamically retrieves current display surface size for normalized coordinate mapping."""
        surface = pygame.display.get_surface()
        if surface:
            return surface.get_size()
        return (640, 480)

    def _normalize_touch_pos(self, event_x: float, event_y: float, display_w: int, display_h: int) -> Tuple[int, int]:
        """Clamps normalized touch coords (0.0 to 1.0) strictly within active pixel bounds (0..W-1, 0..H-1)."""
        x = min(display_w - 1, max(0, int(event_x * display_w)))
        y = min(display_h - 1, max(0, int(event_y * display_h)))
        return (x, y)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if self.style == "DISABLED" or not self.callback:
            return False

        display_w, display_h = self._get_display_size()

        # 1. Standard Mouse Events (Mouse Emulation)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.active_pointer_id is None and self.rect.collidepoint(event.pos):
                self.is_pressed = True
                self.active_pointer_id = "mouse"
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.active_pointer_id == "mouse":
                if not self.rect.collidepoint(event.pos):
                    self.is_pressed = False
                    self.active_pointer_id = None

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_pointer_id == "mouse":
                self.is_pressed = False
                self.active_pointer_id = None
                if self.rect.collidepoint(event.pos):
                    self.callback()
                    return True

        # 2. Native Touch Events (with finger_id tracking and coordinate clamping)
        elif event.type == pygame.FINGERDOWN:
            finger_id = getattr(event, "finger_id", getattr(event, "touch_id", 0))
            pos = self._normalize_touch_pos(event.x, event.y, display_w, display_h)
            if self.active_pointer_id is None and self.rect.collidepoint(pos):
                self.is_pressed = True
                self.active_pointer_id = finger_id
                return True

        elif event.type == pygame.FINGERMOTION:
            finger_id = getattr(event, "finger_id", getattr(event, "touch_id", 0))
            if self.active_pointer_id == finger_id:
                pos = self._normalize_touch_pos(event.x, event.y, display_w, display_h)
                if not self.rect.collidepoint(pos):
                    self.is_pressed = False
                    self.active_pointer_id = None

        elif event.type == pygame.FINGERUP:
            finger_id = getattr(event, "finger_id", getattr(event, "touch_id", 0))
            if self.active_pointer_id == finger_id:
                pos = self._normalize_touch_pos(event.x, event.y, display_w, display_h)
                self.is_pressed = False
                self.active_pointer_id = None
                if self.rect.collidepoint(pos):
                    self.callback()
                    return True

        return False

    def draw(self, surface: pygame.Surface):
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

        surface.fill(bg_color, self.rect)
        pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=1)

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