import pygame
import os
import random as rnd
import time
import sys


pygame.init()
size = width, height = 1000, 1000
screen = pygame.display.set_mode(size)
screen_rect = (0, 0, width, height)


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

class Snow(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__(snowfall)
        self.image = rnd.choice(images)
        self.size = rnd.randint(10, 100)
        self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.speed = rnd.randint(1, 3)

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > height:
            self.rect.y = -self.size
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
    for i in range(0, 50):
        x = rnd.randint(0, width)
        y = rnd.randint(0, height)
        Snow(x, y)


class Particles(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, pos, dx, dy):
        super().__init__(particles)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = 1

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(screen_rect):
            self.kill()


def create_particles(position):
    particle_count = 20
    numbers = range(-5, 20)
    for _ in range(particle_count):
        Particles(load_image("particles2.png"), 2, 1, position, rnd.choice(numbers), rnd.choice(numbers))


def main():
    screen.fill((0, 0, 0))
    running = True
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                create_particles(pygame.mouse.get_pos())
        screen.fill((255, 255, 255))
        particles.draw(screen)
        particles.update()
        clock.tick(10)
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()