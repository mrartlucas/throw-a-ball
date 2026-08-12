from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.roller_ball import POWER_SECONDS, RESULT_HOLD_SECONDS, ROLL_SECONDS, PowerZone
from throw_a_ball.runtime import Phase, RollerBallRuntime


class FakeSdk:
    def __init__(self):
        self.running = True
        self.hits = []
        self.active = []
        self.button_events = {}
        self.frames = []
        self.closed = False

    def get_dart_hits(self):
        hits, self.hits = self.hits, []
        return hits

    def get_active_darts(self):
        return list(self.active)

    def get_button_events(self):
        events, self.button_events = self.button_events, {}
        return events

    def update_frame_buffer(self, frame):
        self.frames.append(bytes(frame))
        return True

    def close(self):
        self.closed = True


class FakeSecondaryDisplay:
    def __init__(self):
        self.frames = []
        self.closed = False

    def submit(self, frame):
        self.frames.append(bytes(frame))

    def close(self):
        self.closed = True


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def press(runtime, sdk, button):
    sdk.button_events = {button: True}
    runtime.step()


def reach_play(runtime, sdk):
    assert runtime.phase is Phase.GAME_SELECT
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.MACHINE_SELECT
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.STYLE_SELECT


def start_arcade(runtime, sdk):
    reach_play(runtime, sdk)
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.ARCADE_READY


def arm_fresh_throw(runtime):
    runtime.step()
    assert runtime.throw_armed


def test_setup_flow_and_back_navigation():
    sdk = FakeSdk()
    runtime = RollerBallRuntime(DartsnutFacade(sdk))

    assert runtime.phase is Phase.GAME_SELECT
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.MACHINE_SELECT
    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.GAME_SELECT
    press(runtime, sdk, "btn_a")
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.STYLE_SELECT
    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.MACHINE_SELECT


def test_arcade_scores_only_after_full_ball_travel():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    start_arcade(runtime, sdk)
    arm_fresh_throw(runtime)

    sdk.hits = [(0, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL
    assert runtime.score == 0
    assert runtime.balls_used == 0

    clock.advance(ROLL_SECONDS - 0.01)
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL
    assert runtime.score == 0

    clock.advance(0.02)
    runtime.step()
    assert runtime.phase is Phase.RESULT
    assert runtime.score == 50
    assert runtime.balls_used == 1


def test_stale_hits_are_drained_until_board_is_clear_and_a_new_hit_arrives():
    sdk = FakeSdk()
    runtime = RollerBallRuntime(DartsnutFacade(sdk))
    start_arcade(runtime, sdk)

    sdk.active = [(0, 64, 36)]
    sdk.hits = [(0, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.ARCADE_READY
    assert not runtime.throw_armed
    assert sdk.hits == []

    sdk.active = []
    runtime.step()
    assert runtime.phase is Phase.ARCADE_READY
    assert runtime.throw_armed

    runtime.step()
    assert runtime.phase is Phase.ARCADE_READY
    sdk.hits = [(1, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL


def test_scoring_dart_must_be_removed_before_next_ball_can_arm():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    start_arcade(runtime, sdk)
    arm_fresh_throw(runtime)

    sdk.hits = [(0, 64, 36)]
    sdk.active = [(0, 64, 36)]
    runtime.step()
    clock.advance(ROLL_SECONDS + 0.01)
    runtime.step()
    clock.advance(RESULT_HOLD_SECONDS + 0.01)
    runtime.step()
    assert runtime.phase is Phase.WAIT_FOR_REMOVAL

    sdk.hits = [(0, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.WAIT_FOR_REMOVAL
    assert sdk.hits == []

    sdk.active = []
    runtime.step()
    assert runtime.phase is Phase.ARCADE_READY
    assert not runtime.throw_armed
    runtime.step()
    assert runtime.throw_armed


def test_pro_flow_power_timing_one_dart_and_back_navigation():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    reach_play(runtime, sdk)
    press(runtime, sdk, "btn_right")
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.PRO_AIM
    assert runtime.aim.value == "center"

    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.STYLE_SELECT
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.PRO_AIM
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.PRO_POWER
    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.PRO_AIM
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.PRO_POWER

    for _ in range(4):
        press(runtime, sdk, "btn_a")
    clock.advance(POWER_SECONDS - 0.01)
    runtime.step()
    assert runtime.phase is Phase.PRO_POWER
    clock.advance(0.02)
    runtime.step()
    assert runtime.phase is Phase.PRO_THROW_READY

    press(runtime, sdk, "btn_b")
    assert runtime.phase is Phase.PRO_POWER
    clock.advance(POWER_SECONDS + 0.01)
    runtime.step()
    assert runtime.phase is Phase.PRO_THROW_READY

    sdk.hits = [(2, 64, 36), (3, 96, 35)]
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL
    assert runtime.blocked_dart_index == 2
    assert runtime.balls_used == 0


def test_pro_power_uses_rapid_a_charge_decay_and_five_second_lock():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    reach_play(runtime, sdk)
    press(runtime, sdk, "btn_right")
    press(runtime, sdk, "btn_a")
    press(runtime, sdk, "btn_a")

    for _ in range(7):
        press(runtime, sdk, "btn_a")
    assert runtime.power_charge == 21.0

    clock.advance(1.0)
    runtime.step()
    assert runtime.power_charge == 19.4
    assert runtime.phase is Phase.PRO_POWER

    clock.advance(POWER_SECONDS - 1.0)
    press(runtime, sdk, "btn_a")
    assert runtime.phase is Phase.PRO_THROW_READY
    assert runtime.power_zone is PowerZone.RED


def test_pro_aim_has_exactly_three_bounded_positions_and_defaults_center():
    sdk = FakeSdk()
    runtime = RollerBallRuntime(DartsnutFacade(sdk))
    reach_play(runtime, sdk)
    press(runtime, sdk, "btn_right")
    press(runtime, sdk, "btn_a")

    assert runtime.aim.value == "center"
    press(runtime, sdk, "btn_left")
    assert runtime.aim.value == "left"
    press(runtime, sdk, "btn_left")
    assert runtime.aim.value == "left"
    press(runtime, sdk, "btn_right")
    assert runtime.aim.value == "center"
    press(runtime, sdk, "btn_right")
    assert runtime.aim.value == "right"
    press(runtime, sdk, "btn_right")
    assert runtime.aim.value == "right"


def test_screen_two_receives_distinct_setup_state_frames():
    sdk = FakeSdk()
    secondary = FakeSecondaryDisplay()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), secondary_display=secondary)

    runtime.step()
    game_frame = secondary.frames[-1]
    press(runtime, sdk, "btn_a")
    machine_frame = secondary.frames[-1]
    press(runtime, sdk, "btn_a")
    play_frame = secondary.frames[-1]

    assert len(game_frame) == len(machine_frame) == len(play_frame) == 64 * 32 * 3
    assert len({game_frame, machine_frame, play_frame}) == 3
