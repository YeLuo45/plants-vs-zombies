import pygame
from source.constants import *

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, row, grid, ice=False):
        super().__init__()
        self.x = x
        self.y = y
        self.row = row
        self.grid = grid
        self.ice = ice
        self.speed = BULLET_SPEED
        self.damage = BULLET_DAMAGE
        self.radius = 8
        self.alive = True
        self.y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2

    def update(self, dt):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 20:
            self.alive = False

    def draw(self, surface):
        color = (100, 200, 255) if self.ice else (0, 200, 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        if self.ice:
            pygame.draw.circle(surface, (200, 230, 255), (int(self.x), int(self.y)), self.radius - 3)

    def check_collision(self, zombies):
        for z in zombies:
            if z.row == self.row:
                dist = abs(self.x - z.x)
                if dist < 30:
                    hit = z.take_damage(self.damage)
                    if self.ice:
                        z.apply_slow()
                    self.alive = False
                    return z
        return None

class ExplosionEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 80
        self.timer = 0
        self.duration = 0.5
        self.alive = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False
        else:
            progress = self.timer / self.duration
            self.radius = int(5 + (self.max_radius - 5) * progress)

    def draw(self, surface):
        color = (255, 50, 50) if self.radius < 40 else (255, 150, 0)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)

class SunParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 0.5
        self.alive = True
        self.radius = 15
        self.floating = False

    def update(self, dt):
        self.timer += dt
        if self.timer < self.duration:
            self.y -= 0.5
        else:
            self.floating = True
            self.y += 0.3

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 200, 0), (int(self.x), int(self.y)), self.radius - 5)
