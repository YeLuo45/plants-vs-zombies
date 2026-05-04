import pygame
from source.constants import *


class Plant(pygame.sprite.Sprite):
    def __init__(self, name, row, col, grid):
        super().__init__()
        self.name = name
        self.row = row
        self.col = col
        self.grid = grid
        cfg = PLANTS[name]
        self.hp = cfg['hp']
        self.max_hp = cfg['hp']
        self.attack = cfg['attack']
        self.attack_interval = cfg['interval']
        self.attack_timer = 0
        self.cooldown = 0
        self.color = cfg['color']
        self.rect = grid.get_cell_rect(row, col)
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.anim_timer = 0
        self.anim_frame = 0
        self.shake_timer = 0
        self.shake_active = False

        # Sunflower
        self.sun_timer = 0
        self.sun_interval = 3.0

        # Potato Mine
        self.armed = False
        self.armed_timer = 0

        # Cherry Bomb / Squash
        self.exploding = False
        self.explode_timer = 0
        self.explode_delay = 0.5

        # Chomper
        self.eating = False
        self.eat_timer = 0
        self.eat_target = None

        # Squash
        self.squash_state = 'waiting'
        self.squash_target = None
        self.squash_damage = 999
        self.squash_jump_timer = 0
        self.squash_land_timer = 0
        self.squash_original_y = self.y

        # Winter Melon
        self.last_shot_col = -1

        # Ice Shroom
        self.ice_fired = False

        # Hypno Shroom
        self.hypno_active = False

        # Ladder (plant can be laddered by ladder zombie)
        self.laddered = False

        # Scaredy Shroom
        self.hidden = False
        self.sun_timer_scaredy = 0
        self.sun_interval_scaredy = 3.0

        # Zapricot - electric glow
        self.electric_timer = 0

        # Cattail - targeting
        self.cattail_target = None

        # Gloom Shroom
        self.spore_released = False

    def update(self, dt, events):
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        if self.cooldown > 0:
            self.cooldown -= dt

        # Shake timer update
        if self.shake_active:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_active = False
                self.shake_timer = 0

        # Sunflower
        if self.name == 'sunflower':
            self.sun_timer += dt
            if self.sun_timer >= self.sun_interval:
                self.sun_timer = 0
                return 'produce_sun'

        # Scaredy Shroom
        if self.name == 'scaredy':
            if not self.hidden:
                self.sun_timer_scaredy += dt
                if self.sun_timer_scaredy >= self.sun_interval_scaredy:
                    self.sun_timer_scaredy = 0
                    return 'produce_sun'
            for z in events:
                if z.get('type') == 'zombie_near' and z.get('row') == self.row:
                    col_dist = abs(z.get('col', 0) - self.col)
                    if col_dist <= 3 and not z.get('dead'):
                        if not self.hidden:
                            self.hidden = True
                        return None
            if self.hidden:
                zombie_nearby = False
                for z in events:
                    if z.get('type') == 'zombie_near' and z.get('row') == self.row:
                        zombie_nearby = True
                        break
                if not zombie_nearby:
                    self.hidden = False

        # Potato Mine — V5: 5.0s armed timer
        if self.name == 'potatomine' and not self.armed:
            self.armed_timer += dt
            if self.armed_timer >= 5.0:
                self.armed = True

        # Cherry Bomb
        if self.name == 'cherrybomb':
            self.explode_timer += dt
            if self.explode_timer >= self.explode_delay and not self.exploding:
                self.exploding = True
                return 'explode'

        # Squash
        if self.name == 'squash':
            return self._update_squash(dt, events)

        # Ice Shroom
        if self.name == 'iceshroom' and not self.ice_fired:
            self.explode_timer += dt
            if self.explode_timer >= 3.0 and not self.ice_fired:
                self.ice_fired = True
                return 'ice_blast'

        # Winter Melon
        if self.name == 'wintermelon':
            if self.attack_interval > 0:
                self.attack_timer += dt
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    return 'shoot'

        # Hypno Shroom
        if self.name == 'hypnoshroom' and self.hypno_active:
            return 'hypnotize'

        # Repeater / peashooter variants
        if self.name in ('peashooter', 'snowpea', 'repeater', 'wintermelon'):
            if self.attack_interval > 0:
                self.attack_timer += dt
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    return 'shoot'

        # Zapricot - 3x3 electric area attack
        if self.name == 'zapricot':
            if self.attack_interval > 0:
                self.attack_timer += dt
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    return 'electric_shot'

        # Cattail - global targeting, always hits
        if self.name == 'cattail':
            if self.attack_interval > 0:
                self.attack_timer += dt
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    return 'spike_shot'

        # Gloom Shroom - one-time spore cloud
        if self.name == 'gloomshroom' and not self.spore_released:
            self.attack_timer += dt
            if self.attack_timer >= 0.5:
                self.spore_released = True
                return 'spore_explode'

        return None

    def _update_squash(self, dt, events):
        if self.squash_state == 'waiting':
            for z in events:
                if z.get('type') == 'zombie_near' and z.get('row') == self.row:
                    col_dist = abs(z.get('col', 0) - self.col)
                    if col_dist <= 4 and not z.get('dead'):
                        self.squash_target = z.get('col', self.col + 3)
                        self.squash_state = 'jumping'
                        self.squash_jump_timer = 0
                        return None
            return None

        elif self.squash_state == 'jumping':
            self.squash_jump_timer += dt
            self.y = self.squash_original_y - 60
            if self.squash_jump_timer >= 0.5:
                self.squash_state = 'falling'
                self.squash_jump_timer = 0
            return None

        elif self.squash_state == 'falling':
            self.squash_jump_timer += dt
            self.y = self.squash_original_y - 60 + int(60 * (self.squash_jump_timer / 0.3))
            if self.squash_jump_timer >= 0.3:
                self.y = self.squash_original_y
                self.squash_state = 'landed'
                self.squash_jump_timer = 0
                return 'squash_land'
            return None

        elif self.squash_state == 'landed':
            self.squash_land_timer += dt
            if self.squash_land_timer >= 0.5:
                self.squash_state = 'done'
                return 'squash_done'
            return None

        elif self.squash_state == 'done':
            self.kill()
            return 'squash_done'

        return None

    def draw(self, surface, scroll_x=0, scroll_y=0):
        x, y = int(self.rect.centerx - scroll_x), int(self.rect.centery - scroll_y)

        # Apply shake offset
        if self.shake_active:
            import math
            shake_offset = int(math.sin(self.shake_timer * 60) * 5)
            x += shake_offset

        # Torchwood (V5) — fire on top
        if self.name == 'torchwood':
            pygame.draw.rect(surface, (101, 67, 33), (x - 20, y - 15, 40, 30))
            import random
            for i in range(3):
                flame_h = 15 + random.randint(0, 10)
                flame_x = x - 12 + i * 12
                flame_y = y - 15
                pygame.draw.circle(surface, (255, 100 + i * 30, 0), (flame_x, flame_y), 8)
                pygame.draw.circle(surface, (255, 200, 0), (flame_x, flame_y + 3), 5)
            if self.hp < self.max_hp:
                self._draw_hp_bar(surface, x, y)
            return

        # Scaredy hidden state
        if self.name == 'scaredy' and self.hidden:
            pygame.draw.circle(surface, self.color, (x, y + 5), 12)
            return

        # Squash jumping/falling animation
        squash_y_offsets = {
            'waiting': 0, 'jumping': -60, 'falling': -60, 'landed': 0, 'done': 0,
        }
        if self.name == 'squash':
            offset = squash_y_offsets.get(self.squash_state, 0)
            y = self.rect.centery - scroll_y + offset

        # Ice Shroom (pulsing glow when ready)
        if self.name == 'iceshroom' and not self.ice_fired:
            pulse = 0.8 + 0.2 * (self.anim_frame * 2 - 1)
            glow_r = int(25 * pulse)
            pygame.draw.circle(surface, ICE_BLUE, (x, y), glow_r, 2)

        # Winter Melon (draw melon wedge)
        if self.name == 'wintermelon':
            pygame.draw.circle(surface, WATERMELON_COLOR, (x, y), 22)
            pygame.draw.arc(surface, (30, 100, 30), (x - 22, y - 22, 44, 44), 0, 3.14, 3)
        elif self.name == 'hypnoshroom':
            pygame.draw.circle(surface, PURPLE, (x, y), 22)
            pygame.draw.circle(surface, (220, 180, 255), (x, y), 10)
        elif self.name == 'squash':
            pygame.draw.circle(surface, self.color, (x, y), 24)
            if self.squash_state == 'waiting':
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
            elif self.squash_state in ('jumping', 'falling'):
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
                pygame.draw.line(surface, BLACK, (x - 10, y - 10), (x - 3, y - 7), 2)
                pygame.draw.line(surface, BLACK, (x + 3, y - 7), (x + 10, y - 10), 2)
            elif self.squash_state == 'landed':
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
        elif self.name == 'iceshroom':
            pygame.draw.circle(surface, self.color, (x, y), 22)
            pygame.draw.line(surface, WHITE, (x - 8, y), (x + 8, y), 1)
            pygame.draw.line(surface, WHITE, (x, y - 8), (x, y + 8), 1)
        elif self.name == 'scaredy':
            pygame.draw.circle(surface, self.color, (x, y), 20)
            pygame.draw.circle(surface, WHITE, (x - 5, y - 3), 6)
            pygame.draw.circle(surface, WHITE, (x + 5, y - 3), 6)
            pygame.draw.circle(surface, BLACK, (x - 5, y - 3), 3)
            pygame.draw.circle(surface, BLACK, (x + 5, y - 3), 3)
        elif self.name == 'zapricot':
            # Electric yellow with glow effect
            import random
            glow = 5 + int(3 * (self.anim_frame * 2 - 1))
            pygame.draw.circle(surface, (255, 255, 100), (x, y), 22 + glow, 2)
            pygame.draw.circle(surface, self.color, (x, y), 22)
            # Electric arc lines
            for i in range(3):
                angle = self.anim_frame * 2 + i * 2.1
                ex = x + int(math.cos(angle) * 18)
                ey = y + int(math.sin(angle) * 18)
                pygame.draw.line(surface, (255, 255, 200), (x, y), (ex, ey), 2)
        elif self.name == 'cattail':
            # Cattail - green stalk with cattail top
            pygame.draw.circle(surface, self.color, (x, y), 22)
            # Cattail spike at top
            pygame.draw.ellipse(surface, (120, 80, 40), (x - 4, y - 35, 8, 18))
            # Leaves
            pygame.draw.line(surface, (50, 150, 50), (x, y + 10), (x - 18, y + 30), 3)
            pygame.draw.line(surface, (50, 150, 50), (x, y + 10), (x + 18, y + 30), 3)
        elif self.name == 'gloomshroom':
            # Gloom shroom - dark poisonous mushroom
            # Cap
            pygame.draw.circle(surface, (80, 120, 40), (x, y - 5), 22)
            pygame.draw.circle(surface, (60, 100, 30), (x, y - 5), 22, 2)
            # Spots
            pygame.draw.circle(surface, (120, 180, 60), (x - 8, y - 10), 4)
            pygame.draw.circle(surface, (120, 180, 60), (x + 6, y - 8), 3)
            pygame.draw.circle(surface, (120, 180, 60), (x, y - 2), 3)
            # Stem
            pygame.draw.rect(surface, (180, 160, 140), (x - 6, y + 5, 12, 18))
        elif self.name == 'potatomine':
            if not self.armed:
                pygame.draw.circle(surface, (101, 67, 33), (x, y), 10)
            else:
                pygame.draw.ellipse(surface, (205, 165, 50), (x - 15, y - 10, 30, 20))
                pygame.draw.circle(surface, BLACK, (x - 5, y - 3), 3)
                pygame.draw.circle(surface, BLACK, (x + 5, y - 3), 3)
        else:
            pygame.draw.circle(surface, self.color, (x, y), 22)

        if self.hp < self.max_hp:
            self._draw_hp_bar(surface, x, y)

    def _draw_hp_bar(self, surface, x, y):
        bar_w = 40
        bar_h = 5
        bx = x - bar_w // 2
        by = y - 35
        pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, GREEN, (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp > 0:
            self.shake_active = True
            self.shake_timer = 0.3
        return self.hp <= 0

    def try_eat_zombie(self, zombie):
        if self.name != 'chomper':
            return False
        if not self.eating and zombie and zombie.row == self.row:
            dist = zombie.x - self.rect.centerx
            if 0 < dist < 60:
                self.eating = True
                self.eat_timer = 0
                self.eat_target = zombie
                return True
        return False


def create_plant(name, row, col, grid):
    return Plant(name, row, col, grid)
