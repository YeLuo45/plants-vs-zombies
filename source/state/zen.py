import pygame
import random
import os
import json
import math
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.bullet import SunParticle
from source.state.achievements import AchievementManager, StatsManager


ZEN_BG = (20, 80, 30)
ZEN_GRID_COLOR = (255, 255, 255, 40)
ZEN_TITLE_COLOR = (255, 255, 180)
ZEN_SUN_INTERVAL = 5.0
ZEN_WATER_DURATION = 3.0
ZEN_WATER_BONUS = 5
ZEN_MARIGOLD_SUN = 30
ZEN_REGULAR_SUN = 15
ZEN_MAGNET_RADIUS = 150
ZEN_MAGNET_SPEED = 200
ZEN_PLANT_FOOD_COST = 50
ZEN_PLANT_FOOD_BONUS = 100

GARDEN_SAVE_FILE = os.path.expanduser('~/.pvz_garden.json')


class WaterEffect:
    """Blue sparkle effect when a plant is watered."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 0.6
        self.alive = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha = int(255 * (1.0 - progress))
        radius = int(10 + 30 * progress)
        for _ in range(3):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            pygame.draw.circle(surface, (100, 180, 255, alpha),
                               (int(self.x + offset_x), int(self.y + offset_y)), radius // 2)


class PlantFoodEffect:
    """Golden sparkle burst effect when plant is fed."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 0
        self.duration = 1.0
        self.alive = True
        self.particles = []
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 150)
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'dist': 0,
                'size': random.randint(4, 8),
            })

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.alive = False
            return
        for p in self.particles:
            p['dist'] += p['speed'] * dt

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha = int(255 * (1.0 - progress))
        for p in self.particles:
            dx = math.cos(p['angle']) * p['dist']
            dy = math.sin(p['angle']) * p['dist']
            cx = int(self.x + dx)
            cy = int(self.y + dy)
            pygame.draw.circle(surface, (255, 215, 0, alpha), (cx, cy), p['size'])


class GardenGnome:
    """Decorative garden gnome - spawned after watering 10 plants."""
    def __init__(self, row, col, grid):
        self.row = row
        self.col = col
        self.rect = grid.get_cell_rect(row, col)
        self.x = self.rect.centerx
        self.y = self.rect.centery

    def draw(self, surface):
        # Gnome hat (red pointed hat)
        pygame.draw.polygon(surface, (200, 30, 30), [
            (self.x, self.y - 30),
            (self.x - 12, self.y - 5),
            (self.x + 12, self.y - 5),
        ])
        # Hat brim
        pygame.draw.ellipse(surface, (150, 20, 20), (self.x - 14, self.y - 8, 28, 8))
        # Face
        pygame.draw.circle(surface, (240, 200, 160), (self.x, self.y + 5), 12)
        # Beard
        pygame.draw.ellipse(surface, (220, 220, 220), (self.x - 10, self.y + 8, 20, 14))
        # Eyes
        pygame.draw.circle(surface, BLACK, (self.x - 4, self.y + 2), 2)
        pygame.draw.circle(surface, BLACK, (self.x + 4, self.y + 2), 2)


