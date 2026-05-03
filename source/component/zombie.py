import pygame
from source.constants import *

class Zombie(pygame.sprite.Sprite):
    def __init__(self, name, x, row, grid):
        super().__init__()
        self.name = name
        self.row = row
        self.grid = grid
        cfg = ZOMBIES[name]
        self.hp = cfg['hp']
        self.max_hp = cfg['hp']
        self.base_speed = cfg['speed']
        self.speed = cfg['speed']
        self.attack = cfg['attack']
        self.attack_interval = cfg['interval']
        self.attack_timer = 0
        self.color = cfg['color']
        self.w = cfg['w']
        self.h = cfg['h']
        self.x = x
        self.y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2
        self.attacking = False
        self.attack_target = None
        self.slow_timer = 0
        self.pole_jumped = False

    def update(self, dt):
        self.attack_timer += dt
        if self.slow_timer > 0:
            self.slow_timer -= dt
            self.speed = self.base_speed * ICE_SLOW_FACTOR
        else:
            self.speed = self.base_speed
        # Find plant to attack
        plant_in_way = None
        for col in range(self.grid.cols):
            p = self.grid.cells[self.row][col]
            if p and hasattr(p, 'hp') and p.hp > 0:
                plant_x = p.rect.centerx
                if self.x - plant_x < 40 and self.x - plant_x > -40:
                    plant_in_way = p
                    break
                elif self.x <= plant_x:
                    break
        if plant_in_way:
            self.attacking = True
            self.attack_target = plant_in_way
            if self.attack_timer >= self.attack_interval:
                self.attack_timer = 0
                dead = plant_in_way.take_damage(self.attack)
                if dead:
                    for c in range(self.grid.cols):
                        if self.grid.cells[self.row][c] == plant_in_way:
                            self.grid.cells[self.row][c] = None
                            break
                    self.attacking = False
                    self.attack_target = None
        else:
            self.attacking = False
            self.attack_target = None
            self.x -= self.speed
        if self.x < self.grid.offset_x - 20:
            return 'reached_home'
        return None

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        pygame.draw.rect(surface, self.color, (x - self.w//2, y - self.h//2, self.w, self.h))
        pygame.draw.circle(surface, (180, 180, 180), (x, y - self.h//2 - 10), 12)
        if self.slow_timer > 0:
            pygame.draw.circle(surface, (150, 200, 255), (x, y), 5, 2)
        if self.hp < self.max_hp:
            bar_w = 40
            bar_h = 5
            bx = x - bar_w // 2
            by = y - self.h//2 - 30
            pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (0, 200, 0), (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))

    def take_damage(self, dmg):
        self.hp -= dmg
        return self.hp <= 0

    def apply_slow(self):
        self.slow_timer = 2.0

def create_zombie(name, x, row, grid):
    return Zombie(name, x, row, grid)
