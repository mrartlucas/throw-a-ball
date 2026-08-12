"""Playable single-player Roller Ball runtime with simple clear-board throw arming."""
from __future__ import annotations
from enum import Enum
import time
from throw_a_ball.rendering import render_frame
from throw_a_ball.roller_ball import (
    AIM_X, AimPosition, BALLS_PER_GAME, POWER_SECONDS, RESULT_HOLD_SECONDS, ROLL_SECONDS,
    power_zone_for_taps, resolve_arcade_shot, resolve_pro_shot, sample_ball_position,
)

class PlayStyle(str, Enum):
    ARCADE="arcade"
    PRO="pro"

class Phase(str, Enum):
    STYLE_SELECT="style_select"
    ARCADE_READY="arcade_ready"
    PRO_AIM="pro_aim"
    PRO_POWER="pro_power"
    PRO_THROW_READY="pro_throw_ready"
    BALL_ROLL="ball_roll"
    RESULT="result"
    WAIT_FOR_REMOVAL="wait_for_removal"
    GAME_OVER="game_over"

AIM_ORDER=(AimPosition.LEFT,AimPosition.CENTER,AimPosition.RIGHT)
POWER_PULSE_BOOST = 3.0
POWER_DECAY_PER_SECOND = 1.6

class RollerBallRuntime:
    def __init__(self,facade,monotonic=time.monotonic):
        self.facade=facade
        self.monotonic=monotonic
        self.phase=Phase.STYLE_SELECT
        self.style_index=0
        self.style=None
        self.score=0
        self.balls_used=0
        self.current_shot=None
        self.shot_started_at=None
        self.result_started_at=None
        self.blocked_dart_index=None
        self.aim_index=1
        self.aim=AimPosition.CENTER
        self.power_started_at=None
        self.power_last_tick=None
        self.power_charge=0.0
        self.power_zone=None
        self.throw_armed=False
        self.cached_frame=render_frame(score=0,balls_used=0,ui_mode="style",style_index=0)

    def restart(self):
        self.__init__(self.facade,self.monotonic)

    def _active_darts(self):
        return self.facade.read_active_darts()

    def _active(self,index):
        return index is not None and any(d.dart_index==index for d in self._active_darts())

    def _board_clear(self):
        return len(self._active_darts()) == 0

    def _drain_hits(self):
        self.facade.read_dart_hits()

    def _aim_xy(self):
        return (AIM_X[self.aim],96)

    def _begin_next_ball(self):
        self.current_shot=None
        self.blocked_dart_index=None
        self.aim_index=1
        self.aim=AimPosition.CENTER
        self.power_started_at=None
        self.power_last_tick=None
        self.power_charge=0.0
        self.power_zone=None
        self.throw_armed=False
        self._drain_hits()
        if self.style is PlayStyle.PRO:
            self.phase=Phase.PRO_AIM
            self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="aim",aim_position=self._aim_xy(),aim_slots=True)
        else:
            self.phase=Phase.ARCADE_READY
            self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used)

    def _start_roll(self,shot,index,now):
        self.current_shot=shot
        self.blocked_dart_index=index
        self.shot_started_at=now
        self.throw_armed=False
        self.phase=Phase.BALL_ROLL
        self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ball_position=sample_ball_position(shot,0.0))

    def _finish(self):
        if self._active(self.blocked_dart_index):
            self.phase=Phase.WAIT_FOR_REMOVAL
            self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,last_shot=self.current_shot,message_code=2)
            return
        self.blocked_dart_index=None
        if self.balls_used>=BALLS_PER_GAME:
            self.phase=Phase.GAME_OVER
            self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,message_code=3)
        else:
            self._begin_next_ball()

    def _ready_for_fresh_throw(self):
        if not self.throw_armed:
            self._drain_hits()
            if self._board_clear():
                self.throw_armed=True
            return None
        hits=self.facade.read_dart_hits()
        return hits[0] if hits else None

    def step(self):
        now=self.monotonic()
        buttons=self.facade.buttons()

        if self.phase is Phase.STYLE_SELECT:
            self._drain_hits()
            if "btn_left" in buttons or "btn_right" in buttons:
                self.style_index=1-self.style_index
            if "btn_a" in buttons:
                self.style=PlayStyle.ARCADE if self.style_index==0 else PlayStyle.PRO
                self._begin_next_ball()
            else:
                self.cached_frame=render_frame(score=0,balls_used=0,ui_mode="style",style_index=self.style_index)
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.GAME_OVER:
            self._drain_hits()
            if "btn_a" in buttons:
                self.restart()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.WAIT_FOR_REMOVAL:
            self._drain_hits()
            if not self._active(self.blocked_dart_index):
                self.blocked_dart_index=None
                if self.balls_used>=BALLS_PER_GAME:
                    self.phase=Phase.GAME_OVER
                    self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,message_code=3)
                else:
                    self._begin_next_ball()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.PRO_AIM:
            self._drain_hits()
            if "btn_left" in buttons and self.aim_index>0:
                self.aim_index-=1
                self.aim=AIM_ORDER[self.aim_index]
            if "btn_right" in buttons and self.aim_index<2:
                self.aim_index+=1
                self.aim=AIM_ORDER[self.aim_index]
            if "btn_a" in buttons:
                self.phase=Phase.PRO_POWER
                self.power_started_at=now
                self.power_last_tick=now
                self.power_charge=0.0
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="power",power_taps=0)
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="aim",aim_position=self._aim_xy(),aim_slots=True)
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.PRO_POWER:
            self._drain_hits()
            dt=max(0.0,now-self.power_last_tick)
            self.power_last_tick=now
            if "btn_a" in buttons:
                self.power_charge=min(12.0,self.power_charge+POWER_PULSE_BOOST)
            else:
                self.power_charge=max(0.0,self.power_charge-POWER_DECAY_PER_SECOND*dt)
            if now-self.power_started_at>=POWER_SECONDS:
                locked=int(round(self.power_charge))
                self.power_zone=power_zone_for_taps(locked)
                self.phase=Phase.PRO_THROW_READY
                self.throw_armed=True
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="ready",power_zone=self.power_zone,aim_position=self._aim_xy(),aim_slots=True)
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="power",power_taps=self.power_charge)
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.BALL_ROLL:
            self._drain_hits()
            progress=(now-self.shot_started_at)/ROLL_SECONDS
            if progress>=1.0:
                self.score+=self.current_shot.score
                self.balls_used+=1
                self.phase=Phase.RESULT
                self.result_started_at=now
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ball_position=(self.current_shot.target_x,self.current_shot.target_y),last_shot=self.current_shot,message_code=1)
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ball_position=sample_ball_position(self.current_shot,progress))
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.RESULT:
            self._drain_hits()
            if now-self.result_started_at>=RESULT_HOLD_SECONDS:
                self._finish()
            self.facade.submit(self.cached_frame)
            return

        if self.phase is Phase.PRO_THROW_READY:
            hit=self._ready_for_fresh_throw()
            if hit is not None:
                self._start_roll(resolve_pro_shot(self.aim,hit.x,hit.y,self.power_zone),hit.dart_index,now)
        elif self.phase is Phase.ARCADE_READY:
            hit=self._ready_for_fresh_throw()
            if hit is not None:
                self._start_roll(resolve_arcade_shot(hit.x,hit.y),hit.dart_index,now)
        self.facade.submit(self.cached_frame)

def run_roller_ball(facade,frame_seconds=1/30,sleeper=time.sleep):
    runtime=RollerBallRuntime(facade)
    try:
        while facade.is_running():
            runtime.step()
            sleeper(frame_seconds)
    finally:
        facade.close()
