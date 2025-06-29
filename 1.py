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
RED = (255, 0, 0)  # зоны башен и надпись волны
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (100, 200, 255)  # финиш
PATH_COLOR = (245, 245, 245)  # светло-серый для дорожки
DARK_GRAY = (50, 50, 50)
DISABLED_GRAY = (80, 80, 80)

# Настройки игры
START_MONEY = 200
ENEMY_BASE_HEALTH = 100
ENEMY_BASE_SPEED = 1.0
BULLET_SPEED = 5
ENEMY_BULLET_SPEED = 3
TOWER_BASE_COST = {"Стандартная": 100, "Быстрая": 150, "Сильная": 200}
TOWER_UPGRADE_COST = {
    "Стандартная": [100, 150],
    "Быстрая": [100, 100],
    "Сильная": [150, 200],
}
TOWER_MAX_LEVEL = 3

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defence")

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

# Попытка загрузить фон
try:
    background_img = pygame.image.load("background.png")
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except Exception:
    background_img = None


# Загрузка спрайтов
def load_sprite_sheet(filename, frame_width, frame_height):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
    except Exception as e:
        print(f"Ошибка загрузки {filename}: {e}")
        return []
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    for i in range(sheet_width // frame_width):
        frame = sheet.subsurface(
            pygame.Rect(i * frame_width, 0, frame_width, frame_height)
        )
        frames.append(frame)
    return frames


sprites_towers = {
    "Быстрая": load_sprite_sheet("speed.png", 50, 50),
    "Стандартная": load_sprite_sheet("standart.png", 50, 50),
    "Сильная": load_sprite_sheet("strong.png", 50, 50),
}

sprites_enemy = load_sprite_sheet("ez.png", 50, 50)


# Класс типа башни
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
            start = path[i]
            end = path[i + 1]
            pygame.draw.line(screen, PATH_COLOR, start, end, 40)
        for rect in tower_zones:
            pygame.draw.rect(screen, RED, rect)
        pygame.draw.rect(screen, LIGHT_BLUE, finish_zone)


# Класс врага
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
        self.attack_cooldown = 60  # уменьшено для более частой стрельбы
        self.attack_timer = self.attack_cooldown  # чтобы стрелять сразу
        self.attack_damage = 15
        self.attack_range = 150  # увеличен радиус атаки

        # Анимация
        self.walk_frames = sprites_enemy[:4]
        self.death_frames = sprites_enemy[4:9]
        self.anim_index = 0
        self.anim_speed = 0.15
        self.anim_timer = 0
        self.is_dying = False
        self.death_anim_done = False

    def update(self, towers, enemy_bullets):
        if not self.alive and not self.is_dying:
            self.is_dying = True
            self.anim_index = 0
            self.anim_timer = 0
            return True

        if self.is_dying:
            self.anim_timer += self.anim_speed
            if self.anim_timer >= 1:
                self.anim_timer = 0
                self.anim_index += 1
                if self.anim_index >= len(self.death_frames):
                    self.death_anim_done = True
                    return False
            return True

        self.attack_timer += 1

        # Движение по пути
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

        # Поиск башни для атаки
        target = None
        min_dist = float("inf")
        for tower in towers:
            if not tower.alive:
                continue
            dist_to_tower = math.hypot(tower.x - self.x, tower.y - self.y)
            if dist_to_tower <= self.attack_range and dist_to_tower < min_dist:
                min_dist = dist_to_tower
                target = tower

        if target and self.attack_timer >= self.attack_cooldown:
            enemy_bullets.append(
                EnemyBullet(self.x, self.y, target, self.attack_damage)
            )
            self.attack_timer = 0

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
                rect = frame.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(frame, rect)
            return

        frame = self.walk_frames[self.anim_index]
        rect = frame.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(frame, rect)

        # Полоса здоровья
        health_bar_width = 30
        health_bar_height = 5
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(
            screen,
            RED,
            (
                self.x - health_bar_width // 2,
                self.y - self.radius - 10,
                health_bar_width,
                health_bar_height,
            ),
        )
        pygame.draw.rect(
            screen,
            GREEN,
            (
                self.x - health_bar_width // 2,
                self.y - self.radius - 10,
                int(health_bar_width * health_ratio),
                health_bar_height,
            ),
        )

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False


# Класс снаряда башни
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


# Класс снаряда врага
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
        if hasattr(self.target, "take_damage"):
            self.target.take_damage(self.damage)
        else:
            self.target.health -= self.damage
            if self.target.health <= 0:
                self.target.alive = False
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, MAGENTA, (int(self.x), int(self.y)), self.radius)


