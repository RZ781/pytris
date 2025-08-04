import random, sys, copy, time, enum, math
import ui, multiplayer
from typing import List, Optional, Dict

TPS = 60 # ticks per second
LOCK_COUNT = 15
MISCLICK_PROTECT_TIME = 0.15 # seconds

class Key(enum.Enum):
    LEFT = 0
    RIGHT = 1
    SOFT_DROP = 2
    HARD_DROP = 3
    ROTATE = 4
    CLOCKWISE = 5
    ANTICLOCKWISE = 6
    ROTATE_180 = 7
    HOLD = 8
    FORFEIT = 9

class Objective(enum.Enum):
    NONE = 0
    LINES = 1
    TIME = 2

class SpinType(enum.Enum):
    NONE = 0
    MINI = 1
    SPIN = 2

class GarbageType(enum.Enum):
    NONE = 0
    SLOW_CHEESE = 1
    FAST_CHEESE = 2
    SLOW_CLEAN = 3
    FAST_CLEAN = 4
    BACKFIRE = 5

class HoldType(enum.Enum):
    NONE = 0
    NORMAL = 1
    INFINITE = 2

class PieceType:
    def __init__(self, shape: List[List[int]], colour: ui.Colour, name: str) -> None:
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
        self.name = name

class Piece:
    def __init__(self, base: PieceType, game: "Game") -> None:
        self.base = base
        self.game = game
        self.name = self.base.name
        self.x = (self.game.config.width - len(self.base.shapes[0][0])) // 2
        self.y = -2
        self.rotation = 0
        self.rotation_last = False
        self.last_kick = 0

    def draw(self, board_x: int, board_y: int, colour: Optional[ui.Colour] = None, shadow: bool = True) -> None:
        if shadow:
            old_y = self.y
            while not self.on_floor():
                self.y += 1
            shadow_colour = colour
            if shadow_colour is None:
                shadow_colour = ui.Colour.LIGHT_GREY
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

    def intersect(self) -> bool:
        for y, row in enumerate(self.base.shapes[self.rotation]):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c and self.game.board_get(x, y):
                    return True
        return False

    def on_floor(self) -> bool:
        self.y += 1
        x = self.intersect()
        self.y -= 1
        return x

    def move(self, dx: int, dy: int) -> bool:
        self.x += dx
        self.y += dy
        if self.intersect():
            self.x -= dx
            self.y -= dy
            return False
        self.rotation_last = False
        return True

    def lock(self) -> None:
        for y, row in enumerate(self.base.shapes[self.rotation]):
            y += self.y
            for x, c in enumerate(row):
                x += self.x
                if c:
                    self.game.board_set(x, y, self.base.colour)

    def reset(self, hold: bool = False) -> None:
        self.rotation = 0
        if hold:
            if len(self.base.shapes[0]) == 4:
                self.x = self.y = 0
            else:
                self.x = self.y = 1
        else:
            self.x = (self.game.config.width - len(self.base.shapes[0][0])) // 2
            self.y = -2

    def rotate(self, rotation_change: int) -> bool:
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
                self.last_kick = 0
                return True
            self.rotation = old_rotation
            return False
        # check kick table
        old_x = self.x
        old_y = self.y
        clockwise = rotation_change % 4 == 1
        kick_table = I_KICK_TABLE if self.base is pieces[PIECE_I] else MAIN_KICK_TABLE
        index = old_rotation if clockwise else self.rotation
        for i, kick in enumerate(kick_table[index]):
            dx, dy = kick
            if not clockwise:
                dx = -dx
                dy = -dy
            self.x = old_x + dx
            self.y = old_y + dy
            if not self.intersect():
                self.rotation_last = True
                self.last_kick = i
                return True
        self.x = old_x
        self.y = old_y
        self.rotation = old_rotation
        return False

class Randomiser:
    def next_piece(self) -> int: raise NotImplementedError

