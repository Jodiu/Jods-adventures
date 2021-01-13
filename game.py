import pygame
import os
from random import randint

WIDTH = 1280
HEIGHT = 720
SIZE = WIDTH, HEIGHT
FPS = 60
LEVEL_LIST = ['level1.txt', 'level2.txt', 'level3.txt', 'level4.txt', 'level5.txt', 'level6.txt']
CURRENT_LEVEL = 'level1.txt'


def sound_load(name):
    full_name = os.path.join('data', 'sounds', name)
    if not os.path.isfile(full_name):
        print('Файл со звуком {0} не найден'.format(full_name))
    sound = pygame.mixer.Sound(full_name)
    return sound


def image_load(name, color_key=None):
    full_name = os.path.join('data', 'sprites', name)
    if not os.path.isfile(full_name):
        print('Файл с изображением {0} не найден'.format(full_name))
    image = pygame.image.load(full_name)
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        else:
            image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def level_load(name):
    full_name = os.path.join('data', 'levels', name)
    with open(full_name, mode='r') as file:
        level = file.read()
        level = level.split('\n')
    return level


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, all_sprites, image, columns, rows):
        super().__init__(all_sprites)
        self.frames = list()
        self.frame_list = list()
        self.frame_list = self.frames
        self.cut_sheet(image, columns, rows)
        self.cur_frame = 0
        self.image = self.frame_list[self.cur_frame]
        self.mask = pygame.mask.from_surface(self.image)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frame_list)
        self.image = self.frame_list[self.cur_frame]


class Entity(AnimatedSprite):
    # Инициализация: группа спрайтов, картинка, кол-во по горизонтали, кол-во по вертикали,
    # позиция x, позиция y, кол-во фреймов: смотрит влево, смотрит вправо, движ. влево, движ. вправо,
    # прыгучих влево, прыгучих вправо
    def __init__(self, all_sprites, image, columns, rows, pos_x, pos_y, facing_left_count,
                 facing_right_count, moving_left_count, moving_right_count, jumpframes_left_count=0,
                 jumpframes_right_count=0):
        super().__init__(all_sprites, image, columns, rows)
        self.dy = 0
        self.dx = 0
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos = (self.pos_x, self.pos_y)
        self.x_speed = 5

        # Списки фреймов
        self.facing_left_frames = self.frames[:facing_left_count]
        if facing_right_count != 0:
            self.facing_right_frames = self.frames[facing_left_count:facing_left_count + facing_right_count]
        if moving_left_count != 0:
            self.move_left_frames = self.frames[facing_left_count + facing_right_count:
                                                facing_left_count + facing_right_count + moving_left_count]
        if moving_right_count != 0:
            self.move_right_frames = self.frames[facing_left_count + facing_right_count + moving_left_count:
                                                 facing_left_count + facing_right_count + moving_left_count +
                                                 moving_right_count]
        if jumpframes_left_count != 0:
            self.jump_frames_left = self.frames[facing_left_count + facing_right_count +
                                                moving_left_count + moving_right_count:
                                                jumpframes_left_count + facing_left_count +
                                                facing_right_count + moving_left_count + moving_right_count]
        if jumpframes_right_count != 0:
            self.jump_frames_right = self.frames[jumpframes_left_count + facing_left_count +
                                                 facing_right_count + moving_left_count + moving_right_count:
                                                 jumpframes_left_count + jumpframes_right_count + facing_left_count +
                                                 facing_right_count + moving_left_count + moving_right_count]
        # Списки фреймов

        self.frame_list = self.facing_right_frames  # Активные фреймы
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.mask.get_rect()
        self.rect.topleft = self.pos  # Начальное положение


class Block(pygame.sprite.Sprite):
    def __init__(self, all_sprites, image, pos_x, pos_y, is_fake=False):
        if not is_fake:
            super().__init__(all_sprites)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.is_fake = is_fake
        if not is_fake:
            self.image = image
            self.mask = pygame.mask.from_surface(self.image)
            self.rect = self.mask.get_rect()
        else:
            self.rect = pygame.Rect(pos_x, pos_y, 64, 64)
        self.rect.topleft = (pos_x, pos_y)


class Spike(Block):
    def __init__(self, all_sprites, image, pos_x, pos_y):
        super().__init__(all_sprites, image, pos_x, pos_y)
        self.pos_x = pos_x
        self.pos_y = pos_y + 10
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.pos_x, self.pos_y)
        self.mask = pygame.mask.from_surface(self.image)


