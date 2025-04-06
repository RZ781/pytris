import sys, time, os, shutil
import config

COLOUR_BLACK    = 0
COLOUR_RED      = 1
COLOUR_GREEN    = 2
COLOUR_YELLOW   = 3
COLOUR_BLUE     = 4
COLOUR_MAGENTA  = 5
COLOUR_CYAN     = 6
COLOUR_WHITE    = 7

COLOUR_BRIGHT_BLACK    = 8
COLOUR_BRIGHT_RED      = 9
COLOUR_BRIGHT_GREEN    = 10
COLOUR_BRIGHT_YELLOW   = 11
COLOUR_BRIGHT_BLUE     = 12
COLOUR_BRIGHT_MAGENTA  = 13
COLOUR_BRIGHT_CYAN     = 14
COLOUR_BRIGHT_WHITE    = 15

COLOURS = (
    (0, 0, 0),
    (188, 46, 61),
    (8, 148, 24),
    (202, 99, 41),
    (55, 67, 190),
    (155, 55, 134),
    (89, 154, 209),
    (255, 255, 255),
    (128, 128, 128),
    (237, 28, 36),
    (117, 174, 54),
    (253, 255, 12),
    (4, 42, 255),
    (196, 6, 255),
    (8, 254, 255),
    (255, 255, 255),
)

SCANCODE_TO_ESCAPE_CODE = {
    0x48: "\x1b[A", # up
    0x50: "\x1b[B", # down
    0x4D: "\x1b[C", # right
    0x4B: "\x1b[D", # left
    0x47: "\x1b[1~", # home
    0x52: "\x1b[2~", # insert
    0x53: "\x1b[3~", # delete
    0x4F: "\x1b[4~", # end
    0x49: "\x1b[5~", # page up
    0x51: "\x1b[6~", # page down
    0x08: "\x7f", # delete
}

class ExitException(Exception):
    pass

class Menu:
    def init(self, ui): raise NotImplementedError
    def tick(self): raise NotImplementedError
    def key(self, c): raise NotImplementedError
    def resize(self, width, height): raise NotImplementedError

class UI:
    def init(self): raise NotImplementedError
    def quit(self): raise NotImplementedError
    def draw_text(self, text, x, y, fg_colour=COLOUR_WHITE, bg_colour=COLOUR_BLACK): raise NotImplementedError
    def set_pixel(self, colour, x, y): raise NotImplementedError
    def beep(self): raise NotImplementedError
    def update_screen(self): raise NotImplementedError
    def main_loop(self, menu, tps=10): raise NotImplementedError
    def menu(self, options, starting_option=0): raise NotImplementedError
    def get_key(self): raise NotImplementedError
    def options_menu(self): raise NotImplementedError

