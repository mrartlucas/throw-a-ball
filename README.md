# Throw a Ball

**Throw A Way Games presents Throw a Ball**

Dartsnut / PixelDarts arcade-ball collection built around three machine families.

## Current machine families

### Alley Roller
- Roller Ball
- 3 Across
- Pitch Perfect

### Basket-Roll
- Blacktop Bounce
- Jungle Ball
- Mug Drop
- Rum Run
- Fish in a Barrel

### Knock Down
- Bug Splats
- Coconut Bash
- Balloon Pop
- Fish Bowl Splash

## Current cabinet playtest: v0.33

- Approved Arcade dart/throw feel is locked and should not be changed casually.
- Shared lower-screen readiness pattern alternates **THROW READY ↔ current gameplay state** until the next valid throw.
- Bug Splats is the simple/classic Knock Down machine: DOUBLE SPLAT, TRIPLE SPLAT, and row/column/diagonal LINE SPLAT bonuses.
- Coconut Bash uses 30 / 50 / 10 scoring with Hear / See / Speak centered in the 50-point middle row; See No Evil is always a two-hit stun-then-KO target.
- Balloon Pop uses drifting air-stream rows with clearly different speeds. Gold and bomb targets are rare timed specials and may coexist on different rows.
- Fish Bowl Splash scores the current 1 / 2 / 3-fish stack and migrates fish down water rails into remaining bowls.
- Current Game Over flow: Screen 1 final scores/winner; Screen 2 **A PLAY AGAIN / B MENU**.

Series-wide interaction, UI, combo, and presentation rules live in the `mrartlucas/throw-a-way-games` universal repository.
