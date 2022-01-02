import pygame
import os
import sys
import sqlite3
import level
from particles import initilize_snow, snowfall
import time


pygame.init()
size = width, height = 1000, 1000
background = pygame.Color('#d3ad8d')
text_color = pygame.Color('#8c4d2c')
button_color = pygame.Color('#2C7E8C')
all_sprites = pygame.sprite.Group()
setting_sprites = pygame.sprite.Group()
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
images = {'setting': level.load_image('setting.png'), 'left': level.load_image('left.png'),
          'right': level.load_image('right.png'), 'sound': level.load_image('sound.png'),
          'snow': level.load_image('snow.png')}

con = sqlite3.connect(os.path.join('data', 'database', "levels"))
cur = con.cursor()

levels = cur.execute("""SELECT id FROM level;""").fetchall()
sound = True if cur.execute("""SELECT value FROM setting WHERE name = 'sound';""").fetchone()[0] == 'True' else False
snow = True if cur.execute("""SELECT value FROM setting WHERE name = 'snow';""").fetchone()[0] == 'True' else False

music = list({'Last Christmas.mp3', 'Happy New Year.mp3', "It Doesn't Have to Be That Way.mp3", "Jingle Bells.mp3",
                 "Let It Snow.mp3", "Thanks god its christmas.mp3", "We wish you a merry Christmas.mp3"})
pygame.mixer.music.load(os.path.join('data', 'music', music[0]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[1]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[2]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[3]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[4]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[5]))
pygame.mixer.music.queue(os.path.join('data', 'music', music[6]))
sound_button = pygame.mixer.Sound(os.path.join('data', 'music', 'button sound.mp3'))
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


class MainWindow:
    def __init__(self):
        self.id = -1
        self.surface = None
        self.prev_id = -1
        self.button = None
        self.draw_arrows()

    def render(self):
        if not any(map(lambda i: i.rect.collidepoint(22, 22), all_sprites)):
            Objects(all_sprites, images, 'setting', 22, 22, 64)
        if self.id == -1:
            font = pygame.font.Font(None, 50)
            text = font.render("Создать уровень", True, background)
            text_w = text.get_width()
            text_h = text.get_height()
            text_x = (width - text_w) // 2
            text_y = (height - text_h) // 2
            r_r = ((text_x - 40, text_y - 40), (text_w + 80, text_h + 80))
            pygame.draw.rect(screen, button_color, r_r, border_radius=20)
            screen.blit(text, (text_x, text_y))
        else:
            n = cur.execute(f"""SELECT width FROM level WHERE id = '{self.id}'""").fetchone()
            if self.prev_id != self.id or self.button:
                level.main(int(n[0]), self.id, 240, 240, True, True)
            screen.fill(background)
            run_snow()
            self.surface = level.screen
            screen.blit(self.surface, (240, 240))
            pygame.draw.rect(screen, text_color, ((240, 240), (520, 520)), 10)
            font = pygame.font.Font(None, 50)
            text = font.render(f"Уровень {n[0]} x {n[0]}", True, text_color)
            text_w = text.get_width()
            text_x = 240 + (520 - text_w) // 2
            text_y = 785
            screen.blit(text, (text_x, text_y))
        pygame.draw.rect(screen, button_color, ((20, 20), (70, 70)), border_radius=20)
        self.prev_id = self.id
        self.button = None

    def draw_arrows(self):
        if levels and self.id < len(levels) - 1 and not any(map(lambda i: i.rect.collidepoint(887, 468), all_sprites)):
            Objects(all_sprites, images, 'right', 887, 468, 64)
        elif not levels or self.id >= len(levels) - 1:
            for i in all_sprites:
                if i.rect.collidepoint(887, 468):
                    i.kill()
                    break
        if levels and 0 <= self.id < len(levels) and not any(map(lambda i: i.rect.collidepoint(49, 468), all_sprites)):
            Objects(all_sprites, images, 'left', 49, 468, 64)
        elif not levels or self.id < 0 or self.id >= len(levels):
            for i in all_sprites:
                if i.rect.collidepoint(49, 468):
                    i.kill()
                    break

    def get_click(self, mouse_pos):
        button = self.get_button(mouse_pos)
        self.on_click(button)

    def get_button(self, mouse_pos):
        if 20 <= mouse_pos[0] <= 90 and 20 <= mouse_pos[1] <= 90:
            return 'setting'
        if 313 <= mouse_pos[0] <= 687 and 442 <= mouse_pos[1] <= 557 and self.id == -1:
            return 'build'
        if 49 <= mouse_pos[0] <= 113 and 468 <= mouse_pos[1] <= 532 and 0 <= self.id < len(levels):
            return 'left'
        if 887 <= mouse_pos[0] <= 951 and 468 <= mouse_pos[1] <= 532 and self.id < len(levels) - 1:
            return 'right'
        if 240 <= mouse_pos[0] <= 760 and 240 <= mouse_pos[1] <= 760 and self.id > -1:
            return 'load'
        else:
            return None

    def on_click(self, button):
        if button:
            global snow, sound
            if sound:
                sound_button.play()
            if button == 'build':
                build_level()
                snow = True if cur.execute("""SELECT value FROM setting WHERE name = 'snow'""").fetchone()[
                                   0] == 'True' else False
                sound = True if cur.execute("""SELECT value FROM setting WHERE name = 'sound'""").fetchone()[
                                    0] == 'True' else False
            elif button == 'right':
                self.id += 1
                self.draw_arrows()
            elif button == 'left':
                self.id -= 1
                self.draw_arrows()
            elif button == 'load':
                load_level(self.id)
                self.button = True
                snow = True if cur.execute("""SELECT value FROM setting WHERE name = 'snow'""").fetchone()[
                                   0] == 'True' else False
                sound = True if cur.execute("""SELECT value FROM setting WHERE name = 'sound'""").fetchone()[
                                    0] == 'True' else False
            elif button == 'setting':
                setting(self)
            global levels
            levels = cur.execute("""SELECT id FROM level""").fetchall()
            self.draw_arrows()


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


