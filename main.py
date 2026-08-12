"""Throw a Ball Roller Ball v0.12 entry point."""

import argparse
import sys

from throw_a_ball.platform import DartsnutFacade
from throw_a_ball.runtime import run_roller_ball


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--screen2-window", action="store_true")
    options, sdk_args = parser.parse_known_args()
    sys.argv = [sys.argv[0], *sdk_args]

    from pydartsnut import Dartsnut

    secondary_display = None
    if options.screen2_window:
        from throw_a_ball.secondary_display import SecondaryDisplayWindow
        secondary_display = SecondaryDisplayWindow()
    run_roller_ball(DartsnutFacade(Dartsnut()), secondary_display=secondary_display)


if __name__ == "__main__":
    main()
