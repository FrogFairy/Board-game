import pygame
import os
import random as rnd
import time
import sys


pygame.init()
size = width, height = 1000, 1000
screen = pygame.display.set_mode(size)


def load_image(name, color_key=None):
    fullname = os.path.join('data', 'images', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image

background = pygame.Color('#d3ad8d')
images = [load_image('snow1.png'), load_image('snow2.png'), load_image('snow3.png'), load_image('snow4.png'),
          load_image('snow5.png'), load_image('snow6.png'), load_image('snow7.png'), load_image('snow8.png'),
          load_image('snow9.png'), load_image('snow10.png')]
snowfall = pygame.sprite.Group()
particles = pygame.sprite.Group()
clock = pygame.time.Clock()

# класс снега
class Snow(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(snowfall)
        # случайно выбираем изображение, размер и скорость
        self.image = rnd.choice(images)
        self.size = rnd.randint(10, 100)
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.speed = rnd.randint(1, 5)

    def update(self):
        self.rect.y += self.speed
        # если снежинка вылетела за пределы экрана отрисовываем ее сверху
        if self.rect.y > height:
            self.rect.y = -self.size
        # выбираем случайное направление
        i = rnd.randint(1, 3)
        if i == 1:  # поворот направо
            self.rect.x += 1
            if self.rect.x > width:
                self.rect.x = -self.size
        elif i == 2:  # поворот налево
            self.rect.x -= 1
            if self.rect.x < -self.size:
                self.rect.x = width


def initilize_snow():
    # генерируем 50 снежинок
    for i in range(0, 50):
        x = rnd.randint(0, width)
        y = rnd.randint(0, height)
        Snow(x, y)


class Fireworks(pygame.sprite.Sprite):
    def __init__(self, pos, color, screen_rect):
        super().__init__(particles)
        # смещение точек
        self.move = [[-10, 0], [10, 0], [0, 10], [0, -10],
                       [10, 10], [-10, 10], [-10, -10], [10, -10],
                       [-15, 5], [-10, 5], [-5, 10], [-5, 15],
                       [15, 5], [10, 5], [5, 10], [5, 15],
                       [15, -5], [10, -5], [5, -10], [5, -15],
                       [-15, -5], [-10, -5], [-5, -10], [-5, -15]]
        # точки и цвета
        self.points = [[[100, 100]] for _ in range(24)]
        self.colors = [[0, 0, 0] for _ in range(24)]
        # в color передается 0, 1 или 2 - r, g или b соотвественно.
        # Меняется только этот параметр, остальные остаются 0
        for i in range(len(self.colors)):
            self.colors[i][color] = rnd.randint(50, 255)
        self.screen_rect = screen_rect
        self.pos = pos
        self.size = [200, 200]
        self.image = pygame.Surface(self.size, pygame.SRCALPHA, 32)
        self.image = self.image.convert_alpha()
        self.image.fill([0, 0, 0, 0])
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = self.pos[0] - self.size[0] / 2, self.pos[1] - self.size[1] / 2
        self.gravity = 3
        # флаг означает, начали ли точки падать вниз
        self.flag = False

    def update(self):
        # у image делаем прозрачный фон
        self.image.fill((0, 0, 0, 0))
        for i in range(24):
            # если точка дошла до "края" прямоугольника, все точки,
            # нарисованные по этой линии удаляются, а точка падает вниз
            if not (self.pos[0] - 100 <= self.points[i][-1][0] + self.rect.x <= self.pos[0] + 100
                    and
                    self.pos[1] - 100 <= self.points[i][-1][0] + self.rect.y <= self.pos[1] + 100)\
                    or self.flag:
                if len(self.points[i]) > 1:
                    del self.points[i][0]
                self.flag = True
            # иначе добавляем в линию этой точки еще одну с координатой + смещением
            else:
                self.points[i].append([self.points[i][-1][0] + self.move[i][0],
                                       self.points[i][-1][1] + self.move[i][1]])
            # если мы удалили все ненужные точки, точка начинает падать вниз
            if len(self.points[i]) == 1:
                self.move[i][1] = self.gravity if self.move[i][1] < 0 else self.move[i][1] + self.gravity
                self.move[i][0] = 0
                self.points[i][-1][0] += self.move[i][0]
                self.points[i][-1][1] += self.move[i][1]
            # отрисовываем всю линию точек
            for j in range(len(self.points[i])):
                pygame.draw.circle(self.image, self.colors[i], (self.points[i][j][0], self.points[i][j][1]), 5)
            if not self.rect.colliderect(self.screen_rect):
                self.kill()


def create_particles(position, screen_rect):
    # генерирует фейерверк по координатам
    Fireworks(position, rnd.randint(0, 2), screen_rect)