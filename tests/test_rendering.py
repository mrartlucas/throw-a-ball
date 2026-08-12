from throw_a_ball.rendering import (
    BLACK,
    LOWER_RGB888_BYTE_LENGTH,
    RGB888_BYTE_LENGTH,
    render_frame,
    render_lower_frame,
)
from throw_a_ball.roller_ball import AimPosition


def test_framebuffer_is_128_by_128_rgb888():
    frame = render_frame(score=0, balls_used=0)
    assert isinstance(frame, bytes)
    assert len(frame) == RGB888_BYTE_LENGTH == 128 * 128 * 3


def test_renderer_accepts_game_over_score():
    frame = render_frame(score=450, balls_used=9, message_code=3)
    assert len(frame) == RGB888_BYTE_LENGTH


def test_screen_two_framebuffer_is_64_by_32_rgb888():
    frame = render_lower_frame("GAME", "ROLLER BALL", "A NEXT")
    assert isinstance(frame, bytes)
    assert len(frame) == LOWER_RGB888_BYTE_LENGTH == 64 * 32 * 3


def test_all_three_lower_screen_aim_arrow_states_are_distinct():
    frames = [
        render_lower_frame("AIM", "", "A LOCK  B BACK", aim=aim)
        for aim in AimPosition
    ]
    assert len(set(frames)) == 3
    assert all(len(frame) == LOWER_RGB888_BYTE_LENGTH for frame in frames)


def test_screen_one_keeps_roller_ball_board_visible_during_setup():
    setup_frame = render_frame(score=0, balls_used=0)

    def pixel(x, y):
        offset = (y * 128 + x) * 3
        return tuple(setup_frame[offset : offset + 3])

    # Pocket borders and the wooden lane are stable board landmarks.
    assert pixel(64, 23) != BLACK
    assert pixel(64, 116) != BLACK
