from throw_a_ball.roller_ball import BALLS_PER_GAME, resolve_arcade_shot, sample_ball_position


def test_placeholder_pocket_centers_score_exact_values():
    cases = [
        ((32, 35), 100),
        ((64, 36), 50),
        ((96, 35), 100),
        ((64, 53), 40),
        ((64, 70), 30),
        ((64, 89), 20),
    ]
    for (x, y), score in cases:
        assert resolve_arcade_shot(x, y).score == score


def test_outer_bowl_is_forgiving_ten_point_catch():
    assert resolve_arcade_shot(30, 80).score == 10
    assert resolve_arcade_shot(98, 80).score == 10


def test_true_miss_scores_zero():
    assert resolve_arcade_shot(5, 120).score == 0


def test_ball_starts_at_lane_and_finishes_at_target():
    shot = resolve_arcade_shot(64, 36)
    assert sample_ball_position(shot, 0.0) == (64, 121)
    assert sample_ball_position(shot, 1.0) == (shot.target_x, shot.target_y)


def test_game_uses_nine_balls():
    assert BALLS_PER_GAME == 9
