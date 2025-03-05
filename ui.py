import sys, select, termios, time, os

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

COLOUR_DEFAULT = 16

class ExitException(Exception):
    pass

class Menu:
    def init(self, ui): raise NotImplementedError
    def tick(self): raise NotImplementedError
    def key(self, c): raise NotImplementedError

class UI:
    def init(self): pass
    def quit(self): pass
    def draw_text(self, text, x, y, fg_colour=COLOUR_DEFAULT, bg_colour=COLOUR_DEFAULT): raise NotImplementedError
    def set_pixel(self, colour, x, y): raise NotImplementedError
    def update_screen(self): raise NotImplementedError
    def main_loop(self, menu, tps=10): raise NotImplementedError
    def menu(self, options, starting_option=0): raise NotImplementedError
    def get_key(self): raise NotImplemented

class TerminalUI(UI):
    fg_colour_codes = [f"\x1b[3{x}m" for x in range(8)] + [f"\x1b[9{x}m" for x in range(8)] + ["\x1b[0m"]
    bg_colour_codes = [f"\x1b[4{x}m" for x in range(8)] + [f"\x1b[10{x}m" for x in range(8)] + ["\x1b[0m"]
    reset_code = "\x1b[0m"
    def __init__(self):
        self.fg_colour = COLOUR_DEFAULT
        self.bg_colour = COLOUR_DEFAULT
        self.buffer = ""
        self.inital_options = None
    def init(self):
        # update terminal options
        self.initial_options = termios.tcgetattr(0)
        custom_options = self.initial_options.copy()
        custom_options[3] &= ~termios.ECHO
        custom_options[3] &= ~termios.ICANON
        termios.tcsetattr(0, termios.TCSANOW, custom_options)
    def clear(self):
        self.buffer += "\x1b[0m\x1b[2J"
    def quit(self):
        # reset terminal options
        termios.tcsetattr(0, termios.TCSANOW, self.initial_options)
        # reset terminal
        self.set_fg_colour(COLOUR_WHITE)
        self.set_bg_colour(COLOUR_BLACK)
        self.goto(0, 0)
        self.update_screen()
    def set_fg_colour(self, colour):
        if colour != self.fg_colour:
            if colour == COLOUR_DEFAULT:
                self.buffer += TerminalUI.reset_code
                # set background colour again if resetting terminal for foreground
                old_bg_colour = self.bg_colour
                self.fg_colour = self.bg_colour = COLOUR_DEFAULT
                self.set_bg_colour(old_bg_colour)
            else:
                self.buffer += TerminalUI.fg_colour_codes[colour]
                self.fg_colour = colour
    def set_bg_colour(self, colour):
        if colour != self.bg_colour:
            if colour == COLOUR_DEFAULT:
                self.buffer += TerminalUI.reset_code
                # set foreground colour again if resetting terminal for background
                old_fg_colour = self.fg_colour
                self.fg_colour = self.bg_colour = COLOUR_DEFAULT
                self.set_fg_colour(old_fg_colour)
            else:
                self.buffer += TerminalUI.bg_colour_codes[colour]
                self.bg_colour = colour
    def goto(self, x, y):
        self.buffer += f"\x1b[{y+1};{x+1}H"
    def draw_text(self, text, x, y, fg_colour=COLOUR_DEFAULT, bg_colour=COLOUR_DEFAULT):
        self.set_fg_colour(fg_colour)
        self.set_bg_colour(bg_colour)
        self.goto(x, y)
        self.buffer += text
    def set_pixel(self, colour, x, y):
        self.set_bg_colour(colour)
        self.goto(x*2, y) # double x so pixels are approximately square
        self.buffer += "  "
    def update_screen(self):
        self.goto(0, 0)
        sys.stdout.write(self.buffer)
        sys.stdout.flush()
        self.buffer = ""
    def main_loop(self, menu, tps=10):
        try:
            self.clear()
            self.update_screen()
            menu.init(self)
            time_left = 1/tps
            while True:
                start_time = time.perf_counter()
                r, _, _ = select.select([0], [], [], time_left)
                end_time = time.perf_counter()
                time_left -= end_time - start_time
                if r:
                    menu.key(os.read(0, 100).decode("utf8"))
                while time_left < 0:
                    time_left += 1/tps
                    menu.tick()
        except ExitException:
            return
    def menu(self, options, starting_option=0):
        menu = TerminalMenu(options, starting_option)
        self.main_loop(menu, tps=1)
        return menu.current
    def get_key(self):
        return os.read(0, 100).decode("utf8")

class TerminalMenu:
    def __init__(self, options, current):
        self.options = options
        self.current = current
        self.ui = None
    def init(self, ui):
        self.ui = ui
        ui.clear()
        for i, option in enumerate(self.options):
            ui.draw_text(option, 2, i)
        ui.draw_text(">", 0, self.current)
        ui.update_screen()
    def key(self, c):
        self.ui.draw_text(" ", 0, self.current)
        if c == '\x1b[A' or c == 'k':
            self.current -= 1
        elif c == '\x1b[B' or c == 'j':
            self.current += 1
        elif c == '\n':
            raise ExitException
        self.current %= len(self.options)
        self.ui.draw_text(">", 0, self.current)
        self.ui.update_screen()
    def tick(self):
        pass
