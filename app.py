import pygame
import math
import sys
import random

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 640, 640
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (100, 200, 255)
PATH_COLOR = (245, 245, 245)
DARK_GRAY = (50, 50, 50)
DISABLED_GRAY = (80, 80, 80)

SPRITE_SIZE = 50
ANIMATION_SPEED = 8

# Настройки игры
START_MONEY = 300
ENEMY_BASE_HEALTH = 100
ENEMY_BASE_SPEED = 1.0
BULLET_SPEED = 5
ENEMY_BULLET_SPEED = 7
TOWER_BASE_COST = {"Стандартная": 100, "Быстрая": 150, "Сильная": 200}
TOWER_UPGRADE_COST = {
    "Стандартная": [100, 150],
    "Быстрая": [100, 100],
    "Сильная": [150, 200],
}
TOWER_MAX_LEVEL = 3

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Защита Башни")

clock = pygame.time.Clock()

# Путь для врагов
path = [
    (640, 130),
    (130, 130),
    (50, 260),
    (130, 350),
    (510, 350),
    (590, 463),
    (510, 576),
    (0, 576),
]

# Места для башен
tower_zones = [
    pygame.Rect(42, 42, 50, 50),
    pygame.Rect(180, 215, 50, 50),
    pygame.Rect(180, 430, 50, 50),
    pygame.Rect(480, 215, 50, 50),
    pygame.Rect(400, 430, 50, 50),
]

# Финиш
finish_zone = pygame.Rect(0, 520, 80, 80)

# Фон
try:
    background_img = pygame.image.load("background.png")
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except:
    background_img = None


class TowerType:
    def __init__(self, name, color, range_, fire_rate, damage, radius):
        self.name = name
        self.color = color
        self.range = range_
        self.fire_rate = fire_rate
        self.damage = damage
        self.radius = radius


tower_types = {
    "Стандартная": TowerType("Стандартная", BLUE, 120, 60, 25, 20),
    "Быстрая": TowerType("Быстрая", CYAN, 100, 20, 10, 15),
    "Сильная": TowerType("Сильная", MAGENTA, 150, 90, 50, 25),
}


def get_tower_stats(tower_type_name, level):
    base = tower_types[tower_type_name]
    range_ = base.range + (level - 1) * 10
    damage = int(base.damage * (1 + 0.5 * (level - 1)))
    fire_rate = max(5, int(base.fire_rate / (1 + 0.5 * (level - 1))))
    radius = base.radius + (level - 1) * 5
    return range_, fire_rate, damage, radius


def draw_path():
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(GREEN)
        for i in range(len(path) - 1):
            pygame.draw.line(screen, PATH_COLOR, path[i], path[i + 1], 40)
        for rect in tower_zones:
            pygame.draw.rect(screen, RED, rect)
        pygame.draw.rect(screen, LIGHT_BLUE, finish_zone)


