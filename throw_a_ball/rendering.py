"""Tiny dependency-free RGB888 renderer for the 128x128 Roller Ball prototype."""
from __future__ import annotations

from throw_a_ball.roller_ball import POCKETS, ShotResult

WIDTH = 128
HEIGHT = 128
RGB888_BYTE_LENGTH = WIDTH * HEIGHT * 3

Color = tuple[int, int, int]
BLACK: Color = (3, 5, 12)
NAVY: Color = (5, 13, 35)
BLUE: Color = (32, 128, 255)
CYAN: Color = (66, 232, 255)
WHITE: Color = (235, 244, 255)
YELLOW: Color = (255, 202, 46)
RED: Color = (245, 52, 40)
GREEN: Color = (70, 218, 106)
PURPLE: Color = (178, 78, 255)
GRAY: Color = (98, 112, 140)
DARK_GRAY: Color = (32, 38, 52)
WOOD: Color = (91, 51, 29)

_DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
}


def _frame(fill: Color = BLACK) -> bytearray:
    return bytearray(fill * (WIDTH * HEIGHT))


def _px(frame: bytearray, x: int, y: int, color: Color) -> None:
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        frame[i:i+3] = bytes(color)


def _rect(frame: bytearray, x: int, y: int, w: int, h: int, color: Color) -> None:
    for yy in range(max(0, y), min(HEIGHT, y + h)):
        for xx in range(max(0, x), min(WIDTH, x + w)):
            _px(frame, xx, yy, color)


def _circle(frame: bytearray, cx: int, cy: int, radius: int, color: Color, *, hollow: bool = False, thickness: int = 2) -> None:
    r2 = radius * radius
    inner = max(0, radius - thickness)
    inner2 = inner * inner
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r2 and (not hollow or d2 >= inner2):
                _px(frame, x, y, color)


def _digit(frame: bytearray, ch: str, x: int, y: int, color: Color, scale: int = 1) -> None:
    pattern = _DIGITS.get(ch)
    if pattern is None:
        return
    for row, bits in enumerate(pattern):
        for col, bit in enumerate(bits):
            if bit == "1":
                _rect(frame, x + col * scale, y + row * scale, scale, scale, color)


def _number(frame: bytearray, value: int, x: int, y: int, color: Color, scale: int = 1) -> None:
    text = str(value)
    stride = 4 * scale
    for index, ch in enumerate(text):
        _digit(frame, ch, x + index * stride, y, color, scale)


def _pocket_color(score: int) -> Color:
    if score == 100:
        return WHITE
    if score == 50:
        return YELLOW
    if score == 40:
        return BLUE
    if score == 30:
        return CYAN
    if score == 20:
        return WHITE
    return GRAY


def _draw_board(frame: bytearray) -> None:
    _rect(frame, 4, 2, 120, 124, NAVY)
    _rect(frame, 7, 5, 114, 118, BLACK)
    _rect(frame, 11, 13, 106, 100, NAVY)
    _rect(frame, 19, 105, 90, 17, WOOD)
    _rect(frame, 25, 111, 78, 11, (120, 72, 38))

    _circle(frame, 64, 78, 43, CYAN, hollow=True, thickness=3)
    _circle(frame, 64, 78, 39, (10, 24, 54))
    _number(frame, 10, 58, 102, WHITE, 2)

    for pocket in POCKETS:
        color = _pocket_color(pocket.score)
        _circle(frame, pocket.x, pocket.y, pocket.radius + 2, DARK_GRAY)
        _circle(frame, pocket.x, pocket.y, pocket.radius, color, hollow=True, thickness=3)
        _circle(frame, pocket.x, pocket.y, max(2, pocket.radius - 4), BLACK)
        digits = len(str(pocket.score))
        _number(frame, pocket.score, pocket.x - digits * 2, pocket.y - 2, color, 1)


def render_frame(*, score: int, balls_used: int, ball_position: tuple[int, int] | None = None,
                 last_shot: ShotResult | None = None, message_code: int = 0) -> bytes:
    """Render one frame. message_code: 0=play, 1=result, 2=remove dart, 3=game over."""
    frame = _frame()
    _draw_board(frame)

    _rect(frame, 8, 6, 112, 6, DARK_GRAY)
    _number(frame, score, 11, 7, YELLOW, 1)
    _number(frame, max(0, 9 - balls_used), 105, 7, WHITE, 1)

    if last_shot is not None and message_code in (1, 2):
        _rect(frame, 48, 114, 32, 9, DARK_GRAY)
        _number(frame, last_shot.score, 55, 116, GREEN if last_shot.score else RED, 1)

    if message_code == 2:
        _rect(frame, 10, 115, 32, 5, RED)
    elif message_code == 3:
        _rect(frame, 10, 114, 108, 8, PURPLE)
        _number(frame, score, 52, 116, WHITE, 1)

    if ball_position is not None:
        bx, by = ball_position
        _circle(frame, bx, by, 4, BLUE)
        _circle(frame, bx - 1, by - 1, 1, WHITE)

    if len(frame) != RGB888_BYTE_LENGTH:
        raise RuntimeError("renderer produced wrong framebuffer size")
    return bytes(frame)
