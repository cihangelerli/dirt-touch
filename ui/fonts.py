# ui/fonts.py
from typing import Optional

import pygame

_font_large: Optional[pygame.font.Font] = None
_font_small: Optional[pygame.font.Font] = None


def init_fonts():
    global _font_large, _font_small
    pygame.font.init()

    try:
        _font_large = pygame.font.SysFont(
            "DejaVu Sans Mono, FreeMono, Monospace", 22, bold=True
        )
        _font_small = pygame.font.SysFont(
            "DejaVu Sans Mono, FreeMono, Monospace", 14, bold=True
        )
    except Exception:
        _font_large = pygame.font.Font(None, 24)
        _font_small = pygame.font.Font(None, 16)


def reset_fonts():
    """Clears cached font references so Pygame safely reinstantiates them after pygame.quit()."""
    global _font_large, _font_small
    _font_large = None
    _font_small = None
    init_fonts()


def get_font_large() -> pygame.font.Font:
    if _font_large is None:
        init_fonts()
    return _font_large


def get_font_small() -> pygame.font.Font:
    if _font_small is None:
        init_fonts()
    return _font_small
