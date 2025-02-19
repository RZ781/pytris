#!/usr/bin/python3
import termios, select, time, sys, os, random, copy

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
        shadow = Piece(self.shape, self.x, self.y, 8)
        while not shadow.on_floor():
            shadow.y += 1
        return shadow
    def draw(self, colour=None, shadow=True, flush=True):
        if shadow:
            shadow = self.get_shadow()
            shadow.draw(colour=colour, shadow=False, flush=False)
            self.buffer += shadow.buffer
        if colour is None:
            colour = self.colour
        # set colour
        self.buffer += colours[colour]
        for y, row in enumerate(self.shape):
            if 1 not in row:
                continue
            x = row.index(1)
            count = sum(row[x:])
            # goto position and draw it
            self.buffer += f"\x1b[{7+y+self.y};{2+2*x+2*self.x}H" + "  " * count
        # reset
        if flush:
            self.buffer += "\x1b[;H\x1b[0m"
            sys.stdout.write(self.buffer)
            sys.stdout.flush()
            self.buffer = ""
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
                    if board[y][x]:
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
        self.draw(colour=0, flush=False)
        self.y += 1
        self.draw()
    def hard_drop(self):
        self.draw(colour=0, flush=False)
        while not self.on_floor():
            self.y += 1
        self.draw()
        snap_piece()
    def snap(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    board[y][x] = self.colour
    def left(self):
        self.draw(colour=0, flush=False)
        self.x -= 1
        if self.intersect():
            self.x += 1
        self.draw()
    def right(self):
        self.draw(colour=0, flush=False)
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
        self.draw(colour=0, flush=False)
        self.rotate(shape)
        self.draw()
    def rotate_left(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[-x-1][y] = c
        self.draw(colour=0, flush=False)
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
    i = [[0]*4, [0]*4, [1]*4, [0]*4]
    return random.choice([l, j, o, i, s, z, t])

def redraw():
    buffer = colours[0]
    prev_colour = 0
    for y, row in enumerate(board):
        buffer += f"\x1b[{7+y};2H"
        for c in row:
            if c != prev_colour:
                prev_colour = c
                buffer += colours[c]
            buffer += "  "
    sys.stdout.write(buffer)
    sys.stdout.flush()
    current_piece.draw()

def init():
    print(colours[0])
    os.system("clear")
    print("arrows\t- move")
    print("up/z/x\t- rotate")
    print("down\t- soft drop")
    print("space\t- hard drop")
    print("c, v\t- hold")
    print(colours[7], end="")
    for  i in range(22):
        print(" "*22)
    redraw()

def snap_piece():
    global ground_ticks, fall_ticks, current_piece
    current_piece.snap()
    ground_ticks = SNAP_TIME * TPS
    fall_ticks = TPS / FALL_SPEED
    current_piece = Piece()
    current_piece.draw()
    full = []
    for i, line in enumerate(board):
        if all(line):
            full.append(i)
    offset = 0
    for i in full:
        del board[i-offset]
        offset += 1
    for i in full:
        board.insert(0, [0]*10)
    redraw()
    if current_piece.intersect():
        print(colours[0] + "\x1b[15;8HYou died")
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

def key(c):
    global hold_piece, current_piece, ground_ticks, fall_ticks
    c = c.decode("utf8")
    if c == 'j' or c == '\x1b[B': # down
        current_piece.down()
    elif c == 'c' or c == 'v': # hold
        ground_ticks = SNAP_TIME * TPS
        fall_ticks = TPS / FALL_SPEED
        current_piece.draw(colour=0)
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

class ExitException(Exception):
    pass

colour_buffer = []
colours = ["\x1b[0m"] + [f"\x1b[4{x}m\x1b[3{x}m" for x in range(1, 8)] + ["\x1b[100m"]
board = [[0]*10 for i in range(20)]
hold_piece = None
ground_ticks = SNAP_TIME * TPS
fall_ticks = TPS / FALL_SPEED
current_piece = Piece()
initial_options = termios.tcgetattr(0)

try:
    # set up terminal options
    tetris_options = initial_options.copy()
    tetris_options[3] &= ~termios.ECHO
    tetris_options[3] &= ~termios.ICANON
    termios.tcsetattr(0, termios.TCSANOW, tetris_options)
    # game loop
    time_left = 1/TPS
    init()
    while True:
        start_time = time.perf_counter()
        r, _, _ = select.select([0], [], [], time_left)
        end_time = time.perf_counter()
        time_left -= end_time - start_time
        if r:
            key(os.read(0, 100))
        while time_left < 0:
            time_left += 1/TPS
            tick()
except ExitException: # proper exit
    current_piece.draw()
except KeyboardInterrupt: # ctrl-c
    pass
except BaseException as e: # error
    print(colours[0] + "\x1b[30;H")
    raise
finally:
    # reset terminal options
    termios.tcsetattr(0, termios.TCSANOW, initial_options)
    # reset terminal
    print(colours[0] + "\x1b[30;H")
