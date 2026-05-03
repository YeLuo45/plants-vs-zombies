import pygame
import random
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.zombie import create_zombie
from source.component.bullet import Bullet, ExplosionEffect, SunParticle
from source.component.menubar import Menubar

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
        self.wave_complete = False
        self.game_over = False
        self.victory = False
        self.total_waves = len(WAVES)
        self.zombies_killed = 0
        # Start first wave after 5 seconds
        self.pre_wave_timer = 5.0

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
        # Pre-wave countdown
        if not self.wave_active and self.pre_wave_timer > 0:
            self.pre_wave_timer -= dt
            if self.pre_wave_timer <= 0:
                self.start_wave(self.wave_index)
            return

        # Spawn zombies from wave
        if self.wave_active and self.wave_zombies_remaining:
            self.spawn_timer += dt
            wave_cfg = WAVES[self.wave_index]
            if self.spawn_timer >= wave_cfg['spawn_delay']:
                self.spawn_timer = 0
                ztype = self.wave_zombies_remaining.pop(0)
                row = random.randint(0, GRID_ROWS - 1)
                z = create_zombie(ztype, SCREEN_WIDTH + 50, row, self.grid)
                self.zombies.append(z)

        # Sun drop
        self.sun_timer += dt
        if self.sun_timer >= self.sun_interval:
            self.sun_timer = 0
            x = random.randint(GRID_OFFSET_X, GRID_OFFSET_X + GRID_COLS * CELL_WIDTH)
            y = random.randint(GRID_OFFSET_Y, GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT)
            self.sun_particles.append(SunParticle(x, y))

        # Update sun particles
        for sp in self.sun_particles[:]:
            sp.update(dt)
            if sp.y > SCREEN_HEIGHT:
                sp.alive = False
            if not sp.alive:
                self.sun_particles.remove(sp)

        # Update zombies
        for z in self.zombies[:]:
            result = z.update(dt)
            if result == 'reached_home':
                self.game_over = True
            if z.hp <= 0:
                self.zombies.remove(z)
                self.zombies_killed += 1

        # Update bullets
        for b in self.bullets[:]:
            b.update(dt)
            hit = b.check_collision(self.zombies)
            if not b.alive:
                self.bullets.remove(b)

        # Update explosions
        for e in self.particles[:]:
            e.update(dt)
            if not e.alive:
                self.particles.remove(e)

        # Update plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p:
                    action = p.update(dt, [])
                    if action == 'produce_sun':
                        x = p.rect.centerx + random.randint(-20, 20)
                        y = p.rect.centery - 20
                        self.sun_particles.append(SunParticle(x, y))
                    elif action == 'shoot':
                        bx = p.rect.right
                        by = p.rect.centery
                        ice = (p.name == 'snowpea')
                        shots = 2 if p.name == 'repeater' else 1
                        for _ in range(shots):
                            self.bullets.append(Bullet(bx, by, row, self.grid, ice))
                    elif action == 'explode':
                        # Cherry bomb explosion
                        cx, cy = p.rect.centerx, p.rect.centery
                        self.particles.append(ExplosionEffect(cx, cy))
                        # Kill zombies in 3x3 area
                        for z in self.zombies[:]:
                            if abs(z.x - cx) < 120 and abs(z.y - cy) < 100:
                                if z.take_damage(999):
                                    self.zombies.remove(z)
                                    self.zombies_killed += 1
                        # Remove plant
                        self.grid.remove_plant(p.row, p.col)
                    elif action == 'chomp_done':
                        pass

        # Chomper eating
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p and p.name == 'chomper':
                    for z in self.zombies:
                        if z.row == row and not p.eating:
                            p.try_eat_zombie(z)

        # Check wave completion
        if self.wave_active and not self.wave_zombies_remaining and not self.zombies:
            self.wave_active = False
            self.wave_index += 1
            if self.wave_index >= self.total_waves:
                self.victory = True
            else:
                self.pre_wave_timer = 5.0

    def handle_click(self, mx, my):
        # Check card click
        card = self.menubar.get_card_at(mx, my)
        if card:
            if self.menubar.can_afford(card):
                self.menubar.selected = card
            else:
                self.menubar.selected = None
            return
        # Check sun collection
        for sp in self.sun_particles[:]:
            dx = mx - sp.x
            dy = my - sp.y
            if dx*dx + dy*dy < 400:
                self.menubar.add_sun(25)
                self.sun_particles.remove(sp)
                return
        # Check plant placement
        if self.menubar.selected:
            row, col = self.grid.get_cell_from_mouse(mx, my)
            if self.grid.can_plant(row, col):
                plant = create_plant(self.menubar.selected, row, col, self.grid)
                self.grid.place_plant(plant, row, col)
                self.menubar.spend(self.menubar.selected)

    def draw(self, surface):
        surface.fill((30, 80, 30))  # dark bg
        self.grid.draw(surface)
        # Draw plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p:
                    p.draw(surface)
        # Draw zombies
        for z in self.zombies:
            z.draw(surface)
        # Draw bullets
        for b in self.bullets:
            b.draw(surface)
        # Draw explosions
        for e in self.particles:
            e.draw(surface)
        # Draw sun particles
        for sp in self.sun_particles:
            sp.draw(surface)
        # Draw menubar
        self.menubar.draw(surface)
        # Wave info
        font = pygame.font.Font(None, 28)
        wave_text = font.render(f'Wave: {self.wave_index+1}/{self.total_waves}', True, WHITE)
        surface.blit(wave_text, (SCREEN_WIDTH - 150, 30))
        # Pre-wave countdown
        if not self.wave_active and not self.victory and not self.game_over and self.pre_wave_timer > 0:
            count_font = pygame.font.Font(None, 72)
            count_text = count_font.render(str(int(self.pre_wave_timer)+1), True, (255, 100, 100))
            count_rect = count_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            surface.blit(count_text, count_rect)
