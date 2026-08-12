"""Playable single-player Roller Ball runtime preserving v0.11 throw safety with v0.12 setup UI."""
from __future__ import annotations
from enum import Enum
import time
from typing import Protocol

from throw_a_ball.rendering import render_frame, render_lower_frame
from throw_a_ball.roller_ball import (
    AIM_X, AimPosition, BALLS_PER_GAME, POWER_SECONDS, RESULT_HOLD_SECONDS, ROLL_SECONDS,
    power_zone_for_taps, resolve_arcade_shot, resolve_pro_shot, sample_ball_position,
)

FULL_WIDTH=128
FULL_HEIGHT=160
FULL_RGB888_BYTE_LENGTH=FULL_WIDTH*FULL_HEIGHT*3
MAIN_WIDTH=128
MAIN_HEIGHT=128
LOWER_WIDTH=64
LOWER_HEIGHT=32


def compose_dartsnut_full_frame(main_frame:bytes,lower_frame:bytes)->bytes:
    """Pack Screen 1 and Screen 2 into Dartsnut's verified 128x160 RGB888 layout."""
    if type(main_frame) is not bytes or len(main_frame)!=MAIN_WIDTH*MAIN_HEIGHT*3:
        raise ValueError("main_frame must be exact 128x128 RGB888 bytes")
    if type(lower_frame) is not bytes or len(lower_frame)!=LOWER_WIDTH*LOWER_HEIGHT*3:
        raise ValueError("lower_frame must be exact 64x32 RGB888 bytes")
    full=bytearray((3,5,12)*(FULL_WIDTH*FULL_HEIGHT))
    full[:len(main_frame)]=main_frame
    full_row_bytes=FULL_WIDTH*3
    lower_row_bytes=LOWER_WIDTH*3
    for row in range(LOWER_HEIGHT):
        src=row*lower_row_bytes
        dst=(MAIN_HEIGHT+row)*full_row_bytes
        full[dst:dst+lower_row_bytes]=lower_frame[src:src+lower_row_bytes]
    if len(full)!=FULL_RGB888_BYTE_LENGTH:
        raise RuntimeError("full framebuffer produced wrong size")
    return bytes(full)


class PlayStyle(str, Enum):
    ARCADE="arcade"
    PRO="pro"

class Phase(str, Enum):
    GAME_SELECT="game_select"
    MACHINE_SELECT="machine_select"
    STYLE_SELECT="style_select"
    ARCADE_READY="arcade_ready"
    PRO_AIM="pro_aim"
    PRO_POWER="pro_power"
    PRO_THROW_READY="pro_throw_ready"
    BALL_ROLL="ball_roll"
    RESULT="result"
    WAIT_FOR_REMOVAL="wait_for_removal"
    GAME_OVER="game_over"

class SecondaryDisplay(Protocol):
    def submit(self, frame: bytes) -> None: ...
    def close(self) -> None: ...

AIM_ORDER=(AimPosition.LEFT,AimPosition.CENTER,AimPosition.RIGHT)
POWER_PULSE_BOOST=3.0
POWER_DECAY_PER_SECOND=1.6

