"""Text and panel helpers shared by all screens."""

from pathlib import Path

import pygame

WHITE = (255, 255, 255)
INK = (24, 28, 52)
GOLD = (255, 214, 92)
SOFT_BLUE = (170, 210, 255)
GREEN = (120, 220, 130)
RED = (255, 120, 120)
# Fill of full-screen pages (notebook, info pages), opaque so nothing shines through.
PAGE_FILL = (22, 28, 60, 255)

# The game font: Fredoka (SIL Open Font License, see fonts/OFL.txt).
FONT_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {False: FONT_DIR / "Fredoka-Medium.ttf", True: FONT_DIR / "Fredoka-SemiBold.ttf"}
# Fredoka is wider than pygame's default font; sizes are scaled so that texts keep their width.
FONT_SCALE = 0.733

_font_cache = {}


def get_font(size, bold=False):
    """Return the game font in the given size (cached); pygame's default font if it is missing."""
    key = (size, bold)
    if key not in _font_cache:
        path = FONT_FILES[bool(bold)]
        if path.exists():
            font = pygame.font.Font(path, max(8, round(size * FONT_SCALE)))
        else:
            font = pygame.font.Font(None, size)
            font.set_bold(bold)
        _font_cache[key] = font
    return _font_cache[key]


def clear_font_cache():
    """Forget cached fonts and panels; they become invalid when pygame shuts down."""
    _font_cache.clear()
    _panel_cache.clear()


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
    # The same line steps as with pygame's default font, so that layouts keep their height.
    step = round(size * 0.75) + line_gap
    x, y = topleft
    for line in wrap_text(text, font, max_width):
        if centered:
            draw_text(surface, line, (x + max_width // 2, y), size, color, anchor="midtop")
        else:
            draw_text(surface, line, (x, y), size, color)
        y += step
    return y


_panel_cache = {}


def _panel_image(size, fill, border, radius):
    """Build a panel once: soft drop shadow, a light top, the border and a thin inner line."""
    width, height = size
    shadow = 8
    image = pygame.Surface((width + 2 * shadow, height + 2 * shadow), pygame.SRCALPHA)
    for spread, alpha in ((8, 18), (5, 28), (2, 40)):
        pygame.draw.rect(image, (0, 0, 0, alpha), (shadow - spread + 2, shadow - spread + 6, width + 2 * spread - 4, height + 2 * spread - 4), border_radius=radius + spread)
    box = pygame.Rect(shadow, shadow, width, height)
    pygame.draw.rect(image, fill, box, border_radius=radius)
    fill_alpha = fill[3] if len(fill) > 3 else 255
    # A light that fades out towards the middle, cut to the rounded shape.
    light = pygame.Surface(size, pygame.SRCALPHA)
    top = round(22 * fill_alpha / 255)
    for y in range(height // 2):
        pygame.draw.line(light, (255, 255, 255, round(top * (1 - y / (height / 2)))), (0, y), (width, y))
    shape = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(shape, (255, 255, 255, 255), shape.get_rect(), border_radius=radius)
    light.blit(shape, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    image.blit(light, box)
    if width > 24 and height > 24:
        pygame.draw.rect(image, (255, 255, 255, 34), box.inflate(-10, -10), width=1, border_radius=max(2, radius - 5))
    pygame.draw.rect(image, border, box, width=3, border_radius=radius)
    return image


def draw_panel(surface, rect, fill=(22, 28, 60, 235), border=GOLD, radius=18):
    """Draw a rounded, slightly transparent panel with a border and a soft shadow."""
    key = (rect.size, tuple(fill), tuple(border), radius)
    image = _panel_cache.get(key)
    if image is None:
        if len(_panel_cache) > 400:
            _panel_cache.clear()
        image = _panel_cache[key] = _panel_image(rect.size, fill, border, radius)
    surface.blit(image, (rect.x - 8, rect.y - 8))


def draw_pill(surface, rect, alpha=120):
    """A quiet dark backing that keeps HUD text readable on bright backgrounds."""
    pill = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(pill, (*INK, alpha), pill.get_rect(), border_radius=min(18, rect.height // 2))
    surface.blit(pill, rect)


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
