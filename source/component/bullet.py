import pygame
import random
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

    def draw(self, surface, scroll_x=0, scroll_y=0):
        color = (100, 200, 255) if self.ice else (0, 200, 0)
        pygame.draw.circle(surface, color, (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius)
        if self.ice:
            pygame.draw.circle(surface, (200, 230, 255), (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius - 3)

    def check_collision(self, zombies):
        for z in zombies:
            if z.row == self.row:
                dist = abs(self.x - z.x)
                if dist < 30:
                    hit = z.take_damage(self.damage)
                    if self.ice:
                        z.apply_slow()
                    self.alive = False
                    return z, self.x, self.y, self.ice
        return None, 0, 0, False


class HitParticle:
    """Circular shockwave effect when bullet hits a zombie."""
    def __init__(self, x, y, ice):
        self.x = x
        self.y = y
        self.ice = ice
        self.timer = 0
        self.duration = 0.3
        self.alive = True
        self.initial_radius = 5
        self.max_radius = 25

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        progress = self.timer / self.duration
        radius = int(self.initial_radius + (self.max_radius - self.initial_radius) * progress)
        alpha = int(255 * (1.0 - progress))
        sx = int(self.x - scroll_x)
        sy = int(self.y - scroll_y)
        if self.ice:
            pygame.draw.circle(surface, (150, 220, 255, alpha), (sx, sy), radius, 2)
        else:
            pygame.draw.circle(surface, (0, 200, 0, alpha), (sx, sy), radius, 2)

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

    def draw(self, surface, scroll_x=0, scroll_y=0):
        color = (255, 50, 50) if self.radius < 40 else (255, 150, 0)
        pygame.draw.circle(surface, color, (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius)

class BiteParticle:
    """Plant debris particles when zombie bites."""
    def __init__(self, x, y):
        import random
        self.x = x
        self.y = y
        # Random debris chunks
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, 1)
        self.timer = 0
        self.duration = 0.4
        self.alive = True
        self.particle_count = 5
        self.size = random.randint(3, 6)

    def update(self, dt):
        self.timer += dt
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # gravity
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        # Draw a few small debris chunks
        import random
        for i in range(self.particle_count):
            progress = self.timer / self.duration
            alpha = int(255 * (1.0 - progress))
            ox = int(self.vx * self.timer * 5 + random.randint(-5, 5))
            oy = int(self.vy * self.timer * 5 + random.randint(-5, 5))
            px = int(self.x - scroll_x + ox)
            py = int(self.y - scroll_y + oy)
            color = (60 + random.randint(0, 40), 120 + random.randint(0, 60), 30)
            pygame.draw.circle(surface, color, (px, py), self.size - i)

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

    def draw(self, surface, scroll_x=0, scroll_y=0):
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius)
        pygame.draw.circle(surface, (255, 200, 0), (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius - 5)
