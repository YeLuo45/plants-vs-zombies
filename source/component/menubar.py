import pygame
from source.constants import *

MALLET_COST = 25
MALLET_MAX_USES = 3


class Menubar:
    def __init__(self):
        self.sun = SUN_VALUE
        self.card_panel_h = 100
        # All 13 plants (8 + torchwood + P2 plants)
        self.all_cards = list(PLANTS.keys())
        self.cards_per_page = 8
        self.card_page = 0
        self.card_list = self.all_cards[:self.cards_per_page]
        self.selected = None
        self.shovel_selected = False
        # Per-card cooldown timers (seconds remaining)
        self.cooldowns = {name: 0.0 for name in self.card_list}
        # Mallet tool
        self.mallet_selected = False
        self.mallet_uses = MALLET_MAX_USES
        # Card positions
        self._calc_card_rects()

    def _recalc_pages(self):
        """Rebuild card_list for current page."""
        start = self.card_page * self.cards_per_page
        self.card_list = self.all_cards[start:start + self.cards_per_page]
        # Sync cooldowns dict to current page
        for name in self.all_cards:
            if name not in self.cooldowns:
                self.cooldowns[name] = 0.0
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
        # Mallet rect: left of first card
        self.mallet_rect = pygame.Rect(start_x - 60, CARD_PANEL_Y + 5, 50, 70)
        # Page nav arrows (left and right of card strip)
        self.left_arrow = pygame.Rect(start_x - 28, CARD_PANEL_Y + 30, 22, 40)
        total_w = len(self.card_list) * CARD_W + (len(self.card_list) - 1) * CARD_GAP
        self.right_arrow = pygame.Rect(start_x + total_w + 7, CARD_PANEL_Y + 30, 28, 40)

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

        # Draw mallet tool (left of cards)
        self._draw_mallet(surface)

        # Draw page navigation arrows
        total_pages = (len(self.all_cards) + self.cards_per_page - 1) // self.cards_per_page
        if total_pages > 1:
            # Left arrow
            if self.card_page > 0:
                pygame.draw.polygon(surface, (200, 200, 200), [
                    (self.left_arrow.right - 5, self.left_arrow.centery),
                    (self.left_arrow.left + 5, self.left_arrow.top + 10),
                    (self.left_arrow.left + 5, self.left_arrow.bottom - 10)])
            # Right arrow
            if self.card_page < total_pages - 1:
                pygame.draw.polygon(surface, (200, 200, 200), [
                    (self.right_arrow.left + 5, self.right_arrow.centery),
                    (self.right_arrow.right - 5, self.right_arrow.top + 10),
                    (self.right_arrow.right - 5, self.right_arrow.bottom - 10)])
            # Page indicator
            page_font = pygame.font.Font(None, 20)
            page_text = page_font.render(f'{self.card_page + 1}/{total_pages}', True, (180, 180, 180))
            surface.blit(page_text, (self.right_arrow.right + 5, CARD_PANEL_Y + 55))

        # Draw shovel
        shovel_color = (180, 100, 50) if self.shovel_selected else BROWN
        pygame.draw.rect(surface, shovel_color, self.shovel_rect)
        pygame.draw.rect(surface, GREEN if self.shovel_selected else GRAY, self.shovel_rect, 2)
        # Shovel icon (simple rect + line)
        sx, sy = self.shovel_rect.centerx, self.shovel_rect.centery
        pygame.draw.rect(surface, GRAY, (sx - 5, sy - 20, 10, 25))
        pygame.draw.rect(surface, (160, 100, 50), (sx - 8, sy + 5, 16, 8))

    def _draw_mallet(self, surface):
        mx, my = self.mallet_rect.centerx, self.mallet_rect.centery
        is_selected = self.mallet_selected

        # Background
        bg = (160, 80, 80) if is_selected else (120, 60, 60)
        pygame.draw.rect(surface, bg, self.mallet_rect)
        border = (255, 100, 100) if is_selected else (150, 100, 100)
        pygame.draw.rect(surface, border, self.mallet_rect, 2)

        # Mallet head (brown rectangle)
        pygame.draw.rect(surface, (139, 90, 43), (mx - 15, my - 22, 30, 18))
        # Mallet handle
        pygame.draw.rect(surface, (160, 120, 80), (mx - 4, my - 4, 8, 22))
        # Uses count
        uses_font = pygame.font.Font(None, 22)
        uses_color = (100, 255, 100) if self.mallet_uses > 0 else (150, 50, 50)
        uses_text = uses_font.render(f'x{self.mallet_uses}', True, uses_color)
        surface.blit(uses_text, (self.mallet_rect.x + 5, self.mallet_rect.bottom - 18))
        # Cost
        cost_color = YELLOW if self.sun >= MALLET_COST else (150, 150, 50)
        cost_surf = uses_font.render(f'{MALLET_COST}', True, cost_color)
        surface.blit(cost_surf, (self.mallet_rect.right - 22, self.mallet_rect.bottom - 18))

    def update(self, dt):
        # Tick down cooldowns
        for name in self.cooldowns:
            if self.cooldowns[name] > 0:
                self.cooldowns[name] -= dt
                if self.cooldowns[name] < 0:
                    self.cooldowns[name] = 0

    def get_card_at(self, mx, my):
        # Check page arrows first
        if self.left_arrow.collidepoint(mx, my) and self.card_page > 0:
            self.card_page -= 1
            self._recalc_pages()
            return None
        if self.right_arrow.collidepoint(mx, my):
            total_pages = (len(self.all_cards) + self.cards_per_page - 1) // self.cards_per_page
            if self.card_page < total_pages - 1:
                self.card_page += 1
                self._recalc_pages()
                return None
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mx, my):
                return self.card_list[i]
        return None

    def is_shovel_at(self, mx, my):
        return self.shovel_rect.collidepoint(mx, my)

    def is_mallet_at(self, mx, my):
        return self.mallet_rect.collidepoint(mx, my)

    def can_afford(self, name):
        return self.sun >= PLANTS[name]['cost']

    def can_use_mallet(self):
        return self.mallet_uses > 0 and self.sun >= MALLET_COST

    def spend(self, name):
        cost = PLANTS[name]['cost']
        self.sun -= cost
        self.selected = None
        self.cooldowns[name] = PLANTS[name]['cooldown']

    def use_mallet(self):
        if self.mallet_uses > 0 and self.sun >= MALLET_COST:
            self.sun -= MALLET_COST
            self.mallet_uses -= 1
            self.mallet_selected = False
            return True
        return False

    def is_ready(self, name):
        return self.cooldowns[name] <= 0

    def add_sun(self, amount):
        self.sun += amount
