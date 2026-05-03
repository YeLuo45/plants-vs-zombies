import pygame
import sys
import time as time_module
from source.constants import *
from source.state.level import LevelState
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
        self.sound = SoundManager.get_instance()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)
        self.font_tiny = pygame.font.Font(None, 24)

        # Pause menu button rects
        self._build_pause_buttons()
        self._build_end_buttons()

    def _build_pause_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.pause_resume_btn = pygame.Rect(bx, 200, bw, bh)
        self.pause_restart_btn = pygame.Rect(bx, 265, bw, bh)
        self.pause_quit_btn = pygame.Rect(bx, 330, bw, bh)

    def _build_end_buttons(self):
        bw, bh = 180, 55
        bx = SCREEN_WIDTH // 2 - bw // 2
        self.end_restart_btn = pygame.Rect(bx, 320, bw, bh)
        self.end_menu_btn = pygame.Rect(bx, 385, bw, bh)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._handle_escape()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._handle_enter()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                self._handle_click(mx, my)
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if self.state == 'playing' and self.level:
                    self.level.handle_mouse_move(mx, my)

    def _handle_escape(self):
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

    def _handle_enter(self):
        if self.state == 'menu':
            self.start_game()
        elif self.state in ('gameover', 'victory'):
            self.state = 'menu'

    def _handle_click(self, mx, my):
        if self.state == 'menu':
            # Start button
            if 300 <= mx <= 500 and 350 <= my <= 420:
                self.sound.play('click')
                self.start_game()
        elif self.state == 'playing':
            self.level.handle_click(mx, my)
        elif self.state == 'paused':
            self._handle_pause_click(mx, my)
        elif self.state in ('gameover', 'victory'):
            self._handle_end_click(mx, my)

    def _handle_pause_click(self, mx, my):
        if self.pause_resume_btn.collidepoint(mx, my):
            self.state = 'playing'
            self.sound.play('click')
        elif self.pause_restart_btn.collidepoint(mx, my):
            self.sound.play('click')
            self.start_game()
        elif self.pause_quit_btn.collidepoint(mx, my):
            self.running = False

    def _handle_end_click(self, mx, my):
        if self.end_restart_btn.collidepoint(mx, my):
            self.sound.play('click')
            self.start_game()
        elif self.end_menu_btn.collidepoint(mx, my):
            self.state = 'menu'
            self.sound.play('click')

    def start_game(self):
        self.level = LevelState(self.screen)
        self.level.start_time = time_module.time()
        self.state = 'playing'

    def update(self, dt):
        if self.state == 'playing' and self.level:
            self.level.update(dt)
            if self.level.game_over:
                self.state = 'gameover'
                self.sound.play('gameover')
            elif self.level.victory:
                self.state = 'victory'
                self.sound.play('victory')

    def draw(self):
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            if self.level:
                self.level.draw(self.screen)
        elif self.state == 'paused':
            # Draw game state behind overlay
            if self.level:
                self.level.draw(self.screen)
            self.draw_pause_menu()
        elif self.state == 'gameover':
            self.draw_gameover()
        elif self.state == 'victory':
            self.draw_victory()
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
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 130))
        self.screen.blit(title, title_rect)

        # Animated subtitle
        import time
        t = time.time()
        colors = [(50, 200, 50), (100, 255, 100)]
        idx = int(t * 2) % 2
        sub = self.font_small.render('Build your deck. Defend the lawn.', True, colors[idx])
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 190))
        self.screen.blit(sub, sub_rect)

        btn_rect = pygame.Rect(300, 330, 200, 70)
        mx, my = pygame.mouse.get_pos()
        hover = btn_rect.collidepoint(mx, my)
        self.draw_button(btn_rect, 'Start', hover)

        # Controls hint
        for i, hint in enumerate([
            'Mouse: Select card / Place plant',
            'Shovel icon: Remove plant',
            'ESC: Pause game',
        ]):
            h = self.font_tiny.render(hint, True, (140, 140, 140))
            r = h.get_rect(center=(SCREEN_WIDTH // 2, 440 + i * 25))
            self.screen.blit(h, r)

    def draw_pause_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.font_large.render('PAUSED', True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)

        mx, my = pygame.mouse.get_pos()
        self.draw_button(self.pause_resume_btn, 'Resume', self.pause_resume_btn.collidepoint(mx, my))
        self.draw_button(self.pause_restart_btn, 'Restart', self.pause_restart_btn.collidepoint(mx, my))
        self.draw_button(self.pause_quit_btn, 'Quit', self.pause_quit_btn.collidepoint(mx, my))

        hint = self.font_tiny.render('Press ESC to resume', True, (160, 160, 160))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, 420))
        self.screen.blit(hint, hint_rect)

    def _draw_end_screen(self, title_text, title_color, bg_color, is_victory):
        self.screen.fill(bg_color)

        title = self.font_large.render(title_text, True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)

        if self.level:
            stats = self.level.get_stats()
            lines = [
                f"Waves Completed: {stats['waves_completed']}/{stats['total_waves']}",
                f"Zombies Killed: {stats['zombies_killed']}",
                f"Plants Placed: {stats['plants_placed']}",
                f"Time: {stats['time_elapsed']}",
            ]
            for i, line in enumerate(lines):
                surf = self.font_medium.render(line, True, WHITE)
                r = surf.get_rect(center=(SCREEN_WIDTH // 2, 180 + i * 45))
                self.screen.blit(surf, r)

        mx, my = pygame.mouse.get_pos()
        self.draw_button(self.end_restart_btn, 'Play Again', self.end_restart_btn.collidepoint(mx, my))
        self.draw_button(self.end_menu_btn, 'Main Menu', self.end_menu_btn.collidepoint(mx, my))

    def draw_gameover(self):
        self._draw_end_screen('GAME OVER', (200, 50, 50), (30, 0, 0), False)

    def draw_victory(self):
        self._draw_end_screen('VICTORY!', (255, 215, 0), (10, 50, 10), True)

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
