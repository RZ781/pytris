import random, sys, copy, time
import ui, random

TPS = 60 # ticks per second
LOCK_TIME = 0.5 # seconds
LOCK_COUNT = 15
BOARD_WIDTH = 12
BOARD_HEIGHT = 22
MISCLICK_PROTECT_TIME = 0.15 # seconds

KEY_LEFT = 0
KEY_RIGHT = 1
KEY_SOFT_DROP = 2
KEY_HARD_DROP = 3
KEY_ROTATE = 4
KEY_CLOCKWISE = 5
KEY_ANTICLOCKWISE = 6
KEY_180 = 7
KEY_HOLD = 8

OBJECTIVE_NONE = 0
OBJECTIVE_LINES = 1
OBJECTIVE_TIME = 2

class PieceType:
    def __init__(self, shape, colour, spawn_x, spawn_y):
        shapes = []
        for i in range(4):
            shapes.append(shape)
            new_shape = copy.deepcopy(shape)
            for y, row in enumerate(shape):
                for x, c in enumerate(row):
                    new_shape[x][-y-1] = c
            shape = new_shape
        self.shapes = shapes
        self.colour = colour
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

class Piece:
    def __init__(self, base, game):
        self.x = base.spawn_x
        self.y = base.spawn_y
        self.rotation = 0
        self.base = base
        self.game = game
        self.rotation_last = False

    def draw(self, board_x, board_y, colour=None, shadow=True):
        if shadow:
            old_y = self.y
            while not self.on_floor():
                self.y += 1
            shadow_colour = colour
            if shadow_colour is None:
                shadow_colour = ui.COLOUR_BRIGHT_BLACK
            self.draw(board_x, board_y, colour=shadow_colour, shadow=False)
            self.y = old_y
        if colour is None:
            colour = self.base.colour
        for y, row in enumerate(self.base.shapes[self.rotation]):
            if 1 not in row:
                continue
            x = row.index(1)
            count = sum(row[x:])
            tx = self.x + x + board_x
            ty = self.y + y + board_y
            for dx in range(count):
                self.game.ui.set_pixel(colour, tx+dx, ty)

    def intersect(self):
        for y, row in enumerate(self.base.shapes[self.rotation]):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c and self.game.board_get(x, y):
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
        self.rotation_last = False
        return True

    def lock(self):
        for y, row in enumerate(self.base.shapes[self.rotation]):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    self.game.board_set(x, y, self.base.colour)

    def reset(self, hold=False):
        self.rotation = 0
        if hold:
            if len(self.base.shapes[0]) == 4:
                self.x = self.y = 0
            else:
                self.x = self.y = 1
        else:
            self.x = self.base.spawn_x
            self.y = self.base.spawn_y

    def rotate(self, rotation_change):
        # O pieces don't rotate
        if self.base is pieces[PIECE_O]:
            return True
        # handle 180 rotations
        old_rotation = self.rotation
        self.rotation += rotation_change
        self.rotation %= 4
        if rotation_change % 4 == 2:
            if not self.intersect():
                self.rotation_last = True
                return True
            self.rotation = old_rotation
            return False
        # check kick table
        old_x = self.x
        old_y = self.y
        clockwise = rotation_change % 4 == 1
        kick_table = I_KICK_TABLE if self.base is pieces[PIECE_I] else MAIN_KICK_TABLE
        index = old_rotation if clockwise else self.rotation
        for dx, dy in kick_table[index]:
            if not clockwise:
                dx = -dx
                dy = -dy
            self.x = old_x + dx
            self.y = old_y + dy
            if not self.intersect():
                self.rotation_last = True
                return True
        self.x = old_x
        self.y = old_y
        self.rotation = old_rotation
        return False

