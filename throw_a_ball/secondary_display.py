"""Pygame emulator window for the logical 64x32 secondary display."""
from __future__ import annotations

import pygame

from throw_a_ball.rendering import LOWER_HEIGHT, LOWER_RGB888_BYTE_LENGTH, LOWER_WIDTH


class SecondaryDisplayWindow:
    """Show RGB888 Screen 2 frames without depending on the cabinet SDK."""

    def __init__(self, scale: int = 8):
        self.scale = scale
        pygame.display.init()
        pygame.display.set_caption("Throw a Ball - Screen 2 (64x32)")
        self._window = pygame.display.set_mode((LOWER_WIDTH * scale, LOWER_HEIGHT * scale))
        self._closed = False

    def submit(self, frame: bytes) -> None:
        if self._closed:
            return
        if len(frame) != LOWER_RGB888_BYTE_LENGTH:
            raise ValueError("Screen 2 frame must be 64x32 RGB888")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
        logical = pygame.image.frombuffer(frame, (LOWER_WIDTH, LOWER_HEIGHT), "RGB")
        scaled = pygame.transform.scale(logical, (LOWER_WIDTH * self.scale, LOWER_HEIGHT * self.scale))
        self._window.blit(scaled, (0, 0))
        pygame.display.flip()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            pygame.display.quit()