class Player(Entity):
    def __init__(self, all_sprites, image, columns, rows, pos_x, pos_y, facing_left_count,
                 facing_right_count, moving_left_count, moving_right_count, jumpframes_left_count=0,
                 jumpframes_right_count=0):
        super().__init__(all_sprites, image, columns, rows, pos_x, pos_y, facing_left_count,
                         facing_right_count, moving_left_count, moving_right_count, jumpframes_left_count,
                         jumpframes_right_count)
        self.jump_sound = sound_load('jump.wav')
        self.death_music = sound_load('music\\death.wav')
        self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
        self.faces = 'right'
        self.air_time = 0
        self.animation_loop = True
        self.is_dead = False

    def move(self, direction, blocks):
        if not self.is_dead:
            self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
            if 'left' in direction:
                self.dx = -1
                self.faces = 'left'
            if 'right' in direction:
                self.dx = 1
                self.faces = 'right'
            if ('left' in direction and 'right' in direction) or \
                    ('left' not in direction and 'right' not in direction):
                self.dx = 0
            self.rect.x += self.dx * self.x_speed
            collision_list = collide_detect(self, blocks)
            for block in collision_list:
                if not block.is_fake:
                    if self.dx > 0:
                        self.rect.right = block.rect.left
                        self.collision_sides['right'] = True
                    elif self.dx < 0:
                        self.rect.left = block.rect.right
                        self.collision_sides['left'] = True
            self.rect.y -= 10 * self.dy / 100  # Падение
            if self.dy >= -70:  # Если меньше - перестает ускоряться
                self.dy -= 5  # Ускорение падения
            collision_list = collide_detect(self, blocks)
            self.air_time += 1
            for block in collision_list:
                if not block.is_fake:
                    if self.dy < 0:
                        self.rect.bottom = block.rect.top
                        self.collision_sides['bottom'] = True
                        self.dy = 0
                        self.air_time = 0
                        self.animation_loop = True
                    elif self.dy > 0:
                        self.rect.top = block.rect.bottom
                        self.collision_sides['top'] = True
                        self.dy = 0
            if self.air_time == 3:
                self.cur_frame = 0
        else:
            self.rect.y -= 10 * self.dy / 100  # Падение
            self.dy -= 5  # Ускорение падения
            self.rect.x += self.dx * self.x_speed
            self.air_time += 2
            # Прыжок от стены (странный)
            # if (self.collision_sides['right'] or self.collision_sides['left']) and not self.collision_sides['bottom']:
            #     self.air_time = 0

    def jump(self):
        self.animation_loop = False
        self.cur_frame = 0
        if self.air_time < 5:
            self.dy = 120
            self.jump_sound.play()

    def update(self):
        if not self.is_dead:
            if self.animation_loop:
                self.cur_frame = (self.cur_frame + 1) % len(self.frame_list)
                self.image = self.frame_list[self.cur_frame]
            else:
                if self.cur_frame < len(self.frame_list) - 1:
                    self.image = self.frame_list[self.cur_frame]
                    self.cur_frame += 1
                else:
                    self.image = self.frame_list[self.cur_frame]

    def sprite_change(self):
        if self.air_time < 3:
            if self.faces == 'right':
                if self.dx > 0:
                    self.frame_list = self.move_right_frames
                else:
                    self.frame_list = self.facing_right_frames
            if self.faces == 'left':
                if self.dx < 0:
                    self.frame_list = self.move_left_frames
                else:
                    self.frame_list = self.facing_left_frames
        else:
            self.animation_loop = False
            if self.faces == 'right':
                self.frame_list = self.jump_frames_right
            elif self.faces == 'left':
                self.frame_list = self.jump_frames_left

    def die(self):
        self.is_dead = True
        pygame.mixer.stop()
        self.death_music.play(-1)
        self.dy = 140
        self.dx = self.dx / 2
        self.air_time = 5


class Enemy(Entity):
    def __init__(self, all_sprites, image, columns, rows, pos_x, pos_y, facing_left_count,
                 facing_right_count, moving_left_count, moving_right_count, jumpframes_left_count=0,
                 jumpframes_right_count=0):
        super().__init__(all_sprites, image, columns, rows, pos_x, pos_y, facing_left_count,
                         facing_right_count, moving_left_count, moving_right_count, jumpframes_left_count,
                         jumpframes_right_count)
        self.dy = 0
        self.dx = randint(-1, 1)
        self.frame_list = self.facing_right_frames
        self.direction = list()
        self.direction.append('left')
        self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
        self.air_time = 0
        self.x_speed = 3

    def move(self, blocks):
        self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
        if 'left' in self.direction:
            self.dx = -1
        if 'right' in self.direction:
            self.dx = 1
        self.rect.x += self.dx * self.x_speed
        collision_list = collide_detect(self, blocks)
        for block in collision_list:
            if self.dx > 0:
                self.rect.right = block.rect.left
                self.collision_sides['right'] = True
                self.direction.append('left')
                self.direction.pop(self.direction.index('right'))
            elif self.dx < 0:
                self.rect.left = block.rect.right
                self.collision_sides['left'] = True
                self.direction.append('right')
                self.direction.pop(self.direction.index('left'))
        self.rect.y -= 10 * self.dy / 100  # Падение
        if self.dy >= -70:  # Если меньше - перестает ускоряться
            self.dy -= 5  # Ускорение падения
        collision_list = collide_detect(self, blocks)
        self.air_time += 1
        for block in collision_list:
            if self.dy < 0:
                self.rect.bottom = block.rect.top
                self.collision_sides['bottom'] = True
                self.dy = 0
                self.air_time = 0

    def sprite_change(self):
        if self.air_time < 3:
            if 'right' in self.direction:
                if self.dx > 0:
                    self.frame_list = self.move_right_frames
                else:
                    self.frame_list = self.facing_right_frames
            if 'left' in self.direction:
                if self.dx < 0:
                    self.frame_list = self.move_left_frames
                else:
                    self.frame_list = self.facing_left_frames


