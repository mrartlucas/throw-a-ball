# Throw a Ball

**Throw A Way Games presents Throw a Ball**

## Roller Ball prototype v0.13 recovery

This branch is the cabinet-test recovery pass built directly on `prototype/roller-ball-v0.12`.

Recovered for this test:
- Player-facing **PRO ROLLER** naming.
- Screen 2 setup hierarchy: **GAME -> THROW A BALL**, **MACHINE -> ROLLER BALL**, then **PLAY -> ARCADE / PRO ROLLER**.
- Purple Throw a Ball identity accents on Screen 2 without replacing player or power semantic colors.
- P1 indicator slot on Screen 2.
- Locked Aim remains visible through Power and Throw Ready.
- Locked Power zone remains visible at Throw Ready.
- Power meter still decays visibly when tapping stops.
- Throw Ready is a major Screen 2 billboard state.
- Screen 2 gets a miniature Roller Ball action animation during ball travel.
- Screen 2 gets a large result payoff after the ball lands.
- Pro Aim has more horizontal authority for this playtest: 45% Aim / 55% final dart X.
- Result hold increased slightly to 1.3 seconds so Screen 2 payoff can read.

Preserved:
- Arcade = one physical dart launches one virtual ball.
- Pro = Left/Center/Right Aim -> A lock -> 5-second Test-Your-Might A mash -> Throw Ready -> one scoring dart.
- Fresh-dart gating and stale-hit draining.
- Scoring dart removal before the next ball.
- Yellow/Green/Red power semantics, no numeric player-facing power value.
- 128x160 combined framebuffer with 128x128 Screen 1 and 64x32 Screen 2 in the lower-left.

For development environments that can pass command-line flags:

```bash
python main.py --screen2-window
```