class RollerBallRuntime:
    def __init__(self,facade,monotonic=time.monotonic,secondary_display:SecondaryDisplay|None=None):
        self.facade=facade
        self.monotonic=monotonic
        self.secondary_display=secondary_display
        self.phase=Phase.GAME_SELECT
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
        self.cached_frame=render_frame(score=0,balls_used=0)

    def _lower_frame(self):
        if self.phase is Phase.GAME_SELECT: return render_lower_frame("GAME","ROLLER BALL","A NEXT")
        if self.phase is Phase.MACHINE_SELECT: return render_lower_frame("MACHINE","ROLLER BALL","A NEXT  B BACK")
        if self.phase is Phase.STYLE_SELECT: return render_lower_frame("PLAY","ARCADE" if self.style_index==0 else "PRO","A NEXT  B BACK")
        if self.phase is Phase.PRO_AIM: return render_lower_frame("AIM","","A LOCK  B BACK",aim=self.aim)
        if self.phase is Phase.PRO_POWER: return render_lower_frame("POWER","","A MASH  B BACK",power_taps=self.power_charge,power_zone=self.power_zone)
        if self.phase is Phase.PRO_THROW_READY: return render_lower_frame("THROW","READY","THROW  B BACK")
        if self.phase is Phase.WAIT_FOR_REMOVAL: return render_lower_frame("BALL","REMOVE DART","WAIT")
        if self.phase is Phase.GAME_OVER: return render_lower_frame("GAME","GAME OVER","A RESTART")
        if self.phase in (Phase.BALL_ROLL,Phase.RESULT): return render_lower_frame("THROW","ROLLING" if self.phase is Phase.BALL_ROLL else "SCORE","WAIT")
        return render_lower_frame("THROW","READY","THROW")

    def _submit(self):
        lower=self._lower_frame()
        self.facade.submit(compose_dartsnut_full_frame(self.cached_frame,lower))
        if self.secondary_display is not None:
            self.secondary_display.submit(lower)

    def restart(self):
        self.__init__(self.facade,self.monotonic,self.secondary_display)

    def _active_darts(self): return self.facade.read_active_darts()
    def _active(self,index): return index is not None and any(d.dart_index==index for d in self._active_darts())
    def _board_clear(self): return len(self._active_darts())==0
    def _drain_hits(self): self.facade.read_dart_hits()
    def _aim_xy(self): return (AIM_X[self.aim],96)

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
            if self._board_clear(): self.throw_armed=True
            return None
        hits=self.facade.read_dart_hits()
        return hits[0] if hits else None

    def step(self):
        now=self.monotonic()
        buttons=self.facade.buttons()

        if self.phase is Phase.GAME_SELECT:
            self._drain_hits()
            if "btn_a" in buttons: self.phase=Phase.MACHINE_SELECT
            self._submit(); return

        if self.phase is Phase.MACHINE_SELECT:
            self._drain_hits()
            if "btn_b" in buttons: self.phase=Phase.GAME_SELECT
            elif "btn_a" in buttons: self.phase=Phase.STYLE_SELECT
            self._submit(); return

        if self.phase is Phase.STYLE_SELECT:
            self._drain_hits()
            if "btn_left" in buttons or "btn_right" in buttons: self.style_index=1-self.style_index
            if "btn_a" in buttons:
                self.style=PlayStyle.ARCADE if self.style_index==0 else PlayStyle.PRO
                self._begin_next_ball()
            elif "btn_b" in buttons:
                self.phase=Phase.MACHINE_SELECT
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used)
            self._submit(); return

        if self.phase is Phase.GAME_OVER:
            self._drain_hits()
            if "btn_a" in buttons: self.restart()
            self._submit(); return

        if self.phase is Phase.WAIT_FOR_REMOVAL:
            self._drain_hits()
            if not self._active(self.blocked_dart_index):
                self.blocked_dart_index=None
                if self.balls_used>=BALLS_PER_GAME:
                    self.phase=Phase.GAME_OVER
                    self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,message_code=3)
                else: self._begin_next_ball()
            self._submit(); return

        if self.phase is Phase.PRO_AIM:
            self._drain_hits()
            if "btn_b" in buttons:
                self.phase=Phase.STYLE_SELECT
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used)
                self._submit(); return
            if "btn_left" in buttons and self.aim_index>0:
                self.aim_index-=1; self.aim=AIM_ORDER[self.aim_index]
            if "btn_right" in buttons and self.aim_index<2:
                self.aim_index+=1; self.aim=AIM_ORDER[self.aim_index]
            if "btn_a" in buttons:
                self.phase=Phase.PRO_POWER
                self.power_started_at=now
                self.power_last_tick=now
                self.power_charge=0.0
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="power",power_taps=0)
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="aim",aim_position=self._aim_xy(),aim_slots=True)
            self._submit(); return

        if self.phase is Phase.PRO_POWER:
            self._drain_hits()
            if "btn_b" in buttons:
                self.phase=Phase.PRO_AIM
                self.power_started_at=None; self.power_last_tick=None; self.power_charge=0.0; self.power_zone=None
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="aim",aim_position=self._aim_xy(),aim_slots=True)
                self._submit(); return
            dt=max(0.0,now-self.power_last_tick)
            self.power_last_tick=now
            if "btn_a" in buttons: self.power_charge=min(24.0,self.power_charge+POWER_PULSE_BOOST)
            else: self.power_charge=max(0.0,self.power_charge-POWER_DECAY_PER_SECOND*dt)
            if now-self.power_started_at>=POWER_SECONDS:
                locked=int(round(self.power_charge))
                self.power_zone=power_zone_for_taps(locked)
                self.phase=Phase.PRO_THROW_READY
                self.throw_armed=True
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="ready",power_zone=self.power_zone,aim_position=self._aim_xy(),aim_slots=True)
            else:
                self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="power",power_taps=self.power_charge)
            self._submit(); return

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
            self._submit(); return

        if self.phase is Phase.RESULT:
            self._drain_hits()
            if now-self.result_started_at>=RESULT_HOLD_SECONDS: self._finish()
            self._submit(); return

        if self.phase is Phase.PRO_THROW_READY and "btn_b" in buttons:
            self.phase=Phase.PRO_POWER
            self.power_started_at=now; self.power_last_tick=now; self.power_charge=0.0; self.power_zone=None; self.throw_armed=False
            self.cached_frame=render_frame(score=self.score,balls_used=self.balls_used,ui_mode="power",power_taps=0)
            self._submit(); return

        if self.phase is Phase.PRO_THROW_READY:
            hit=self._ready_for_fresh_throw()
            if hit is not None: self._start_roll(resolve_pro_shot(self.aim,hit.x,hit.y,self.power_zone),hit.dart_index,now)
        elif self.phase is Phase.ARCADE_READY:
            hit=self._ready_for_fresh_throw()
            if hit is not None: self._start_roll(resolve_arcade_shot(hit.x,hit.y),hit.dart_index,now)
        self._submit()

def run_roller_ball(facade,frame_seconds=1/30,sleeper=time.sleep,secondary_display:SecondaryDisplay|None=None):
    runtime=RollerBallRuntime(facade,secondary_display=secondary_display)
    try:
        while facade.is_running():
            runtime.step(); sleeper(frame_seconds)
    finally:
        if secondary_display is not None: secondary_display.close()
        facade.close()
