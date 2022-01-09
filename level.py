import pygame
import random as rnd
import math
import os
import sys
import sqlite3
from particles import initilize_snow, snowfall, create_particles, particles
import time


pygame.init()
size = width, height = 1000, 1000
screen = pygame.display.set_mode(size)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', 'images', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


background = pygame.Color('#d3ad8d')
text_color = pygame.Color('#8c4d2c')
button_color = pygame.Color('#2C7E8C')
images = {'house': load_image('house.png'), 'people': load_image('people.png'),
          'cancel': load_image('cancel.png'), 'setting': load_image('setting.png'),
          'sound': load_image('sound.png'), 'snow': load_image('snow.png')}
grass = [pygame.Color(240, 240, 240), pygame.Color('#bad5dc'), pygame.Color('#e3e8ee'),
         pygame.Color('#d4dfe5'), pygame.Color('#a5b4b9'), pygame.Color('#b4b4af')]
all_sprites = pygame.sprite.Group()
error_sprites = pygame.sprite.Group()
setting_sprites = pygame.sprite.Group()
study_sprites = pygame.sprite.Group()
animated_sprites = pygame.sprite.Group()
clock = pygame.time.Clock()

con = sqlite3.connect(os.path.join('data', 'database', "levels"))
cur = con.cursor()

snow = True if cur.execute("""SELECT value FROM setting WHERE name = 'snow'""").fetchone()[0] == 'True' else False
sound = True if cur.execute("""SELECT value FROM setting WHERE name = 'sound'""").fetchone()[0] == 'True' else False
music = list({'Last Christmas.mp3', 'Happy New Year.mp3', "It Doesn't Have to Be That Way.mp3", "Jingle Bells.mp3",
                 "Let It Snow.mp3", "Thanks god its christmas.mp3", "We wish you a merry Christmas.mp3"})
pygame.mixer.music.load(os.path.join('data', 'music', music[0]))
sound_button = pygame.mixer.Sound(os.path.join('data', 'music', 'button sound.mp3'))
sound_cell = pygame.mixer.Sound(os.path.join('data', 'music', 'cell sound.mp3'))
sound_complete = pygame.mixer.Sound(os.path.join('data', 'music', 'complete.mp3'))
sound_fail = pygame.mixer.Sound(os.path.join('data', 'music', 'directed by.mp3'))
pygame.mixer.music.queue(os.path.join('data', 'music', music[1]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[2]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[3]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[4]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[5]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[6]))
if sound:
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(0.7)
    play_music = True
else:
    play_music = False
if snow:
    initilize_snow()
    play_snow = True
else:
    play_snow = False


