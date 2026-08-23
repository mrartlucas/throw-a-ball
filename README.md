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

## Current cabinet playtest: v0.34

- Approved Arcade dart/throw feel remains locked.
- Shared lower-screen readiness pattern alternates **THROW READY ↔ current gameplay state** until the next valid throw.
- Bug Splats remains the simple/classic Knock Down machine with DOUBLE SPLAT, TRIPLE SPLAT, and LINE SPLAT bonuses.
- Coconut Bash uses 30 / 50 / 10 scoring, Hear / See / Speak in the 50-point middle row, updated open/closed monkey art, independent Whac-A-Mole timing, and See No Evil as a stun-then-KO two-hit target.
- Balloon Pop keeps the three different row speeds. Gold appears about every 10 seconds and Bomb about every 15-20 seconds. Specials are temporary opportunities rather than permanent unlocks, normally rotate to a different row on the next appearance, and Gold/Bomb may coexist on different rows. Moving balloon layers preserve the full authored sprite tops instead of clipping them to the old row-cell boundaries.
- Fish Bowl Splash keeps its established 1 / 2 / 3-fish scoring. Fish now route left/right within their current row: side bowls can feed the live center bowl to build 2- and 3-fish stacks; a broken center blocks later cross-row travel and reduces the available stack payoff. Fish hops are shown on both screens after impact before score/state lock.
- Current Game Over flow: Screen 1 final scores/winner; Screen 2 **A PLAY AGAIN / B MENU**.

Series-wide interaction, UI, combo, and presentation rules live in the `mrartlucas/throw-a-way-games` universal repository.
