# ui/fonts.py
import pygame
from typing import Optional

_font_large: Optional[pygame.font.Font] = None
_font_small: Optional[pygame.font.Font] = None

def init_fonts():
    global _font_large, _font_small
    pygame.font.init()
    
    # Try system monospaced/sans fonts or fallback to default
    try:
        _font_large = pygame.font.SysFont("DejaVu Sans Mono, FreeMono, Monospace", 22, bold=True)
        _font_small = pygame.font.SysFont("DejaVu Sans Mono, FreeMono, Monospace", 14, bold=True)
    except Exception:
        _font_large = pygame.font.Font(None, 24)
        _font_small = pygame.font.Font(None, 16)

def get_font_large() -> pygame.font.Font:
    if _font_large is None:
        init_fonts()
    return _font_large

def get_font_small() -> pygame.font.Font:
    if _font_small is None:
        init_fonts()
    return _font_small