class GameConfig:
    def __init__(self) -> None:
        self.width = 10
        self.height = 20
        self.lock_delay = 30
        self.garbage_type = GarbageType.NONE
        self.garbage_cancelling = True
        self.objective_type = Objective.NONE
        self.objective_count = 0
        self.infinite_soft_drop = False
        self.hold_type = HoldType.NORMAL

class Game(ui.Menu):
    board: Dict[int, List[ui.Colour]]
    hold_piece: Optional[Piece]
    death_ticks: Optional[int]
    controls: Dict[Key, str]
    connection: Optional[multiplayer.Connection]
    garbage_queue: List[int]

    def __init__(self, config: GameConfig, randomiser: Randomiser, controls: Dict[Key, str]) -> None:
        self.config = config
        self.t_spin = SpinType.SPIN
        self.mini_t_spin = SpinType.MINI
        self.immobile_t = SpinType.NONE
        self.all_spin = SpinType.NONE
        self.controls = controls
        self.board = {}
        self.hold_piece = None
        self.fall_speed = 1.2
        self.fall_ticks = TPS / self.fall_speed
        self.ground_ticks = config.lock_delay
        self.randomiser = randomiser
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
        self.enable_garbage_queue = config.garbage_type != GarbageType.NONE
        self.garbage_queue = []
        self.countdown = 3 * TPS
        self.connection = None

    def enable_custom_handling(self) -> bool:
        return True

    def set_connection(self, connection: multiplayer.Connection) -> None:
        self.connection = connection
        self.enable_garbage_queue = True

    def set_spins(self, t_spin: SpinType, mini_t_spin: SpinType, immobile_t: SpinType, all_spin: SpinType) -> None:
        self.t_spin = t_spin
        self.mini_t_spin = mini_t_spin
        self.immobile_t = immobile_t
        self.all_spin = all_spin

    def board_get(self, x: int, y: int) -> bool:
        if y >= self.config.height:
            return True
        if not 0 <= x < self.config.width:
            return True
        if y not in self.board:
            return False
        return self.board[y][x] != ui.Colour.BLACK

    def board_set(self, x: int, y: int, colour: ui.Colour) -> None:
        if y not in self.board:
            self.board[y] = [ui.Colour.BLACK] * self.config.width
        self.board[y][x] = colour

    def create_piece(self) -> Piece:
        return Piece(pieces[self.randomiser.next_piece()], self)

    def next_piece(self) -> Piece:
        self.next_pieces.append(self.create_piece())
        piece = self.next_pieces.pop(0)
        piece.reset()
        return piece

    def lock_piece(self) -> None:
        # spin detection
        spin_type = SpinType.NONE
        if self.current_piece.rotation_last:
            t_spin = False
            mini_t_spin = False
            if self.current_piece.base is pieces[PIECE_T]:
                corners = 0
                front_corners = 0
                back_corners = 0
                front_x, front_y = ((1, 0), (2, 1), (1, 2), (0, 1))[self.current_piece.rotation]
                for dx, dy in ((0, 0), (0, 2), (2, 0), (2, 2)):
                    x = self.current_piece.x + dx
                    y = self.current_piece.y + dy
                    if 0 <= x < self.config.width and 0 <= y < self.config.height:
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
                    if self.current_piece.last_kick == 4:
                        t_spin = True
                    else:
                        mini_t_spin = True
            immobile = True
            for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
                moved = self.current_piece.move(dx, dy)
                if moved:
                    immobile = False
                    self.current_piece.move(-dx, -dy)
                    break
            if t_spin:
                spin_type = self.t_spin
            elif mini_t_spin:
                spin_type = self.mini_t_spin
            elif immobile:
                if self.current_piece.base is pieces[PIECE_T]:
                    spin_type = self.immobile_t
                else:
                    spin_type = self.all_spin

        # clear lines
        self.current_piece.lock()
        full = []
        for y, line in self.board.items():
            if all([c != ui.Colour.BLACK for c in line]):
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

        # check all clear, b2b, combo
        all_clear = len(self.board) == 0
        if spin_type != SpinType.NONE:
            if len(full) > 0:
                self.b2b += 1
        else:
            if len(full) == 4:
                self.b2b += 1
            elif len(full) > 0:
                self.b2b = 0
        if len(full) > 0:
            self.combo += 1
        else:
            self.combo = 0

        # send and cancel garbage
        if len(full) > 0:
            if spin_type == SpinType.SPIN:
                lines = len(full) * 2
            elif len(full) == 4:
                lines = 4
            else:
                lines = len(full) - 1
            if all_clear:
                lines += 5
            if self.b2b > 1:
                lines += 1
            if self.combo > 1:
                if lines == 0:
                    lines = int(math.log(1 + 1.25 * (self.combo - 1)))
                else:
                    lines = int(lines * (1 + 0.25 * (self.combo - 1)))
            while lines > 0 and len(self.garbage_queue) > 0 and self.config.garbage_cancelling:
                if lines >= self.garbage_queue[0]:
                    lines -= self.garbage_queue.pop(0)
                else:
                    self.garbage_queue[0] -= lines
                    lines = 0
            self.send_garbage(lines)

        # receive garbage
        if len(self.garbage_queue) > 0 and len(full) == 0:
            for lines in self.garbage_queue:
                line = [ui.Colour.DARK_GREY] * self.config.width
                line[random.randint(0, self.config.width-1)] = ui.Colour.BLACK
                for _ in range(lines):
                    for i in sorted(self.board.keys()):
                        self.board[i-1] = self.board[i]
                        self.board.pop(i)
                    self.board[self.config.height-1] = line.copy()
                    if self.current_piece.intersect():
                        self.current_piece.y -= 1
            self.redraw()
            self.garbage_queue = []

        # add score
        if spin_type == SpinType.SPIN:
            multiplier = (400, 800, 1200, 1600)[len(full)]
        elif spin_type == SpinType.MINI:
            multiplier = (100, 200, 400, 800)[len(full)]
        else:
            multiplier = (0, 100, 300, 500, 800)[len(full)]
        if self.combo > 1:
            multiplier += (self.combo - 1) * 50
        if all_clear:
            if self.b2b > 1:
                multiplier += 3200
            else:
                multiplier += (0, 800, 1200, 1800, 2000)[len(full)]
        if self.b2b > 1 and len(full) > 0:
            multiplier = int(multiplier * 1.5)
        self.score += multiplier * self.level
        self.lines += len(full)
        self.level = self.lines // 10 + 1
        self.fall_speed = 1.2 + self.level * 0.5

        # action text
        name = ("", "Single", "Double", "Triple", "Quad")[len(full)]
        if spin_type == SpinType.SPIN:
            name = f"{self.current_piece.name} Spin {name}"
        elif spin_type == SpinType.MINI:
            name = f"Mini {self.current_piece.name} Spin {name}"
        if self.b2b > 1 and len(full) > 0:
            if self.b2b == 2:
                count = ""
            else:
                count = f" x{self.b2b-1}"
            name = f"B2B{count} {name}"
        if self.combo > 1:
            name = f"{name} Combo {self.combo-1}"
        if all_clear:
            name =  f"All Clear {name}"
        name = name.strip()

        # reset state and redraw
        self.ground_ticks = self.config.lock_delay
        self.fall_ticks = TPS / self.fall_speed
        self.lock_count = LOCK_COUNT
        self.current_piece = self.next_piece()
        self.held = False
        self.no_hard_drop_ticks = int(MISCLICK_PROTECT_TIME * TPS)
        self.redraw()
        if name:
            self.ui.draw_text(name, self.board_x+self.config.width//2, self.board_y-4, align=ui.Alignment.CENTER)
        if len(full) > 0:
            self.ui.beep()
        if self.current_piece.intersect():
            self.ui.draw_text("You died", self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
            self.ui.update_screen()
            self.end_game()

    def lock_reset(self) -> None:
        if self.current_piece.on_floor() and self.lock_count:
            self.lock_count -= 1
            self.ground_ticks = self.config.lock_delay

    def init(self, main_ui: ui.UI) -> None:
        self.ui = main_ui
        self.resize(main_ui.width, main_ui.height)

    def resize(self, width: int, height: int) -> None:
        self.board_x = (width - self.config.width) // 2
        self.board_y = (height - self.config.height) // 2
        if self.enable_garbage_queue:
            self.hold_x = self.board_x - 7
        else:
            self.hold_x = self.board_x - 5
        self.hold_y = self.board_y + 1
        self.next_x = self.board_x + self.config.width + 1
        self.next_y = self.board_y + 1
        self.counter_x = self.hold_x - 5
        self.counter_y = self.board_y + 13
        self.redraw()

    def end_game(self) -> None:
        self.death_ticks = TPS * 3
        if self.connection is not None:
            self.connection.close()

    def tick(self) -> None:
        if self.death_ticks is not None:
            self.death_ticks -= 1
            if self.death_ticks == 0:
                self.ui.pop_menu()
            return
        if self.countdown:
            self.countdown -= 1
            if self.countdown % 60 == 0:
                self.redraw()
            return
        self.ticks += 1
        self.redraw_timer()
        if self.connection is not None:
            messages = self.connection.recv()
            for command, data in messages:
                if command == multiplayer.CMD_RECEIVE_GARBAGE:
                    self.receive_garbage(int.from_bytes(data, "big"))
                elif command == multiplayer.CMD_EXIT:
                    self.ui.draw_text("Disconnected", self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
                    self.ui.draw_text("from server", self.board_x+self.config.width//2, self.board_y+8, align=ui.Alignment.CENTER)
                    self.ui.update_screen()
                    self.end_game()
                    return
                else:
                    exit(f"Unknown command from server: {command}")
        if self.config.garbage_type == GarbageType.SLOW_CHEESE:
            if self.ticks % 300 == 0:
                self.receive_garbage(1)
        elif self.config.garbage_type == GarbageType.FAST_CHEESE:
            if self.ticks % 120 == 0:
                self.receive_garbage(1)
        elif self.config.garbage_type == GarbageType.SLOW_CLEAN:
            if self.ticks % 600 == 0:
                self.receive_garbage(4)
        elif self.config.garbage_type == GarbageType.FAST_CLEAN:
            if self.ticks % 210 == 0:
                self.receive_garbage(4)
        if self.config.objective_type == Objective.TIME:
            if self.ticks >= self.config.objective_count * TPS:
                text = f"Score: {self.score}"
                self.ui.draw_text(text, self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
                self.ui.update_screen()
                self.end_game()
                return
        elif self.config.objective_type == Objective.LINES:
            if self.lines >= self.config.objective_count:
                seconds = self.ticks // TPS
                ms = int((self.ticks % TPS) / TPS * 1000)
                minutes = seconds // TPS
                seconds %= TPS
                text = f"Time: {minutes}:{seconds:02}.{ms:02}"
                self.ui.draw_text(text, self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
                self.ui.update_screen()
                self.end_game()
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
            self.current_piece.draw(self.board_x, self.board_y, colour=ui.Colour.BLACK)
            self.current_piece.move(0, 1)
            self.current_piece.draw(self.board_x, self.board_y)
        self.ui.update_screen()

    def key(self, c: str, repeated: bool = False) -> None:
        if self.death_ticks is not None:
            if c == self.controls[Key.FORFEIT] and not repeated:
                self.ui.pop_menu()
            return
        if c == self.controls[Key.FORFEIT]:
            self.redraw()
            self.ui.draw_text("Forfeited", self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
            self.ui.update_screen()
            self.end_game()
            return
        if self.countdown:
            return
        self.current_piece.draw(self.board_x, self.board_y, colour=ui.Colour.BLACK)
        if c == self.controls[Key.SOFT_DROP]:
            count = self.config.height * 2 if self.config.infinite_soft_drop else 1
            for i in range(count):
                if self.current_piece.move(0, 1):
                    self.score += 1
            self.redraw_counters()
        if c == self.controls[Key.HOLD] and not repeated:
            if not self.held and self.config.hold_type != HoldType.NONE:
                self.current_piece.draw(self.board_x, self.board_y, colour=ui.Colour.BLACK)
                self.redraw_hold_piece(colour=ui.Colour.BLACK)
                if self.config.hold_type == HoldType.NORMAL:
                    self.held = True
                self.ground_ticks = self.config.lock_delay
                self.fall_ticks = TPS / self.fall_speed
                self.lock_count = LOCK_COUNT
                if self.hold_piece:
                    self.hold_piece, self.current_piece = self.current_piece, self.hold_piece
                    first_hold = False
                else:
                    self.hold_piece = self.current_piece
                    self.current_piece = self.next_piece()
                    first_hold = True
                self.current_piece.reset()
                self.hold_piece.reset(hold=True)
                if first_hold:
                    self.redraw()
                else:
                    self.redraw_hold_piece()
        if c == self.controls[Key.LEFT]:
            if self.current_piece.move(-1, 0):
                self.lock_reset()
        if c == self.controls[Key.RIGHT]:
            if self.current_piece.move(1, 0):
                self.lock_reset()
        if c == self.controls[Key.ANTICLOCKWISE] and not repeated:
            if self.current_piece.rotate(-1):
                self.lock_reset()
        if (c == self.controls[Key.ROTATE] or c == self.controls[Key.CLOCKWISE]) and not repeated:
            if self.current_piece.rotate(1):
                self.lock_reset()
        if c == self.controls[Key.ROTATE_180] and not repeated:
            if self.current_piece.rotate(2):
                self.lock_reset()
        if c == self.controls[Key.HARD_DROP] and not repeated:
            if self.no_hard_drop_ticks <= 0:
                while self.current_piece.move(0, 1):
                    self.score += 2
                self.lock_piece()
        self.current_piece.draw(self.board_x, self.board_y)
        self.ui.update_screen()

    def send_garbage(self, lines: int) -> None:
        if self.connection is not None:
            self.connection.send(multiplayer.CMD_SEND_GARBAGE, lines.to_bytes(1, "big"))
        if self.config.garbage_type == GarbageType.BACKFIRE:
            self.receive_garbage(lines)

    def receive_garbage(self, lines: int) -> None:
        if lines < 1:
            return
        y = self.board_y + self.config.height - sum(self.garbage_queue) - 1
        for i in range(lines-1):
            self.ui.set_pixel(ui.Colour.BRIGHT_RED, self.board_x - 2, y)
            y -= 1
        self.ui.set_pixel(ui.Colour.RED, self.board_x - 2, y)
        self.ui.update_screen()
        self.garbage_queue.append(lines)

    def redraw_hold_piece(self, colour: Optional[ui.Colour] = None) -> None:
        if self.hold_piece:
            if colour is None and self.held:
                colour = ui.Colour.LIGHT_GREY
            self.hold_piece.draw(self.hold_x, self.hold_y, colour=colour, shadow=False)

    def redraw(self, update: bool = True) -> None:
        self.ui.clear()

        # draw main border
        if self.enable_garbage_queue:
            left = -2
        else:
            left = 0
        for x in range(left, self.config.width+2):
            for y in range(self.config.height+1):
                if x in (-2, 0, self.config.width+1) or y == self.config.height:
                    self.ui.set_pixel(ui.Colour.WHITE, x+self.board_x-1, y+self.board_y)

        # draw hold border
        if self.config.hold_type != HoldType.NONE:
            for x in range(5):
                for y in range(6):
                    if x == 0 or y in (0, 5):
                        self.ui.set_pixel(ui.Colour.WHITE, x+self.hold_x-1, y+self.hold_y-1)

        # draw next piece border
        for x in range(6):
            for y in range(14):
                if x in (0, 5) or y in (0, 13):
                    self.ui.set_pixel(ui.Colour.WHITE, x+self.next_x-1, y+self.next_y-1)

        # draw board
        for y, row in self.board.items():
            ty = y + self.board_y
            for x, c in enumerate(row):
                tx = x + self.board_x
                self.ui.set_pixel(c, tx, ty)

        # draw garbage meter
        if self.enable_garbage_queue:
            y = self.board_y + self.config.height - 1
            for lines in self.garbage_queue:
                if lines == 0:
                    continue
                for i in range(lines):
                    self.ui.set_pixel(ui.Colour.BRIGHT_RED, self.board_x-2, y)
                    y -= 1
                self.ui.set_pixel(ui.Colour.RED, self.board_x-2, y+1)

        self.current_piece.draw(self.board_x, self.board_y)
        for y in range(12):
            for x in range(4):
                self.ui.set_pixel(ui.Colour.BLACK, x+self.next_x, y+self.next_y)
        for i, piece in enumerate(self.next_pieces):
            piece.reset(hold=True)
            piece.y += i * 4
            piece.draw(self.next_x, self.next_y, shadow=False)
        for y in range(4):
            for x in range(4):
                self.ui.set_pixel(ui.Colour.BLACK, x+self.hold_x, y+self.hold_y)
        self.redraw_hold_piece()
        self.redraw_counters()
        if self.countdown > 0:
            self.ui.draw_text(str(self.countdown//TPS), self.board_x+self.config.width//2, self.board_y+7, align=ui.Alignment.CENTER)
        if update:
            self.ui.update_screen()

    def redraw_counters(self) -> None:
        self.ui.draw_text(f"Level: {self.level}", self.counter_x, self.counter_y)
        self.ui.draw_text(f"Lines: {self.lines}", self.counter_x, self.counter_y+1)
        self.ui.draw_text(f"Score: {self.score}", self.counter_x, self.counter_y+2)

    def redraw_timer(self) -> None:
        seconds = self.ticks // 60
        minutes = seconds // 60
        seconds %= 60
        self.ui.draw_text(f"Time: {minutes}:{seconds:02}", self.counter_x, self.counter_y+4)

class ClassicRandomiser(Randomiser):
    previous: int
    def __init__(self) -> None:
        self.previous = 0
    def next_piece(self) -> int:
        i = self.previous
        while i == self.previous:
            i = random.randint(0, 6)
        self.previous = i
        return i

class BagRandomiser(Randomiser):
    bag: List[int]
    def __init__(self, n_7_pieces: int, n_extras: int) -> None:
        self.n_7_pieces = n_7_pieces;
        self.n_extras = n_extras
        self.bag = []
    def next_piece(self) -> int:
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
    PieceType([[0, 0, 1], [1, 1, 1], [0, 0, 0]], ui.Colour.ORANGE, "L"),
    PieceType([[1, 0, 0], [1, 1, 1], [0, 0, 0]], ui.Colour.BLUE, "J"),
    PieceType([[1, 1], [1, 1]], ui.Colour.YELLOW, "O"),
    PieceType([[0, 1, 0], [1, 1, 1], [0, 0, 0]], ui.Colour.MAGENTA, "T"),
    PieceType([[0, 1, 1], [1, 1, 0], [0, 0, 0]], ui.Colour.GREEN, "S"),
    PieceType([[1, 1, 0], [0, 1, 1], [0, 0, 0]], ui.Colour.RED, "Z"),
    PieceType([[0]*4, [1]*4, [0]*4, [0]*4], ui.Colour.CYAN, "I"),
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
