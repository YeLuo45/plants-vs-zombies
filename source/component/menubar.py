import pygame
from source.constants import *

class Menubar:
    def __init__(self):
        self.sun = SUN_VALUE
        self.card_panel_h = 100
        self.card_list = list(PLANTS.keys())[:6]
        self.selected = None
        self.shovel_selected = False
        # Per-card cooldown timers (seconds remaining)
        self.cooldowns = {name: 0.0 for name in self.card_list}
        # Card positions
        self._calc_card_rects()

    def _calc_card_rects(self):
        total_w = len(self.card_list) * CARD_W + (len(self.card_list) - 1) * CARD_GAP
        start_x = (SCREEN_WIDTH - total_w) // 2
        self.card_rects = []
        for i in range(len(self.card_list)):
            x = start_x + i * (CARD_W + CARD_GAP)
            self.card_rects.append(pygame.Rect(x, CARD_PANEL_Y, CARD_W, CARD_H))
        # Shovel rect to the right of cards
        shovel_x = start_x + len(self.card_list) * (CARD_W + CARD_GAP) + 15
        self.shovel_rect = pygame.Rect(shovel_x, CARD_PANEL_Y + 10, SHOVEL_W, SHOVEL_H)

    def draw(self, surface):
        # Draw menu bar background
        pygame.draw.rect(surface, (80, 80, 80), (0, 0, SCREEN_WIDTH, MENUBAR_HEIGHT))
        # Draw sun counter
        font = pygame.font.Font(None, 36)
        sun_text = font.render(f'Sun: {self.sun}', True, YELLOW)
        surface.blit(sun_text, (20, 25))

        # Draw seed cards
        for i, name in enumerate(self.card_list):
            rect = self.card_rects[i]
            cfg = PLANTS[name]
            is_selected = self.selected == name
            # Cooldown fraction (0 = ready, 1 = full cooldown)
            cd_frac = min(1.0, self.cooldowns[name] / cfg['cooldown'])
            can_use = cd_frac < 1.0 and self.cooldowns[name] <= 0

            # Card bg
            if is_selected:
                bg = CARD_SELECTED
            elif cd_frac >= 1.0:
                bg = CARD_COOLDOWN
            else:
                bg = CARD_BG_COLOR
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, (200, 200, 100) if can_use else GRAY, rect, 2)

            # Plant circle
            cx, cy = rect.centerx, rect.centery - 10
            # Dim if on cooldown
            plant_color = cfg['color']
            if cd_frac > 0:
                dim = tuple(max(0, c - int(100 * cd_frac)) for c in plant_color)
                plant_color = dim
            pygame.draw.circle(surface, plant_color, (cx, cy), 20)

            # Cost text
            cost_font = pygame.font.Font(None, 22)
            cost_text = cost_font.render(f'{cfg["cost"]}', True, YELLOW)
            cost_rect = cost_text.get_rect(center=(cx, cy + 28))
            surface.blit(cost_text, cost_rect)

            # Cooldown overlay (darkened sweep from top)
            if cd_frac > 0:
                overlay_h = int(CARD_H * cd_frac)
                overlay_surf = pygame.Surface((CARD_W, overlay_h), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, int(180 * cd_frac)))
                surface.blit(overlay_surf, (rect.x, rect.y))
                # Cooldown seconds text
                cd_sec = int(cfg['cooldown'] - self.cooldowns[name])
                cd_font = pygame.font.Font(None, 24)
                cd_text = cd_font.render(str(max(0, cd_sec)), True, WHITE)
                cd_rect = cd_text.get_rect(center=(cx, cy))
                surface.blit(cd_text, cd_rect)

        # Draw shovel
        shovel_color = (180, 100, 50) if self.shovel_selected else BROWN
        pygame.draw.rect(surface, shovel_color, self.shovel_rect)
        pygame.draw.rect(surface, GREEN if self.shovel_selected else GRAY, self.shovel_rect, 2)
        # Shovel icon (simple rect + line)
        sx, sy = self.shovel_rect.centerx, self.shovel_rect.centery
        pygame.draw.rect(surface, GRAY, (sx - 5, sy - 20, 10, 25))
        pygame.draw.rect(surface, (160, 100, 50), (sx - 8, sy + 5, 16, 8))

    def update(self, dt):
        # Tick down cooldowns
        for name in self.cooldowns:
            if self.cooldowns[name] > 0:
                self.cooldowns[name] -= dt
                if self.cooldowns[name] < 0:
                    self.cooldowns[name] = 0

    def get_card_at(self, mx, my):
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mx, my):
                return self.card_list[i]
        return None

    def is_shovel_at(self, mx, my):
        return self.shovel_rect.collidepoint(mx, my)

    def can_afford(self, name):
        return self.sun >= PLANTS[name]['cost']

    def spend(self, name):
        cost = PLANTS[name]['cost']
        self.sun -= cost
        self.selected = None
        self.cooldowns[name] = PLANTS[name]['cooldown']

    def is_ready(self, name):
        return self.cooldowns[name] <= 0

    def add_sun(self, amount):
        self.sun += amount
