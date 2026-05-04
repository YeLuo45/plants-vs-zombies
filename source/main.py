import pygame
import sys
import time as time_module
from source.constants import *
from source.state.level import LevelState
from source.state.achievements import AchievementManager, AchievementPanel, StatsPanel, StatsManager
from source.state.save_system import SaveManager, SettingsState, LoadScreen
from source.state.leaderboard import LeaderboardManager
from source.component.sound_manager import SoundManager


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Plants vs Zombies')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.level = None
        self.endless = None
        self.zen = None
        self.lawnbowling = None
        self.sound = SoundManager.get_instance()
        self.ach = AchievementManager.get_instance()
        self.sm = SaveManager.get_instance()
        self.stm = StatsManager.get_instance()
        self.leaderboard = LeaderboardManager.get_instance()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)

        self._build_menu_buttons()
        self._build_pause_buttons()
        self._build_end_buttons()
        self.show_ach_panel = False
        self.show_stats_panel = False
        self.ach_panel = None
        self.stats_panel = None
        self.settings = None
        self.load_screen = None
        self.pending_mode = None  # mode to start after load
        self.save_enabled = True  # can save current game
        self.show_leaderboard = False  # for endless game over screen
        self._session_start_time = time_module.time()

    def _build_menu_buttons(self):
        bw, bh = 200, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.menu_buttons = [
            ('adventure',  pygame.Rect(bx, 210, bw, bh)),
            ('endless',    pygame.Rect(bx, 275, bw, bh)),
            ('spectator',  pygame.Rect(bx, 340, bw, bh)),
            ('zen',        pygame.Rect(bx, 405, bw, bh)),
            ('bowling',    pygame.Rect(bx, 470, bw, bh)),
        ]
        self.ach_btn = pygame.Rect(SCREEN_WIDTH - 130, 40, 120, 40)
        self.stats_btn = pygame.Rect(SCREEN_WIDTH - 130, 90, 120, 40)
        self.load_btn = pygame.Rect(SCREEN_WIDTH // 2 - bw // 2, 495, bw, 45)
        self.settings_btn = pygame.Rect(SCREEN_WIDTH - 50, 10, 40, 40)

    def _build_pause_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.pause_resume_btn = pygame.Rect(bx, 170, bw, bh)
        self.pause_save_btn = pygame.Rect(bx, 235, bw, bh)
        self.pause_settings_btn = pygame.Rect(bx, 300, bw, bh)
        self.pause_restart_btn = pygame.Rect(bx, 365, bw, bh)
        self.pause_quit_btn = pygame.Rect(bx, 430, bw, bh)

    def _build_end_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.end_restart_btn = pygame.Rect(bx, 350, bw, bh)
        self.end_menu_btn = pygame.Rect(bx, 415, bw, bh)

    @property
    def current_state(self):
        return self.level or self.endless or self.zen or self.lawnbowling or self.spectator

    @property
    def game_speed(self):
        return self.sm.get('game_speed', 1.0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()
                elif event.key in (pygame.K_a, pygame.K_j):
                    # Open achievements panel
                    if not self.show_ach_panel and not self.show_stats_panel:
                        self.ach_panel = AchievementPanel(self.ach)
                        self.show_ach_panel = True
                elif event.key == pygame.K_s:
                    # Open stats panel
                    if not self.show_ach_panel and not self.show_stats_panel:
                        self.stats_panel = StatsPanel(self.ach, self.stm)
                        self.show_stats_panel = True
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    # Speed control for spectator mode
                    if self.spectator and self.state == 'playing':
                        self.spectator.handle_key(event.key)
                elif self.show_ach_panel and self.ach_panel:
                    self.ach_panel.handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                self._handle_click(mx, my)
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self._handle_mouse_move(mx, my)

    def _handle_escape(self):
        if self.show_ach_panel:
            self.show_ach_panel = False
            self.ach_panel = None
            return
        if self.show_stats_panel:
            self.show_stats_panel = False
            self.stats_panel = None
            return
        if self.settings:
            self.settings = None
            return
        if self.load_screen:
            self.load_screen = None
            return
        if self.state == 'menu':
            self.running = False
        elif self.state == 'playing':
            self.state = 'paused'
        elif self.state == 'paused':
            self.state = 'playing'
        elif self.state in ('gameover', 'victory'):
            self.state = 'menu'

    def _handle_mouse_move(self, mx, my):
        if self.state == 'playing' and self.level:
            self.level.handle_mouse_move(mx, my)
        elif self.state == 'playing' and self.lawnbowling:
            self.lawnbowling.handle_mouse_move(mx, my)
        elif self.state == 'playing' and self.zen:
            self.zen.handle_mouse_move(mx, my)

    def _handle_click(self, mx, my):
        if self.show_ach_panel:
            result = self.ach_panel.handle_click(mx, my)
            if result == 'close':
                self.show_ach_panel = False
                self.ach_panel = None
            return

        if self.show_stats_panel:
            result = self.stats_panel.handle_click(mx, my)
            if result == 'close':
                self.show_stats_panel = False
                self.stats_panel = None
            return

        # Settings overlay
        if self.settings:
            result = self.settings.handle_click(mx, my)
            if result == 'back':
                self.settings = None
            elif result == 'fullscreen_toggle':
                self._toggle_fullscreen()
            elif result == 'changed':
                self.sound.apply_volume_settings()
            return

        # Load screen overlay
        if self.load_screen:
            result = self.load_screen.handle_click(mx, my)
            if result == 'back':
                self.load_screen = None
            elif result in (1, 2, 3):
                self._do_load(result)
            return

        if self.state == 'menu':
            for name, rect in self.menu_buttons:
                if rect.collidepoint(mx, my):
                    self.sound.play('click')
                    self._start_mode(name)
                    return
            if self.ach_btn.collidepoint(mx, my):
                self.sound.play('click')
                self.ach_panel = AchievementPanel(self.ach)
                self.show_ach_panel = True
                return
            if self.stats_btn.collidepoint(mx, my):
                self.sound.play('click')
                self.stats_panel = StatsPanel(self.ach, self.stm)
                self.show_stats_panel = True
                return
            if self.load_btn.collidepoint(mx, my):
                if self.sm.has_save():
                    self.sound.play('click')
                    self.load_screen = LoadScreen(self.screen, self.sm)
                return
            if self.settings_btn.collidepoint(mx, my):
                self.sound.play('click')
                self.settings = SettingsState(self.screen)
                return

        elif self.state == 'playing':
            if self.settings:
                return
            cs = self.current_state
            if cs:
                cs.handle_click(mx, my)

        elif self.state == 'paused':
            if self.pause_resume_btn.collidepoint(mx, my):
                self.state = 'playing'
                self.sound.play('click')
            elif self.pause_save_btn.collidepoint(mx, my):
                self._do_save()
                self.sound.play('click')
            elif self.pause_settings_btn.collidepoint(mx, my):
                self.settings = SettingsState(self.screen)
                self.sound.play('click')
            elif self.pause_restart_btn.collidepoint(mx, my):
                self.sound.play('click')
                self._restart_current_mode()
            elif self.pause_quit_btn.collidepoint(mx, my):
                self.state = 'menu'
                self.sound.play('click')

        elif self.state in ('gameover', 'victory'):
            is_endless_ev = bool(self.endless and hasattr(self.endless, 'wave_index'))
            if self.show_leaderboard and is_endless_ev:
                if self.leaderboard.handle_click(mx, my):
                    self.show_leaderboard = False
                    return
            if self.end_restart_btn.collidepoint(mx, my):
                self.sound.stop_music()
                self._restart_current_mode()
            elif self.end_menu_btn.collidepoint(mx, my):
                self.state = 'menu'
                self.show_leaderboard = False
                self.sound.play('click')

    def _toggle_fullscreen(self):
        pygame.display.toggle_fullscreen()

    def _start_mode(self, mode):
        self.level = None
        self.endless = None
        self.zen = None
        self.lawnbowling = None
        self.spectator = None
        self.save_enabled = True

        if mode == 'adventure':
            self.level = LevelState(self.screen)
            self.level.start_time = time_module.time()
        elif mode == 'endless':
            from source.state.endless import EndlessState
            self.endless = EndlessState(self.screen)
        elif mode == 'spectator':
            from source.state.spectator import SpectatorState
            self.spectator = SpectatorState(self.screen)
            self.save_enabled = False
        elif mode == 'zen':
            from source.state.zen import ZenState
            self.zen = ZenState(self.screen)
            self.save_enabled = False  # Zen doesn't save
        elif mode == 'bowling':
            from source.state.lawnbowling import LawnBowlingState
            self.lawnbowling = LawnBowlingState(self.screen)
            self.save_enabled = False
        self.state = 'playing'
        self.sound.play_music(mode)

    def _do_save(self):
        if not self.current_state or not self.save_enabled:
            return
        slot = self.sm.get_latest_slot()
        if slot is None:
            slot = 1
        elif slot >= 3:
            slot = 1
        else:
            slot += 1

        mode = 'adventure'
        if self.endless:
            mode = 'endless'
        elif self.lawnbowling:
            mode = 'bowling'

        self.sm.save(slot, self.current_state, mode)

    def _do_load(self, slot):
        data = self.sm.load(slot)
        if data is None:
            return
        mode = data.get('mode', 'adventure')
        self._start_mode(mode)
        # Restore state
        if mode == 'adventure' and self.level:
            self._restore_level(data)
        elif mode == 'endless' and self.endless:
            self._restore_endless(data)

    def _restore_level(self, data):
        self.level.wave_index = data.get('wave_index', 0)
        self.level.wave_active = data.get('wave_active', False)
        self.level.pre_wave_timer = data.get('pre_wave_timer', 5.0)
        self.level.menubar.sun = data.get('sun', 150)
        self.level.menubar.cooldowns = dict(data.get('cooldowns', {}))
        self.level.plants_placed = data.get('plants_placed', 0)
        self.level.zombies_killed = data.get('zombies_killed', 0)
        # Restore grid
        grid_data = data.get('grid', {})
        for key, pdata in grid_data.items():
            r, c = int(key.split(',')[0]), int(key.split(',')[1])
            from source.component.plant import create_plant
            p = create_plant(pdata['name'], r, c, self.level.grid)
            p.hp = pdata.get('hp', 100)
            p.cooldown_timer = pdata.get('cooldown_timer', 0)
            p.shoot_timer = pdata.get('shoot_timer', 0)
            p.sun_timer = pdata.get('sun_timer', 0)
            p.eat_timer = pdata.get('eat_timer', 0)
            p.eating = pdata.get('eating', False)
            p.eaten = pdata.get('eaten', False)
            p.armed = pdata.get('armed', False)
            p.flash_timer = pdata.get('flash_timer', 0)
            p.squash_state = pdata.get('squash_state', 'idle')
            p.hypno_active = pdata.get('hypno_active', False)
            p.laddered = pdata.get('laddered', False)
            p.scared_hidden = pdata.get('scared_hidden', False)
            p.scared_timer = pdata.get('scared_timer', 0)
            self.level.grid.place_plant(p, r, c)
        # Restore zombies
        for zdata in data.get('zombies', []):
            from source.component.zombie import create_zombie
            z = create_zombie(zdata['name'], zdata['x'], zdata['row'], self.level.grid)
            z.hp = zdata.get('hp', 100)
            if zdata.get('newspaper_destroyed'):
                z.newspaper_destroyed = True
                z.color = (200, 80, 80)
            self.level.zombies.append(z)

    def _restore_endless(self, data):
        if hasattr(self.endless, 'hp_multiplier'):
            self.endless.hp_multiplier = data.get('hp_multiplier', 1.0)
        # Similar restoration as level
        self._restore_level(data)

    def _restart_current_mode(self):
        self.show_leaderboard = False
        mode = 'adventure'
        if self.endless:
            mode = 'endless'
        elif self.lawnbowling:
            mode = 'bowling'
        elif self.zen:
            mode = 'zen'
        self._start_mode(mode)

    def update(self, dt):
        if self.state == 'playing':
            # Accumulate play time
            self.stm.add_play_time(dt)

        if self.state != 'playing':
            return
        cs = self.current_state
        if cs is None:
            return

        speed = self.game_speed
        cs.update(dt * speed)

        if self.level:
            if self.level.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
                self.ach.on_win(plants_lost=0)
                self.stm.on_game_lost()
            elif self.level.victory:
                self.state = 'victory'
                self.sound.play('victory')
                self.ach.on_win(plants_lost=0)
                self.stm.on_game_won()
        elif self.endless:
            if self.endless.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
                self.show_leaderboard = True
                self.stm.on_game_lost()
        elif self.lawnbowling:
            if self.lawnbowling.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
                self.stm.on_game_lost()
            elif self.lawnbowling.victory:
                self.state = 'victory'
                self.sound.play('victory')
                self.ach.on_mini_game_win('bowling')
                self.stm.on_game_won()

    def draw(self):
        if self.state == 'menu':
            self.draw_menu()
            if self.sound.current_music != 'menu':
                self.sound.play_music('menu')
        elif self.state == 'playing':
            cs = self.current_state
            if cs:
                cs.draw(self.screen)
            self.ach.draw_badge(self.screen)
            # Settings gear icon
            self._draw_settings_icon()
        elif self.state == 'paused':
            cs = self.current_state
            if cs:
                cs.draw(self.screen)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            self.draw_pause_menu()
        elif self.state == 'gameover':
            self._draw_end_screen()
        elif self.state == 'victory':
            self._draw_end_screen()

        if self.show_ach_panel and self.ach_panel:
            self.ach_panel.draw(self.screen)
        if self.show_stats_panel and self.stats_panel:
            self.stats_panel.draw(self.screen)
        if self.settings:
            self.settings.draw(self.screen)
        if self.load_screen:
            self.load_screen.draw(self.screen)

        pygame.display.flip()

    def _draw_settings_icon(self):
        bx, by = SCREEN_WIDTH - 50, 10
        pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, 40, 40))
        # Gear symbol
        font = pygame.font.Font(None, 24)
        t = font.render('⚙', True, (150, 150, 150))
        self.screen.blit(t, (bx + 8, by + 4))

    def draw_button(self, rect, text, hover=False):
        bg = (80, 160, 80) if hover else (50, 120, 50)
        pygame.draw.rect(self.screen, bg, rect)
        pygame.draw.rect(self.screen, (150, 255, 150), rect, 2)
        surf = self.font_medium.render(text, True, WHITE)
        r = surf.get_rect(center=rect.center)
        self.screen.blit(surf, r)

    def draw_menu(self):
        self.screen.fill((20, 60, 20))

        title = self.font_large.render('Plants vs Zombies', True, (50, 200, 50))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(title, title_rect)

        import time as ti_module
        t = ti_module.time()
        colors = [(50, 200, 50), (100, 255, 100)]
        idx = int(t * 2) % 2
        sub = self.font_small.render('Build your deck. Defend the lawn.', True, colors[idx])
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 155))
        self.screen.blit(sub, sub_rect)

        mx, my = pygame.mouse.get_pos()
        mode_names = {
            'adventure': 'Adventure Mode',
            'endless':   'Endless Survival',
            'spectator': 'Spectator Mode',
            'zen':       'Zen Garden',
            'bowling':   'Lawn Bowling',
        }
        for name, rect in self.menu_buttons:
            hover = rect.collidepoint(mx, my)
            self.draw_button(rect, mode_names[name], hover)

        # Load button
        if self.sm.has_save():
            lh = self.load_btn.collidepoint(mx, my)
            pygame.draw.rect(self.screen, (60, 100, 60) if lh else (50, 80, 50), self.load_btn)
            pygame.draw.rect(self.screen, (150, 255, 150), self.load_btn, 2)
            t = self.font_small.render('Load Game', True, WHITE)
            self.screen.blit(t, t.get_rect(center=self.load_btn.center))

        # Achievement button
        ach_hover = self.ach_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (60, 60, 30) if ach_hover else (40, 40, 20), self.ach_btn)
        pygame.draw.rect(self.screen, (200, 200, 100), self.ach_btn, 1)
        ach_count = self.ach.count_unlocked()
        ach_text = self.font_small.render(f'{ach_count}/13', True, (200, 200, 100))
        ar = ach_text.get_rect(center=self.ach_btn.center)
        self.screen.blit(ach_text, ar)

        # Stats button
        stats_hover = self.stats_btn.collidepoint(mx, my)
        pygame.draw.rect(self.screen, (30, 50, 70) if stats_hover else (20, 35, 55), self.stats_btn)
        pygame.draw.rect(self.screen, (100, 160, 200), self.stats_btn, 1)
        stats_text = self.font_small.render('Stats', True, (100, 160, 200))
        sr = stats_text.get_rect(center=self.stats_btn.center)
        self.screen.blit(stats_text, sr)

        # Settings gear
        self._draw_settings_icon()

        for i, hint in enumerate([
            'Mouse: Select card / Place plant   ESC: Pause game',
            'A/J: Achievements   S: Stats   ESC: Menu',
        ]):
            h = self.font_tiny.render(hint, True, (100, 100, 100))
            r = h.get_rect(center=(SCREEN_WIDTH // 2, 555 + i * 22))
            self.screen.blit(h, r)

    def draw_pause_menu(self):
        title = self.font_large.render('PAUSED', True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(title, title_rect)
        mx, my = pygame.mouse.get_pos()
        self.draw_button(self.pause_resume_btn, 'Resume', self.pause_resume_btn.collidepoint(mx, my))
        if self.save_enabled:
            self.draw_button(self.pause_save_btn, 'Save Game', self.pause_save_btn.collidepoint(mx, my))
        self.draw_button(self.pause_settings_btn, 'Settings', self.pause_settings_btn.collidepoint(mx, my))
        self.draw_button(self.pause_restart_btn, 'Restart', self.pause_restart_btn.collidepoint(mx, my))
        self.draw_button(self.pause_quit_btn, 'Main Menu', self.pause_quit_btn.collidepoint(mx, my))

    def _draw_end_screen(self):
        self.screen.fill((30, 0, 0) if self.state == 'gameover' else (10, 50, 10))
        title_text = 'GAME OVER' if self.state == 'gameover' else 'VICTORY!'
        title_color = (200, 50, 50) if self.state == 'gameover' else (255, 215, 0)
        title = self.font_large.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        cs = self.current_state
        lines = []
        is_endless = bool(self.endless and hasattr(self.endless, 'wave_index'))
        if self.level and hasattr(self.level, 'get_stats'):
            stats = self.level.get_stats()
            lines = [
                f"Waves: {stats['waves_completed']}/{stats['total_waves']}",
                f"Kills: {stats['zombies_killed']}",
                f"Plants: {stats['plants_placed']}",
                f"Time: {stats['time_elapsed']}",
            ]
        elif is_endless:
            stats = self.endless.get_stats()
            is_record = self.leaderboard.is_new_record(stats['wave_index']) if hasattr(self, 'leaderboard') else False
            lines = [
                f"Waves Survived: {stats['wave_index']}",
                f"Kills: {stats['zombies_killed']}",
                f"Plants: {stats['plants_placed']}",
                f"Time: {stats['time_elapsed']}",
            ]
            if is_record:
                record_surf = self.font_medium.render('NEW RECORD!', True, (255, 215, 0))
                record_rect = record_surf.get_rect(center=(SCREEN_WIDTH // 2, 180))
                self.screen.blit(record_surf, record_rect)
        elif self.lawnbowling and hasattr(self.lawnbowling, 'wave_index'):
            lines = [
                f"Waves: {self.lawnbowling.wave_index}/10",
                f"Kills: {self.lawnbowling.total_kills}",
            ]
        elif self.zen and hasattr(self.zen, 'plants_placed'):
            lines = [f"Plants Placed: {self.zen.plants_placed}"]

        for i, line in enumerate(lines):
            surf = self.font_medium.render(line, True, WHITE)
            r = surf.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 45))
            self.screen.blit(surf, r)

        # Show leaderboard for endless mode
        if self.show_leaderboard and is_endless:
            self.leaderboard.draw(self.screen)

        mx, my = pygame.mouse.get_pos()
        self.draw_button(self.end_restart_btn, 'Play Again', self.end_restart_btn.collidepoint(mx, my))
        self.draw_button(self.end_menu_btn, 'Main Menu', self.end_menu_btn.collidepoint(mx, my))

    def run(self):
        dt = 0
        while self.running:
            self.handle_events()
            self.update(dt)
            self.draw()
            dt = self.clock.tick(FPS) / 1000.0
        pygame.quit()


def main():
    game = Game()
    game.run()

if __name__ == '__main__':
    main()
