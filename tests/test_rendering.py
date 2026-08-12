from throw_a_ball.rendering import (
    LOWER_RGB888_BYTE_LENGTH, LOWER_WIDTH, RGB888_BYTE_LENGTH,
    lower_text_width, render_frame, render_lower_frame,
)
from throw_a_ball.roller_ball import AimPosition


def test_framebuffer_is_128_by_128_rgb888():
    frame = render_frame(score=0, balls_used=0)
    assert isinstance(frame, bytes)
    assert len(frame) == RGB888_BYTE_LENGTH == 128 * 128 * 3


def test_renderer_accepts_game_over_score():
    frame = render_frame(score=450, balls_used=9, message_code=3)
    assert len(frame) == RGB888_BYTE_LENGTH


def test_lower_display_states_are_64_by_32_and_helpers_fit():
    helpers = ("A NEXT", "A NEXT  B BACK", "A LOCK  B BACK", "A MASH  B BACK", "THROW  B BACK")
    for helper in helpers:
        assert lower_text_width(helper) <= LOWER_WIDTH
        assert len(render_lower_frame("PLAY", "PRO", helper)) == LOWER_RGB888_BYTE_LENGTH


def test_all_three_directional_aim_states_render():
    frames = [render_lower_frame("AIM", "", "A LOCK  B BACK", aim=aim) for aim in AimPosition]
    assert all(len(frame) == LOWER_RGB888_BYTE_LENGTH for frame in frames)
    assert len(set(frames)) == 3


def test_main_screen_uses_arrows_and_setup_keeps_board_visible():
    plain = render_frame(score=0, balls_used=0)
    aim = render_frame(score=0, balls_used=0, ui_mode="aim", aim_position=(64, 96), aim_slots=True)
    # The pocket area remains identical while the subtle lane indicator changes.
    assert plain[:90 * 128 * 3] == aim[:90 * 128 * 3]
    assert plain != aim
