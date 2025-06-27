import pygame
import math
import sys

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 640, 640
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 200, 0)  # лужайка
RED = (255, 0, 0)    # зоны башен и надпись волны
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (100, 200, 255)  # финиш
PATH_COLOR = (245, 245, 245)  # светло-серый для дорожки
DARK_GRAY = (50, 50, 50)
DISABLED_GRAY = (80, 80, 80)

# Настройки игры
START_MONEY = 200  # стартовые деньги
ENEMY_BASE_HEALTH = 100
ENEMY_BASE_SPEED = 1.0
BULLET_SPEED = 5
ENEMY_BULLET_SPEED = 3
TOWER_BASE_COST = {
    "Стандартная": 100,
    "Быстрая": 150,
    "Сильная": 200
}
TOWER_UPGRADE_COST = {
    "Стандартная": [100, 150],  # уровень 2 и 3 соответственно
    "Быстрая": [100, 100],
    "Сильная": [150, 200]
}
TOWER_MAX_LEVEL = 3

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defence")

clock = pygame.time.Clock()

# Путь для врагов — список точек (по центру дорожки)
path = [
    (640, 130),
    (130, 130),
    (50, 260),
    (130, 350),
    (510, 350),
    (590, 463),
    (510, 576),
    (0, 576)
]

# Красные квадраты — места для башен
tower_zones = [
    pygame.Rect(42, 42, 50, 50),
    pygame.Rect(180, 215, 50, 50),
    pygame.Rect(180, 430, 50, 50),
    pygame.Rect(480, 215, 50, 50),
    pygame.Rect(400, 430, 50, 50),
]

# Голубой квадрат — финиш
finish_zone = pygame.Rect(0, 520, 80, 80)

# Попытка загрузить фон
try:
    background_img = pygame.image.load('background.png')
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except Exception:
    background_img = None

# --- Загрузка спрайтов и подготовка анимаций ---

