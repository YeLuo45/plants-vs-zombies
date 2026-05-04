import pygame
import random
import time as time_module
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.zombie import create_zombie
from source.component.bullet import Bullet, ExplosionEffect, IceBlastEffect, SunParticle
from source.component.effects import CherryBombExplosion, NewspaperShredEffect, SquashSmashEffect
from source.state.achievements import AchievementManager, StatsManager
from source.component.menubar import Menubar
from source.component.sound_manager import SoundManager
from source.state.leaderboard import LeaderboardManager


# All zombie type names for endless spawning
ALL_ZOMBIE_TYPES = list(ZOMBIES.keys())


class EndlessState:
    def __init__(self, screen):
        self.screen = screen
        self.grid = Grid()
        self.menubar = Menubar()
        self.zombies = []
        self.bullets = []
        self.particles = []
        self.sun_particles = []
        self.sun_timer = 0
        self.sun_interval = 10.0
        self.wave_index = 0
        self.wave_active = False
        self.wave_zombies_remaining = []
        self.spawn_timer = 0
        self.game_over = False
        self.victory = False  # never triggers in endless
        self.total_waves = 'infinite'
        self.zombies_killed = 0
        self.plants_placed = 0
        self.pre_wave_timer = 3.0
        self.mowers = [LawnMower(GRID_OFFSET_X - 30, GRID_OFFSET_Y + r * CELL_HEIGHT + CELL_HEIGHT // 2)
                       for r in range(GRID_ROWS)]
        self.sound = SoundManager.get_instance()
        self.achievements = AchievementManager.get_instance()
        self.leaderboard = LeaderboardManager.get_instance()
        self.start_time = time_module.time()
        self.score_saved = False
        self.preview_row = None
        self.preview_col = None
        self.ice_blast_effect = None
        self.zombie_hp_multiplier = 1.0
        self._survival_5_reported = False
        self.start_time = time_module.time()

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
        }

    def _current_spawn_delay(self):
        return max(0.3, 3.0 - self.wave_index * 0.05)

    def _current_zombie_count(self):
        return 5 + (self.wave_index // 3) * 2

    def _current_sun_interval(self):
        return max(4, 10 - self.wave_index * 0.1)

    def _current_sun_value(self):
        return 25 + (self.wave_index // 5) * 10

    def _build_zombie_pool(self):
        """Build a shuffled pool of zombie types for this wave."""
        count = self._current_zombie_count()
        pool = []
        # Base always includes basic
        basic_count = max(1, count // 2)
        pool.extend(['basic'] * basic_count)

        remaining = count - basic_count
        # Cone appears after wave 1
        if self.wave_index >= 1:
            cone_count = min(remaining, 2 + self.wave_index // 4)
            pool.extend(['cone'] * cone_count)
            remaining -= cone_count
        # Bucket appears after wave 4
        if self.wave_index >= 4:
            bucket_count = min(remaining, 1 + (self.wave_index - 4) // 3)
            pool.extend(['bucket'] * bucket_count)
            remaining -= bucket_count
        # Polevaulter appears after wave 3
        if self.wave_index >= 3:
            pole_count = min(remaining, 1 + (self.wave_index - 3) // 4)
            pool.extend(['pole'] * pole_count)
            remaining -= pole_count
        # Football appears after wave 6
        if self.wave_index >= 6:
            fb_count = min(remaining, 1 + (self.wave_index - 6) // 5)
            pool.extend(['football'] * fb_count)
            remaining -= fb_count
        # Newspaper appears after wave 5
        if self.wave_index >= 5:
            news_count = min(remaining, 1 + (self.wave_index - 5) // 5)
            pool.extend(['newspaper'] * news_count)
            remaining -= news_count
        # Miner appears after wave 7
        if self.wave_index >= 7:
            miner_count = min(remaining, 1 + (self.wave_index - 7) // 6)
            pool.extend(['miner'] * miner_count)
            remaining -= miner_count
        # Ladder appears after wave 8
        if self.wave_index >= 8:
            ladder_count = min(remaining, 1 + (self.wave_index - 8) // 6)
            pool.extend(['ladder'] * ladder_count)
            remaining -= ladder_count

        # Fill remaining with basic if needed
        while remaining > 0:
            pool.append('basic')
            remaining -= 1

        random.shuffle(pool)
        return pool

    def get_stats(self):
        elapsed = time_module.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        return {
            'waves_completed': self.wave_index,
            'total_waves': self.total_waves,
            'zombies_killed': self.zombies_killed,
            'plants_placed': self.plants_placed,
            'time_elapsed': f'{mins:02d}:{secs:02d}',
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

    def start_wave(self, wave_idx):
        self.wave_index = wave_idx
        # Every 5 waves: zombie HP multiplier += 0.2
        self.zombie_hp_multiplier = 1.0 + (wave_idx // 5) * 0.2
        self.wave_zombies_remaining = self._build_zombie_pool()
        self.spawn_timer = 0
        self.wave_active = True

    def update(self, dt):
        self.menubar.update(dt)

        # Check survival_5 achievement
        if self.wave_index >= 5 and not self._survival_5_reported:
            self.achievements.on_endless_wave(self.wave_index)
            self._survival_5_reported = True

        if not self.wave_active and self.pre_wave_timer > 0:
            self.pre_wave_timer -= dt
            if self.pre_wave_timer <= 0:
                self.start_wave(self.wave_index)
            return

        if self.wave_active and self.wave_zombies_remaining:
            self.spawn_timer += dt
            if self.spawn_timer >= self._current_spawn_delay():
                self.spawn_timer = 0
                ztype = self.wave_zombies_remaining.pop(0)
                row = random.randint(0, GRID_ROWS - 1)
                z = create_zombie(ztype, SCREEN_WIDTH + 50, row, self.grid)
                # Apply HP multiplier from endless scaling
                z.hp = int(z.hp * self.zombie_hp_multiplier)
                z.max_hp = int(z.max_hp * self.zombie_hp_multiplier)
                self.zombies.append(z)

        # Sun spawning
        self.sun_timer += dt
        if self.sun_timer >= self._current_sun_interval():
            self.sun_timer = 0
            x = random.randint(GRID_OFFSET_X, GRID_OFFSET_X + GRID_COLS * CELL_WIDTH)
            y = random.randint(GRID_OFFSET_Y, GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT)
            self.sun_particles.append(SunParticle(x, y))
            self.sound.play('sun_appear')

        for sp in self.sun_particles[:]:
            sp.update(dt)
            if sp.y > SCREEN_HEIGHT or not sp.alive:
                self.sun_particles.remove(sp)

        for mower in self.mowers:
            mower.update(dt, self)

        for z in self.zombies[:]:
            if not z.dead:
                if z.x <= GRID_OFFSET_X - 10:
                    row = z.row
                    mower = self.mowers[row]
                    if not mower.activated and mower.alive:
                        mower.trigger()
                        self.sound.play('lawnmower')
                if z.x < GRID_OFFSET_X - 60:
                    if not self.score_saved:
                        stats = self.get_stats()
                        self.leaderboard.add_score(
                            stats['wave_index'], stats['zombies_killed'],
                            stats['plants_placed'], stats['elapsed_seconds'])
                        self.score_saved = True
                    self.game_over = True

            result = z.update(dt)
            if z.dead and z.death_timer > 0.6:
                self.zombies.remove(z)

        events = self._build_events()

        for b in self.bullets[:]:
            b.update(dt)
            if not b.alive:
                self.bullets.remove(b)

        for e in self.particles[:]:
            e.update(dt)
            if not e.alive:
                self.particles.remove(e)

        if self.ice_blast_effect:
            self.ice_blast_effect.update(dt)
            if not self.ice_blast_effect.alive:
                self.ice_blast_effect = None

        # Update plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p is None:
                    continue

                action = p.update(dt, events)

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
                    is_potatomine = (p.name == 'potatomine')
                    radius = 80 if is_potatomine else 120
                    self.particles.append(CherryBombExplosion(cx, cy, self.grid, p.row))
                    self.sound.play('explode')
                    for z in self.zombies[:]:
                        if abs(z.x - cx) < radius and abs(z.y - cy) < radius * 0.8:
                            _, shred = z.take_damage(999)
                            if z.dead:
                                self.zombies_killed += 1
                                self.achievements.on_zombie_killed()
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
                                    self.achievements.on_zombie_killed(killed_by='squash')
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

        # Wave completion: endless never wins, just starts next wave
        if self.wave_active and not self.wave_zombies_remaining and not self.zombies:
            self.wave_active = False
            self.wave_index += 1
            # Every 5 waves: zombie HP multiplier += 0.2 (done in start_wave)
            # Recalculate sun values for next wave
            self.sun_interval = self._current_sun_interval()
            self.pre_wave_timer = 3.0
            # Victory is NEVER triggered in endless mode

    def handle_click(self, mx, my):
        # Check shovel
        if self.menubar.is_shovel_at(mx, my):
            self.menubar.shovel_selected = not self.menubar.shovel_selected
            self.menubar.selected = None
            return

        if self.menubar.shovel_selected:
            row, col = self.grid.get_cell_from_mouse(mx, my)
            if row is not None and col is not None:
                if self.grid.cells[row][col]:
                    self.grid.remove_plant(row, col)
                    self.menubar.shovel_selected = False
            return

        # Card click
        card = self.menubar.get_card_at(mx, my)
        if card:
            if self.menubar.can_afford(card) and self.menubar.is_ready(card):
                self.menubar.selected = card
                self.menubar.shovel_selected = False
            else:
                self.menubar.selected = None
            return

        # Sun collection
        sun_value = self._current_sun_value()
        for sp in self.sun_particles[:]:
            dx = mx - sp.x
            dy = my - sp.y
            if dx * dx + dy * dy < 400:
                self.menubar.add_sun(sun_value)
                self.sun_particles.remove(sp)
                self.sound.play('sun_collect')
                return

        # Plant placement
        if self.menubar.selected:
            row, col = self.grid.get_cell_from_mouse(mx, my)
            if self.grid.can_plant(row, col):
                plant = create_plant(self.menubar.selected, row, col, self.grid)
                self.grid.place_plant(plant, row, col)
                self.menubar.spend(self.menubar.selected)
                self.plants_placed += 1
                StatsManager.get_instance().on_plant_placed()
                self.sound.play('plant')

    def handle_mouse_move(self, mx, my):
        if self.menubar.selected:
            row, col = self.grid.get_cell_from_mouse(mx, my)
            self.preview_row = row
            self.preview_col = col
        else:
            self.preview_row = None
            self.preview_col = None

    def draw(self, surface):
        surface.fill((30, 80, 30))
        self.grid.draw(surface)

        # Plant preview
        if self.menubar.selected and self.preview_row is not None:
            row, col = self.preview_row, self.preview_col
            if self.grid.can_plant(row, col):
                rect = self.grid.get_cell_rect(row, col)
                ghost_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                cfg = PLANTS[self.menubar.selected]
                color = cfg['color']
                pygame.draw.rect(ghost_surf, (*color, 100), ghost_surf.get_rect())
                pygame.draw.circle(ghost_surf, (*color, 150), (rect.width // 2, rect.height // 2), 20)
                pygame.draw.rect(ghost_surf, (*color, 80), ghost_surf.get_rect(), 2)
                surface.blit(ghost_surf, rect.topleft)
            elif row is not None:
                rect = self.grid.get_cell_rect(row, col)
                ghost_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(ghost_surf, (255, 0, 0, 60), ghost_surf.get_rect())
                pygame.draw.rect(ghost_surf, (255, 0, 0, 120), ghost_surf.get_rect(), 2)
                surface.blit(ghost_surf, rect.topleft)

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
        self.menubar.draw(surface)

        font = pygame.font.Font(None, 28)
        wave_text = font.render(f'Wave: {self.wave_index + 1} (INFINITE)', True, WHITE)
        surface.blit(wave_text, (SCREEN_WIDTH - 170, 30))
        kill_text = font.render(f'Kills: {self.zombies_killed}', True, WHITE)
        surface.blit(kill_text, (SCREEN_WIDTH - 150, 55))

        if not self.wave_active and not self.victory and not self.game_over and self.pre_wave_timer > 0:
            count_font = pygame.font.Font(None, 72)
            count_text = count_font.render(str(int(self.pre_wave_timer) + 1), True, (255, 100, 100))
            count_rect = count_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(count_text, count_rect)


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
