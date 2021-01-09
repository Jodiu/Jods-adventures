import pygame
import os

WIDTH = 1280
HEIGHT = 720
SIZE = WIDTH, HEIGHT
FPS = 60


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
    # позиция x, позиция y, кол-во фреймов: стоячих, движ. влево, движ. вправо, прыгучих
    def __init__(self, all_sprites, image, columns, rows, pos_x, pos_y, standframes_count,
                 moving_left_count, moving_right_count, jumpframes_count=0):
        super().__init__(all_sprites, image, columns, rows)
        self.dy = 0
        self.dx = 0
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos = (self.pos_x, self.pos_y)
        self.x_speed = 5

        # Списки фреймов
        self.stand_frames = self.frames[:standframes_count]
        self.move_left_frames = self.frames[standframes_count:
                                            standframes_count + moving_left_count]
        self.move_right_frames = self.frames[standframes_count + moving_left_count:
                                             standframes_count + moving_left_count + moving_right_count]
        if jumpframes_count != 0:
            self.jump_frames = self.frames[standframes_count + moving_left_count + moving_right_count:
                                           jumpframes_count + standframes_count + moving_left_count + moving_right_count]
        # Списки фреймов

        self.frame_list = self.stand_frames  # Активные фреймы
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.mask.get_rect()
        self.rect.topleft = self.pos  # Начальное положение


class Block(pygame.sprite.Sprite):
    def __init__(self, all_sprites, image, pos_x, pos_y):
        super().__init__(all_sprites)
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.image = image
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.mask.get_rect()
        self.rect.topleft = (pos_x, pos_y)


class Player(Entity):
    def __init__(self, all_sprites, image, columns, rows, pos_x, pos_y, standframes_count,
                 moving_left_count, moving_right_count, jumpframes_count):
        super().__init__(all_sprites, image, columns, rows, pos_x, pos_y, standframes_count,
                         moving_left_count, moving_right_count, jumpframes_count)
        self.jump_sound = sound_load('jump.wav')
        self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
        self.air_time = 0

    def move(self, direction, blocks):
        self.collision_sides = {'left': False, 'right': False, 'top': False, 'bottom': False}
        if 'left' in direction:
            self.dx = -1
        if 'right' in direction:
            self.dx = 1
        if ('left' in direction and 'right' in direction) or \
                ('left' not in direction and 'right' not in direction):
            self.dx = 0
        self.rect.x += self.dx * self.x_speed
        collision_list = collide_detect(self, blocks)
        for block in collision_list:
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
            if self.dy < 0:
                self.rect.bottom = block.rect.top
                self.collision_sides['bottom'] = True
                self.dy = 0
                self.air_time = 0
            elif self.dy > 0:
                self.rect.top = block.rect.bottom
                self.collision_sides['top'] = True
                self.dy = 0
                self.air_time = 0

    def jump(self):
        if self.air_time < 5:
            self.dy += 150
            self.jump_sound.play()

    def sprite_change(self):
        if self.air_time < 3:
            if self.dx == 0:
                self.frame_list = self.stand_frames
            if self.dx > 0:
                self.frame_list = self.move_right_frames
            if self.dx < 0:
                self.frame_list = self.move_left_frames
        else:
            self.frame_list = self.jump_frames


def collide_detect(character, blocks):
    collide_list = list()
    for block in blocks:
        if character.rect.colliderect(block.rect):
            collide_list.append(block)
    return collide_list


def main():
    direction = list()
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_caption('игра')
    canvas = pygame.display.set_mode(SIZE)
    all_sprites = pygame.sprite.Group()
    jod = Player(all_sprites, pygame.transform.scale(image_load('characters\\Jodiu.png'), (800, 100)),
                 8, 1, 630, 300, 2, 2, 2, 2)  # Создание игрока

    # Нужно заменить на функцию load_level
    blocks = list()
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 800, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 720, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 640, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 560, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 480, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 400, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 320, 600))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 640, 400))
    blocks.append(Block(all_sprites, image_load('blocks\\block.png'), 320, 520))
    # Нужно заменить на функцию load_level

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
        if counter % 5 == 0:  # Скорость анимации спрайтов
            jod.update()  # Анимация
            counter = 0
        jod.move(direction, blocks)  # Движение

        canvas.fill((70, 70, 170))
        all_sprites.draw(canvas)  # Отрисовка всех спрайтов
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
