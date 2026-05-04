import pygame
import random
import time as time_module
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.zombie import create_zombie
from source.component.bullet import Bullet, IceBlastEffect, SunParticle, ElectricArcEffect
from source.component.effects import (
    ZombieDeathEffect, IceShatterEffect, NewspaperShredEffect,
    CherryBombExplosion, SquashSmashEffect, PlantGrowEffect,
    WalkingZombieAnimator, SteamEffect, SunPopEffect,
    GloomShroomSporeExplosion
)
from source.state.achievements import AchievementManager, StatsManager
from source.component.menubar import Menubar
from source.component.sound_manager import SoundManager


# Simple AI plant selector - picks based on sun and random strategy
def ai_select_plant(sun):
    """Simple AI to select a plant based on available sun."""
    candidates = []
    if sun >= 50:
        candidates.extend(['sunflower', 'sunflower'])
    if sun >= 100:
        candidates.extend(['peashooter', 'peashooter'])
    if sun >= 200:
        candidates.append('repeater')
    if sun >= 175:
        candidates.append('snowpea')
    if sun >= 150:
        candidates.append('cherrybomb')
    if sun >= 75:
        candidates.append('iceshroom')
    if sun >= 50:
        candidates.append('wallnut')
    if sun >= 25:
        candidates.append('potatomine')
    if not candidates:
        return None
    return random.choice(candidates)


