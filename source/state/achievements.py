import pygame
import json
import os
import time as time_module
from source.constants import SCREEN_WIDTH, SCREEN_HEIGHT

# Achievement definitions
ACHIEVEMENTS = [
    {'id': 'first_blood',      'name': 'First Blood',         'desc': 'Kill your first zombie',            'condition': 'Kill 1 zombie'},
    {'id': 'zombie_slayer',   'name': 'Zombie Slayer',        'desc': 'Kill 50 zombies',                  'condition': 'Kill 50 zombies'},
    {'id': 'zombie_horde',     'name': 'Zombie Horde',         'desc': 'Kill 100 zombies',                  'condition': 'Kill 100 zombies'},
    {'id': 'first_win',        'name': 'First Victory',        'desc': 'Complete a level for the first time','condition': 'Win 1 level'},
    {'id': 'peaceful_garden',  'name': 'Peaceful Garden',      'desc': 'Win without losing a single plant',  'condition': 'Win with 0 plants lost'},
    {'id': 'sun_collector',    'name': 'Sun Collector',        'desc': 'Collect 1000 sun total',            'condition': 'Collect 1000 sun'},
    {'id': 'squash_crush',     'name': 'Squash Crush',         'desc': 'Kill a zombie with Squash',          'condition': 'Squash kills 1 zombie'},
    {'id': 'winter_freeze',    'name': 'Winter Freeze',        'desc': 'Freeze 10 zombies with Ice Shroom', 'condition': 'Freeze 10 zombies'},
    {'id': 'hypnotist',        'name': 'Hypnotist',             'desc': 'Hypnotize a zombie',               'condition': 'Use Hypno Shroom'},
    {'id': 'scaredy_producer', 'name': 'Shy Producer',         'desc': 'Have Scaredy Shroom produce 50 sun','condition': 'Scaredy produces 50 sun'},
    {'id': 'bowling_nut',      'name': 'Bowling Champion',      'desc': 'Complete Lawn Bowling mode',         'condition': 'Win bowling mode'},
    {'id': 'survival_5',       'name': 'Survivor',              'desc': 'Survive 5 waves in Endless mode',   'condition': 'Survive 5 waves endless'},
    {'id': 'zen_master',       'name': 'Zen Master',            'desc': 'Place 10 plants in Zen Garden',      'condition': 'Place 10 plants in Zen'},
    {'id': 'green_thumb',      'name': 'Green Thumb',           'desc': 'Water 10 plants in Zen Garden',      'condition': 'Water 10 plants in Zen'},
    {'id': 'golden_garden',    'name': 'Golden Garden',         'desc': 'Place 20 Marigolds in Zen Garden',   'condition': 'Place 20 Marigolds in Zen'},
    {'id': 'magnetized',       'name': 'Magnetized',             'desc': 'Collect 500 sun with Gold Magnets',  'condition': 'Collect 500 sun with Gold Magnets'},
]

DATA_DIR = os.path.expanduser('~/.hermes/prj-plants-vs-zombies')
DATA_FILE = os.path.join(DATA_DIR, 'achievements.json')

STATS_FILE = os.path.join(DATA_DIR, 'stats.json')

