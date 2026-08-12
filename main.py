"""Throw a Ball Roller Ball v0.1 entry point."""

from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.runtime import run_roller_ball


def main() -> None:
    from pydartsnut import Dartsnut

    run_roller_ball(DartsnutFacade(Dartsnut()))


if __name__ == "__main__":
    main()
