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
<<<<<<< HEAD
RED = (255, 0, 0)    # зоны башен и надпись волны
=======
RED = (255, 0, 0)  # зоны башен
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
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
TOWER_BASE_COST = {
    "Стандартная": 100,
    "Быстрая": 150,
    "Сильная": 200
}
TOWER_UPGRADE_COST = {
    "Стандартная": [100, 150],
    "Быстрая": [100, 100],
    "Сильная": [150, 200]
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
<<<<<<< HEAD
    pygame.Rect(42, 42, 50, 50),
    pygame.Rect(180, 215, 50, 50),
    pygame.Rect(180, 430, 50, 50),
    pygame.Rect(480, 215, 50, 50),
    pygame.Rect(400, 430, 50, 50),
=======
    pygame.Rect(42, 42, 50, 50),  # (55, 55, 50, 50)
    pygame.Rect(180, 215, 50, 50),  # (535, 55, 50, 50)
    pygame.Rect(180, 430, 50, 50),  # (175, 295, 50, 50)
    pygame.Rect(480, 215, 50, 50),  # (415, 295, 50, 50)
    pygame.Rect(400, 430, 50, 50),  # (295, 495, 50, 50)
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
]

# Финиш
finish_zone = pygame.Rect(0, 520, 80, 80)

<<<<<<< HEAD
# Попытка загрузить фон
try:
    background_img = pygame.image.load('background.png')
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
except Exception:
    background_img = None

# Класс типа башни
=======

# Класс для описания типа башни
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
class TowerType:
    def __init__(self, name, color, range_, fire_rate, damage, radius):
        self.name = name
        self.color = color
        self.range = range_
        self.fire_rate = fire_rate
        self.damage = damage
        self.radius = radius

<<<<<<< HEAD
=======

# Определяем разные типы башен
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
tower_types = [
    TowerType("Стандартная", BLUE, 120, 60, 25, 20),
    TowerType("Быстрая", CYAN, 100, 20, 10, 15),
    TowerType("Сильная", MAGENTA, 150, 90, 50, 25),
]

# Функция для получения параметров башни по уровню (можно расширить)
def get_tower_stats(tower_type_name, level):
    base = next((t for t in tower_types if t.name == tower_type_name), None)
    if not base:
        return 100, 60, 25, 20  # дефолт
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

<<<<<<< HEAD
# Класс врага с атакой башен
=======
#     # Рисуем дорожку светло-серой линией толщиной 40px по пути
#     for i in range(len(path) - 1):
#         start = path[i]
#         end = path[i + 1]
#         pygame.draw.line(screen, PATH_COLOR, start, end, 40)

#     # Рисуем красные квадраты — зоны для башен
#     for rect in tower_zones:
#         pygame.draw.rect(screen, RED, rect)

#     # Рисуем голубой квадрат — финиш
#     pygame.draw.rect(screen, LIGHT_BLUE, finish_zone)


# Класс врага
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
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
        self.attack_cooldown = 60
        self.attack_timer = self.attack_cooldown
        self.attack_damage = 15
        self.attack_range = 150

    def update(self, towers, enemy_bullets):
        if not self.alive:
            return False

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

        # Атака башен в радиусе
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

        return True

    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
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

<<<<<<< HEAD
# Класс пули башни
=======
    def update(self, enemies, bullets):
        self.timer += 1
        if self.timer >= self.fire_rate:
            target = None
            min_dist = float("inf")
            for enemy in enemies:
                dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if dist <= self.range and enemy.alive:
                    if dist < min_dist:
                        min_dist = dist
                        target = enemy
            if target:
                bullet = Bullet(self.x, self.y, target, self.damage)
                bullets.append(bullet)
                self.timer = 0

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (self.range, self.range), self.range)
        screen.blit(s, (self.x - self.range, self.y - self.range))


# Класс пули
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
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
        self.target.take_damage(self.damage)
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

<<<<<<< HEAD
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
        self.target.take_damage(self.damage)
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, MAGENTA, (int(self.x), int(self.y)), self.radius)