class EnemyAnimation:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.current_animation = "walk"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = ANIMATION_SPEED
        self.flip = False

        try:
            self.sprite_sheet = pygame.image.load("terrorist.png").convert_alpha()
        except:
            self.sprite_sheet = pygame.Surface((SPRITE_SIZE * 5, SPRITE_SIZE * 2), pygame.SRCALPHA)
            pygame.draw.rect(self.sprite_sheet, RED, (0, 0, SPRITE_SIZE * 5, SPRITE_SIZE * 2), 1)

        self.animations = {
            "walk": (0, 4, 0, True),   # start_col, frame_count, row, loop
            "death": (0, 5, 1, False)   # start_col, frame_count, row, loop
        }
        self.frames = {}
        self._load_frames()

    def _load_frames(self):
        for anim_name, (start_col, frame_count, row, _) in self.animations.items():
            frames = []
            for i in range(frame_count):
                frame = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
                frame.blit(self.sprite_sheet, (0, 0),
                          ((start_col + i) * SPRITE_SIZE, row * SPRITE_SIZE, SPRITE_SIZE, SPRITE_SIZE))
                frames.append(frame)
            self.frames[anim_name] = frames

    def change_animation(self, new_animation):
        if new_animation != self.current_animation and new_animation in self.frames:
            self.current_animation = new_animation
            self.current_frame = 0
            self.animation_timer = 0

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            anim_data = self.animations[self.current_animation]
            frame_count = anim_data[1]
            loop = anim_data[3]
            
            if self.current_frame < frame_count - 1:
                self.current_frame += 1
            elif loop:
                self.current_frame = 0
            self.animation_timer = 0

    def draw(self, screen, angle):
        if self.current_animation not in self.frames:
            return

        frame = self.frames[self.current_animation][self.current_frame]
        angle_deg = math.degrees(angle)
        rotated_frame = pygame.transform.rotate(frame, -angle_deg)
        screen.blit(rotated_frame, 
                   (self.x - rotated_frame.get_width() // 2,
                    self.y - rotated_frame.get_height() // 2))


class Enemy:
    def __init__(self, health, speed):
        self.path = path
        self.path_pos = 0
        self.x, self.y = self.path[0]
        self.speed = speed
        self.health = health
        self.max_health = health
        self.radius = 15
        self.alive = True
        self.dying = False
        self.dead = False

        self.attack_cooldown = 90
        self.attack_timer = random.randint(0, self.attack_cooldown)
        self.attack_damage = 5 + random.randint(-2, 2)
        self.attack_range = 120
        self.target = None
        self.attack_effect_timer = 0
        self.burst_count = 0
        self.burst_delay = 0

        self.direction = 0
        self.shooting_direction = 0
        self.is_attacking = False

        self.animation = EnemyAnimation()
        self.animation.x = self.x
        self.animation.y = self.y
        self.animation.change_animation("walk")

    def update(self, towers, enemy_bullets):
        if self.dead:
            return False, False
        
        if self.dying:
            if self.animation.current_animation != "death":
                self.animation.change_animation("death")
            
            self.animation.update()
            
            if (self.animation.current_animation == "death" and 
                self.animation.current_frame == len(self.animation.frames["death"]) - 1):
                self.dead = True
                self.alive = False
            return True, False

        if self.health <= 0 and not self.dying:
            self.dying = True
            return True, False

        if self.path_pos + 1 >= len(self.path):
            if finish_zone.collidepoint(self.x, self.y):
                self.alive = False
                return False, True
            else:
                self.alive = False
                return False, False

        target_x, target_y = self.path[self.path_pos + 1]
        vec_x = target_x - self.x
        vec_y = target_y - self.y
        dist = math.hypot(vec_x, vec_y)

        if dist > 0:
            self.direction = math.atan2(vec_y, vec_x)
            self.is_attacking = False

        if dist == 0:
            self.path_pos += 1
        else:
            move_x = (vec_x / dist) * self.speed
            move_y = (vec_y / dist) * self.speed
            self.x += move_x
            self.y += move_y
            if math.hypot(target_x - self.x, target_y - self.y) < self.speed:
                self.path_pos += 1

        self.animation.x = self.x
        self.animation.y = self.y

        # Атака
        self.attack_timer += 1
        if self.attack_effect_timer > 0:
            self.attack_effect_timer -= 1
        if self.burst_delay > 0:
            self.burst_delay -= 1

        if self.attack_timer >= self.attack_cooldown and self.burst_count < 3 and self.burst_delay <= 0:
            if self.target is None or not self.target.alive or \
                    math.hypot(self.target.x - self.x, self.target.y - self.y) > self.attack_range:
                self.target = None
                min_dist = float('inf')
                for tower in towers:
                    if not tower.alive:
                        continue
                    dist_to_tower = math.hypot(tower.x - self.x, tower.y - self.y)
                    if dist_to_tower <= self.attack_range and dist_to_tower < min_dist:
                        min_dist = dist_to_tower
                        self.target = tower

            if self.target:
                dx = self.target.x - self.x
                dy = self.target.y - self.y
                self.shooting_direction = math.atan2(dy, dx)
                self.is_attacking = True

                enemy_bullets.append(EnemyBullet(self.x, self.y, self.target, self.attack_damage))
                self.attack_effect_timer = 5
                self.burst_count += 1
                self.burst_delay = 5

                if self.burst_count >= 3:
                    self.attack_timer = 0
                    self.burst_count = 0
                    self.is_attacking = False

        if not self.dying:
            self.animation.change_animation("walk")
            self.animation.update()
        return True, False

    def draw(self):
        if self.dead:
            return
            
        if self.is_attacking:
            self.animation.draw(screen, self.shooting_direction)
        else:
            self.animation.draw(screen, self.direction)

        if self.attack_effect_timer > 0:
            s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            alpha = 150 * self.attack_effect_timer / 10
            pygame.draw.circle(s, (255, 255, 0, alpha), (self.radius * 2, self.radius * 2), self.radius * 2)
            screen.blit(s, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))

        if not self.dying:
            health_bar_width = 30
            health_bar_height = 5
            health_ratio = max(self.health / self.max_health, 0)
            pygame.draw.rect(screen, RED, (self.x - health_bar_width // 2, self.y - self.radius - 10,
                                         health_bar_width, health_bar_height))
            pygame.draw.rect(screen, GREEN, (self.x - health_bar_width // 2, self.y - self.radius - 10,
                                           int(health_bar_width * health_ratio), health_bar_height))


class TowerAnimation:
    def __init__(self, tower_type):
        self.x = 0
        self.y = 0
        self.tower_type = tower_type
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 5

        self.current_animation = "stance"
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = ANIMATION_SPEED

        try:
            self.sprite_sheet = pygame.image.load(f"{tower_type}.png").convert_alpha()
        except:
            self.sprite_sheet = pygame.Surface((SPRITE_SIZE * 5, SPRITE_SIZE), pygame.SRCALPHA)
            color = BLUE if tower_type == "standart" else CYAN if tower_type == "speed" else MAGENTA
            pygame.draw.rect(self.sprite_sheet, color, (0, 0, SPRITE_SIZE * 5, SPRITE_SIZE), 1)

        self.animations = {
            "shoot": (0, 4),
            "stance": (4, 1)
        }
        self.frames = {}
        self._load_frames()

    def _load_frames(self):
        for anim_name, (start_col, frame_count) in self.animations.items():
            frames = []
            for i in range(frame_count):
                frame = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
                frame.blit(self.sprite_sheet, (0, 0),
                           ((start_col + i) * SPRITE_SIZE, 0, SPRITE_SIZE, SPRITE_SIZE))
                frames.append(frame)
            self.frames[anim_name] = frames

    def rotate_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        self.target_angle = math.degrees(math.atan2(-dy, dx))

    def change_animation(self, new_animation):
        if new_animation != self.current_animation and new_animation in self.frames:
            self.current_animation = new_animation
            self.current_frame = 0
            self.animation_timer = 0

    def update(self):
        angle_diff = (self.target_angle - self.angle + 180) % 360 - 180
        if abs(angle_diff) > self.rotation_speed:
            self.angle += self.rotation_speed if angle_diff > 0 else -self.rotation_speed
        else:
            self.angle = self.target_angle

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames[self.current_animation])
            self.animation_timer = 0

    def draw(self, screen):
        if self.current_animation not in self.frames or not self.frames[self.current_animation]:
            return

        frame = self.frames[self.current_animation][self.current_frame]
        rotated_frame = pygame.transform.rotate(frame, self.angle)
        screen.blit(rotated_frame, (self.x - rotated_frame.get_width() // 2,
                                    self.y - rotated_frame.get_height() // 2))


class Tower:
    def __init__(self, x, y, zone_rect, tower_type_name):
        self.x = x
        self.y = y
        self.zone_rect = zone_rect
        self.type_name = tower_type_name
        self.level = 1
        self.range, self.fire_rate, self.damage, self.radius = get_tower_stats(tower_type_name, self.level)
        self.timer = 0
        self.color = tower_types[tower_type_name].color
        self.max_health = 100 + 50 * (self.level - 1)
        self.health = self.max_health
        self.alive = True

        sprite_name = "standart" if tower_type_name == "Стандартная" else "speed" if tower_type_name == "Быстрая" else "strong"
        self.animation = TowerAnimation(sprite_name)
        self.animation.x = self.x
        self.animation.y = self.y
        self.shooting = False
        self.shoot_timer = 0

    def update(self, enemies, bullets):
        if not self.alive:
            return

        self.timer += 1
        self.shoot_timer += 1

        if self.shooting and self.shoot_timer > 10:
            self.shooting = False
            self.animation.change_animation("stance")

        target = None
        min_dist = float('inf')
        for enemy in enemies:
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.range and enemy.alive and not enemy.dying:
                if dist < min_dist:
                    min_dist = dist
                    target = enemy

        if target:
            self.animation.rotate_towards(target.x, target.y)

        if self.timer >= self.fire_rate and target:
            bullets.append(Bullet(self.x, self.y, target, self.damage))
            self.timer = 0
            self.shooting = True
            self.shoot_timer = 0
            self.animation.change_animation("shoot")

        self.animation.update()

    def draw(self):
        if not self.alive:
            return

        self.animation.draw(screen)

        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (self.range, self.range), self.range)
        screen.blit(s, (self.x - self.range, self.y - self.range))

        health_bar_width = 40
        health_bar_height = 6
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(screen, RED, (self.x - health_bar_width // 2, self.y + SPRITE_SIZE // 2 + 5,
                                     health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - health_bar_width // 2, self.y + SPRITE_SIZE // 2 + 5,
                                       int(health_bar_width * health_ratio), health_bar_height))

        font = pygame.font.SysFont(None, 18)
        lvl_text = font.render(f"lv{self.level}", True, BLACK)
        screen.blit(lvl_text, (self.x - lvl_text.get_width() // 2, self.y - lvl_text.get_height() // 2))

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False

    def upgrade(self, money):
        if self.level >= TOWER_MAX_LEVEL:
            return False, money
        cost = TOWER_UPGRADE_COST[self.type_name][self.level - 1]
        if money >= cost:
            self.level += 1
            self.range, self.fire_rate, self.damage, self.radius = get_tower_stats(self.type_name, self.level)
            self.max_health = 100 + 50 * (self.level - 1)
            self.health = self.max_health
            money -= cost
            return True, money
        return False, money

    def sell_price(self):
        base_cost = TOWER_BASE_COST[self.type_name]
        upgrades_cost = sum(TOWER_UPGRADE_COST[self.type_name][:self.level - 1]) if self.level > 1 else 0
        return (base_cost + upgrades_cost) // 2

    def can_sell(self):
        return self.health >= self.max_health * 0.25


class Bullet:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.speed = BULLET_SPEED
        self.radius = 5
        self.damage = damage
        self.alive = True
        self.life_timer = 0
        self.max_life = 120

    def update(self):
        if not self.target.alive:
            self.alive = False
            return
        vec_x = self.target.x - self.x
        vec_y = self.target.y - self.y
        dist = math.hypot(vec_x, vec_y)
        if dist == 0:
            self.hit_target()
            return
        move_x = (vec_x / dist) * self.speed
        move_y = (vec_y / dist) * self.speed
        self.x += move_x
        self.y += move_y
        if math.hypot(self.target.x - self.x, self.target.y - self.y) < self.speed:
            self.hit_target()
        self.life_timer += 1
        if self.life_timer > self.max_life:
            self.alive = False

    def hit_target(self):
        self.target.health -= self.damage
        if self.target.health <= 0:
            self.target.alive = False
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)


class EnemyBullet:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.speed = ENEMY_BULLET_SPEED
        self.radius = 5
        self.damage = damage
        self.alive = True
        self.life_timer = 0
        self.max_life = 180
        self.color = (255, 100, 100)
        self.trail = []
        self.max_trail = 5

    def update(self):
        if not self.target.alive:
            self.alive = False
            return

        self.trail.append((self.x, self.y))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

        vec_x = self.target.x - self.x
        vec_y = self.target.y - self.y
        dist = math.hypot(vec_x, vec_y)

        if dist < self.speed:
            self.hit_target()
            return

        if dist > 0:
            spread = 0.2
            move_x = (vec_x / dist) * self.speed + random.uniform(-spread, spread)
            move_y = (vec_y / dist) * self.speed + random.uniform(-spread, spread)
            self.x += move_x
            self.y += move_y

        self.life_timer += 1
        if self.life_timer > self.max_life:
            self.alive = False

    def hit_target(self):
        self.target.health -= self.damage
        if self.target.health <= 0:
            self.target.alive = False
        self.alive = False

    def draw(self):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            radius = int(self.radius * (i / len(self.trail)))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
            screen.blit(s, (int(tx - radius), int(ty - radius)))

        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

        if self.life_timer < 5:
            s = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 100, 150), (self.radius * 2, self.radius * 2), self.radius * 2)
            screen.blit(s, (int(self.x - self.radius * 2), int(self.y - self.radius * 2)))


