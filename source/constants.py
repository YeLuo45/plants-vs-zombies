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
CARD_COOLDOWN = (30, 30, 30)
SUN_BG_COLOR = (255, 255, 100)
TEXT_COLOR = (255, 255, 255)
RED = (200, 50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (120, 120, 120)
BROWN = (139, 90, 43)
LAWN_MOWER_COLOR = (0, 180, 0)
PURPLE = (150, 50, 200)
CYAN = (0, 200, 220)
DARK_GREEN = (30, 120, 30)
WATERMELON_COLOR = (50, 150, 50)
ICE_BLUE = (150, 220, 255)

# Sun
SUN_VALUE = 50
SUN_DROP_INTERVAL = 10

# UI
MENUBAR_HEIGHT = 80
CARD_PANEL_Y = SCREEN_HEIGHT - 100
CARD_W = 70
CARD_H = 80
CARD_GAP = 10
SHOVEL_W = 60
SHOVEL_H = 60

# ============================================================
# Game Content Constants
# ============================================================

# Plant definitions (13 plants)
PLANTS = {
    'sunflower':    {'cost': 50,  'cooldown': 7,  'hp': 100,  'attack': 0,   'interval': 0,    'color': (255, 255, 0),    'w': 60, 'h': 60, 'desc': 'Sunflower'},
    'peashooter':   {'cost': 100, 'cooldown': 7,  'hp': 100,  'attack': 20,  'interval': 1.0,  'color': (0, 200, 0),     'w': 60, 'h': 60, 'desc': 'Peashooter'},
    'wallnut':      {'cost': 50,  'cooldown': 30, 'hp': 400,  'attack': 0,   'interval': 0,    'color': (150, 100, 50),   'w': 60, 'h': 60, 'desc': 'Wallnut'},
    'snowpea':      {'cost': 175, 'cooldown': 7,  'hp': 100,  'attack': 20,  'interval': 1.0,  'color': (100, 200, 255), 'w': 60, 'h': 60, 'desc': 'Snow Pea'},
    'cherrybomb':   {'cost': 150, 'cooldown': 50, 'hp': 100,  'attack': 999, 'interval': 0,    'color': (200, 0, 0),     'w': 60, 'h': 60, 'desc': 'Cherry Bomb'},
    'potatomine':   {'cost': 25,  'cooldown': 20, 'hp': 100,  'attack': 999, 'interval': 0,    'color': (200, 150, 50),   'w': 60, 'h': 60, 'desc': 'Potato Mine'},
    'chomper':      {'cost': 150, 'cooldown': 7,  'hp': 100,  'attack': 999, 'interval': 0,    'color': (0, 200, 100),   'w': 60, 'h': 60, 'desc': 'Chomper'},
    'repeater':     {'cost': 200, 'cooldown': 7,  'hp': 100,  'attack': 20,  'interval': 1.0,  'color': (0, 150, 0),     'w': 60, 'h': 60, 'desc': 'Repeater'},
    'torchwood':    {'cost': 175, 'cooldown': 7,  'hp': 100,  'attack': 0,   'interval': 0,    'color': (139, 69, 19),   'w': 60, 'h': 60, 'desc': 'Torchwood'},
    # P2-B new plants
    'squash':       {'cost': 50,  'cooldown': 30, 'hp': 100,  'attack': 999, 'interval': 0,    'color': (0, 180, 0),     'w': 60, 'h': 60, 'desc': 'Squash'},
    'wintermelon':  {'cost': 300, 'cooldown': 7,  'hp': 100,  'attack': 20,  'interval': 1.0,  'color': WATERMELON_COLOR,'w': 60, 'h': 60, 'desc': 'Winter Melon'},
    'iceshroom':    {'cost': 75,  'cooldown': 50, 'hp': 100,  'attack': 0,   'interval': 0,    'color': ICE_BLUE,        'w': 60, 'h': 60, 'desc': 'Ice Shroom'},
    'hypnoshroom':  {'cost': 75,  'cooldown': 30, 'hp': 100,  'attack': 0,   'interval': 0,    'color': PURPLE,          'w': 60, 'h': 60, 'desc': 'Hypno Shroom'},
    'scaredy':      {'cost': 50,  'cooldown': 7,  'hp': 100, 'attack': 0,   'interval': 0,    'color': (200, 200, 100), 'w': 60, 'h': 60, 'desc': 'Scaredy Shroom'},
    # H-plants
    'zapricot':     {'cost': 150, 'cooldown': 5,  'hp': 100, 'attack': 40, 'interval': 2.0, 'color': (255, 255, 100), 'w': 60, 'h': 60, 'desc': 'Zapricot'},
    'cattail':      {'cost': 225, 'cooldown': 7,  'hp': 100, 'attack': 80, 'interval': 1.5, 'color': (50, 180, 50),   'w': 60, 'h': 60, 'desc': 'Cattail'},
    'gloomshroom':  {'cost': 150, 'cooldown': 10, 'hp': 100, 'attack': 0,  'interval': 0,   'color': (100, 150, 50),  'w': 60, 'h': 60, 'desc': 'Gloom Shroom'},
    # Zen Special plants
    'marigold':     {'cost': 50,  'cooldown': 0,  'hp': 100, 'attack': 0,  'interval': 0,   'color': (255, 215, 0),   'w': 60, 'h': 60, 'desc': 'Marigold'},
    'goldmagnet':   {'cost': 75,  'cooldown': 0,  'hp': 100, 'attack': 0,  'interval': 0,   'color': (200, 200, 220), 'w': 60, 'h': 60, 'desc': 'Gold Magnet'},
}

# Zombie definitions
ZOMBIES = {
    'basic':    {'hp': 100, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (100, 150, 100), 'w': 50, 'h': 70, 'desc': 'Zombie'},
    'cone':     {'hp': 200, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (255, 150, 0),   'w': 50, 'h': 70, 'desc': 'Conehead Zombie'},
    'bucket':   {'hp': 400, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (150, 150, 150),  'w': 50, 'h': 70, 'desc': 'Buckethead Zombie'},
    'pole':     {'hp': 100, 'speed': 0.5, 'attack': 10, 'interval': 0.5, 'color': (150, 100, 200), 'w': 50, 'h': 70, 'desc': 'Pole Vaulting Zombie'},
    'football': {'hp': 300, 'speed': 0.5, 'attack': 20, 'interval': 0.5, 'color': (80, 80, 80),    'w': 55, 'h': 75, 'desc': 'Football Zombie'},
    # P2-A new zombies
    'newspaper': {'hp': 100, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (120, 100, 140), 'w': 50, 'h': 70, 'desc': 'Newspaper Zombie'},
    'miner':    {'hp': 100, 'speed': 0.5, 'attack': 10, 'interval': 0.5, 'color': (100, 80, 60),   'w': 50, 'h': 70, 'desc': 'Digger Zombie'},
    'ladder':   {'hp': 100, 'speed': 0.3, 'attack': 10, 'interval': 0.5, 'color': (100, 140, 100), 'w': 50, 'h': 70, 'desc': 'Ladder Zombie'},
}

# 10-wave progressive difficulty (includes 8 zombie types)
WAVES = [
    {'zombies': [('basic', 3), ('cone', 2)],                                                       'spawn_delay': 3.0},
    {'zombies': [('basic', 4), ('cone', 3)],                                                       'spawn_delay': 3.0},
    {'zombies': [('basic', 4), ('cone', 3), ('bucket', 1)],                                         'spawn_delay': 2.5},
    {'zombies': [('basic', 5), ('cone', 3), ('bucket', 2), ('pole', 1)],                           'spawn_delay': 2.5},
    {'zombies': [('basic', 5), ('cone', 3), ('bucket', 2), ('pole', 2), ('football', 1)],          'spawn_delay': 2.0},
    {'zombies': [('basic', 6), ('cone', 4), ('bucket', 2), ('pole', 2), ('football', 2), ('newspaper', 1)], 'spawn_delay': 2.0},
    {'zombies': [('basic', 6), ('cone', 5), ('bucket', 3), ('pole', 3), ('football', 2), ('newspaper', 2)], 'spawn_delay': 1.5},
    {'zombies': [('basic', 7), ('cone', 5), ('bucket', 4), ('pole', 3), ('football', 3), ('newspaper', 2), ('ladder', 1)], 'spawn_delay': 1.5},
    {'zombies': [('basic', 8), ('cone', 6), ('bucket', 4), ('pole', 4), ('football', 3), ('newspaper', 3), ('ladder', 2), ('miner', 1)], 'spawn_delay': 1.0},
    {'zombies': [('basic', 10), ('cone', 8), ('bucket', 5), ('pole', 5), ('football', 4), ('newspaper', 4), ('ladder', 3), ('miner', 2)], 'spawn_delay': 0.8},
]

# Bullet stats
BULLET_DAMAGE = 20
BULLET_SPEED = 5
ICE_SLOW_FACTOR = 0.5
MELON_SPLASH_RADIUS = 60

# Lawn mower
MOWER_POS_X = GRID_OFFSET_X - 5
MOWER_WIDTH = 25
MOWER_HEIGHT = 35
