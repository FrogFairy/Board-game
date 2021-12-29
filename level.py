import pygame
import random as rnd
import math
import os
import sys
import sqlite3


pygame.init()
size = width, height = 1000, 1000
cell_count = 6
background = pygame.Color('#d3ad8d')
text_color = pygame.Color('#8c4d2c')
button_color = pygame.Color('#2C7E8C')
all_sprites = pygame.sprite.Group()
error_sprites = pygame.sprite.Group()
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
screen_rect = (0, 0, width, height)

con = sqlite3.connect("films_db.sqlite")
cur = con.cursor()

result = cur.execute("""SELECT * FROM films
            WHERE year = 2010""").fetchall()
for elem in result:
    print(elem)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
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


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]  # 1 - домик, 2 - человечек, 3-6 - трава
        self.player = [[0] * width for _ in range(height)]
        self.step = None
        self.cell_size = 300
        self.left = (width - (self.width * self.cell_size)) // 2
        self.top = (height - (self.height * self.cell_size)) // 2
        self.houses = []
        self.peoples = []
        self.numbers = []
        self.steps = []
        self.images = {'house': load_image('house.png'), 'people': load_image('people.png'),
                       'cancel': load_image('cancel.png')}
        self.grass = [pygame.Color(240, 240, 240), pygame.Color('#bad5dc'), pygame.Color('#e3e8ee'),
                      pygame.Color('#d4dfe5'), pygame.Color('#a5b4b9'), pygame.Color('#b4b4af')]
        self.set_houses()
        self.set_peoples()
        self.set_numbers()
        self.set_grass()

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size

    def load_board(self):
        pass

    def render(self):
        pygame.draw.rect(screen, button_color, ((20, 20), (70, 70)), border_radius=20)
        if all(list(map(lambda x: 1 not in x and 3 not in x and 4 not in x and
                                                                    5 not in x and 6 not in x, self.player))):
            Objects(self.images, 'cancel', 22, 22, 64)
        for y in range(self.height):
            for x in range(self.width):
                r_r = ((self.left + x * self.cell_size, self.top + y * self.cell_size), (self.cell_size, self.cell_size))
                if self.player[y][x] == 2:
                    pygame.draw.rect(screen, self.grass[0], r_r, border_radius=20)
                    color = background
                    if all(list(map(lambda x: 1 not in x and 3 not in x and 4 not in x and
                                                                    5 not in x and 6 not in x, self.player))):
                        Objects(self.images, 'people', r_r[0][0] + 1, r_r[0][1] + 1, self.cell_size - 2)
                elif self.player[y][x] == 0:
                    pygame.draw.rect(screen, background, r_r, border_radius=20)
                    pygame.draw.rect(screen, text_color, (r_r[0][0] + 5, r_r[0][1] + 5,
                                                       r_r[1][0] - 10, r_r[1][1] - 10), 3)
                    color = text_color
                elif self.player[y][x] == 1:
                    pygame.draw.rect(screen, self.grass[0], r_r, border_radius=20)
                    Objects(self.images, 'house', r_r[0][0] + 1, r_r[0][1] + 1, self.cell_size - 2)
                    color = background
                else:
                    pygame.draw.rect(screen, self.grass[self.player[y][x] - 3], r_r, border_radius=20)
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
                len(list(filter(lambda j: j[1] is True, self.numbers[1]))) == len(self.numbers[1]) and not self.step:
                check = self.check()
                error(check, self.height, self.width, self.cell_size, self.top, self.left)
                self.step = True
                global error_sprites
                error_sprites = pygame.sprite.Group()


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

    def get_cell(self, mouse_pos):
        if 20 <= mouse_pos[0] <= 90 and 20 <= mouse_pos[1] <= 90:
            return 'cancel'
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
        if cell_coords and cell_coords != 'cancel':
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
            elif x < 0:
                if self.numbers[1][y][-1] is True:
                    for i in range(self.width):
                        if self.player[y][i] == 0:
                            if self.board[y][i] in range(3, 7):
                                self.player[y][i] = self.board[y][i]
                            else:
                                self.player[y][i] = rnd.randint(3, 6)
                            a.append([i, y])
            else:
                if self.player[y][x] in range(3, 7):
                    self.player[y][x] = 1
                elif self.player[y][x] == 0:
                    if self.board[y][x] in range(3, 7):
                        self.player[y][x] = self.board[y][x]
                    else:
                        self.player[y][x] = rnd.randint(3, 6)
                elif self.player[y][x] == 1:
                    self.player[y][x] = 0
                    for i in all_sprites:
                        if i.rect.collidepoint(self.left + x * self.cell_size + 1, self.top + y * self.cell_size + 1):
                            i.kill()
            if a:
                self.steps.append(a)
        elif cell_coords == 'cancel':
            self.cancel()

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
    def __init__(self, tile_images, tile_type, pos_x, pos_y, s):
        super().__init__(all_sprites)
        self.image = tile_images[tile_type]
        self.image = pygame.transform.scale(self.image, (s, s))
        self.rect = self.image.get_rect().move(pos_x, pos_y)

