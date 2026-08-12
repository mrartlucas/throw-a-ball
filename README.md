# Throw a Ball

**Throw A Way Games presents Throw a Ball**

Dartsnut / PixelDarts skee-ball arcade game featuring Roller Ball, Bug Bash, Alley Oops, 3 Across, and a hidden physics puzzle game.

## Roller Ball prototype v0.2

Current playtest slice on `prototype/roller-ball-v0.2`:

- single-player Roller Ball
- startup choice between Arcade and Pro
- Arcade: just throw and score
- Pro: dart to SET AIM, remove the aim dart, rapid-tap A during the timed POWER phase, then throw the scoring dart
- Yellow / Green / Red power zones with no percentages
- Power helps correct vertical reach; Aim and the final dart are blended for the shot path
- automatic curve/path correction remains internal
- 9 balls per game
- placeholder 10 / 20 / 30 / 40 / 50 / dual-100 target layout
- animated ball travel and score accumulation
- dart-removal protection
- game-over display and A-button restart

### Style selection

Use Left/Right to switch between the two style cards, then press A.

- Card 1 = Arcade
- Card 2 = Pro

### Pro sequence

1. Throw a dart to set Aim.
2. Remove that dart.
3. Rapid-tap A during the 1.6-second Power window.
4. Yellow = low, Green = medium, Red = high.
5. Throw the scoring dart.

This is still a mechanics playtest using procedural placeholder graphics. Final cabinet art and the 64×32 lower-screen presentation come after the control feel is approved.