class BaseTerminalUI(UI):
    MODES = ["4 bit", "8 bit", "24 bit", "Monochrome"]
    COLOURS_8_BIT = (232, 160, 40, 166, 21, 129, 45, 255, 243, 196, 118, 226, 27, 165, 51, 255)
    fg_colour_codes = [
        [f"\x1b[3{x}m" for x in range(7)] + [""] + [f"\x1b[9{x}m" for x in range(8)], # 4 bit
        [f"\x1b[38;5;{x}m" for x in COLOURS_8_BIT], # 8 bit
        [f"\x1b[38;2;{r};{g};{b}m" for r, g, b in COLOURS], # 24 bit
        [""]*7 + ["\x1b[0m"] + [""]*8, # monochrome
    ]
    bg_colour_codes = [
        [""] + [f"\x1b[4{x}m" for x in range(1, 8)] + [f"\x1b[10{x}m" for x in range(8)], # 4 bit
        [f"\x1b[48;5;{x}m" for x in COLOURS_8_BIT], # 8 bit
        [f"\x1b[48;2;{r};{g};{b}m" for r, g, b in COLOURS], # 24 bit
        ["\x1b[0m"] + ["\x1b[7m"]*15, # monochrome
    ]
    reset_code = "\x1b[0m"

    def __init__(self):
        self.fg_colour = COLOUR_WHITE
        self.bg_colour = COLOUR_BLACK
        self.buffer = ""
        self.inital_options = None
        terminal_size = shutil.get_terminal_size()
        self.width = terminal_size.columns // 2
        self.height = terminal_size.lines
        self.mode = 1
        colour_mode = config.load("colours")
        if colour_mode:
            mode = colour_mode["mode"]
            if mode in BaseTerminalUI.MODES:
                self.mode = BaseTerminalUI.MODES.index(mode)
        self.enable_beep = False
        beep = config.load("beep")
        if beep:
            self.enable_beep = beep["enabled"]

    def clear(self):
        self.buffer += "\x1b[0m\x1b[2J"

    def set_fg_colour(self, colour):
        if colour != self.fg_colour:
            if colour == COLOUR_WHITE:
                self.buffer += TerminalUI.reset_code
                # set background colour again if resetting terminal for foreground
                old_bg_colour = self.bg_colour
                self.fg_colour = COLOUR_WHITE
                self.bg_colour = COLOUR_BLACK
                self.set_bg_colour(old_bg_colour)
            else:
                self.buffer += TerminalUI.fg_colour_codes[self.mode][colour]
                self.fg_colour = colour

    def set_bg_colour(self, colour):
        if colour != self.bg_colour:
            if colour == COLOUR_BLACK:
                self.buffer += TerminalUI.reset_code
                # set foreground colour again if resetting terminal for background
                old_fg_colour = self.fg_colour
                self.fg_colour = COLOUR_WHITE
                self.bg_colour = COLOUR_BLACK
                self.set_fg_colour(old_fg_colour)
            else:
                self.buffer += TerminalUI.bg_colour_codes[self.mode][colour]
                self.bg_colour = colour

    def goto(self, x, y):
        self.buffer += f"\x1b[{y+1};{2*x+1}H" # double x so pixels are approximately square

    def draw_text(self, text, x, y, fg_colour=COLOUR_WHITE, bg_colour=COLOUR_BLACK):
        self.set_fg_colour(fg_colour)
        self.set_bg_colour(bg_colour)
        self.goto(x, y)
        self.buffer += text

    def set_pixel(self, colour, x, y):
        self.goto(x, y)
        if self.mode == 3 and colour == COLOUR_BRIGHT_BLACK:
            self.set_bg_colour(COLOUR_BLACK)
            self.buffer += "''"
        elif self.mode == 3 and colour == COLOUR_WHITE:
            self.set_bg_colour(COLOUR_BLACK)
            self.buffer += "##"
        else:
            self.set_bg_colour(colour)
            self.buffer += "  "

    def beep(self):
        if self.enable_beep:
            self.buffer += "\x07"

    def update_screen(self):
        self.goto(0, 0)
        sys.stdout.write(self.buffer)
        sys.stdout.flush()
        self.buffer = ""

    def menu(self, options, starting_option=0):
        menu = TerminalMenu(options, starting_option)
        self.main_loop(menu)
        return menu.current

    def options_menu(self):
        options = ("Colours", "Beep", "Close")
        while True:
            option = self.menu(options)
            if option == 0:
                self.mode = self.menu(BaseTerminalUI.MODES, starting_option=self.mode)
                config.save("colours", {"mode": BaseTerminalUI.MODES[self.mode]})
            elif option == 1:
                self.enable_beep = self.menu(("Enable", "Disable"), starting_option = 0 if self.beep else 1) == 0
                config.save("beep", {"enabled": self.enable_beep})
            else:
                break

