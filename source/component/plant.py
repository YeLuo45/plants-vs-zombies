import pygame
import math
from source.constants import *

class Plant(pygame.sprite.Sprite):
    def __init__(self, name, row, col, grid):
        super().__init__()
        self.name = name
        self.row = row
        self.col = col
        self.grid = grid
        cfg = PLANTS[name]
        self.hp = cfg['hp']
        self.max_hp = cfg['hp']
        self.attack = cfg['attack']
        self.attack_interval = cfg['interval']
        self.attack_timer = 0
        self.sun_produce = 25 if name == 'sunflower' else 0
        self.sun_timer = 0
        self.sun_interval = 3.0
        self.cooldown = 0
        self.color = cfg['color']
        self.rect = grid.get_cell_rect(row, col)
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.state = 'idle'
        self.anim_timer = 0
        self.exploding = False
        self.explode_timer = 0
        self.armed = False
        self.armed_timer = 0
        self.eating = False
        self.eat_timer = 0
        self.eat_target = None
        # Shake (when damaged)
        self.shake_timer = 0
        self.shake_active = False

    def update(self, dt, events):
        self.anim_timer += dt
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.name == 'sunflower':
            self.sun_timer += dt
            if self.sun_timer >= self.sun_interval:
                self.sun_timer = 0
                return 'produce_sun'
        if self.name == 'potatomine' and not self.armed:
            self.armed_timer += dt
            if self.armed_timer >= 5.0:
                self.armed = True
        if self.name == 'cherrybomb':
            self.explode_timer += dt
            if self.explode_timer >= 0.5 and not self.exploding:
                self.exploding = True
                return 'explode'
        if self.name == 'chomper' and self.eating:
            self.eat_timer += dt
            if self.eat_timer >= 0.5:
                self.eating = False
                self.eat_timer = 0
                if self.eat_target and self.eat_target.hp > 0:
                    self.eat_target.hp = 0
                    self.eat_target = None
                return 'chomp_done'
        if self.attack_interval > 0:
            self.attack_timer += dt
            if self.attack_timer >= self.attack_interval:
                self.attack_timer = 0
                return 'shoot'

        # Shake timer update
        if self.shake_active:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_active = False
                self.shake_timer = 0

        return None

    def draw(self, surface, scroll_x=0, scroll_y=0):
        x, y = self.rect.centerx, self.rect.centery

        # Apply shake offset when active
        if self.shake_active:
            shake_offset = int(math.sin(self.shake_timer * 60) * 5)
            x += shake_offset

        # Apply scroll offset
        x -= scroll_x
        y -= scroll_y

        if self.name == 'torchwood':
            # Draw log body
            pygame.draw.rect(surface, (101, 67, 33), (int(x) - 20, int(y) - 15, 40, 30))
            # Fire on top
            import random
            for i in range(3):
                flame_h = 15 + random.randint(0, 10)
                flame_x = int(x) - 12 + i * 12
                flame_y = int(y) - 15
                pygame.draw.circle(surface, (255, 100 + i * 30, 0), (flame_x, flame_y), 8)
                pygame.draw.circle(surface, (255, 200, 0), (flame_x, flame_y + 3), 5)
        elif self.name == 'potatomine':
            if not self.armed:
                # Underground: small brown mound
                pygame.draw.circle(surface, (101, 67, 33), (int(x), int(y)), 10)
            else:
                # Armed: potato shape
                pygame.draw.ellipse(surface, (205, 165, 50), (int(x) - 15, int(y) - 10, 30, 20))
                # Eyes
                pygame.draw.circle(surface, (0, 0, 0), (int(x) - 5, int(y) - 3), 3)
                pygame.draw.circle(surface, (0, 0, 0), (int(x) + 5, int(y) - 3), 3)
        else:
            pygame.draw.circle(surface, self.color, (int(x), int(y)), 25)
        if self.hp < self.max_hp:
            bar_w = 40
            bar_h = 5
            bx = x - bar_w // 2
            by = y - 35
            pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (0, 200, 0), (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp > 0:
            self.shake_active = True
            self.shake_timer = 0.3
        return self.hp <= 0

    def try_eat_zombie(self, zombie):
        if self.name != 'chomper':
            return False
        if not self.eating and zombie and zombie.row == self.row:
            dist = zombie.x - self.rect.centerx
            if 0 < dist < 60:
                self.eating = True
                self.eat_timer = 0
                self.eat_target = zombie
                return True
        return False

def create_plant(name, row, col, grid):
    return Plant(name, row, col, grid)
