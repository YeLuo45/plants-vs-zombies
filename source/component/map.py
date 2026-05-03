import pygame
from source.constants import *

class Grid:
    def __init__(self):
        self.rows = GRID_ROWS
        self.cols = GRID_COLS
        self.cell_w = CELL_WIDTH
        self.cell_h = CELL_HEIGHT
        self.offset_x = GRID_OFFSET_X
        self.offset_y = GRID_OFFSET_Y
        self.cells = [[None for _ in range(self.cols)] for _ in range(self.rows)]

    def get_cell_rect(self, row, col):
        x = self.offset_x + col * self.cell_w
        y = self.offset_y + row * self.cell_h
        return pygame.Rect(x, y, self.cell_w, self.cell_h)

    def get_cell_from_mouse(self, mx, my):
        col = (mx - self.offset_x) // self.cell_w
        row = (my - self.offset_y) // self.cell_h
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return int(row), int(col)
        return None, None

    def can_plant(self, row, col):
        if row is None or col is None:
            return False
        return self.cells[row][col] is None

    def place_plant(self, plant, row, col):
        self.cells[row][col] = plant

    def remove_plant(self, row, col):
        self.cells[row][col] = None

    def draw(self, surface):
        lawn_rect = pygame.Rect(self.offset_x, self.offset_y,
                                 self.cols * self.cell_w, self.rows * self.cell_h)
        pygame.draw.rect(surface, BG_COLOR, lawn_rect)
        for row in range(self.rows + 1):
            y = self.offset_y + row * self.cell_h
            pygame.draw.line(surface, GRID_LINE_COLOR,
                             (self.offset_x, y),
                             (self.offset_x + self.cols * self.cell_w, y), 2)
        for col in range(self.cols + 1):
            x = self.offset_x + col * self.cell_w
            pygame.draw.line(surface, GRID_LINE_COLOR,
                             (x, self.offset_y),
                             (x, self.offset_y + self.rows * self.cell_h), 2)
