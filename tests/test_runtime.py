from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.roller_ball import POWER_SECONDS, RESULT_HOLD_SECONDS, ROLL_SECONDS, AimPosition
from throw_a_ball.runtime import Phase, PlayStyle, RollerBallRuntime


class FakeSdk:
    def __init__(self):
        self.running = True
        self.hits = []
        self.active = []
        self.pressed = set()
        self.frames = []
        self.lower_frames = []
        self.closed = False

    def get_dart_hits(self):
        hits, self.hits = self.hits, []
        return hits

    def get_active_darts(self): return list(self.active)
    def get_button_events(self):
        pressed, self.pressed = self.pressed, set()
        return {name: True for name in pressed}
    def update_frame_buffer(self, frame): self.frames.append(bytes(frame)); return True
    def close(self): self.closed = True


class FakeScreen2:
    def __init__(self): self.frames = []; self.closed = False
    def submit(self, frame): self.frames.append(frame)
    def close(self): self.closed = True


class Clock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


def press(runtime, sdk, button):
    sdk.pressed = {button}
    runtime.step()


def enter_play(runtime, sdk, *, pro=False):
    press(runtime, sdk, "btn_a")  # game -> machine
    press(runtime, sdk, "btn_a")  # machine -> play
    if pro: press(runtime, sdk, "btn_right")
    press(runtime, sdk, "btn_a")


def test_setup_back_navigation_and_center_default():
    sdk, clock = FakeSdk(), Clock()
    screen2 = FakeScreen2()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), clock, screen2)
    assert runtime.phase is Phase.GAME_SELECT
    press(runtime, sdk, "btn_a"); assert runtime.phase is Phase.MACHINE_SELECT
    press(runtime, sdk, "btn_b"); assert runtime.phase is Phase.GAME_SELECT
    enter_play(runtime, sdk, pro=True)
    assert runtime.phase is Phase.PRO_AIM
    assert runtime.aim is AimPosition.CENTER
    press(runtime, sdk, "btn_left"); assert runtime.aim is AimPosition.LEFT
    press(runtime, sdk, "btn_right"); assert runtime.aim is AimPosition.CENTER
    press(runtime, sdk, "btn_right"); assert runtime.aim is AimPosition.RIGHT
    press(runtime, sdk, "btn_a"); assert runtime.phase is Phase.PRO_POWER
    press(runtime, sdk, "btn_b"); assert runtime.phase is Phase.PRO_AIM
    press(runtime, sdk, "btn_b"); assert runtime.phase is Phase.STYLE_SELECT
    assert screen2.frames and all(len(frame) == 64 * 32 * 3 for frame in screen2.frames)


def test_pro_uses_one_dart_only_after_aim_and_power():
    sdk, clock = FakeSdk(), Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), clock)
    enter_play(runtime, sdk, pro=True)
    sdk.hits = [(0, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.PRO_AIM and sdk.hits  # Aim never reads a dart.
    press(runtime, sdk, "btn_a")
    runtime.step()
    assert runtime.phase is Phase.PRO_POWER and sdk.hits  # Nor does Power.
    clock.advance(POWER_SECONDS)
    runtime.step()
    assert runtime.phase is Phase.PRO_THROW_READY
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL and sdk.hits == []
    clock.advance(ROLL_SECONDS - 0.01); runtime.step()
    assert runtime.score == 0 and runtime.balls_used == 0
    clock.advance(0.02); runtime.step()
    assert runtime.phase is Phase.RESULT and runtime.balls_used == 1


def test_arcade_roll_scores_at_destination_and_blocks_until_removal():
    sdk, clock = FakeSdk(), Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), clock)
    enter_play(runtime, sdk)
    assert runtime.style is PlayStyle.ARCADE and runtime.phase is Phase.ARCADE_READY
    sdk.hits = [(0, 64, 36)]; sdk.active = [(0, 64, 36)]
    runtime.step(); assert runtime.phase is Phase.BALL_ROLL
    clock.advance(ROLL_SECONDS); runtime.step()
    assert runtime.phase is Phase.RESULT and runtime.score == 50
    sdk.hits = [(0, 64, 36)]
    clock.advance(RESULT_HOLD_SECONDS); runtime.step()
    assert runtime.phase is Phase.WAIT_FOR_REMOVAL and runtime.balls_used == 1
    runtime.step()
    assert runtime.phase is Phase.WAIT_FOR_REMOVAL and sdk.hits  # blocked dart is not read
    sdk.active = []; runtime.step()
    assert runtime.phase is Phase.ARCADE_READY


def test_throw_ready_back_does_not_spend_ball():
    sdk, clock = FakeSdk(), Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), clock)
    enter_play(runtime, sdk, pro=True)
    press(runtime, sdk, "btn_a")
    clock.advance(POWER_SECONDS); runtime.step()
    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.PRO_POWER
    assert runtime.balls_used == 0 and runtime.score == 0
