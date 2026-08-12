from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.roller_ball import RESULT_HOLD_SECONDS, ROLL_SECONDS
from throw_a_ball.runtime import Phase, RollerBallRuntime


class FakeSdk:
    def __init__(self):
        self.running = True
        self.hits = []
        self.active = []
        self.a = False
        self.frames = []
        self.closed = False

    def get_dart_hits(self):
        hits, self.hits = self.hits, []
        return hits

    def get_active_darts(self):
        return list(self.active)

    def get_button_events(self):
        value = self.a
        self.a = False
        return {"btn_a": value}

    def update_frame_buffer(self, frame):
        self.frames.append(bytes(frame))
        return True

    def close(self):
        self.closed = True


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_one_center_50_throw_scores_after_roll():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    sdk.hits = [(0, 64, 36)]
    runtime.step()
    assert runtime.phase is Phase.BALL_ROLL
    clock.advance(ROLL_SECONDS + 0.01)
    runtime.step()
    assert runtime.phase is Phase.RESULT
    assert runtime.score == 50
    assert runtime.balls_used == 1


def test_dart_must_be_removed_before_next_ball():
    sdk = FakeSdk()
    clock = Clock()
    runtime = RollerBallRuntime(DartsnutFacade(sdk), monotonic=clock)
    sdk.hits = [(0, 64, 36)]
    sdk.active = [(0, 64, 36)]
    runtime.step()
    clock.advance(ROLL_SECONDS + 0.01)
    runtime.step()
    clock.advance(RESULT_HOLD_SECONDS + 0.01)
    runtime.step()
    assert runtime.phase is Phase.WAIT_FOR_REMOVAL
    sdk.active = []
    runtime.step()
    assert runtime.phase is Phase.READY