def collide_detect(character, things):
    collide_list = list()
    for thing in things:
        if not type(thing) == Spike and not type(thing) == Enemy:
            if character.rect.colliderect(thing.rect):
                collide_list.append(thing)
        elif (type(thing) == Spike or type(thing) == Enemy) and type(character) == Player:
            if pygame.sprite.collide_mask(character, thing):
                character.die()
    return collide_list


def level_change(all_sprites, name, jod, things, blocks, enemies):
    global CURRENT_LEVEL
    jod_pos = None
    all_sprites.empty()
    things.clear()
    blocks.clear()
    enemies.clear()
    if LEVEL_LIST.index(name) > LEVEL_LIST.index(CURRENT_LEVEL):
        jod.rect.y = HEIGHT
    elif LEVEL_LIST.index(name) > LEVEL_LIST.index(CURRENT_LEVEL):
        jod.rect.y = 0
    level = level_load(name)
    CURRENT_LEVEL = name
    row_count = 0
    for row in level:
        row_count += 1
        symbol_count = 0
        for symbol in row:
            symbol_count += 1
            if symbol != '#':
                if symbol == 'J':
                    jod_pos = ((32 * symbol_count), (32 * row_count - 32))
                if symbol == 'b':
                    blocks.append(Block(all_sprites, image_load('blocks\\block1.png'), (32 * symbol_count),
                                        (32 * row_count)))
                if symbol == 'i':
                    blocks.append(Block(all_sprites, image_load('blocks\\block_.png'), (32 * symbol_count),
                                        (32 * row_count), is_fake=True))
                if symbol == 's':
                    blocks.append(Spike(all_sprites, image_load('blocks\\spike1.png'), (32 * symbol_count),
                                        (32 * row_count)))
                if symbol == 'e':
                    enemies.append(Enemy(all_sprites, image_load('characters\\test_enemy1.png'),
                                         2, 4, (32 * symbol_count), (32 * row_count), 2, 2, 2, 2, 0, 0))
    for block in blocks:
        things.append(block)
    for enemy in enemies:
        things.append(enemy)
    if jod_pos is not None:
        return enemies, blocks, things, jod_pos
    else:
        return enemies, blocks, things


class DeathScreen(pygame.sprite.Sprite):
    def __init__(self, all_sprites):
        super().__init__(all_sprites)
        self.image = image_load('menu\\death.png')
        self.rect = self.image.get_rect()
        self.rect.topleft = (0, 0)


def main():
    direction = list()
    pygame.init()
    pygame.mixer.init()
    all_sprites = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    music = sound_load('music\\menu.wav')
    music.set_volume(0.3)
    music.play(-1)
    pygame.display.set_caption('игра')
    canvas = pygame.display.set_mode(SIZE)
    jod = Player(player_group, image_load('characters\\Jods.png'),
                 22, 1, -50, 0, 4, 4, 4, 4, 3, 3)  # Создание игрока
    enemies, blocks, things, jod_pos = level_change(all_sprites, 'level1.txt', jod, blocks=list(),
                                                    enemies=list(), things=list())
    jod.rect.topleft = jod_pos

    clock = pygame.time.Clock()
    counter = 0  # Счетчик для анимации спрайтов
    running = True
    while running:
        counter += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Нажатия на кнопки
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    jod.jump()
                if event.key == pygame.K_RIGHT:
                    direction.append('right')
                if event.key == pygame.K_LEFT:
                    direction.append('left')
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT:
                    direction.pop(direction.index('right'))
                if event.key == pygame.K_LEFT:
                    direction.pop(direction.index('left'))
            # Нажатия на кнопки
        jod.sprite_change()  # Изменение активных фреймов
        for enemy in enemies:
            enemy.sprite_change()
        if counter % 8 == 0:  # Скорость анимации спрайтов
            jod.update()  # Анимация
            for enemy in enemies:
                enemy.update()
            counter = 0
        jod.move(direction, things)  # Движение
        for enemy in enemies:
            enemy.move(blocks)

        if jod.rect.y >= HEIGHT:
            if not CURRENT_LEVEL == 'level1.txt':
                level_change(all_sprites, LEVEL_LIST[LEVEL_LIST.index(CURRENT_LEVEL) - 1], jod, things, blocks, enemies)
                jod.rect.y = 0
            else:
                DeathScreen(all_sprites)
        elif jod.rect.y <= 0:
            if not CURRENT_LEVEL == 'level6.txt':
                level_change(all_sprites, LEVEL_LIST[LEVEL_LIST.index(CURRENT_LEVEL) + 1], jod, things, blocks, enemies)
                jod.rect.y = HEIGHT
        canvas.fill((70, 70, 170))
        player_group.draw(canvas)
        all_sprites.draw(canvas)  # Отрисовка всех спрайтов
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
