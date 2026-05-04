import pygame
import math
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
        self.base_y = grid.offset_y + row * grid.cell_h + grid.cell_h // 2
        self.y = self.base_y
        self.attacking = False
        self.attack_target = None
        self.slow_timer = 0
        self.dead = False
        self.death_timer = 0
        self.eating = False
        self.eat_anim_timer = 0
        self.just_bitten = False
        self.pole_jumped = False
        self.jump_timer = 0
        self.jumping = False
        self.pole_vaulting = False
        self.pole_vaulting_timer = 0
        self.anim_frame = 0
        self.anim_timer = 0
        self.arm_y = 0
        # Shake (when damaged)
        self.shake_timer = 0
        self.shake_active = False

        # P2-A zombie states
        self.newspaper_hp = 100 if name == 'newspaper' else 0
        self.newspaper_destroyed = False
        self.panic_timer = 0
        self.miner_phase = 'walking_right' if name == 'miner' else None
        self.miner_start_row = row
        self.has_ladder = True if name == 'ladder' else False
        self.ladder_placed_plant = None
        self.walking_over_plants = False
        # Football helmet HP (separate from body HP)
        self.helmet_hp = 200 if name == 'football' else 0
        self.max_helmet_hp = 200 if name == 'football' else 0

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
            if self.newspaper_destroyed:
                self.speed = 0.6
            else:
                self.speed = self.base_speed

        # Shake timer update
        if self.shake_active:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_active = False
                self.shake_timer = 0

        # Miner zombie
        if self.name == 'miner':
            return self._update_miner(dt)

        # Pole vaulting zombie
        if self.name == 'pole':
            return self._update_pole(dt)

        # Newspaper zombie stumble
        if self.name == 'newspaper':
            self.panic_timer += dt
            if self.newspaper_destroyed and self.panic_timer < 0.3:
                return None

        plant_in_way = self._find_plant_ahead()

        # Ladder zombie
        if self.has_ladder and plant_in_way and not self.ladder_placed_plant:
            self.ladder_placed_plant = plant_in_way
            plant_in_way.laddered = True
            self.has_ladder = False
            self.walking_over_plants = True

        if plant_in_way:
            if hasattr(plant_in_way, 'laddered') and plant_in_way.laddered:
                self.walking_over_plants = True
                self.x -= self.speed
                self.attacking = True
                self.attack_target = plant_in_way
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    plant_in_way.take_damage(self.attack * 0.3)
                    if plant_in_way.hp <= 0:
                        plant_in_way.laddered = False
                        self.walking_over_plants = False
                        for c in range(self.grid.cols):
                            if self.grid.cells[self.row][c] == plant_in_way:
                                self.grid.cells[self.row][c] = None
                                break
                        self.attacking = False
            else:
                self.attacking = True
                self.eating = True
                self.attack_target = plant_in_way
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    self.eat_anim_timer = 0
                    self.just_bitten = True
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
            self.walking_over_plants = False
            self.x -= self.speed

        if self.eating:
            self.eat_anim_timer += dt
            self.arm_y = int(5 * (1 if int(self.eat_anim_timer * 6) % 2 == 0 else -1))

        if self.x < self.grid.offset_x - 20:
            return 'reached_home'
        return None

    def _find_plant_ahead(self):
        for col in range(self.grid.cols):
            p = self.grid.cells[self.row][col]
            if p and hasattr(p, 'hp') and p.hp > 0:
                plant_x = p.rect.centerx
                if self.x - plant_x < 40 and self.x - plant_x > -40:
                    return p
                elif self.x <= plant_x:
                    break
        return None

    def _update_miner(self, dt):
        if self.miner_phase == 'walking_right':
            self.x -= self.speed
            if self.x >= SCREEN_WIDTH - 20:
                self.miner_phase = 'digging_down'
                self.row = self.miner_start_row
                self.y = self.grid.offset_y + self.row * self.grid.cell_h + self.grid.cell_h // 2

        elif self.miner_phase == 'digging_down':
            self.row -= 1
            if self.row < 0:
                self.row = 0
                self.miner_phase = 'walking_left'
                self.y = self.base_y
            else:
                self.y = self.grid.offset_y + self.row * self.grid.cell_h + self.grid.cell_h // 2

        elif self.miner_phase == 'walking_left':
            self.y = self.base_y
            self.row = 0
            self.x -= self.speed

        if self.x < self.grid.offset_x - 20:
            return 'reached_home'
        return None

    def _update_pole(self, dt):
        if not self.pole_jumped and not self.jumping:
            plant = self._find_plant_ahead()
            if plant:
                self.jumping = True
                self.jump_timer = 0
                self.jump_start_x = self.x
                self.jump_target_col = plant.col + 1

        if self.jumping:
            self.jump_timer += dt
            if self.jump_timer < 0.2:
                jump_progress = self.jump_timer / 0.2
                self.y = self.base_y - int(80 * jump_progress)
            elif self.jump_timer < 0.4:
                jump_progress = (self.jump_timer - 0.2) / 0.2
                self.y = self.base_y - int(80 * (1 - jump_progress))
            else:
                self.y = self.base_y
                self.jumping = False
                self.pole_jumped = True
                for c in range(self.grid.cols):
                    p = self.grid.cells[self.row][c]
                    if p and hasattr(p, 'hp') and p.hp > 0:
                        if c >= self.jump_target_col:
                            self.x = p.rect.centerx + 50
                            break
                self.speed = self.base_speed
        else:
            plant_in_way = self._find_plant_ahead()
            if plant_in_way:
                self.attacking = True
                self.eating = True
                self.attack_target = plant_in_way
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
            else:
                self.attacking = False
                self.eating = False
                self.x -= self.speed

        if self.eating:
            self.eat_anim_timer += dt
            self.arm_y = int(5 * (1 if int(self.eat_anim_timer * 6) % 2 == 0 else -1))

        if self.x < self.grid.offset_x - 20:
            return 'reached_home'
        return None

    def take_damage(self, dmg):
        if self.name == 'newspaper' and not self.newspaper_destroyed:
            self.newspaper_hp -= dmg
            if self.newspaper_hp <= 0:
                self.newspaper_destroyed = True
                self.color = (200, 80, 80)
                self.panic_timer = 0
                remaining = abs(self.newspaper_hp)
                self.hp -= remaining
                if self.hp <= 0:
                    self.die()
                    return (True, True)   # (zombie_dead, newspaper_destroyed)
                return (False, True)    # (zombie_not_dead, newspaper_destroyed)
            return (False, False)

        # Football helmet absorbs damage first
        if self.name == 'football' and self.helmet_hp > 0:
            self.helmet_hp -= dmg
            self.shake_active = True
            self.shake_timer = 0.2
            if self.helmet_hp <= 0:
                self.helmet_hp = 0
                # Helmet destroyed — flash and continue
            return (False, False)

        self.hp -= dmg
        if self.hp > 0:
            self.shake_active = True
            self.shake_timer = 0.3
        if self.hp <= 0:
            self.die()
            return (True, False)
        return (False, False)

    def apply_slow(self):
        self.slow_timer = 2.0

    def die(self):
        self.dead = True
        self.death_timer = 0

    def draw(self, surface, scroll_x=0, scroll_y=0):
        if self.dead:
            alpha = max(0, 255 - int(self.death_timer * 500))
            if alpha <= 0:
                return
            x, y = int(self.x - scroll_x), int(self.y - scroll_y)
            temp_surf = pygame.Surface((self.w + 10, self.h + 10), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (*self.color, alpha), (5, 5, self.w, self.h))
            pygame.draw.circle(temp_surf, (180, 180, 180, alpha), (self.w // 2 + 5, 5), 12)
            surface.blit(temp_surf, (x - self.w // 2 - 5, y - self.h // 2 - 5))
            return

        x, y = int(self.x - scroll_x), int(self.y - scroll_y)
        body_y = y + self.arm_y if self.eating else y

        # Apply shake
        if self.shake_active:
            shake_offset = int(math.sin(self.shake_timer * 60) * 5)
            x += shake_offset

        # Miner digging angle
        if self.name == 'miner' and self.miner_phase == 'digging_down':
            temp_surf = pygame.Surface((self.w + 10, self.h + 10), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (*self.color, 255), (5, 5, self.w, self.h))
            pygame.draw.circle(temp_surf, (180, 180, 180), (self.w // 2 + 5, 5), 12)
            pygame.draw.line(temp_surf, (150, 100, 50), (self.w + 5, 5), (self.w + 15, -5), 3)
            surface.blit(temp_surf, (x - self.w // 2 - 5, y - self.h // 2 - 5))
            return

        # Body
        body_rect = pygame.Rect(x - self.w // 2, body_y - self.h // 2, self.w, self.h)
        pygame.draw.rect(surface, self.color, body_rect)

        # Arms
        if self.eating:
            pygame.draw.rect(surface, self.color, (x - self.w // 2 - 8, body_y - self.h // 2 + 5 + self.arm_y, 8, 20))
            pygame.draw.rect(surface, self.color, (x + self.w // 2, body_y - self.h // 2 + 10, 8, 20))
        else:
            bob = int(2 * (self.anim_frame * 2 - 1))
            arm_swing = 8 if self.anim_frame == 0 else -8
            walking_body_y = body_y + bob
            pygame.draw.rect(surface, self.color, (x - self.w // 2 - 8, walking_body_y - 5 + arm_swing, 8, 20))
            pygame.draw.rect(surface, self.color, (x + self.w // 2, walking_body_y - 5 - arm_swing, 8, 20))
            body_y = walking_body_y

        # Head
        head_y = y - self.h // 2 - 10 + (self.arm_y if self.eating else bob)
        pygame.draw.circle(surface, (180, 180, 180), (x, head_y), 12)

        # Type decorations
        if self.name == 'cone':
            pygame.draw.rect(surface, ORANGE, (x - 15, y - self.h // 2 - 25, 30, 15))
        elif self.name == 'bucket':
            pygame.draw.rect(surface, GRAY, (x - 18, y - self.h // 2 - 28, 36, 20))
        elif self.name == 'football':
            helmet_y = y - self.h // 2 - 30
            if self.helmet_hp > self.max_helmet_hp * 0.5:
                pygame.draw.rect(surface, (80, 80, 80), (x - 20, helmet_y, 40, 25))
            elif self.helmet_hp > 0:
                # Cracked helmet
                pygame.draw.rect(surface, (80, 80, 80), (x - 20, helmet_y, 40, 25))
                pygame.draw.line(surface, (40, 40, 40), (x - 10, helmet_y + 2), (x, helmet_y + 20), 2)
                pygame.draw.line(surface, (40, 40, 40), (x + 5, helmet_y + 5), (x - 3, helmet_y + 18), 2)
            # else: helmet destroyed — no helmet drawn, body takes hits
        elif self.name == 'pole':
            if not self.pole_jumped:
                if self.jumping:
                    pygame.draw.line(surface, (139, 90, 43), (x - 30, y - 20), (x + 10, y - 20), 4)
                else:
                    pygame.draw.line(surface, (139, 90, 43), (x + self.w // 2, y - 30), (x + self.w // 2 + 25, y - 30), 4)
        elif self.name == 'newspaper':
            if not self.newspaper_destroyed:
                pygame.draw.rect(surface, (230, 220, 200), (x - 25, y - 15, 20, 25))
                pygame.draw.rect(surface, (200, 200, 180), (x - 25, y - 15, 20, 25), 1)
                pygame.draw.circle(surface, (180, 180, 180), (x - 2, y - self.h // 2 - 10), 12)
            else:
                pygame.draw.circle(surface, (180, 180, 180), (x, y - self.h // 2 - 10), 12)
                pygame.draw.line(surface, (200, 50, 50), (x - 6, y - self.h // 2 - 14), (x - 2, y - self.h // 2 - 11), 2)
                pygame.draw.line(surface, (200, 50, 50), (x + 2, y - self.h // 2 - 11), (x + 6, y - self.h // 2 - 14), 2)
        elif self.name == 'miner':
            pygame.draw.line(surface, (150, 100, 50), (x - self.w // 2 - 5, y - 10), (x - self.w // 2 - 15, y - 25), 4)
            pygame.draw.circle(surface, GRAY, (x - self.w // 2 - 15, y - 25), 5)
        elif self.name == 'ladder':
            if self.has_ladder:
                pygame.draw.rect(surface, YELLOW, (x - self.w // 2 + 3, y - self.h // 2 + 2, 6, self.h - 4))
                for ly in range(y - self.h // 2 + 8, y + self.h // 2 - 2, 10):
                    pygame.draw.line(surface, (180, 140, 0), (x - self.w // 2 + 3, ly), (x - self.w // 2 + 8, ly), 1)

        # Ice slow indicator
        if self.slow_timer > 0:
            pygame.draw.circle(surface, (150, 200, 255), (x, y), 5, 2)
            pygame.draw.circle(surface, (150, 200, 255, 100), (x, body_y), self.w // 2 + 5, 2)

        # Newspaper panic indicator
        if self.newspaper_destroyed:
            panic_font = pygame.font.Font(None, 18)
            txt = panic_font.render('!!', True, (255, 50, 50))
            surface.blit(txt, (x - 8, y - self.h // 2 - 40))

        # HP bar
        if self.hp < self.max_hp:
            bar_w = 40
            bar_h = 5
            bx = x - bar_w // 2
            by = y - self.h // 2 - 35
            pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, GREEN, (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))


def create_zombie(name, x, row, grid):
    return Zombie(name, x, row, grid)
