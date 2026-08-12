"""Playable single-player Roller Ball runtime with Arcade and Pro styles."""
from __future__ import annotations

from enum import Enum
import time
from typing import Callable

from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.rendering import render_frame
from throw_a_ball.roller_ball import (
    BALLS_PER_GAME, POWER_SECONDS, RESULT_HOLD_SECONDS, ROLL_SECONDS,
    PowerZone, power_zone_for_taps, resolve_arcade_shot,
    resolve_pro_shot, sample_ball_position,
)


class PlayStyle(str, Enum):
    ARCADE = "arcade"
    PRO = "pro"


class Phase(str, Enum):
    STYLE_SELECT = "style_select"
    ARCADE_READY = "arcade_ready"
    PRO_AIM = "pro_aim"
    PRO_POWER = "pro_power"
    BALL_ROLL = "ball_roll"
    RESULT = "result"
    WAIT_FOR_REMOVAL = "wait_for_removal"
    GAME_OVER = "game_over"


class RollerBallRuntime:
    def __init__(self, facade: DartsnutFacade, monotonic: Callable[[], float] = time.monotonic):
        self.facade = facade
        self.monotonic = monotonic
        self.phase = Phase.STYLE_SELECT
        self.style_index = 0
        self.style: PlayStyle | None = None
        self.score = 0
        self.balls_used = 0
        self.current_shot = None
        self.shot_started_at = None
        self.result_started_at = None
        self.blocked_dart_index = None
        self.aim: tuple[int, int] | None = None
        self.power_started_at = None
        self.power_taps = 0
        self.power_zone: PowerZone | None = None
        self.cached_frame = render_frame(score=0, balls_used=0, ui_mode="style", style_index=0)

    def restart(self):
        self.__init__(self.facade, self.monotonic)

    def _active(self, index):
        if index is None:
            return False
        return any(d.dart_index == index for d in self.facade.read_active_darts())

    def _begin_next_ball(self):
        self.current_shot = None
        self.aim = None
        self.power_started_at = None
        self.power_taps = 0
        self.power_zone = None
        if self.style is PlayStyle.PRO:
            self.phase = Phase.PRO_AIM
            self.cached_frame = render_frame(
                score=self.score, balls_used=self.balls_used,
                ui_mode="aim", aim_position=(64, 70)
            )
        else:
            self.phase = Phase.ARCADE_READY
            self.cached_frame = render_frame(score=self.score, balls_used=self.balls_used)

    def _start_roll(self, shot, now):
        self.current_shot = shot
        self.shot_started_at = now
        self.phase = Phase.BALL_ROLL
        self.cached_frame = render_frame(
            score=self.score,
            balls_used=self.balls_used,
            ball_position=sample_ball_position(shot, 0.0),
        )

    def _finish_result_or_wait(self):
        if self._active(self.blocked_dart_index):
            self.phase = Phase.WAIT_FOR_REMOVAL
            self.cached_frame = render_frame(
                score=self.score,
                balls_used=self.balls_used,
                last_shot=self.current_shot,
                message_code=2,
            )
            return
        self.blocked_dart_index = None
        if self.balls_used >= BALLS_PER_GAME:
            self.phase = Phase.GAME_OVER
            self.cached_frame = render_frame(
                score=self.score, balls_used=self.balls_used, message_code=3
            )
        else:
            self._begin_next_ball()

    def step(self):
        now = self.monotonic()
        buttons = self.facade.buttons()

        if self.phase is Phase.STYLE_SELECT:
            if "btn_left" in buttons or "btn_right" in buttons:
                self.style_index = 1 - self.style_index
            if "btn_a" in buttons:
                self.style = PlayStyle.ARCADE if self.style_index == 0 else PlayStyle.PRO
                self._begin_next_ball()
            else:
                self.cached_frame = render_frame(
                    score=0, balls_used=0, ui_mode="style", style_index=self.style_index
                )
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.GAME_OVER:
            if "btn_a" in buttons:
                self.restart()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.WAIT_FOR_REMOVAL:
            if not self._active(self.blocked_dart_index):
                self.blocked_dart_index = None
                if self.balls_used >= BALLS_PER_GAME:
                    self.phase = Phase.GAME_OVER
                    self.cached_frame = render_frame(
                        score=self.score, balls_used=self.balls_used, message_code=3
                    )
                else:
                    self._begin_next_ball()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.PRO_POWER:
            if "btn_a" in buttons:
                self.power_taps += 1
            elapsed = now - self.power_started_at
            if elapsed >= POWER_SECONDS:
                self.power_zone = power_zone_for_taps(self.power_taps)
                assert self.aim is not None
                self.current_shot = resolve_pro_shot(self.aim[0], self.aim[1], self.power_zone)
                self._start_roll(self.current_shot, now)
            else:
                self.cached_frame = render_frame(
                    score=self.score,
                    balls_used=self.balls_used,
                    ui_mode="power",
                    power_taps=min(self.power_taps, 12),
                )
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.BALL_ROLL:
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
            if now - self.result_started_at >= RESULT_HOLD_SECONDS:
                self._finish_result_or_wait()
            self.facade.submit(self.cached_frame)
            return

        hits = self.facade.read_dart_hits()
        if self.phase is Phase.PRO_AIM:
            if hits:
                hit = hits[0]
                self.aim = (hit.x, hit.y)
                self.blocked_dart_index = hit.dart_index
                self.phase = Phase.PRO_POWER
                self.power_started_at = now
                self.power_taps = 0
                self.cached_frame = render_frame(
                    score=self.score,
                    balls_used=self.balls_used,
                    ui_mode="power",
                    power_taps=0,
                )
            else:
                self.cached_frame = render_frame(
                    score=self.score,
                    balls_used=self.balls_used,
                    ui_mode="aim",
                    aim_position=(64, 70),
                )
        elif self.phase is Phase.ARCADE_READY and hits:
            hit = hits[0]
            self.blocked_dart_index = hit.dart_index
            self._start_roll(resolve_arcade_shot(hit.x, hit.y), now)

        self.facade.submit(self.cached_frame)


def run_roller_ball(
    facade: DartsnutFacade,
    *,
    frame_seconds: float = 1 / 30,
    sleeper: Callable[[float], object] = time.sleep,
) -> None:
    runtime = RollerBallRuntime(facade)
    try:
        while facade.is_running():
            runtime.step()
            sleeper(frame_seconds)
    finally:
        facade.close()
