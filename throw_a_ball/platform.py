"""Narrow Dartsnut SDK facade used by the Roller Ball prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DartHit:
    dart_index: int
    x: int
    y: int


class DartsnutProtocol(Protocol):
    running: bool
    def get_dart_hits(self) -> list[tuple[int, int, int]]: ...
    def get_active_darts(self) -> list[tuple[int, int, int]]: ...
    def get_button_events(self) -> dict[str, bool]: ...
    def update_frame_buffer(self, frame: bytearray) -> bool: ...
    def close(self) -> None: ...


class DartsnutFacade:
    def __init__(self, sdk: DartsnutProtocol):
        self._sdk = sdk

    def is_running(self) -> bool:
        return bool(self._sdk.running)

    def read_dart_hits(self) -> tuple[DartHit, ...]:
        hits = []
        for dart_index, x, y in self._sdk.get_dart_hits():
            if 0 <= dart_index <= 11 and 0 <= x <= 127 and 0 <= y <= 127:
                hits.append(DartHit(int(dart_index), int(x), int(y)))
        return tuple(hits)

    def read_active_darts(self) -> tuple[DartHit, ...]:
        active = []
        for dart_index, x, y in self._sdk.get_active_darts():
            if 0 <= dart_index <= 11 and 0 <= x <= 127 and 0 <= y <= 127:
                active.append(DartHit(int(dart_index), int(x), int(y)))
        return tuple(active)

    def buttons(self) -> frozenset[str]:
        events = self._sdk.get_button_events()
        return frozenset(name for name, pressed in events.items() if pressed)

    def a_pressed(self) -> bool:
        return "btn_a" in self.buttons()

    def submit(self, frame: bytes) -> bool:
        return bool(self._sdk.update_frame_buffer(bytearray(frame)))

    def submit_lower(self, frame: bytes) -> bool:
        """Submit the 64x32 setup display when the host exposes one.

        Older development SDKs only expose the main framebuffer, so keeping this
        capability optional lets the same build continue to run on them.
        """
        update = getattr(self._sdk, "update_lower_frame_buffer", None)
        if update is None:
            update = getattr(self._sdk, "update_secondary_frame_buffer", None)
        return bool(update(bytearray(frame))) if update is not None else False

    def close(self) -> None:
        self._sdk.close()
