from pygame import *
import math
import random

# Константы экрана
SCREEN_WIDTH = 512
SCREEN_HEIGHT = 512
FPS = 60

# Параметры спрайтов
SPRITE_SIZE = 32
ANIMATION_SPEED = 8


class Object(sprite.Sprite):
    def __init__(self, image_path, x, y, width, height, speed):
        super().__init__()
        self.image = transform.scale(image.load(image_path), (width, height))
        self.speed = speed
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))















game = True

window = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Tower Defence")
clock = time.Clock()