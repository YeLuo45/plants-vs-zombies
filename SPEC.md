# PvZ Clone — Technical Specification

## Constants
- SCREEN: 800 x 600
- GRID: 5 rows x 9 cols
- CELL_SIZE: ~80px (computed from screen / grid)
- FPS: 60

## Plant Stats
| Name | Sun Cost | Cooldown | HP | Attack | Special |
|------|----------|----------|-----|--------|---------|
| sunflower | 50 | 7s | 100 | 0 | produces 25 sun/tick |
| peashooter | 100 | 7s | 100 | 20/tick | shoots pea |
| wallnut | 50 | 30s | 400 | 0 | no attack |
| snowpea | 175 | 7s | 100 | 20/tick | ice pea (slow) |
| cherrybomb | 150 | 50s | 100 | instant | 3x3 AOE at placement |
| potatomine | 25 | 20s | 100 | instant | delayed AOE |
| chomper | 150 | 7s | 100 | instant | melee eat zombie |
| repeater | 200 | 7s | 100 | 20x2/tick | double shot |

## Zombie Stats
| Name | HP | Speed | Attack | Special |
|------|-----|-------|--------|---------|
| basic | 100 | 1.0 | 10/tick | - |
| cone | 200 | 1.0 | 10/tick | cone hat |
| bucket | 400 | 1.0 | 10/tick | bucket hat |
| pole | 100 | 2.0 | 10/tick | vault pole |
| football | 300 | 1.5 | 20/tick | fast + strong |

## Wave Design
- Wave 1: 5 basic zombies, staggered spawns
- Wave 2: 8 zombies (basic + cone)
- Wave 3: 10 zombies (basic + cone + bucket + pole)
- Victory: all 3 waves cleared
- Defeat: any zombie reaches left edge (x < 0)

## Key Classes
- `Game`: main loop, state machine (menu/playing/gameover/victory)
- `Grid`: 5x9 cell management
- `Plant`: base class with update() and draw()
- `Zombie`: base class with update() and draw()
- `Bullet`: pea projectile
- `CardPanel`: bottom card selection
- `SunManager`: sun collection logic
