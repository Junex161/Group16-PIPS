"""Text and panel helpers shared by all screens."""

import pygame

WHITE = (255, 255, 255)
INK = (24, 28, 52)
GOLD = (255, 214, 92)
SOFT_BLUE = (170, 210, 255)
GREEN = (120, 220, 130)
RED = (255, 120, 120)

_font_cache = {}


def get_font(size, bold=False):
    """Return the default pygame font in the given pixel size (cached)."""
    key = (size, bold)
    if key not in _font_cache:
        font = pygame.font.Font(None, size)
        font.set_bold(bold)
        _font_cache[key] = font
    return _font_cache[key]


def clear_font_cache():
    """Forget cached fonts; they become invalid when pygame shuts down."""
    _font_cache.clear()


def draw_text(surface, text, position, size=30, color=WHITE, anchor="topleft", bold=False, shadow=False):
    """
    Draw one line of text.

    Parameters
    ----------
    surface : pygame.Surface
        Target surface.
    text : str
        Text to draw (plain ASCII).
    position : tuple of int
        Pixel position of the anchor point.
    size : int, optional
        Font size in pixels.
    color : tuple of int, optional
        RGB text colour.
    anchor : str, optional
        Name of the pygame.Rect attribute placed at ``position``,
        for example "topleft", "center" or "midtop".
    bold : bool, optional
        Use a bold font.
    shadow : bool, optional
        Add a dark drop shadow, for text drawn directly on the game world.

    Returns
    -------
    pygame.Rect
        Area covered by the text.
    """
    font = get_font(size, bold)
    image = font.render(text, True, color)
    rect = image.get_rect(**{anchor: position})
    if shadow:
        surface.blit(font.render(text, True, INK), rect.move(2, 2))
    surface.blit(image, rect)
    return rect


def wrap_text(text, font, max_width):
    """Split ``text`` into lines no wider than ``max_width`` pixels.

    Line breaks in the text are kept.
    """
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and font.size(candidate)[0] > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def draw_paragraph(surface, text, topleft, max_width, size=30, color=WHITE, line_gap=6, centered=False):
    """Draw wrapped text and return the y coordinate below its last line."""
    font = get_font(size)
    x, y = topleft
    for line in wrap_text(text, font, max_width):
        if centered:
            draw_text(surface, line, (x + max_width // 2, y), size, color, anchor="midtop")
        else:
            draw_text(surface, line, (x, y), size, color)
        y += font.get_height() + line_gap
    return y


def draw_panel(surface, rect, fill=(22, 28, 60, 235), border=GOLD, radius=18):
    """Draw a rounded, slightly transparent panel with a border."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, border, panel.get_rect(), width=3, border_radius=radius)
    surface.blit(panel, rect)


def dim(surface, alpha=150):
    """Darken the whole surface, used behind overlays."""
    shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    shade.fill((8, 10, 28, alpha))
    surface.blit(shade, (0, 0))
