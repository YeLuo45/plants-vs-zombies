import pygame
import sys
from source.constants import *
from source.state.level import LevelState

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Plants vs Zombies')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.level = None
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 36)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.state == 'menu':
                        self.start_game()
                    elif self.state in ('gameover', 'victory'):
                        self.state = 'menu'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if self.state == 'menu':
                    # Start button area
                    if 300 <= mx <= 500 and 350 <= my <= 420:
                        self.start_game()
                elif self.state == 'playing':
                    self.level.handle_click(mx, my)

    def start_game(self):
        self.level = LevelState(self.screen)
        self.state = 'playing'

    def update(self, dt):
        if self.state == 'playing' and self.level:
            self.level.update(dt)
            if self.level.game_over:
                self.state = 'gameover'
            elif self.level.victory:
                self.state = 'victory'

    def draw(self):
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            if self.level:
                self.level.draw(self.screen)
        elif self.state == 'gameover':
            self.draw_gameover()
        elif self.state == 'victory':
            self.draw_victory()
        pygame.display.flip()

    def draw_menu(self):
        self.screen.fill((20, 60, 20))
        title = self.font_large.render('Plants vs Zombies', True, (50, 200, 50))
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        # Start button
        btn_rect = pygame.Rect(300, 350, 200, 70)
        pygame.draw.rect(self.screen, (50, 150, 50), btn_rect)
        pygame.draw.rect(self.screen, (100, 255, 100), btn_rect, 3)
        btn_text = self.font_medium.render('Start', True, WHITE)
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)
        hint = self.font_small.render('Press START or ENTER', True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH//2, 450))
        self.screen.blit(hint, hint_rect)

    def draw_gameover(self):
        self.screen.fill((40, 0, 0))
        go_text = self.font_large.render('GAME OVER', True, (200, 50, 50))
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(go_text, go_rect)
        hint = self.font_small.render('Press ENTER to return to menu', True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(hint, hint_rect)

    def draw_victory(self):
        self.screen.fill((20, 60, 20))
        v_text = self.font_large.render('VICTORY!', True, (255, 215, 0))
        v_rect = v_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(v_text, v_rect)
        hint = self.font_small.render('Press ENTER to return to menu', True, (180, 180, 180))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(hint, hint_rect)

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
