#!/usr/bin/python3

import pygame
from pygame.locals import *
import random
from math import ceil

from tetrominos import *

class GameState:
    READY, RUNNING, ANIMATING, PAUSED, LOST = range(5)


POINTS_FOR_LINES = (40, 100, 300, 1200)
CELL_SIZE = 25
WIDTH = 14
HEIGHT = 20
SIDEBAR_WIDTH = 6

EMPTY_CELL_COLOR = (20, 20, 20)
SEPARATOR_CELL_COLOR = (80, 80, 80)
TEXT_COLOR = (200, 200, 200)
FINAL_POSITION_COLOR = (40, 40, 40)

SHAPES = (TetrominoT, TetrominoI, TetrominoL, TetrominoJ, TetrominoS, TetrominoZ, TetrominoO)

FPS = 60

KEY_FIRST_REPEAT_DELAY = 250
KEY_REPEAT_INTERVAL = 20

HARD_DROP_ANIMATION_TIME = 200
MOVE_ANIMATION_TIME = 20

DROP_EVENT = pygame.USEREVENT

class Animation:
    __slots__ = ['obj', 'attr', 'start', 'end', 'interval', 'callback']
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Tetrys')

        self.display = pygame.display.set_mode(((WIDTH + 1 + SIDEBAR_WIDTH) * CELL_SIZE, HEIGHT * CELL_SIZE),
                                               pygame.HWSURFACE | pygame.DOUBLEBUF)

        self.small_font = pygame.font.SysFont('droidsansmono', 15)
        self.large_font = pygame.font.SysFont('droidsansmono', 45)

        self.clock = pygame.time.Clock()
        self.delta = 0

        pygame.key.set_repeat(KEY_FIRST_REPEAT_DELAY, KEY_REPEAT_INTERVAL)

        self.shadow = pygame.Surface((WIDTH * CELL_SIZE, HEIGHT * CELL_SIZE), SRCALPHA)
        self.shadow.fill((0, 0, 0, 150))

        self.cell_images = { 'TetrominoL': pygame.image.load('L.png').convert_alpha(),
                             'TetrominoJ': pygame.image.load('J.png').convert_alpha(),
                             'TetrominoS': pygame.image.load('S.png').convert_alpha(),
                             'TetrominoZ': pygame.image.load('Z.png').convert_alpha(),
                             'TetrominoT': pygame.image.load('T.png').convert_alpha(),
                             'TetrominoO': pygame.image.load('O.png').convert_alpha(),
                             'TetrominoI': pygame.image.load('I.png').convert_alpha() }
        self.running = True
        self.space_pressed = False
        self.show_final = True
        self.animations = []

        self.start()

    def start(self):
        self.state = GameState.READY

        self.locked = [[None] * HEIGHT for _ in range(WIDTH)]

        self.level = 1
        self.lines = 0
        self.score = 0

        shape = random.choice(SHAPES)
        self.next = shape()
        self.pick_next()

        self.reset_drop_timer()
 
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == KEYDOWN:
            if self.state == GameState.READY:
                self.state = GameState.RUNNING
            elif self.state == GameState.PAUSED:
                self.toggle_pause()
            elif self.state == GameState.LOST:
                if event.key == K_r:
                    self.start()
                    self.state = GameState.RUNNING
                elif event.key == K_q:
                    self.running = False
            elif event.key == K_RIGHT:
                self.right()
            elif event.key == K_LEFT:
                self.left()
            elif event.key == K_UP:
                self.rotate()
            elif event.key == K_DOWN:
                self.drop()
            # We don't want to repeat hard drops
            elif event.key == K_SPACE and not self.space_pressed:
                self.space_pressed = True
                self.hard_drop()
            elif event.key == K_q:
                self.running = False
            elif event.key == K_p:
                self.toggle_pause()
            elif event.key == K_g:
                self.add_garbage()
            elif event.key == K_f:
                self.show_final = not self.show_final
        elif event.type == KEYUP:
            if event.key == K_SPACE:
                self.space_pressed = False
        elif event.type == DROP_EVENT:
            self.drop()

    def reset_drop_timer(self):
        pygame.time.set_timer(DROP_EVENT, (11 - self.level) * 50)

    def pick_next(self):
        self.current = self.next
        shape = random.choice(SHAPES)
        self.next = shape()
        self.current.x = (WIDTH - self.current.get_width()) // 2
        if not self.can_place():
            self.state = GameState.LOST
        self.reset_drop_timer()

    def move(self, dx, dy):
        self.current.move(dx, dy)
        if not self.can_place():
            self.current.move(-dx, -dy)
            return False
        return True

    def can_place(self):
        for x, y in self.current:
            x = ceil(x)
            y = ceil(y)
            if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT or self.locked[x][y]:
                return False
        return True

    def update_final_y(self):
        dy = 0
        while self.can_place():
            self.current.move(0, 1)
            dy += 1
        self.final_y = ceil(self.current.y - 1)
        self.current.move(0, -dy)

    def animate(self, obj, attr, start, end, interval, callback=None):
        #self.state = GameState.ANIMATING
        animation = Animation(obj=obj, attr=attr, start=start, end=end,
                              interval=interval, callback=callback)
        self.animations.append(animation)

    def can_move(self, dx, dy):
        self.current.move(dx, dy)
        if self.can_place():
            self.current.move(-dx, -dy)
            return True
        else:
            self.current.move(-dx, -dy)
            return False

    def left(self):
        if self.state != GameState.RUNNING:
            return
        if self.can_move(-1, 0):
            self.animate(self.current, 'x', self.current.x, self.current.x - 1, MOVE_ANIMATION_TIME)

    def right(self):
        if self.state != GameState.RUNNING:
            return
        if self.can_move(1, 0):
            self.animate(self.current, 'x', self.current.x, self.current.x + 1, MOVE_ANIMATION_TIME)

    def rotate(self):
        if self.state != GameState.RUNNING:
            return
        self.current.rotate()
        if self.can_place():
            return
        # Try a wall kick to the left...
        self.current.move(-1, 0)
        if self.can_place():
            return
        # ...then a wall kick to the right...
        self.current.move(2, 0)
        if self.can_place():
            return
        # ...didn't work out
        self.current.rotate(-1)
        self.current.move(-1, 0)

    def drop(self):
        if self.state != GameState.RUNNING:
            return
        if self.can_move(0, 1):
            self.animate(self.current, 'y', self.current.y, self.current.y + 1,
                         MOVE_ANIMATION_TIME)
        else:
            self.on_drop_finished()

    def hard_drop(self):
        if self.state != GameState.RUNNING:
            return
        self.animate(self.current, 'y', self.current.y, self.final_y,
                     HARD_DROP_ANIMATION_TIME, self.on_drop_finished)

    def on_drop_finished(self):
        self.lock()
        self.pick_next()
        self.handle_complete_lines()

    def update_animations(self):
        #now = pygame.time.get_ticks()
        #delta = now - self.last_time
        #self.last_time = now

        next_animations = []
        for a in self.animations:
            #obj, attr, start, end, interval, callback = animation
            current = getattr(a.obj, a.attr) + (a.end - a.start) * self.delta / a.interval
            if current >= a.end >= a.start or current <= a.end <= a.start:
                setattr(a.obj, a.attr, a.end)
                if a.callback:
                    (a.callback)()
            else:
                setattr(a.obj, a.attr, current)
                next_animations.append(a)

        self.animations = next_animations
        #if not self.animations:
        #    self.state = GameState.RUNNING

    def handle_complete_lines(self):
        completed = 0
        for y in range(HEIGHT):
            if all(self.locked[x][y] for x in range(WIDTH)):
                completed += 1
                for x in range(WIDTH):
                    del self.locked[x][y]
                    self.locked[x].insert(0, None)

        self.lines += completed
        if completed > 0:
            self.score += (self.level + 1) * POINTS_FOR_LINES[completed - 1]
        self.level = min(10, 1 + self.lines // 10)

    def lock(self):
        for x, y in self.current:
            self.locked[ceil(x)][ceil(y)] = self.current.__class__.__name__
        self.current = None

    def add_garbage(self):
        if self.state != GameState.RUNNING:
            return

        for x in range(WIDTH):
            del self.locked[x][0]
            filler = random.choice([None, random.choice(list(self.cell_images))])
            self.locked[x].append(filler)

        self.score += 100

    def toggle_pause(self):
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.RUNNING

    def on_loop(self):
        #delta = self.clock.tick(FPS)
        self.update_final_y()
        self.update_animations()

    def on_render(self):
        self.delta = self.clock.tick(FPS)

        self.display.fill((0, 0, 0))

        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.locked[x][y]:
                    self.draw_tetromino_cell((x, y), self.locked[x][y])
                else:
                    self.draw_cell((x, y), EMPTY_CELL_COLOR)

        if self.show_final:
            for x, y in self.current:
                self.draw_cell((x, int(y - self.current.y + self.final_y)), FINAL_POSITION_COLOR)

        for cell in self.current:
            self.draw_tetromino_cell(cell, self.current.__class__.__name__)

        for cell in self.next:
            self.draw_tetromino_cell(cell, self.next.__class__.__name__,
                                     WIDTH + 1 + (SIDEBAR_WIDTH - self.next.get_width()) / 2,
                                     (5 - self.next.get_height()) / 2)

        for y in range(HEIGHT):
            self.draw_cell((WIDTH, y), SEPARATOR_CELL_COLOR)

        for y in (5, 10, 15):
            for x in range(SIDEBAR_WIDTH):
                self.draw_cell((x + WIDTH + 1, y), SEPARATOR_CELL_COLOR)

        center_x = (WIDTH + 1 + SIDEBAR_WIDTH / 2) * CELL_SIZE
        self.display_text(self.small_font, 'LEVEL',
                          center_x, 7 * CELL_SIZE)
        self.display_text(self.large_font, str(self.level),
                          center_x, 7 * CELL_SIZE + 40)
        self.display_text(self.small_font, 'LINES',
                          center_x, 12 * CELL_SIZE)
        self.display_text(self.large_font, str(self.lines),
                          center_x, 12 * CELL_SIZE + 40)
        self.display_text(self.small_font, 'SCORE',
                          center_x, 17 * CELL_SIZE)
        self.display_text(self.large_font, str(self.score),
                          center_x, 17 * CELL_SIZE + 40)

        center_x = WIDTH * CELL_SIZE / 2
        center_y = HEIGHT * CELL_SIZE / 2
        if self.state == GameState.READY:
            self.display.blit(self.shadow, (0, 0))
            self.display_text(self.small_font, 'PRESS ANY KEY', center_x, center_y - 25)
            self.display_text(self.small_font, 'TO START', center_x, center_y + 25)
        if self.state == GameState.LOST:
            self.display.blit(self.shadow, (0, 0))
            self.display_text(self.large_font, 'GAME OVER', center_x, center_y - 25)
            self.display_text(self.small_font, 'PRESS "R" TO RESTART', center_x, center_y + 25)
        if self.state == GameState.PAUSED:
            self.display.blit(self.shadow, (0, 0))
            self.display_text(self.large_font, 'PAUSED', center_x, center_y - 25)
            self.display_text(self.small_font, 'ANY KEY TO CONTINUE', center_x, center_y + 25)

        pygame.display.flip()

    def display_text(self, font, text, x, y):
        text_surface = font.render(text, True, TEXT_COLOR)
        rect = text_surface.get_rect()
        rect.left = x - rect.width / 2
        rect.top = y - rect.height / 2
        self.display.blit(text_surface, rect)

    def draw_cell(self, cell, color, x_offset=0, y_offset=0):
        x, y = cell
        x, y = x + x_offset, y + y_offset
        r = pygame.Rect(CELL_SIZE * x + 1, CELL_SIZE * y + 1, CELL_SIZE - 1, CELL_SIZE - 1)
        pygame.draw.rect(self.display, color, r)

    def draw_tetromino_cell(self, cell, color, x_offset=0, y_offset=0):
        x, y = cell
        x, y = x + x_offset, y + y_offset
        self.display.blit(self.cell_images[color], (x * CELL_SIZE + 1, y * CELL_SIZE + 1))

    def mainloop(self):
        while self.running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        pygame.quit()
 
if __name__ == "__main__":
    game = Game()
    game.mainloop()

