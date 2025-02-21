import random, sys, copy, time
import ui, random

TPS = 10 # ticks per second
FALL_SPEED = 1.5 # blocks per second
SNAP_TIME = 1 # seconds

def generate_shape():
    l = [[0, 0, 1], [1, 1, 1], [0, 0, 0]]
    j = [[1, 0, 0], [1, 1, 1], [0, 0, 0]]
    o = [[1, 1], [1, 1]]
    t = [[0, 1, 0], [1, 1, 1], [0, 0, 0]]
    s = [[0, 1, 1], [1, 1, 0], [0, 0, 0]]
    z = [[1, 1, 0], [0, 1, 1], [0, 0, 0]]
    i = [[0]*4, [1]*4, [0]*4, [0]*4]
    return random.choice([l, j, o, i, s, z, t])

class Piece:
    def __init__(self, shape, colour, game, x=None, y=None):
        self.shape = shape
        self.game = game
        self.x = x
        self.y = y
        if x is None or y is None:
            self.reset_position()
        self.colour = colour
        self.buffer = ""

    def get_shadow(self): # create shadow/ghost piece
        shadow = Piece(self.shape, ui.COLOUR_BRIGHT_BLACK, self.game, self.x, self.y)
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
                self.game.ui.set_pixel(colour, tx+dx, ty)

    def intersect(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    if not 0 <= y < len(self.game.board):
                        return True
                    if not 0 <= x < len(self.game.board[y]):
                        return True
                    if self.game.board[y][x] != ui.COLOUR_DEFAULT:
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
        self.game.snap_piece()

    def snap(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    self.game.board[y][x] = self.colour

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

class Game(ui.Menu):
    def __init__(self):
        self.colour_buffer = []
        self.board = [[ui.COLOUR_DEFAULT]*10 for i in range(20)]
        self.hold_piece = None
        self.ground_ticks = SNAP_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.current_piece = self.new_piece()

    def new_piece(self):
        if not self.colour_buffer:
            for i in range(1, 7):
                self.colour_buffer.append(i)
            random.shuffle(self.colour_buffer)
        colour = self.colour_buffer.pop()
        return Piece(generate_shape(), colour, self)

    def snap_piece(self):
        self.current_piece.snap()
        self.ground_ticks = SNAP_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.current_piece = self.new_piece()
        full = []
        for i, line in enumerate(self.board):
            if all([x != ui.COLOUR_DEFAULT for x in line]):
                full.append(i)
        offset = 0
        for i in full:
            del self.board[i-offset]
            offset += 1
        for i in full:
            self.board.insert(0, [ui.COLOUR_DEFAULT]*10)
        self.redraw()
        if self.current_piece.intersect():
            self.ui.draw_text("You died", 7, 14)
            self.ui.update_screen()
            time.sleep(2)
            raise ui.ExitException

    def init(self, main_ui):
        self.ui = main_ui
        self.ui.draw_text("arrows - move", 0, 0)
        self.ui.draw_text("up/z/x - rotate", 0, 1)
        self.ui.draw_text("down   - soft drop", 0, 2)
        self.ui.draw_text("space  - hard drop", 0, 3)
        self.ui.draw_text("c      - hold", 0, 4)
        for x in range(12):
            for y in range(22):
                self.ui.set_pixel(ui.COLOUR_WHITE, x, y+5)
        self.ui.update_screen()
        self.redraw()

    def tick(self):
        if self.current_piece.on_floor():
            self.ground_ticks -= 1
            if self.ground_ticks <= 0:
                self.snap_piece()
                return
        self.fall_ticks -= 1
        if self.fall_ticks <= 0:
            self.fall_ticks = TPS / FALL_SPEED
            self.current_piece.down()
        self.ui.update_screen()

    def key(self, c):
        if c == 'j' or c == '\x1b[B': # down
            self.current_piece.down()
        elif c == 'c' or c == 'v': # hold
            self.ground_ticks = SNAP_TIME * TPS
            self.fall_ticks = TPS / FALL_SPEED
            self.current_piece.draw(colour=ui.COLOUR_DEFAULT)
            if self.hold_piece:
                self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
            else:
                self.hold_piece = self.current_piece
                self.current_piece = self.new_piece()
            self.current_piece.reset_position()
            self.current_piece.draw()
        elif c == 'h' or c == '\x1b[D': # left
            self.current_piece.left()
        elif c == 'l' or c == '\x1b[C': # right
            self.current_piece.right()
        elif c == 'z': # anticlockwise
            self.current_piece.rotate_left()
        elif c == 'x' or c == '\x1b[A': # clockwise
            self.current_piece.rotate_right()
        elif c == ' ': # hard drop
            self.current_piece.hard_drop()
        self.ui.update_screen()

    def redraw(self):
        for y, row in enumerate(self.board):
            ty = y + 6
            for x, c in enumerate(row):
                tx = x + 1
                self.ui.set_pixel(c, tx, ty)
        self.current_piece.draw()
        self.ui.update_screen()
