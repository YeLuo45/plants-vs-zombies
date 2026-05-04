import pygame
import json
import os
from source.constants import *

SAVE_DIR = os.path.expanduser('~/.hermes/prj-plants-vs-zombies/saves')
SETTINGS_FILE = os.path.expanduser('~/.hermes/prj-plants-vs-zombies/settings.json')


class SaveManager:
    _instance = None

    def __init__(self):
        if SaveManager._instance is not None:
            return
        SaveManager._instance = self
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.slots = self._list_slots()
        self._load_settings()

    @staticmethod
    def get_instance():
        if SaveManager._instance is None:
            SaveManager()
        return SaveManager._instance

    def _list_slots(self):
        slots = {}
        for i in range(1, 4):
            path = os.path.join(SAVE_DIR, f'slot{i}.json')
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    slots[i] = {
                        'mode': data.get('mode', 'adventure'),
                        'wave': data.get('wave_index', 0),
                        'sun': data.get('sun', 150),
                        'plants_placed': data.get('plants_placed', 0),
                        'zombies_killed': data.get('zombies_killed', 0),
                        'time_str': data.get('time_str', ''),
                        'timestamp': os.path.getmtime(path),
                    }
                except Exception:
                    slots[i] = None
            else:
                slots[i] = None
        return slots

    def has_save(self):
        return any(s is not None for s in self.slots.values())

    def get_latest_slot(self):
        """Return slot number with most recent save, or None."""
        best = None
        best_time = 0
        for i, s in self.slots.items():
            if s and s.get('timestamp', 0) > best_time:
                best_time = s['timestamp']
                best = i
        return best

    def save(self, slot, level_state, mode='adventure'):
        path = os.path.join(SAVE_DIR, f'slot{slot}.json')
        import time as ti_module
        data = {
            'mode': mode,
            'wave_index': level_state.wave_index,
            'wave_active': level_state.wave_active,
            'pre_wave_timer': level_state.pre_wave_timer,
            'sun': level_state.menubar.sun,
            'cooldowns': {k: level_state.menubar.cooldowns.get(k, 0) for k in PLANTS},
            'plants_placed': level_state.plants_placed,
            'zombies_killed': level_state.zombies_killed,
            'total_waves': level_state.total_waves,
            'grid': self._serialize_grid(level_state.grid),
            'zombies': self._serialize_zombies(level_state.zombies),
            'mowers': [
                {'activated': m.activated, 'x': m.x, 'alive': m.alive}
                for m in level_state.menubar.get('mowers', []) if hasattr(level_state.menubar, 'mowers')
            ],
            'time_str': ti_module.strftime('%Y-%m-%d %H:%M'),
        }

        # Endless-specific
        if mode == 'endless' and hasattr(level_state, 'hp_multiplier'):
            data['hp_multiplier'] = level_state.hp_multiplier

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        self.slots = self._list_slots()

    def _serialize_grid(self, grid):
        cells = {}
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = grid.cells[r][c]
                if p:
                    cells[f'{r},{c}'] = {
                        'name': p.name,
                        'hp': p.hp,
                        'row': p.row,
                        'col': p.col,
                        # Plant-specific state
                        'cooldown_timer': getattr(p, 'cooldown_timer', 0),
                        'shoot_timer': getattr(p, 'shoot_timer', 0),
                        'sun_timer': getattr(p, 'sun_timer', 0),
                        'eat_timer': getattr(p, 'eat_timer', 0),
                        'eating': getattr(p, 'eating', False),
                        'eaten': getattr(p, 'eaten', False),
                        'armed': getattr(p, 'armed', False),
                        'flash_timer': getattr(p, 'flash_timer', 0),
                        'squash_state': getattr(p, 'squash_state', 'idle'),
                        'hypno_active': getattr(p, 'hypno_active', False),
                        'laddered': getattr(p, 'laddered', False),
                        'scared_hidden': getattr(p, 'scared_hidden', False),
                        'scared_timer': getattr(p, 'scared_timer', 0),
                    }
        return cells

    def _serialize_zombies(self, zombies):
        zlist = []
        for z in zombies:
            if z.dead:
                continue
            zlist.append({
                'name': z.name,
                'row': z.row,
                'x': z.x,
                'hp': z.hp,
                'newspaper_destroyed': getattr(z, 'newspaper_destroyed', False),
                'miner_phase': getattr(z, 'miner_phase', None),
                'pole_jumped': getattr(z, 'pole_jumped', False),
                'has_ladder': getattr(z, 'has_ladder', False),
                'ladder_placed_plant': None,
            })
        return zlist

    def load(self, slot):
        path = os.path.join(SAVE_DIR, f'slot{slot}.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return json.load(f)

    def delete(self, slot):
        path = os.path.join(SAVE_DIR, f'slot{slot}.json')
        if os.path.exists(path):
            os.remove(path)
        self.slots = self._list_slots()

    # ========== Settings ==========
    def _load_settings(self):
        self.settings = {
            'music_volume': 0.7,
            'sfx_volume': 0.8,
            'game_speed': 1.0,
            'fullscreen': False,
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    self.settings.update(json.load(f))
            except Exception:
                pass

    def save_settings(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def get_settings(self):
        return dict(self.settings)


class SettingsState:
    """In-game settings overlay panel."""

    def __init__(self, screen):
        self.screen = screen
        self.sm = SaveManager.get_instance()
        self.settings = self.sm.get_settings()
        self._build_slider_rects()
        self.dirty = False

    def _build_slider_rects(self):
        panel_w = 360
        panel_h = 320
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - panel_h // 2
        self.panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        # Music slider
        self.music_rect = pygame.Rect(px + 30, py + 65, 200, 20)
        # SFX slider
        self.sfx_rect = pygame.Rect(px + 30, py + 130, 200, 20)
        # Speed buttons
        self.speed_btn_075 = pygame.Rect(px + 30, py + 195, 60, 35)
        self.speed_btn_100 = pygame.Rect(px + 100, py + 195, 60, 35)
        self.speed_btn_200 = pygame.Rect(px + 170, py + 195, 60, 35)
        # Fullscreen toggle
        self.fs_btn = pygame.Rect(px + 30, py + 250, 120, 40)
        # Back button
        self.back_btn = pygame.Rect(px + panel_w // 2 - 70, py + panel_h - 55, 140, 45)

    def handle_click(self, mx, my):
        # Music slider
        if self.music_rect.collidepoint(mx, my):
            val = (mx - self.music_rect.x) / self.music_rect.width
            val = max(0, min(1, val))
            self.settings['music_volume'] = round(val, 2)
            self.sm.set('music_volume', self.settings['music_volume'])
            return 'changed'
        # SFX slider
        if self.sfx_rect.collidepoint(mx, my):
            val = (mx - self.sfx_rect.x) / self.sfx_rect.width
            val = max(0, min(1, val))
            self.settings['sfx_volume'] = round(val, 2)
            self.sm.set('sfx_volume', self.settings['sfx_volume'])
            return 'changed'
        # Speed buttons
        if self.speed_btn_075.collidepoint(mx, my):
            self.settings['game_speed'] = 0.75
            self.sm.set('game_speed', 0.75)
            return 'changed'
        if self.speed_btn_100.collidepoint(mx, my):
            self.settings['game_speed'] = 1.0
            self.sm.set('game_speed', 1.0)
            return 'changed'
        if self.speed_btn_200.collidepoint(mx, my):
            self.settings['game_speed'] = 2.0
            self.sm.set('game_speed', 2.0)
            return 'changed'
        # Fullscreen
        if self.fs_btn.collidepoint(mx, my):
            self.settings['fullscreen'] = not self.settings['fullscreen']
            self.sm.set('fullscreen', self.settings['fullscreen'])
            return 'fullscreen_toggle'
        # Back
        if self.back_btn.collidepoint(mx, my):
            return 'back'
        return None

    def draw(self, surface):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Panel bg
        bg = pygame.Surface((self.panel_rect.w, self.panel_rect.h), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 245))
        surface.blit(bg, self.panel_rect.topleft)
        pygame.draw.rect(surface, (100, 100, 100), self.panel_rect, 2)

        font_title = pygame.font.Font(None, 40)
        font_label = pygame.font.Font(None, 28)
        font_value = pygame.font.Font(None, 24)
        font_btn = pygame.font.Font(None, 32)

        # Title
        t = font_title.render('SETTINGS', True, (200, 200, 200))
        surface.blit(t, (self.panel_rect.centerx - t.get_width() // 2, self.panel_rect.top + 12))

        mx, my = pygame.mouse.get_pos()

        # Music volume
        label = font_label.render('Music Volume', True, (180, 180, 180))
        surface.blit(label, (self.panel_rect.left + 30, self.panel_rect.top + 38))
        val = self.settings['music_volume']
        pygame.draw.rect(surface, (60, 60, 60), self.music_rect)
        pygame.draw.rect(surface, (80, 200, 80), (self.music_rect.x, self.music_rect.y,
                  int(self.music_rect.width * val), self.music_rect.height))
        pygame.draw.rect(surface, (150, 150, 150), self.music_rect, 1)
        pct = font_value.render(f'{int(val * 100)}%', True, (150, 150, 150))
        surface.blit(pct, (self.music_rect.right + 10, self.music_rect.y))

        # SFX volume
        label = font_label.render('Sound Effects', True, (180, 180, 180))
        surface.blit(label, (self.panel_rect.left + 30, self.panel_rect.top + 100))
        val = self.settings['sfx_volume']
        pygame.draw.rect(surface, (60, 60, 60), self.sfx_rect)
        pygame.draw.rect(surface, (80, 200, 80), (self.sfx_rect.x, self.sfx_rect.y,
                  int(self.sfx_rect.width * val), self.sfx_rect.height))
        pygame.draw.rect(surface, (150, 150, 150), self.sfx_rect, 1)
        pct = font_value.render(f'{int(val * 100)}%', True, (150, 150, 150))
        surface.blit(pct, (self.sfx_rect.right + 10, self.sfx_rect.y))

        # Game speed
        label = font_label.render('Game Speed', True, (180, 180, 180))
        surface.blit(label, (self.panel_rect.left + 30, self.panel_rect.top + 165))
        speed = self.settings['game_speed']
        for btn, label_text, speed_val in [
            (self.speed_btn_075, '0.75x', 0.75),
            (self.speed_btn_100, '1x', 1.0),
            (self.speed_btn_200, '2x', 2.0),
        ]:
            hover = btn.collidepoint(mx, my)
            bg = (80, 160, 80) if speed == speed_val else ((60, 120, 60) if hover else (50, 100, 50))
            pygame.draw.rect(surface, bg, btn)
            pygame.draw.rect(surface, (150, 255, 150), btn, 1)
            t = font_btn.render(label_text, True, WHITE)
            surface.blit(t, t.get_rect(center=btn.center))

        # Fullscreen
        fs = self.settings['fullscreen']
        hover = self.fs_btn.collidepoint(mx, my)
        bg = (80, 160, 80) if fs else ((60, 120, 60) if hover else (50, 100, 50))
        pygame.draw.rect(surface, bg, self.fs_btn)
        pygame.draw.rect(surface, (150, 255, 150), self.fs_btn, 1)
        t = font_btn.render('Fullscreen' if fs else 'Windowed', True, WHITE)
        surface.blit(t, t.get_rect(center=self.fs_btn.center))

        # Back button
        hover = self.back_btn.collidepoint(mx, my)
        bg = (80, 160, 80) if hover else (50, 120, 50)
        pygame.draw.rect(surface, bg, self.back_btn)
        pygame.draw.rect(surface, (150, 255, 150), self.back_btn, 2)
        t = font_btn.render('Back', True, WHITE)
        surface.blit(t, t.get_rect(center=self.back_btn.center))


class LoadScreen:
    """Save/Load slot selection screen."""

    def __init__(self, screen, sm):
        self.screen = screen
        self.sm = sm
        self.slots = sm.slots
        self.slot_btns = []
        self.delete_btns = []
        self.back_btn = None
        self._build_rects()
        self.selected_slot = None
        self.confirm_delete = None

    def _build_rects(self):
        panel_w = 420
        panel_h = 300
        px = SCREEN_WIDTH // 2 - panel_w // 2
        py = SCREEN_HEIGHT // 2 - panel_h // 2
        self.panel_rect = pygame.Rect(px, py, panel_w, panel_h)

        self.slot_btns = []
        self.delete_btns = []
        for i in range(1, 4):
            ry = py + 30 + (i - 1) * 80
            self.slot_btns.append(pygame.Rect(px + 20, ry, 280, 60))
            self.delete_btns.append(pygame.Rect(px + 310, ry + 15, 80, 30))

        self.back_btn = pygame.Rect(px + panel_w // 2 - 70, py + panel_h - 55, 140, 45)

    def handle_click(self, mx, my):
        if self.confirm_delete is not None:
            # Confirm/cancel delete dialog
            if self.confirm_delete == 'yes':
                self.sm.delete(self.confirm_slot)
                self.slots = self.sm.slots
                self._build_rects()
            self.confirm_delete = None
            self.confirm_slot = None
            return None

        for i, btn in enumerate(self.slot_btns, 1):
            if btn.collidepoint(mx, my):
                if self.slots.get(i) is not None:
                    return i
        for i, btn in enumerate(self.delete_btns, 1):
            if btn.collidepoint(mx, my):
                if self.slots.get(i) is not None:
                    self.confirm_delete = 'yes'
                    self.confirm_slot = i
                    return 'confirm_delete'
        if self.back_btn.collidepoint(mx, my):
            return 'back'
        return None

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        bg = pygame.Surface((self.panel_rect.w, self.panel_rect.h), pygame.SRCALPHA)
        bg.fill((30, 30, 30, 245))
        surface.blit(bg, self.panel_rect.topleft)
        pygame.draw.rect(surface, (100, 100, 100), self.panel_rect, 2)

        font_title = pygame.font.Font(None, 40)
        font_slot = pygame.font.Font(None, 28)
        font_label = pygame.font.Font(None, 22)
        font_btn = pygame.font.Font(None, 30)

        t = font_title.render('LOAD GAME', True, (200, 200, 200))
        surface.blit(t, (self.panel_rect.centerx - t.get_width() // 2, self.panel_rect.top + 8))

        mx, my = pygame.mouse.get_pos()

        for i in range(1, 4):
            idx = i - 1
            btn = self.slot_btns[idx]
            db = self.delete_btns[idx]
            slot = self.slots.get(i)

            hover = btn.collidepoint(mx, my)
            if slot:
                pygame.draw.rect(surface, (60, 100, 60) if hover else (50, 90, 50), btn)
                pygame.draw.rect(surface, (150, 255, 150), btn, 1)
                mode_name = {'adventure': 'Adventure', 'endless': 'Endless', 'zen': 'Zen', 'bowling': 'Bowling'}.get(slot.get('mode', ''), '?')
                lines = [
                    f"Slot {i} — {mode_name}  Wave {slot.get('wave', 0)+1}  Sun {slot.get('sun', 0)}",
                    f"Kills: {slot.get('zombies_killed', 0)}  Plants: {slot.get('plants_placed', 0)}  {slot.get('time_str', '')}"
                ]
                for j, line in enumerate(lines):
                    s = font_label.render(line, True, (180, 200, 180))
                    surface.blit(s, (btn.x + 10, btn.y + 8 + j * 22))
                d_hover = db.collidepoint(mx, my)
                pygame.draw.rect(surface, (160, 60, 60) if d_hover else (120, 40, 40), db)
                dt = font_label.render('Delete', True, WHITE)
                surface.blit(dt, dt.get_rect(center=db.center))
            else:
                pygame.draw.rect(surface, (50, 50, 50) if not hover else (70, 70, 70), btn)
                pygame.draw.rect(surface, (100, 100, 100), btn, 1)
                s = font_slot.render(f'Slot {i} — Empty', True, (100, 100, 100))
                surface.blit(s, (btn.x + 10, btn.y + 18))

        hover = self.back_btn.collidepoint(mx, my)
        pygame.draw.rect(surface, (80, 160, 80) if hover else (50, 120, 50), self.back_btn)
        pygame.draw.rect(surface, (150, 255, 150), self.back_btn, 2)
        t = font_btn.render('Back', True, WHITE)
        surface.blit(t, t.get_rect(center=self.back_btn.center))

        # Confirm delete dialog
        if self.confirm_delete:
            dlg_w, dlg_h = 260, 120
            dlg = pygame.Rect(SCREEN_WIDTH // 2 - dlg_w // 2, SCREEN_HEIGHT // 2 - dlg_h // 2, dlg_w, dlg_h)
            pygame.draw.rect(surface, (50, 50, 50), dlg)
            pygame.draw.rect(surface, (200, 80, 80), dlg, 2)
            t = font_slot.render('Delete this save?', True, WHITE)
            surface.blit(t, t.get_rect(center=(dlg.centerx, dlg.y + 30)))
            y_btn = pygame.Rect(dlg.x + 30, dlg.y + 65, 80, 35)
            n_btn = pygame.Rect(dlg.x + 140, dlg.y + 65, 80, 35)
            for b, label in [(y_btn, 'Yes'), (n_btn, 'No')]:
                h = b.collidepoint(mx, my)
                pygame.draw.rect(surface, (160, 60, 60) if h else (120, 40, 40), b)
                pygame.draw.rect(surface, (200, 100, 100), b, 1)
                tx = font_btn.render(label, True, WHITE)
                surface.blit(tx, tx.get_rect(center=b.center))