class TerminalMenu:
    def __init__(self, options, current):
        self.columns = []
        self.n_options = len(options)
        length = max(len(option) for option in options)
        for i in range(length):
            column = []
            for option in options:
                if isinstance(option, str) and i == 0:
                    column.append(option)
                elif isinstance(option, tuple) and i < len(option):
                    column.append(option[i])
                else:
                    column.append("")
            self.columns.append(column)
        self.current = current
        self.ui = None
    def init(self, ui):
        self.ui = ui
        self.resize(ui.width, ui.height)
    def resize(self, width, height):
        self.ui.clear()
        text_width = max(max(len(x)//2 + 4 for x in column) for column in self.columns)
        self.menu_x = (width - text_width) // 2
        self.menu_y = height // 5
        column_x = self.menu_x + 1
        for column in self.columns:
            for i, option in enumerate(column):
                self.ui.draw_text(option, column_x, self.menu_y+i)
            max_length = max(len(option) for option in column)
            column_x += max_length // 2 + 4
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
    def key(self, c):
        self.ui.draw_text(" ", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
        if c == '\x1b[A' or c == 'k':
            self.current -= 1
        elif c == '\x1b[B' or c == 'j':
            self.current += 1
        elif c == '\n' or c == ' ':
            raise ExitException
        self.current %= self.n_options
        self.ui.draw_text(">", self.menu_x, self.menu_y + self.current)
        self.ui.update_screen()
    def tick(self):
        pass

if os.name == "posix":
    import select, termios
    class TerminalUI(BaseTerminalUI):
        def init(self):
            # update terminal options
            self.initial_options = termios.tcgetattr(0)
            custom_options = self.initial_options.copy()
            custom_options[3] &= ~termios.ECHO
            custom_options[3] &= ~termios.ICANON
            termios.tcsetattr(0, termios.TCSANOW, custom_options)

        def quit(self):
            # reset terminal options
            termios.tcsetattr(0, termios.TCSANOW, self.initial_options)
            # reset terminal
            self.set_fg_colour(COLOUR_WHITE)
            self.set_bg_colour(COLOUR_BLACK)
            self.goto(0, 0)
            self.update_screen()

        def main_loop(self, menu, tps=60):
            try:
                self.clear()
                self.update_screen()
                menu.init(self)
                time_left = 1/tps
                while True:
                    start_time = time.perf_counter()
                    r, _, _ = select.select([0], [], [], time_left)
                    terminal_size = shutil.get_terminal_size()
                    width = terminal_size.columns // 2
                    height = terminal_size.lines
                    if width != self.width or height != self.height:
                        self.width = width
                        self.height = height
                        menu.resize(width, height)
                    end_time = time.perf_counter()
                    time_left -= end_time - start_time
                    if r:
                        menu.key(os.read(0, 100).decode("utf8"))
                    while time_left < 0:
                        time_left += 1/tps
                        menu.tick()
            except ExitException:
                return

        def get_key(self):
            return os.read(0, 100).decode("utf8")

elif os.name == "nt":
    import msvcrt
    class TerminalUI(BaseTerminalUI):
        def init(self):
            pass

        def quit(self):
            self.set_fg_colour(COLOUR_WHITE)
            self.set_bg_colour(COLOUR_BLACK)
            self.goto(0, 0)
            self.update_screen()

        def main_loop(self, menu, tps=60):
            try:
                self.clear()
                self.update_screen()
                menu.init(self)
                while True:
                    terminal_size = shutil.get_terminal_size()
                    width = terminal_size.columns // 2
                    height = terminal_size.lines
                    if width != self.width or height != self.height:
                        self.width = width
                        self.height = height
                        menu.resize(width, height)
                    end_time = time.perf_counter()
                    if msvcrt.kbhit():
                        menu.key(self.get_key())
                    menu.tick()
                    time.sleep(1/tps)
            except ExitException:
                return

        def get_key(self):
            c = msvcrt.getch()
            if c == b'\r':
                return '\n'
            elif c == b'\xe0' or c == b'\x00':
                scancode = msvcrt.getch()[0]
                # use an arbritary string as a fallback so the game can still distinguish keys even if it doesn't know what they are
                s = "\x00" + chr(scancode)
                return SCANCODE_TO_ESCAPE_CODE.get(scancode, s)
            else:
                return chr(c[0])

else:
    exit("Unsupported operating system")
