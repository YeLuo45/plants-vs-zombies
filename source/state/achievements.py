import pygame
import json
import os

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
]

DATA_DIR = os.path.expanduser('~/.hermes/prj-plants-vs-zombies')
DATA_FILE = os.path.join(DATA_DIR, 'achievements.json')


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