def load_sprite_sheet(filename, frame_width, frame_height):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
        return []
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for i in range(sheet_width // frame_width):
        frame = sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
        frames.append(frame)
    return frames

# Загружаем спрайты башен
sprites_towers = {
    "Быстрая": load_sprite_sheet("speed.png", 50, 50),    # speed.png
    "Стандартная": load_sprite_sheet("standart.png", 50, 50),  # standart.png
    "Сильная": load_sprite_sheet("strong.png", 50, 50)     # strong.png
}

# Загружаем спрайты врага
sprites_enemy = load_sprite_sheet("ez.png", 50, 50)  # 4 ходьба + 5 смерть

# Функция поворота спрайта с сохранением центра
def rotate_center(image, angle):
    rotated_image = pygame.transform.rotozoom(image, -angle, 1)
    rotated_rect = rotated_image.get_rect(center=image.get_rect().center)
    return rotated_image, rotated_rect

# Класс для описания типа башни
class TowerType:
    def __init__(self, name, color, range_, fire_rate, damage, radius):
        self.name = name
        self.color = color
        self.range = range_
        self.fire_rate = fire_rate
        self.damage = damage
        self.radius = radius

# Определяем типы башен (уровень 1 параметры)
tower_types = {
    "Стандартная": TowerType("Стандартная", BLUE, 120, 60, 25, 20),
    "Быстрая": TowerType("Быстрая", CYAN, 100, 20, 10, 15),
    "Сильная": TowerType("Сильная", MAGENTA, 150, 90, 50, 25)
}

def get_tower_stats(tower_type_name, level):
    base = tower_types[tower_type_name]
    range_ = base.range + (level - 1) * 10
    damage = int(base.damage * (1 + 0.5 * (level - 1)))
    fire_rate = max(5, int(base.fire_rate / (1 + 0.5 * (level - 1))))
    radius = base.radius + (level -1) * 5
    return range_, fire_rate, damage, radius

def draw_path():
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(GREEN)
        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            pygame.draw.line(screen, PATH_COLOR, start, end, 40)
        for rect in tower_zones:
            pygame.draw.rect(screen, RED, rect)
        pygame.draw.rect(screen, LIGHT_BLUE, finish_zone)

# --- Классы с анимациями ---

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
        self.attack_cooldown = 120
        self.attack_timer = 0
        self.attack_damage = 15
        self.attack_range = 100

        # Анимация
        self.walk_frames = sprites_enemy[:4]  # 4 кадра ходьбы
        self.death_frames = sprites_enemy[4:9]  # 5 кадров смерти
        self.anim_index = 0
        self.anim_speed = 0.15  # скорость смены кадров
        self.anim_timer = 0
        self.is_dying = False
        self.death_anim_done = False

        self.angle = 0  # угол поворота спрайта

    def update(self, towers, enemy_bullets):
        if not self.alive and not self.is_dying:
            # Начинаем анимацию смерти
            self.is_dying = True
            self.anim_index = 0
            self.anim_timer = 0
            return True  # чтобы не удалять сразу (будет удалено после анимации)

        if self.is_dying:
            self.anim_timer += self.anim_speed
            if self.anim_timer >= 1:
                self.anim_timer = 0
                self.anim_index += 1
                if self.anim_index >= len(self.death_frames):
                    self.death_anim_done = True
                    return False  # анимация смерти закончена, можно удалить врага
            return True

        self.attack_timer += 1

        # Двигаемся по пути
        if self.path_pos + 1 >= len(self.path):
            if finish_zone.collidepoint(self.x, self.y):
                self.alive = False
                return False
            else:
                self.alive = False
                return False
        target_x, target_y = self.path[self.path_pos + 1]
        vec_x = target_x - self.x
        vec_y = target_y - self.y
        dist = math.hypot(vec_x, vec_y)
        if dist == 0:
            self.path_pos += 1
        else:
            move_x = (vec_x / dist) * self.speed
            move_y = (vec_y / dist) * self.speed
            self.x += move_x
            self.y += move_y
            if math.hypot(target_x - self.x, target_y - self.y) < self.speed:
                self.path_pos += 1

        # Обновляем угол поворота спрайта по направлению движения
        self.angle = math.degrees(math.atan2(vec_y, vec_x))

        # Проверяем, есть ли башня в радиусе атаки, чтобы стрелять
        target = None
        min_dist = float('inf')
        for tower in towers:
            if not tower.alive:
                continue
            dist_to_tower = math.hypot(tower.x - self.x, tower.y - self.y)
            if dist_to_tower <= self.attack_range and dist_to_tower < min_dist:
                min_dist = dist_to_tower
                target = tower

        if target and self.attack_timer >= self.attack_cooldown:
            enemy_bullets.append(EnemyBullet(self.x, self.y, target, self.attack_damage))
            self.attack_timer = 0
            # Поворачиваемся к цели при стрельбе
            dx = target.x - self.x
            dy = target.y - self.y
            self.angle = math.degrees(math.atan2(dy, dx))

        # Анимация ходьбы
        self.anim_timer += self.anim_speed
        if self.anim_timer >= 1:
            self.anim_timer = 0
            self.anim_index = (self.anim_index + 1) % len(self.walk_frames)

        return True

    def draw(self):
        if self.is_dying:
            if self.anim_index < len(self.death_frames):
                frame = self.death_frames[self.anim_index]
                rotated_frame, rotated_rect = rotate_center(frame, self.angle)
                rect = rotated_frame.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(rotated_frame, rect)
            return

        frame = self.walk_frames[self.anim_index]
        rotated_frame, rotated_rect = rotate_center(frame, self.angle)
        rect = rotated_frame.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated_frame, rect)

        # Рисуем полосу здоровья
        health_bar_width = 30
        health_bar_height = 5
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(screen, RED, (self.x - health_bar_width // 2, self.y - self.radius - 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - health_bar_width // 2, self.y - self.radius - 10, int(health_bar_width * health_ratio), health_bar_height))

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False

class Corpse:
    def __init__(self, x, y, radius, color, lifetime=180):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.lifetime = lifetime  # в кадрах (3 секунды при 60 FPS)
        self.timer = 0
        self.alive = True

    def update(self):
        self.timer += 1
        if self.timer >= self.lifetime:
            self.alive = False

    def draw(self):
        s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        alpha = max(0, 150 - int(150 * (self.timer / self.lifetime)))
        pygame.draw.circle(s, (*self.color[:3], alpha), (self.radius, self.radius), self.radius)
        screen.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

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
        self.target.take_damage(self.damage)
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, MAGENTA, (int(self.x), int(self.y)), self.radius)

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

        # Анимация
        self.sprites = sprites_towers.get(tower_type_name, [])
        self.anim_index = 4  # стартуем с кадра стойки (5-й кадр, индекс 4)
        self.anim_timer = 0
        self.anim_speed = 0.2
        self.is_shooting = False
        self.shoot_anim_length = 4  # первые 4 кадра - стрельба
        self.shoot_anim_timer = 0
        self.shoot_anim_duration = 10  # кадры анимации стрельбы

        self.angle = 0  # угол поворота башни

    def update(self, enemies, bullets):
        if not self.alive:
            return
        self.timer += 1
        self.is_shooting = False

        target = None
        min_dist = float('inf')
        for enemy in enemies:
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.range and enemy.alive:
                if dist < min_dist:
                    min_dist = dist
                    target = enemy

        if target and self.timer >= self.fire_rate:
            bullet = Bullet(self.x, self.y, target, self.damage)
            bullets.append(bullet)
            self.timer = 0
            self.is_shooting = True
            self.shoot_anim_timer = 0
            self.anim_index = 0  # начать анимацию стрельбы с кадра 0
            # Поворачиваем башню в сторону цели
            dx = target.x - self.x
            dy = target.y - self.y
            self.angle = math.degrees(math.atan2(dy, dx))
        elif target:
            # Если есть цель, поворачиваемся к ней, даже если не стреляем
            dx = target.x - self.x
            dy = target.y - self.y
            self.angle = math.degrees(math.atan2(dy, dx))
        else:
            # Нет цели — поворачиваем в исходное положение (0 градусов)
            self.angle = 0

        # Обновление анимации
        if self.is_shooting:
            self.shoot_anim_timer += 1
            if self.shoot_anim_timer >= self.shoot_anim_duration:
                # Анимация стрельбы закончилась — возвращаемся к стойке
                self.anim_index = 4
                self.is_shooting = False
            else:
                # Переходим по кадрам стрельбы
                self.anim_timer += self.anim_speed
                if self.anim_timer >= 1:
                    self.anim_timer = 0
                    self.anim_index += 1
                    if self.anim_index >= self.shoot_anim_length:
                        self.anim_index = 0
        else:
            # Если не стреляем — показываем кадр стойки (4-й индекс)
            self.anim_index = 4

    def draw(self):
        if not self.alive:
            return
        # Рисуем радиус действия
        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (self.range, self.range), self.range)
        screen.blit(s, (self.x - self.range, self.y - self.range))

        # Рисуем спрайт башни с поворотом
        if self.sprites and 0 <= self.anim_index < len(self.sprites):
            frame = self.sprites[self.anim_index]
            rotated_frame, rotated_rect = rotate_center(frame, self.angle)
            rect = rotated_frame.get_rect(center=(self.x, self.y))
            screen.blit(rotated_frame, rect)
        else:
            # Если спрайтов нет — рисуем простой круг
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

        # Полоса здоровья
        health_bar_width = 40
        health_bar_height = 6
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(screen, RED, (self.x - health_bar_width // 2, self.y + self.radius + 5, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - health_bar_width // 2, self.y + self.radius + 5, int(health_bar_width * health_ratio), health_bar_height))

        # Уровень
        font = pygame.font.SysFont(None, 18)
        lvl_text = font.render(f"Lv{self.level}", True, BLACK)
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

        upgrade_text = "Upgrade"
        if self.tower.level >= TOWER_MAX_LEVEL:
            upgrade_text = "Max Level"
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
        sell_text = f"Sell ({sell_price})"
        sell_surf = self.font.render(sell_text, True, WHITE)

        if not self.tower.can_sell():
            sell_color = DISABLED_GRAY
            warning_surf = self.font.render("Too damaged to sell", True, RED)
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
    font = pygame.font.SysFont(None, 24)
    selected_tower_type_name = "Стандартная"
    tower_menu = None

    current_wave = 1
    enemies_spawned = 0
    enemies_per_wave = 10
    wave_in_progress = False
    wave_cooldown = 180
    wave_cooldown_timer = wave_cooldown

    # Параметры для плавного появления текста волны
    wave_text_alpha = 0
    wave_text_fade_in = True
    wave_text_fade_speed = 5  # скорость изменения alpha

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
                        if action in ("upgrade", "sell"):
                            if action == "sell":
                                tower_menu = None
                        else:
                            mx_, my_ = event.pos
                            tower_rect = pygame.Rect(tower_menu.tower.x - tower_menu.tower.radius,
                                                     tower_menu.tower.y - tower_menu.tower.radius,
                                                     tower_menu.tower.radius * 2,
                                                     tower_menu.tower.radius * 2)
                            if not tower_rect.collidepoint(mx_, my_):
                                if not (tower_menu.x <= mx_ <= tower_menu.x + tower_menu.width and
                                        tower_menu.y <= my_ <= tower_menu.y + tower_menu.height):
                                    tower_menu = None
                    else:
                        clicked_tower = None
                        for tower in towers:
                            tower_rect = pygame.Rect(tower.x - tower.radius, tower.y - tower.radius,
                                                     tower.radius * 2, tower.radius * 2)
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
                                            towers.append(Tower(cx, cy, zone_rect, selected_tower_type_name))
                                            money -= cost
                                            tower_menu = None
                                    break
                elif event.button == 3:
                    clicked_tower = None
                    for tower in towers:
                        tower_rect = pygame.Rect(tower.x - tower.radius, tower.y - tower.radius,
                                                 tower.radius * 2, tower.radius * 2)
                        if tower.alive and tower_rect.collidepoint(mx, my):
                            clicked_tower = tower
                            break
                    if clicked_tower:
                        tower_menu = TowerMenu(clicked_tower)

        # Логика волн

        if not wave_in_progress:
            wave_cooldown_timer -= 1
            # Обновляем alpha для плавного появления текста волны
            if wave_text_fade_in:
                wave_text_alpha += wave_text_fade_speed
                if wave_text_alpha >= 255:
                    wave_text_alpha = 255
                    wave_text_fade_in = False
            else:
                wave_text_alpha -= wave_text_fade_speed
                if wave_text_alpha <= 0:
                    wave_text_alpha = 0

            if wave_cooldown_timer <= 0:
                wave_in_progress = True
                enemies_spawned = 0
                enemies_per_wave = 10 + (current_wave - 1) * 5
                spawn_timer = spawn_interval
                wave_text_alpha = 0
                wave_text_fade_in = True
        else:
            spawn_timer += 1

            spawn_interval = max(30, 120 - (current_wave -1) * 10)
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

        # Обновление врагов
        for enemy in enemies[:]:
            alive = enemy.update(towers, enemy_bullets)
            if not alive:
                if enemy.alive:
                    lives -= 1
                else:
                    corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, RED))
                    money += 50
                enemies.remove(enemy)
                if tower_menu and not tower_menu.tower.alive:
                    tower_menu = None
            elif not enemy.alive:
                corpses.append(Corpse(enemy.x, enemy.y, enemy.radius, RED))
                money += 50
                enemies.remove(enemy)
                if tower_menu and not tower_menu.tower.alive:
                    tower_menu = None

        # Обновление трупов
        for corpse in corpses[:]:
            corpse.update()
            if not corpse.alive:
                corpses.remove(corpse)

        towers = [t for t in towers if t.alive]
        if tower_menu and not tower_menu.tower.alive:
            tower_menu = None

        for tower in towers:
            tower.update(enemies, bullets)

        for bullet in bullets[:]:
            bullet.update()
            if not bullet.alive:
                bullets.remove(bullet)

        for ebullet in enemy_bullets[:]:
            ebullet.update()
            if not ebullet.alive:
                enemy_bullets.remove(ebullet)

        # Рисуем трупы под врагами и башнями
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

        money_text = font.render(f"Money: {money}", True, BLACK)
        lives_text = font.render(f"Lives: {lives}", True, BLACK)
        wave_text = font.render(f"Wave: {current_wave}", True, BLACK)
        screen.blit(money_text, (10, 10))
        screen.blit(lives_text, (10, 30))
        screen.blit(wave_text, (10, 50))

        base_cost = TOWER_BASE_COST[selected_tower_type_name]
        tower_info = font.render(f"Selected Tower: {selected_tower_type_name} (1-3 to change), Cost: {base_cost} (LMB to build)", True, BLACK)
        screen.blit(tower_info, (10, 70))
        upgrade_info = font.render(f"RMB or LMB on tower to open menu, ESC to close menu", True, BLACK)
        screen.blit(upgrade_info, (10, 90))

        # Плавное появление текста волны
        if not wave_in_progress and wave_text_alpha > 0:
            wave_msg_font = pygame.font.SysFont(None, 72)
            wave_msg = wave_msg_font.render(f"Волна {current_wave}", True, RED)
            wave_msg.set_alpha(wave_text_alpha)
            screen.blit(wave_msg, (WIDTH // 2 - wave_msg.get_width() // 2, HEIGHT // 2 - wave_msg.get_height() // 2))

        if lives <= 0:
            game_over_text = font.render("Game Over! Press ESC to quit.", True, RED)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            wait_for_exit()
            running = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
исправь то что враги не стреляют и не поворачиваются, а турель поворачивается не так исправь это пожалуйстаа о меня уволят с работы
