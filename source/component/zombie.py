import pygame
from source.constants import *

class Zombie(pygame.sprite.Sprite):
    def __init__(self, name, x, row, grid):
        super().__init__()
        self.name = name
        self.row = row
        self.grid = grid
        cfg = ZOMBIES[name]
        self.hp = cfg['hp']
        self.max_hp = cfg['hp']
        self.base_speed = cfg['speed']
        self.speed = cfg['speed']
        self.attack = cfg['attack']
        self.attack_interval = cfg['interval']
        self.attack_timer = 0
        self.color = cfg['color']
        self.w = cfg['w']
        self.h = cfg['h']
        self.x = x
        self.y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2
        self.attacking = False
        self.attack_target = None
        self.slow_timer = 0
        self.pole_jumped = False
        self.dead = False
        self.death_timer = 0
        self.eating = False
        self.eat_anim_timer = 0
        # Animation
        self.anim_frame = 0
        self.anim_timer = 0
        self.arm_y = 0  # arm raise offset for eating

    def update(self, dt):
        if self.dead:
            self.death_timer += dt
            return None

        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        self.attack_timer += dt
        if self.slow_timer > 0:
            self.slow_timer -= dt
            self.speed = self.base_speed * ICE_SLOW_FACTOR
        else:
            self.speed = self.base_speed

        # Find plant to attack
        plant_in_way = None
        for col in range(self.grid.cols):
            p = self.grid.cells[self.row][col]
            if p and hasattr(p, 'hp') and p.hp > 0:
                plant_x = p.rect.centerx
                if self.x - plant_x < 40 and self.x - plant_x > -40:
                    plant_in_way = p
                    break
                elif self.x <= plant_x:
                    break

        if plant_in_way:
            self.attacking = True
            self.eating = True
            self.attack_target = plant_in_way
            self.x -= 0  # Stop walking while eating
            if self.attack_timer >= self.attack_interval:
                self.attack_timer = 0
                self.eat_anim_timer = 0
                dead = plant_in_way.take_damage(self.attack)
                if dead:
                    for c in range(self.grid.cols):
                        if self.grid.cells[self.row][c] == plant_in_way:
                            self.grid.cells[self.row][c] = None
                            break
                    self.attacking = False
                    self.eating = False
                    self.attack_target = None
        else:
            self.attacking = False
            self.eating = False
            self.x -= self.speed

        if self.eating:
            self.eat_anim_timer += dt
            # Arm raises up and down while eating
            self.arm_y = int(5 * (1 if int(self.eat_anim_timer * 6) % 2 == 0 else -1))

        if self.x < self.grid.offset_x - 20:
            return 'reached_home'
        return None

    def die(self):
        self.dead = True
        self.death_timer = 0

    def draw(self, surface):
        if self.dead:
            # Death animation: fade out over 0.5s
            alpha = max(0, 255 - int(self.death_timer * 500))
            if alpha <= 0:
                return
            x, y = int(self.x), int(self.y)
            # Draw zombie in darker color with transparency
            temp_surf = pygame.Surface((self.w + 10, self.h + 10), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (*self.color, alpha), 
                           (5, 5, self.w, self.h))
            pygame.draw.circle(temp_surf, (180, 180, 180, alpha), 
                             (self.w // 2 + 5, 5), 12)
            surface.blit(temp_surf, (x - self.w // 2 - 5, y - self.h // 2 - 5))
            return

        x, y = int(self.x), int(self.y)
        body_y = y + self.arm_y if self.eating else y

        # Body
        body_rect = pygame.Rect(x - self.w // 2, body_y - self.h // 2, self.w, self.h)
        pygame.draw.rect(surface, self.color, body_rect)

        # Arms (raised while eating, normal while walking)
        if self.eating:
            # Raised arm
            pygame.draw.rect(surface, self.color, (x - self.w // 2 - 8, body_y - self.h // 2 + 5 + self.arm_y, 8, 20))
            # Lowered arm (dangling)
            pygame.draw.rect(surface, self.color, (x + self.w // 2, body_y - self.h // 2 + 10, 8, 20))
        else:
            # Normal arms swinging with walk animation
            arm_offset = 5 if self.anim_frame == 0 else -5
            pygame.draw.rect(surface, self.color, (x - self.w // 2 - 8, body_y - 5 + arm_offset, 8, 20))
            pygame.draw.rect(surface, self.color, (x + self.w // 2, body_y - 5 - arm_offset, 8, 20))

        # Head
        pygame.draw.circle(surface, (180, 180, 180), (x, y - self.h // 2 - 10 + (self.arm_y if self.eating else 0)), 12)

        # Zombie type decoration
        if self.name == 'cone':
            pygame.draw.rect(surface, ORANGE, (x - 15, y - self.h // 2 - 25, 30, 15))
        elif self.name == 'bucket':
            pygame.draw.rect(surface, GRAY, (x - 18, y - self.h // 2 - 28, 36, 20))
        elif self.name == 'football':
            pygame.draw.rect(surface, (80, 80, 80), (x - 20, y - self.h // 2 - 30, 40, 25))

        # Ice slow indicator
        if self.slow_timer > 0:
            pygame.draw.circle(surface, (150, 200, 255), (x, y), 5, 2)

        # HP bar
        if self.hp < self.max_hp:
            bar_w = 40
            bar_h = 5
            bx = x - bar_w // 2
            by = y - self.h // 2 - 35
            pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, GREEN, (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.die()
            return True
        return False

    def apply_slow(self):
        self.slow_timer = 2.0

def create_zombie(name, x, row, grid):
    return Zombie(name, x, row, grid)
