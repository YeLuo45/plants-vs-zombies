import pygame
import random
from source.constants import *
from source.component.map import Grid
from source.component.plant import create_plant
from source.component.bullet import SunParticle


ZEN_BG = (20, 80, 30)
ZEN_GRID_COLOR = (255, 255, 255, 40)  # subtle white
ZEN_TITLE_COLOR = (255, 255, 180)  # soft yellow
ZEN_SUN_INTERVAL = 5.0
ZEN_WATER_DURATION = 3.0
ZEN_WATER_BONUS = 5


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

        # Draw expanding blue circle
        for _ in range(3):
            offset_x = random.randint(-15, 15)
            offset_y = random.randint(-15, 15)
            pygame.draw.circle(surface, (100, 180, 255, alpha),
                               (int(self.x + offset_x), int(self.y + offset_y)), radius // 2)


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
        self.watered_plants = {}  # plant -> timer remaining
        self.selected = None
        self.all_plant_names = list(PLANTS.keys())

    def update(self, dt):
        # Sun production from plants every 5 seconds
        self.sun_timer += dt
        if self.sun_timer >= ZEN_SUN_INTERVAL:
            self.sun_timer = 0
            for row in range(GRID_ROWS):
                for col in range(GRID_COLS):
                    p = self.grid.cells[row][col]
                    if p is not None:
                        # Each plant produces sun
                        x = p.rect.centerx + random.randint(-20, 20)
                        y = p.rect.centery - 20
                        self.sun_particles.append(SunParticle(x, y))

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

    def handle_click(self, mx, my):
        # Check menubar area first
        if my < MENUBAR_HEIGHT:
            # Click on card
            card_names = self.all_plant_names[:8]
            total_w = len(card_names) * CARD_W + (len(card_names) - 1) * CARD_GAP
            start_x = (SCREEN_WIDTH - total_w) // 2
            for i, name in enumerate(card_names):
                rx = start_x + i * (CARD_W + CARD_GAP)
                rect = pygame.Rect(rx, CARD_PANEL_Y, CARD_W, CARD_H)
                if rect.collidepoint(mx, my):
                    self.selected = name
                    return
            return

        # Check if clicking on a placed plant (to water it)
        row, col = self.grid.get_cell_from_mouse(mx, my)
        if row is not None and col is not None:
            plant = self.grid.cells[row][col]
            if plant is not None:
                # Water the plant
                self.water_effects.append(WaterEffect(plant.rect.centerx, plant.rect.centery))
                self.watered_plants[plant] = ZEN_WATER_DURATION
                self.sun += ZEN_WATER_BONUS
                self.sun_collected_total += ZEN_WATER_BONUS
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
        if self.selected is not None:
            if self.grid.can_plant(row, col):
                plant = create_plant(self.selected, row, col, self.grid)
                self.grid.place_plant(plant, row, col)
                self.plants_placed += 1
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
            return 'menu'

    def draw(self, surface):
        # Peaceful background
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
                    # Watered indicator: water droplet icon
                    if p in self.watered_plants:
                        timer = self.watered_plants[p]
                        # Draw water droplet near plant
                        dx, dy = p.rect.centerx + 15, p.rect.centery - 25
                        pygame.draw.circle(surface, (100, 180, 255), (int(dx), int(dy)), 6)
                        pygame.draw.circle(surface, WHITE, (int(dx) - 2, int(dy) - 2), 2)

        # Draw water effects
        for w in self.water_effects:
            w.draw(surface)

        # Draw sun particles
        for sp in self.sun_particles:
            sp.draw(surface)

        # Draw menubar (all 13 plants, all cost 0)
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
        hint = hint_font.render("Click plant to water | Click card to select | Click grid to place", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 15))
        surface.blit(hint, hint_rect)

    def _draw_menubar(self, surface):
        # Draw menu bar background
        pygame.draw.rect(surface, (80, 80, 80), (0, 0, SCREEN_WIDTH, MENUBAR_HEIGHT))

        card_names = self.all_plant_names[:8]
        total_w = len(card_names) * CARD_W + (len(card_names) - 1) * CARD_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, name in enumerate(card_names):
            x = start_x + i * (CARD_W + CARD_GAP)
            rect = pygame.Rect(x, CARD_PANEL_Y, CARD_W, CARD_H)
            cfg = PLANTS[name]
            is_selected = self.selected == name

            # Card bg
            bg = CARD_SELECTED if is_selected else CARD_BG_COLOR
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, (200, 200, 100), rect, 2)

            # Plant circle
            cx, cy = rect.centerx, rect.centery - 10
            pygame.draw.circle(surface, cfg['color'], (cx, cy), 20)

            # Cost (0 for zen)
            cost_font = pygame.font.Font(None, 22)
            cost_text = cost_font.render("0", True, ZEN_TITLE_COLOR)
            cost_rect = cost_text.get_rect(center=(cx, cy + 28))
            surface.blit(cost_text, cost_rect)
