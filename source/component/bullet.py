from source.constants import *
import random
import math

import pygame


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, row, grid, ice=False, splash=False, fire=False):
        super().__init__()
        self.x = x
        self.y = y
        self.row = row
        self.grid = grid
        self.ice = ice
        self.splash = splash
        self.fire = fire
        self.speed = BULLET_SPEED
        self.damage = BULLET_DAMAGE
        self.radius = 8 if not splash else 14
        self.alive = True
        self.y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2

    def update(self, dt):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 20:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        dx = int(self.x - scroll_x)
        dy = int(self.y - scroll_y)
        if self.splash:
            # Winter melon: large green sphere with stripes
            pygame.draw.circle(surface, WATERMELON_COLOR, (dx, dy), self.radius)
            pygame.draw.circle(surface, (30, 100, 30), (dx, dy), self.radius, 2)
            if self.ice:
                pygame.draw.circle(surface, ICE_BLUE, (dx, dy), self.radius - 4)
        elif self.fire:
            # Fire bullet (from Torchwood)
            pygame.draw.circle(surface, (255, 100, 0), (dx, dy), self.radius)
            pygame.draw.circle(surface, (255, 200, 0), (dx, dy), self.radius - 3)
        elif self.ice:
            pygame.draw.circle(surface, (100, 200, 255), (dx, dy), self.radius)
            pygame.draw.circle(surface, WHITE, (dx, dy), self.radius - 3)
        else:
            pygame.draw.circle(surface, (0, 200, 0), (dx, dy), self.radius)

    def check_collision(self, zombies):
        for z in zombies:
            dist = abs(self.x - z.x)
            col_dist = abs(z.row - self.row)
            if dist < 30 and col_dist == 0:
                if self.splash:
                    for z2 in zombies:
                        z2_dist = abs(self.x - z2.x)
                        z2_row = abs(z2.row - self.row)
                        if z2_dist < MELON_SPLASH_RADIUS and z2_row <= 1:
                            z2.take_damage(self.damage)
                            if self.ice:
                                z2.apply_slow()
                    z.take_damage(self.damage)
                    if self.ice:
                        z.apply_slow()
                else:
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

    def draw(self, surface, scroll_x=0, scroll_y=0):
        color = (255, 50, 50) if self.radius < 40 else (255, 150, 0)
        pygame.draw.circle(surface, color, (int(self.x - scroll_x), int(self.y - scroll_y)), self.radius)



class IceBlastEffect:
    def __init__(self):
        self.timer = 0
        self.duration = 1.5
        self.alive = True
        self.freeze_radius = 2000

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        alpha = int(80 * (1.0 - self.timer / self.duration))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((150, 220, 255, alpha))
        surface.blit(overlay, (0, 0))


class HitParticle:
    def __init__(self, x, y, ice=False):
        self.x = x + random.uniform(-5, 5)
        self.y = y + random.uniform(-5, 5)
        self.ice = ice
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, 1)
        self.timer = 0
        self.alive = True

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.timer += dt
        if self.timer > 0.3:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        color = (150, 200, 255) if self.ice else (200, 200, 100)
        pygame.draw.circle(surface, color, (int(self.x - scroll_x), int(self.y - scroll_y)), 3)


class BiteParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-4, 1)
        self.timer = 0
        self.alive = True

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.timer += dt
        if self.timer > 0.5:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        pygame.draw.circle(surface, (0, 200, 100), (int(self.x - scroll_x), int(self.y - scroll_y)), 3)


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
