#!/usr/bin/python3
import random, copy, sys
import ui

TPS = 10 # ticks per second
FALL_SPEED = 1.5 # blocks per second
SNAP_TIME = 1 # seconds

class Piece:
    def __init__(self, shape=None, x=None, y=None, colour=None):
        if shape:
            self.shape = shape
        else:
            self.shape = generate_shape()
        self.x = x
        self.y = y
        if x is None or y is None:
            self.reset_position()
        if not colour_buffer:
            for i in range(1, 7):
                colour_buffer.append(i)
            random.shuffle(colour_buffer)
        self.colour = colour_buffer.pop() if colour is None else colour
        self.buffer = ""
    def get_shadow(self): # create shadow/ghost piece
        shadow = Piece(self.shape, self.x, self.y, ui.COLOUR_BRIGHT_BLACK)
        while not shadow.on_floor():
            shadow.y += 1
        return shadow
    def draw(self, colour=None, shadow=True):
        if shadow:
            self.get_shadow().draw(colour=colour, shadow=False)
        if colour is None:
            colour = self.colour
        for y, row in enumerate(self.shape):
            if 1 not in row:
                continue
            x = row.index(1)
            count = sum(row[x:])
            tx = self.x + x + 1
            ty = self.y + y + 6
            for dx in range(count):
                main_ui.set_pixel(colour, tx+dx, ty)
    def intersect(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    if not 0 <= y < len(board):
                        return True
                    if not 0 <= x < len(board[y]):
                        return True
                    if board[y][x] != ui.COLOUR_DEFAULT:
                        return True
        return False
    def on_floor(self):
        self.y += 1
        x = self.intersect()
        self.y -= 1
        return x
    def down(self):
        if self.on_floor():
            return
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.y += 1
        self.draw()
    def hard_drop(self):
        while not self.on_floor():
            self.y += 1
        snap_piece()
    def snap(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    board[y][x] = self.colour
    def left(self):
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.x -= 1
        if self.intersect():
            self.x += 1
        self.draw()
    def right(self):
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.x += 1
        if self.intersect():
            self.x -= 1
        self.draw()
    def reset_position(self):
        self.x = 5 - len(self.shape[0]) // 2
        self.y = 0
    def rotate_right(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[x][-y-1] = c
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.rotate(shape)
        self.draw()
    def rotate_left(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[-x-1][y] = c
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.rotate(shape)
        self.draw()
    def rotate(self, new_shape):
        old_shape = self.shape
        old_x = self.x
        old_y = self.y
        self.shape = new_shape
        for dy in (0, 1, 2, -1):
            for dx in (0, 1, -1, 2, -2):
                self.x = old_x + dx
                self.y = old_y + dy
                if not self.intersect():
                    return
        self.x = old_x
        self.y = old_y
        self.shape = old_shape

def generate_shape():
    l = [[0, 0, 1], [1, 1, 1], [0, 0, 0]]
    j = [[1, 0, 0], [1, 1, 1], [0, 0, 0]]
    o = [[1, 1], [1, 1]]
    t = [[0, 1, 0], [1, 1, 1], [0, 0, 0]]
    s = [[0, 1, 1], [1, 1, 0], [0, 0, 0]]
    z = [[1, 1, 0], [0, 1, 1], [0, 0, 0]]
    i = [[0]*4, [1]*4, [0]*4, [0]*4]
    return random.choice([l, j, o, i, s, z, t])

def redraw():
    for y, row in enumerate(board):
        ty = y + 6
        for x, c in enumerate(row):
            tx = x + 1
            main_ui.set_pixel(c, tx, ty)
    current_piece.draw()
    main_ui.update_screen()

def init():
    main_ui.draw_text("arrows - move", 0, 0)
    main_ui.draw_text("up/z/x - rotate", 0, 1)
    main_ui.draw_text("down   - soft drop", 0, 2)
    main_ui.draw_text("space  - hard drop", 0, 3)
    main_ui.draw_text("c      - hold", 0, 4)
    for x in range(12):
        for y in range(22):
            main_ui.set_pixel(ui.COLOUR_WHITE, x, y+5)
    main_ui.update_screen()
    redraw()

def snap_piece():
    global ground_ticks, fall_ticks, current_piece
    current_piece.snap()
    ground_ticks = SNAP_TIME * TPS
    fall_ticks = TPS / FALL_SPEED
    current_piece = Piece()
    full = []
    for i, line in enumerate(board):
        if all([x != ui.COLOUR_DEFAULT for x in line]):
            full.append(i)
    offset = 0
    for i in full:
        del board[i-offset]
        offset += 1
    for i in full:
        board.insert(0, [ui.COLOUR_DEFAULT]*10)
    redraw()
    if current_piece.intersect():
        main_ui.draw_text("You died", 7, 14)
        raise ExitException

def tick():
    global ground_ticks, fall_ticks
    if current_piece.on_floor():
        ground_ticks -= 1
        if ground_ticks <= 0:
            snap_piece()
            return
    fall_ticks -= 1
    if fall_ticks <= 0:
        fall_ticks = TPS / FALL_SPEED
        current_piece.down()
    main_ui.update_screen()

def key(c):
    global hold_piece, current_piece, ground_ticks, fall_ticks
    c = c.decode("utf8")
    if c == 'j' or c == '\x1b[B': # down
        current_piece.down()
    elif c == 'c' or c == 'v': # hold
        ground_ticks = SNAP_TIME * TPS
        fall_ticks = TPS / FALL_SPEED
        current_piece.draw(colour=ui.COLOUR_DEFAULT)
        if hold_piece:
            hold_piece, current_piece = current_piece, hold_piece
        else:
            hold_piece = current_piece
            current_piece = Piece()
        current_piece.reset_position()
        current_piece.draw()
    elif c == 'h' or c == '\x1b[D': # left
        current_piece.left()
    elif c == 'l' or c == '\x1b[C': # right
        current_piece.right()
    elif c == 'z': # anticlockwise
        current_piece.rotate_left()
    elif c == 'x' or c == '\x1b[A': # clockwise
        current_piece.rotate_right()
    elif c == ' ': # hard drop
        current_piece.hard_drop()
    main_ui.update_screen()

class ExitException(Exception):
    pass

colour_buffer = []
board = [[ui.COLOUR_DEFAULT]*10 for i in range(20)]
hold_piece = None
ground_ticks = SNAP_TIME * TPS
fall_ticks = TPS / FALL_SPEED
current_piece = Piece()
main_ui = ui.TerminalUI()

try:
    # game loop
    init()
    main_ui.main_loop(tick, key, tps=TPS)
except ExitException: # proper exit
    current_piece.draw()
except KeyboardInterrupt: # ctrl-c
    pass
