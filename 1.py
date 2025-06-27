<<<<<<< HEAD
=======
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
RED = (255, 0, 0)    # зоны башен
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (100, 200, 255)  # финиш
PATH_COLOR = (245, 245, 245)  # светло-серый для дорожки

# Настройки игры
TOWER_COST = 100
START_MONEY = 300
ENEMY_HEALTH = 100
ENEMY_SPEED = 1.0
BULLET_SPEED = 5

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defence")

clock = pygame.time.Clock()

# Путь для врагов — список точек (по центру дорожки)
path = [
    (640, 80),
    (64, 80),
    (64, 320),
    (576, 320),
    (576, 576),
    (0, 576)
]

# Красные квадраты — места для башен (x, y, width, height)
tower_zones = [
    pygame.Rect(20, 230, 50, 50),
    pygame.Rect(180, 120, 50, 50),
    pygame.Rect(350, 120, 50, 50),
    pygame.Rect(420, 400, 50, 50),
    pygame.Rect(600, 400, 50, 50)
]

# Голубой квадрат — финиш (нижний левый угол)
finish_zone = pygame.Rect(0, 520, 80, 80)

# Класс для описания типа башни
class TowerType:
    def __init__(self, name, color, range_, fire_rate, damage, radius):
        self.name = name
        self.color = color
        self.range = range_
        self.fire_rate = fire_rate
        self.damage = damage
        self.radius = radius

# Определяем разные типы башен
tower_types = [
    TowerType("Стандартная", BLUE, 120, 60, 25, 20),
    TowerType("Быстрая", CYAN, 100, 20, 10, 15),
    TowerType("Сильная", MAGENTA, 150, 90, 50, 25)
]

# Функция для рисования лужайки, дорожки, зон башен и финиша
def draw_path():
    # Лужайка — фон зеленый
    screen.fill(GREEN)

    # Рисуем дорожку светло-серой линией толщиной 40px по пути
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        pygame.draw.line(screen, PATH_COLOR, start, end, 40)

    # Рисуем красные квадраты — зоны для башен
    for rect in tower_zones:
        pygame.draw.rect(screen, RED, rect)

    # Рисуем голубой квадрат — финиш
    pygame.draw.rect(screen, LIGHT_BLUE, finish_zone)

# Класс врага
class Enemy:
    def __init__(self):
        self.path = path
        self.path_pos = 0  # индекс текущей точки пути
        self.x, self.y = self.path[0]
        self.speed = ENEMY_SPEED
        self.health = ENEMY_HEALTH
        self.max_health = ENEMY_HEALTH
        self.radius = 15
        self.alive = True

    def update(self):
        if self.path_pos + 1 >= len(self.path):
            # Проверяем, в зоне ли финиша
            if finish_zone.collidepoint(self.x, self.y):
                self.alive = False
                return False  # Враг дошел до финиша
            else:
                # Остановить врага, если вышел за путь
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
            # Проверяем, не достигли ли следующей точки
            if math.hypot(target_x - self.x, target_y - self.y) < self.speed:
                self.path_pos += 1
        return True

    def draw(self):
        # Тело врага
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        # Здоровье
        health_bar_width = 30
        health_bar_height = 5
        health_ratio = max(self.health / self.max_health, 0)
        pygame.draw.rect(screen, RED, (self.x - health_bar_width // 2, self.y - self.radius - 10, health_bar_width, health_bar_height))
        pygame.draw.rect(screen, GREEN, (self.x - health_bar_width // 2, self.y - self.radius - 10, int(health_bar_width * health_ratio), health_bar_height))

# Класс башни
class Tower:
    def __init__(self, x, y, zone_rect, tower_type):
        self.x = x
        self.y = y
        self.zone_rect = zone_rect
        self.type = tower_type
        self.range = tower_type.range
        self.fire_rate = tower_type.fire_rate
        self.damage = tower_type.damage
        self.timer = 0
        self.color = tower_type.color
        self.radius = tower_type.radius

    def update(self, enemies, bullets):
        self.timer += 1
        if self.timer >= self.fire_rate:
            target = None
            min_dist = float('inf')
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
class Bullet:
    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.speed = BULLET_SPEED
        self.radius = 5
        self.damage = damage
        self.alive = True

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
        # Проверяем попадание
        if math.hypot(self.target.x - self.x, self.target.y - self.y) < self.speed:
            self.hit_target()

    def hit_target(self):
        self.target.health -= self.damage
        if self.target.health <= 0:
            self.target.alive = False
        self.alive = False

    def draw(self):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)

# Основная функция
def main():
    running = True
    enemies = []
    towers = []
    bullets = []
    spawn_timer = 0
    spawn_interval = 120  # кадры между спавном врагов
    money = START_MONEY
    lives = 10
    font = pygame.font.SysFont(None, 24)
    selected_tower_type_index = 0

    while running:
        clock.tick(FPS)
        draw_path()

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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # левая кнопка мыши - поставить башню
                    mx, my = event.pos
                    for zone_rect in tower_zones:
                        if zone_rect.collidepoint(mx, my):
                            zone_taken = False
                            for tower in towers:
                                if tower.zone_rect == zone_rect:
                                    zone_taken = True
                                    break
                            if not zone_taken and money >= TOWER_COST:
                                cx = zone_rect.x + zone_rect.width // 2
                                cy = zone_rect.y + zone_rect.height // 2
                                tower_type = tower_types[selected_tower_type_index]
                                towers.append(Tower(cx, cy, zone_rect, tower_type))
                                money -= TOWER_COST
                            break

        # Спавн врагов
        spawn_timer += 1
        if spawn_timer >= spawn_interval:
            enemies.append(Enemy())
            spawn_timer = 0

        # Обновление врагов
        for enemy in enemies[:]:
            alive = enemy.update()
            if not alive:
                # Враг добрался до конца - уменьшаем жизни
                lives -= 1
                enemies.remove(enemy)
            elif not enemy.alive:
                # Враг убит - даём деньги
                money += 50
                enemies.remove(enemy)

        # Обновление башен
        for tower in towers:
            tower.update(enemies, bullets)

        # Обновление пуль
        for bullet in bullets[:]:
            bullet.update()
            if not bullet.alive:
                bullets.remove(bullet)

        # Отрисовка башен, врагов, пуль
        for tower in towers:
            tower.draw()
        for enemy in enemies:
            enemy.draw()
        for bullet in bullets:
            bullet.draw()

        # Отображение HUD
        money_text = font.render(f"Money: {money}", True, BLACK)
        lives_text = font.render(f"Lives: {lives}", True, BLACK)
        screen.blit(money_text, (10, 10))
        screen.blit(lives_text, (10, 30))

        # Отображаем выбранный тип башни
        selected_type = tower_types[selected_tower_type_index]
        tower_info = font.render(f"Selected Tower: {selected_type.name} (1-3 to change)", True, BLACK)
        screen.blit(tower_info, (10, 50))

        if lives <= 0:
            game_over_text = font.render("Game Over! Press ESC to quit.", True, RED)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            wait_for_exit()
            running = False

        pygame.display.flip()

    pygame.quit()
    sys.exit()

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

if __name__ == "__main__":
    main()
>>>>>>> 0c64791d9d0c22478c150ae9b88bf5688e114257
