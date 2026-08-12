# Throw a Ball

**Throw A Way Games presents Throw a Ball**

## Roller Ball prototype v0.12

This branch is the corrected v0.12 line built directly on `prototype/roller-ball-v0.11`.

Preserved from v0.11:
- fresh-dart gating / stale-hit draining
- 5-second Test-Your-Might Pro power mash
- charge decay and scaled power behavior
- immediate Pro throw arming after Power
- three fixed Aim positions

Added for v0.12:
- GAME -> MACHINE -> PLAY setup hierarchy
- B-button back navigation
- 64x32 Screen 2 setup renderer
- pygame Screen 2 emulator preview
- small Left / Center / Right Aim arrows on Screen 1
- Roller Ball board remains visible during setup
- 1.2-second readable ball travel before scoring

Arcade remains: throw one physical dart, watch the virtual ball travel, score, remove the dart, next ball.

Pro remains: select Left / Center / Right Aim, lock with A, mash A during the 5-second Power window, reach Throw Ready, then throw one physical scoring dart.

For development environments that can pass command-line flags, Screen 2 can be previewed with:

```bash
python main.py --screen2-window
```

The Dartsnut Agent playtest package may use an Agent-specific launcher so the user does not need Terminal access.