class ZenState:
    """
    Relaxing Zen Garden mode.
    No zombies, no pressure. Place plants, collect sun, water your garden.
    """
    def __init__(self, screen):
        self.screen = screen
        self.grid = Grid()
        self.sun = 500
        self.sun_timer = 0
        self.sun_particles = []
        self.plants_placed = 0
        self.sun_collected_total = 0
        self.preview_row = None
        self.preview_col = None
        self.water_effects = []
        self.plant_food_effects = []
        self.watered_plants = {}
        self.selected = None
        self.all_plant_names = list(PLANTS.keys())

        # Paged plant selection
        self.card_page = 0
        self.cards_per_page = 8
        self.total_pages = (len(self.all_plant_names) + self.cards_per_page - 1) // self.cards_per_page
        self.left_arrow_rect = pygame.Rect(0, CARD_PANEL_Y, 40, CARD_H)
        self.right_arrow_rect = pygame.Rect(0, CARD_PANEL_Y, 40, CARD_H)

        # Session stats
        self.session_water_count = 0
        self.session_marigolds = 0
        self.session_magnet_sun = 0
        self.gnome_spawned = False
        self.gnome = None
        self.gnome_spawn_row = None
        self.gnome_spawn_col = None

        # Plant Food usage
        self.plant_food_uses = 0

        # Try to play zen music
        try:
            from source.component.sound_manager import SoundManager
            sm = SoundManager.get_instance()
            sm.play_music('zen')
        except Exception:
            pass

        # Load saved garden
        self._load_garden()

    def _get_page_card_names(self):
        start = self.card_page * self.cards_per_page
        end = start + self.cards_per_page
        return self.all_plant_names[start:end]

    def _save_garden(self):
        """Save garden state to file."""
        cells_data = {}
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.grid.cells[r][c]
                if p:
                    cells_data[f'{r},{c}'] = p.name

        data = {
            'sun': self.sun,
            'plants_placed': self.plants_placed,
            'sun_collected_total': self.sun_collected_total,
            'cells': cells_data,
            'session_water_count': self.session_water_count,
            'session_marigolds': self.session_marigolds,
            'session_magnet_sun': self.session_magnet_sun,
            'plant_food_uses': self.plant_food_uses,
        }
        try:
            os.makedirs(os.path.dirname(GARDEN_SAVE_FILE), exist_ok=True)
            with open(GARDEN_SAVE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_garden(self):
        """Load garden state from file."""
        if not os.path.exists(GARDEN_SAVE_FILE):
            return
        try:
            with open(GARDEN_SAVE_FILE, 'r') as f:
                data = json.load(f)
            self.sun = data.get('sun', 500)
            self.plants_placed = data.get('plants_placed', 0)
            self.sun_collected_total = data.get('sun_collected_total', 0)
            self.session_water_count = data.get('session_water_count', 0)
            self.session_marigolds = data.get('session_marigolds', 0)
            self.session_magnet_sun = data.get('session_magnet_sun', 0)
            self.plant_food_uses = data.get('plant_food_uses', 0)

            cells = data.get('cells', {})
            for key, plant_name in cells.items():
                r, c = key.split(',')
                r, c = int(r), int(c)
                if plant_name in PLANTS:
                    plant = create_plant(plant_name, r, c, self.grid)
                    self.grid.place_plant(plant, r, c)

            # Check if gnome should exist (was spawned before)
            if self.session_water_count >= 10:
                self.gnome_spawned = True
                # Try to find an empty cell for gnome
                empty_cells = []
                for r in range(GRID_ROWS):
                    for c in range(GRID_COLS):
                        if self.grid.cells[r][c] is None:
                            empty_cells.append((r, c))
                if empty_cells:
                    self.gnome_spawn_row, self.gnome_spawn_col = random.choice(empty_cells)
                    self.gnome = GardenGnome(self.gnome_spawn_row, self.gnome_spawn_col, self.grid)

            # Notify achievements
            ach = AchievementManager.get_instance()
            if self.plants_placed >= 10:
                ach.on_zen_plant(self.plants_placed)
            if self.session_water_count >= 10:
                ach.on_zen_water(self.session_water_count)
            if self.session_marigolds >= 20:
                ach.on_marigold_placed(self.session_marigolds)
            if self.session_magnet_sun >= 500:
                ach.on_magnet_sun(self.session_magnet_sun)

        except Exception:
            pass

    def update(self, dt):
        # Sun production from plants every 5 seconds
        self.sun_timer += dt
        if self.sun_timer >= ZEN_SUN_INTERVAL:
            self.sun_timer = 0
            for row in range(GRID_ROWS):
                for col in range(GRID_COLS):
                    p = self.grid.cells[row][col]
                    if p is not None:
                        # Marigold produces 30, others produce 15
                        sun_amount = ZEN_MARIGOLD_SUN if p.name == 'marigold' else ZEN_REGULAR_SUN
                        for _ in range(sun_amount // 15):
                            x = p.rect.centerx + random.randint(-20, 20)
                            y = p.rect.centery - 20
                            self.sun_particles.append(SunParticle(x, y))

        # Gold Magnet attraction
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p is not None and p.name == 'goldmagnet':
                    mx, my = p.rect.centerx, p.rect.centery
                    for sp in self.sun_particles[:]:
                        dx = mx - sp.x
                        dy = my - sp.y
                        dist_sq = dx * dx + dy * dy
                        if dist_sq < ZEN_MAGNET_RADIUS * ZEN_MAGNET_RADIUS and dist_sq > 0:
                            dist = math.sqrt(dist_sq)
                            # Accelerate toward magnet
                            speed = ZEN_MAGNET_SPEED * dt
                            sp.x += (dx / dist) * speed
                            sp.y += (dy / dist) * speed
                            sp.vy = 0  # Cancel gravity while being attracted
                            sp.vx = 0
                            # Check if reached magnet
                            if dist < 25:
                                self.sun += 25
                                self.sun_collected_total += 25
                                self.session_magnet_sun += 25
                                AchievementManager.get_instance().on_magnet_sun(self.session_magnet_sun)
                                self.sun_particles.remove(sp)

        # Update sun particles
        for sp in self.sun_particles[:]:
            sp.update(dt)
            if sp.y > SCREEN_HEIGHT or not sp.alive:
                self.sun_particles.remove(sp)

        # Update watered plant timers
        for p in list(self.watered_plants.keys()):
            self.watered_plants[p] -= dt
            if self.watered_plants[p] <= 0:
                del self.watered_plants[p]

        # Update water effects
        for w in self.water_effects[:]:
            w.update(dt)
            if not w.alive:
                self.water_effects.remove(w)

        # Update plant food effects
        for pf in self.plant_food_effects[:]:
            pf.update(dt)
            if not pf.alive:
                self.plant_food_effects.remove(pf)

        # Update gnome animation (subtle bob)
        if self.gnome is not None:
            self.gnome.y += math.sin(pygame.time.get_ticks() / 500.0) * 0.05

    def handle_click(self, mx, my):
        # Check left arrow
        if self.left_arrow_rect.collidepoint(mx, my):
            if self.card_page > 0:
                self.card_page -= 1
            return

        # Check right arrow
        if self.right_arrow_rect.collidepoint(mx, my):
            if self.card_page < self.total_pages - 1:
                self.card_page += 1
            return

        # Check menubar area
        if my < MENUBAR_HEIGHT:
            card_names = self._get_page_card_names()
            total_w = len(card_names) * CARD_W + (len(card_names) - 1) * CARD_GAP
            # Adjust for page offset
            page_offset_x = self.card_page * self.cards_per_page * (CARD_W + CARD_GAP)
            start_x = (SCREEN_WIDTH - self.cards_per_page * CARD_W - (self.cards_per_page - 1) * CARD_GAP) // 2

            for i, name in enumerate(card_names):
                rx = start_x + i * (CARD_W + CARD_GAP)
                rect = pygame.Rect(rx, CARD_PANEL_Y, CARD_W, CARD_H)
                if rect.collidepoint(mx, my):
                    self.selected = name
                    return
            return

        # Check if clicking on a placed plant (to water or feed)
        row, col = self.grid.get_cell_from_mouse(mx, my)
        if row is not None and col is not None:
            plant = self.grid.cells[row][col]
            if plant is not None:
                # Plant Food: click on plant when we have sun >= 50
                if self.sun >= ZEN_PLANT_FOOD_COST:
                    self.sun -= ZEN_PLANT_FOOD_COST
                    self.sun += ZEN_PLANT_FOOD_BONUS
                    self.sun_collected_total += ZEN_PLANT_FOOD_BONUS
                    self.plant_food_uses += 1
                    StatsManager.get_instance().plants_planted += 1  # track usage
                    # Plant food effect
                    self.plant_food_effects.append(PlantFoodEffect(
                        plant.rect.centerx, plant.rect.centery))
                    return

                # Water the plant (no plant food)
                if plant not in self.watered_plants:
                    self.water_effects.append(WaterEffect(plant.rect.centerx, plant.rect.centery))
                    self.watered_plants[plant] = ZEN_WATER_DURATION
                    self.sun += ZEN_WATER_BONUS
                    self.sun_collected_total += ZEN_WATER_BONUS
                    self.session_water_count += 1
                    AchievementManager.get_instance().on_zen_water(self.session_water_count)

                    # Spawn gnome after watering 10 plants (once per session)
                    if self.session_water_count >= 10 and not self.gnome_spawned:
                        self.gnome_spawned = True
                        # Find empty cell for gnome
                        empty_cells = []
                        for r in range(GRID_ROWS):
                            for c in range(GRID_COLS):
                                if self.grid.cells[r][c] is None:
                                    empty_cells.append((r, c))
                        if empty_cells:
                            self.gnome_spawn_row, self.gnome_spawn_col = random.choice(empty_cells)
                            self.gnome = GardenGnome(self.gnome_spawn_row, self.gnome_spawn_col, self.grid)
                    return

        # Check sun collection
        for sp in self.sun_particles[:]:
            dx = mx - sp.x
            dy = my - sp.y
            if dx * dx + dy * dy < 400:
                self.sun += 25
                self.sun_collected_total += 25
                self.sun_particles.remove(sp)
                return

        # Plant placement (free, instant)
        if self.selected is not None and row is not None and col is not None:
            if self.grid.can_plant(row, col):
                plant = create_plant(self.selected, row, col, self.grid)
                self.grid.place_plant(plant, row, col)
                self.plants_placed += 1
                AchievementManager.get_instance().on_plant_placed()
                AchievementManager.get_instance().on_zen_plant(self.plants_placed)

                # Track marigolds
                if self.selected == 'marigold':
                    self.session_marigolds += 1
                    AchievementManager.get_instance().on_marigold_placed(self.session_marigolds)

                self.selected = None

    def handle_mouse_move(self, mx, my):
        if self.selected is not None:
            row, col = self.grid.get_cell_from_mouse(mx, my)
            self.preview_row = row
            self.preview_col = col
        else:
            self.preview_row = None
            self.preview_col = None

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self._save_garden()
            return 'menu'

    def draw(self, surface):
        surface.fill(ZEN_BG)

        # Draw subtle grid
        for row in range(GRID_ROWS + 1):
            y = self.grid.offset_y + row * self.grid.cell_h
            pygame.draw.line(surface, ZEN_GRID_COLOR,
                             (self.grid.offset_x, y),
                             (self.grid.offset_x + self.grid.cols * self.grid.cell_w, y), 1)
        for col in range(GRID_COLS + 1):
            x = self.grid.offset_x + col * self.grid.cell_w
            pygame.draw.line(surface, ZEN_GRID_COLOR,
                             (x, self.grid.offset_y),
                             (x, self.grid.offset_y + self.grid.rows * self.grid.cell_h), 1)

        # Plant preview
        if self.selected and self.preview_row is not None:
            row, col = self.preview_row, self.preview_col
            if self.grid.can_plant(row, col):
                rect = self.grid.get_cell_rect(row, col)
                ghost_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                cfg = PLANTS[self.selected]
                color = cfg['color']
                pygame.draw.rect(ghost_surf, (*color, 100), ghost_surf.get_rect())
                pygame.draw.circle(ghost_surf, (*color, 150),
                                   (rect.width // 2, rect.height // 2), 20)
                pygame.draw.rect(ghost_surf, (*color, 80), ghost_surf.get_rect(), 2)
                surface.blit(ghost_surf, rect.topleft)
            elif row is not None:
                rect = self.grid.get_cell_rect(row, col)
                ghost_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(ghost_surf, (255, 0, 0, 60), ghost_surf.get_rect())
                pygame.draw.rect(ghost_surf, (255, 0, 0, 120), ghost_surf.get_rect(), 2)
                surface.blit(ghost_surf, rect.topleft)

        # Draw plants
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                p = self.grid.cells[row][col]
                if p:
                    p.draw(surface)
                    # Watered indicator
                    if p in self.watered_plants:
                        timer = self.watered_plants[p]
                        dx, dy = p.rect.centerx + 15, p.rect.centery - 25
                        pygame.draw.circle(surface, (100, 180, 255), (int(dx), int(dy)), 6)
                        pygame.draw.circle(surface, WHITE, (int(dx) - 2, int(dy) - 2), 2)
                    # Gold Magnet radius indicator (subtle)
                    if p.name == 'goldmagnet':
                        pygame.draw.circle(surface, (200, 200, 220, 30),
                                          (p.rect.centerx, p.rect.centery), ZEN_MAGNET_RADIUS, 1)

        # Draw garden gnome
        if self.gnome is not None:
            self.gnome.draw(surface)

        # Draw water effects
        for w in self.water_effects:
            w.draw(surface)

        # Draw plant food effects
        for pf in self.plant_food_effects:
            pf.draw(surface)

        # Draw sun particles
        for sp in self.sun_particles:
            sp.draw(surface)

        # Draw menubar with paged plant selection
        self._draw_menubar(surface)

        # Title
        title_font = pygame.font.Font(None, 40)
        title = title_font.render("Zen Garden - Relax and grow", True, ZEN_TITLE_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 45))
        surface.blit(title, title_rect)

        # Stats at top right
        font = pygame.font.Font(None, 28)
        sun_text = font.render(f"Sun: {self.sun}", True, ZEN_TITLE_COLOR)
        surface.blit(sun_text, (SCREEN_WIDTH - 140, 30))
        plants_text = font.render(f"Plants: {self.plants_placed}", True, ZEN_TITLE_COLOR)
        surface.blit(plants_text, (SCREEN_WIDTH - 140, 55))

        # Hint at bottom
        hint_font = pygame.font.Font(None, 24)
        hint = hint_font.render("Click plant to water/feed | Click card to select | Click grid to place | ESC to save & quit", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 15))
        surface.blit(hint, hint_rect)

    def _draw_menubar(self, surface):
        pygame.draw.rect(surface, (80, 80, 80), (0, 0, SCREEN_WIDTH, MENUBAR_HEIGHT))

        # Left arrow
        self.left_arrow_rect.x = 5
        self.left_arrow_rect.y = CARD_PANEL_Y
        arrow_color = (150, 150, 100) if self.card_page > 0 else (60, 60, 60)
        pygame.draw.polygon(surface, arrow_color, [
            (self.left_arrow_rect.right, self.left_arrow_rect.centery),
            (self.left_arrow_rect.left + 5, self.left_arrow_rect.top + 15),
            (self.left_arrow_rect.left + 5, self.left_arrow_rect.bottom - 15),
        ])

        # Right arrow
        self.right_arrow_rect.x = SCREEN_WIDTH - 45
        self.right_arrow_rect.y = CARD_PANEL_Y
        arrow_color = (150, 150, 100) if self.card_page < self.total_pages - 1 else (60, 60, 60)
        pygame.draw.polygon(surface, arrow_color, [
            (self.right_arrow_rect.left, self.right_arrow_rect.centery),
            (self.right_arrow_rect.right - 5, self.right_arrow_rect.top + 15),
            (self.right_arrow_rect.right - 5, self.right_arrow_rect.bottom - 15),
        ])

        # Cards for current page
        card_names = self._get_page_card_names()
        total_w = len(card_names) * CARD_W + (len(card_names) - 1) * CARD_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, name in enumerate(card_names):
            x = start_x + i * (CARD_W + CARD_GAP)
            rect = pygame.Rect(x, CARD_PANEL_Y, CARD_W, CARD_H)
            cfg = PLANTS[name]
            is_selected = self.selected == name

            bg = CARD_SELECTED if is_selected else CARD_BG_COLOR
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, (200, 200, 100), rect, 2)

            # Plant circle
            cx, cy = rect.centerx, rect.centery - 10
            pygame.draw.circle(surface, cfg['color'], (cx, cy), 20)

            # Cost (0 for zen, but show original cost for display)
            cost_font = pygame.font.Font(None, 22)
            cost_text = cost_font.render("0", True, ZEN_TITLE_COLOR)
            cost_rect = cost_text.get_rect(center=(cx, cy + 28))
            surface.blit(cost_text, cost_rect)

        # Page indicator
        page_font = pygame.font.Font(None, 24)
        page_text = page_font.render(f"{self.card_page + 1}/{self.total_pages}", True, ZEN_TITLE_COLOR)
        page_rect = page_text.get_rect(center=(SCREEN_WIDTH // 2, MENUBAR_HEIGHT - 12))
        surface.blit(page_text, page_rect)