class Errors(Sprite):
    def __init__(self, tile_images, tile_type, pos_x, pos_y, s):
        super().__init__(error_sprites)
        self.image = tile_images[tile_type]
        self.image = pygame.transform.scale(self.image, (s, s))
        self.rect = self.image.get_rect().move(pos_x, pos_y)


def error(check, h, w, cell_size, top, left):
    tile_image = {'house': load_image('cross.png'), 'people': load_image('circle.png')}
    global error_sprites
    error_sprites = pygame.sprite.Group()
    if check is True:
        end_level()
        return
    elif check[0] == 'houses':
        text = "Домики не могут касаться друг друга!"
        x1 = check[1][0] * cell_size + left + 2
        y1 = check[1][1] * cell_size + top + 2
        x2 = check[2][0] * cell_size + left + 2
        y2 = check[2][1] * cell_size + top + 2
        Errors(tile_image, 'house', x1, y1, cell_size - 2)
        Errors(tile_image, 'house', x2, y2, cell_size - 2)
    elif check[0] == 'house':
        text = "Рядом с домиком нет человечка!"
        x1 = check[1][0] * cell_size + left + 2
        y1 = check[1][1] * cell_size + top + 2
        Errors(tile_image, 'house', x1, y1, cell_size - 2)
    else:
        text = "Рядом с человечком нет домика!"
        x1 = check[1][0] * cell_size + left + 2
        y1 = check[1][1] * cell_size + top + 2
        Errors(tile_image, 'people', x1, y1, cell_size - 2)
    font = pygame.font.Font(None, 50)
    text = font.render(text, True, background)
    text_w = text.get_width()
    text_h = text.get_height()
    text_x = (width - text_w) // 2
    text_y = h * cell_size + top + (width - h * cell_size - top - text_h) // 2
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
                    return
        pygame.display.flip()
        error_sprites.draw(screen)
        clock.tick(50)


def end_level():
    fon = pygame.transform.smoothscale(screen, (70, 70))
    fon = pygame.transform.scale(fon, size)
    font = pygame.font.Font(None, 100)
    text = font.render("Уровень завершен!", True, text_color)
    text_w = text.get_width()
    text_h = text.get_height()
    text_x = (width - text_w) // 2 + 20
    text_y = (height - text_h) // 2 + 20
    r_r = ((text_x - 50, text_y - 50), (text_w + 100, text_h + 100))
    screen.blit(fon, (0, 0))
    pygame.draw.rect(screen, background, r_r, border_radius=20)
    pygame.draw.rect(screen, text_color, r_r, 10, border_radius=20)
    screen.blit(text, (text_x, text_y))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.flip()
        clock.tick(50)


def main():
    screen.fill(background)
    board = Board(cell_count, cell_count)
    board.set_view(200, 200, (width - 400) // cell_count)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                board.get_click(event.pos)
                board.render()
                all_sprites.draw(screen)
        screen.fill(background)
        board.render()
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(50)
    pygame.quit()
    con.close()
    sys.exit()

if __name__ == '__main__':
    main()