class Corpse:
    def __init__(self, x, y, radius, color, lifetime=180):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.lifetime = lifetime
        self.timer = 0
        self.alive = True

    def update(self):
        self.timer += 1
        if self.timer >= self.lifetime:
            self.alive = False

    def draw(self):
        s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        alpha = max(0, 150 - int(150 * (self.timer / self.lifetime)))
        pygame.draw.circle(s, (*self.color[:3], alpha), (self.radius, self.radius), self.radius)
        screen.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))


class TowerMenu:
    def __init__(self, tower):
        self.tower = tower
        self.width = 120
        self.height = 70
        self.padding = 5
        self.x = tower.x + tower.radius + 10
        self.y = tower.y - self.height // 2
        if self.x + self.width > WIDTH:
            self.x = tower.x - tower.radius - 10 - self.width
        if self.y < 0:
            self.y = 0
        elif self.y + self.height > HEIGHT:
            self.y = HEIGHT - self.height

        self.font = pygame.font.SysFont(None, 20)
        self.buttons = {
            "upgrade": pygame.Rect(self.x + self.padding, self.y + self.padding, self.width - 2 * self.padding, 30),
            "sell": pygame.Rect(self.x + self.padding, self.y + 35, self.width - 2 * self.padding, 30)
        }

    def draw(self, screen):
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2, border_radius=5)

        upgrade_text = "Улучшить"
        if self.tower.level >= TOWER_MAX_LEVEL:
            upgrade_text = "Макс. уровень"
            upgrade_color = DISABLED_GRAY
        else:
            cost = TOWER_UPGRADE_COST[self.tower.type_name][self.tower.level - 1]
            upgrade_text += f" ({cost})"
            upgrade_color = BLUE
        upgrade_surf = self.font.render(upgrade_text, True, WHITE)
        pygame.draw.rect(screen, upgrade_color, self.buttons["upgrade"], border_radius=3)
        screen.blit(upgrade_surf, (self.buttons["upgrade"].x + (self.buttons["upgrade"].width - upgrade_surf.get_width()) // 2,
                                 self.buttons["upgrade"].y + (self.buttons["upgrade"].height - upgrade_surf.get_height()) // 2))

        sell_price = self.tower.sell_price()
        sell_text = f"Продать ({sell_price})"
        sell_surf = self.font.render(sell_text, True, WHITE)

        if not self.tower.can_sell():
            sell_color = DISABLED_GRAY
            warning_surf = self.font.render("Слишком повреждена", True, RED)
        else:
            sell_color = RED
            warning_surf = None

        pygame.draw.rect(screen, sell_color, self.buttons["sell"], border_radius=3)
        screen.blit(sell_surf, (self.buttons["sell"].x + (self.buttons["sell"].width - sell_surf.get_width()) // 2,
                              self.buttons["sell"].y + (self.buttons["sell"].height - sell_surf.get_height()) // 2))

        if warning_surf:
            screen.blit(warning_surf, (self.x, self.y + self.height + 2))

    def handle_event(self, event, money):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.buttons["upgrade"].collidepoint(mx, my):
                if self.tower.level >= TOWER_MAX_LEVEL:
                    return None, money
                cost = TOWER_UPGRADE_COST[self.tower.type_name][self.tower.level - 1]
                if money >= cost:
                    upgraded, money = self.tower.upgrade(money)
                    return "upgrade", money
                else:
                    return None, money
            elif self.buttons["sell"].collidepoint(mx, my):
                if self.tower.can_sell():
                    money += self.tower.sell_price()
                    self.tower.alive = False
                    return "sell", money
                else:
                    return None, money
        return None, money


class WaveText:
    def __init__(self, wave_number):
        self.wave_number = wave_number
        self.font = pygame.font.SysFont(None, 64, bold=False)
        self.alpha = 0
        self.max_alpha = 255
        self.fade_in_speed = 10
        self.display_time = 60
        self.timer = 0
        self.finished = False

        self.text_surface = self.font.render(f"Волна {self.wave_number}", True, RED)
        self.text_surface.set_alpha(self.alpha)
        self.rect = self.text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    def update(self):
        if self.alpha < self.max_alpha and self.timer == 0:
            self.alpha += self.fade_in_speed
            if self.alpha > self.max_alpha:
                self.alpha = self.max_alpha
            self.text_surface.set_alpha(self.alpha)
        else:
            self.timer += 1
            if self.timer > self.display_time:
                self.finished = True

    def draw(self, screen):
        screen.blit(self.text_surface, self.rect)


def main():
    running = True
    enemies = []
    towers = []
    bullets = []
    enemy_bullets = []
    corpses = []
    spawn_timer = 0
    spawn_interval = 120
    money = START_MONEY
    lives = 10
    font = pygame.font.SysFont(None, 20)
    selected_tower_type_name = "Стандартная"
    tower_menu = None

    current_wave = 1
    enemies_spawned = 0
    enemies_per_wave = 10
    wave_in_progress = False
    wave_cooldown = 60
    wave_cooldown_timer = wave_cooldown

    wave_text = None

    while running:
        clock.tick(FPS)
        draw_path()

        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_tower_type_name = "Стандартная"
                    tower_menu = None
                elif event.key == pygame.K_2:
                    selected_tower_type_name = "Быстрая"
                    tower_menu = None
                elif event.key == pygame.K_3:
                    selected_tower_type_name = "Сильная"
                    tower_menu = None
                elif event.key == pygame.K_ESCAPE:
                    if tower_menu:
                        tower_menu = None
                    else:
                        running = False
                elif event.key == pygame.K_DELETE:
                    for tower in towers:
                        if tower.zone_rect.collidepoint(mx, my) and tower.alive:
                            if tower.can_sell():
                                money += tower.sell_price()
                                tower.alive = False
                                tower_menu = None
                            break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if tower_menu:
                        action, money = tower_menu.handle_event(event, money)
                        if action == "sell":
                            tower_menu = None
                        else:
                            mx_, my_ = event.pos
                            tower_rect = pygame.Rect(
                                tower_menu.tower.x - tower_menu.tower.radius,
                                tower_menu.tower.y - tower_menu.tower.radius,
                                tower_menu.tower.radius * 2,
                                tower_menu.tower.radius * 2,
                            )
                            if not tower_rect.collidepoint(mx_, my_):
                                if not (
                                    tower_menu.x <= mx_ <= tower_menu.x + tower_menu.width and
                                    tower_menu.y <= my_ <= tower_menu.y + tower_menu.height
                                ):
                                    tower_menu = None
                    else:
                        clicked_tower = None
                        for tower in towers:
                            tower_rect = pygame.Rect(
                                tower.x - tower.radius,
                                tower.y - tower.radius,
                                tower.radius * 2,
                                tower.radius * 2,
                            )
                            if tower.alive and tower_rect.collidepoint(mx, my):
                                clicked_tower = tower
                                break
                        if clicked_tower:
                            tower_menu = TowerMenu(clicked_tower)
                        else:
                            for zone_rect in tower_zones:
                                if zone_rect.collidepoint(mx, my):
                                    zone_taken = False
                                    for tower in towers:
                                        if tower.zone_rect == zone_rect and tower.alive:
                                            zone_taken = True
                                            break
                                    if not zone_taken:
                                        cost = TOWER_BASE_COST[selected_tower_type_name]
                                        if money >= cost:
                                            cx = zone_rect.x + zone_rect.width // 2
                                            cy = zone_rect.y + zone_rect.height // 2
                                            towers.append(
                                                Tower(cx, cy, zone_rect, selected_tower_type_name)
                                            )
                                            money -= cost
                                            tower_menu = None
                                    break
                elif event.button == 3:
                    clicked_tower = None
                    for tower in towers:
                        tower_rect = pygame.Rect(
                            tower.x - tower.radius,
                            tower.y - tower.radius,
                            tower.radius * 2,
                            tower.radius * 2,
                        )
                        if tower.alive and tower_rect.collidepoint(mx, my):
                            clicked_tower = tower
                            break
                    if clicked_tower:
                        tower_menu = TowerMenu(clicked_tower)

        # Волны врагов
        if not wave_in_progress:
            wave_cooldown_timer -= 1
            if wave_cooldown_timer <= 0:
                wave_in_progress = True
                enemies_spawned = 0
                enemies_per_wave = 10 + (current_wave - 1) * 5
                spawn_timer = spawn_interval
                wave_text = WaveText(current_wave)
        else:
            spawn_timer += 1
            spawn_interval = max(30, 120 - (current_wave - 1) * 10)
            enemy_health = int(ENEMY_BASE_HEALTH * (1 + 0.2 * (current_wave - 1)))
            enemy_speed = ENEMY_BASE_SPEED * (1 + 0.1 * (current_wave - 1))

            if spawn_timer >= spawn_interval and enemies_spawned < enemies_per_wave:
                enemies.append(Enemy(enemy_health, enemy_speed))
                enemies_spawned += 1
                spawn_timer = 0

            if enemies_spawned >= enemies_per_wave and len(enemies) == 0:
                wave_in_progress = False
                current_wave += 1
                wave_cooldown_timer = wave_cooldown

        # Обновление текста волны
        if wave_text:
            wave_text.update()
            wave_text.draw(screen)
            if wave_text.finished:
                wave_text = None

        # Обновление врагов
        for enemy in enemies[:]:
            alive, reached_finish = enemy.update(towers, enemy_bullets)
            if enemy.dead:
                corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, RED))
                money += 50
                enemies.remove(enemy)
                if tower_menu and tower_menu.tower in [None, enemy]:
                    tower_menu = None
            elif not alive:
                if reached_finish:
                    lives -= 1
                enemies.remove(enemy)
                if tower_menu and tower_menu.tower in [None, enemy]:
                    tower_menu = None

        # Обновление трупов
        for corpse in corpses[:]:
            corpse.update()
            if not corpse.alive:
                corpses.remove(corpse)

        # Удаление мертвых башен
        towers = [t for t in towers if t.alive]
        if tower_menu and not tower_menu.tower.alive:
            tower_menu = None

        # Обновление башен
        for tower in towers:
            tower.update(enemies, bullets)

        # Обновление пуль
        for bullet in bullets[:]:
            bullet.update()
            if not bullet.alive:
                bullets.remove(bullet)

        for ebullet in enemy_bullets[:]:
            ebullet.update()
            if not ebullet.alive:
                enemy_bullets.remove(ebullet)

        # Отрисовка
        for corpse in corpses:
            corpse.draw()

        for tower in towers:
            tower.draw()

        for enemy in enemies:
            enemy.draw()

        for bullet in bullets:
            bullet.draw()

        for ebullet in enemy_bullets:
            ebullet.draw()

        if tower_menu:
            tower_menu.draw(screen)

        # HUD
        hud_padding = 8
        hud_margin = 10
        hud_lines = [
            f"Деньги: {money}",
            f"Жизни: {lives}",
            f"Волна: {current_wave}",
            f"Выбранная башня: {selected_tower_type_name} ({TOWER_BASE_COST[selected_tower_type_name]}$)",
            "Клавиши: 1-3 для выбора башни",
            "ЛКМ/ПКМ по башне: меню",
            "ESC: закрыть меню/выйти",
        ]

        max_width = 0
        line_height = font.get_height()
        for line in hud_lines:
            w, _ = font.size(line)
            if w > max_width:
                max_width = w
        hud_width = max_width + hud_padding * 2
        hud_height = line_height * len(hud_lines) + hud_padding * 2

        hud_x = WIDTH - hud_width - hud_margin
        hud_y = hud_margin

        hud_surface = pygame.Surface((hud_width, hud_height), pygame.SRCALPHA)
        hud_surface.fill((30, 30, 30, 180))
        screen.blit(hud_surface, (hud_x, hud_y))

        for i, line in enumerate(hud_lines):
            text_surf = font.render(line, True, WHITE)
            screen.blit(text_surf, (hud_x + hud_padding, hud_y + hud_padding + i * line_height))

        if lives <= 0:
            game_over_text = font.render("Игра окончена! Нажмите ESC для выхода.", True, RED)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            wait_for_exit()
            running = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()


def wait_for_exit():
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    waiting = False
        pygame.time.wait(100)


if __name__ == "__main__":
    main()
