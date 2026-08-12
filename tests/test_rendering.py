from throw_a_ball.rendering import RGB888_BYTE_LENGTH, render_frame


def test_framebuffer_is_128_by_128_rgb888():
    frame = render_frame(score=0, balls_used=0)
    assert isinstance(frame, bytes)
    assert len(frame) == RGB888_BYTE_LENGTH == 128 * 128 * 3


def test_renderer_accepts_game_over_score():
    frame = render_frame(score=450, balls_used=9, message_code=3)
    assert len(frame) == RGB888_BYTE_LENGTH
