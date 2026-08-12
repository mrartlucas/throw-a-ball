# Throw a Ball

**Throw A Way Games presents Throw a Ball**

Dartsnut / PixelDarts skee-ball arcade game featuring Roller Ball, Bug Bash, Alley Oops, 3 Across, and a hidden physics puzzle game.

## Roller Ball prototype v0.1

Current playable slice on `prototype/roller-ball-v0.1`:

- single-player Arcade mode
- 128×128 RGB888 main playfield
- 9 balls per game
- placeholder Roller Ball target layout: 10 / 20 / 30 / 40 / 50 / dual 100s
- fresh dart hit starts one animated ball roll
- target resolution and score accumulation
- forgiving 10-point outer catch area
- dart-removal protection so a dart left in the board cannot repeat-score
- game-over display and A-button restart
- procedural placeholder art so gameplay can be tested before final assets

Run with the Dartsnut environment available:

```bash
python main.py
```

Run tests:

```bash
python -m pytest -q
```

## Next development step

Playtest Arcade mode first. Once the target mapping and basic ball feel are approved, add Pro mode with Set Aim, rapid-button Yellow/Green/Red Power, compensation, auto-curve, and trick-shot hooks.

The 64×32 lower display remains outside this first code slice because the verified `pydartsnut==1.2.1` package interface does not expose a secondary-display API. We can wire the lower screen when the cabinet/emulator interface used for it is confirmed.