# Класс башни с поворотом
class Tower:
    def __init__(self, x, y, zone_rect, tower_type_name):
        self.x = x
        self.y = y
        self.zone_rect = zone_rect
        self.type_name = tower_type_name
        self.level = 1
        self.range, self.fire_rate, self.damage, self.radius = get_tower_stats(
            tower_type_name, self.level
        )
        self.timer = 0
        self.color = tower_types[tower_type_name].color
        self.max_health = 100 + 50 * (self.level - 1)
        self.health = self.max_health
        self.alive = True

        # Анимация
        self.sprites = sprites_towers.get(tower_type_name, [])
        self.anim_index = 4
        self.anim_timer = 0
        self.anim_speed = 0.2
        self.is_shooting = False
        self.shoot_anim_length = 4
        self.shoot_anim_timer = 0
        self.shoot_anim_duration = 10

        # Поворот
        self.angle = 0  # угол поворота в градусах

    def update(self, enemies, bullets):
        if not self.alive:
            return
        self.timer += 1
        self.is_shooting = False

        # Найти цель (ближайший враг в радиусе)
        target = None
        min_dist = float("inf")
        for enemy in enemies:
            dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if dist <= self.range and enemy.alive:
                if dist < min_dist:
                    min_dist = dist
                    target = enemy

        if target:
            # Вычислить угол поворота к цели
            dx = target.x - self.x
            dy = target.y - self.y
            if dx != 0 or dy != 0:
                self.angle = math.degrees(
                    math.atan2(-dy, dx)
                )  # pygame поворачивает против часовой, поэтому -dy

        if self.timer >= self.fire_rate and target:
            bullet = Bullet(self.x, self.y, target, self.damage)
            bullets.append(bullet)
            self.timer = 0
            self.is_shooting = True
            self.shoot_anim_timer = 0
            self.anim_index = 0

        # Обновление анимации
        if self.is_shooting:
            self.shoot_anim_timer += 1
            if self.shoot_anim_timer >= self.shoot_anim_duration:
                self.anim_index = 4
                self.is_shooting = False
            else:
                self.anim_timer += self.anim_speed
                if self.anim_timer >= 1:
                    self.anim_timer = 0
                    self.anim_index += 1
                    if self.anim_index >= self.shoot_anim_length:
                        self.anim_index = 0
        else:
            self.anim_index = 4

    def draw(self):
        if not self.alive:
            return

        # Рисуем радиус действия
        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (self.range, self.range), self.range)
        screen.blit(s, (self.x - self.range, self.y - self.range))

        # Рисуем спрайт с поворотом
        if self.sprites and 0 <= self.anim_index < len(self.sprites):
            frame = self.sprites[self.anim_index]
            rotated_frame = pygame.transform.rotate(frame, self.angle)
            rect = rotated_frame.get_rect(center=(self.x, self.y))
            screen.blit(rotated_frame, rect)
        else:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

        # Полоса здоровья
        health_bar_width = 40
        health_bar_height = 6
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(
            screen,
            RED,
            (
                self.x - health_bar_width // 2,
                self.y + self.radius + 5,
                health_bar_width,
                health_bar_height,
            ),
        )
        pygame.draw.rect(
            screen,
            GREEN,
            (
                self.x - health_bar_width // 2,
                self.y + self.radius + 5,
                int(health_bar_width * health_ratio),
                health_bar_height,
            ),
        )

        # Уровень
        font = pygame.font.SysFont(None, 18)
        lvl_text = font.render(f"Lv{self.level}", True, BLACK)
        screen.blit(
            lvl_text,
            (self.x - lvl_text.get_width() // 2, self.y - lvl_text.get_height() // 2),
        )

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
            self.range, self.fire_rate, self.damage, self.radius = get_tower_stats(
                self.type_name, self.level
            )
            self.max_health = 100 + 50 * (self.level - 1)
            self.health = self.max_health
            money -= cost
            return True, money
        return False, money

    def sell_price(self):
        base_cost = TOWER_BASE_COST[self.type_name]
        upgrades_cost = (
            sum(TOWER_UPGRADE_COST[self.type_name][: self.level - 1])
            if self.level > 1
            else 0
        )
        return (base_cost + upgrades_cost) // 2

    def can_sell(self):
        return self.health >= self.max_health * 0.25


# Класс меню башни
class TowerMenu:
    def __init__(self, tower):
        self.tower = tower
        self.width = 130
        self.height = 50
        self.x = tower.x - self.width // 2
        self.y = tower.y - tower.radius - self.height - 10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.upgrade_rect = pygame.Rect(self.x + 5, self.y + 5, 60, 40)
        self.sell_rect = pygame.Rect(self.x + 65, self.y + 5, 60, 40)
        self.font = pygame.font.SysFont(None, 20)

    def draw(self, money):
        pygame.draw.rect(screen, GRAY, self.rect)
        # Кнопка улучшения
        upgrade_cost = 0
        can_upgrade = False
        if self.tower.level < TOWER_MAX_LEVEL:
            upgrade_cost = TOWER_UPGRADE_COST[self.tower.type_name][
                self.tower.level - 1
            ]
            can_upgrade = money >= upgrade_cost
        upgrade_color = GREEN if can_upgrade else DISABLED_GRAY
        pygame.draw.rect(screen, upgrade_color, self.upgrade_rect)
        upgrade_text = self.font.render(f"Улучшить {upgrade_cost}", True, BLACK)
        screen.blit(upgrade_text, (self.upgrade_rect.x + 5, self.upgrade_rect.y + 10))

        # Кнопка продажи
        sell_price = self.tower.sell_price()
        sell_color = GREEN if self.tower.can_sell() else DISABLED_GRAY
        pygame.draw.rect(screen, sell_color, self.sell_rect)
        sell_text = self.font.render(f"Продать {sell_price}", True, BLACK)
        screen.blit(sell_text, (self.sell_rect.x + 5, self.sell_rect.y + 10))

    def handle_event(self, event, money):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.upgrade_rect.collidepoint(pos):
                success, money = self.tower.upgrade(money)
                return "upgrade" if success else None, money
            elif self.sell_rect.collidepoint(pos):
                if self.tower.can_sell():
                    money += self.tower.sell_price()
                    self.tower.alive = False
                    return "sell", money
        return None, money


# Класс трупа (остаток башни)
class Corpse:
    def __init__(self, x, y, tower_type_name):
        self.x = x
        self.y = y
        self.type_name = tower_type_name
        self.color = tower_types[tower_type_name].color
        self.radius = 15
        self.life_time = 300  # кадры, сколько труп будет на экране
        self.timer = 0

    def update(self):
        self.timer += 1
        return self.timer < self.life_time

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        # Можно добавить эффект затухания, если хотите


# Основная функция игры
def main():
    global ENEMY_BASE_HEALTH, ENEMY_BASE_SPEED
    money = START_MONEY
    enemies = []
    bullets = []
    enemy_bullets = []
    towers = []
    corpses = []
    selected_tower = None
    tower_menu = None
    wave = 1
    spawn_timer = 0
    spawn_interval = 60
    enemies_to_spawn = wave * 5
    font = pygame.font.SysFont(None, 24)

    running = True
    while running:
        # остальной код
        if enemies_to_spawn == 0 and not enemies:
            wave += 1
            enemies_to_spawn = wave * 5
            spawn_interval = max(20, spawn_interval - 5)
            ENEMY_BASE_HEALTH += 20
            ENEMY_BASE_SPEED += 0.05
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Проверка клика по меню башни
                if tower_menu:
                    action, money = tower_menu.handle_event(event, money)
                    if action in ("upgrade", "sell"):
                        tower_menu = None
                        selected_tower = None
                        continue

                # Проверка клика по башням
                clicked_tower = None
                for tower in towers:
                    dist = math.hypot(tower.x - pos[0], tower.y - pos[1])
                    if dist <= tower.radius and tower.alive:
                        clicked_tower = tower
                        break
                if clicked_tower:
                    selected_tower = clicked_tower
                    tower_menu = TowerMenu(selected_tower)
                else:
                    # Проверка на размещение новой башни
                    for zone in tower_zones:
                        if zone.collidepoint(pos):
                            # Проверка, что в зоне нет башни
                            if any(
                                tower.zone_rect == zone and tower.alive
                                for tower in towers
                            ):
                                break
                            # Выбор типа башни (для примера — стандартная)
                            tower_type_name = "Стандартная"
                            cost = TOWER_BASE_COST[tower_type_name]
                            if money >= cost:
                                new_tower = Tower(
                                    zone.centerx, zone.centery, zone, tower_type_name
                                )
                                towers.append(new_tower)
                                money -= cost
                            break
                    selected_tower = None
                    tower_menu = None

        # Спавн врагов
        spawn_timer += 1
        if spawn_timer >= spawn_interval and enemies_to_spawn > 0:
            enemies.append(Enemy(ENEMY_BASE_HEALTH, ENEMY_BASE_SPEED))
            enemies_to_spawn -= 1
            spawn_timer = 0
        if enemies_to_spawn == 0 and not enemies:
            wave += 1
            enemies_to_spawn = wave * 5
            spawn_interval = max(20, spawn_interval - 5)
            ENEMY_BASE_HEALTH += 20
            ENEMY_BASE_SPEED += 0.05

        # Обновление врагов
        enemies = [enemy for enemy in enemies if enemy.update(towers, enemy_bullets)]
        # Обновление снарядов башен
        for bullet in bullets:
            bullet.update()
        bullets = [b for b in bullets if b.alive]

        # Обновление снарядов врагов
        for e_bullet in enemy_bullets:
            e_bullet.update()
        enemy_bullets = [b for b in enemy_bullets if b.alive]

        # Обновление башен
        for tower in towers:
            tower.update(enemies, bullets)

        # Обновление трупов
        corpses = [corpse for corpse in corpses if corpse.update()]

        # Добавление трупов от мертвых башен
        for tower in towers:
            if not tower.alive and not any(
                corpse.x == tower.x and corpse.y == tower.y for corpse in corpses
            ):
                corpses.append(Corpse(tower.x, tower.y, tower.type_name))
        towers = [t for t in towers if t.alive]

        # Отрисовка
        draw_path()

        for corpse in corpses:
            corpse.draw()

        for tower in towers:
            tower.draw()

        for bullet in bullets:
            bullet.draw()

        for e_bullet in enemy_bullets:
            e_bullet.draw()

        for enemy in enemies:
            enemy.draw()

        # Отрисовка меню башни
        if tower_menu:
            tower_menu.draw(money)

        # Отрисовка денег и волны
        money_text = font.render(f"Деньги: {money}", True, BLACK)
        wave_text = font.render(f"Волна: {wave}", True, BLACK)
        screen.blit(money_text, (10, 10))
        screen.blit(wave_text, (WIDTH - wave_text.get_width() - 10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
