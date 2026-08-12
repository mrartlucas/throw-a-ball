"""Roller Ball rules and target geometry."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

BOARD_SIZE = 128
BALLS_PER_GAME = 9
ROLL_SECONDS = 0.72
RESULT_HOLD_SECONDS = 1.0
POWER_SECONDS = 1.6


class PowerZone(str, Enum):
    YELLOW = "yellow"
    GREEN = "green"
    RED = "red"


@dataclass(frozen=True)
class Pocket:
    name: str
    score: int
    x: int
    y: int
    radius: int


POCKETS: tuple[Pocket, ...] = (
    Pocket("100L", 100, 32, 35, 10),
    Pocket("50", 50, 64, 36, 11),
    Pocket("100R", 100, 96, 35, 10),
    Pocket("40", 40, 64, 53, 10),
    Pocket("30", 30, 64, 70, 11),
    Pocket("20", 20, 64, 89, 11),
)

TEN_CATCH_CENTER = (64, 78)
TEN_CATCH_RADIUS_X = 44
TEN_CATCH_RADIUS_Y = 39


@dataclass(frozen=True)
class ShotResult:
    dart_x: int
    dart_y: int
    target_x: int
    target_y: int
    score: int
    label: str


def _validate_coordinate(value: int, name: str) -> None:
    if type(value) is not int or not 0 <= value < BOARD_SIZE:
        raise ValueError(f"{name} must be an integer from 0 through 127")


def _resolve_effective(x: int, y: int, dart_x: int, dart_y: int) -> ShotResult:
    pocket_hits: list[tuple[float, Pocket]] = []
    for pocket in POCKETS:
        distance = math.hypot(x - pocket.x, y - pocket.y)
        if distance <= pocket.radius:
            pocket_hits.append((distance, pocket))
    if pocket_hits:
        _, pocket = min(pocket_hits, key=lambda item: item[0])
        return ShotResult(dart_x, dart_y, pocket.x, pocket.y, pocket.score, pocket.name)

    cx, cy = TEN_CATCH_CENTER
    normalized = ((x - cx) / TEN_CATCH_RADIUS_X) ** 2 + ((y - cy) / TEN_CATCH_RADIUS_Y) ** 2
    if normalized <= 1.0 and y >= 47:
        return ShotResult(dart_x, dart_y, 64, 101, 10, "10")
    return ShotResult(dart_x, dart_y, x, min(y, 112), 0, "MISS")


def resolve_arcade_shot(x: int, y: int) -> ShotResult:
    _validate_coordinate(x, "x")
    _validate_coordinate(y, "y")
    return _resolve_effective(x, y, x, y)


def resolve_pro_shot(aim_x: int, aim_y: int, throw_x: int, throw_y: int, power: PowerZone) -> ShotResult:
    """Blend setup aim with final dart; power corrects vertical reach."""
    for value, name in ((aim_x, "aim_x"), (aim_y, "aim_y"), (throw_x, "throw_x"), (throw_y, "throw_y")):
        _validate_coordinate(value, name)
    if type(power) is not PowerZone:
        raise TypeError("power must be a PowerZone")

    x = round(aim_x * 0.62 + throw_x * 0.38)
    y = round(aim_y * 0.62 + throw_y * 0.38)
    if power is PowerZone.RED:
        y -= 13
    elif power is PowerZone.YELLOW:
        y += 10
    y = max(0, min(127, y))
    return _resolve_effective(x, y, throw_x, throw_y)


def power_zone_for_taps(taps: int) -> PowerZone:
    if taps >= 9:
        return PowerZone.RED
    if taps >= 5:
        return PowerZone.GREEN
    return PowerZone.YELLOW


def sample_ball_position(shot: ShotResult, progress: float) -> tuple[int, int]:
    if not isinstance(shot, ShotResult):
        raise TypeError("shot must be a ShotResult")
    if isinstance(progress, bool) or not isinstance(progress, (int, float)):
        raise TypeError("progress must be numeric")
    t = max(0.0, min(1.0, float(progress)))
    eased = 1.0 - (1.0 - t) ** 2
    start_x, start_y = 64.0, 121.0
    end_x, end_y = float(shot.target_x), float(shot.target_y)
    bend = (shot.target_x - 64) * 0.18 * math.sin(math.pi * t)
    x = start_x + (end_x - start_x) * eased + bend
    y = start_y + (end_y - start_y) * eased
    return round(x), round(y)
