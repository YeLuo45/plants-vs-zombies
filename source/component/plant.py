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
        self.squash_state = 'waiting'  # waiting -> jumping -> falling -> landed
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

        # Scaredy Shroom
        self.hidden = False
        self.sun_timer_scaredy = 0
        self.sun_interval_scaredy = 3.0

    def update(self, dt, events):
        self.anim_timer += dt
        if self.anim_timer >= 0.15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2

        if self.cooldown > 0:
            self.cooldown -= dt

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
            # Check if zombie nearby -> hide
            for z in events:
                if z.get('type') == 'zombie_near' and z.get('row') == self.row:
                    col_dist = abs(z.get('col', 0) - self.col)
                    if col_dist <= 3 and not z.get('dead'):
                        if not self.hidden:
                            self.hidden = True
                        return None
            if self.hidden:
                # Zombies gone?
                zombie_nearby = False
                for z in events:
                    if z.get('type') == 'zombie_near' and z.get('row') == self.row:
                        zombie_nearby = True
                        break
                if not zombie_nearby:
                    self.hidden = False

        # Potato Mine
        if self.name == 'potatomine' and not self.armed:
            self.armed_timer += dt
            if self.armed_timer >= 3.0:
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
                    # Find zombie in range (every 2 columns ahead)
                    return 'shoot'

        # Hypno Shroom (eaten by zombie -> hypnotize)
        if self.name == 'hypnoshroom' and self.hypno_active:
            return 'hypnotize'

        # Repeater (and peashooter variants)
        if self.name in ('peashooter', 'snowpea', 'repeater', 'wintermelon'):
            if self.attack_interval > 0:
                self.attack_timer += dt
                if self.attack_timer >= self.attack_interval:
                    self.attack_timer = 0
                    return 'shoot'

        # Chomper
        if self.name == 'chomper' and self.eating:
            self.eat_timer += dt
            if self.eat_timer >= 0.5:
                self.eating = False
                self.eat_timer = 0
                if self.eat_target and self.eat_target.hp > 0:
                    self.eat_target.hp = 0
                    self.eat_target = None
                return 'chomp_done'

        return None

    def _update_squash(self, dt, events):
        if self.squash_state == 'waiting':
            # Find zombie 2-4 columns ahead
            target = None
            for col in range(self.col + 2, min(self.col + 5, GRID_COLS)):
                for z in events:
                    if z.get('type') == 'zombie_near' and z.get('col') == col and z.get('row') == self.row and not z.get('dead'):
                        target = z
                        break
                if target:
                    break
            if target:
                self.squash_target = target
                self.squash_state = 'jumping'
                self.squash_jump_timer = 0
            return None

        elif self.squash_state == 'jumping':
            self.squash_jump_timer += dt
            # Rise up above the grid
            jump_progress = self.squash_jump_timer / 0.4
            self.y = self.squash_original_y - int(60 * jump_progress) if jump_progress < 1.0 else self.squash_original_y - 60
            if self.squash_jump_timer >= 0.4:
                self.squash_state = 'falling'
                self.squash_jump_timer = 0
            return None

        elif self.squash_state == 'falling':
            self.squash_jump_timer += dt
            # Fall down toward target
            fall_progress = self.squash_jump_timer / 0.3
            if fall_progress >= 1.0:
                self.squash_state = 'landed'
                self.squash_jump_timer = 0
                return 'squash_land'
            return None

        elif self.squash_state == 'landed':
            self.squash_land_timer += dt
            if self.squash_land_timer >= 0.5:
                # Deal damage to zombies in 2-cell radius
                self.squash_state = 'done'
                return 'squash_damage'
            return None

        return None

    def draw(self, surface):
        x, y = self.rect.centerx, int(self.y)

        # Scaredy hidden state
        if self.name == 'scaredy' and self.hidden:
            # Draw shrunken/crouched version
            pygame.draw.circle(surface, self.color, (x, y + 5), 12)
            return

        # Squash jumping/falling animation
        squash_y_offsets = {
            'waiting': 0,
            'jumping': -60,
            'falling': -60,
            'landed': 0,
            'done': 0,
        }
        if self.name == 'squash':
            offset = squash_y_offsets.get(self.squash_state, 0)
            y = self.rect.centery + offset

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
            # Draw spiral on top
            pygame.draw.circle(surface, PURPLE, (x, y), 22)
            pygame.draw.circle(surface, (220, 180, 255), (x, y), 10)
        elif self.name == 'squash':
            # Draw as heavy green circle
            pygame.draw.circle(surface, self.color, (x, y), 24)
            # Sad face when waiting
            if self.squash_state == 'waiting':
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
            elif self.squash_state in ('jumping', 'falling'):
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
                # Angry eyebrows
                pygame.draw.line(surface, BLACK, (x - 10, y - 10), (x - 3, y - 7), 2)
                pygame.draw.line(surface, BLACK, (x + 3, y - 7), (x + 10, y - 10), 2)
            elif self.squash_state == 'landed':
                # Impact face
                pygame.draw.circle(surface, BLACK, (x - 6, y - 4), 3)
                pygame.draw.circle(surface, BLACK, (x + 6, y - 4), 3)
        elif self.name == 'iceshroom':
            pygame.draw.circle(surface, self.color, (x, y), 22)
            # Snowflake-like markings
            pygame.draw.line(surface, WHITE, (x - 8, y), (x + 8, y), 1)
            pygame.draw.line(surface, WHITE, (x, y - 8), (x, y + 8), 1)
        elif self.name == 'scaredy':
            # Wide scared eyes
            pygame.draw.circle(surface, self.color, (x, y), 20)
            pygame.draw.circle(surface, WHITE, (x - 5, y - 3), 6)
            pygame.draw.circle(surface, WHITE, (x + 5, y - 3), 6)
            pygame.draw.circle(surface, BLACK, (x - 5, y - 3), 3)
            pygame.draw.circle(surface, BLACK, (x + 5, y - 3), 3)
        else:
            pygame.draw.circle(surface, self.color, (x, y), 22)

        # HP bar (only if damaged)
        if self.hp < self.max_hp:
            bar_w = 40
            bar_h = 5
            bx = self.rect.centerx - bar_w // 2
            by = y - 35
            pygame.draw.rect(surface, RED, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, GREEN, (bx, by, int(bar_w * self.hp / self.max_hp), bar_h))

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            return True
        return False

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
