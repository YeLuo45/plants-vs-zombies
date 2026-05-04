from source.constants import *
import random
import math

import pygame


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, row, grid, ice=False, splash=False, fire=False, electric=False, spike=False):
        super().__init__()
        self.x = x
        self.y = y
        self.row = row
        self.grid = grid
        self.ice = ice
        self.splash = splash
        self.fire = fire
        self.electric = electric
        self.spike = spike
        self.speed = BULLET_SPEED
        self.damage = BULLET_DAMAGE
        self.radius = 8 if not splash else 14
        if electric:
            self.radius = 10
        if spike:
            self.radius = 6
            self.speed = BULLET_SPEED * 2
        self.alive = True
        self.y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2
        self.start_x = x
        self.start_y = self.y
        self.target_x = None
        self.target_y = None
        self.arc_height = 0
        self.hit_done = False

    def update(self, dt):
        if self.spike and self.target_x is not None:
            # Move toward target with arc
            dx = self.target_x - self.start_x
            progress = (self.x - self.start_x) / dx if dx != 0 else 1.0
            progress = max(0, min(1, progress))
            # Arc: parabolic height
            arc = 4 * self.arc_height * progress * (1 - progress)
            self.y = self.start_y - arc
            if dx != 0:
                sign = 1 if dx > 0 else -1
                self.x += sign * min(abs(dx) / 1.0, BULLET_SPEED * 2)
            else:
                self.x = self.target_x
            if (dx > 0 and self.x >= self.target_x) or (dx < 0 and self.x <= self.target_x):
                self.x = self.target_x
                self.y = self.target_y
                self.hit_done = True
                self.alive = False
        else:
            self.x += self.speed
        if self.x > SCREEN_WIDTH + 20:
            self.alive = False

    def set_spike_target(self, tx, ty, arc_h=80):
        """Set spike to travel in arc from current pos to (tx, ty)."""
        self.target_x = tx
        self.target_y = ty
        self.arc_height = arc_h
        self.start_x = self.x
        self.start_y = self.y
        dx = tx - self.start_x
        self.speed = BULLET_SPEED * 2
        if dx != 0:
            self.speed = abs(dx) / 1.0  # complete in 1 second-ish

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
        elif self.electric:
            # Electric arc - bright yellow with glow
            import random
            pygame.draw.circle(surface, (255, 255, 100), (dx, dy), self.radius + 4, 2)
            pygame.draw.circle(surface, (255, 255, 200), (dx, dy), self.radius)
            pygame.draw.circle(surface, WHITE, (dx, dy), self.radius - 3)
            # Electric arcs emanating outward
            for i in range(4):
                angle = random.uniform(0, 6.28)
                lx = dx + int(math.cos(angle) * (self.radius + 5))
                ly = dy + int(math.sin(angle) * (self.radius + 5))
                pygame.draw.line(surface, (255, 255, 150), (dx, dy), (lx, ly), 1)
        elif self.spike:
            # Spike - sharp brown/gray projectile
            pygame.draw.circle(surface, (139, 90, 43), (dx, dy), self.radius)
            pygame.draw.circle(surface, (100, 60, 30), (dx, dy), self.radius, 1)
            # Sharp point indicator
            pygame.draw.polygon(surface, (180, 140, 100), [
                (dx, dy - self.radius - 3),
                (dx - 3, dy),
                (dx + 3, dy),
            ])
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


class ElectricArcEffect:
    """Lightning arc visual between zapricot and all zombies in 3x3 range."""
    def __init__(self, x, y, targets):
        self.x = x
        self.y = y
        self.targets = targets  # list of (tx, ty) tuples
        self.timer = 0
        self.duration = 0.3
        self.alive = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface, scroll_x=0, scroll_y=0):
        import random
        dx = int(self.x - scroll_x)
        dy = int(self.y - scroll_y)
        for (tx, ty) in self.targets:
            tx -= scroll_x
            ty -= scroll_y
            # Draw jagged lightning bolt
            steps = 5
            pts = [(dx, dy)]
            for i in range(1, steps):
                t = i / steps
                mid_x = dx + (tx - dx) * t + random.uniform(-15, 15)
                mid_y = dy + (ty - dy) * t + random.uniform(-15, 15)
                pts.append((int(mid_x), int(mid_y)))
            pts.append((int(tx), int(ty)))
            # Draw bolt segments with glow
            alpha = max(0, int(200 * (1 - self.timer / self.duration)))
            for i in range(len(pts) - 1):
                color = (255, 255, 100, alpha) if alpha > 0 else (255, 255, 100)
                pygame.draw.line(surface, (255, 255, 200), pts[i], pts[i + 1], 3)
                pygame.draw.line(surface, (255, 255, 100), pts[i], pts[i + 1], 1)