class Game(ui.Menu):
    def __init__(self, objective_type, objective_count, randomiser, controls, infinite_soft_drop, infinite_hold):
        self.objective_type = objective_type
        self.objective_count = objective_count
        self.infinite_soft_drop = infinite_soft_drop
        self.infinite_hold = infinite_hold
        self.board = {}
        self.hold_piece = None
        self.fall_speed = 1.2
        self.fall_ticks = TPS / self.fall_speed
        self.ground_ticks = LOCK_TIME * TPS
        self.randomiser = randomiser
        self.controls = controls
        self.lock_count = LOCK_COUNT
        self.death_ticks = None
        self.next_pieces = [self.create_piece() for i in range(3)]
        self.current_piece = self.next_piece()
        self.level = 1
        self.lines = 0
        self.score = 0
        self.held = False
        self.no_hard_drop_ticks = 0
        self.ticks = 0
        self.b2b = 0
        self.combo = 0

    def board_get(self, x, y):
        if y > 19:
            return True
        if not 0 <= x < 10:
            return True
        if y not in self.board:
            return False
        return self.board[y][x] != ui.COLOUR_BLACK

    def board_set(self, x, y, colour):
        if y not in self.board:
            self.board[y] = [ui.COLOUR_BLACK] * 10
        self.board[y][x] = colour

    def create_piece(self):
        return Piece(pieces[self.randomiser.next_piece()], self)

    def next_piece(self):
        self.next_pieces.append(self.create_piece())
        piece = self.next_pieces.pop(0)
        piece.reset()
        return piece

    def lock_piece(self):
        self.current_piece.lock()

        # t spin detection
        t_spin = False
        mini_t_spin = False
        if self.current_piece.base is pieces[PIECE_T] and self.current_piece.rotation_last:
            corners = 0
            front_corners = 0
            back_corners = 0
            front_x, front_y = ((1, 0), (2, 1), (1, 2), (0, 1))[self.current_piece.rotation]
            for dx, dy in ((0, 0), (0, 2), (2, 0), (2, 2)):
                x = self.current_piece.x + dx
                y = self.current_piece.y + dy
                if 0 <= x < 10 and 0 <= y < 20:
                    corner_filled = self.board_get(x, y)
                else:
                    corner_filled = True
                if front_x == dx or front_y == dy:
                    front_corners += corner_filled
                else:
                    back_corners += corner_filled
            if front_corners == 2 and back_corners >= 1:
                t_spin = True
            elif front_corners == 1 and back_corners == 2:
                mini_t_spin = True

        # clear lines
        full = []
        for y, line in self.board.items():
            if all([c != ui.COLOUR_BLACK for c in line]):
                full.append(y)
        offset = 0
        rows = sorted(self.board.keys())
        rows.reverse()
        for i in rows:
            if i in full:
                del self.board[i]
                offset += 1
            else:
                if offset > 0:
                    self.board[i+offset] = self.board[i]
                    del self.board[i]

        # add score
        if t_spin:
            multiplier = (400, 800, 1200, 1600)[len(full)]
        elif mini_t_spin:
            multiplier = (100, 200, 400)[len(full)]
        else:
            multiplier = (0, 100, 300, 500, 800)[len(full)]
        if t_spin or mini_t_spin:
            if len(full) > 0:
                self.b2b += 1
        else:
            if len(full) == 4:
                self.b2b += 1
            elif len(full) > 0:
                self.b2b = 0
        multiplier += self.combo * 50
        if self.b2b > 1 and len(full) > 0:
            multiplier = int(multiplier * 1.5)
        self.score += multiplier * self.level
        self.lines += len(full)
        self.level = self.lines // 10 + 1
        self.fall_speed = 1.2 + self.level * 0.5
        if len(full) > 0:
            self.combo += 1
        else:
            self.combo = 0

        # reset state
        self.ground_ticks = LOCK_TIME * TPS
        self.fall_ticks = TPS / self.fall_speed
        self.lock_count = LOCK_COUNT
        self.current_piece = self.next_piece()
        self.held = False
        self.no_hard_drop_ticks = MISCLICK_PROTECT_TIME * TPS
        self.redraw()
        if self.current_piece.intersect():
            self.ui.draw_text("You died", self.board_x+3, self.board_y+7)
            self.ui.update_screen()
            self.death_ticks = TPS * 2
            return

        # action text
        name = ("", "Single", "Double", "Triple", "Quad")[len(full)]
        if t_spin:
            name = f"T Spin {name}"
        elif mini_t_spin:
            name = f"Mini T Spin {name}"
        if self.b2b > 1 and len(full) > 0:
            name = f"B2B {name}"
        if self.combo > 1:
            name = f"{name} Combo {self.combo-1}"
        name = name.strip()
        self.ui.draw_text(" "*32, self.board_x-3, self.board_y-4)
        if name:
            self.ui.draw_text(name, self.board_x+5-len(name)//4, self.board_y-4)
            self.ui.update_screen()
        if len(full) > 0:
            self.ui.beep()

    def lock_reset(self):
        if self.current_piece.on_floor() and self.lock_count:
            self.lock_count -= 1
            self.ground_ticks = LOCK_TIME * TPS

    def init(self, main_ui):
        self.ui = main_ui
        self.resize(main_ui.width, main_ui.height)

    def resize(self, width, height):
        self.board_x = (width - BOARD_WIDTH) // 2
        self.board_y = (height - BOARD_HEIGHT) // 2
        self.hold_x = self.board_x - 5
        self.hold_y = self.board_y + 1
        self.next_x = self.board_x + 11
        self.next_y = self.board_y + 1
        self.counter_x = self.board_x - 8
        self.counter_y = self.board_y + 15
        self.redraw()

    def tick(self):
        if self.death_ticks is not None:
            self.death_ticks -= 1
            if self.death_ticks == 0:
                raise ui.ExitException
            return
        self.ticks += 1
        if self.objective_type == OBJECTIVE_TIME:
            if self.ticks >= self.objective_count * TPS:
                text = f"Score: {self.score}"
                self.ui.draw_text(text, self.board_x+5-len(text)//4, self.board_y+7)
                self.ui.update_screen()
                self.death_ticks = 3 * TPS
                return
        elif self.objective_type == OBJECTIVE_LINES:
            if self.lines >= self.objective_count:
                seconds = self.ticks // TPS
                ms = int((self.ticks % TPS) / TPS * 1000)
                minutes = seconds // TPS
                seconds %= TPS
                text = f"Time: {minutes}:{seconds:02}.{ms:02}"
                self.ui.draw_text(text, self.board_x+5-len(text)//4, self.board_y+7)
                self.ui.update_screen()
                self.death_ticks = 3 * TPS
                return
        if self.no_hard_drop_ticks > 0:
            self.no_hard_drop_ticks -= 1
        if self.current_piece.on_floor():
            if self.ground_ticks <= 0:
                self.lock_piece()
                return
            self.ground_ticks -= 1
        self.fall_ticks -= 1
        if self.fall_ticks <= 0:
            self.fall_ticks = TPS / self.fall_speed
            self.current_piece.draw(self.board_x, self.board_y, colour=ui.COLOUR_BLACK)
            self.current_piece.move(0, 1)
            self.current_piece.draw(self.board_x, self.board_y)
            self.ui.update_screen()

    def key(self, c):
        if self.death_ticks is not None:
            return
        self.current_piece.draw(self.board_x, self.board_y, colour=ui.COLOUR_BLACK)
        if c == self.controls[KEY_SOFT_DROP]:
            count = 25 if self.infinite_soft_drop else 1
            for i in range(count):
                if self.current_piece.move(0, 1):
                    self.score += 1
            self.redraw_counters()
        if c == self.controls[KEY_HOLD]:
            if not self.held:
                if not self.infinite_hold:
                    self.held = True
                self.ground_ticks = LOCK_TIME * TPS
                self.fall_ticks = TPS / self.fall_speed
                self.lock_count = LOCK_COUNT
                if self.hold_piece:
                    self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
                else:
                    self.hold_piece = self.current_piece
                    self.current_piece = self.next_piece()
                self.current_piece.reset()
                self.hold_piece.reset(hold=True)
                self.redraw()
        if c == self.controls[KEY_LEFT]:
            if self.current_piece.move(-1, 0):
                self.lock_reset()
        if c == self.controls[KEY_RIGHT]:
            if self.current_piece.move(1, 0):
                self.lock_reset()
        if c == self.controls[KEY_ANTICLOCKWISE]:
            if self.current_piece.rotate(-1):
                self.lock_reset()
        if c == self.controls[KEY_ROTATE] or c == self.controls[KEY_CLOCKWISE]:
            if self.current_piece.rotate(1):
                self.lock_reset()
        if c == self.controls[KEY_180]:
            if self.current_piece.rotate(2):
                self.lock_reset()
        if c == self.controls[KEY_HARD_DROP]:
            if self.no_hard_drop_ticks <= 0:
                while self.current_piece.move(0, 1):
                    self.score += 2
                self.lock_piece()
        self.current_piece.draw(self.board_x, self.board_y)
        self.ui.update_screen()

    def redraw(self):
        self.ui.clear()
        for x in range(12):
            for y in range(21):
                if x in (0, 11) or y == 20:
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
        for y, row in self.board.items():
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
        for y in range(4):
            for x in range(4):
                self.ui.set_pixel(ui.COLOUR_BLACK, x+self.hold_x, y+self.hold_y)
        if self.hold_piece:
            if self.held:
                self.hold_piece.draw(self.hold_x, self.hold_y, colour=ui.COLOUR_BRIGHT_BLACK, shadow=False)
            else:
                self.hold_piece.draw(self.hold_x, self.hold_y, shadow=False)
        self.redraw_counters()
        self.ui.update_screen()

    def redraw_counters(self):
        self.ui.draw_text(f"Level: {self.level}", self.counter_x, self.counter_y)
        self.ui.draw_text(f"Lines: {self.lines}", self.counter_x, self.counter_y+1)
        self.ui.draw_text(f"Score: {self.score}", self.counter_x, self.counter_y+2)

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
        return i

class BagRandomiser(Randomiser):
    def __init__(self, n_7_pieces, n_extras):
        self.n_7_pieces = n_7_pieces;
        self.n_extras = n_extras
        self.bag = []
    def next_piece(self):
        if not self.bag:
            self.bag = list(range(7)) * self.n_7_pieces
            for i in range(self.n_extras):
                self.bag.append(random.randint(0, 6))
            random.shuffle(self.bag)
        return self.bag.pop()

PIECE_L = 0
PIECE_J = 1
PIECE_O = 2
PIECE_T = 3
PIECE_S = 4
PIECE_Z = 5
PIECE_I = 6

pieces = [
    PieceType([[0, 0, 1], [1, 1, 1], [0, 0, 0]], ui.COLOUR_YELLOW, 3, -2),
    PieceType([[1, 0, 0], [1, 1, 1], [0, 0, 0]], ui.COLOUR_BLUE, 3, -2),
    PieceType([[1, 1], [1, 1]], ui.COLOUR_BRIGHT_YELLOW, 4, -2),
    PieceType([[0, 1, 0], [1, 1, 1], [0, 0, 0]], ui.COLOUR_MAGENTA, 3, -2),
    PieceType([[0, 1, 1], [1, 1, 0], [0, 0, 0]], ui.COLOUR_BRIGHT_GREEN, 3, -2),
    PieceType([[1, 1, 0], [0, 1, 1], [0, 0, 0]], ui.COLOUR_RED, 3, -2),
    PieceType([[0]*4, [1]*4, [0]*4, [0]*4], ui.COLOUR_CYAN, 3, -2),
]

KICKS = ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2))

MAIN_KICK_TABLE = (
        KICKS,
        tuple((-x, -y) for x, y in KICKS),
        tuple((-x, y) for x, y in KICKS),
        tuple((x, -y) for x, y in KICKS),
)

I_KICK_TABLE = (
    ((0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)),
    ((0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)),
    ((0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)),
    ((0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1))
)