class SpectatorState:
    """Spectator mode - watch an AI-controlled endless game."""

    def __init__(self, screen):
        self.screen = screen
        self.grid = Grid()
        # Spectator has no menubar - no player interaction
        self.zombies = []
        self.bullets = []
        self.particles = []
        self.sun_particles = []
        self.sun_timer = 0
        self.sun_interval = 8.0
        self.wave_index = 0
        self.wave_active = False
        self.wave_zombies_remaining = []
        self.spawn_timer = 0
        self.game_over = False
        self.victory = False
        self.total_waves = 'infinite'
        self.zombies_killed = 0
        self.plants_placed = 0
        self.pre_wave_timer = 3.0
        self.mowers = [LawnMower(GRID_OFFSET_X - 30, GRID_OFFSET_Y + r * CELL_HEIGHT + CELL_HEIGHT // 2)
                       for r in range(GRID_ROWS)]
        self.sound = SoundManager.get_instance()
        self.achievements = AchievementManager.get_instance()
        self.start_time = time_module.time()
        self.preview_row = None
        self.preview_col = None
        self.ice_blast_effect = None
        # Poison DoT tracking
        self.poison_effects = {}

        # Spectator controls
        self.speed = 1.0
        self.watched_state = 'countdown'  # 'countdown', 'playing', 'gameover'
        self.countdown_timer = 3.0

        # AI control
        self.ai_sun = 150  # Start with some sun
        self.ai_plant_timer = 0
        self.ai_plant_interval = 3.0  # Try to plant every 3 seconds

        # Stats tracking
        self.current_wave = 0

    def get_stats(self):
        elapsed = time_module.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return {
            'wave_index': self.wave_index,
            'zombies_killed': self.zombies_killed,
            'plants_placed': self.plants_placed,
            'time_elapsed': f'{mins:02d}:{secs:02d}',
            'elapsed_seconds': elapsed,
            'mode': 'spectator',
        }

    def _build_events(self):
        """Build event list for plants to react to."""
        events = []
        for z in self.zombies:
            if not z.dead:
                events.append({
                    'type': 'zombie_near',
                    'row': z.row,
                    'col': int((z.x - self.grid.offset_x) / self.grid.cell_w),
                    'dead': z.dead,
                    'zombie': z,
                })
        return events

    def _spawn_zombie_death(self, zombie):
        """Spawn appropriate death effect for a zombie."""
        from source.component.effects import ZombieDeathEffect, IceShatterEffect
        if zombie.slow_timer > 0:
            self.particles.append(IceShatterEffect(zombie.x, zombie.y))
        else:
            self.particles.append(ZombieDeathEffect(zombie))

    def _ai_try_plant(self):
        """AI tries to place a plant on the grid."""
        if self.ai_sun < 50:
            return

        # Find empty cells, preferring front columns (right side is danger zone)
        empty_cells = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                if self.grid.cells[row][col] is None:
                    empty_cells.append((row, col))

        if not empty_cells:
            return

        # Sort by column - plant more on left (defensive)
        empty_cells.sort(key=lambda x: x[1])

        # Pick a plant based on available sun
        plant_name = ai_select_plant(self.ai_sun)
        if plant_name is None:
            return

        cost = PLANTS[plant_name]['cost']
        if self.ai_sun < cost:
            return

        # Pick a random cell from available ones
        row, col = random.choice(empty_cells[:max(1, len(empty_cells) // 2)])

        # Don't plant in first 2 columns (reserved for lawn mowers)
        if col < 2:
            return

        plant = create_plant(plant_name, row, col, self.grid)
        self.grid.place_plant(plant, row, col)
        self.ai_sun -= cost
        self.plants_placed += 1
        self.particles.append(PlantGrowEffect(plant.x, plant.y, plant.color))

    def start_wave(self, wave_idx):
        wave = self._build_wave_config(wave_idx)
        self.wave_zombies_remaining = []
        for ztype, count in wave['zombies']:
            for _ in range(count):
                self.wave_zombies_remaining.append(ztype)
        random.shuffle(self.wave_zombies_remaining)
        self.spawn_timer = 0
        self.wave_active = True
        self.current_wave = wave_idx

    def _build_wave_config(self, wave_idx):
        """Build wave configuration for endless spectator mode."""
        base_count = 5 + (wave_idx // 2) * 2
        zombies = []

        # Always include basic zombies
        basic_count = max(2, base_count // 3)
        zombies.append(('basic', basic_count))

        # Add cone after wave 1
        if wave_idx >= 1:
            cone_count = min(base_count // 3, 2 + wave_idx // 3)
            zombies.append(('cone', cone_count))

        # Add bucket after wave 3
        if wave_idx >= 3:
            bucket_count = min(base_count // 4, 1 + (wave_idx - 3) // 2)
            zombies.append(('bucket', bucket_count))

        # Add polevaulter after wave 2
        if wave_idx >= 2:
            pole_count = min(base_count // 5, 1 + wave_idx // 4)
            zombies.append(('pole', pole_count))

        # Add football after wave 5
        if wave_idx >= 5:
            fb_count = min(base_count // 6, 1 + (wave_idx - 5) // 3)
            zombies.append(('football', fb_count))

        spawn_delay = max(0.5, 2.5 - wave_idx * 0.05)

        return {'zombies': zombies, 'spawn_delay': spawn_delay}

    def update(self, dt):
        # Apply spectator speed
        effective_dt = dt * self.speed

        if self.watched_state == 'countdown':
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.watched_state = 'playing'
                self.start_wave(0)
            return

        if self.watched_state == 'gameover':
            return

        # AI sun accumulation (from sunflowers)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p and p.name == 'sunflower':
                    p.sun_timer += effective_dt
                    if p.sun_timer >= 7.0:
                        p.sun_timer = 0
                        x = p.rect.centerx + random.randint(-20, 20)
                        y = p.rect.centery - 20
                        self.sun_particles.append(SunParticle(x, y))

        # AI collect sun and try to plant
        self.ai_plant_timer += effective_dt
        if self.ai_plant_timer >= self.ai_plant_interval:
            self.ai_plant_timer = 0
            # Auto-collect nearby sun
            for sp in self.sun_particles[:]:
                if sp.y > GRID_OFFSET_Y:
                    self.ai_sun += 25
                    self.sun_particles.remove(sp)
            # Try to plant
            self._ai_try_plant()

        # Sun drop timer
        self.sun_timer += effective_dt
        if self.sun_timer >= self.sun_interval:
            self.sun_timer = 0
            x = random.randint(GRID_OFFSET_X, GRID_OFFSET_X + GRID_COLS * CELL_WIDTH)
            y = random.randint(GRID_OFFSET_Y, GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT)
            self.sun_particles.append(SunParticle(x, y))

        for sp in self.sun_particles[:]:
            sp.update(effective_dt)
            if sp.y > SCREEN_HEIGHT or not sp.alive:
                self.sun_particles.remove(sp)

        for mower in self.mowers:
            mower.update(effective_dt, self)

        for z in self.zombies[:]:
            if not z.dead:
                if z.x <= GRID_OFFSET_X - 10:
                    row = z.row
                    mower = self.mowers[row]
                    if not mower.activated and mower.alive:
                        mower.trigger()
                        self.sound.play('lawnmower')
                if z.x < GRID_OFFSET_X - 60:
                    self.game_over = True
                    self.watched_state = 'gameover'

            result = z.update(effective_dt)
            if z.dead and z.death_timer > 0.6:
                self.zombies.remove(z)

        events = self._build_events()

        for b in self.bullets[:]:
            b.update(effective_dt)

        # Ice + Fire bullet cancellation
        if len(self.bullets) >= 2:
            for i in range(len(self.bullets)):
                for j in range(i + 1, len(self.bullets)):
                    b1, b2 = self.bullets[i], self.bullets[j]
                    if b1.alive and b2.alive and b1.row == b2.row:
                        if (b1.ice and b2.fire) or (b1.fire and b2.ice):
                            mid_x = (b1.x + b2.x) / 2
                            self.particles.append(SteamEffect(mid_x, b1.y))
                            b1.alive = False
                            b2.alive = False

        for b in self.bullets[:]:
            # Torchwood conversion
            for p in self.grid.cells[b.row]:
                if p and p.name == 'torchwood':
                    torchwood_x = p.rect.centerx
                    if b.x >= torchwood_x - 5:
                        b.fire = True
                        b.ice = False
            # Bullet-zombie collision
            for z in self.zombies:
                if z.dead:
                    continue
                dist = abs(b.x - z.x)
                row_dist = abs(z.row - b.row)
                if dist < 30 and row_dist == 0:
                    if b.splash:
                        for z2 in self.zombies:
                            z2_dist = abs(b.x - z2.x)
                            z2_row = abs(z2.row - b.row)
                            if z2_dist < MELON_SPLASH_RADIUS and z2_row <= 1:
                                z2.killed, shred = z2.take_damage(b.damage)
                                if z2.dead:
                                    self.zombies_killed += 1
                                    self._spawn_zombie_death(z2)
                                if shred:
                                    self.particles.append(NewspaperShredEffect(z2.x, z2.y))
                        z.killed, shred = z.take_damage(b.damage)
                        if z.dead:
                            self.zombies_killed += 1
                            self._spawn_zombie_death(z)
                        if shred:
                            self.particles.append(NewspaperShredEffect(z.x, z.y))
                        if b.ice:
                            z.apply_slow()
                    else:
                        killed, shred = z.take_damage(b.damage)
                        if z.dead:
                            self.zombies_killed += 1
                            self._spawn_zombie_death(z)
                        elif b.fire:
                            self.sound.play('zombie_hit')
                        if shred:
                            self.particles.append(NewspaperShredEffect(z.x, z.y))
                        if b.ice:
                            z.apply_slow()
                    b.alive = False
                    break
            if not b.alive:
                self.bullets.remove(b)

        for e in self.particles[:]:
            e.update(effective_dt)
            if not e.alive:
                self.particles.remove(e)

        if self.ice_blast_effect:
            self.ice_blast_effect.update(effective_dt)
            if not self.ice_blast_effect.alive:
                self.ice_blast_effect = None

        # Update plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p is None:
                    continue

                action = p.update(effective_dt, events)

                if action == 'produce_sun':
                    x = p.rect.centerx + random.randint(-20, 20)
                    y = p.rect.centery - 20
                    self.sun_particles.append(SunParticle(x, y))
                    self.sound.play('sun_appear')

                elif action == 'shoot':
                    bx = p.rect.right
                    by = p.rect.centery
                    ice = (p.name in ('snowpea', 'wintermelon'))
                    splash = (p.name == 'wintermelon')
                    shots = 2 if p.name == 'repeater' else 1
                    for _ in range(shots):
                        self.bullets.append(Bullet(bx, by, row, self.grid, ice, splash))
                    self.sound.play('shoot')

                elif action == 'explode':
                    cx, cy = p.rect.centerx, p.rect.centery
                    self.particles.append(CherryBombExplosion(cx, cy, self.grid, p.row))
                    self.sound.play('explode')
                    for z in self.zombies[:]:
                        if abs(z.x - cx) < 120 and abs(z.y - cy) < 100:
                            _, shred = z.take_damage(999)
                            if z.dead:
                                self.zombies_killed += 1
                            if shred:
                                self.particles.append(NewspaperShredEffect(z.x, z.y))
                    self.grid.remove_plant(p.row, p.col)

                elif action == 'squash_damage':
                    cx = p.rect.centerx
                    cy = p.rect.centery
                    self.particles.append(SquashSmashEffect(cx, cy))
                    self.sound.play('explode')
                    for z in self.zombies[:]:
                        if z.row == p.row:
                            dist = abs(z.x - cx)
                            if dist < 80:
                                _, shred = z.take_damage(999)
                                if z.dead:
                                    self.zombies_killed += 1
                                if shred:
                                    self.particles.append(NewspaperShredEffect(z.x, z.y))
                    self.grid.remove_plant(p.row, p.col)

                elif action == 'ice_blast':
                    self.ice_blast_effect = IceBlastEffect()
                    self.sound.play('explode')
                    for z in self.zombies:
                        if not z.dead:
                            z.apply_slow()
                            z.apply_slow()
                    self.grid.remove_plant(p.row, p.col)

                elif action == 'electric_shot':
                    cx, cy = p.rect.centerx, p.rect.centery
                    center_col = p.col
                    center_row = p.row
                    targets = []
                    for z in self.zombies:
                        if z.dead:
                            continue
                        z_col = int((z.x - self.grid.offset_x) / self.grid.cell_w)
                        z_row = z.row
                        if abs(z_col - center_col) <= 1 and abs(z_row - center_row) <= 1:
                            targets.append(z)
                    if targets:
                        self.particles.append(ElectricArcEffect(cx, cy, [(z.x, z.y) for z in targets]))
                        for z in targets:
                            killed, shred = z.take_damage(p.attack)
                            if z.dead:
                                self.zombies_killed += 1
                                self._spawn_zombie_death(z)
                            if shred:
                                self.particles.append(NewspaperShredEffect(z.x, z.y))
                        self.sound.play('shoot')

                elif action == 'spore_explode':
                    cx, cy = p.rect.centerx, p.rect.centery
                    self.particles.append(GloomShroomSporeExplosion(cx, cy, self.grid, p.row))
                    self.sound.play('explode')
                    center_col = p.col
                    center_row = p.row
                    for z in self.zombies:
                        if z.dead:
                            continue
                        z_col = int((z.x - self.grid.offset_x) / self.grid.cell_w)
                        z_row = z.row
                        if abs(z_col - center_col) <= 1 and abs(z_row - center_row) <= 1:
                            self.poison_effects[z] = {
                                'timer': 0.0,
                                'damage': 10,
                                'tick_interval': 0.5,
                                'ticks_left': 4,
                            }
                            z.poisoned = True
                    self.grid.remove_plant(p.row, p.col)

        # Process poison DoT effects
        for z in list(self.poison_effects.keys()):
            if z.dead:
                del self.poison_effects[z]
                continue
            pe = self.poison_effects[z]
            pe['timer'] += effective_dt
            if pe['timer'] >= pe['tick_interval']:
                pe['timer'] = 0.0
                if pe['ticks_left'] > 0:
                    pe['ticks_left'] -= 1
                    killed, shred = z.take_damage(pe['damage'])
                    if z.dead:
                        self.zombies_killed += 1
                        self._spawn_zombie_death(z)
                    if shred:
                        self.particles.append(NewspaperShredEffect(z.x, z.y))
                    if pe['ticks_left'] <= 0:
                        del self.poison_effects[z]
                        z.poisoned = False

        # Chomper eating
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p and p.name == 'chomper':
                    for z in self.zombies:
                        if z.row == row and not p.eating:
                            ate = p.try_eat_zombie(z)
                            if ate:
                                self.sound.play('chomper')

        # Wave spawning
        if self.wave_active and self.wave_zombies_remaining:
            wave_cfg = self._build_wave_config(self.wave_index)
            self.spawn_timer += effective_dt
            if self.spawn_timer >= wave_cfg['spawn_delay']:
                self.spawn_timer = 0
                ztype = self.wave_zombies_remaining.pop(0)
                row = random.randint(0, GRID_ROWS - 1)
                z = create_zombie(ztype, SCREEN_WIDTH + 50, row, self.grid)
                self.zombies.append(z)
                self.sound.play('zombie_groan')

        # Check wave completion
        if self.wave_active and not self.wave_zombies_remaining and not self.zombies:
            self.wave_active = False
            self.wave_index += 1
            self.pre_wave_timer = 3.0
            self.start_wave(self.wave_index)

    def handle_click(self, mx, my):
        """Spectator mode doesn't handle clicks for game interaction."""
        pass

    def handle_key(self, key):
        """Handle speed control keys."""
        if key == pygame.K_1:
            self.speed = 1.0
        elif key == pygame.K_2:
            self.speed = 2.0
        elif key == pygame.K_3:
            self.speed = 3.0
        elif key == pygame.K_4:
            self.speed = 4.0

    def draw(self, surface):
        surface.fill((30, 80, 30))
        self.grid.draw(surface)

        for mower in self.mowers:
            mower.draw(surface)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p:
                    p.draw(surface)

        for z in self.zombies:
            z.draw(surface)

        for b in self.bullets:
            b.draw(surface)

        for e in self.particles:
            e.draw(surface)

        if self.ice_blast_effect:
            self.ice_blast_effect.draw(surface)

        for sp in self.sun_particles:
            sp.draw(surface)

        # Draw spectator UI overlay
        self._draw_spectator_ui(surface)

        # Draw countdown
        if self.watched_state == 'countdown':
            self._draw_countdown(surface)

    def _draw_spectator_ui(self, surface):
        """Draw spectator mode UI elements."""

        # Top bar background
        pygame.draw.rect(surface, (0, 0, 0, 180), (0, 0, SCREEN_WIDTH, 60))

        # Title
        font_large = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)

        title = font_large.render('SPECTATOR MODE', True, (255, 200, 100))
        surface.blit(title, (20, 15))

        # Speed indicator
        speed_colors = {1.0: (100, 255, 100), 2.0: (255, 255, 100), 3.0: (255, 200, 100), 4.0: (255, 100, 100)}
        speed_color = speed_colors.get(self.speed, (255, 255, 255))
        speed_text = font_small.render(f'Speed: {self.speed:.1f}x', True, speed_color)
        surface.blit(speed_text, (220, 20))

        # Wave info
        wave_text = font_small.render(f'Wave: {self.current_wave + 1}', True, (200, 200, 200))
        surface.blit(wave_text, (350, 20))

        # Kill count
        kills_text = font_small.render(f'Kills: {self.zombies_killed}', True, (200, 200, 200))
        surface.blit(kills_text, (470, 20))

        # Plants placed
        plants_text = font_small.render(f'Plants: {self.plants_placed}', True, (200, 200, 200))
        surface.blit(plants_text, (600, 20))

        # AI Sun
        sun_text = font_small.render(f'AI Sun: {self.ai_sun}', True, (255, 255, 100))
        surface.blit(sun_text, (700, 20))

        # Bottom hints
        hint_font = pygame.font.Font(None, 22)
        hints = [
            'Speed: 1-4 keys | Watch the AI defend the lawn!',
        ]
        for i, hint in enumerate(hints):
            h = hint_font.render(hint, True, (150, 150, 150))
            r = h.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25))
            surface.blit(h, r)

        # Game over overlay
        if self.watched_state == 'gameover':
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            font_big = pygame.font.Font(None, 72)
            game_over_text = font_big.render('SPECTATOR GAME OVER', True, (255, 50, 50))
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            surface.blit(game_over_text, game_over_rect)

            font_med = pygame.font.Font(None, 36)
            stats_text = font_med.render(f'Waves Survived: {self.current_wave} | Total Kills: {self.zombies_killed}', True, (255, 255, 255))
            stats_rect = stats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            surface.blit(stats_text, stats_rect)

            hint_text = font_med.render('Press ESC to return to menu', True, (200, 200, 200))
            hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            surface.blit(hint_text, hint_rect)

    def _draw_countdown(self, surface):
        """Draw countdown before spectator mode starts."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        font_big = pygame.font.Font(None, 72)
        countdown_num = int(self.countdown_timer) + 1
        if countdown_num <= 0:
            countdown_num = 3

        count_text = font_big.render(str(countdown_num), True, (255, 255, 255))
        count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(count_text, count_rect)

        font_med = pygame.font.Font(None, 36)
        info_text = font_med.render('Watch the AI defend the lawn!', True, (200, 200, 200))
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        surface.blit(info_text, info_rect)

        hint_text = font_med.render('Press 1-4 for speed control', True, (150, 150, 150))
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        surface.blit(hint_text, hint_rect)


class LawnMower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = MOWER_WIDTH
        self.h = MOWER_HEIGHT
        self.activated = False
        self.speed = 6
        self.alive = True

    def trigger(self):
        self.activated = True

    def update(self, dt, level):
        if not self.activated or not self.alive:
            return
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 50:
            self.alive = False
            return
        for z in level.zombies[:]:
            if z.row == self._get_row() and not z.dead:
                if abs(z.x - self.x) < 35:
                    _, shred = z.take_damage(999)
                    level.zombies_killed += 1
                    if shred:
                        level.particles.append(NewspaperShredEffect(z.x, z.y))

    def _get_row(self):
        return int((self.y - GRID_OFFSET_Y) // CELL_HEIGHT)

    def draw(self, surface):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        body_color = (0, 200, 0) if self.activated else LAWN_MOWER_COLOR
        pygame.draw.rect(surface, body_color, (cx - self.w // 2, cy - self.h // 2, self.w, self.h))
        pygame.draw.rect(surface, GRAY, (cx - self.w // 2, cy - self.h // 2, self.w, self.h), 2)
        wheel_r = 6
        pygame.draw.circle(surface, GRAY, (cx - 8, cy + self.h // 2 - 2), wheel_r)
        pygame.draw.circle(surface, GRAY, (cx + 8, cy + self.h // 2 - 2), wheel_r)
        pygame.draw.circle(surface, (200, 200, 100), (cx, cy - 3), 8, 2)
