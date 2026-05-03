import pygame
from source.constants import *

class Menubar:
    def __init__(self):
        self.sun = SUN_VALUE
        self.card_panel_h = 100
        self.cards = []
        # Available plants for this level (select 6)
        self.available = list(PLANTS.keys())
        self.selected = None
        self.card_rects = []
        self.init_cards()

    def init_cards(self):
        # Select first 6 plants as available cards
        self.card_list = self.available[:6]
        card_w = 70
        card_h = 80
        start_x = SCREEN_WIDTH // 2 - (len(self.card_list) * (card_w + 10)) // 2
        self.card_rects = []
        for i, name in enumerate(self.card_list):
            x = start_x + i * (card_w + 10)
            y = CARD_PANEL_Y
            self.card_rects.append(pygame.Rect(x, y, card_w, card_h))

    def draw(self, surface):
        # Draw menu bar background
        pygame.draw.rect(surface, (80, 80, 80), (0, 0, SCREEN_WIDTH, MENUBAR_HEIGHT))
        # Draw sun counter
        font = pygame.font.Font(None, 36)
        sun_text = font.render(f'Sun: {self.sun}', True, (255, 255, 0))
        surface.blit(sun_text, (20, 25))
        # Draw cards
        for i, (name, rect) in enumerate(zip(self.card_list, self.card_rects)):
            cfg = PLANTS[name]
            is_selected = self.selected == name
            # Card bg
            bg_color = CARD_SELECTED if is_selected else CARD_BG_COLOR
            pygame.draw.rect(surface, bg_color, rect)
            pygame.draw.rect(surface, (200, 200, 100), rect, 2)
            # Plant circle
            cx, cy = rect.centerx, rect.centery - 10
            pygame.draw.circle(surface, cfg['color'], (cx, cy), 20)
            # Cost text
            cost_font = pygame.font.Font(None, 22)
            cost_text = cost_font.render(f'{cfg["cost"]}', True, (255, 255, 0))
            cost_rect = cost_text.get_rect(center=(cx, cy + 28))
            surface.blit(cost_text, cost_rect)
            # Name
            name_font = pygame.font.Font(None, 16)
            name_surf = name_font.render(cfg['desc'], True, TEXT_COLOR)
            name_rect = name_surf.get_rect(center=(cx, rect.bottom - 15))
            surface.blit(name_surf, name_rect)
            # Cooldown overlay
            cfg_plant = PLANTS[name]
            cd = 0  # TODO: track cooldown per card

    def get_card_at(self, mx, my):
        for i, rect in enumerate(self.card_rects):
            if rect.collidepoint(mx, my):
                return self.card_list[i]
        return None

    def can_afford(self, name):
        return self.sun >= PLANTS[name]['cost']

    def spend(self, name):
        cost = PLANTS[name]['cost']
        self.sun -= cost
        if self.selected == name:
            self.selected = None

    def add_sun(self, amount):
        self.sun += amount
