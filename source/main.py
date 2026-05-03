import pygame
import sys
import time as time_module
from source.constants import *
from source.state.level import LevelState
from source.state.achievements import AchievementManager
from source.component.sound_manager import SoundManager

# Lazy-loaded state modules
_endless_state = None
_zen_state = None
_lawnbowling_state = None


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
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)

        self._build_pause_buttons()
        self._build_end_buttons()
        self._build_menu_buttons()
        self.show_ach_panel = False

    def _build_menu_buttons(self):
        bw, bh = 200, 60
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.menu_buttons = [
            ('adventure',  pygame.Rect(bx, 260, bw, bh)),
            ('endless',    pygame.Rect(bx, 330, bw, bh)),
            ('zen',        pygame.Rect(bx, 400, bw, bh)),
            ('bowling',    pygame.Rect(bx, 470, bw, bh)),
        ]
        # Achievement button
        self.ach_btn = pygame.Rect(SCREEN_WIDTH - 130, 40, 120, 40)

    def _build_pause_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.pause_resume_btn = pygame.Rect(bx, 200, bw, bh)
        self.pause_restart_btn = pygame.Rect(bx, 265, bw, bh)
        self.pause_quit_btn = pygame.Rect(bx, 330, bw, bh)

    def _build_end_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.end_restart_btn = pygame.Rect(bx, 350, bw, bh)
        self.end_menu_btn = pygame.Rect(bx, 415, bw, bh)

    @property
    def current_state(self):
        return self.level or self.endless or self.zen or self.lawnbowling

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                self._handle_click(mx, my)
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                self._handle_mouse_move(mx, my)

    def _handle_escape(self):
        if self.show_ach_panel:
            self.show_ach_panel = False
            return
        if self.state == 'menu':
            self.running = False
        elif self.state == 'playing':
            self.state = 'paused'
            self.sound.play('click')
        elif self.state == 'paused':
            self.state = 'playing'
            self.sound.play('click')
        elif self.state in ('gameover', 'victory'):
            self.state = 'menu'
            self.sound.play('click')

    def _handle_mouse_move(self, mx, my):
        if self.state == 'playing' and self.level:
            self.level.handle_mouse_move(mx, my)
        elif self.state == 'playing' and self.lawnbowling:
            self.lawnbowling.handle_mouse_move(mx, my)
        elif self.state == 'playing' and self.zen:
            self.zen.handle_mouse_move(mx, my)

    def _handle_click(self, mx, my):
        if self.show_ach_panel:
            self.show_ach_panel = False
            return

        if self.state == 'menu':
            for name, rect in self.menu_buttons:
                if rect.collidepoint(mx, my):
                    self.sound.play('click')
                    self._start_mode(name)
                    return
            if self.ach_btn.collidepoint(mx, my):
                self.sound.play('click')
                self.show_ach_panel = True
                return
        elif self.state == 'playing':
            cs = self.current_state
            if cs:
                cs.handle_click(mx, my)
        elif self.state == 'paused':
            if self.pause_resume_btn.collidepoint(mx, my):
                self.state = 'playing'
                self.sound.play('click')
            elif self.pause_restart_btn.collidepoint(mx, my):
                self.sound.play('click')
                self._restart_current_mode()
            elif self.pause_quit_btn.collidepoint(mx, my):
                self.running = False
        elif self.state in ('gameover', 'victory'):
            if self.end_restart_btn.collidepoint(mx, my):
                self.sound.play('click')
                self._restart_current_mode()
            elif self.end_menu_btn.collidepoint(mx, my):
                self.state = 'menu'
                self.sound.play('click')

    def _start_mode(self, mode):
        self.level = None
        self.endless = None
        self.zen = None
        self.lawnbowling = None
        if mode == 'adventure':
            self.level = LevelState(self.screen)
            self.level.start_time = time_module.time()
        elif mode == 'endless':
            from source.state.endless import EndlessState
            self.endless = EndlessState(self.screen)
        elif mode == 'zen':
            from source.state.zen import ZenState
            self.zen = ZenState(self.screen)
        elif mode == 'bowling':
            from source.state.lawnbowling import LawnBowlingState
            self.lawnbowling = LawnBowlingState(self.screen)
        self.state = 'playing'

    def _restart_current_mode(self):
        mode = 'adventure'
        if self.endless:
            mode = 'endless'
        elif self.lawnbowling:
            mode = 'bowling'
        elif self.zen:
            mode = 'zen'
        self._start_mode(mode)

    def update(self, dt):
        if self.state != 'playing':
            return
        cs = self.current_state
        if cs is None:
            return

        cs.update(dt)

        if self.level:
            if self.level.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
                # Track achievement
                plants_lost = self.level.plants_placed - self.level.zombies_killed // 5
                self.ach.on_win(plants_lost=0)
            elif self.level.victory:
                self.state = 'victory'
                self.sound.play('victory')
                self.ach.on_win(plants_lost=0)
        elif self.endless:
            if self.endless.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
        elif self.lawnbowling:
            if self.lawnbowling.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
            elif self.lawnbowling.victory:
                self.state = 'victory'
                self.sound.play('victory')
                self.ach.on_mini_game_win('bowling')

    def draw(self):
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            cs = self.current_state
            if cs:
                cs.draw(self.screen)
            # Achievement badge
            self.ach.draw_badge(self.screen)
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

        if self.show_ach_panel:
            self.ach.draw_panel(self.screen)

        pygame.display.flip()

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
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        import time as ti_module
        t = ti_module.time()
        colors = [(50, 200, 50), (100, 255, 100)]
        idx = int(t * 2) % 2
        sub = self.font_small.render('Build your deck. Defend the lawn.', True, colors[idx])
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 165))
        self.screen.blit(sub, sub_rect)

        mx, my = pygame.mouse.get_pos()
        mode_names = {
            'adventure': 'Adventure Mode',
            'endless':   'Endless Survival',
            'zen':       'Zen Garden',
            'bowling':   'Lawn Bowling',
        }
        for name, rect in self.menu_buttons:
            hover = rect.collidepoint(mx, my)
            self.draw_button(rect, mode_names[name], hover)

        # Achievement button
        ach_hover = self.ach_btn.collidepoint(mx, my)
        ach_bg = (60, 60, 30) if ach_hover else (40, 40, 20)
        pygame.draw.rect(self.screen, ach_bg, self.ach_btn)
        pygame.draw.rect(self.screen, (200, 200, 100), self.ach_btn, 1)
        ach_count = self.ach.count_unlocked()
        ach_text = self.font_small.render(f'{ach_count}/13 Achievements', True, (200, 200, 100))
        ar = ach_text.get_rect(center=self.ach_btn.center)
        self.screen.blit(ach_text, ar)

        for i, hint in enumerate([
            'Mouse: Select card / Place plant',
            'Shovel icon: Remove plant',
            'ESC: Pause game',
        ]):
            h = self.font_tiny.render(hint, True, (100, 100, 100))
            r = h.get_rect(center=(SCREEN_WIDTH // 2, 540 + i * 22))
            self.screen.blit(h, r)

    def draw_pause_menu(self):
        title = self.font_large.render('PAUSED', True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)
        mx, my = pygame.mouse.get_pos()
        self.draw_button(self.pause_resume_btn, 'Resume', self.pause_resume_btn.collidepoint(mx, my))
        self.draw_button(self.pause_restart_btn, 'Restart', self.pause_restart_btn.collidepoint(mx, my))
        self.draw_button(self.pause_quit_btn, 'Quit', self.pause_quit_btn.collidepoint(mx, my))

    def _draw_end_screen(self):
        self.screen.fill((30, 0, 0) if self.state == 'gameover' else (10, 50, 10))
        title_text = 'GAME OVER' if self.state == 'gameover' else 'VICTORY!'
        title_color = (200, 50, 50) if self.state == 'gameover' else (255, 215, 0)
        title = self.font_large.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        # Stats
        cs = self.current_state
        lines = []
        if self.level and hasattr(self.level, 'get_stats'):
            stats = self.level.get_stats()
            lines = [
                f"Waves: {stats['waves_completed']}/{stats['total_waves']}",
                f"Kills: {stats['zombies_killed']}",
                f"Plants: {stats['plants_placed']}",
                f"Time: {stats['time_elapsed']}",
            ]
        elif self.endless and hasattr(self.endless, 'wave_index'):
            lines = [f"Waves Survived: {self.endless.wave_index}"]
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
