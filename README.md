# Throw a Ball

**Throw A Way Games presents Throw a Ball**

Dartsnut / PixelDarts skee-ball arcade game featuring Roller Ball, Bug Bash, Alley Oops, 3 Across, and a hidden physics puzzle game.

## Rollerball v0.22 playtest

v0.22 is built directly from the user-approved **v0.21 IMPACT PHYSICS** cabinet build. The v0.21 loading sequence, second-screen setup, three-position Pro Aim, power flow, dart lifecycle, impact physics, and 3 throws x 3 rounds structure are preserved.

Changes in v0.22:

- Live Rollerball animation uses the authored nine-ball sprite library instead of the placeholder ball.
- Single-player uses the base ball set.
- Multiplayer uses the active player's complete color set: P1 Blue, P2 Red, P3 Green, P4 Yellow.
- The nine authored balls cycle in fixed order across each player's nine throws.
- Screen 1 score is larger and centered at the top.
- Ball count is removed from Screen 1 and displayed beneath the P# status area on Screen 2.
- Pro Aim remains the Throw a Strike-style selector reduced to **three fixed lane positions: Left / Center / Right** because Rollerball has a narrower lane.

The cabinet playtest package for this branch is `Throw-a-Ball-Rollerball-v0.22-BALL-ART-HUD.zip`. Local validation: **66 tests passed**.

## Development Status

Rollerball is the active playable prototype. This branch documents the v0.22 cabinet test while the umbrella Throw A Way Games repository continues to own shared framebuffer, player-color, and secondary-screen rules.