# Класс башни
class Tower:
    def __init__(self, x, y, zone_rect, tower_type):
        self.x = x
        self.y = y
        self.zone_rect = zone_rect
        self.type_name = tower_type.name
        self.level = 1
        self.range, self.fire_rate, self.damage, self.radius = get_tower_stats(self.type_name, self.level)
        self.timer = 0
        self.color = tower_type.color
        self.max_health = 100 + 50 * (self.level - 1)
        self.health = self.max_health
        self.alive = True

    def update(self, enemies, bullets):
        if not self.alive:
            return
        self.timer += 1
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

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 50), (self.range, self.range), self.range)
        screen.blit(s, (self.x - self.range, self.y - self.range))

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
            upgrade_cost = TOWER_UPGRADE_COST[self.tower.type_name][self.tower.level - 1]
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
                return 'upgrade' if success else None, money
            elif self.sell_rect.collidepoint(pos):
                if self.tower.can_sell():
                    money += self.tower.sell_price()
                    self.tower.alive = False
                    return 'sell', money
        return None, money

# Основная функция игры
=======

# Основная функция
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
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
    selected_tower_type_index = 0

<<<<<<< HEAD
    running = True
    while running:
        dt = clock.tick(FPS)
        # Отрисовка фона / дорожки
        draw_path()

=======
    while running:
        screen.blit(
            pygame.transform.scale(
                pygame.image.load("background.png"), (WIDTH, HEIGHT)
            ),
            (0, 0),
        )
        clock.tick(FPS)
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_tower_type_index = 0
                elif event.key == pygame.K_2:
                    selected_tower_type_index = 1
                elif event.key == pygame.K_3:
                    selected_tower_type_index = 2
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Клик по меню башни
                if tower_menu:
                    action, money = tower_menu.handle_event(event, money)
                    if action in ('upgrade', 'sell'):
                        tower_menu = None
                        selected_tower = None
                        continue

                # Клик по башням
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
                    # Размещение новой башни
                    for zone in tower_zones:
                        if zone.collidepoint(pos):
                            if any(t.zone_rect == zone and t.alive for t in towers):
                                break
                            tower_type = tower_types[selected_tower_type_index]
                            cost = TOWER_BASE_COST[tower_type.name]
                            if money >= cost:
                                new_tower = Tower(zone.centerx, zone.centery, zone, tower_type)
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

        # Если волна закончилась, увеличить сложность
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

        # Отрисовка трупов (если реализовать)
        # corpses = [corpse for corpse in corpses if corpse.update()]
        # for corpse in corpses:
        #     corpse.draw()

        # Добавление трупов от мертвых башен (если нужно)
        # for tower in towers:
        #     if not tower.alive and not any(corpse.x == tower.x and corpse.y == tower.y for corpse in corpses):
        #         corpses.append(Corpse(tower.x, tower.y, tower.type_name))
        towers = [t for t in towers if t.alive]

        # Отрисовка
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

        # Отображаем выбранный тип башни
        selected_type = tower_types[selected_tower_type_index]
<<<<<<< HEAD
        tower_info = font.render(f"Выбранная башня: {selected_type.name} (1-3 переключить)", True, BLACK)
        screen.blit(tower_info, (10, 40))
=======
        tower_info = font.render(
            f"Selected Tower: {selected_type.name} (1-3 to change)", True, BLACK
        )
        screen.blit(tower_info, (10, 50))

        if lives <= 0:
            game_over_text = font.render("Game Over! Press ESC to quit.", True, RED)
            screen.blit(
                game_over_text,
                (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2),
            )
            pygame.display.flip()
            wait_for_exit()
            running = False
>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e

        pygame.display.flip()

    pygame.quit()
    sys.exit()

<<<<<<< HEAD
=======

# Функция ожидания выхода после окончания игры
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


>>>>>>> 4d5f577a64765ec1bb97a27eba4cc6b15237ea5e
if __name__ == "__main__":
    main()
