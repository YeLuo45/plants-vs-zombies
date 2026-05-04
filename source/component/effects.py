import pygame
import random
import math


class Effect:
    def __init__(self):
        self.alive = True
        self.timer = 0

    def update(self, dt):
        self.timer += dt

    def draw(self, surface):
        pass


# ============================================================
# ZOMBIE DEATH EFFECTS
# ============================================================

class ZombieDeathEffect(Effect):
    """Rich zombie death with arm-flying + body-fade + optional ice shatter."""
    def __init__(self, zombie):
        super().__init__()
        self.x = zombie.x
        self.y = zombie.y
        self.row = zombie.row
        self.color = zombie.color
        self.w = zombie.w
        self.h = zombie.h
        self.duration = 0.8
        # Arm flying off pieces
        self.arms = []
        for _ in range(2):
            self.arms.append({
                'angle': random.uniform(-math.pi/2 - 0.5, -math.pi/2 + 0.5),
                'speed': random.uniform(80, 160),
                'rot': random.uniform(-3, 3),
                'x': self.x + random.choice([-1, 1]) * (self.w // 2 + 5),
                'y': self.y + random.randint(-10, 10),
                'size': random.randint(5, 10),
            })
        # Blood splatter particles
        self.drops = []
        for _ in range(6):
            self.drops.append({
                'x': self.x + random.uniform(-20, 20),
                'y': self.y + random.uniform(-20, 20),
                'vx': random.uniform(-60, 60),
                'vy': random.uniform(-100, -20),
                'size': random.randint(3, 7),
            })
        self.dead_timer = 0
        self.is_frozen = zombie.slow_timer > 0

    def update(self, dt):
        super().update(dt)
        self.dead_timer += dt
        for arm in self.arms:
            arm['x'] += math.cos(arm['angle']) * arm['speed'] * dt
            arm['y'] += math.sin(arm['angle']) * arm['speed'] * dt
            arm['angle'] += arm['rot'] * dt
        for d in self.drops:
            d['x'] += d['vx'] * dt
            d['y'] += d['vy'] * dt
            d['vy'] += 200 * dt  # gravity

    def draw(self, surface):
        frac = self.dead_timer / self.duration
        alpha = max(0, int(255 * (1 - frac * 1.2)))

        # Ice shatter: draw ice shards
        if self.is_frozen and frac < 0.5:
            ice_alpha = max(0, int(200 * (1 - frac * 2)))
            for i in range(8):
                angle = i * (2 * math.pi / 8) + frac * 3
                dist = 20 + frac * 60
                sx = self.x + int(math.cos(angle) * dist)
                sy = self.y + int(math.sin(angle) * dist)
                size = max(2, int(8 * (1 - frac)))
                pygame.draw.line(surface, (150, 200, 255, ice_alpha),
                               (sx, sy), (sx + int(math.cos(angle) * (size + 4)),
                                sy + int(math.sin(angle) * (size + 4))), 2)

        # Body fade
        if alpha > 0:
            body_surf = pygame.Surface((self.w + 20, self.h + 20), pygame.SRCALPHA)
            pygame.draw.rect(body_surf, (*self.color, alpha), (10, 10, self.w, self.h))
            pygame.draw.circle(body_surf, (180, 180, 180, alpha),
                             (self.w // 2 + 10, 10), 12)
            surface.blit(body_surf, (int(self.x) - self.w // 2 - 10, int(self.y) - self.h // 2 - 10))

        # Arm pieces flying
        arm_alpha = max(0, int(200 * (1 - frac)))
        for arm in self.arms:
            if arm_alpha > 0:
                pygame.draw.rect(surface, (*self.color, arm_alpha),
                              (int(arm['x']), int(arm['y']), arm['size'], arm['size'] // 2))

        # Blood drops
        for d in self.drops:
            drop_alpha = max(0, int(180 * (1 - frac)))
            if drop_alpha > 0:
                pygame.draw.circle(surface, (180, 30, 30, drop_alpha),
                                (int(d['x']), int(d['y'])), max(1, int(d['size'] * (1 - frac))))

        if self.dead_timer >= self.duration:
            self.alive = False


class NewspaperShredEffect(Effect):
    """Newspaper fragments flying when newspaper zombie loses its paper."""
    def __init__(self, x, y):
        super().__init__()
        self.duration = 1.2
        self.fragments = []
        for _ in range(8):
            self.fragments.append({
                'x': x + random.uniform(-15, 15),
                'y': y + random.uniform(-15, 15),
                'vx': random.uniform(-80, 80),
                'vy': random.uniform(-120, -40),
                'rot': 0,
                'rot_speed': random.uniform(-5, 5),
                'w': random.randint(8, 14),
                'h': random.randint(6, 10),
            })

    def update(self, dt):
        super().update(dt)
        for f in self.fragments:
            f['x'] += f['vx'] * dt
            f['y'] += f['vy'] * dt
            f['vy'] += 150 * dt
            f['rot'] += f['rot_speed'] * dt

    def draw(self, surface):
        frac = self.timer / self.duration
        alpha = max(0, int(230 * (1 - frac)))
        if alpha <= 0:
            self.alive = False
            return
        for f in self.fragments:
            # Draw rotated rectangle (newspaper fragment)
            surf = pygame.Surface((f['w'] + 4, f['h'] + 4), pygame.SRCALPHA)
            pygame.draw.rect(surf, (230, 220, 200, alpha), (2, 2, f['w'], f['h']))
            orig = (f['w'] // 2 + 2, f['h'] // 2 + 2)
            rotated = pygame.transform.rotate(surf, math.degrees(f['rot']))
            rw, rh = rotated.get_size()
            surface.blit(rotated, (int(f['x'] - rw // 2), int(f['y'] - rh // 2)))


class IceShatterEffect(Effect):
    """Ice crystal shatter when frozen zombie dies."""
    def __init__(self, x, y):
        super().__init__()
        self.duration = 0.6
        self.x = x
        self.y = y
        self.shards = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(60, 180)
            self.shards.append({
                'angle': angle,
                'speed': speed,
                'x': x,
                'y': y,
                'size': random.randint(4, 10),
                'rot': random.uniform(0, math.pi * 2),
                'rot_speed': random.uniform(-6, 6),
            })

    def update(self, dt):
        super().update(dt)
        frac = self.timer / self.duration
        for s in self.shards:
            s['x'] += math.cos(s['angle']) * s['speed'] * dt
            s['y'] += math.sin(s['angle']) * s['speed'] * dt
            s['speed'] *= 0.95  # drag
            s['rot'] += s['rot_speed'] * dt

    def draw(self, surface):
        frac = self.timer / self.duration
        alpha = max(0, int(220 * (1 - frac)))
        if alpha <= 0:
            self.alive = False
            return
        for s in self.shards:
            sz = max(1, int(s['size'] * (1 - frac * 0.5)))
            # Ice shard: elongated diamond
            pts = [
                (int(s['x']), int(s['y'] - sz)),
                (int(s['x'] + sz * 0.5), int(s['y'])),
                (int(s['x']), int(s['y'] + sz)),
                (int(s['x'] - sz * 0.5), int(s['y'])),
            ]
            pygame.draw.polygon(surface, (150, 200, 255, alpha), pts)


# ============================================================
# PLANT EFFECTS
# ============================================================

class PlantGrowEffect(Effect):
    """Sprout → full-size animation when plant is placed."""
    def __init__(self, plant_x, plant_y, plant_color):
        super().__init__()
        self.x = plant_x
        self.y = plant_y
        self.color = plant_color
        self.duration = 0.5

    def update(self, dt):
        super().update(dt)
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        frac = self.timer / self.duration
        # Scale from 0 to 1 with overshoot bounce
        if frac < 0.6:
            scale = frac / 0.6 * 1.2  # grow past 1
        else:
            t = (frac - 0.6) / 0.4
            scale = 1.2 - 0.2 * t  # settle back to 1
        scale = max(0.05, min(scale, 1.2))

        alpha = int(255 * min(1, frac * 2))
        r = int(22 * scale)

        surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (30, 30), r)
        # Small stem
        if scale > 0.5:
            stem_h = int(15 * scale)
            pygame.draw.rect(surf, (50, 120, 50, alpha), (28, 30 + r // 2, 4, stem_h))
        surface.blit(surf, (int(self.x) - 30, int(self.y) - 30))


class CherryBombExplosion(Effect):
    """Cherry bomb smoke + sparks explosion."""
    def __init__(self, x, y, grid, row):
        super().__init__()
        self.x = x
        self.y = y
        self.duration = 1.2
        # Smoke puffs
        self.puffs = []
        for _ in range(10):
            self.puffs.append({
                'x': x + random.uniform(-20, 20),
                'y': y + random.uniform(-20, 10),
                'vx': random.uniform(-30, 30),
                'vy': random.uniform(-80, -30),
                'size': random.randint(15, 30),
                'alpha': 200,
            })
        # Sparks
        self.sparks = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 250)
            self.sparks.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 50,
                'size': random.randint(3, 6),
            })
        self.damage_radius = 3  # grid cells

    def update(self, dt):
        super().update(dt)
        frac = self.timer / self.duration
        for p in self.puffs:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] -= 20 * dt
            p['alpha'] = max(0, int(200 * (1 - frac)))
            p['size'] += 15 * dt
        for s in self.sparks:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
            s['vy'] += 200 * dt

    def draw(self, surface):
        frac = self.timer / self.duration
        if frac > 0.7:
            self.alive = False
            return

        # Smoke puffs
        for p in self.puffs:
            if p['alpha'] > 0:
                dark = int(80 * (1 - frac))
                pygame.draw.circle(surface, (dark, dark, dark, p['alpha']),
                                 (int(p['x']), int(p['y'])), max(5, int(p['size'])))

        # Sparks
        spark_alpha = max(0, int(255 * (1 - frac * 1.5)))
        for s in self.sparks:
            if spark_alpha > 0:
                pygame.draw.circle(surface, (255, 200, 50, spark_alpha),
                                 (int(s['x']), int(s['y'])), max(1, int(s['size'] * (1 - frac))))

        # Red glow ring
        if frac < 0.3:
            glow_alpha = int(150 * (1 - frac / 0.3))
            glow_r = int(60 + frac * 40)
            pygame.draw.circle(surface, (255, 50, 50, glow_alpha),
                             (int(self.x), int(self.y)), glow_r, 3)


class SquashSmashEffect(Effect):
    """Squash lands with a ground-pound dust cloud."""
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.duration = 0.5
        self.dust = []
        for _ in range(8):
            angle = random.uniform(-math.pi, 0)  # upward fan
            speed = random.uniform(40, 100)
            self.dust.append({
                'x': x + random.uniform(-15, 15),
                'y': y + 10,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.randint(6, 14),
            })

    def update(self, dt):
        super().update(dt)
        frac = self.timer / self.duration
        for d in self.dust:
            d['x'] += d['vx'] * dt
            d['y'] += d['vy'] * dt
            d['vy'] += 80 * dt  # gravity
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        frac = self.timer / self.duration
        alpha = max(0, int(180 * (1 - frac)))
        if alpha <= 0:
            return
        for d in self.dust:
            sz = max(3, int(d['size'] * (1 - frac * 0.5)))
            pygame.draw.circle(surface, (150, 130, 100, alpha),
                             (int(d['x']), int(d['y'])), sz)


# ============================================================
# ZOMBIE WALKING ANIMATION HELPERS
# ============================================================

class WalkingZombieAnimator:
    """Pure draw helper - arm swing + body bob for walking zombies."""

    @staticmethod
    def draw(surface, zombie, x, y):
        """Draw zombie with walking animation (arm swing + body bob)."""
        bob = int(2 * (zombie.anim_frame * 2 - 1))  # subtle up/down

        if zombie.eating:
            # Eating animation (already handled in zombie.draw)
            return

        body_y = y + bob

        # Body rectangle
        body_rect = pygame.Rect(x - zombie.w // 2, body_y - zombie.h // 2, zombie.w, zombie.h)
        pygame.draw.rect(surface, zombie.color, body_rect)

        # Walking arm swing
        arm_swing = 8 if zombie.anim_frame == 0 else -8
        # Left arm
        pygame.draw.rect(surface, zombie.color,
                        (x - zombie.w // 2 - 8, body_y - 5 + arm_swing, 8, 20))
        # Right arm (opposite phase)
        pygame.draw.rect(surface, zombie.color,
                        (x + zombie.w // 2, body_y - 5 - arm_swing, 8, 20))

        # Head
        head_y = body_y - zombie.h // 2 - 10 + (bob // 2)
        pygame.draw.circle(surface, (180, 180, 180), (x, head_y), 12)

        # Ice slow glow
        if zombie.slow_timer > 0:
            pygame.draw.circle(surface, (150, 200, 255, 100), (x, body_y), zombie.w // 2 + 5, 2)


class PlantAnimator:
    """Draw helpers for plant animations."""

    @staticmethod
    def draw_sunflower(surface, x, y, anim_frame, sun_timer, sun_interval):
        """Sunflower with pulsing center and swaying."""
        sway = int(2 * (anim_frame * 2 - 1))
        # Petals
        for i in range(8):
            angle = i * (2 * math.pi / 8) + sway * 0.1
            px = x + int(math.cos(angle) * 14)
            py = y + int(math.sin(angle) * 14)
            pygame.draw.circle(surface, YELLOW, (px, py), 7)
        # Center
        pulse = 1.0 + 0.1 * math.sin(sun_timer / sun_interval * 2 * math.pi)
        r = int(10 * pulse)
        pygame.draw.circle(surface, (200, 150, 0), (x, y), r)

    @staticmethod
    def draw_wallnut(surface, x, y, anim_frame, hp, max_hp):
        """Wallnut with cracks when damaged."""
        pygame.draw.circle(surface, (139, 90, 43), (x, y), 22)
        # Eyes
        pygame.draw.circle(surface, BLACK, (x - 7, y - 4), 3)
        pygame.draw.circle(surface, BLACK, (x + 7, y - 4), 3)
        # Mouth
        pygame.draw.arc(surface, BLACK, (x - 9, y + 2, 18, 8), 0, 3.14, 2)
        # Cracks based on damage
        dmg_frac = 1 - hp / max_hp
        if dmg_frac > 0.3:
            crack_alpha = int(150 * (dmg_frac - 0.3) / 0.7)
            pygame.draw.line(surface, (80, 50, 20), (x - 10, y - 15), (x + 5, y + 5), 2)
        if dmg_frac > 0.6:
            pygame.draw.line(surface, (80, 50, 20), (x + 8, y - 18), (x - 3, y + 3), 2)

    @staticmethod
    def draw_tallnut(surface, x, y, anim_frame, hp, max_hp):
        """Tallnut with segment lines."""
        pygame.draw.ellipse(surface, (107, 142, 35), (x - 16, y - 28, 32, 56))
        # Segment lines
        for i in range(1, 4):
            py = y - 28 + i * 14
            pygame.draw.line(surface, (80, 110, 20), (x - 14, py), (x + 14, py), 1)
        # Eyes
        pygame.draw.circle(surface, BLACK, (x - 5, y - 8), 3)
        pygame.draw.circle(surface, BLACK, (x + 5, y - 8), 3)


# ============================================================
# SUNFLOWER / SUN PRODUCING ANIMATION
# ============================================================

class SunPopEffect(Effect):
    """Sun pops out of sunflower with a little bounce."""
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.start_y = y
        self.duration = 0.4
        self.bounce_y = y - 30

    def update(self, dt):
        super().update(dt)
        frac = self.timer / self.duration
        if frac < 0.4:
            # Rise up with overshoot
            t = frac / 0.4
            self.y = self.start_y + (self.bounce_y - self.start_y) * (t * (2 - t))
        else:
            # Settle back
            t = (frac - 0.4) / 0.6
            self.y = self.bounce_y + (self.start_y - self.bounce_y) * t
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        pass  # Sun is the actual particle; this is just positional


class SteamEffect(Effect):
    """Steam cloud when ice + fire bullets cancel each other out."""
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.duration = 0.8
        self.puffs = []
        for _ in range(6):
            self.puffs.append({
                'x': x + random.uniform(-12, 12),
                'y': y + random.uniform(-8, 8),
                'vx': random.uniform(-20, 20),
                'vy': random.uniform(-60, -30),
                'size': random.randint(8, 16),
            })

    def update(self, dt):
        super().update(dt)
        frac = self.timer / self.duration
        for p in self.puffs:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] -= 30 * dt  # steam rises faster
            p['size'] += 20 * dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        frac = self.timer / self.duration
        alpha = max(0, int(200 * (1 - frac)))
        if alpha <= 0:
            return
        for p in self.puffs:
            pygame.draw.circle(surface, (220, 220, 255, alpha),
                             (int(p['x']), int(p['y'])), max(4, int(p['size'])))
