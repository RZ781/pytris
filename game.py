import random, sys, copy, time
import ui, random

TPS = 10 # ticks per second
FALL_SPEED = 1.5 # blocks per second
LOCK_TIME = 0.5 # seconds
LOCK_COUNT = 15

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
            ty = self.y + y + 3
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
                    if y >= 0 and  self.game.board[y][x] != ui.COLOUR_DEFAULT:
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

    def left(self):
        success = True
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.x -= 1
        if self.intersect():
            self.x += 1
            success = False
        self.draw()
        return success

    def right(self):
        success = True
        self.draw(colour=ui.COLOUR_DEFAULT)
        self.x += 1
        if self.intersect():
            self.x -= 1
            success = False
        self.draw()
        return success

    def reset(self):
        self.x = self.base.x
        self.y = self.base.y
        self.shape = copy.deepcopy(self.base.shape)

    def copy(self):
        return Piece(copy.deepcopy(self.shape), self.colour, self.x, self.y, game=self.game, base=self)

    def rotate_right(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[x][-y-1] = c
        self.draw(colour=ui.COLOUR_DEFAULT)
        success = self.rotate(shape)
        self.draw()
        return success

    def rotate_left(self):
        shape = copy.deepcopy(self.shape)
        for y, row in enumerate(self.shape):
            for x, c in enumerate(row):
                shape[-x-1][y] = c
        self.draw(colour=ui.COLOUR_DEFAULT)
        success = self.rotate(shape)
        self.draw()
        return success

    def rotate_180(self):
        shape = copy.deepcopy(self.shape)
        for row in shape:
            row.reverse()
        shape.reverse()
        self.draw(colour=ui.COLOUR_DEFAULT)
        success = self.rotate(shape)
        self.draw()
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
        self.board = [[ui.COLOUR_DEFAULT]*10 for i in range(20)]
        self.hold_piece = None
        self.ground_ticks = LOCK_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.randomiser = randomiser
        self.current_piece = self.new_piece()
        self.controls = controls
        self.lock_count = LOCK_COUNT
        self.death_ticks = None

    def new_piece(self):
        piece = self.randomiser.next_piece().copy()
        piece.game = self
        return piece

    def lock_piece(self):
        success = self.current_piece.lock()
        if not success:
            self.ui.draw_text("You died", 8, 10)
            self.ui.update_screen()
            self.death_ticks = TPS * 2
            return
        self.ground_ticks = LOCK_TIME * TPS
        self.fall_ticks = TPS / FALL_SPEED
        self.lock_count = LOCK_COUNT
        self.current_piece = self.new_piece()
        # clear lines
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

    def lock_reset(self):
        if self.current_piece.on_floor() and self.lock_count:
            self.lock_count -= 1
            self.ground_ticks = LOCK_TIME * TPS

    def init(self, main_ui):
        self.ui = main_ui
        for x in range(12):
            for y in range(3):
                self.ui.set_pixel(ui.COLOUR_BRIGHT_BLACK, x, y)
        for x in range(12):
            for y in range(3,24):
                self.ui.set_pixel(ui.COLOUR_WHITE, x, y)
        self.ui.update_screen()
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
            self.current_piece.down()
        self.ui.update_screen()

    def key(self, c):
        if self.death_ticks is not None:
            return
        if c == self.controls[KEY_SOFT_DROP]:
            self.current_piece.down()
        elif c == self.controls[KEY_HOLD]:
            self.ground_ticks = LOCK_TIME * TPS
            self.fall_ticks = TPS / FALL_SPEED
            self.lock_count = LOCK_COUNT
            self.current_piece.draw(colour=ui.COLOUR_DEFAULT)
            if self.hold_piece:
                self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
            else:
                self.hold_piece = self.current_piece
                self.current_piece = self.new_piece()
            self.current_piece.reset()
            self.current_piece.draw()
        elif c == self.controls[KEY_LEFT]:
            if self.current_piece.left():
                self.lock_reset()
        elif c == self.controls[KEY_RIGHT]:
            if self.current_piece.right():
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
        self.ui.update_screen()

    def redraw(self):
        for y in range(1, 3):
            for x in range(1, 11):
                self.ui.set_pixel(ui.COLOUR_DEFAULT, x, y)
        for y, row in enumerate(self.board):
            ty = y + 3
            for x, c in enumerate(row):
                tx = x + 1
                self.ui.set_pixel(c, tx, ty)
        self.current_piece.draw()
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
S = Piece([[0, 1, 1], [1, 1, 0], [0, 0, 0]], ui.COLOUR_GREEN, 3, -2)
Z = Piece([[1, 1, 0], [0, 1, 1], [0, 0, 0]], ui.COLOUR_RED, 3, -2)
I = Piece([[0]*4, [1]*4, [0]*4, [0]*4], ui.COLOUR_CYAN, 3, -2)
pieces = [L, J, O, T, S, Z, I]
