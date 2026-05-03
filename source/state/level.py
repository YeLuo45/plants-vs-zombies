import pygame
import random
import time as time_module
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.zombie import create_zombie
from source.component.bullet import Bullet, ExplosionEffect, SunParticle
from source.component.menubar import Menubar
from source.component.sound_manager import SoundManager


class LevelState:
    def __init__(self, screen):
        self.screen = screen
        self.grid = Grid()
        self.menubar = Menubar()
        self.zombies = []
        self.bullets = []
        self.particles = []
        self.sun_particles = []
        self.sun_timer = 0
        self.sun_interval = SUN_DROP_INTERVAL
        self.wave_index = 0
        self.wave_active = False
        self.wave_zombies_remaining = []
        self.spawn_timer = 0
        self.game_over = False
        self.victory = False
        self.total_waves = len(WAVES)
        self.zombies_killed = 0
        self.plants_placed = 0
        self.pre_wave_timer = 5.0
        self.mowers = [LawnMower(GRID_OFFSET_X - 30, GRID_OFFSET_Y + r * CELL_HEIGHT + CELL_HEIGHT // 2)
                       for r in range(GRID_ROWS)]
        self.sound = SoundManager.get_instance()
        self.start_time = time_module.time()
        # Preview plant (ghost) at mouse position
        self.preview_row = None
        self.preview_col = None

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

    def start_wave(self, wave_idx):
        wave = WAVES[wave_idx]
        self.wave_zombies_remaining = []
        for ztype, count in wave['zombies']:
            for _ in range(count):
                self.wave_zombies_remaining.append(ztype)
        random.shuffle(self.wave_zombies_remaining)
        self.spawn_timer = 0
        self.wave_active = True

    def update(self, dt):
        self.menubar.update(dt)

        if not self.wave_active and self.pre_wave_timer > 0:
            self.pre_wave_timer -= dt
            if self.pre_wave_timer <= 0:
                self.start_wave(self.wave_index)
            return

        if self.wave_active and self.wave_zombies_remaining:
            self.spawn_timer += dt
            wave_cfg = WAVES[self.wave_index]
            if self.spawn_timer >= wave_cfg['spawn_delay']:
                self.spawn_timer = 0
                ztype = self.wave_zombies_remaining.pop(0)
                row = random.randint(0, GRID_ROWS - 1)
                z = create_zombie(ztype, SCREEN_WIDTH + 50, row, self.grid)
                self.zombies.append(z)

        self.sun_timer += dt
        if self.sun_timer >= self.sun_interval:
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
                    self.game_over = True

            result = z.update(dt)
            if z.dead and z.death_timer > 0.6:
                self.zombies.remove(z)

        for b in self.bullets[:]:
            prev_alive = b.alive
            b.update(dt)
            if prev_alive and not b.alive:
                # bullet hit something and died
                pass
            if not b.alive:
                self.bullets.remove(b)

        for e in self.particles[:]:
            e.update(dt)
            if not e.alive:
                self.particles.remove(e)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p:
                    action = p.update(dt, [])
                    if action == 'produce_sun':
                        x = p.rect.centerx + random.randint(-20, 20)
                        y = p.rect.centery - 20
                        self.sun_particles.append(SunParticle(x, y))
                        self.sound.play('sun_appear')
                    elif action == 'shoot':
                        bx = p.rect.right
                        by = p.rect.centery
                        ice = (p.name == 'snowpea')
                        shots = 2 if p.name == 'repeater' else 1
                        for _ in range(shots):
                            self.bullets.append(Bullet(bx, by, row, self.grid, ice))
                            self.sound.play('shoot')
                    elif action == 'explode':
                        cx, cy = p.rect.centerx, p.rect.centery
                        self.particles.append(ExplosionEffect(cx, cy))
                        self.sound.play('explode')
                        for z in self.zombies[:]:
                            if abs(z.x - cx) < 120 and abs(z.y - cy) < 100:
                                z.take_damage(999)
                                if z.dead:
                                    self.zombies_killed += 1
                        self.grid.remove_plant(p.row, p.col)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p and p.name == 'chomper':
                    for z in self.zombies:
                        if z.row == row and not p.eating:
                            ate = p.try_eat_zombie(z)
                            if ate:
                                self.sound.play('chomper')

        if self.wave_active and not self.wave_zombies_remaining and not self.zombies:
            self.wave_active = False
            self.wave_index += 1
            if self.wave_index >= self.total_waves:
                self.victory = True
            else:
                self.pre_wave_timer = 5.0

    def handle_click(self, mx, my):
        # Check shovel click first
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

        card = self.menubar.get_card_at(mx, my)
        if card:
            if self.menubar.can_afford(card) and self.menubar.is_ready(card):
                self.menubar.selected = card
                self.menubar.shovel_selected = False
            else:
                self.menubar.selected = None
            return

        # Sun collection
        for sp in self.sun_particles[:]:
            dx = mx - sp.x
            dy = my - sp.y
            if dx * dx + dy * dy < 400:
                self.menubar.add_sun(25)
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
                self.sound.play('plant')

    def handle_mouse_move(self, mx, my):
        """Update plant placement preview."""
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

        # Plant placement preview (ghost)
        if self.menubar.selected and self.preview_row is not None:
            row, col = self.preview_row, self.preview_col
            if self.grid.can_plant(row, col):
                rect = self.grid.get_cell_rect(row, col)
                ghost_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                cfg = PLANTS[self.menubar.selected]
                color = cfg['color']
                ghost_color = (*color, 100)  # semi-transparent
                pygame.draw.rect(ghost_surf, ghost_color, ghost_surf.get_rect())
                pygame.draw.circle(ghost_surf, (*color, 150), (rect.width // 2, rect.height // 2), 20)
                pygame.draw.rect(ghost_surf, (*color, 80), ghost_surf.get_rect(), 2)
                surface.blit(ghost_surf, rect.topleft)
            elif row is not None:
                # Invalid cell — red tint
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
        for sp in self.sun_particles:
            sp.draw(surface)
        self.menubar.draw(surface)

        # Wave info
        font = pygame.font.Font(None, 28)
        wave_text = font.render(f'Wave: {self.wave_index+1}/{self.total_waves}', True, WHITE)
        surface.blit(wave_text, (SCREEN_WIDTH - 150, 30))
        kill_text = font.render(f'Kills: {self.zombies_killed}', True, WHITE)
        surface.blit(kill_text, (SCREEN_WIDTH - 150, 55))

        # Pre-wave countdown
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
                    z.take_damage(999)
                    level.zombies_killed += 1

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
