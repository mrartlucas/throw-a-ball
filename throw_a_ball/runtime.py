"""Playable single-player Roller Ball Arcade runtime."""
from __future__ import annotations

from enum import Enum
import time
from typing import Callable

from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.rendering import render_frame
from throw_a_ball.roller_ball import (
    BALLS_PER_GAME,
    RESULT_HOLD_SECONDS,
    ROLL_SECONDS,
    ShotResult,
    resolve_arcade_shot,
    sample_ball_position,
)


class Phase(str, Enum):
    READY = "ready"
    BALL_ROLL = "ball_roll"
    RESULT = "result"
    WAIT_FOR_REMOVAL = "wait_for_removal"
    GAME_OVER = "game_over"


class RollerBallRuntime:
    def __init__(self, facade: DartsnutFacade, monotonic: Callable[[], float] = time.monotonic):
        self.facade = facade
        self.monotonic = monotonic
        self.phase = Phase.READY
        self.score = 0
        self.balls_used = 0
        self.current_shot: ShotResult | None = None
        self.shot_started_at: float | None = None
        self.result_started_at: float | None = None
        self.blocked_dart_index: int | None = None
        self.cached_frame = render_frame(score=0, balls_used=0)

    @property
    def complete(self) -> bool:
        return self.phase is Phase.GAME_OVER

    def restart(self) -> None:
        self.phase = Phase.READY
        self.score = 0
        self.balls_used = 0
        self.current_shot = None
        self.shot_started_at = None
        self.result_started_at = None
        self.blocked_dart_index = None
        self.cached_frame = render_frame(score=0, balls_used=0)

    def _dart_still_active(self) -> bool:
        if self.blocked_dart_index is None:
            return False
        return any(d.dart_index == self.blocked_dart_index for d in self.facade.read_active_darts())

    def _finish_result_or_wait(self) -> None:
        if self._dart_still_active():
            self.phase = Phase.WAIT_FOR_REMOVAL
            self.cached_frame = render_frame(
                score=self.score, balls_used=self.balls_used, last_shot=self.current_shot, message_code=2
            )
            return
        self.blocked_dart_index = None
        if self.balls_used >= BALLS_PER_GAME:
            self.phase = Phase.GAME_OVER
            self.cached_frame = render_frame(score=self.score, balls_used=self.balls_used, message_code=3)
        else:
            self.phase = Phase.READY
            self.current_shot = None
            self.cached_frame = render_frame(score=self.score, balls_used=self.balls_used)

    def step(self) -> None:
        now = self.monotonic()

        if self.phase is Phase.GAME_OVER:
            if self.facade.a_pressed():
                self.restart()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.WAIT_FOR_REMOVAL:
            if not self._dart_still_active():
                self.blocked_dart_index = None
                if self.balls_used >= BALLS_PER_GAME:
                    self.phase = Phase.GAME_OVER
                    self.cached_frame = render_frame(score=self.score, balls_used=self.balls_used, message_code=3)
                else:
                    self.phase = Phase.READY
                    self.current_shot = None
                    self.cached_frame = render_frame(score=self.score, balls_used=self.balls_used)
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.BALL_ROLL:
            assert self.current_shot is not None and self.shot_started_at is not None
            progress = (now - self.shot_started_at) / ROLL_SECONDS
            if progress >= 1.0:
                self.score += self.current_shot.score
                self.balls_used += 1
                self.phase = Phase.RESULT
                self.result_started_at = now
                self.cached_frame = render_frame(
                    score=self.score,
                    balls_used=self.balls_used,
                    ball_position=(self.current_shot.target_x, self.current_shot.target_y),
                    last_shot=self.current_shot,
                    message_code=1,
                )
            else:
                self.cached_frame = render_frame(
                    score=self.score,
                    balls_used=self.balls_used,
                    ball_position=sample_ball_position(self.current_shot, progress),
                )
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.RESULT:
            assert self.result_started_at is not None
            if now - self.result_started_at >= RESULT_HOLD_SECONDS:
                self._finish_result_or_wait()
            self.facade.submit(self.cached_frame)
            return

        hits = self.facade.read_dart_hits()
        if hits:
            hit = hits[0]
            self.current_shot = resolve_arcade_shot(hit.x, hit.y)
            self.blocked_dart_index = hit.dart_index
            self.shot_started_at = now
            self.phase = Phase.BALL_ROLL
            self.cached_frame = render_frame(
                score=self.score,
                balls_used=self.balls_used,
                ball_position=sample_ball_position(self.current_shot, 0.0),
            )
        self.facade.submit(self.cached_frame)


def run_roller_ball(facade: DartsnutFacade, *, frame_seconds: float = 1 / 30,
                    sleeper: Callable[[float], object] = time.sleep) -> None:
    runtime = RollerBallRuntime(facade)
    try:
        while facade.is_running():
            runtime.step()
            sleeper(frame_seconds)
    finally:
        facade.close()
