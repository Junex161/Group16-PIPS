"""Text and panel helpers shared by all screens."""

import pygame

WHITE = (255, 255, 255)
INK = (24, 28, 52)
GOLD = (255, 214, 92)
SOFT_BLUE = (170, 210, 255)
GREEN = (120, 220, 130)
RED = (255, 120, 120)
# Fill of full-screen pages (notebook, info pages), opaque so nothing shines through.
PAGE_FILL = (22, 28, 60, 255)

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


def draw_bar_chart(surface, rect, bars, title="", unit="", decimals=0):
    """
    Draw a simple bar chart inside a panel.

    Parameters
    ----------
    surface : pygame.Surface
        Target surface.
    rect : pygame.Rect
        Area of the chart.
    bars : list of tuple
        ``(label, value, color)`` per bar; a value of None is shown as "-".
        A label may contain "\n" to start a new line.
    title : str, optional
        Heading above the bars.
    unit : str, optional
        Unit written after each value, for example "ms".
    decimals : int, optional
        Decimal places of the values.
    """
    draw_panel(surface, rect)
    draw_text(surface, title, (rect.centerx, rect.top + 16), 28, SOFT_BLUE, "midtop")
    highest = max([value for _, value, _ in bars if value is not None], default=0) or 1
    baseline = rect.bottom - 70
    max_height = baseline - rect.top - 100
    slot = (rect.width - 40) / len(bars)
    for index, (label, value, color) in enumerate(bars):
        center_x = int(rect.left + 20 + slot * (index + 0.5))
        height = 0 if value is None else int(max_height * value / highest)
        bar = pygame.Rect(0, 0, min(110, int(slot * 0.6)), max(height, 2))
        bar.midbottom = (center_x, baseline)
        pygame.draw.rect(surface, color, bar, border_radius=6)
        shown = "-" if value is None else f"{value:.{decimals}f} {unit}".strip()
        draw_text(surface, shown, (center_x, bar.top - 8), 30, WHITE, "midbottom", bold=True)
        lines = [line for part in label.split("\n") for line in wrap_text(part, get_font(22), int(slot) - 10)]
        for line_number, line in enumerate(lines):
            draw_text(surface, line, (center_x, baseline + 8 + line_number * 22), 22, WHITE, "midtop")
    pygame.draw.line(surface, WHITE, (rect.left + 20, baseline), (rect.right - 20, baseline), 2)
