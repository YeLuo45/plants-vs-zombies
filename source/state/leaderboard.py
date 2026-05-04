import pygame
import json
import os
from source.constants import *

SCORES_FILE = os.path.expanduser('~/.pvz_endless_scores.json')


class LeaderboardManager:
    _instance = None

    def __init__(self):
        if LeaderboardManager._instance is not None:
            return
        LeaderboardManager._instance = self
        self.scores = self._load()

    @staticmethod
    def get_instance():
        if LeaderboardManager._instance is None:
            LeaderboardManager()
        return LeaderboardManager._instance

    def _load(self):
        if os.path.exists(SCORES_FILE):
            try:
                with open(SCORES_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save(self):
        try:
            with open(SCORES_FILE, 'w') as f:
                json.dump(self.scores, f, indent=2)
        except IOError:
            pass

    def add_score(self, wave_index, kills, plants_placed, elapsed_seconds):
        entry = {
            'wave': wave_index,
            'kills': kills,
            'plants': plants_placed,
            'time': elapsed_seconds,
        }
        self.scores.append(entry)
        self.scores.sort(key=lambda x: x['wave'], reverse=True)
        self.scores = self.scores[:10]  # keep top 10
        self._save()

    def is_new_record(self, wave_index):
        if not self.scores:
            return True
        return wave_index > self.scores[0]['wave']

    def get_scores(self):
        return self.scores[:10]

    def get_top_wave(self):
        if not self.scores:
            return 0
        return self.scores[0]['wave']

    def draw(self, surface):
        """Draw leaderboard overlay on the given surface."""
        # Semi-transparent background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Title
        font_title = pygame.font.Font(None, 60)
        title_surf = font_title.render('ENDLESS MODE RECORDS', True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 60))
        surface.blit(title_surf, title_rect)

        # Close button (X) top-right of leaderboard panel
        close_btn = pygame.Rect(SCREEN_WIDTH // 2 + 195, 50, 35, 35)
        pygame.draw.rect(surface, (80, 30, 30), close_btn)
        pygame.draw.rect(surface, (200, 60, 60), close_btn, 2)
        font_x = pygame.font.Font(None, 28)
        x_surf = font_x.render('X', True, (255, 100, 100))
        x_rect = x_surf.get_rect(center=close_btn.center)
        surface.blit(x_surf, x_rect)
        self._close_btn_rect = close_btn

        # Column headers
        font_head = pygame.font.Font(None, 28)
        headers = ['#', 'Wave', 'Kills', 'Plants', 'Time']
        col_xs = [SCREEN_WIDTH // 2 - 200, SCREEN_WIDTH // 2 - 150,
                  SCREEN_WIDTH // 2 - 50, SCREEN_WIDTH // 2 + 50, SCREEN_WIDTH // 2 + 130]
        for i, (hdr, cx) in enumerate(zip(headers, col_xs)):
            surf = font_head.render(hdr, True, (180, 180, 180))
            r = surf.get_rect(center=(cx, 110))
            surface.blit(surf, r)

        # Divider line
        pygame.draw.line(surface, (100, 100, 100), (SCREEN_WIDTH // 2 - 230, 125),
                         (SCREEN_WIDTH // 2 + 230, 125))

        # Score rows
        font_row = pygame.font.Font(None, 32)
        scores = self.get_scores()
        if not scores:
            none_surf = font_row.render('No records yet. Be the first!', True, (150, 150, 150))
            none_rect = none_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
            surface.blit(none_surf, none_rect)
        else:
            for i, entry in enumerate(scores):
                y = 145 + i * 38
                bg_color = (30, 30, 30) if i % 2 == 0 else (20, 20, 20)
                pygame.draw.rect(surface, bg_color, (SCREEN_WIDTH // 2 - 230, y - 14, 460, 34))

                mins = int(entry['time'] // 60)
                secs = int(entry['time'] % 60)
                time_str = f'{mins}:{secs:02d}'
                row_data = [str(i + 1), f"#{entry['wave']}", str(entry['kills']),
                             str(entry['plants']), time_str]
                for j, (val, cx) in enumerate(zip(row_data, col_xs)):
                    color = (255, 215, 0) if i == 0 else WHITE
                    surf = font_row.render(val, True, color)
                    r = surf.get_rect(center=(cx, y + 5))
                    surface.blit(surf, r)

        # Close hint
        font_hint = pygame.font.Font(None, 24)
        hint_surf = font_hint.render('Click X or anywhere to close', True, (120, 120, 120))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
        surface.blit(hint_surf, hint_rect)

    def handle_click(self, mx, my):
        """Returns True if leaderboard should dismiss."""
        if hasattr(self, '_close_btn_rect') and self._close_btn_rect.collidepoint(mx, my):
            return True
        lb_rect = pygame.Rect(SCREEN_WIDTH // 2 - 230, 50, 460, SCREEN_HEIGHT - 100)
        if lb_rect.collidepoint(mx, my):
            return True
        return False