def build_level():
    h0 = (height - 35 * 7 - 300) // 2
    w0 = (width - 420) // 2
    draw_build_level()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 280 <= event.pos[0] <= 720 and 301 <= event.pos[1] < 355:
                    n = 5
                elif 280 <= event.pos[0] <= 720 and 385 <= event.pos[1] < 439:
                    n = 6
                elif 280 <= event.pos[0] <= 720 and 469 <= event.pos[1] < 523:
                    n = 7
                elif 280 <= event.pos[0] <= 720 and 553 <= event.pos[1] < 607:
                    n = 8
                elif 280 <= event.pos[0] <= 720 and 637 <= event.pos[1] < 691:
                    n = 9
                elif 280 <= event.pos[0] <= 720 and 721 <= event.pos[1] <= 776:
                    n = 10
                elif w0 + 420 <= event.pos[0] <= w0 + 475 and h0 - 50 <= event.pos[1] <= h0 + 5:
                    if sound:
                        sound_button.play()
                    return
                else:
                    n = None
                if n:
                    if sound:
                        sound_button.play()
                    level.main(n, len(levels))
                    return
        pygame.display.flip()
        clock.tick(50)


def load_level(id):
    n = cur.execute(f"""SELECT width FROM level WHERE id = '{id}'""").fetchone()
    level.main(int(n[0]), id, load=True)


def setting(window):
    global sound
    h0 = (height - 35 * 4 - 200) // 2
    w0 = (width - 420) // 2
    draw_setting(window)
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
                elif 280 <= event.pos[0] <= 720 and 575 <= event.pos[1] <= 615:
                    if sound:
                        sound_button.play()
                    global levels
                    cur.execute('DELETE FROM level;',)
                    con.commit()
                    return
                elif 665 <= event.pos[0] <= 720 and 405 <= event.pos[1] <= 455:
                    if sound:
                        sound_button.play()
                        pygame.draw.line(screen, pygame.Color('black'), (669, 459), (714, 405), 10)
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
                        draw_setting(window)
                    cur.execute(f"UPDATE setting SET value = '{sound}' WHERE name = 'sound';")
                    con.commit()
                elif 665 <= event.pos[0] <= 720 and 490 <= event.pos[1] <= 545:
                    if sound:
                        sound_button.play()
                    global snow
                    if snow:
                        pygame.draw.line(screen, pygame.Color('black'), (669, 544), (714, 490), 10)
                        snow = False
                    else:
                        screen.fill(background)
                        snow = True
                        draw_setting(window)
                    cur.execute(f"UPDATE setting SET value = '{snow}' WHERE name = 'snow';")
                    con.commit()
        pygame.display.flip()
        clock.tick(50)


def draw_setting(window):
    window.render()
    all_sprites.draw(screen)
    run_snow()
    global setting_sprites
    setting_sprites = pygame.sprite.Group()
    fon = pygame.transform.smoothscale(screen, (100, 100))
    fon = pygame.transform.scale(fon, size)
    screen.blit(fon, (0, 0))
    buttons = ['Настройки', 'Звук', 'Снежинки', 'Удалить все уровни']
    h0 = (height - 35 * 4 - 200) // 2
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
        pygame.draw.line(screen, pygame.Color('black'), (669, 544), (714, 490), 10)
    if not sound:
        pygame.draw.line(screen, pygame.Color('black'), (669, 459), (714, 405), 10)
    setting_sprites.draw(screen)


def  draw_build_level():
    run_snow()
    fon = pygame.transform.smoothscale(screen, (100, 100))
    fon = pygame.transform.scale(fon, size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 50)
    h0 = (height - 35 * 7 - 300) // 2
    w0 = (width - 420) // 2
    for i in range(4, 11):
        if i == 4:
            text = "Выберите размеры поля"
            border = None
        else:
            text = f"{i} x {i}"
            border = True
        text = font.render(text, True, background)
        text_x = (width - text.get_width()) // 2
        text_y = h0 + 50 * (i - 4) + text.get_height() * (i - 4)
        r_r = ((w0 - 25, text_y - 25), (470, 85))
        pygame.draw.rect(screen, text_color, r_r)
        if border:
            pygame.draw.rect(screen, background, ((r_r[0][0] + 5, r_r[0][1] + 5), (r_r[1][0] - 10, r_r[1][1] - 10)), 10)
        screen.blit(text, (text_x, text_y))
    pygame.draw.rect(screen, button_color, ((w0 + 420, h0 - 50), (55, 55)))
    pygame.draw.line(screen, pygame.Color('black'), (w0 + 427, h0 - 45), (w0 + 468, h0), 10)
    pygame.draw.line(screen, pygame.Color('black'), (w0 + 468, h0 - 45), (w0 + 427, h0), 10)


def run_snow():
    if snow:
        snowfall.draw(screen)
        snowfall.update()
        time.sleep(0.04)


def main():
    global play_snow
    screen.fill(background)
    main_window = MainWindow()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                main_window.get_click(event.pos)
        screen.fill(background)
        if snow and not play_snow:
            initilize_snow()
            play_snow = True
        run_snow()
        main_window.render()
        all_sprites.draw(screen)
        clock.tick(50)
        pygame.display.flip()
    pygame.quit()
    con.close()
    sys.exit()

if __name__ == '__main__':
    main()