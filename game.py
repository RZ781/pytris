import random, sys, copy, time
import ui, random

TPS = 10 # ticks per second
FALL_SPEED = 1.5 # blocks per second
LOCK_TIME = 0.5 # seconds
LOCK_COUNT = 15
BOARD_WIDTH = 12
BOARD_HEIGHT = 22

KEY_LEFT = 0
KEY_RIGHT = 1
KEY_SOFT_DROP = 2
KEY_HARD_DROP = 3
KEY_ROTATE = 4
KEY_CLOCKWISE = 5
KEY_ANTICLOCKWISE = 6
KEY_180 = 7
KEY_HOLD = 8

class Piece:
    def __init__(self, shape, colour, x, y, game=None, base=None):
        self.shape = shape
        self.x = x
        self.y = y
        self.colour = colour
        self.base = base
        self.game = game

    def get_shadow(self): # create shadow/ghost piece
        shadow = self.copy()
        shadow.colour = ui.COLOUR_BRIGHT_BLACK
        while not shadow.on_floor():
            shadow.y += 1
        return shadow

    def draw(self, board_x, board_y, colour=None, shadow=True):
        if shadow:
            self.get_shadow().draw(board_x, board_y, colour=colour, shadow=False)
        if colour is None:
            colour = self.colour
        for y, row in enumerate(self.shape):
            if 1 not in row:
                continue
            x = row.index(1)
            count = sum(row[x:])
            tx = self.x + x + board_x
            ty = self.y + y + board_y
            for dx in range(count):
                self.game.ui.set_pixel(colour, tx+dx, ty)

    def intersect(self):
        for y, row in enumerate(self.shape):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    if y >= len(self.game.board):
                        return True
                    if not 0 <= x < len(self.game.board[y]):
                        return True
                    if y >= 0 and self.game.board[y][x] != ui.COLOUR_BLACK:
                        return True
        return False

    def on_floor(self):
        self.y += 1
        x = self.intersect()
        self.y -= 1
        return x

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        if self.intersect():
            self.x -= dx
            self.y -= dy
            return False
        return True

    def hard_drop(self):
        while not self.on_floor():
            self.y += 1
        self.game.lock_piece()

    def lock(self):
        for y, row in enumerate(self.shape):
            y += self.y
            if y < 0:
                return False
            for x, c in enumerate(row):
                x += self.x
                if c:
                    self.game.board[y][x] = self.colour
        return True

    def reset(self, hold=False):
        self.shape = copy.deepcopy(self.base.shape)
        if hold:
            if len(self.shape) == 4:
                self.x = self.y = 0
            else:
                self.x = self.y = 1
        else:
            self.x = self.base.x
            self.y = self.base.y

    def copy(self):
        return Piece(copy.deepcopy(self.shape), self.colour, self.x, self.y, game=self.game, base=self)

    def rotate_right(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[x][-y-1] = c
        success = self.rotate(shape)
        return success

    def rotate_left(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[-x-1][y] = c
        success = self.rotate(shape)
        return success

    def rotate_180(self):
        shape = copy.deepcopy(self.shape)
        for row in shape:
            row.reverse()
        shape.reverse()
        success = self.rotate(shape)
        return success

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
                    return True
        self.x = old_x
        self.y = old_y
        self.shape = old_shape
        return False

class Game(ui.Menu):
    def __init__(self, randomiser, controls):
        self.board = [[ui.COLOUR_BLACK]*10 for i in range(20)]
        self.hold_piece = None
        self.ground_ticks = LOCK_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.randomiser = randomiser
        self.controls = controls
        self.lock_count = LOCK_COUNT
        self.death_ticks = None
        self.next_pieces = [self.create_piece() for i in range(3)]
        self.current_piece = self.next_piece()

    def create_piece(self):
        piece = self.randomiser.next_piece().copy()
        piece.game = self
        return piece

    def next_piece(self):
        self.next_pieces.append(self.create_piece())
        piece = self.next_pieces.pop(0)
        piece.reset()
        return piece

    def lock_piece(self):
        success = self.current_piece.lock()
        if not success:
            self.ui.draw_text("You died", self.board_x+3, self.board_y+7)
            self.ui.update_screen()
            self.death_ticks = TPS * 2
            return
        self.ground_ticks = LOCK_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.lock_count = LOCK_COUNT
        self.current_piece = self.next_piece()
        # clear lines
        full = []
        for i, line in enumerate(self.board):
            if all([x != ui.COLOUR_BLACK for x in line]):
                full.append(i)
        offset = 0
        for i in full:
            del self.board[i-offset]
            offset += 1
        for i in full:
            self.board.insert(0, [ui.COLOUR_BLACK]*10)
        self.redraw()

    def lock_reset(self):
        if self.current_piece.on_floor() and self.lock_count:
            self.lock_count -= 1
            self.ground_ticks = LOCK_TIME * TPS

    def init(self, main_ui):
        self.ui = main_ui
        self.board_x = (self.ui.width - BOARD_WIDTH) // 2
        self.board_y = (self.ui.height - BOARD_HEIGHT) // 2
        self.hold_x = self.board_x - 5
        self.hold_y = self.board_y + 2
        self.next_x = self.board_x + 11
        self.next_y = self.board_y + 2
        for x in range(12):
            for y in range(3):
                # draw the gray border 3 above the main board
                self.ui.set_pixel(ui.COLOUR_BRIGHT_BLACK, x+self.board_x-1, y+self.board_y-3)
        for x in range(12):
            for y in range(21):
                if x in (0, 11) or y in (0, 20):
                    # draw main border
                    self.ui.set_pixel(ui.COLOUR_WHITE, x+self.board_x-1, y+self.board_y)
        for x in range(5):
            for y in range(6):
                if x == 0 or y in (0, 5):
                    self.ui.set_pixel(ui.COLOUR_WHITE, x+self.hold_x-1, y+self.hold_y-1)
        for x in range(5):
            for y in range(14):
                if x == 4 or y in (0, 13):
                    self.ui.set_pixel(ui.COLOUR_WHITE, x+self.next_x, y+self.next_y-1)
        self.redraw()

    def tick(self):
        if self.death_ticks is not None:
            self.death_ticks -= 1
            if self.death_ticks == 0:
                raise ui.ExitException
            return
        if self.current_piece.on_floor():
            if self.ground_ticks <= 0:
                self.lock_piece()
                return
            self.ground_ticks -= 1
        self.fall_ticks -= 1
        if self.fall_ticks <= 0:
            self.fall_ticks = TPS / FALL_SPEED
            self.current_piece.draw(self.board_x, self.board_y, colour=ui.COLOUR_BLACK)
            self.current_piece.move(0, 1)
            self.current_piece.draw(self.board_x, self.board_y)
            self.ui.update_screen()

    def key(self, c):
        if self.death_ticks is not None:
            return
        self.current_piece.draw(self.board_x, self.board_y, colour=ui.COLOUR_BLACK)
        if c == self.controls[KEY_SOFT_DROP]:
            self.current_piece.move(0, 1)
        elif c == self.controls[KEY_HOLD]:
            self.ground_ticks = LOCK_TIME * TPS
            self.fall_ticks = TPS / FALL_SPEED
            self.lock_count = LOCK_COUNT
            if self.hold_piece:
                self.hold_piece.draw(self.hold_x, self.hold_y, colour=ui.COLOUR_BLACK, shadow=False)
                self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
            else:
                self.hold_piece = self.current_piece
                self.current_piece = self.next_piece()
            self.current_piece.reset()
            self.hold_piece.reset(hold=True)
            self.hold_piece.draw(self.hold_x, self.hold_y, shadow=False)
        elif c == self.controls[KEY_LEFT]:
            if self.current_piece.move(-1, 0):
                self.lock_reset()
        elif c == self.controls[KEY_RIGHT]:
            if self.current_piece.move(1, 0):
                self.lock_reset()
        elif c == self.controls[KEY_ANTICLOCKWISE]:
            if self.current_piece.rotate_left():
                self.lock_reset()
        elif c == self.controls[KEY_ROTATE] or c == self.controls[KEY_CLOCKWISE]:
            if self.current_piece.rotate_right():
                self.lock_reset()
        elif c == self.controls[KEY_180]:
            if self.current_piece.rotate_180():
                self.lock_reset()
        elif c == self.controls[KEY_HARD_DROP]:
            self.current_piece.hard_drop()
        self.current_piece.draw(self.board_x, self.board_y)
        self.ui.update_screen()

    def redraw(self):
        for y in range(2):
            for x in range(10):
                self.ui.set_pixel(ui.COLOUR_BLACK, x+self.board_x, y+self.board_y-2)
        for y, row in enumerate(self.board):
            ty = y + self.board_y
            for x, c in enumerate(row):
                tx = x + self.board_x
                self.ui.set_pixel(c, tx, ty)
        self.current_piece.draw(self.board_x, self.board_y)
        for y in range(12):
            for x in range(4):
                self.ui.set_pixel(ui.COLOUR_BLACK, x+self.next_x, y+self.next_y)
        for i, piece in enumerate(self.next_pieces):
            piece.reset(hold=True)
            piece.y += i * 4
            piece.draw(self.next_x, self.next_y, shadow=False)
        self.ui.update_screen()

class Randomiser:
    def next_piece(self): raise NotImplemented

class ClassicRandomiser(Randomiser):
    def __init__(self):
        self.previous = None
    def next_piece(self):
        i = self.previous
        while i == self.previous:
            i = random.randint(0, 6)
        self.previous = i
        return pieces[i]

class BagRandomiser(Randomiser):
    def __init__(self, n_7_pieces, n_extras):
        self.n_7_pieces = n_7_pieces;
        self.n_extras = n_extras
        self.bag = []
    def next_piece(self):
        if not self.bag:
            for i in range(self.n_7_pieces):
                self.bag += pieces
            for i in range(self.n_extras):
                self.bag.append(random.choice(pieces))
            random.shuffle(self.bag)
        return self.bag.pop()

L = Piece([[0, 0, 1], [1, 1, 1], [0, 0, 0]], ui.COLOUR_YELLOW, 3, -2)
J = Piece([[1, 0, 0], [1, 1, 1], [0, 0, 0]], ui.COLOUR_BLUE, 3, -2)
O = Piece([[1, 1], [1, 1]], ui.COLOUR_BRIGHT_YELLOW, 4, -2)
T = Piece([[0, 1, 0], [1, 1, 1], [0, 0, 0]], ui.COLOUR_MAGENTA, 3, -2)
S = Piece([[0, 1, 1], [1, 1, 0], [0, 0, 0]], ui.COLOUR_BRIGHT_GREEN, 3, -2)
Z = Piece([[1, 1, 0], [0, 1, 1], [0, 0, 0]], ui.COLOUR_RED, 3, -2)
I = Piece([[0]*4, [1]*4, [0]*4, [0]*4], ui.COLOUR_CYAN, 3, -2)
pieces = [L, J, O, T, S, Z, I]