# --------------------------------------------------------------------
# StatsManager (singleton)
# --------------------------------------------------------------------
class StatsManager:
    _instance = None

    def __init__(self):
        if StatsManager._instance is not None:
            return
        StatsManager._instance = self
        self.total_play_seconds = 0.0
        self.games_won = 0
        self.games_lost = 0
        self.plants_planted = 0
        self._load()

    @staticmethod
    def get_instance():
        if StatsManager._instance is None:
            StatsManager()
        return StatsManager._instance

    def _load(self):
        if not os.path.exists(STATS_FILE):
            return
        try:
            with open(STATS_FILE, 'r') as f:
                data = json.load(f)
            self.total_play_seconds = data.get('total_play_seconds', 0.0)
            self.games_won = data.get('games_won', 0)
            self.games_lost = data.get('games_lost', 0)
            self.plants_planted = data.get('plants_planted', 0)
        except Exception:
            pass

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {
            'total_play_seconds': self.total_play_seconds,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'plants_planted': self.plants_planted,
        }
        with open(STATS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def add_play_time(self, seconds):
        self.total_play_seconds += seconds
        # Save at most every 10 seconds
        if not hasattr(self, '_last_save_time') or time_module.time() - self._last_save_time > 10:
            self.save()
            self._last_save_time = time_module.time()

    def on_game_won(self):
        self.games_won += 1
        self.save()

    def on_game_lost(self):
        self.games_lost += 1
        self.save()

    def on_plant_placed(self):
        self.plants_planted += 1

    def format_play_time(self):
        secs = int(self.total_play_seconds)
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        return f'{h:02d}:{m:02d}:{s:02d}'


# --------------------------------------------------------------------
# AchievementPanel UI
# --------------------------------------------------------------------
class AchievementPanel:
    ICON_COLORS = [
        (255, 215, 0), (100, 200, 100), (100, 150, 255),
        (255, 150, 100), (200, 100, 255), (100, 255, 200),
        (255, 100, 150), (150, 200, 100), (200, 150, 100),
        (150, 100, 200), (255, 200, 100), (100, 200, 150), (200, 200, 100),
    ]

    def __init__(self, ach_manager):
        self.ach = ach_manager
        self.scroll_offset = 0
        self.max_scroll = 0
        # Panel dimensions
        self.panel_w = 600
        self.panel_h = 500
        self.panel_x = SCREEN_WIDTH // 2 - self.panel_w // 2
        self.panel_y = SCREEN_HEIGHT // 2 - self.panel_h // 2
        # Close button
        self.close_btn = pygame.Rect(self.panel_x + self.panel_w - 40, self.panel_y + 5, 35, 35)
        # Grid: 2 columns
        self.col_width = (self.panel_w - 40) // 2
        self.row_h = 70
        self.margin_x = 20
        self.margin_y = 50
        self._recalc_max_scroll()

    def _recalc_max_scroll(self):
        ach_list = list(self.ach.achievements.values())
        n = len(ach_list)
        rows_needed = (n + 1) // 2
        total_content_h = self.margin_y + rows_needed * self.row_h + 40
        self.max_scroll = max(0, total_content_h - self.panel_h)

    def draw(self, surface):
        # Semi-transparent overlay backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Panel background
        bg = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        bg.fill((25, 30, 25, 245))
        surface.blit(bg, (self.panel_x, self.panel_y))
        pygame.draw.rect(surface, (80, 200, 80), (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2)

        # Title
        font_title = pygame.font.Font(None, 42)
        title_surf = font_title.render('ACHIEVEMENTS', True, (100, 255, 100))
        surface.blit(title_surf, (self.panel_x + self.panel_w // 2 - title_surf.get_width() // 2, self.panel_y + 10))

        # Close button (X)
        pygame.draw.rect(surface, (80, 30, 30), self.close_btn)
        pygame.draw.rect(surface, (200, 80, 80), self.close_btn, 2)
        font_x = pygame.font.Font(None, 28)
        x_surf = font_x.render('X', True, (255, 100, 100))
        x_rect = x_surf.get_rect(center=self.close_btn.center)
        surface.blit(x_surf, x_rect)

        # Achievements in 2-column grid
        font_name = pygame.font.Font(None, 22)
        font_desc = pygame.font.Font(None, 16)
        font_time = pygame.font.Font(None, 14)
        font_star = pygame.font.Font(None, 24)

        ach_list = list(self.ach.achievements.values())
        for idx, a in enumerate(ach_list):
            col = idx % 2
            row = idx // 2
            ax = self.panel_x + self.margin_x + col * self.col_width
            ay = self.panel_y + self.margin_y + row * self.row_h - self.scroll_offset

            # Skip if outside visible panel area
            if ay + self.row_h < self.panel_y or ay > self.panel_y + self.panel_h:
                continue

            unlocked = a['unlocked']
            icon_color = self.ICON_COLORS[idx % len(self.ICON_COLORS)]

            # Icon rectangle
            icon_rect = pygame.Rect(ax, ay + 5, 36, 36)
            pygame.draw.rect(surface, icon_color if unlocked else (60, 60, 60), icon_rect)
            pygame.draw.rect(surface, (200, 200, 100) if unlocked else (80, 80, 80), icon_rect, 1)

            # Star
            star = '★' if unlocked else '☆'
            star_color = (255, 215, 0) if unlocked else (80, 80, 80)
            star_surf = font_star.render(star, True, star_color)
            surface.blit(star_surf, (ax + 40, ay + 2))

            # Name
            name_color = (255, 215, 0) if unlocked else (120, 120, 120)
            name_surf = font_name.render(a['name'], True, name_color)
            surface.blit(name_surf, (ax + 60, ay + 2))

            # Description
            desc_color = (180, 180, 180) if unlocked else (90, 90, 90)
            desc_surf = font_desc.render(a['desc'], True, desc_color)
            surface.blit(desc_surf, (ax + 60, ay + 22))

            # Unlock timestamp
            if unlocked and a.get('unlock_time'):
                time_surf = font_time.render(a['unlock_time'], True, (130, 130, 80))
                surface.blit(time_surf, (ax + 60, ay + 40))
            elif not unlocked:
                cond_surf = font_time.render(f'[{a["condition"]}]', True, (70, 70, 70))
                surface.blit(cond_surf, (ax + 60, ay + 40))

        # Scroll bar (if needed)
        if self.max_scroll > 0:
            bar_h = max(20, int(40 * (self.panel_h / (self.max_scroll + self.panel_h))))
            bar_y = self.panel_y + 50 + int((self.scroll_offset / self.max_scroll) * (self.panel_h - 50 - bar_h - 10))
            pygame.draw.rect(surface, (60, 60, 60), (self.panel_x + self.panel_w - 12, bar_y, 8, bar_h))
            pygame.draw.rect(surface, (100, 200, 100), (self.panel_x + self.panel_w - 12, bar_y, 8, bar_h), 1)

        # Bottom hint
        font_hint = pygame.font.Font(None, 20)
        hint_surf = font_hint.render('Scroll: W/S or Arrow Keys   |   Close: ESC or X', True, (100, 100, 100))
        surface.blit(hint_surf, (self.panel_x + self.panel_w // 2 - hint_surf.get_width() // 2, self.panel_y + self.panel_h - 22))

    def handle_click(self, mx, my):
        if self.close_btn.collidepoint(mx, my):
            return 'close'
        # Scroll with click on scrollbar
        if self.max_scroll > 0:
            bar_area = pygame.Rect(self.panel_x + self.panel_w - 12, self.panel_y + 50, 12, self.panel_h - 50)
            if bar_area.collidepoint(mx, my):
                rel_y = my - (self.panel_y + 50)
                frac = rel_y / (self.panel_h - 50)
                self.scroll_offset = int(frac * self.max_scroll)
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset))
        return None

    def handle_key(self, key):
        if key == pygame.K_w or key == pygame.K_UP:
            self.scroll_offset = max(0, self.scroll_offset - 30)
        elif key == pygame.K_s or key == pygame.K_DOWN:
            self.scroll_offset = min(self.max_scroll, self.scroll_offset + 30)


# --------------------------------------------------------------------
# StatsPanel UI
# --------------------------------------------------------------------
class StatsPanel:
    def __init__(self, ach_manager, stats_manager):
        self.ach = ach_manager
        self.stats = stats_manager
        self.panel_w = 480
        self.panel_h = 400
        self.panel_x = SCREEN_WIDTH // 2 - self.panel_w // 2
        self.panel_y = SCREEN_HEIGHT // 2 - self.panel_h // 2
        self.close_btn = pygame.Rect(self.panel_x + self.panel_w - 40, self.panel_y + 5, 35, 35)

    def draw(self, surface):
        # Backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Panel
        bg = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        bg.fill((20, 25, 20, 245))
        surface.blit(bg, (self.panel_x, self.panel_y))
        pygame.draw.rect(surface, (80, 160, 200), (self.panel_x, self.panel_y, self.panel_w, self.panel_h), 2)

        # Title
        font_title = pygame.font.Font(None, 42)
        title_surf = font_title.render('PLAYER STATS', True, (100, 180, 255))
        surface.blit(title_surf, (self.panel_x + self.panel_w // 2 - title_surf.get_width() // 2, self.panel_y + 10))

        # Close button
        pygame.draw.rect(surface, (80, 30, 30), self.close_btn)
        pygame.draw.rect(surface, (200, 80, 80), self.close_btn, 2)
        font_x = pygame.font.Font(None, 28)
        x_surf = font_x.render('X', True, (255, 100, 100))
        x_rect = x_surf.get_rect(center=self.close_btn.center)
        surface.blit(x_surf, x_rect)

        # Build stat rows from AchievementManager stats + StatsManager
        ach_stats = self.ach.stats
        rows = [
            ('Total Play Time',    self.stats.format_play_time()),
            ('Zombies Killed',     str(ach_stats.get('zombies_killed', 0))),
            ('Plants Planted',     str(self.stats.plants_planted)),
            ('Sun Collected',      str(ach_stats.get('sun_collected', 0))),
            ('Games Won',          str(self.stats.games_won)),
            ('Games Lost',         str(self.stats.games_lost)),
            ('Zombies Frozen',      str(ach_stats.get('zombies_frozen', 0))),
            ('Sun from Scaredy',   str(ach_stats.get('sun_from_scaredy', 0))),
            ('Squash Kills',       str(ach_stats.get('squash_kills', 0))),
            ('Hypno Uses',         str(ach_stats.get('hypno_uses', 0))),
            ('Zen Plants Watered', str(ach_stats.get('zen_plants_watered', 0))),
            ('Marigolds Placed',   str(ach_stats.get('marigolds_placed', 0))),
            ('Sun from Magnets',   str(ach_stats.get('sun_from_magnet', 0))),
            ('Achievements',       f'{self.ach.count_unlocked()}/{len(self.ach.achievements)}'),
        ]

        font_label = pygame.font.Font(None, 26)
        font_value = pygame.font.Font(None, 26)
        font_div = pygame.font.Font(None, 18)

        y = self.panel_y + 55
        row_h = 30
        for label, value in rows:
            # Alternating row bg
            bg_row = pygame.Rect(self.panel_x + 15, y - 4, self.panel_w - 30, row_h)
            pygame.draw.rect(surface, (30, 35, 30), bg_row)

            label_surf = font_label.render(label + ':', True, (160, 160, 160))
            surface.blit(label_surf, (self.panel_x + 25, y))

            value_surf = font_value.render(value, True, (220, 220, 100))
            surface.blit(value_surf, (self.panel_x + self.panel_w - 25 - value_surf.get_width(), y))

            y += row_h
            # Divider
            pygame.draw.line(surface, (50, 55, 50), (self.panel_x + 15, y - 2),
                             (self.panel_x + self.panel_w - 15, y - 2))

        # Bottom hint
        font_hint = pygame.font.Font(None, 20)
        hint_surf = font_hint.render('Press ESC or click X to close', True, (100, 100, 100))
        surface.blit(hint_surf, (self.panel_x + self.panel_w // 2 - hint_surf.get_width() // 2,
                                  self.panel_y + self.panel_h - 22))

    def handle_click(self, mx, my):
        if self.close_btn.collidepoint(mx, my):
            return 'close'
        return None


class AchievementManager:
    _instance = None

    def __init__(self):
        if AchievementManager._instance is not None:
            return
        AchievementManager._instance = self

        self.achievements = {}
        for a in ACHIEVEMENTS:
            self.achievements[a['id']] = {
                'id': a['id'],
                'name': a['name'],
                'desc': a['desc'],
                'condition': a['condition'],
                'unlocked': False,
                'unlock_time': None,
            }

        self.newly_unlocked = []  # IDs unlocked this session (for notification)
        self.stats = {
            'zombies_killed': 0,
            'zombies_frozen': 0,
            'sun_collected': 0,
            'sun_from_scaredy': 0,
            'squash_kills': 0,
            'hypno_uses': 0,
            'zen_plants_watered': 0,
            'marigolds_placed': 0,
            'sun_from_magnet': 0,
        }

        self._load()

    @staticmethod
    def get_instance():
        if AchievementManager._instance is None:
            AchievementManager()
        return AchievementManager._instance

    def _load(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            if 'achievements' in data:
                for k, v in data['achievements'].items():
                    if k in self.achievements:
                        self.achievements[k]['unlocked'] = v.get('unlocked', False)
                        self.achievements[k]['unlock_time'] = v.get('unlock_time')
            if 'stats' in data:
                self.stats.update(data['stats'])
        except Exception:
            pass

    def save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        data = {
            'achievements': {k: {'unlocked': v['unlocked'], 'unlock_time': v.get('unlock_time')}
                             for k, v in self.achievements.items()},
            'stats': self.stats,
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def unlock(self, achievement_id):
        a = self.achievements.get(achievement_id)
        if a is None:
            return False
        if a['unlocked']:
            return False
        a['unlocked'] = True
        import time
        a['unlock_time'] = time.strftime('%Y-%m-%d %H:%M')
        self.newly_unlocked.append(achievement_id)
        self.save()
        return True

    def is_unlocked(self, achievement_id):
        return self.achievements.get(achievement_id, {}).get('unlocked', False)

    def count_unlocked(self):
        return sum(1 for a in self.achievements.values() if a['unlocked'])

    def on_zombie_killed(self, zombie_type=None, killed_by=None):
        self.stats['zombies_killed'] += 1
        k = self.stats['zombies_killed']
        if k >= 1:
            self.unlock('first_blood')
        if k >= 50:
            self.unlock('zombie_slayer')
        if k >= 100:
            self.unlock('zombie_horde')

        if killed_by == 'squash':
            self.stats['squash_kills'] += 1
            self.unlock('squash_crush')

        if killed_by == 'hypno':
            self.stats['hypno_uses'] += 1
            self.unlock('hypnotist')

    def on_zombie_frozen(self):
        self.stats['zombies_frozen'] += 1
        if self.stats['zombies_frozen'] >= 10:
            self.unlock('winter_freeze')

    def on_sun_collected(self, amount, source=None):
        self.stats['sun_collected'] += amount
        if source == 'scaredy':
            self.stats['sun_from_scaredy'] += amount
            if self.stats['sun_from_scaredy'] >= 50:
                self.unlock('scaredy_producer')
        if self.stats['sun_collected'] >= 1000:
            self.unlock('sun_collector')

    def on_win(self, plants_lost=0):
        self.unlock('first_win')
        if plants_lost == 0:
            self.unlock('peaceful_garden')

    def on_mini_game_win(self, game_type):
        if game_type == 'bowling':
            self.unlock('bowling_nut')
        elif game_type == 'endless':
            pass  # survival_5 triggered separately
        elif game_type == 'zen':
            pass  # zen_master triggered separately

    def on_endless_wave(self, wave_index):
        if wave_index >= 5:
            self.unlock('survival_5')

    def on_zen_plant(self, count):
        if count >= 10:
            self.unlock('zen_master')

    def on_zen_water(self, total_watered):
        self.stats['zen_plants_watered'] = total_watered
        if total_watered >= 10:
            self.unlock('green_thumb')

    def on_marigold_placed(self, total_marigolds):
        self.stats['marigolds_placed'] = total_marigolds
        if total_marigolds >= 20:
            self.unlock('golden_garden')

    def on_magnet_sun(self, total_sun):
        self.stats['sun_from_magnet'] = total_sun
        if total_sun >= 500:
            self.unlock('magnetized')

    def pop_newly_unlocked(self):
        ids = self.newly_unlocked[:]
        self.newly_unlocked = []
        return ids

    def draw_panel(self, surface, offset_x=0, offset_y=0):
        """Draw full achievement panel."""
        ach_list = list(self.achievements.values())
        n = len(ach_list)

        panel_w = 420
        panel_h = min(50 + n * 42, SCREEN_HEIGHT - 40)
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2 + offset_x
        panel_y = SCREEN_HEIGHT // 2 - panel_h // 2 + offset_y

        # Background
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 230))
        surface.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(surface, (80, 200, 80), (panel_x, panel_y, panel_w, panel_h), 2)

        # Title
        font_title = pygame.font.Font(None, 36)
        font_name = pygame.font.Font(None, 24)
        font_desc = pygame.font.Font(None, 18)

        title_surf = font_title.render('ACHIEVEMENTS', True, (100, 255, 100))
        surface.blit(title_surf, (panel_x + panel_w // 2 - title_surf.get_width() // 2, panel_y + 8))

        for i, a in enumerate(ach_list):
            ay = panel_y + 40 + i * 42
            if ay + 40 > panel_y + panel_h:
                break

            # Star icon
            star = '★' if a['unlocked'] else '☆'
            star_color = (255, 215, 0) if a['unlocked'] else (80, 80, 80)
            star_surf = font_name.render(star, True, star_color)
            surface.blit(star_surf, (panel_x + 10, ay))

            # Name
            name_color = (100, 255, 100) if a['unlocked'] else (120, 120, 120)
            name_surf = font_name.render(a['name'], True, name_color)
            surface.blit(name_surf, (panel_x + 35, ay))

            # Description
            desc_surf = font_desc.render(a['desc'], True, (160, 160, 160))
            surface.blit(desc_surf, (panel_x + 35, ay + 20))

        # Close hint
        hint = font_desc.render('Press ESC or click to close', True, (100, 100, 100))
        surface.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 20))

    def draw_badge(self, surface):
        """Draw small badge in top-right corner showing N/13 unlocked."""
        count = self.count_unlocked()
        total = len(self.achievements)
        font = pygame.font.Font(None, 20)

        badge_w = 130
        badge_h = 26
        badge_x = SCREEN_WIDTH - badge_w - 8
        badge_y = 8

        pygame.draw.rect(surface, (40, 40, 40), (badge_x, badge_y, badge_w, badge_h))
        pygame.draw.rect(surface, (80, 200, 80), (badge_x, badge_y, badge_w, badge_h), 1)

        text = f'Achievements: {count}/{total}'
        t_surf = font.render(text, True, (100, 255, 100))
        surface.blit(t_surf, (badge_x + 8, badge_y + 5))