class Board:
    def __init__(self, w, h, id, load=None, pic=None):
        self.id = id
        self.cell_size = (width - 400) // w
        self.left = (width - (w * self.cell_size)) // 2
        self.top = (height - (h * self.cell_size)) // 2
        self.stop = False
        if not load:
            self.width = w
            self.height = h
            self.board = [[0] * w for _ in range(h)]
            self.player = [[0] * w for _ in range(h)]
            self.step = None
            self.houses = []
            self.peoples = []
            self.numbers = []
            self.steps = []
            self.set_houses()
            self.set_peoples()
            self.set_numbers()
            self.set_grass()
            insert = """INSERT INTO level
                                      (id, width, height, board, player, step, cell_size, left, top, numbers, steps)
                                      VALUES
                                      (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            values = (str(self.id), str(self.width), str(self.height), self.coding(self.board, 'board'),
                      self.coding(self.player, 'player'), str(self.step), str(self.cell_size), str(self.left), str(self.top),
                      self.coding(self.numbers, 'numbers'), self.coding(self.steps, 'steps'))
            cur.execute(insert, values)
            con.commit()
        else:
            self.load_board(pic)

    def coding(self, data, name):
        if name == 'board' or name == 'player':
            return '.'.join([' '.join(list(map(str, i))) for i in data])
        else:
            return '%'.join(['.'.join([' '.join(list(map(str, j))) for j in i]) for i in data])

    def uncoding(self, data, name):
        if name == 'board' or name == 'player':
            return [list(map(int, i.split(' '))) for i in data.split('.')]
        elif name == 'numbers':
            return [[[int(j.split(' ')[0]), bool(j.split(' ')[1])] for j in i.split('.')] for i in data.split('%')]
        else:
            return [[[int(j.split(' ')[0]), int(j.split(' ')[1])] for j in i.split('.')] for i in data.split('%')]

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def load_board(self, pic, new=False):
        result = cur.execute(f"""SELECT * FROM level
                    WHERE id == '{self.id}'""").fetchall()
        self.width = int(result[0][1])
        self.height = int(result[0][2])
        self.board = self.uncoding(result[0][3], 'board')
        self.player = self.uncoding(result[0][4], 'player')
        self.step = True if result[0][5] == 'True' else None
        self.cell_size = int(result[0][6])
        self.left = int(result[0][7])
        self.top = int(result[0][8])
        self.numbers = self.uncoding(result[0][9], 'numbers')
        self.steps = self.uncoding(result[0][10], 'steps') if result[0][10] else []
        if self.check() is True and not pic or new:
            global all_sprites, error_sprites, setting_sprites, animated_sprites
            all_sprites = pygame.sprite.Group()
            error_sprites = pygame.sprite.Group()
            setting_sprites = pygame.sprite.Group()
            animated_sprites = pygame.sprite.Group()
            self.step = None
            self.player = [[0] * self.width for _ in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    if self.board[y][x] == 2:
                        self.player[y][x] = 2
            self.set_numbers()

    def render(self, pic=None, d=None):
        global all_sprites
        if not pic:
            pygame.draw.rect(screen, button_color, ((20, 20), (70, 70)), border_radius=20)
            font = pygame.font.Font(None, 40)
            text = font.render("Обучение", True, background)
            text_w = text.get_width()
            text_h = text.get_height()
            text_x = width - text_w - 30
            text_y = 30
            r_r = ((text_x - 10, text_y - 10), (text_w + 20, text_h + 20))
            pygame.draw.rect(screen, button_color, r_r, border_radius=20)
            screen.blit(text, (text_x, text_y))
            pygame.draw.rect(screen, button_color, ((20, 20), (70, 70)), border_radius=20)
            pygame.draw.rect(screen, button_color, ((100, 20), (70, 70)), border_radius=20)
            if not any(map(lambda i: i.rect.collidepoint(102, 22), all_sprites)):
                Objects(all_sprites, images, 'cancel', 102, 22, 64)
            if not any(map(lambda i: i.rect.collidepoint(22, 22), all_sprites)):
                Objects(all_sprites, images, 'setting', 22, 22, 64)
        for y in range(self.height):
            for x in range(self.width):
                r_r = ((self.left + x * self.cell_size, self.top + y * self.cell_size),
                       (self.cell_size, self.cell_size))
                if not d or [x, y] not in d:
                    if self.player[y][x] == 2:
                        pygame.draw.rect(screen, grass[0], r_r, border_radius=20)
                        color = background
                        if not any(map(lambda i: i.rect.x == self.left + x * self.cell_size + 2 and
                                                 i.rect.y == self.top + y * self.cell_size - 2,
                                       animated_sprites)):
                            AnimatedSprite(animated_sprites, images, 'people', 5, 1, r_r[0][0] + 2, r_r[0][1] - 2,
                                          self.cell_size - 4)
                    elif self.player[y][x] == 0:
                        pygame.draw.rect(screen, background, r_r, border_radius=20)
                        pygame.draw.rect(screen, text_color, (r_r[0][0] + 5, r_r[0][1] + 5,
                                                           r_r[1][0] - 10, r_r[1][1] - 10), 3)
                        color = text_color
                    elif self.player[y][x] == 1:
                        pygame.draw.rect(screen, grass[0], r_r, border_radius=20)
                        if not any(map(lambda i: i.rect.collidepoint(self.left + x * self.cell_size + 1,
                                                                     self.top + y * self.cell_size + 1),
                                       all_sprites)):
                            Objects(all_sprites, images, 'house', r_r[0][0] + 1, r_r[0][1] + 1, self.cell_size - 2)
                        color = background
                    else:
                        pygame.draw.rect(screen, grass[self.player[y][x] - 3], r_r, border_radius=20)
                        color = background
                    pygame.draw.rect(screen, color, r_r, 3)
                if y == 0 or x == 0:
                    if x == 0 and y == 0:
                        num1 = self.numbers[y][x]
                        num2 = self.numbers[1][y]
                        arg = 'w'
                        self.draw_num(num2, r_r, 'h', [x, y])
                    elif y == 0:
                        num1 = self.numbers[y][x]
                        arg = 'w'
                    else:
                        num1 = self.numbers[1][y]
                        arg = 'h'
                    self.draw_num(num1, r_r, arg, [x, y])
        if len(list(filter(lambda j: j[1] is True, self.numbers[0]))) == len(self.numbers[0]) and \
                len(list(filter(lambda j: j[1] is True, self.numbers[1]))) == len(self.numbers[1]) and \
                not self.step and not self.stop:
            check = self.check()
            if check is True:
                self.stop = True
            error(check, self, pic)
            self.step = True
            global error_sprites
            error_sprites = pygame.sprite.Group()

    def draw_grass(self, *args):
        data = []
        for i in args:
            x, y = i
            r_r = ((self.left + x * self.cell_size, self.top + y * self.cell_size), (self.cell_size, self.cell_size))
            pos = ((r_r[0][0] + self.cell_size / 2, r_r[0][1] + self.cell_size / 2), (0, 0))
            pygame.draw.rect(screen, background, r_r, 3)
            pygame.draw.rect(screen, background, (r_r[0][0] + 5, r_r[0][1] + 5,
                                                  r_r[1][0] - 10, r_r[1][1] - 10), 3)
            data.append([pos, r_r])
        while data[0][0][0][0] > data[0][1][0][0]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.get_click(event.pos)
                    self.render()
                    return
            screen.fill(background)
            run_snow()
            self.render(d=list(args))
            for i in range(len(data)):
                pygame.draw.rect(screen, grass[self.player[args[i][1]][args[i][0]] - 3], data[i][0], border_radius=15)
                pygame.draw.rect(screen, text_color, data[i][1], 3)
                data[i][0] = ((data[i][0][0][0] - 5, data[i][0][0][1] - 5),
                              (data[i][0][1][0] + 10, data[i][0][1][1] + 10))
            all_sprites.draw(screen)
            animated_sprites.draw(screen)
            animated_sprites.update()
            pygame.display.flip()
            clock.tick(50)

    def check(self):
        a = 0
        for i in range(self.height):
            if self.player[i] == self.board[i]:
                a += 1
        if a == self.height:
            return True
        for i in range(self.height):
            for j in range(self.width):
                if self.player[j][i] == 1:
                    neighbors = self.get_neighbors(i, j)
                    b = list(map(lambda x: self.player[x[1]][x[0]] == 1, neighbors))
                    if any(b):
                        return ['houses', [i, j], neighbors[b.index(True)]]
                    if not any(list(map(lambda x: self.player[x[1]][x[0]] == 2, neighbors))):
                        return ['house', [i, j]]
                elif self.player[j][i] == 2:
                    neighbors = self.get_neighbors(i, j, True)
                    if not any(list(map(lambda x: self.player[x[1]][x[0]] == 1, neighbors))):
                        return ['people', [i, j]]
        return True

    def draw_num(self, num, r_r, arg, pos):
        font = pygame.font.Font(None, self.cell_size)
        text = font.render(str(num[0]), True, '#8c4d2c')
        text_w = text.get_width()
        text_h = text.get_height()
        x, y = pos
        if arg == 'w':
            text_x = r_r[0][0] + (r_r[1][0] - text_w) // 2
            text_y = r_r[0][1] - (r_r[1][1] - text_h) // 2 - text_h
            if self.numbers[y][x][0] == sum([i[x] for i in self.player if i[x] == 1]):
                color = '#217219'
                flag = True
            elif self.numbers[y][x][0] < sum([i[x] for i in self.player if i[x] == 1]) or \
                    self.numbers[y][x][0] > sum([i[x] for i in self.player if i[x] == 1]) and \
                    all(list(map(lambda i: i[x] != 0, self.player))):
                color = '#B43D29'
                flag = False
            else:
                color = '#8c4d2c'
                flag = None
            self.numbers[y][x][-1] = flag
        else:
            text_x = r_r[0][0] - (r_r[1][0] - text_w) // 2 - text_w
            text_y = r_r[0][1] + (r_r[1][1] - text_h) // 2
            if self.numbers[1][y][0] == sum(list(map(lambda i: i == 1, self.player[y]))):
                color = '#217219'
                flag = True
            elif self.numbers[1][y][0] < sum(list(map(lambda i: i == 1, self.player[y]))) or \
                    self.numbers[1][y][0] > sum(list(map(lambda i: i == 1 and i != 0, self.player[y]))) and \
                    all(list(map(lambda i: i != 0, self.player[y]))):
                color = '#B43D29'
                flag = False
            else:
                color = '#8c4d2c'
                flag = None
            self.numbers[1][y][-1] = flag
        text = font.render(str(num[0]), True, color)
        screen.blit(text, (text_x, text_y))
        if flag is True:
            pygame.draw.line(screen, color, [text_x + text_w + 3, text_y + text_h // 2],
                             [text_x + text_w + 7, text_y + text_h // 2 + 8], 5)
            pygame.draw.line(screen, color, [text_x + text_w + 7, text_y + text_h // 2 + 8],
                             [text_x + text_w + 11, text_y + text_h // 2 - 2], 5)
        elif flag is False:
            pygame.draw.line(screen, color, [text_x + text_w + 3, text_y + text_h // 2 - 2],
                             [text_x + text_w + 11, text_y + text_h // 2 + 6], 5)
            pygame.draw.line(screen, color, [text_x + text_w + 3, text_y + text_h // 2 + 6],
                             [text_x + text_w + 11, text_y + text_h // 2 - 2], 5)
        insert = f"UPDATE level SET numbers = '{self.coding(self.numbers, 'numbers')}' WHERE id = '{self.id}';"
        cur.execute(insert)
        con.commit()

    def get_cell(self, mouse_pos):
        if 100 <= mouse_pos[0] <= 170 and 20 <= mouse_pos[1] <= 90:
            return 'cancel'
        if 20 <= mouse_pos[0] <= 90 and 20 <= mouse_pos[1] <= 90:
            return 'setting'
        if 830 <= mouse_pos[0] <= 980 and 20 <= mouse_pos[1] <= 68:
            return 'study'
        if self.cell_size <= mouse_pos[0] <= self.left and \
                mouse_pos[1] in range(self.top, self.cell_size * self.height + self.top + 1):
            return (-1, (mouse_pos[1] - self.top) // self.cell_size)
        elif self.cell_size <= mouse_pos[1] <= self.top and \
                mouse_pos[0] in range(self.left, self.cell_size * self.width + self.left + 1):
            return ((mouse_pos[0] - self.left) // self.cell_size, -1)
        x_click = (mouse_pos[0] - self.left) // self.cell_size
        y_click = (mouse_pos[1] - self.top) // self.cell_size
        if x_click < 0 or x_click >= self.width or y_click < 0 or y_click >= self.height:
            return None
        return (x_click, y_click)

    def on_click(self, cell_coords):
        if cell_coords and cell_coords != 'cancel' and cell_coords != 'setting' and cell_coords != 'study':
            if sound:
                sound_cell.play()
            self.step = None
            x, y = cell_coords
            if self.player[y][x] != 2 and x >= 0 and y >= 0:
                self.steps.append([cell_coords])
            a = []
            if y < 0:
                if self.numbers[0][x][-1] is True:
                    for i in range(self.height):
                        if self.player[i][x] == 0:
                            if self.board[i][x] in range(3, 7):
                                self.player[i][x] = self.board[i][x]
                            else:
                                self.player[i][x] = rnd.randint(3, 6)
                            a.append([x, i])
                self.draw_grass(*a)
            elif x < 0:
                if self.numbers[1][y][-1] is True:
                    for i in range(self.width):
                        if self.player[y][i] == 0:
                            if self.board[y][i] in range(3, 7):
                                self.player[y][i] = self.board[y][i]
                            else:
                                self.player[y][i] = rnd.randint(3, 6)
                            a.append([i, y])
                self.draw_grass(*a)
            else:
                if self.player[y][x] in range(3, 7):
                    self.player[y][x] = 1
                elif self.player[y][x] == 0:
                    if self.board[y][x] in range(3, 7):
                        self.player[y][x] = self.board[y][x]
                    else:
                        self.player[y][x] = rnd.randint(3, 6)
                    self.draw_grass([x, y])
                elif self.player[y][x] == 1:
                    self.player[y][x] = 0
                    for i in all_sprites:
                        if i.rect.collidepoint(self.left + x * self.cell_size + 1, self.top + y * self.cell_size + 1):
                            i.kill()
                            break
            if a:
                self.steps.append(a)
        elif cell_coords == 'cancel':
            if sound:
                sound_button.play()
            self.cancel()
        elif cell_coords == 'setting':
            if sound:
                sound_button.play()
            setting(self)
        elif cell_coords == 'study':
            if sound:
                sound_button.play()
            study()
        insert = f"UPDATE level SET player = '{self.coding(self.player, 'player')}', step = '{str(self.step)}', " \
                 f"steps = '{self.coding(self.steps, 'steps')}' WHERE id = '{self.id}';"
        cur.execute(insert)
        con.commit()

    def cancel(self):
        if self.steps:
            for j in self.steps[-1]:
                x, y = j
                if y < 0:
                    for i in range(self.height):
                        if self.player[i][x] in range(3, 7):
                            self.player[i][x] = 0
                elif x < 0:
                    for i in range(self.width):
                        if self.player[y][i] in range(3, 7):
                            self.player[y][i] = 0
                else:
                    if self.player[y][x] in range(3, 7):
                        self.player[y][x] = 0
                    elif self.player[y][x] == 0:
                        self.player[y][x] = 1
                    elif self.player[y][x] == 1:
                        if self.board[y][x] in range(3, 7):
                            self.player[y][x] = self.board[y][x]
                        else:
                            self.player[y][x] = rnd.randint(3, 6)
                        for i in all_sprites:
                            if i.rect.collidepoint(self.left + x * self.cell_size + 1, self.top + y * self.cell_size + 1):
                                i.kill()
                                break
            self.steps = self.steps[:-1]

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def get_neighbors(self, x, y, arg=None):
        if not arg:
            return list(filter(lambda i: 0 <= i[0] < self.height and 0 <= i[1] < self.width and [i[0], i[1]] != [x, y],
                               [[i, j] for i in range(x - 1, x + 2) for j in range(y - 1, y + 2)]))
        return list(filter(lambda i: 0 <= i[0] < self.height and 0 <= i[1] < self.width,
                               [[x, y - 1], [x - 1, y], [x + 1, y], [x, y + 1]]))

    def set_houses(self):
        n = rnd.randint(self.height - 2, math.ceil(self.width / 2) * math.ceil(self.height / 2))
        for i in range(n):
            if all(list(map(lambda a: all(a), self.board))):
                break
            x, y = rnd.randint(0, self.width - 1), rnd.randint(0, self.height - 1)
            neighbors = self.get_neighbors(x, y)
            while [x, y] in self.houses or any(list(map(lambda a: self.board[a[1]][a[0]] == 1,
                                                                               neighbors))):
                x, y = rnd.randint(0, self.width - 1), rnd.randint(0, self.height - 1)
                neighbors = self.get_neighbors(x, y)
            self.houses.append([x, y])
            self.board[y][x] = 1

    def set_peoples(self):
        for i in self.houses:
            neighbors = self.get_neighbors(i[0], i[1], True)
            x, y = rnd.choice(neighbors)
            while [x, y] in self.peoples or [x, y] in self.houses:
                x, y = rnd.choice(neighbors)
            self.peoples.append([x, y])
            self.board[y][x] = 2
            self.player[y][x] = 2

    def set_grass(self):
        for i in range(self.height):
            for j in range(self.width):
                if self.board[j][i] == 0:
                    self.board[j][i] = rnd.randint(3, 6)

    def set_numbers(self):
        self.numbers = [[[[self.board[j][i] for j in range(self.height)].count(1), None] for i in range(self.width)],
                        [[i.count(1), None] for i in self.board]]


class Sprite(pygame.sprite.Sprite):
    def __init__(self, group):
        super().__init__(group)
        self.rect = None

    def get_event(self, event):
        pass


class Objects(Sprite):
    def __init__(self, sprite_group, tile_images, tile_type, pos_x, pos_y, s):
        super().__init__(sprite_group)
        self.image = tile_images[tile_type]
        self.image = pygame.transform.scale(self.image, (s, s))
        self.rect = self.image.get_rect().move(pos_x, pos_y)


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sprite_group, tile_images, tile_type, columns, rows, x, y, s):
        super().__init__(sprite_group)
        self.frames = []
        self.cut_sheet(tile_images[tile_type], columns, rows)
        self.cur_frame = 0
        self.size = s
        self.image = self.frames[self.cur_frame]
        self.image = pygame.transform.scale(self.image, (s, s))
        self.rect = self.rect.move(x, y)
        self.n = 5

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        if self.n  % 5 == 0:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]
            self.image = pygame.transform.scale(self.image, (self.size, self.size))
        self.n += 1


def error(check, board, pic):
    tile_image = {'house': load_image('cross.png'), 'people': load_image('circle.png')}
    global error_sprites
    error_sprites = pygame.sprite.Group()
    if check is True:
        end_level(board, pic)
        return
    if not pic:
        if sound:
            pygame.mixer.music.set_volume(0)
            sound_fail.play()
        if check[0] == 'houses':
            text = "Домики не могут касаться друг друга!"
            x1 = check[1][0] * board.cell_size + board.left + 2
            y1 = check[1][1] * board.cell_size + board.top + 2
            x2 = check[2][0] * board.cell_size + board.left + 2
            y2 = check[2][1] * board.cell_size + board.top + 2
            Objects(error_sprites, tile_image, 'house', x1, y1, board.cell_size - 2)
            Objects(error_sprites, tile_image, 'house', x2, y2, board.cell_size - 2)
        elif check[0] == 'house':
            text = "Рядом с домиком нет человечка!"
            x1 = check[1][0] * board.cell_size + board.left + 2
            y1 = check[1][1] * board.cell_size + board.top + 2
            Objects(error_sprites, tile_image, 'house', x1, y1, board.cell_size - 2)
        else:
            text = "Рядом с человечком нет домика!"
            x1 = check[1][0] * board.cell_size + board.left + 2
            y1 = check[1][1] * board.cell_size + board.top + 2
            Objects(error_sprites, tile_image, 'people', x1, y1, board.cell_size - 2)
        font = pygame.font.Font(None, 50)
        text = font.render(text, True, background)
        text_w = text.get_width()
        text_h = text.get_height()
        text_x = (width - text_w) // 2
        text_y = board.height * board.cell_size + board.top + (width - board.height * board.cell_size - board.top - text_h) // 2
        r_r = ((text_x - 40, text_y - 40), (text_w + 80, text_h + 80))
        pygame.draw.rect(screen, text_color, r_r, border_radius=20)
        screen.blit(text, (text_x, text_y))
        text = font.render("Oк", True, background)
        r_r2 = ((text_x + text_w, text_y + text_h + 2), (text.get_width() + 20, text.get_height() + 20))
        text_x = r_r2[0][0] + 10
        text_y = r_r2[0][1] + 10
        pygame.draw.rect(screen, button_color, r_r2, border_radius=20)
        screen.blit(text, (text_x, text_y))
        run = True
        all_sprites.draw(screen)
        error_sprites.draw(screen)
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[0] in range(r_r2[0][0], r_r2[0][0] + r_r2[1][0] + 1) and event.pos[1] in range(r_r2[0][1], r_r2[0][1] + r_r2[1][1] + 1):
                        if sound:
                            sound_fail.stop()
                            pygame.mixer.music.set_volume(0.7)
                            sound_button.play()
                        return
            pygame.display.flip()
            error_sprites.draw(screen)
            clock.tick(50)


def setting(board):
    global sound
    if sound:
        sound_button.play()
    h0 = (height - 35 * 5 - 250) // 2
    w0 = (width - 420) // 2
    draw_setting(board)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if w0 + 420 <= event.pos[0] <= w0 + 475 and h0 - 50 <= event.pos[1] <= h0 + 5:
                    if sound:
                        sound_button.play()
                    return
                elif 280 <= event.pos[0] <= 720 and 532 <= event.pos[1] <= 587:
                    if sound:
                        sound_button.play()
                    board.load_board(False, True)
                    return
                elif 280 <= event.pos[0] <= 720 and 617 <= event.pos[1] <= 672:
                    if sound:
                        sound_button.play()
                    board.stop = True
                    return
                elif 665 <= event.pos[0] <= 720 and 364 <= event.pos[1] <= 415:
                    if sound:
                        sound_button.play()
                        pygame.draw.line(screen, pygame.Color('black'), (669, 415), (714, 362), 10)
                        sound = False
                        pygame.mixer.music.pause()
                    else:
                        global play_music
                        screen.fill(background)
                        sound = True
                        if not play_music:
                            pygame.mixer.music.play()
                            pygame.mixer.music.set_volume(0.7)
                            play_music = True
                        else:
                            pygame.mixer.music.unpause()
                        draw_setting(board)
                    cur.execute(f"UPDATE setting SET value = '{sound}' WHERE name = 'sound';")
                    con.commit()
                elif 665 <= event.pos[0] <= 720 and 449 <= event.pos[1] <= 500:
                    if sound:
                        sound_button.play()
                    global snow
                    if snow:
                        pygame.draw.line(screen, pygame.Color('black'), (669, 501), (714, 447), 10)
                        snow = False
                    else:
                        screen.fill(background)
                        snow = True
                        draw_setting(board)
                    cur.execute(f"UPDATE setting SET value = '{snow}' WHERE name = 'snow';")
                    con.commit()
        pygame.display.flip()
        clock.tick(50)


def draw_setting(board):
    board.render()
    all_sprites.draw(screen)
    run_snow()
    global setting_sprites
    setting_sprites = pygame.sprite.Group()
    fon = pygame.transform.smoothscale(screen, (100, 100))
    fon = pygame.transform.scale(fon, size)
    screen.blit(fon, (0, 0))
    buttons = ['Настройки', 'Звук', 'Снежинки', 'Заново', 'Выйти в главное меню']
    h0 = (height - 35 * 5 - 250) // 2
    w0 = (width - 420) // 2
    font = pygame.font.Font(None, 50)
    for i in range(len(buttons)):
        t = buttons[i]
        border = None if t == 'Настройки' else True
        text = font.render(t, True, background)
        if t != 'Настройки':
            text_x = w0
        else:
            text_x = (width - text.get_width()) // 2
        text_y = h0 + 50 * i + 35 * i
        r_r = ((w0 - 25, text_y - 25), (470, 85))
        pygame.draw.rect(screen, button_color, r_r)
        if border:
            pygame.draw.rect(screen, background, ((r_r[0][0] + 5, r_r[0][1] + 5), (r_r[1][0] - 10, r_r[1][1] - 10)), 10)
        if t == 'Звук':
            pygame.draw.rect(screen, background, ((r_r[0][0] + 390, r_r[0][1] + 5), (75, 75)), 10)
            Objects(setting_sprites, images, 'sound', r_r[0][0] + 402, r_r[0][1] + 17, 51)
        elif t == 'Снежинки':
            pygame.draw.rect(screen, background, ((r_r[0][0] + 390, r_r[0][1] + 5), (75, 75)), 10)
            Objects(setting_sprites, images, 'snow', r_r[0][0] + 402, r_r[0][1] + 17, 51)
        screen.blit(text, (text_x, text_y))
    pygame.draw.rect(screen, text_color, ((w0 + 420, h0 - 50), (55, 55)))
    pygame.draw.line(screen, pygame.Color('black'), (w0 + 427, h0 - 45), (w0 + 468, h0), 10)
    pygame.draw.line(screen, pygame.Color('black'), (w0 + 468, h0 - 45), (w0 + 427, h0), 10)
    if not snow:
        pygame.draw.line(screen, pygame.Color('black'), (669, 501), (714, 447), 10)
    if not sound:
        pygame.draw.line(screen, pygame.Color('black'), (669, 415), (714, 362), 10)
    setting_sprites.draw(screen)


def end_level(board, pic=None):
    draw_end(board, pic)
    if not pic:
        if sound:
            pygame.mixer.music.set_volume(0)
            sound_complete.play()
        r_r = ((116, 585), (768, 64))
        for i in range(30, 941, 188):
            pos = (rnd.randint(i, i + 150), rnd.randint(100, 250))
            create_particles(pos, (0, 0, width, 300))
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if r_r[0][0] <= event.pos[0] <= r_r[1][0] + r_r[0][0] and r_r[0][1] <= event.pos[1] <= r_r[1][1] + r_r[0][1]:
                        if sound:
                            sound_complete.stop()
                            pygame.mixer.music.set_volume(0.7)
                            sound_button.play()
                        return
            screen.fill(background)
            draw_end(board, pic)
            particles.draw(screen)
            particles.update()
            pygame.display.flip()
            clock.tick(10)


def draw_end(board, pic=None):
    global all_sprites, animated_sprites
    s, k = (50, 25) if pic else (100, 50)
    if pic:
        all_sprites = pygame.sprite.Group()
        animated_sprites = pygame.sprite.Group()
    else:
        board.render()
        all_sprites.draw(screen)
        run_snow()
    fon = pygame.transform.smoothscale(screen, (70, 70))
    fon = pygame.transform.scale(fon, size)
    font = pygame.font.Font(None, s)
    text = font.render("Уровень завершен!", True, text_color)
    text_w = text.get_width()
    text_h = text.get_height()
    text_x = (width - text_w) // 2
    text_y = (height - text_h) // 2
    r_r = ((text_x - k, text_y - k), (text_w + k * 2, text_h + k * 2))
    screen.blit(fon, (0, 0))
    pygame.draw.rect(screen, background, r_r, border_radius=20)
    pygame.draw.rect(screen, text_color, r_r, k // 5, border_radius=20)
    screen.blit(text, (text_x, text_y))
    if not pic:
        font = pygame.font.Font(None, 50)
        text = font.render("Выйти в главное меню", True, background)
        text_w = text.get_width()
        text_h = text.get_height()
        text_x = (width - text_w) // 2
        text_y = r_r[0][1] + r_r[1][1] + 25
        r_r = ((r_r[0][0], text_y - 25), (r_r[1][0], text_h + 50))
        pygame.draw.rect(screen, button_color, r_r, border_radius=20)
        screen.blit(text, (text_x, text_y))


def run_snow():
    if snow:
        snowfall.draw(screen)
        snowfall.update()
        time.sleep(0.04)


def study():
    h0 = 180
    w0 = 200
    w = width - w0 * 2
    draw_study()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if w0 + w - 27 <= event.pos[0] <= w0 + w + 28 and h0 - 25 <= event.pos[1] <= h0 + 25:
                    if sound:
                        sound_button.play()
                    return
        pygame.display.flip()
        clock.tick(50)


def draw_study():
    run_snow()
    fon = pygame.transform.smoothscale(screen, (100, 100))
    fon = pygame.transform.scale(fon, size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 35)
    h0 = 180
    w0 = 200
    w = width - w0 * 2
    h = 750
    t = 'Человечки расположены\n' \
        'по сетке.\n' \
        'Вам нужно поместить один домик\n' \
        'рядом с каждым человечком.\n'\
        'В других клетках должен быть снег\n' \
        'Цифры сверху и справа от сетки\n' \
        'показывают число домиков в\n' \
        'строке или столбце.\n' \
        'Каждый домик должен быть в одной\n' \
        'из четырех соседних клеток человечка\n'\
        '(по горизонтали или по вертикали,\n' \
        'но не по диагонали).\n'\
        'Домики не могут касаться друг друга,\n' \
        'даже по диагонали.\n' \
        'Чтобы установить снег нажмите\n' \
        'на пустую клетку.\n' \
        'Чтобы установить домик нажмите\n' \
        'на клетку со снегом.\n' \
        'При нажатии на зеленую цифру\n' \
        'все пустые поля заполняются снегом.'
    t1 = []
    pygame.draw.rect(screen, text_color, ((w0, h0), (w, h)), border_radius=20)
    pygame.draw.rect(screen, button_color, ((w0 + w - 27, h0 - 25), (55, 55)))
    pygame.draw.line(screen, pygame.Color('black'), (w0 + w - 25, h0 - 20), (w0 + w + 26, h0 + 20), 10)
    pygame.draw.line(screen, pygame.Color('black'), (w0 + w + 26, h0 - 20), (w0 + w - 25, h0 + 20), 10)
    for i in range(len(t.split('\n'))):
        if t.split('\n')[i] == 'Человечки расположены':
            text0 = font.render('Человечки расположены', True, background)
            text1 = font.render('Человечки ', True, background)
            text_x = w0 + (w - text0.get_width() - 50) // 2
            text_y = h0 + 30 + 35 * i
            if not any(map(lambda i: i.rect.collidepoint(text_x + text1.get_width(), text_y - 20), study_sprites)):
                Objects(study_sprites, images, 'people', text_x + text1.get_width(), text_y - 20, 50)
            t1.append([text1, text_x, text_y])
            text = font.render(' расположены', True, background)
            text_x += text1.get_width() + 50
        elif t.split('\n')[i] == 'Вам нужно поместить один домик':
            text = font.render('Вам нужно поместить один домик ', True, background)
            text_x = w0 + (w - text.get_width() - 40) // 2
            text_y = h0 + 30 + 35 * i
            if not any(map(lambda i: i.rect.collidepoint(text_x + text.get_width(), text_y - 20), study_sprites)):
                Objects(study_sprites, images, 'house', text_x + text.get_width(), text_y - 20, 50)
        elif t.split('\n')[i] == 'В других клетках должен быть снег':
            text = font.render('В других клетках должен быть снег ', True, background)
            text_x = w0 + (w - text.get_width() - 40) // 2
            text_y = h0 + 30 + 35 * i
            pygame.draw.rect(screen, grass[0], ((text_x + text.get_width(), text_y - 20), (50, 50)), border_radius=20)
        else:
            text = font.render(t.split('\n')[i], True, background)
            text_x = w0 + (w - text.get_width()) // 2
            text_y = h0 + 30 + 35 * i
        t1.append([text, text_x, text_y])
    study_sprites.draw(screen)
    for i in t1:
        screen.blit(i[0], (i[1], i[2]))


def main(n, id, pos_x=200, pos_y=200, load=None, pic=None):
    global all_sprites, error_sprites, screen, width, height, size, snow, sound, play_snow, animated_sprites
    snow = True if cur.execute("""SELECT value FROM setting WHERE name = 'snow'""").fetchone()[0] == 'True' else False
    sound = True if cur.execute("""SELECT value FROM setting WHERE name = 'sound'""").fetchone()[0] == 'True' else False
    all_sprites = pygame.sprite.Group()
    error_sprites = pygame.sprite.Group()
    animated_sprites = pygame.sprite.Group()
    size = width, height = 1000, 1000
    screen = pygame.display.set_mode(size)
    if not pic:
        screen.fill(background)
        board = Board(n, n, id, load)
        board.set_view(pos_x, pos_y, (width - pos_x - pos_y) // n)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    board.get_click(event.pos)
                    board.render()
            screen.fill(background)
            if board.stop:
                return
            if snow and not play_snow:
                initilize_snow()
                play_snow = True
            run_snow()
            board.render()
            all_sprites.draw(screen)
            animated_sprites.draw(screen)
            animated_sprites.update()
            pygame.display.flip()
            clock.tick(50)
        con.close()
        return
    else:
        width, height = size = width - pos_x * 2, height - pos_y * 2
        screen = pygame.Surface((width, height))
        screen.fill(background)
        x, y = width // (n + 1), height // (n + 1)
        board = Board(n, n, id, load, pic)
        board.set_view(x, y, width // (n + 1))
        board.render(True)
        all_sprites.draw(screen)
        animated_sprites.draw(screen)
        return