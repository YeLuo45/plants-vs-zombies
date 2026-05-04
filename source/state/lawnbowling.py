import pygame
import random
from source.constants import *


class Nut:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.speed = 8
        self.vx = 0
        self.vy = 0
        self.active = True

    def roll(self):
        self.vx = -self.speed
        # slight vertical bounce direction based on position
        self.vy = random.choice([-2, 2])

    def update(self, dt, top_bound, bottom_bound):
        if self.vx == 0:
            return
        self.x += self.vx
        self.y += self.vy
        # bounce off top/bottom
        if self.y - self.radius < top_bound:
            self.y = top_bound + self.radius
            self.vy = abs(self.vy)
        if self.y + self.radius > bottom_bound:
            self.y = bottom_bound - self.radius
            self.vy = -abs(self.vy)

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.circle(surface, (150, 100, 50), (cx, cy), self.radius)
        pygame.draw.circle(surface, (180, 130, 70), (cx, cy), self.radius, 2)
        # highlight
        pygame.draw.circle(surface, (200, 160, 100), (cx - 6, cy - 6), 5)


class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 40
        self.h = 60
        self.speed = 0.2
        self.dead = False

    def update(self, dt):
        if not self.dead:
            self.x += self.speed

    def draw(self, surface):
        if self.dead:
            return
        cx, cy = int(self.x), int(self.y)
        # body
        pygame.draw.rect(surface, (100, 60, 40), (cx - self.w // 2, cy - self.h // 2, self.w, self.h))
        pygame.draw.rect(surface, (80, 50, 30), (cx - self.w // 2, cy - self.h // 2, self.w, self.h), 2)
        # head
        pygame.draw.circle(surface, (120, 80, 60), (cx, cy - self.h // 2 - 10), 12)
        pygame.draw.circle(surface, (80, 50, 30), (cx, cy - self.h // 2 - 10), 12, 2)
        # eyes
        pygame.draw.circle(surface, (200, 200, 200), (cx - 4, cy - self.h // 2 - 12), 3)
        pygame.draw.circle(surface, (200, 200, 200), (cx + 4, cy - self.h // 2 - 12), 3)


class LawnBowlingState:
    def __init__(self, screen):
        self.screen = screen
        self.state = 'aiming'
        self.wave = 1
        self.total_waves = 10
        self.nuts_remaining = 3
        self.kills = 0
        self.nuts = []
        self.zombies = []
        self.aim_x = SCREEN_WIDTH - 80
        self.aim_y = GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT // 2
        self.current_nut = None
        self.wave_complete_timer = 0
        self.game_over = False
        self.victory = False

        self.top_bound = GRID_OFFSET_Y + 10
        self.bottom_bound = GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT - 10
        self._spawn_nuts()
        self._spawn_wave()

    def _spawn_nuts(self):
        self.nuts = []
        rows = [GRID_OFFSET_Y + CELL_HEIGHT // 2 + r * CELL_HEIGHT for r in range(GRID_ROWS)]
        used = []
        for _ in range(min(3, self.nuts_remaining)):
            row = random.choice([r for r in range(GRID_ROWS)])
            while row in used and len(used) < GRID_ROWS:
                row = random.choice([r for r in range(GRID_ROWS)])
            used.append(row)
            y = GRID_OFFSET_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
            x = SCREEN_WIDTH - 80
            self.nuts.append(Nut(x, y))
        self.nuts_remaining -= len(self.nuts)

    def _spawn_wave(self):
        self.zombies = []
        count = 2 + self.wave
        for i in range(count):
            row = random.randint(0, GRID_ROWS - 1)
            x = GRID_OFFSET_X + 20 + i * 60
            y = GRID_OFFSET_Y + row * CELL_HEIGHT + CELL_HEIGHT // 2
            z = Zombie(x, y)
            z.speed = 0.2 + self.wave * 0.02
            self.zombies.append(z)

    def _start_roll(self):
        if not self.nuts:
            return
        self.current_nut = self.nuts.pop(0)
        self.current_nut.roll()
        self.state = 'rolling'

    def update(self, dt):
        if self.state == 'wave_complete':
            self.wave_complete_timer -= dt
            if self.wave_complete_timer <= 0:
                if self.wave >= self.total_waves:
                    self.victory = True
                    self.state = 'victory'
                else:
                    self.wave += 1
                    bonus_nuts = 2
                    self.nuts_remaining += bonus_nuts
                    self._spawn_nuts()
                    self._spawn_wave()
                    self.state = 'aiming'
            return

        if self.state == 'rolling':
            if self.current_nut is None:
                return
            self.current_nut.update(dt, self.top_bound, self.bottom_bound)

            # Check collision with zombies
            for z in self.zombies[:]:
                if z.dead:
                    continue
                dx = self.current_nut.x - z.x
                dy = self.current_nut.y - z.y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < 30:
                    z.dead = True
                    self.kills += 1
                    # bounce nut back
                    self.current_nut.vx = abs(self.current_nut.vx) * 0.5
                    self.current_nut.vy = -self.current_nut.vy * 0.8

            # Nut reached left edge
            if self.current_nut.x < GRID_OFFSET_X:
                self.current_nut = None
                if not self.zombies or all(z.dead for z in self.zombies):
                    self._check_wave_complete()
                else:
                    self._check_nut_loss()
                return

            # Nut bounced back to right edge (lost momentum)
            if self.current_nut.x > SCREEN_WIDTH + 50:
                self.current_nut = None
                self._check_nut_loss()
                return

        # Update zombies
        for z in self.zombies:
            z.update(dt)

        # Check if zombie reached right edge
        for z in self.zombies:
            if not z.dead and z.x > GRID_OFFSET_X + GRID_COLS * CELL_WIDTH:
                z.dead = True
                self.nuts_remaining -= 1
                if self.nuts_remaining < 0:
                    self.nuts_remaining = 0

        # Check wave complete
        self._check_wave_complete()

    def _check_wave_complete(self):
        all_dead = all(z.dead for z in self.zombies)
        no_nuts = len(self.nuts) == 0 and self.current_nut is None
        if all_dead or no_nuts:
            if self.nuts_remaining <= 0 and no_nuts:
                self.state = 'game_over'
                self.game_over = True
            elif all_dead:
                self.state = 'wave_complete'
                self.wave_complete_timer = 2.0
            else:
                self.state = 'game_over'
                self.game_over = True

    def _check_nut_loss(self):
        if not self.nuts and self.current_nut is None:
            if all(z.dead for z in self.zombies):
                self.state = 'wave_complete'
                self.wave_complete_timer = 2.0
            else:
                self.state = 'game_over'
                self.game_over = True

    def handle_click(self, mx, my):
        if self.state == 'aiming':
            self._start_roll()
        elif self.state == 'wave_complete':
            pass
        elif self.state == 'game_over' or self.state == 'victory':
            # Reset game
            self.__init__(self.screen)

    def handle_mouse_move(self, mx, my):
        if self.state == 'aiming':
            # Clamp to lawn area horizontally
            self.aim_x = max(GRID_OFFSET_X, min(mx, SCREEN_WIDTH - 50))
            self.aim_y = my
            # Clamp to lawn rows vertically
            row_h = CELL_HEIGHT
            self.aim_y = max(GRID_OFFSET_Y + 20, min(self.aim_y, GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT - 20))
            if self.nuts:
                self.nuts[0].x = self.aim_x
                self.nuts[0].y = self.aim_y

    def draw(self, surface):
        # Background
        surface.fill((20, 60, 20))

        # Grid lines
        for row in range(GRID_ROWS + 1):
            y = GRID_OFFSET_Y + row * CELL_HEIGHT
            pygame.draw.line(surface, (15, 45, 15), (GRID_OFFSET_X, y), (GRID_OFFSET_X + GRID_COLS * CELL_WIDTH, y), 1)
        for col in range(GRID_COLS + 1):
            x = GRID_OFFSET_X + col * CELL_WIDTH
            pygame.draw.line(surface, (15, 45, 15), (x, GRID_OFFSET_Y), (x, GRID_OFFSET_Y + GRID_ROWS * CELL_HEIGHT), 1)

        # Draw zombies
        for z in self.zombies:
            z.draw(surface)

        # Draw nuts (all nuts in aiming state)
        for n in self.nuts:
            n.draw(surface)

        # Draw rolling nut
        if self.state == 'rolling' and self.current_nut:
            self.current_nut.draw(surface)

        # Draw aim arrow (yellow dashed line)
        if self.state == 'aiming' and self.nuts:
            n = self.nuts[0]
            start_x = int(n.x)
            end_x = GRID_OFFSET_X
            y = int(n.y)
            dash_len = 10
            gap_len = 5
            dx = -1
            x = start_x
            while x > end_x:
                next_x = max(end_x, x + dx * dash_len)
                pygame.draw.line(surface, YELLOW, (x, y), (int(next_x), y), 2)
                x += dx * (dash_len + gap_len)

        # HUD at top
        font = pygame.font.Font(None, 28)
        hud_text = font.render(f'Wave {self.wave}/{self.total_waves} | Nuts: {self.nuts_remaining + (len(self.nuts) if self.state == "aiming" else 0)} | Kills: {self.kills}', True, WHITE)
        surface.blit(hud_text, (GRID_OFFSET_X, 20))

        # Wave complete overlay
        if self.state == 'wave_complete':
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
            big_font = pygame.font.Font(None, 72)
            text = big_font.render(f'Wave {self.wave} Complete!', True, GREEN)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(text, rect)

        # Game over overlay
        if self.state == 'game_over':
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))
            big_font = pygame.font.Font(None, 72)
            text = big_font.render('GAME OVER', True, RED)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(text, rect)
            sub_font = pygame.font.Font(None, 36)
            sub_text = sub_font.render(f'Waves: {self.wave} | Kills: {self.kills}', True, WHITE)
            sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            surface.blit(sub_text, sub_rect)

        # Victory overlay
        if self.state == 'victory':
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
            big_font = pygame.font.Font(None, 72)
            text = big_font.render('VICTORY!', True, YELLOW)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(text, rect)
            sub_font = pygame.font.Font(None, 36)
            sub_text = sub_font.render(f'All 10 Waves Cleared! | Kills: {self.kills}', True, WHITE)
            sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            surface.blit(sub_text, sub_rect)
