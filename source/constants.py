import pygame

# ============================================================
# Display Constants
# ============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Grid
GRID_ROWS = 5
GRID_COLS = 9
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 100
CELL_WIDTH = (SCREEN_WIDTH - GRID_OFFSET_X) // GRID_COLS
CELL_HEIGHT = (SCREEN_HEIGHT - GRID_OFFSET_Y - 80) // GRID_ROWS

# Colors
BG_COLOR = (50, 150, 50)
GRID_LINE_COLOR = (30, 100, 30)
CARD_BG_COLOR = (50, 50, 50)
CARD_SELECTED = (100, 200, 100)
SUN_BG_COLOR = (255, 255, 100)
TEXT_COLOR = (255, 255, 255)
RED = (200, 50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Sun
SUN_VALUE = 50
SUN_DROP_INTERVAL = 10

# UI
MENUBAR_HEIGHT = 80
CARD_PANEL_Y = SCREEN_HEIGHT - 100

# ============================================================
# Game Content Constants
# ============================================================

# Plant definitions
PLANTS = {
    'sunflower':   {'cost': 50,  'cooldown': 7,  'hp': 100, 'attack': 0,  'interval': 0,  'color': (255, 255, 0),   'w': 60, 'h': 60, 'desc': 'Sunflower'},
    'peashooter':  {'cost': 100, 'cooldown': 7,  'hp': 100, 'attack': 20, 'interval': 1.0,'color': (0, 200, 0),    'w': 60, 'h': 60, 'desc': 'Peashooter'},
    'wallnut':     {'cost': 50,  'cooldown': 30, 'hp': 400, 'attack': 0,  'interval': 0,  'color': (150, 100, 50),  'w': 60, 'h': 60, 'desc': 'Wallnut'},
    'snowpea':     {'cost': 175, 'cooldown': 7,  'hp': 100, 'attack': 20, 'interval': 1.0,'color': (100, 200, 255), 'w': 60, 'h': 60, 'desc': 'Snow Pea'},
    'cherrybomb':  {'cost': 150, 'cooldown': 50, 'hp': 100, 'attack': 999,'interval': 0,  'color': (200, 0, 0),    'w': 60, 'h': 60, 'desc': 'Cherry Bomb'},
    'potatomine':  {'cost': 25,  'cooldown': 20, 'hp': 100, 'attack': 999,'interval': 0,  'color': (200, 150, 50), 'w': 60, 'h': 60, 'desc': 'Potato Mine'},
    'chomper':     {'cost': 150, 'cooldown': 7,  'hp': 100, 'attack': 999,'interval': 0,  'color': (0, 200, 100),  'w': 60, 'h': 60, 'desc': 'Chomper'},
    'repeater':    {'cost': 200, 'cooldown': 7,  'hp': 100, 'attack': 20, 'interval': 1.0,'color': (0, 150, 0),    'w': 60, 'h': 60, 'desc': 'Repeater'},
}

# Zombie definitions
ZOMBIES = {
    'basic':    {'hp': 100, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (100, 150, 100), 'w': 50, 'h': 70, 'desc': 'Zombie'},
    'cone':    {'hp': 200, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (255, 150, 0),   'w': 50, 'h': 70, 'desc': 'Conehead Zombie'},
    'bucket':  {'hp': 400, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (150, 150, 150),  'w': 50, 'h': 70, 'desc': 'Buckethead Zombie'},
    'pole':    {'hp': 100, 'speed': 0.6, 'attack': 10, 'interval': 0.5, 'color': (150, 100, 200), 'w': 50, 'h': 70, 'desc': 'Pole Vaulting Zombie'},
    'football':{'hp': 300, 'speed': 0.5, 'attack': 20, 'interval': 0.5, 'color': (80, 80, 80),    'w': 55, 'h': 75, 'desc': 'Football Zombie'},
}

# Wave definitions
WAVES = [
    {'zombies': [('basic', 3), ('cone', 2)], 'spawn_delay': 3.0},
    {'zombies': [('basic', 4), ('cone', 3), ('bucket', 1)], 'spawn_delay': 2.5},
    {'zombies': [('basic', 5), ('cone', 3), ('bucket', 2), ('pole', 2)], 'spawn_delay': 2.0},
]

# Bullet stats
BULLET_DAMAGE = 20
BULLET_SPEED = 5
ICE_SLOW_FACTOR = 0.5
